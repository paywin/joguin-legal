"""Deterministic streamed city. Collision and GPU geometry share building bounds."""
from dataclasses import dataclass
from functools import lru_cache
import math
import numpy as np

BLOCK = 26.0
MAX_BOXES = 512
BUILDING, METAL, LEAF, GLASS, PERSON, CAR, SIGN, WOOD = range(1, 9)


@dataclass(frozen=True)
class Building:
    key: tuple
    x: float
    z: float
    hx: float
    hz: float
    height: float
    style: int

    @property
    def door(self):
        return self.x, self.z-self.hz-.8


def random01(x, z, seed, salt=0):
    n = (x*374761393 + z*668265263 + seed*1442695041 + salt*1274126177) & 0xffffffff
    n = ((n ^ (n >> 13))*1274126177) & 0xffffffff
    return ((n ^ (n >> 16)) & 0xffffffff)/4294967296


class City:
    def __init__(self, seed=42):
        self.seed = seed
        self.interior = None
        self.return_position = None

    @lru_cache(maxsize=64)
    def block(self, ix, iz):
        buildings = []
        for index, (sx, sz) in enumerate(((-1,-1),(1,-1),(-1,1),(1,1))):
            r = random01(ix, iz, self.seed, index)
            buildings.append(Building((ix,iz,index),ix*BLOCK+13+sx*4.6,
                                      iz*BLOCK+13+sz*4.6,3.25+r*.35,3.3,
                                      5.5+math.floor(r*5)*2.8,int(r*4)))
        return tuple(buildings)

    def nearby(self, x, z, radius=1):
        ix, iz = math.floor(x/BLOCK), math.floor(z/BLOCK)
        return tuple(b for dz in range(-radius,radius+1) for dx in range(-radius,radius+1)
                     for b in self.block(ix+dx,iz+dz))

    def blocked(self, x, z, radius=.28):
        if self.interior is not None:
            if abs(x)>5.6-radius or abs(z)>4.6-radius: return True
            return any(abs(x-cx)<hx+radius and abs(z-cz)<hz+radius
                       for cx,cz,hx,hz in self.furniture())
        return any(abs(x-b.x)<b.hx+radius and abs(z-b.z)<b.hz+radius
                   for b in self.nearby(x,z,0))

    def move(self, x, z, dx, dz):
        steps=max(1,math.ceil(math.hypot(dx,dz)/.15))
        for _ in range(steps):
            if not self.blocked(x+dx/steps,z): x+=dx/steps
            if not self.blocked(x,z+dz/steps): z+=dz/steps
        return x,z

    def nearest_door(self, x, z):
        if self.interior is not None: return None
        door=min(self.nearby(x,z),key=lambda b:math.dist((x,z),b.door))
        return door if math.dist((x,z),door.door)<1.8 else None

    def interact(self, character):
        if self.interior is not None:
            if math.dist((character.x,character.z),(0,-4))>2.0: return False
            character.x,character.z=self.return_position
            self.interior=None
        else:
            door=self.nearest_door(character.x,character.z)
            if door is None: return False
            self.interior=door
            self.return_position=door.door
            character.x,character.z=0.,-3.6
        character.height=character.vertical_speed=0.
        return True

    def furniture(self):
        if self.interior is None: return ()
        if self.interior.style%2:
            return ((-3,1,1.5,1.8),(2.7,2,1.4,.65),(-3,-2,.7,.7))
        return ((-2.8,1,1.4,.65),(2.7,1,.65,2),(0,3.7,3,.45))

    @property
    def location(self):
        if self.interior is None: return "TOKYO / HIKARI DISTRICT"
        return "APARTMENT" if self.interior.style%2 else "RAMEN / SHOP"


def pack_box(rows, center, half, color, material, detail=0):
    x,y,z=center; hx,hy,hz=half
    rows.append(((x-hx,y-hy,z-hz,float(material)),(x+hx,y+hy,z+hz,float(detail)),(*color,1.)))


def person(rows,x,z,time,color,height=0.,phase=None):
    phase=time*6 if phase is None else phase
    stride=math.sin(phase)*.19
    pack_box(rows,(x,.92+height,z),(.24,.39,.18),color,PERSON)
    pack_box(rows,(x,1.53+height,z),(.22,.22,.21),(.92,.78,.59),PERSON,1)
    for side in (-1,1):
        pack_box(rows,(x+side*.13,.30+height,z+side*stride),(.08,.30,.10),(.12,.18,.24),PERSON)
    pack_box(rows,(x-.32,1.10+height,z),(.09,.26,.1),color,PERSON)
    pack_box(rows,(x+.32,1.10+height,z),(.09,.26,.1),color,PERSON)


