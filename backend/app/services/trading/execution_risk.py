from decimal import Decimal
from typing import Optional
import logging

from app.strategies.signals import Signal, SignalType
from app.strategies.models import Account
from app.services.trading.schemas import OrderParams, RiskCheckResult

logger = logging.getLogger(__name__)


class ExecutionRiskControl:
    """Risk control for order execution"""
    
    def __init__(self, config: dict = None):
        """
        Initialize execution risk control
        
        Args:
            config: Risk control configuration
        """
        config = config or {}
        self.max_order_size = Decimal(str(config.get('max_order_size', 10.0)))
        self.min_order_size = Decimal(str(config.get('min_order_size', 0.001)))
        self.max_order_value = Decimal(str(config.get('max_order_value', 10000.0)))
        self.max_price_deviation = Decimal(str(config.get('max_price_deviation', 0.05)))  # 5%
        self.max_daily_loss = Decimal(str(config.get('max_daily_loss', 0.1)))  # 10%
        self.max_position_value_pct = Decimal(str(config.get('max_position_value_pct', 0.5)))  # 50%
        self.require_positive_balance = config.get('require_positive_balance', True)
    
    def pre_trade_check(self, signal: Signal, account: Account) -> RiskCheckResult:
        """
        Perform pre-trade risk checks
        
        Args:
            signal: Trading signal
            account: Account state
            
        Returns:
            RiskCheckResult with validation result
        """
        warnings = []
        
        # Check account balance
        if self.require_positive_balance and account.available_balance <= 0:
            return RiskCheckResult(
                passed=False,
                reason="Insufficient balance: account has no available balance"
            )
        
        # Check daily loss limit
        if account.daily_pnl < -abs(self.max_daily_loss * account.equity):
            return RiskCheckResult(
                passed=False,
                reason=f"Daily loss limit reached: {account.daily_pnl} / {account.equity}"
            )
        
        # Check order size limits
        if signal.size < self.min_order_size:
            return RiskCheckResult(
                passed=False,
                reason=f"Order size {signal.size} below minimum {self.min_order_size}"
            )
        
        if signal.size > self.max_order_size:
            warnings.append(f"Order size {signal.size} exceeds maximum {self.max_order_size}, will be adjusted")
        
        # Check order value
        order_value = signal.price * signal.size
        if order_value > self.max_order_value:
            warnings.append(f"Order value {order_value} exceeds maximum {self.max_order_value}, will be adjusted")
        
        # Check if order value exceeds available balance
        required_capital = order_value
        if required_capital > account.available_balance:
            adjusted_size = account.available_balance / signal.price * Decimal("0.99")  # 99% to leave buffer
            if adjusted_size < self.min_order_size:
                return RiskCheckResult(
                    passed=False,
                    reason=f"Insufficient balance: required {required_capital}, available {account.available_balance}"
                )
            warnings.append(f"Order size adjusted to {adjusted_size} due to insufficient balance")
            return RiskCheckResult(
                passed=True,
                adjusted_size=adjusted_size,
                warnings=warnings
            )
        
        # Check position concentration
        total_position_value = sum(pos.size * pos.current_price for pos in account.positions)
        new_position_value = total_position_value + order_value
        max_allowed_value = account.equity * self.max_position_value_pct
        
        if new_position_value > max_allowed_value:
            warnings.append(f"Position concentration high: {new_position_value} / {max_allowed_value}")
        
        # Calculate adjusted size if needed
        adjusted_size = signal.size
        if adjusted_size > self.max_order_size:
            adjusted_size = self.max_order_size
        
        if adjusted_size * signal.price > self.max_order_value:
            adjusted_size = self.max_order_value / signal.price
        
        if adjusted_size != signal.size:
            return RiskCheckResult(
                passed=True,
                adjusted_size=adjusted_size,
                warnings=warnings
            )
        
        return RiskCheckResult(passed=True, warnings=warnings)
    
    def validate_order_params(
        self,
        params: OrderParams,
        current_market_price: Optional[Decimal] = None
    ) -> RiskCheckResult:
        """
        Validate order parameters
        
        Args:
            params: Order parameters
            current_market_price: Current market price (for price validation)
            
        Returns:
            RiskCheckResult with validation result
        """
        warnings = []
        
        # Validate size
        if params.size <= 0:
            return RiskCheckResult(
                passed=False,
                reason="Order size must be positive"
            )
        
        if params.size < self.min_order_size:
            return RiskCheckResult(
                passed=False,
                reason=f"Order size {params.size} below minimum {self.min_order_size}"
            )
        
        if params.size > self.max_order_size:
            warnings.append(f"Order size {params.size} exceeds maximum {self.max_order_size}")
        
        # Validate price for limit orders
        if params.order_type.value in ['limit', 'post_only']:
            if not params.price or params.price <= 0:
                return RiskCheckResult(
                    passed=False,
                    reason="Limit orders require a valid price"
                )
            
            # Check price deviation from market price
            if current_market_price and current_market_price > 0:
                price_deviation = abs(params.price - current_market_price) / current_market_price
                if price_deviation > self.max_price_deviation:
                    return RiskCheckResult(
                        passed=False,
                        reason=f"Price deviation {price_deviation:.2%} exceeds maximum {self.max_price_deviation:.2%}"
                    )
        
        # Validate order value
        if params.price:
            order_value = params.price * params.size
            if order_value > self.max_order_value:
                warnings.append(f"Order value {order_value} exceeds maximum {self.max_order_value}")
        
        return RiskCheckResult(passed=True, warnings=warnings)
    
    def validate_price_reasonability(
        self,
        price: Decimal,
        market_price: Decimal,
        order_side: str
    ) -> bool:
        """
        Validate if order price is reasonable compared to market price
        
        Args:
            price: Order price
            market_price: Current market price
            order_side: Order side (buy/sell)
            
        Returns:
            True if price is reasonable
        """
        if market_price <= 0:
            return True  # Can't validate without market price
        
        deviation = abs(price - market_price) / market_price
        
        # Check if deviation is within acceptable range
        if deviation > self.max_price_deviation:
            logger.warning(
                f"Price deviation {deviation:.2%} exceeds maximum {self.max_price_deviation:.2%}"
            )
            return False
        
        # Additional checks for market manipulation prevention
        if order_side == 'buy' and price > market_price * (Decimal("1") + self.max_price_deviation):
            logger.warning(f"Buy price {price} too high compared to market {market_price}")
            return False
        
        if order_side == 'sell' and price < market_price * (Decimal("1") - self.max_price_deviation):
            logger.warning(f"Sell price {price} too low compared to market {market_price}")
            return False
        
        return True
