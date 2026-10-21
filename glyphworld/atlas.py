"""Single monochrome atlas, generated once, using a redistributable-free system font."""
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Stable indices shared with field.frag. ASCII guarantees broad font coverage.
GLYPHS = ".,:;!il+ox%#@-|/\\vY*()[]=~^"
TILE = (20, 28)


def resolve_font(custom=""):
    if custom:
        return ImageFont.truetype(str(Path(custom).expanduser()), 24)
    candidates = [Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/consolab.ttf",
                  Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/consola.ttf",
                  Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
                  Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
                  Path("/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf")]
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), 24)
    raise RuntimeError("No monospace font found. Set render.font in config.toml to a .ttf file.")


def build_atlas(custom=""):
    font = resolve_font(custom)
    width, height = TILE
    atlas = Image.new("L", (len(GLYPHS) * width, height))
    draw = ImageDraw.Draw(atlas)
    for index, glyph in enumerate(GLYPHS):
        box = draw.textbbox((0, 0), glyph, font=font)
        glyph_width = box[2] - box[0]
        draw.text((index * width + (width - glyph_width) // 2 - box[0], -1),
                  glyph, fill=255, font=font)
    # OpenGL origin is bottom-left.
    pixels = np.asarray(atlas.transpose(Image.Transpose.FLIP_TOP_BOTTOM)).copy()
    coverage = pixels.reshape(height, len(GLYPHS), width).mean(axis=(0, 2)) / 255
    if np.any(coverage <= 0):
        raise RuntimeError("Font produced an empty glyph")
    return pixels, coverage.astype("f4")