def city_geometry(city, character, time):
    """Bounded geometry: 512 boxes in a 3x512 RGBA32F texture (24 KiB)."""
    rows=[]
    if city.interior is not None:
        for c,h in [((0,1.6,4.8),(6,1.6,.2)),((-5.8,1.6,0),(.2,1.6,4.8)),((5.8,1.6,0),(.2,1.6,4.8))]:
            pack_box(rows,c,h,(.78,.75,.65),WOOD)
        for cx,cz,hx,hz in city.furniture():
            pack_box(rows,(cx,.55,cz),(hx,.55,hz),(.48,.30,.17),WOOD)
            pack_box(rows,(cx,1.15,cz),(hx,.05,hz),(.84,.77,.61),WOOD)
        pack_box(rows,(0,2.3,4.55),(2,.5,.1),(.25,.64,.69),SIGN,2)
        pack_box(rows,(-4.8,1.,3.8),(.4,1.,.4),(.21,.45,.30),LEAF)
        pack_box(rows,(3.8,1.65,4.55),(.6,.8,.1),(.7,.87,.92),GLASS)
    else:
        for b in city.nearby(character.x,character.z):
            palette=((.68,.74,.75),(.48,.61,.68),(.78,.74,.64),(.55,.65,.67))
            pack_box(rows,(b.x,b.height*.5,b.z),(b.hx,b.height*.5,b.hz),palette[b.style],BUILDING,b.style)
            pack_box(rows,(b.x,b.height+.17,b.z),(b.hx+.16,.17,b.hz+.16),(.27,.36,.39),METAL)
            pack_box(rows,(b.x+.8,b.height+.65,b.z+.6),(1.05,.5,.8),(.56,.66,.67),METAL,1)
            pack_box(rows,(b.x+b.hx-.48,3.8,b.z-b.hz-.17),(.35,1.45,.15),
                     (.22,.76,.79) if b.style%2 else (1.,.59,.22),SIGN,b.style)
            pack_box(rows,(b.x,2.45,b.z-b.hz-.5),(2.2,.12,.6),(.27,.56,.55),METAL)
            if b.key[2]==0:
                pack_box(rows,(b.x-b.hx-.6,.75,b.z),(.32,.75,.32),(.76,.83,.80),METAL,2)
                pack_box(rows,(b.x-b.hx-1.,2.2,b.z+2.5),(.11,2.2,.11),(.29,.36,.37),METAL)
                pack_box(rows,(b.x-b.hx-1.,4.35,b.z+2.5),(.45,.12,.3),(1.,.82,.46),SIGN)
            if b.key[2]==3:
                pack_box(rows,(b.x+b.hx+.65,.75,b.z+1),(.15,.75,.15),(.38,.26,.16),WOOD)
                pack_box(rows,(b.x+b.hx+.65,2.,b.z+1),(.85,.85,.75),(.30,.50,.33),LEAF)
        ix,iz=math.floor(character.x/BLOCK),math.floor(character.z/BLOCK)
        for dz in range(-1,2):
            for dx in range(-1,2):
                ox,oz=(ix+dx)*BLOCK,(iz+dz)*BLOCK
                for k in range(2):
                    t=(time*.9+random01(ix+dx,iz+dz,city.seed,k+20)*72)%72
                    edge=int(t//18); s=t%18
                    pos=((4+s,4),(22,4+s),(22-s,22),(4,22-s))[edge]
                    person(rows,ox+pos[0],oz+pos[1],time+k,(.48,.46+k*.12,.39))
        # Signals stop vehicles before junctions; this is demonstration traffic, not full AI.
        for axis in (0,1):
            for lane in range(-1,2):
                center=(iz+lane)*BLOCK if axis==0 else (ix+lane)*BLOCK
                for k in range(3):
                    progress=(time*3.2+k*17)%78-39
                    along=(ix if axis==0 else iz)*BLOCK+progress
                    red=((time%16)<8) != (axis==0)
                    offset=along%BLOCK
                    if red and 20<offset<25: along-=offset-20
                    x,z=(along,center-1.5) if axis==0 else (center+1.5,along)
                    half=(1.65,.48,.7) if axis==0 else (.7,.48,1.65)
                    color=((.87,.86,.78),(.25,.50,.58),(.74,.47,.25))[k]
                    pack_box(rows,(x,.65,z),half,color,CAR,axis)
                    pack_box(rows,(x,1.28,z),(.8,.24,.62) if axis==0 else (.62,.24,.8),(.16,.32,.39),GLASS)
    person(rows,character.x,character.z,time,(.36,.90,.93),character.height,character.phase)
    pack_box(rows,(character.x,1.3+character.height,character.z-.23),(.28,.08,.08),(1.,.64,.22),PERSON)
    if len(rows)>MAX_BOXES: raise RuntimeError(f"Scene exceeded {MAX_BOXES} boxes")
    data=np.zeros((MAX_BOXES,3,4),dtype="f4")
    data[:len(rows)]=rows
    return data,len(rows)
