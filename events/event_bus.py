import asyncio
from typing import Dict, List, Callable
from .event_types import Event, EventType

class EventBus:
    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = {}

    def subscribe(self, event_type: EventType, callback: Callable):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    async def emit(self, event: Event):
        if event.type in self.subscribers:
            tasks = [callback(event) for callback in self.subscribers[event.type] if asyncio.iscoroutinefunction(callback)]
            await asyncio.gather(*tasks)
