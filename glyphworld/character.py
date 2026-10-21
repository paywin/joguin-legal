from dataclasses import dataclass
import math

@dataclass
class Character:
    x: float = 0.
    z: float = 8.
    phase: float = 0.
    height: float = 0.
    vertical_speed: float = 0.
    automatic: bool = False

    def update(self, dt, city=None, direction=(0.,0.), jump=False):
        if dt<=0: return
        dx,dz=direction
        if self.automatic: dx,dz=0.,1.
        length=math.hypot(dx,dz)
        if length:
            dx,dz=dx/length*3.5*dt,dz/length*3.5*dt
            before=self.x,self.z
            self.x,self.z=city.move(self.x,self.z,dx,dz) if city else (self.x+dx,self.z+dz)
            self.phase+=math.dist(before,(self.x,self.z))*3.4
        if jump and self.height==0: self.vertical_speed=4.8
        if self.height>0 or self.vertical_speed>0:
            self.height=max(0.,self.height+self.vertical_speed*dt-4.9*dt*dt)
            self.vertical_speed-=9.8*dt
            if self.height==0: self.vertical_speed=0.

    @property
    def bob(self):
        return abs(math.sin(self.phase))*.035
