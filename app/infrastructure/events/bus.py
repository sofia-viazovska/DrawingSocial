from typing import Dict, List, Callable, Type, Any
import logging

logger = logging.getLogger(__name__)

class EventBus:
    """Проста In-Memory реалізація шини подій для асинхронної комунікації"""
    def __init__(self):
        self._subscribers: Dict[Type, List[Callable]] = {}

    def subscribe(self, event_type: Type, handler: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed {handler.__name__} to {event_type.__name__}")

    def publish(self, event: Any):
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error handling event {event_type.__name__} by {handler.__name__}: {e}")

event_bus = EventBus()
