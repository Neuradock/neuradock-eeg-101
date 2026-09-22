"""Strict, source-faithful reader used by the visible Lesson 2 walkthrough."""

from __future__ import annotations

from pathlib import Path
import re

import numpy as np


def _validated_header(line: str) -> tuple[list[str], list[int], int]:
    header = [field.strip() for field in line.strip().split(",")]
    for samples_per_packet in (1, 5):
        expected = ["HEADER_DEF", "T", "P"]
        for _ in range(samples_per_packet):
            expected.extend(["C"] * 7 + ["0"])
        if header == expected:
            # Data rows omit HEADER_DEF, so header positions are shifted left by one.
            channel_indices = [index - 1 for index, field in enumerate(header) if field == "C"]
            return header, channel_indices, samples_per_packet
    raise ValueError(
        "Header must be exactly HEADER_DEF,T,P followed by one or five groups "
        "of seven C fields and one reserved 0 field."
    )


def _malformed(line_number: int, reason: str) -> dict[str, object]:
    return {"line_number": int(line_number), "reason": str(reason)}


def _strict_error(rows: list[dict[str, object]]) -> ValueError:
    first = rows[0]
    return ValueError(
        f"Found {len(rows)} malformed row(s); first is line "
        f"{first['line_number']}: {first['reason']}. "
        "Use strict=False only when you will inspect info['malformed_rows']."
    )


def data_reader(file_path: str | Path, *, strict: bool = True,
                event_prefix: str | None = None) -> tuple[np.ndarray, dict[str, object]]:
    """Read the exact public packet layout without guessing labels, units, or events."""
    path = Path(file_path)
    with path.open(encoding="utf-8-sig") as stream:
        lines = stream.read().splitlines()
    if not lines:
        raise ValueError("The recording is empty.")
    header, channel_indices, samples_per_packet = _validated_header(lines[0])
    if event_prefix is not None and not event_prefix.strip():
        raise ValueError("event_prefix must contain a visible, explicit prefix")
    expected_fields = len(header) - 1
    samples, raw_timestamps, p_fields = [], [], []
    sample_packet_indices, packet_line_numbers = [], []
    malformed_rows, events = [], []
    for line_number, line in enumerate(lines[1:], start=2):
        stripped = line.strip()
        if event_prefix is not None and stripped.startswith(event_prefix):
            label = stripped[len(event_prefix):].strip()
            if label:
                events.append({"sample_index": len(samples), "label": label,
                               "line_number": line_number})
            else:
                malformed_rows.append(_malformed(line_number, "empty explicit event label"))
            continue
        fields = [field.strip() for field in stripped.split(",")]
        if not stripped or len(fields) != expected_fields:
            malformed_rows.append(_malformed(
                line_number, f"expected {expected_fields} fields, received {len(fields)}"))
            continue
        try:
            packet = [[float(fields[index]) for index in
                       channel_indices[group * 7:(group + 1) * 7]]
                      for group in range(samples_per_packet)]
        except ValueError:
            malformed_rows.append(_malformed(line_number, "EEG field is not numeric"))
            continue
        if not np.isfinite(packet).all():
            malformed_rows.append(_malformed(line_number, "EEG field is not finite"))
            continue
        packet_index = len(raw_timestamps)
        samples.extend(packet)
        sample_packet_indices.extend([packet_index] * samples_per_packet)
        raw_timestamps.append(fields[0])
        p_fields.append(fields[1])
        packet_line_numbers.append(line_number)
    if malformed_rows and strict:
        raise _strict_error(malformed_rows)
    if not samples:
        raise ValueError("No valid seven-channel samples were found.")
    data = np.asarray(samples, dtype=float).T
    info = {
        "header": header, "channel_indices": channel_indices,
        "samples_per_packet": samples_per_packet,
        "raw_timestamps": raw_timestamps, "p_fields": p_fields,
        "packet_count": len(raw_timestamps), "malformed_rows": malformed_rows,
        "events": events, "sample_packet_indices": sample_packet_indices,
        "packet_line_numbers": packet_line_numbers,
    }
    return data, info


def _clock_hms_ms_to_seconds(value: str) -> float:
    match = re.fullmatch(r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})", value.strip())
    if match is None:
        raise ValueError("expected HH:MM:SS.mmm")
    hour, minute, second, millisecond = (int(part) for part in match.groups())
    if hour > 23 or minute > 59 or second > 59:
        raise ValueError("clock component is outside its valid range")
    return hour * 3600.0 + minute * 60.0 + second + millisecond / 1000.0


