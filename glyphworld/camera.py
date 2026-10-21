from dataclasses import dataclass
import math


@dataclass
class Camera:
    x: float = -0.18
    zoom: float = 1.0

    def update(self, target, dt):
        self.x += (target + 0.16 - self.x) * (1.0 - math.exp(-dt * 1.6))

    def zoom_by(self, factor):
        self.zoom = min(1.8, max(0.65, self.zoom * factor))
