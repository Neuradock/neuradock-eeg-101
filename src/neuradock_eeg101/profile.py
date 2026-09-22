from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DeviceProfile:
    profile_version: str
    device: str
    hardware_revision: str
    sample_rate_hz: int
    amplitude_unit: str
    channels: tuple[str, ...]
    posterior_channels: tuple[str, ...]
    posterior_left: tuple[str, ...]
    posterior_right: tuple[str, ...]
    line_frequency_hz: float
    alpha_band_hz: tuple[float, float]
    tcp: dict[str, Any]
    quality_thresholds: dict[str, float]

    @property
    def channel_count(self) -> int:
        return len(self.channels)


def default_profile_path() -> Path:
    repository_copy = Path(__file__).resolve().parents[2] / "configs" / "neuradock-v1.json"
    if repository_copy.exists():
        return repository_copy
    return Path(__file__).resolve().parent / "data" / "neuradock-v1.json"


def load_profile(path: str | Path | None = None) -> DeviceProfile:
    source = Path(path) if path else default_profile_path()
    payload = json.loads(source.read_text(encoding="utf-8"))
    channels = tuple(payload["channels"])
    if channels != ("CP5", "CP6", "PO3", "PO4", "O1", "Oz", "O2"):
        raise ValueError("The course requires the canonical seven-channel order")
    if payload["sample_rate_hz"] != 250:
        raise ValueError("The course profile requires a 250 Hz sample rate")
    return DeviceProfile(
        profile_version=str(payload["profile_version"]),
        device=str(payload["device"]),
        hardware_revision=str(payload["hardware_revision"]),
        sample_rate_hz=int(payload["sample_rate_hz"]),
        amplitude_unit=str(payload["amplitude_unit"]),
        channels=channels,
        posterior_channels=tuple(payload["posterior_channels"]),
        posterior_left=tuple(payload["posterior_left"]),
        posterior_right=tuple(payload["posterior_right"]),
        line_frequency_hz=float(payload["line_frequency_hz"]),
        alpha_band_hz=tuple(float(x) for x in payload["alpha_band_hz"]),
        tcp=dict(payload["tcp"]),
        quality_thresholds={k: float(v) for k, v in payload["quality_thresholds"].items()},
    )
