# Lesson 3: official quality-code provenance and boundaries

## Pinned upstream source

Lesson 3 uses `eeg_quality_check` and `clean_eeg_data` from
[`Neuradock/eeg-workstation-agent`, `quality_tools.py`](https://github.com/Neuradock/eeg-workstation-agent/blob/e3539cbeca99e824dfeb3ebdb44d80ca80f0d5dc/src/neuradock_agent/quality_tools.py),
commit `e3539cbeca99e824dfeb3ebdb44d80ca80f0d5dc`.

The vendored function source is in
[`src/neuradock_eeg101/vendor/quality_tools.py`](../src/neuradock_eeg101/vendor/quality_tools.py).
The two function bodies are retained verbatim, with local profile and SciPy
compatibility imports. The accompanying [provenance manifest](../src/neuradock_eeg101/vendor/QUALITY_TOOLS_PROVENANCE.json)
records its origin and hashes; the upstream [MIT license](../src/neuradock_eeg101/vendor/NEURADOCK_MIT_LICENSE.txt)
is retained alongside it. That upstream license is distinct from the course
material license and does not grant rights to any human recording.

The lesson is not a verbatim reuse of the older S2 notebook's five-artifact,
0–100-score method. It also does not use the course's earlier approximate
`screening_qc` path, neighbor-correlation rule, or synthetic artifact figures.
The S2 reading mechanism continues through the Lesson 2 reader; the quality
algorithm comes from the pinned official source above.

## Numerical behavior retained

- Fourth-order Butterworth 1–50 Hz bandpass with forward/backward `filtfilt`.
- Complete, non-overlapping one-second segments: 250 samples at the lesson's 250 Hz.
- Welch PSD-bin sum over 49–51 Hz, flagged when greater than 10.
- Welch PSD-bin sum over 20–40 Hz, flagged when greater than 20.
- Count of filtered samples with absolute amplitude at least 100 µV, flagged when greater than 2.
- Logical OR of the three per-channel, per-segment flags.
- Channels with a flagged-segment fraction greater than 0.40 excluded from the segment-selection vote.
- A segment retained only when no remaining voting channel is flagged.

These are implementation-specific workflow heuristics, not universal EEG
standards. The spectral calculations sum PSD bins without integrating over
frequency, so their units remain µV²/Hz. Do not relabel them as band power in µV²
or replace the formulas while keeping the same thresholds. The high-frequency
rule is an EMG **candidate** screen, not a muscle-specific measurement.

The metrics operate on filtered data. The 1–50 Hz bandpass changes the signal
near 50 Hz; no raw-interference measurement or 60 Hz validation is claimed.
`filtfilt` is an offline, noncausal operation and can affect signal boundaries.
Do not filter across unrelated trials or experimental blocks.

## Teaching wrapper: explicit safeguards, not hidden core edits

[`quality_gate.py`](../src/neuradock_eeg101/quality_gate.py) separates the
vendored calculations from input checks, descriptive metrics, and time masks.
The lesson's safeguards are reported explicitly:

1. Require real recording input; never replace missing input with synthetic data. When units are unknown, calculate only reference diagnostics, leave accepted duration and retention unavailable, and do not accept samples.
2. Keep generic Ch1–Ch7 labels unless acquisition metadata independently establishes scalp locations.
3. If every channel is excluded, retain no segments. An empty set of voting channels is not evidence of clean data.
4. Mark the incomplete final second as unassessed; never silently count it as passed.
5. Preserve sample indices, the original timeline, and explicit masks. Do not concatenate separated retained intervals or overwrite the raw recording.
6. Report the excluded channels, thresholds, retained fraction, and unassessed tail together. A retained interval is conditional on the channels that still vote.

These boundaries differ deliberately from two upstream defaults: the original
`clean_eeg_data` rejects no full segments when its good-channel set is empty,
and pads the incomplete tail as not rejected. It also returns a shortened,
concatenated array. The wrapper does not use that array as a continuous signal;
it builds explicit masks on the original timeline instead. The upstream source
is left unchanged so those differences remain auditable. Canonical names in
the compatibility profile are not historical labels for these S2 recordings;
the teaching wrapper reports generic column labels.

Changing a threshold and rerunning the complete gate can change both flags and
voting-channel membership. Consequently, final retained time need not be
monotonic in that threshold. The classroom experiment instead compares each
detector's flagged channel-second fraction at 0.5×, 1×, and 2× its threshold,
without rerunning the gate. Its count thresholds are 1, 2, and 4 while the
sample-amplitude cutoff remains 100 µV. This is a sensitivity check, not an
optimization for the most favorable retention.

## Real-data units and provenance

On **2026-09-21**, the data owner explicitly confirmed that the values in both
supplied S2 recordings are already in **µV**. No multiplication or other unit
conversion is needed for those exact files. Their SHA-256 identities are:

| Local source file | SHA-256 |
|---|---|
| `S04_01.txt` | `1c7cf69cf4572aa96b3452f2febb176c8c2a024eaf0e95812b22edda881006bb` |
| `S04_11.txt` | `23a8e68b331a86ed7eb79056b580a972bdb9ee74d189e881316f0c7ead35db54` |

The notebook can recognize those exact hashes. It does not infer µV from a
filename, a generic `C` header, or numeric-looking values. A different recording
requires its own documented amplitude-unit confirmation. Historical electrode
placement and experimental-event semantics are not established by the unit
confirmation; labels remain Ch1–Ch7 and `P` is not automatically an event.

The file selection order is `NEURADOCK_LESSON03_FILE`, then
`NEURADOCK_LESSON02_FILE`, then an available
`data/teaching/lesson-02/recording-01.txt`, otherwise the author's local
`../S2/S04_01.txt`. A missing real file raises an error.

See [approved teaching-data provenance](../data/teaching/lesson-02/README.md).
Only the two listed recordings are released for teaching; new captures need
their own publication authorization. Six figures, `summary.json`, and `quality-masks.npz` remain in the Git-ignored
`outputs/notebooks/lesson-03/`; tracked notebooks must remain free of private outputs.

The mask archive distinguishes assessed samples, temporal acceptance, excluded
channels, and accepted channel-samples. Excluded candidate channels are not
restored merely because another channel votes to retain that second.

## Teaching scope

The revised [notebook](../notebooks/03-signal-quality-control.ipynb) and
[tutorial](../tutorials/lesson-03-signal-quality-before-interpretation.md)
form the 60-minute lesson. The earlier Lesson 3 PPT is not yet aligned.
The six figures cover raw/filtered data, line noise, high-frequency activity,
amplitude outliers, the quality gate, and a one-threshold experiment.

Passing a heuristic is not proof of clean brain activity. A flag does not
identify a physical cause, establish electrode detachment or saturation, or
support health, cognitive-state, or treatment claims.
