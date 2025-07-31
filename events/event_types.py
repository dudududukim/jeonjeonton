from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, Optional

class EventType(Enum):
    WEATHER_UPDATE = "weather_update"
    ACTUATOR_POP = "actuator_pop"
    HUMAN_COME = "human_come"
    HUMAN_OUT = "human_out"
    CAMERA_CAPTURE = "camera_capture"
    GEMINI_RESPONSE = "gemini_response"

@dataclass
class Event:
    type: EventType
    detail: Dict[str, Any]
    source: Optional[str] = None
