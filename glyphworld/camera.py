from dataclasses import dataclass
import math

@dataclass
class Camera:
    x: float = 0.
    z: float = 8.
    zoom: float = 1.
    yaw: float = .10
    pitch: float = -.08
    first_person: bool = False

    def update(self, target, dt):
        tx,tz=target
        alpha=1.-math.exp(-dt*5.)
        self.x+=(tx-self.x)*alpha
        self.z+=(tz-self.z)*alpha

    def snap(self, character):
        self.x,self.z=character.x,character.z

    def zoom_by(self, factor):
        self.zoom=min(1.8,max(.65,self.zoom*factor))

    def look(self, dx, dy):
        self.yaw=(self.yaw+dx*.0025) % (2*math.pi)
        self.pitch=max(-1.1,min(1.1,self.pitch-dy*.0025))

    def movement(self, right, forward):
        s,c=math.sin(self.yaw),math.cos(self.yaw)
        return right*c+forward*s, -right*s+forward*c

    def pose(self, character, city):
        s,c=math.sin(self.yaw),math.cos(self.yaw)
        cp,sp=math.cos(self.pitch),math.sin(self.pitch)
        forward=(s*cp,sp,c*cp)
        right=(c,0.,-s)
        up=(-s*sp,cp,-c*sp)
        origin=(character.x,1.65+character.height,character.z)
        if not self.first_person:
            # Sweep the camera arm in small steps: never place it behind a wall.
            anchor=(self.x,1.65+character.height,self.z)
            for step in range(1,46):
                distance=step*.1/self.zoom
                candidate=tuple(anchor[i]-forward[i]*distance for i in range(3))
                if city.blocked(candidate[0],candidate[2],.18) or candidate[1]<.3:
                    break
                origin=candidate
        return dict(camera_origin=origin,camera_forward=forward,camera_right=right,camera_up=up)
