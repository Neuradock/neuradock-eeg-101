"""Safety wrapper around the pinned official NeuraDock quality functions."""

from __future__ import annotations

from typing import Iterable

import numpy as np

from .vendor.quality_tools import clean_eeg_data, eeg_quality_check


CHANNEL_LABELS = tuple(f"Ch{index}" for index in range(1, 8))
FIXED_FS = 250
BAD_CHANNEL_RATIO = 0.4
OUTLIER_ABSOLUTE_UV = 100.0


def _validated_data(data: np.ndarray, fs: int) -> np.ndarray:
    matrix = np.asarray(data, dtype=float)
    if isinstance(fs, bool) or not isinstance(fs, (int, np.integer)) or fs != FIXED_FS:
        raise ValueError("The pinned NeuraDock quality gate requires integer fs=250 Hz.")
    if matrix.ndim != 2 or matrix.shape[0] != 7:
        raise ValueError("Quality gating requires shape (7, samples).")
    if matrix.shape[1] < FIXED_FS:
        raise ValueError("Quality gating requires at least one complete one-second segment.")
    if not np.isfinite(matrix).all():
        raise ValueError("Quality-gate input contains non-finite values.")
    return matrix


def _validated_metrics(
    metrics: Iterable[np.ndarray], n_segments: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values = tuple(np.asarray(value, dtype=float) for value in metrics)
    if len(values) != 3 or any(value.shape != (7, n_segments) for value in values):
        raise ValueError("metrics must contain three finite arrays shaped (7, full_seconds).")
    if any(not np.isfinite(value).all() for value in values):
        raise ValueError("Quality metrics contain non-finite values.")
    return values  # type: ignore[return-value]


def _validated_thresholds(thresholds: Iterable[float]) -> tuple[float, float, float]:
    values = tuple(float(value) for value in thresholds)
    if len(values) != 3 or not np.isfinite(values).all() or any(value < 0 for value in values):
        raise ValueError("thresholds must contain three finite nonnegative values.")
    return values  # type: ignore[return-value]


def gate_from_metrics(
    data: np.ndarray,
    metrics: tuple[np.ndarray, np.ndarray, np.ndarray],
    *,
    fs: int = FIXED_FS,
    unit_confirmed: bool = False,
    thresholds: tuple[float, float, float] = (10.0, 20.0, 2.0),
    fixed_bad_channel_mask: np.ndarray | None = None,
) -> dict[str, object]:
    """Apply segment voting without shortening or interpolating the input timeline."""
    if not isinstance(unit_confirmed, (bool, np.bool_)):
        raise TypeError("unit_confirmed must be a boolean.")
    unit_confirmed = bool(unit_confirmed)
    matrix = _validated_data(data, fs)
    n_segments = matrix.shape[1] // fs
    checked_metrics = _validated_metrics(metrics, n_segments)
    checked_thresholds = _validated_thresholds(thresholds)
    metric_flags = tuple(metric > limit for metric, limit in zip(
        checked_metrics, checked_thresholds))
    issue_mask = metric_flags[0] | metric_flags[1] | metric_flags[2]

    _, _, official_info = clean_eeg_data(
        matrix, checked_metrics, checked_thresholds,
        segment_length=fs, bad_channel_ratio=BAD_CHANNEL_RATIO)
    derived_bad = np.zeros(7, dtype=bool)
    derived_bad[np.asarray(official_info["bad_channels"], dtype=int)] = True
    if fixed_bad_channel_mask is None:
        bad_channel_mask = derived_bad
        bad_mask_source = "derived_from_current_thresholds"
    else:
        bad_channel_mask = np.asarray(fixed_bad_channel_mask, dtype=bool)
        if bad_channel_mask.shape != (7,):
            raise ValueError("fixed_bad_channel_mask must have shape (7,).")
        bad_mask_source = "fixed_for_threshold_comparison"

    good_channel_mask = ~bad_channel_mask
    rejected_segments = (np.any(issue_mask[good_channel_mask], axis=0)
                         if np.any(good_channel_mask)
                         else np.ones(n_segments, dtype=bool))
    assessed_samples = n_segments * fs
    assessed_mask = np.zeros(matrix.shape[1], dtype=bool)
    assessed_mask[:assessed_samples] = True
    keep_mask = np.zeros(matrix.shape[1], dtype=bool)
    if unit_confirmed:
        keep_mask[:assessed_samples] = np.repeat(~rejected_segments, fs)

    accepted_samples = int(np.count_nonzero(keep_mask)) if unit_confirmed else None
    retention_rate = (float(accepted_samples / matrix.shape[1])
                      if accepted_samples is not None else None)
    assessed_retention_rate = (float(accepted_samples / assessed_samples)
                               if accepted_samples is not None else None)
    channel_issue_ratios = np.mean(issue_mask, axis=1)
    all_bad = bool(np.all(bad_channel_mask))
    if not unit_confirmed:
        status = "units_unconfirmed"
    elif all_bad or accepted_samples == 0:
        status = "unusable"
    elif np.any(bad_channel_mask) or np.any(rejected_segments) or assessed_samples < matrix.shape[1]:
        status = "warning"
    else:
        status = "pass"

    summary = {
        "status": status,
        "unit_confirmed_uv": bool(unit_confirmed),
        "quality_claim_permitted": bool(unit_confirmed),
        "sample_rate_hz": int(fs),
        "segment_seconds": 1.0,
        "segment_samples": int(fs),
        "channel_count": 7,
        "channel_labels": list(CHANNEL_LABELS),
        "sample_count": int(matrix.shape[1]),
        "segments_assessed": int(n_segments),
        "assessed_samples": int(assessed_samples),
        "unassessed_tail_samples": int(matrix.shape[1] - assessed_samples),
        "accepted_samples": accepted_samples,
        "retention_rate": retention_rate,
        "assessed_retention_rate": assessed_retention_rate,
        "rejected_segment_count": int(np.count_nonzero(rejected_segments)),
        "rejected_segment_indices": np.flatnonzero(rejected_segments).tolist(),
        "bad_channel_indices": np.flatnonzero(bad_channel_mask).tolist(),
        "bad_channel_labels": [CHANNEL_LABELS[index]
                               for index in np.flatnonzero(bad_channel_mask)],
        "bad_channel_mask_source": bad_mask_source,
        "channel_issue_ratios": [float(value) for value in channel_issue_ratios],
        "metric_flag_counts": {
            "line_noise_49_51_hz": int(np.count_nonzero(metric_flags[0])),
            "high_frequency_20_40_hz": int(np.count_nonzero(metric_flags[1])),
            "extreme_amplitude": int(np.count_nonzero(metric_flags[2])),
        },
        "thresholds": {
            "line_noise_power": checked_thresholds[0],
            "high_frequency_power": checked_thresholds[1],
            "outlier_count_per_second": checked_thresholds[2],
            "outlier_absolute_amplitude_uv": OUTLIER_ABSOLUTE_UV,
            "bad_channel_segment_ratio": BAD_CHANNEL_RATIO,
        },
        "all_channels_bad": all_bad,
        "timeline_preserved": True,
        "tail_policy": "incomplete tail is unassessed and not accepted",
        "interpretation": (
            "Screening heuristics only; flags do not diagnose artifact source or health."
        ),
    }
    return {
        "metrics": checked_metrics,
        "metric_flags": metric_flags,
        "issue_mask": issue_mask,
        "bad_channel_mask": bad_channel_mask,
        "rejected_segments": rejected_segments,
        "assessed_mask": assessed_mask,
        "keep_mask": keep_mask,
        "summary": summary,
    }


def run_quality_gate(
    data: np.ndarray,
    *,
    fs: int = FIXED_FS,
    unit_confirmed: bool = False,
    thresholds: tuple[float, float, float] = (10.0, 20.0, 2.0),
) -> dict[str, object]:
    """Compute official diagnostics once, then apply the safe timeline gate."""
    matrix = _validated_data(data, fs)
    metrics, filtered = eeg_quality_check(matrix, fs)
    result = gate_from_metrics(
        filtered, metrics, fs=fs, unit_confirmed=unit_confirmed,
        thresholds=thresholds)
    result["filtered"] = filtered
    return result
