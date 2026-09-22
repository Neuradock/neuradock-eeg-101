"""Minimal compatibility profile for the pinned NeuraDock quality functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class _Quality:
    outlier_absolute_amplitude: float = 100.0
    bad_channel_segment_ratio: float = 0.4


@dataclass(frozen=True)
class _Profile:
    sampling_rate_hz: int = 250
    channels: tuple[str, ...] = ("CP5", "CP6", "PO3", "PO4", "O1", "Oz", "O2")
    quality: _Quality = _Quality()


PROFILE = _Profile()
