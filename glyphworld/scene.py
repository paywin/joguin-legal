"""Compact world descriptors. No Python objects per displayed cell."""
import numpy as np


def world_palette(seed):
    rng = np.random.default_rng(seed)
    # A seed-dependent accent shared by architecture and lights.
    return tuple(float(x) for x in (np.array([0.86, 0.52, 0.22]) +
                                    rng.uniform(-0.04, 0.04, 3)))
