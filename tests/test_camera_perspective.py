import math
import unittest
from glyphworld.camera import Camera
from glyphworld.character import Character
from glyphworld.scene import City

class PerspectiveTests(unittest.TestCase):
    def test_basis_orthonormal(self):
        camera=Camera(yaw=.8,pitch=.4)
        pose=camera.pose(Character(),City())
        axes=[pose[k] for k in ("camera_forward","camera_right","camera_up")]
        for a in axes: self.assertAlmostEqual(sum(x*x for x in a),1.)
        for i in range(3):
            for j in range(i): self.assertAlmostEqual(sum(a*b for a,b in zip(axes[i],axes[j])),0.)
    def test_movement_rotates_with_view(self):
        x,z=Camera(yaw=math.pi/2).movement(0,1)
        self.assertAlmostEqual(x,1.);self.assertAlmostEqual(z,0.)
    def test_first_person_eye(self):
        c=Character();c.height=.5
        self.assertEqual(Camera(first_person=True).pose(c,City())["camera_origin"],(c.x,2.15,c.z))
    def test_camera_arm_collision(self):
        city=City();c=Character();c.x,c.z=4.,8.
        cam=Camera(yaw=-math.pi/2);cam.snap(c)
        origin=cam.pose(c,city)["camera_origin"]
        self.assertFalse(city.blocked(origin[0],origin[2],.18))
        self.assertLess(math.dist(origin,(c.x,1.65,c.z)),4.5)
    def test_pitch_clamped(self):
        cam=Camera();cam.look(0,100000)
        self.assertEqual(cam.pitch,-1.1)
