import asyncio
import logging
from typing import Dict, List, Callable, Any
from enum import Enum
from datetime import datetime


logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""
    TICKER_UPDATE = "ticker_update"
    CANDLE_UPDATE = "candle_update"
    ORDER_BOOK_UPDATE = "order_book_update"
    DATA_QUALITY_ALERT = "data_quality_alert"
    DATA_SYNC_COMPLETE = "data_sync_complete"
    ANOMALY_DETECTED = "anomaly_detected"


class Event:
    """事件对象"""

    def __init__(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        timestamp: datetime = None
    ):
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


class EventSubscriber:
    """事件订阅者"""

    def __init__(self, callback: Callable, event_types: List[EventType]):
        """
        初始化订阅者

        Args:
            callback: 回调函数
            event_types: 订阅的事件类型列表
        """
        self.callback = callback
        self.event_types = event_types

    async def handle_event(self, event: Event):
        """
        处理事件

        Args:
            event: 事件对象
        """
        if event.event_type in self.event_types:
            try:
                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback(event)
                else:
                    self.callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}", exc_info=True)


class EventBus:
    """事件总线 - 观察者模式实现"""

    def __init__(self):
        self.subscribers: List[EventSubscriber] = []
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task = None

    async def start(self):
        """启动事件总线"""
        if self._running:
            logger.warning("EventBus already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._process_events())
        logger.info("EventBus started")

    async def stop(self):
        """停止事件总线"""
        logger.info("Stopping EventBus")
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def subscribe(
        self,
        callback: Callable,
        event_types: List[EventType]
    ) -> EventSubscriber:
        """
        订阅事件

        Args:
            callback: 回调函数
            event_types: 订阅的事件类型列表

        Returns:
            订阅者对象
        """
        subscriber = EventSubscriber(callback, event_types)
        self.subscribers.append(subscriber)
        logger.info(
            f"Added subscriber for events: {[et.value for et in event_types]}"
        )
        return subscriber

    def unsubscribe(self, subscriber: EventSubscriber):
        """
        取消订阅

        Args:
            subscriber: 订阅者对象
        """
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)
            logger.info("Removed subscriber")

    async def publish(self, event: Event):
        """
        发布事件

        Args:
            event: 事件对象
        """
        await self.event_queue.put(event)
        logger.debug(f"Published event: {event.event_type.value}")

    async def publish_ticker_update(
        self,
        instrument_id: str,
        ticker_data: Dict[str, Any]
    ):
        """发布行情更新事件"""
        event = Event(
            event_type=EventType.TICKER_UPDATE,
            data={
                "instrument_id": instrument_id,
                "ticker": ticker_data
            }
        )
        await self.publish(event)

    async def publish_candle_update(
        self,
        instrument_id: str,
        bar: str,
        candle_data: Dict[str, Any]
    ):
        """发布K线更新事件"""
        event = Event(
            event_type=EventType.CANDLE_UPDATE,
            data={
                "instrument_id": instrument_id,
                "bar": bar,
                "candle": candle_data
            }
        )
        await self.publish(event)

    async def publish_order_book_update(
        self,
        instrument_id: str,
        order_book_data: Dict[str, Any]
    ):
        """发布订单簿更新事件"""
        event = Event(
            event_type=EventType.ORDER_BOOK_UPDATE,
            data={
                "instrument_id": instrument_id,
                "order_book": order_book_data
            }
        )
        await self.publish(event)

    async def publish_data_quality_alert(
        self,
        instrument_id: str,
        alert_type: str,
        message: str,
        details: Dict[str, Any]
    ):
        """发布数据质量告警事件"""
        event = Event(
            event_type=EventType.DATA_QUALITY_ALERT,
            data={
                "instrument_id": instrument_id,
                "alert_type": alert_type,
                "message": message,
                "details": details
            }
        )
        await self.publish(event)

    async def publish_anomaly_detected(
        self,
        instrument_id: str,
        bar: str,
        anomaly_data: Dict[str, Any]
    ):
        """发布异常检测事件"""
        event = Event(
            event_type=EventType.ANOMALY_DETECTED,
            data={
                "instrument_id": instrument_id,
                "bar": bar,
                "anomaly": anomaly_data
            }
        )
        await self.publish(event)

    async def _process_events(self):
        """处理事件队列"""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )

                await self._dispatch_event(event)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)

    async def _dispatch_event(self, event: Event):
        """
        分发事件给订阅者

        Args:
            event: 事件对象
        """
        tasks = []
        for subscriber in self.subscribers:
            if event.event_type in subscriber.event_types:
                tasks.append(subscriber.handle_event(event))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


event_bus = EventBus()