def inspect_timing(
    raw_timestamps: list[str] | tuple[str, ...],
    *,
    timestamp_format: str = "unknown",
) -> dict[str, object]:
    """Summarize packet clocks without fabricating within-packet sample times."""
    raw = [str(value) for value in raw_timestamps]
    result: dict[str, object] = {
        "timestamp_format": timestamp_format,
        "packet_count": len(raw),
        "within_packet_interpolation": False,
        "midnight_rollover_applied": False,
    }
    if timestamp_format == "unknown":
        return {**result, "status": "uninterpreted", "valid_count": 0,
                "invalid_count": len(raw), "monotonic_increasing": None,
                "first_to_last_span_s": None, "median_packet_interval_s": None,
                "minimum_packet_interval_s": None, "maximum_packet_interval_s": None,
                "duplicate_interval_count": None, "backward_interval_count": None,
                "nonpositive_interval_count": None}
    if timestamp_format not in {"clock_hms_ms", "seconds"}:
        raise ValueError("timestamp_format must be clock_hms_ms, seconds, or unknown")
    parsed: list[float] = []
    invalid_indices: list[int] = []
    for index, value in enumerate(raw):
        try:
            parsed_value = (_clock_hms_ms_to_seconds(value)
                            if timestamp_format == "clock_hms_ms" else float(value))
            if not np.isfinite(parsed_value):
                raise ValueError("timestamp is not finite")
            parsed.append(float(parsed_value))
        except ValueError:
            invalid_indices.append(index)
    if invalid_indices:
        return {**result, "status": "invalid", "valid_count": len(parsed),
                "invalid_count": len(invalid_indices),
                "first_invalid_packet_index": invalid_indices[0],
                "monotonic_increasing": None, "first_to_last_span_s": None,
                "median_packet_interval_s": None, "minimum_packet_interval_s": None,
                "maximum_packet_interval_s": None, "duplicate_interval_count": None,
                "backward_interval_count": None,
                "nonpositive_interval_count": None}
    intervals = np.diff(parsed)
    return {**result, "status": "parsed", "valid_count": len(parsed),
            "invalid_count": 0,
            "monotonic_increasing": bool(np.all(intervals > 0)),
            "first_to_last_span_s": (float(parsed[-1] - parsed[0])
                                      if len(parsed) > 1 else None),
            "median_packet_interval_s": (float(np.median(intervals))
                                           if intervals.size else None),
            "minimum_packet_interval_s": (float(np.min(intervals))
                                            if intervals.size else None),
            "maximum_packet_interval_s": (float(np.max(intervals))
                                            if intervals.size else None),
            "duplicate_interval_count": int(np.count_nonzero(intervals == 0)),
            "backward_interval_count": int(np.count_nonzero(intervals < 0)),
            "nonpositive_interval_count": int(np.count_nonzero(intervals <= 0))}


def describe_p_field(p_fields: list[str] | tuple[str, ...]) -> dict[str, object]:
    """Report modulo-256 counter evidence without interpreting P as an event."""
    raw = [str(value).strip() for value in p_fields]
    values: list[int] = []
    invalid_count = 0
    for value in raw:
        try:
            numeric = float(value)
            if not np.isfinite(numeric) or not numeric.is_integer():
                raise ValueError("P is not a finite integer value")
            values.append(int(numeric))
        except ValueError:
            invalid_count += 1
    transition_count = max(len(values) - 1, 0) if invalid_count == 0 else 0
    plus_one = (sum((right - left) % 256 == 1
                    for left, right in zip(values, values[1:]))
                if invalid_count == 0 else 0)
    in_byte_range = bool(values) and all(0 <= value <= 255 for value in values)
    counter_like = bool(transition_count and in_byte_range and plus_one == transition_count)
    return {
        "packet_count": len(raw), "integer_count": len(values),
        "invalid_count": invalid_count,
        "unique_value_count": len(set(values)) if invalid_count == 0 else None,
        "all_values_in_0_255": in_byte_range if invalid_count == 0 else None,
        "transition_count": transition_count if invalid_count == 0 else None,
        "plus_one_mod_256_count": plus_one if invalid_count == 0 else None,
        "plus_one_mod_256_fraction": (float(plus_one / transition_count)
                                       if transition_count else None),
        "wrap_255_to_0_count": (sum(left == 255 and right == 0
                                    for left, right in zip(values, values[1:]))
                                if invalid_count == 0 else None),
        "counter_like": counter_like,
        "interpretation": ("counter-like pattern; not an experimental event label"
                           if counter_like else
                           "undetermined; not treated as an experimental event label"),
        "experimental_events_inferred": 0,
    }
