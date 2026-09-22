"""Teaching-oriented EEG utilities for the NeuraDock EEG 101 course."""

from .profile import DeviceProfile, load_profile
from .recording import EEGRecording

__all__ = ["DeviceProfile", "EEGRecording", "load_profile"]
__version__ = "0.1.0"
