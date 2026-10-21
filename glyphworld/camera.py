from dataclasses import dataclass
import math

@dataclass
class Camera:
    x: float = 0.
    z: float = 8.
    zoom: float = 1.

    def update(self, target, dt):
        tx,tz=target
        alpha=1.-math.exp(-dt*5.)
        self.x+=(tx-self.x)*alpha
        self.z+=(tz-self.z)*alpha

    def snap(self, character):
        self.x,self.z=character.x,character.z

    def zoom_by(self, factor):
        self.zoom=min(1.8,max(.65,self.zoom*factor))
