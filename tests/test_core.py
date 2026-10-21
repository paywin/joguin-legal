import math
from pathlib import Path
import tempfile
import unittest
import numpy as np
from glyphworld.config import Config, grid_size, load_config
from glyphworld.camera import Camera
from glyphworld.character import Character
from glyphworld.lighting import Atmosphere
from glyphworld.scene import City, city_geometry, MAX_BOXES, BLOCK
from glyphworld.atlas import build_atlas, GLYPHS, TILE


class CoreTests(unittest.TestCase):
    def test_grid_covers_non_multiple_framebuffer(self):
        for width, height in [(1280,720),(1,1),(1921,1081)]:
            columns, rows = grid_size(width,height,6,9)
            self.assertGreaterEqual(columns*6,width)
            self.assertLess((columns-1)*6,width)
            self.assertGreaterEqual(rows*9,height)

    def test_config_rejects_invalid_values(self):
        for kwargs in ({"width":0},{"cell_width":1},{"zoom":0},{"exposure":float('nan')},
                       {"seed":-1},{"height":5000},{"temporal_threshold":-0.01}):
            with self.assertRaises(ValueError):
                Config(**kwargs)

    def test_unknown_config_key_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.toml'
            path.write_text('[world]\nrainn = true\n')
            with self.assertRaises(ValueError): load_config(path)

    def test_default_config_loads(self):
        self.assertEqual(load_config().width,1280)

    def test_camera_is_frame_rate_independent_for_fixed_target(self):
        a,b=Camera(),Camera()
        for _ in range(60): a.update((2,5),1/60)
        for _ in range(120): b.update((2,5),1/120)
        self.assertAlmostEqual(a.x,b.x,places=12)
        self.assertAlmostEqual(a.z,b.z,places=12)
        self.assertLess(a.x,2)

    def test_camera_zoom_is_bounded(self):
        camera=Camera()
        camera.zoom_by(100); self.assertEqual(camera.zoom,1.8)
        camera.zoom_by(.0001); self.assertEqual(camera.zoom,.65)

    def test_character_continuous_and_pause_zero_dt(self):
        character=Character()
        for _ in range(60): character.update(1/60,direction=(1,0))
        self.assertAlmostEqual(character.x,3.5)
        before=(character.x,character.phase,character.bob)
        character.update(0)
        self.assertEqual(before,(character.x,character.phase,character.bob))
        self.assertTrue(0 <= character.bob <= .035)

    def test_atmosphere_pause(self):
        atmosphere=Atmosphere()
        atmosphere.update(1); atmosphere.update(0)
        self.assertEqual(atmosphere.time,1)

    def test_city_seed_reproducible_in_both_directions(self):
        self.assertEqual(City(42).block(-2,3),City(42).block(-2,3))
        self.assertNotEqual(City(42).block(-2,3),City(43).block(-2,3))

    def test_atlas_contains_every_symbol_with_blank_margins(self):
        pixels,coverage=build_atlas()
        self.assertEqual(pixels.shape,(TILE[1],TILE[0]*len(GLYPHS)))
        self.assertEqual(len(GLYPHS),len(set(GLYPHS)))
        self.assertTrue(np.all(coverage>0))
        self.assertTrue(np.all(coverage<.85))
        self.assertGreater(float((pixels==0).mean()),.25)
        self.assertEqual(GLYPHS[13:17],'-|/\\')

    def test_diagonal_speed_matches_axial_speed(self):
        a,b=Character(),Character()
        a.update(1,direction=(1,0)); b.update(1,direction=(1,1))
        self.assertAlmostEqual(math.hypot(a.x,a.z-8),math.hypot(b.x,b.z-8))

    def test_jump_returns_to_ground_and_cannot_double_jump(self):
        a,b=Character(),Character()
        a.update(.1,jump=True); b.update(.1,jump=True)
        self.assertGreater(a.height,0)
        a.update(.1,jump=True); b.update(.1,jump=False)
        self.assertEqual(a.height,b.height)
        for _ in range(120): a.update(1/60)
        self.assertEqual((a.height,a.vertical_speed),(0,0))

    def test_walls_stop_player_even_with_large_step(self):
        city=City(); b=city.block(0,0)[0]
        x,z=city.move(b.x,b.z-b.hz-1,0,20)
        self.assertLessEqual(z,b.z-b.hz-.28)
        self.assertFalse(city.blocked(x,z))

    def test_road_crosses_positive_and_negative_chunks(self):
        city=City(); x,z=city.move(0,8,0,160)
        self.assertAlmostEqual(z,168)
        x,z=city.move(x,z,0,-320)
        self.assertAlmostEqual(z,-152)

    def test_alley_allows_sideways_exploration(self):
        city=City()
        x,z=city.move(13,0,0,26)
        self.assertAlmostEqual(z,26)
        self.assertFalse(city.blocked(13,13))

    def test_door_entry_exit_and_interior_walls(self):
        city=City(); player=Character()
        self.assertFalse(city.interact(player))
        door=city.block(0,0)[0]
        player.x,player.z=door.door
        self.assertTrue(city.interact(player))
        self.assertIsNotNone(city.interior)
        self.assertTrue(city.blocked(6,0))
        self.assertTrue(city.interact(player))
        self.assertEqual((player.x,player.z),door.door)
        self.assertIsNone(city.interior)

    def test_exit_requires_return_to_door(self):
        city=City(); player=Character()
        player.x,player.z=city.block(0,0)[0].door
        city.interact(player)
        player.z=2
        self.assertFalse(city.interact(player))

    def test_clock_wrap_and_daylight(self):
        a=Atmosphere(hour=23,day_seconds=240)
        a.update(20)
        self.assertAlmostEqual(a.hour,1)
        self.assertLess(Atmosphere(hour=0).daylight,Atmosphere(hour=12).daylight)
        before=a.hour; a.cycle=False; a.update(100)
        self.assertEqual(a.hour,before)

    def test_geometry_stable_bounded_and_animated(self):
        city=City(); player=Character()
        a,n=city_geometry(city,player,0)
        b,m=city_geometry(city,player,1)
        self.assertEqual(a.shape,(MAX_BOXES,3,4))
        self.assertEqual(n,m)
        self.assertLessEqual(n,MAX_BOXES)
        self.assertTrue(np.all(np.isfinite(a)))
        self.assertTrue(np.all(a[:n,1,:3]>a[:n,0,:3]))
        self.assertFalse(np.array_equal(a,b))

    def test_chunk_cache_is_bounded(self):
        city=City()
        for n in range(150): city.block(n,n)
        self.assertLessEqual(city.block.cache_info().currsize,64)


if __name__=='__main__': unittest.main()
