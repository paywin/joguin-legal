import math
from pathlib import Path
import tempfile
import unittest
import numpy as np
from glyphworld.config import Config, grid_size, load_config
from glyphworld.camera import Camera
from glyphworld.character import Character
from glyphworld.lighting import Atmosphere
from glyphworld.scene import world_palette
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
        for _ in range(60): a.update(2,1/60)
        for _ in range(120): b.update(2,1/120)
        self.assertAlmostEqual(a.x,b.x,places=12)
        self.assertLess(a.x,2.16)

    def test_camera_zoom_is_bounded(self):
        camera=Camera()
        camera.zoom_by(100); self.assertEqual(camera.zoom,1.8)
        camera.zoom_by(.0001); self.assertEqual(camera.zoom,.65)

    def test_character_continuous_and_pause_zero_dt(self):
        character=Character()
        for _ in range(60): character.update(1/60)
        self.assertAlmostEqual(character.x,.075)
        before=(character.x,character.phase,character.bob)
        character.update(0)
        self.assertEqual(before,(character.x,character.phase,character.bob))
        self.assertTrue(0 <= character.bob <= .003)

    def test_atmosphere_pause(self):
        atmosphere=Atmosphere()
        atmosphere.update(1); atmosphere.update(0)
        self.assertEqual(atmosphere.time,1)

    def test_palette_seed_reproducible_and_bounded(self):
        self.assertEqual(world_palette(42),world_palette(42))
        self.assertNotEqual(world_palette(42),world_palette(43))
        self.assertTrue(all(0<x<1 for x in world_palette(42)))

    def test_atlas_contains_every_symbol_with_blank_margins(self):
        pixels,coverage=build_atlas()
        self.assertEqual(pixels.shape,(TILE[1],TILE[0]*len(GLYPHS)))
        self.assertEqual(len(GLYPHS),len(set(GLYPHS)))
        self.assertTrue(np.all(coverage>0))
        self.assertTrue(np.all(coverage<.7))
        self.assertGreater(float((pixels==0).mean()),.5)
        self.assertEqual(GLYPHS[13:17],'-|/\\')


if __name__=='__main__': unittest.main()
