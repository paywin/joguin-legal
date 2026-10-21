from dataclasses import dataclass
import math


@dataclass
class Character:
    x: float = 0.0
    phase: float = 0.0

    def update(self, dt):
        self.phase += dt * 6.5
        self.x += dt * 0.075

    @property
    def bob(self):
        return abs(math.sin(self.phase)) * 0.003
