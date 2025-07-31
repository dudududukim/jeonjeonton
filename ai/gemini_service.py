import google.generativeai as genai
from config.settings import Settings
from events.event_types import Event, EventType

class GeminiService:
    def __init__(self, event_bus, settings: Settings):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro-vision')
        self.event_bus = event_bus
        self.event_bus.subscribe(EventType.GEMINI_RESPONSE, self.handle_analysis)

    async def handle_analysis(self, event):
        path = event.detail['path']
        img = open(path, 'rb').read()
        prompt = "Analyze this image"  # From attachment [3]
        response = self.model.generate_content([prompt, img])
        # Process response
