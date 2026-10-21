from dataclasses import dataclass
import math

@dataclass
class Atmosphere:
    rain: bool = False
    lighting: bool = True
    time: float = 0.
    hour: float = 9.
    day_seconds: float = 480.
    cycle: bool = True

    def update(self, dt):
        self.time+=dt
        if self.cycle: self.hour=(self.hour+dt*24/self.day_seconds)%24

    @property
    def daylight(self):
        return min(1.,max(0.,math.sin((self.hour-6)/24*math.tau)*2+.15))

    @property
    def clock(self):
        return f"{int(self.hour):02}:{int(self.hour%1*60):02}"
