# Canonical NeuraDock Device Profile

This course uses the checked-in profile at [`configs/neuradock-v1.json`](../configs/neuradock-v1.json). Treat it as an invariant for every tutorial and generated result. If a legacy example disagrees, keep this profile and label the example as incompatible until its acquisition metadata is confirmed.

**Historical-file boundary in Lesson 2:** the revised reading notebook inspects
the supplied S2 files without asserting that their acquisition metadata matches
this current hardware profile. Its separate, header-driven `reading.data_reader`
preserves the original EEG values, clock strings, and raw P field. It uses generic
Ch1–Ch7 column labels. The data owner confirmed these stored values are already
microvolts (µV); the historical montage and experimental conditions are unconfirmed.
The supplied P sequences are counter-like; they are not interpreted as experimental
markers. This does not redefine the public hardware profile below. The existing
`parser.parse_recording` path remains in use for the documented synthetic examples
in later lessons and is not the revised Lesson 2 reader.

## Signal layout

| Field | Course value |
|---|---|
| Device | NeuraDock EEG Workstation |
| Course profile version | 1.1 |
| Public hardware profile | v2 |
| Sample rate | 250 Hz |
| Parsed amplitude unit | µV |
| Analysis orientation | `channels × samples` |
| Nominal line frequency | 50 Hz |
| Alpha band | 8–13 Hz |

The exact zero-based channel order is:

| Index | Channel |
|---:|---|
| 0 | CP5 |
| 1 | CP6 |
| 2 | PO3 |
| 3 | PO4 |
| 4 | O1 |
| 5 | Oz |
| 6 | O2 |

The posterior set is `PO3, PO4, O1, Oz, O2`. The sparse posterior left set is `PO3, O1`; the sparse posterior right set is `PO4, O2`.

Never replace these labels with legacy names such as T5 or T6, and never reorder columns to satisfy an analysis. A header that contains seven generic channel fields describes packet shape, not independent proof of electrode placement. Historical files need acquisition provenance before they can be assigned this montage.

## Public text and TCP packet layouts

Each comma-separated data line begins with `timestamp, marker`.

### USB

A USB line contains one group of seven EEG values plus one reserved value, for at least ten fields in total:

```text
timestamp,marker,eeg0,eeg1,eeg2,eeg3,eeg4,eeg5,eeg6,reserved
```

Each valid line decodes to one sample.

### Bluetooth

A Bluetooth line contains five groups of `7 EEG + 1 reserved`, for at least 42 fields. The parser expands one line into five chronological samples. The packet marker applies to every expanded sample in the current public convention.

Within-packet timestamps may be generated as `base_timestamp + sample_index / 250` only when the timestamp is numeric and its unit is confirmed. Preserve device timestamps when available and use a monotonic host clock for software-side receipt or marker timing.

### Buffered TCP input

A single TCP `recv` may contain part of a line, one line, or many lines. The package therefore keeps a rolling text buffer and parses only complete newline-terminated rows.

The public defaults in the checked-in configuration are `127.0.0.1:9600` and start command `start`. They are configuration defaults, not proof that a particular device uses that endpoint. A live workflow must use the host and port documented for the target bridge; it must not scan or guess.

## Integrity reporting

A replay or live capture should report at least:

- expected and decoded transport;
- total lines, valid USB/Bluetooth lines, and malformed lines;
- decoded sample count and malformed-row ratio;
- sample rate, channel order, and array shape;
- marker definition and timestamp evidence; and
- source mode: `simulation`, `replay`, or `live_device`.

The bundled parser rejects recordings without a canonical header, files with no valid samples, transport/header conflicts, and files whose malformed-row ratio exceeds 5%.

## Quality profile

The current course implementation screens complete one-second segments. These are device-workflow heuristics, not universal EEG standards.

| Check | Flag rule |
|---|---:|
| 49–51 Hz line-noise power | greater than 10 |
| 20–40 Hz high-frequency/EMG power | greater than 20 |
| Extreme-amplitude sample | absolute amplitude at least 100 µV |
| Extreme-amplitude count | more than 2 samples per second |
| Candidate bad-channel segment ratio | greater than 0.40 |
| Minimum adjacent-channel correlation | less than 0.15 |

Every QC result should name the method, segment length, thresholds, retained segments, candidate channels, and malformed-row ratio. A flag suggests an acquisition or data-quality problem; it is not a diagnosis of its cause.

Compute evidence about raw 50 Hz contamination before removing it. Post-notch 50 Hz power is not an independent measurement of the original line noise.

## Offline processing defaults

For a completed recording, the package provides median centering, a 1–45 Hz Butterworth bandpass, and a 50 Hz notch using zero-phase filtering. Welch PSD uses two-second segments by default.

Zero-phase filtering depends on future samples and is therefore an offline method. Do not present it as a causal real-time filter. Preserve experimental boundaries and process unrelated trials or blocks separately; filtering across a concatenation can create edge artifacts that cross conditions.

For rolling Alpha analysis, the recommended starting point is a four-second window with a one-second step. A scientific application should include only windows with adequate QC support and report accepted duration for each condition.

## Units

- Parsed time-domain amplitude: µV
- Welch PSD from µV data: µV²/Hz
- PSD integrated over a band: µV²
- Uncalibrated teaching simulation amplitude: arbitrary units (`a.u.`), unless the generator explicitly defines a microvolt scale
- Log power: state the logarithm base and reference; this repository uses `log10(power in µV² + 1e-12)` in its Alpha summary

Unit labels are part of the analysis contract. A mean square is not a PSD, and a PSD should not be relabeled as band power.
