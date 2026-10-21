from dataclasses import dataclass


@dataclass
class Atmosphere:
    rain: bool = True
    lighting: bool = True
    time: float = 0.0

    def update(self, dt):
        self.time += dt
