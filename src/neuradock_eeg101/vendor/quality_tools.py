"""Two functions vendored verbatim from the pinned official NeuraDock source.

See QUALITY_TOOLS_PROVENANCE.json and NEURADOCK_MIT_LICENSE.txt in this directory.
"""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

from .profile import PROFILE
from .signal_compat import butter, filtfilt, welch


def eeg_quality_check(
    eeg_data: np.ndarray,
    fs: int = PROFILE.sampling_rate_hz,
) -> Tuple[Tuple[np.ndarray, np.ndarray, np.ndarray], np.ndarray]:
    """Filter EEG and compute 50 Hz, EMG-band, and outlier metrics per second."""

    matrix = np.asarray(eeg_data, dtype=float)
    if matrix.ndim != 2:
        raise ValueError("eeg_quality_check expects shape (channels, samples).")
    if matrix.shape[1] < fs:
        raise ValueError("Signal quality workflow requires at least one full second.")

    nyquist = 0.5 * fs
    b_filter, a_filter = butter(
        4, [1.0 / nyquist, 50.0 / nyquist], btype="band"
    )
    filtered = filtfilt(b_filter, a_filter, matrix, axis=1)

    segment_length = fs
    n_segments = matrix.shape[1] // segment_length
    metrics = [
        np.zeros((matrix.shape[0], n_segments), dtype=float) for _ in range(3)
    ]
    for channel_index in range(matrix.shape[0]):
        for segment_index in range(n_segments):
            start = segment_index * segment_length
            segment = filtered[channel_index, start : start + segment_length]
            frequencies, psd = welch(
                segment, fs=fs, nperseg=min(len(segment), fs * 2)
            )
            metrics[0][channel_index, segment_index] = np.sum(
                psd[(frequencies >= 49.0) & (frequencies <= 51.0)]
            )
            metrics[1][channel_index, segment_index] = np.sum(
                psd[(frequencies >= 20.0) & (frequencies <= 40.0)]
            )
            metrics[2][channel_index, segment_index] = np.sum(
                (segment <= -PROFILE.quality.outlier_absolute_amplitude)
                | (segment >= PROFILE.quality.outlier_absolute_amplitude)
            )
    return (metrics[0], metrics[1], metrics[2]), filtered


def clean_eeg_data(
    eeg_data: np.ndarray,
    metrics: Tuple[np.ndarray, np.ndarray, np.ndarray],
    thresholds: Tuple[float, float, float],
    segment_length: int = PROFILE.sampling_rate_hz,
    bad_channel_ratio: float = PROFILE.quality.bad_channel_segment_ratio,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, object]]:
    """Reject noisy segments while excluding globally bad channels from voting."""

    matrix = np.asarray(eeg_data, dtype=float)
    if matrix.ndim != 2:
        raise ValueError("clean_eeg_data expects shape (channels, samples).")

    n_segments = metrics[0].shape[1]
    line_bad = metrics[0] > thresholds[0]
    emg_bad = metrics[1] > thresholds[1]
    outlier_bad = metrics[2] > thresholds[2]
    issue_mask = line_bad | emg_bad | outlier_bad
    bad_ratios = np.mean(issue_mask, axis=1) if n_segments else np.zeros(matrix.shape[0])
    bad_indices = np.where(bad_ratios > bad_channel_ratio)[0]
    good_indices = np.where(bad_ratios <= bad_channel_ratio)[0]

    if len(good_indices):
        rejected_segments = np.any(issue_mask[good_indices], axis=0)
    else:
        rejected_segments = np.zeros(n_segments, dtype=bool)

    rejected_points = np.repeat(rejected_segments, segment_length)
    if len(rejected_points) < matrix.shape[1]:
        rejected_points = np.concatenate(
            [
                rejected_points,
                np.zeros(matrix.shape[1] - len(rejected_points), dtype=bool),
            ]
        )
    else:
        rejected_points = rejected_points[: matrix.shape[1]]

    keep_mask = ~rejected_points
    clean = matrix[:, keep_mask]
    channel_names = list(PROFILE.channels)
    info = {
        "bad_channels": bad_indices.tolist(),
        "bad_channel_names": [channel_names[index] for index in bad_indices],
        "channel_bad_ratios": {
            channel_names[index]: float(bad_ratios[index])
            for index in range(matrix.shape[0])
        },
        "retention_rate": float(clean.shape[1] / max(matrix.shape[1], 1)),
        "rejected_segments_count": int(np.sum(rejected_segments)),
        "rejected_segment_indices": np.where(rejected_segments)[0].tolist(),
        "thresholds": {
            "power_50hz": thresholds[0],
            "emg_power": thresholds[1],
            "outlier_count": thresholds[2],
        },
    }
    return clean, keep_mask, info
