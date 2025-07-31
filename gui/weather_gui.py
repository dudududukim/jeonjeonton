import tkinter as tk
from events.event_types import Event, EventType

# Simplified from attachment [1]
class WeatherGUI(tk.Tk):
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self.title("Weather GUI")
        # Add UI elements, button to emit WEATHER_UPDATE
        button = tk.Button(self, text="Update Weather", command=lambda: self.event_bus.emit(Event(EventType.WEATHER_UPDATE, {})))
        button.pack()

    def run(self):
        self.mainloop()
