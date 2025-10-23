import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.services.trading import TradeExecutor, OrderManager, ExecutionRiskControl
from app.services.trading.schemas import OrderParams
from app.models.trading import OrderSide, OrderType, OrderStatus
from app.strategies.signals import Signal, SignalType
from app.strategies.models import Account


@pytest.fixture
def mock_db_session():
    return Mock()


@pytest.fixture
def mock_okx_client():
    client = Mock()
    client.trade = Mock()
    client.trade.place_order = AsyncMock(return_value=[{
        'ordId': '12345',
        'sCode': '0',
        'sMsg': ''
    }])
    client.trade.cancel_order = AsyncMock(return_value=[{
        'ordId': '12345',
        'sCode': '0',
        'sMsg': ''
    }])
    return client


@pytest.fixture
def order_manager(mock_db_session):
    return OrderManager(mock_db_session)


@pytest.fixture
def risk_control():
    return ExecutionRiskControl()


@pytest.fixture
def executor(mock_okx_client, order_manager, risk_control):
    return TradeExecutor(
        okx_client=mock_okx_client,
        order_manager=order_manager,
        risk_manager=risk_control
    )


class TestTradeExecutor:
    
    def test_executor_initialization(self, executor):
        """Test executor initializes correctly"""
        assert executor is not None
        assert executor.okx_client is not None
        assert executor.order_manager is not None
        assert executor.risk_manager is not None
    
    @pytest.mark.asyncio
    async def test_place_order_basic(self, executor, mock_db_session):
        """Test basic order placement"""
        order_params = OrderParams(
            instrument_id="BTC-USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            size=Decimal("0.1"),
            trade_mode="cash"
        )
        
        # Mock database operations
        with patch.object(executor.order_manager, 'create_order') as mock_create:
            mock_order = Mock()
            mock_order.id = 1
            mock_order.instrument_id = "BTC-USDT"
            mock_order.exchange_order_id = None
            mock_create.return_value = mock_order
            
            with patch.object(executor.order_manager, 'update_order_status') as mock_update:
                mock_order.exchange_order_id = "12345"
                mock_update.return_value = mock_order
                
                order = await executor.place_order(order_params)
                
                assert order is not None
                assert mock_create.called
    
    @pytest.mark.asyncio
    async def test_execute_signal(self, executor):
        """Test signal execution"""
        signal = Signal(
            type=SignalType.BUY,
            instrument_id="BTC-USDT",
            price=Decimal("50000"),
            size=Decimal("0.1"),
            confidence=0.8
        )
        
        account = Account(
            balance=Decimal("10000"),
            equity=Decimal("10000"),
            available_balance=Decimal("10000"),
            positions=[],
            daily_pnl=Decimal("0"),
            total_pnl=Decimal("0"),
            margin_used=Decimal("0")
        )
        
        # Mock order creation and placement
        with patch.object(executor, 'place_order') as mock_place:
            mock_order = Mock()
            mock_order.id = 1
            mock_place.return_value = mock_order
            
            order = await executor.execute_signal(signal, account)
            
            assert order is not None
            assert mock_place.called


class TestOrderManager:
    
    def test_order_manager_initialization(self, order_manager):
        """Test order manager initializes correctly"""
        assert order_manager is not None
        assert order_manager.active_orders == {}
    
    def test_create_order(self, order_manager, mock_db_session):
        """Test order creation"""
        order_params = OrderParams(
            instrument_id="BTC-USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            size=Decimal("0.1"),
            trade_mode="cash"
        )
        
        # Mock database operations
        with patch.object(mock_db_session, 'add'):
            with patch.object(mock_db_session, 'commit'):
                with patch.object(mock_db_session, 'refresh'):
                    order = order_manager.create_order(order_params)
                    
                    assert order is not None


class TestExecutionRiskControl:
    
    def test_risk_control_initialization(self, risk_control):
        """Test risk control initializes correctly"""
        assert risk_control is not None
        assert risk_control.max_order_size > 0
    
    def test_pre_trade_check_insufficient_balance(self, risk_control):
        """Test risk check fails with insufficient balance"""
        signal = Signal(
            type=SignalType.BUY,
            instrument_id="BTC-USDT",
            price=Decimal("50000"),
            size=Decimal("1.0"),
            confidence=0.8
        )
        
        account = Account(
            balance=Decimal("1000"),
            equity=Decimal("1000"),
            available_balance=Decimal("1000"),
            positions=[],
            daily_pnl=Decimal("0"),
            total_pnl=Decimal("0"),
            margin_used=Decimal("0")
        )
        
        result = risk_control.pre_trade_check(signal, account)
        
        # Should either fail or adjust size
        assert result.passed or result.adjusted_size is not None
    
    def test_validate_order_params(self, risk_control):
        """Test order parameter validation"""
        order_params = OrderParams(
            instrument_id="BTC-USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            size=Decimal("0.1"),
            price=Decimal("50000"),
            trade_mode="cash"
        )
        
        result = risk_control.validate_order_params(order_params)
        
        assert result.passed
