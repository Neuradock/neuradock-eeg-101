"""Lesson 4: Welch PSD and absolute alpha power on uninterrupted QC windows.

The per-channel Welch loop follows ``calculate_eeg_psd`` in the supplied
``S2/S2_CP_evaluations_share.ipynb``. The old file reader and data selector are
replaced by an already selected *continuous* segment; no new filter is applied.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import trapezoid
from scipy.signal import welch


FIXED_FS = 250
CHANNEL_COUNT = 7
ALPHA_BAND_HZ = (8.0, 13.0)


def _sample_count(seconds: float, fs: int, name: str) -> int:
    if isinstance(seconds, (bool, np.bool_)) or not np.isscalar(seconds):
        raise ValueError(f"{name} must be a positive duration in seconds.")
    try:
        numeric = float(seconds)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive duration in seconds.") from exc
    exact_samples = numeric * fs
    rounded_samples = round(exact_samples) if np.isfinite(exact_samples) else 0
    if (not np.isfinite(exact_samples) or exact_samples <= 0 or rounded_samples < 1
            or not np.isclose(exact_samples, rounded_samples, atol=1e-9, rtol=0)):
        raise ValueError(f"{name} must be positive and an exact number of samples at {fs} Hz.")
    return int(rounded_samples)


def _fixed_fs(fs: int) -> int:
    if isinstance(fs, bool) or not isinstance(fs, (int, np.integer)) or fs != FIXED_FS:
        raise ValueError("This course PSD workflow requires integer fs=250 Hz.")
    return FIXED_FS


def calculate_segment_psd(
    segment: np.ndarray, *, fs: int = FIXED_FS, welch_s: float = 2.0
) -> tuple[np.ndarray, np.ndarray]:
    """Return channels × frequencies, preserving S2's per-channel Welch loop.

    The input is one uninterrupted, already-filtered segment; the function does
    not select samples, join gaps, resample, or apply another filter.
    """
    fs = _fixed_fs(fs)
    nperseg = _sample_count(welch_s, fs, "welch_s")
    matrix = np.asarray(segment, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] < 1:
        raise ValueError("segment must have shape (channels, continuous samples).")
    if matrix.shape[1] < nperseg:
        raise ValueError("segment must contain at least fs * welch_s samples; no silent shortening.")
    if not np.isfinite(matrix).all():
        raise ValueError("segment contains non-finite values.")

    all_channel_psds = []
    freqs = None
    for i in range(matrix.shape[0]):
        channel_data = matrix[i, :]
        f, psd = welch(channel_data, fs=fs, nperseg=nperseg)
        if freqs is None:
            freqs = f
        all_channel_psds.append(psd)
    psd_data = np.array(all_channel_psds)
    return freqs, psd_data


def integrate_band(
    frequencies: np.ndarray,
    psd: np.ndarray,
    *,
    band: tuple[float, float] = ALPHA_BAND_HZ,
) -> np.ndarray:
    """Integrate PSD density on its included frequency bins, without interpolation."""
    freq = np.asarray(frequencies, dtype=float)
    density = np.asarray(psd, dtype=float)
    if freq.ndim != 1 or freq.size < 2 or not np.isfinite(freq).all():
        raise ValueError("frequencies must be a finite one-dimensional grid.")
    if freq[0] < 0 or not np.all(np.diff(freq) > 0):
        raise ValueError("frequencies must be nonnegative and strictly increasing.")
    if density.ndim not in (1, 2) or density.shape[-1] != freq.size:
        raise ValueError("psd must have a frequency axis matching frequencies.")
    if not np.isfinite(density).all() or np.any(density < 0):
        raise ValueError("psd must be finite and nonnegative.")
    if len(band) != 2:
        raise ValueError("band must contain lower and upper frequency bounds.")
    low, high = (float(value) for value in band)
    if not np.isfinite([low, high]).all() or low < 0 or low >= high:
        raise ValueError("band bounds must be finite with 0 <= low < high.")
    if low < freq[0] or high > freq[-1]:
        raise ValueError("band must fit within the PSD frequency grid.")
    selected = (freq >= low) & (freq <= high)
    if np.count_nonzero(selected) < 2:
        raise ValueError("band must contain at least two PSD bins for integration.")
    lower_index = int(np.argmin(np.abs(freq - low)))
    upper_index = int(np.argmin(np.abs(freq - high)))
    if (not np.isclose(freq[lower_index], low, atol=1e-9, rtol=0)
            or not np.isclose(freq[upper_index], high, atol=1e-9, rtol=0)):
        raise ValueError("band edges must align with PSD bins; no interpolation is applied.")
    band_slice = slice(lower_index, upper_index + 1)
    return trapezoid(density[..., band_slice], x=freq[band_slice], axis=-1)


def analyze_alpha_windows(
    filtered: np.ndarray,
    keep_mask: np.ndarray,
    bad_channel_mask: np.ndarray,
    *,
    fs: int = FIXED_FS,
    window_s: float = 4.0,
    step_s: float = 1.0,
    welch_s: float = 2.0,
    unit_confirmed: bool = False,
) -> dict[str, object]:
    """Compute absolute 8–13 Hz power only in entirely accepted 4 s windows.

    This conservative classroom rule is stricter than an 80%-retained recipe:
    a single rejected sample invalidates the entire window, so gaps are never
    spliced together. A global bad-channel candidate has no feature values.
    """
    fs = _fixed_fs(fs)
    if not isinstance(unit_confirmed, (bool, np.bool_)) or not unit_confirmed:
        raise ValueError("Confirmed microvolt units are required for alpha power in µV².")
    window_samples = _sample_count(window_s, fs, "window_s")
    step_samples = _sample_count(step_s, fs, "step_s")
    welch_samples = _sample_count(welch_s, fs, "welch_s")
    if window_samples < welch_samples:
        raise ValueError("window_s must be at least welch_s; Welch may not shorten nperseg.")
    if step_samples > window_samples:
        raise ValueError("step_s must not exceed window_s; coverage gaps need explicit design.")

    matrix = np.asarray(filtered, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != CHANNEL_COUNT:
        raise ValueError("filtered must have shape (7, samples).")
    if not np.isfinite(matrix).all():
        raise ValueError("filtered contains non-finite values.")
    n_samples = matrix.shape[1]
    if n_samples < window_samples:
        raise ValueError("Recording is shorter than one complete analysis window.")
    keep = np.asarray(keep_mask)
    bad = np.asarray(bad_channel_mask)
    if keep.shape != (n_samples,) or keep.dtype.kind != "b":
        raise ValueError("keep_mask must be a boolean array with one value per sample.")
    if bad.shape != (CHANNEL_COUNT,) or bad.dtype.kind != "b":
        raise ValueError("bad_channel_mask must be a boolean array with seven values.")
    if np.all(bad):
        raise ValueError("All channels are bad; no eligible alpha feature can be computed.")

    starts = np.arange(0, n_samples - window_samples + 1, step_samples, dtype=int)
    stops = starts + window_samples
    valid_window_mask = np.array([bool(np.all(keep[start:stop]))
                                  for start, stop in zip(starts, stops)], dtype=bool)
    if not np.any(valid_window_mask):
        raise ValueError("No fully accepted continuous analysis window is available.")

    eligible = np.flatnonzero(~bad)
    frequencies = np.fft.rfftfreq(welch_samples, d=1.0 / fs)
    psd_by_window = np.full(
        (CHANNEL_COUNT, len(starts), len(frequencies)), np.nan, dtype=float)
    alpha_power_uv2 = np.full((CHANNEL_COUNT, len(starts)), np.nan, dtype=float)
    coverage_mask = np.zeros(n_samples, dtype=bool)
    for index in np.flatnonzero(valid_window_mask):
        start, stop = int(starts[index]), int(stops[index])
        window_freq, window_psd = calculate_segment_psd(
            matrix[eligible, start:stop], fs=fs, welch_s=welch_s)
        if not np.array_equal(window_freq, frequencies):
            raise RuntimeError("Welch frequency grid changed between accepted windows.")
        psd_by_window[eligible, index, :] = window_psd
        alpha_power_uv2[eligible, index] = integrate_band(window_freq, window_psd)
        coverage_mask[start:stop] = True

    accepted_samples = int(np.count_nonzero(keep))
    coverage_samples = int(np.count_nonzero(coverage_mask))
    summary = {
        "status": "descriptive_features_available",
        "sample_rate_hz": fs,
        "amplitude_unit": "µV",
        "psd_unit": "µV²/Hz",
        "alpha_power_unit": "µV²",
        "alpha_band_hz": [8.0, 13.0],
        "feature": "absolute_alpha_power_only",
        "alpha_peak_frequency_reported": False,
        "welch_seconds": float(welch_s),
        "welch_samples": welch_samples,
        "window_seconds": float(window_s),
        "window_samples": window_samples,
        "step_seconds": float(step_s),
        "step_samples": step_samples,
        "window_acceptance_rule": "all samples pass the Lesson 3 temporal gate",
        "sample_count": n_samples,
        "total_windows": int(len(starts)),
        "valid_windows": int(np.count_nonzero(valid_window_mask)),
        "invalid_windows": int(np.count_nonzero(~valid_window_mask)),
        "gate_accepted_samples": accepted_samples,
        "gate_accepted_duration_s": float(accepted_samples / fs),
        "coverage_samples": coverage_samples,
        "coverage_duration_s": float(coverage_samples / fs),
        "coverage_fraction_of_recording": float(coverage_samples / n_samples),
        "eligible_channel_indices": eligible.tolist(),
        "bad_channel_indices": np.flatnonzero(bad).tolist(),
        "channel_labels": [f"Ch{index}" for index in range(1, CHANNEL_COUNT + 1)],
        "timeline_preserved": True,
        "interpretation": (
            "Sensor-column descriptive alpha power only; no condition, montage, "
            "clinical, cognitive-state, or causal inference."
        ),
    }
    return {
        "starts": starts,
        "stops": stops,
        "centers_s": (starts + window_samples / 2.0) / fs,
        "valid_window_mask": valid_window_mask,
        "alpha_power_uv2": alpha_power_uv2,
        "frequencies": frequencies,
        "psd_by_window": psd_by_window,
        "coverage_mask": coverage_mask,
        "summary": summary,
    }
