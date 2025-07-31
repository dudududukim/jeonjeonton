import cv2
from datetime import datetime
from events.event_types import Event, EventType

class CameraService:
    def __init__(self, event_bus, settings):
        self.event_bus = event_bus
        self.settings = settings
        self.event_bus.subscribe(EventType.CAMERA_CAPTURE, self.handle_capture)

    async def handle_capture(self, event):
        cap = cv2.VideoCapture(self.settings.CAMERA_PORT)
        ret, frame = cap.read()
        if ret:
            path = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(path, frame)
            await self.event_bus.emit(Event(EventType.GEMINI_RESPONSE, {'path': path}))
        cap.release()
