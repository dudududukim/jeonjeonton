import asyncio
import logging
from typing import Dict, List, Callable
from .event_types import Event, EventType


class EventBus:
    def __init__(self, logger: logging.Logger = None):
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.logger = logger or logging.getLogger(__name__)

    def subscribe(self, event_type: EventType, callback: Callable):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    async def emit(self, event: Event):
        # 이벤트 발생 로그
        self.logger.info(f"Event emitted: {event.type} - {event}")
        
        if event.type in self.subscribers:
            subscriber_count = len(self.subscribers[event.type])
            async_callbacks = [callback for callback in self.subscribers[event.type] 
                             if asyncio.iscoroutinefunction(callback)]
            
            self.logger.debug(f"Processing event {event.type} with {subscriber_count} subscribers, "
                            f"{len(async_callbacks)} async callbacks")
            
            try:
                # 비동기 콜백들 실행
                tasks = [callback(event) for callback in async_callbacks]
                await asyncio.gather(*tasks)
                
                # 동기 콜백들도 실행 (필요한 경우)
                sync_callbacks = [callback for callback in self.subscribers[event.type] 
                                if not asyncio.iscoroutinefunction(callback)]
                for callback in sync_callbacks:
                    callback(event)
                
                self.logger.info(f"Event {event.type} processed successfully")
                
            except Exception as e:
                self.logger.error(f"Error processing event {event.type}: {str(e)}")
                raise
        else:
            self.logger.warning(f"No subscribers found for event type: {event.type}")
