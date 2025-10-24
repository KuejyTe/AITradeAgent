from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal

from app.models.trading import Order
from app.services.trading.schemas import OrderParams


class ExecutionStrategy(ABC):
    """Base class for execution strategies"""
    
    def __init__(self, executor, config: dict = None):
        """
        Initialize execution strategy
        
        Args:
            executor: TradeExecutor instance
            config: Strategy configuration
        """
        self.executor = executor
        self.config = config or {}
    
    @abstractmethod
    async def execute(self, order_params: OrderParams) -> List[Order]:
        """
        Execute order using this strategy
        
        Args:
            order_params: Order parameters
            
        Returns:
            List of created orders
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name"""
        pass
    
    def _split_size(self, total_size: Decimal, num_splits: int) -> List[Decimal]:
        """
        Split order size into multiple parts
        
        Args:
            total_size: Total order size
            num_splits: Number of splits
            
        Returns:
            List of split sizes
        """
        base_size = total_size / num_splits
        sizes = [base_size] * num_splits
        
        # Adjust last size to account for rounding
        sizes[-1] = total_size - sum(sizes[:-1])
        
        return sizes
