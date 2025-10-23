from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
import logging

from app.strategies.base import BaseStrategy
from app.strategies.models import MarketData, Account, Order, Position, Candle, OrderSide, OrderStatus
from app.strategies.signals import Signal, SignalType


logger = logging.getLogger(__name__)


class BacktestResult:
    """Container for backtest results and performance metrics."""
    
    def __init__(self):
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict[str, Any]] = []
        self.signals: List[Signal] = []
        self.initial_balance: Decimal = Decimal("0")
        self.final_balance: Decimal = Decimal("0")
        self.total_trades: int = 0
        self.winning_trades: int = 0
        self.losing_trades: int = 0
        self.total_pnl: Decimal = Decimal("0")
        self.max_drawdown: Decimal = Decimal("0")
        self.sharpe_ratio: float = 0.0
        self.win_rate: float = 0.0
        self.profit_factor: float = 0.0
    
    def calculate_metrics(self):
        """Calculate performance metrics from trade history."""
        if not self.trades:
            return
        
        # Calculate basic statistics
        self.total_trades = len(self.trades)
        
        gross_profit = Decimal("0")
        gross_loss = Decimal("0")
        
        for trade in self.trades:
            pnl = Decimal(str(trade.get("pnl", 0)))
            self.total_pnl += pnl
            
            if pnl > 0:
                self.winning_trades += 1
                gross_profit += pnl
            elif pnl < 0:
                self.losing_trades += 1
                gross_loss += abs(pnl)
        
        # Win rate
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades
        
        # Profit factor
        if gross_loss > 0:
            self.profit_factor = float(gross_profit / gross_loss)
        
        # Calculate max drawdown
        if self.equity_curve:
            peak = Decimal("0")
            max_dd = Decimal("0")
            
            for point in self.equity_curve:
                equity = Decimal(str(point["equity"]))
                if equity > peak:
                    peak = equity
                
                drawdown = (peak - equity) / peak if peak > 0 else Decimal("0")
                if drawdown > max_dd:
                    max_dd = drawdown
            
            self.max_drawdown = max_dd
        
        # Calculate Sharpe ratio (simplified)
        if self.equity_curve and len(self.equity_curve) > 1:
            returns = []
            for i in range(1, len(self.equity_curve)):
                prev_equity = Decimal(str(self.equity_curve[i-1]["equity"]))
                curr_equity = Decimal(str(self.equity_curve[i]["equity"]))
                if prev_equity > 0:
                    ret = float((curr_equity - prev_equity) / prev_equity)
                    returns.append(ret)
            
            if returns:
                avg_return = sum(returns) / len(returns)
                std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
                
                if std_return > 0:
                    # Annualized Sharpe ratio (assuming daily returns)
                    self.sharpe_ratio = (avg_return / std_return) * (252 ** 0.5)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary."""
        return {
            "initial_balance": str(self.initial_balance),
            "final_balance": str(self.final_balance),
            "total_pnl": str(self.total_pnl),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": round(self.win_rate * 100, 2),
            "profit_factor": round(self.profit_factor, 2),
            "max_drawdown": round(float(self.max_drawdown) * 100, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "trades": self.trades,
            "equity_curve": self.equity_curve
        }


class Backtester:
    """
    Backtesting framework for trading strategies.
    
    Simulates strategy execution on historical data and calculates performance metrics.
    """
    
    def __init__(
        self,
        strategy: BaseStrategy,
        initial_balance: Decimal = Decimal("10000"),
        commission_rate: Decimal = Decimal("0.001")
    ):
        """
        Initialize backtester.
        
        Args:
            strategy: Strategy to backtest
            initial_balance: Initial account balance
            commission_rate: Trading commission rate (0.001 = 0.1%)
        """
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.commission_rate = commission_rate
        
        # Simulation state
        self.account: Optional[Account] = None
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.result = BacktestResult()
    
    def run(self, historical_data: List[MarketData]) -> BacktestResult:
        """
        Run backtest on historical data.
        
        Args:
            historical_data: List of historical market data
            
        Returns:
            BacktestResult with performance metrics
        """
        # Initialize account
        self.account = Account(
            balance=self.initial_balance,
            equity=self.initial_balance,
            available_balance=self.initial_balance,
            positions=[],
            daily_pnl=Decimal("0"),
            total_pnl=Decimal("0")
        )
        
        self.result.initial_balance = self.initial_balance
        
        # Start strategy
        self.strategy.on_start()
        
        # Process each data point
        for i, market_data in enumerate(historical_data):
            try:
                # Update positions with current prices
                self._update_positions(market_data)
                
                # Update account equity
                self._update_account()
                
                # Record equity
                self.result.equity_curve.append({
                    "timestamp": market_data.timestamp.isoformat(),
                    "equity": str(self.account.equity)
                })
                
                # Generate signal from strategy
                signal = self.strategy.analyze(market_data)
                
                if signal and self.strategy.validate_signal(signal):
                    # Calculate position size
                    signal.size = self.strategy.calculate_position_size(signal, self.account)
                    
                    # Execute signal
                    self._execute_signal(signal, market_data)
                    
                    self.result.signals.append(signal)
            
            except Exception as e:
                logger.error(f"Error during backtest at step {i}: {str(e)}")
        
        # Stop strategy
        self.strategy.on_stop()
        
        # Close all positions
        for instrument_id, position in list(self.positions.items()):
            last_data = historical_data[-1] if historical_data else None
            if last_data:
                self._close_position(instrument_id, last_data.current_price)
        
        # Finalize results
        self.result.final_balance = self.account.balance
        self.result.calculate_metrics()
        
        return self.result
    
    def _execute_signal(self, signal: Signal, market_data: MarketData):
        """
        Execute a trading signal.
        
        Args:
            signal: Trading signal to execute
            market_data: Current market data
        """
        instrument_id = signal.instrument_id
        
        # Check if position already exists
        if instrument_id in self.positions:
            # Close existing position if signal is opposite
            position = self.positions[instrument_id]
            if (position.side == OrderSide.BUY and signal.type == SignalType.SELL) or \
               (position.side == OrderSide.SELL and signal.type == SignalType.BUY):
                self._close_position(instrument_id, signal.price)
                return
        
        # Open new position
        if signal.type in [SignalType.BUY, SignalType.SELL]:
            self._open_position(signal, market_data)
        elif signal.type == SignalType.CLOSE:
            if instrument_id in self.positions:
                self._close_position(instrument_id, signal.price)
    
    def _open_position(self, signal: Signal, market_data: MarketData):
        """
        Open a new position.
        
        Args:
            signal: Trading signal
            market_data: Current market data
        """
        # Calculate cost including commission
        cost = signal.price * signal.size
        commission = cost * self.commission_rate
        total_cost = cost + commission
        
        # Check if we have sufficient balance
        if total_cost > self.account.available_balance:
            logger.warning(f"Insufficient balance to open position: need {total_cost}, have {self.account.available_balance}")
            return
        
        # Create position
        side = OrderSide.BUY if signal.type == SignalType.BUY else OrderSide.SELL
        position = Position(
            instrument_id=signal.instrument_id,
            size=signal.size,
            entry_price=signal.price,
            current_price=signal.price,
            side=side,
            timestamp=market_data.timestamp
        )
        
        # Update account
        self.account.available_balance -= total_cost
        self.positions[signal.instrument_id] = position
        self.account.positions.append(position)
        
        logger.info(f"Opened {side.value} position: {signal.size} @ {signal.price}")
    
    def _close_position(self, instrument_id: str, close_price: Decimal):
        """
        Close an existing position.
        
        Args:
            instrument_id: Instrument identifier
            close_price: Closing price
        """
        if instrument_id not in self.positions:
            return
        
        position = self.positions[instrument_id]
        
        # Calculate PnL
        if position.side == OrderSide.BUY:
            pnl = (close_price - position.entry_price) * position.size
        else:  # SELL
            pnl = (position.entry_price - close_price) * position.size
        
        # Calculate commission
        close_value = close_price * position.size
        commission = close_value * self.commission_rate
        
        # Net PnL after commission
        net_pnl = pnl - commission - (position.entry_price * position.size * self.commission_rate)
        
        # Update account
        self.account.available_balance += close_value + net_pnl
        self.account.balance += net_pnl
        self.account.total_pnl += net_pnl
        
        # Record trade
        self.result.trades.append({
            "instrument_id": instrument_id,
            "side": position.side.value,
            "entry_price": str(position.entry_price),
            "exit_price": str(close_price),
            "size": str(position.size),
            "pnl": str(net_pnl),
            "entry_time": position.timestamp.isoformat(),
            "exit_time": datetime.now(timezone.utc).isoformat()
        })
        
        # Remove position
        self.account.positions = [p for p in self.account.positions if p.instrument_id != instrument_id]
        del self.positions[instrument_id]
        
        logger.info(f"Closed {position.side.value} position: PnL = {net_pnl}")
    
    def _update_positions(self, market_data: MarketData):
        """
        Update position prices with current market data.
        
        Args:
            market_data: Current market data
        """
        if market_data.instrument_id in self.positions:
            position = self.positions[market_data.instrument_id]
            position.current_price = market_data.current_price
            
            # Calculate unrealized PnL
            if position.side == OrderSide.BUY:
                position.unrealized_pnl = (market_data.current_price - position.entry_price) * position.size
            else:
                position.unrealized_pnl = (position.entry_price - market_data.current_price) * position.size
    
    def _update_account(self):
        """Update account equity based on current positions."""
        # Calculate total unrealized PnL
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        
        # Update equity
        self.account.equity = self.account.balance + total_unrealized_pnl
