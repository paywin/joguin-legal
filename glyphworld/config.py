from dataclasses import dataclass
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    width: int = 1280
    height: int = 720
    cell_width: int = 6
    cell_height: int = 9
    vsync: bool = True
    seed: int = 42
    rain: bool = True
    lighting: bool = True
    zoom: float = 1.0
    exposure: float = 1.7
    temporal_threshold: float = 0.045
    font: str = ""

    def __post_init__(self):
        for name in ("vsync", "rain", "lighting"):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"{name} must be true or false")
        for name in ("width", "height", "cell_width", "cell_height"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.width > 3840 or self.height > 2160:
            raise ValueError("Maximum framebuffer size is 3840x2160")
        if not 3 <= self.cell_width <= 24 or not 5 <= self.cell_height <= 36:
            raise ValueError("Cell size outside supported range")
        if not 0.65 <= self.zoom <= 1.8:
            raise ValueError("zoom must be between 0.65 and 1.8")
        if not 0.1 <= self.exposure <= 4 or not 0 <= self.temporal_threshold <= 0.2:
            raise ValueError("Invalid exposure or temporal threshold")
        if not isinstance(self.seed, int) or not 0 <= self.seed < 1_000_000:
            raise ValueError("seed must be an integer in [0, 1000000)")


def load_config(path=ROOT / "config.toml"):
    with Path(path).open("rb") as handle:
        data = tomllib.load(handle)
    allowed = {"display": {"width", "height", "cell_width", "cell_height", "vsync"},
               "world": {"seed", "rain", "lighting", "zoom"},
               "render": {"exposure", "temporal_threshold", "font"}}
    values = {}
    for section, entries in data.items():
        if section not in allowed or set(entries) - allowed[section]:
            raise ValueError(f"Unknown configuration keys in {section}")
        values.update(entries)
    return Config(**values)


def grid_size(width, height, cell_width, cell_height):
    """Ceil division covers partial cells on resized framebuffers."""
    return ((width + cell_width - 1) // cell_width,
            (height + cell_height - 1) // cell_height)
