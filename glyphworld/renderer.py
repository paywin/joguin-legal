"""Three fixed draw calls per frame; textures own the glyph field on the GPU."""
from pathlib import Path
import moderngl
from .atlas import build_atlas, GLYPHS
from .config import grid_size
from .scene import city_geometry, MAX_BOXES

SHADERS = Path(__file__).with_name("shaders")


class Renderer:
    def __init__(self, ctx, config):
        self.ctx, self.config = ctx, config
        self.cell = (config.cell_width, config.cell_height)
        self.debug = 0
        self.targets = []
        self.programs, self.vaos = {}, {}
        vertex = (SHADERS / "fullscreen.vert").read_text(encoding="utf-8")
        for name in ("scene", "field", "glyph"):
            program = ctx.program(vertex_shader=vertex,
                                  fragment_shader=(SHADERS / f"{name}.frag").read_text(encoding="utf-8"))
            self.programs[name] = program
            self.vaos[name] = ctx.vertex_array(program, [])
        pixels, self.coverage = build_atlas(config.font)
        self.atlas = ctx.texture((pixels.shape[1], pixels.shape[0]), 1, pixels.tobytes())
        self.atlas.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.atlas.repeat_x = self.atlas.repeat_y = False
        self.geometry = ctx.texture((3, MAX_BOXES), 4, dtype="f4")
        self.geometry.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.exposure = config.exposure
        self.resize(config.width, config.height)

    def uniforms(self, name, **values):
        for key, value in values.items():
            if key in self.programs[name]:
                self.programs[name][key].value = value

    def texture(self, size):
        tex = self.ctx.texture(size, 4, dtype="f2")
        tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        tex.repeat_x = tex.repeat_y = False
        self.targets.append(tex)
        return tex

    def resize(self, width, height):
        for target in reversed(self.targets):
            target.release()
        self.targets.clear()
        self.size = (max(1, width), max(1, height))
        self.grid = grid_size(*self.size, *self.cell)
        scene_size = tuple(x * 2 for x in self.grid)
        self.scene = self.texture(scene_size)
        self.info = self.texture(scene_size)
        self.scene_fbo = self.ctx.framebuffer([self.scene, self.info])
        self.targets.append(self.scene_fbo)
        self.fields = [self.texture(self.grid), self.texture(self.grid)]
        self.field_fbos = [self.ctx.framebuffer([tex]) for tex in self.fields]
        self.targets.extend(self.field_fbos)
        for fbo in self.field_fbos:
            fbo.clear()
        self.index, self.history_valid = 0, False
        self.gpu_bytes = (scene_size[0]*scene_size[1]*16 +
                          self.grid[0]*self.grid[1]*16 + self.atlas.size[0]*self.atlas.size[1] + MAX_BOXES*48)

    def density(self, direction):
        presets = [(4, 6), (5, 7), (6, 9), (8, 12), (10, 15)]
        index = min(range(len(presets)), key=lambda i: abs(presets[i][0]-self.cell[0]))
        self.cell = presets[min(len(presets)-1, max(0, index+direction))]
        self.resize(*self.size)

    def render(self, camera, character, atmosphere, city):
        boxes, count = city_geometry(city, character, atmosphere.time)
        self.geometry.write(boxes.tobytes())
        self.geometry.use(4)
        self.scene_fbo.use()
        self.ctx.viewport = (0, 0, *self.scene.size)
        self.uniforms("scene", resolution=self.size, time=atmosphere.time,
                      geometry=4, box_count=count, camera_position=(camera.x,camera.z),
                      player_position=(character.x,character.z), zoom=camera.zoom,
                      daylight=atmosphere.daylight, interior=city.interior is not None,
                      rain=atmosphere.rain, lighting=atmosphere.lighting)
        self.vaos["scene"].render(vertices=3)
        self.field_fbos[self.index].use()
        self.ctx.viewport = (0, 0, *self.grid)
        self.scene.use(0)
        self.info.use(1)
        self.fields[1-self.index].use(2)
        self.uniforms("field", scene=0, info=1, previous=2, grid=self.grid,
                      threshold=self.config.temporal_threshold, history_valid=self.history_valid)
        self.vaos["field"].render(vertices=3)
        self.ctx.screen.use()
        self.ctx.viewport = (0, 0, *self.size)
        self.atlas.use(0)
        self.fields[self.index].use(1)
        self.scene.use(2)
        self.info.use(3)
        self.uniforms("glyph", atlas=0, field=1, scene=2, info=3,
                      grid=self.grid, resolution=self.size, glyph_count=float(len(GLYPHS)),
                      exposure=self.exposure, debug_view=self.debug)
        self.vaos["glyph"].render(vertices=3)
        self.index = 1-self.index
        self.history_valid = True

    def capture(self, path):
        from PIL import Image
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.frombytes("RGB", self.size, self.ctx.screen.read(components=3, alignment=1))
        image.transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(path)

    def release(self):
        for item in reversed(self.targets):
            item.release()
        self.atlas.release()
        self.geometry.release()
        for vao in self.vaos.values():
            vao.release()
        for program in self.programs.values():
            program.release()


