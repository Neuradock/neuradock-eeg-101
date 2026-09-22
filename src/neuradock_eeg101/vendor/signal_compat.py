"""SciPy bindings expected by the pinned NeuraDock quality functions."""

from scipy.signal import butter, filtfilt, welch

__all__ = ["butter", "filtfilt", "welch"]
