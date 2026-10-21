from collections import deque
import numpy as np
import psutil


class Metrics:
    def __init__(self):
        self.samples = deque(maxlen=600)
        self.process = psutil.Process()

    def add(self, seconds):
        if seconds > 0:
            self.samples.append(seconds)

    def summary(self):
        values = np.asarray(self.samples, dtype=float)
        return {"frames": len(values),
                "fps": float(1 / values.mean()) if len(values) else 0,
                "frame_ms": float(values.mean() * 1000) if len(values) else 0,
                "p95_ms": float(np.percentile(values, 95) * 1000) if len(values) else 0,
                "rss_mib": self.process.memory_info().rss / 1024**2}
