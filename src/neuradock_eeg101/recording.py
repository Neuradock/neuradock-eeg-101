from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import numpy as np


@dataclass
class EEGRecording:
    data: np.ndarray
    sample_rate_hz: float
    channels: tuple[str, ...]
    amplitude_unit: str = "uV"
    timestamps: np.ndarray | None = None
    markers: np.ndarray | None = None
    source_mode: str = "replay"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.data = np.asarray(self.data, dtype=float)
        if self.data.ndim != 2:
            raise ValueError("EEG data must have shape channels x samples")
        if self.data.shape[0] != len(self.channels):
            raise ValueError("Channel labels do not match the data rows")
        if not np.isfinite(self.data).all():
            raise ValueError("EEG data contains non-finite values")
        if self.sample_rate_hz <= 0:
            raise ValueError("Sample rate must be positive")
        n = self.data.shape[1]
        if self.timestamps is not None:
            self.timestamps = np.asarray(self.timestamps)
            if self.timestamps.shape != (n,):
                raise ValueError("Timestamps must contain one value per sample")
        if self.markers is not None:
            self.markers = np.asarray(self.markers, dtype=object)
            if self.markers.shape != (n,):
                raise ValueError("Markers must contain one value per sample")

    @property
    def sample_count(self) -> int:
        return int(self.data.shape[1])

    @property
    def duration_s(self) -> float:
        return self.sample_count / float(self.sample_rate_hz)

    def channel_indices(self, names: tuple[str, ...] | list[str]) -> list[int]:
        return [self.channels.index(name) for name in names]
