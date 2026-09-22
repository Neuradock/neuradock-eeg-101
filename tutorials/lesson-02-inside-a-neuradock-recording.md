# Lesson 2 — Read and Plot Your NeuraDock Data

**Core · real-recording replay · about 60 minutes · after Lesson 1**

[Open the notebook](../notebooks/02-reading-neuradock-data.ipynb) in VS Code, select the course Python kernel, and choose **Run All**. This lesson follows one simple path:

**Text file → seven-channel array → relative time → raw waveforms.**

You will read a real recording and generate three figures yourself. There is no filtering, normalization, PSD, automated quality score, or classification. Successful reading does not establish good signal quality.

The notebook and this page are the teaching materials for this 60-minute lesson. The shared analysis parser is outside this revision.

## 1. Choose a real recording · 10 min

The owner-approved real recording is bundled at `data/teaching/lesson-02/recording-01.txt`; `recording-02.txt` is an optional second input. See the [teaching-data README](../data/teaching/lesson-02/README.md) for provenance, hashes, and limitations.

The notebook uses that file if present. Otherwise, in the author's workspace, it reads the original `../S2/S04_01.txt` directly, without copying it into the repository. For your own real recording, replace `DATA_PATH` in the file-settings cell, for example:

```python
DATA_PATH = Path(r"C:\path\to\your\recording.txt")
```

Alternatively, set `NEURADOCK_LESSON02_FILE` before starting the kernel. Relative paths are resolved from the repository root. If no real file is available, the notebook raises a clear error; **it never substitutes synthetic data**.

Inspect the header, not a screenshot of somebody else's result:

```text
HEADER_DEF,T,P,C,C,C,C,C,C,C,0
```

`T` is the recorded time field. `P` is a metadata field whose meaning must be established for this recording. Each `C` contains one EEG channel value; `0` marks a reserved column, not an eighth channel. Seven `C` fields describe one seven-channel sample per row. A supported 35-`C` layout contains five successive samples per row; this lesson focuses on the supplied one-sample layout.

## 2. Read the seven-channel array · 15 min

The visible `data_reader` preserves the central steps of the supplied `S2/S2_CP_evaluations_share.ipynb` reader: locate `C` columns, extract seven floats in their original order, then transpose to **channels × samples**.

```python
data, info = data_reader(DATA_PATH)
print(data.shape)
```

`data[0]` is the first channel over time; `data[:, 0]` is the first sample across all seven channels. This reader is an adaptation, not a verbatim copy: it adds strict layout and finite-value checks, preserves `T` and `P`, and rejects malformed rows instead of treating every failed row as an event. It does not rescale the signal values.

The original reader and the revised reader produce identical EEG arrays for the two supplied local source files:

| Original file | Array shape |
|---|---|
| `S04_01.txt` | `(7, 23518)` |
| `S04_11.txt` | `(7, 29822)` |

Both files are included in this course release. Another recording can have a different sample count.

The default labels are `Ch1`–`Ch7`: column labels, not inferred electrode positions. The data owner confirmed that these two exact recordings already contain µV values, so their plots say **Recorded amplitude (µV)**. A different file retains a unit-unconfirmed label until its calibration is checked; changing a label never converts values.

## 3. Give samples a relative time axis · 10 min

The original S2 notebook declares `FS = 250` Hz. At that nominal rate, samples are 4 ms apart:

```python
time_s = np.arange(data.shape[1]) / FS
```

Sample index 0 is at 0 seconds; index 250 is at 1 second. For `N` samples, `N / FS` is the nominal sample duration, while the last plotted sample is at `(N - 1) / FS`. Verify `FS` for any different recording; it is not a parameter to tune for a nicer-looking plot.

This uniform axis is a plotting convention, not a reconstruction of exact acquisition timing. The original `HH:MM:SS.mmm` clock strings remain in `info["raw_timestamps"]`. The notebook summarizes that packet clock separately. For an unfamiliar format, set `TIMESTAMP_FORMAT = "unknown"` until its meaning is established.

In both supplied files, `P` increments by one modulo 256. This is **counter-like evidence**, not proof of a stimulus or task label. Preserve it without creating experimental events. Event interpretation needs a documented definition or a separate event log.

## 4. Make three raw-data plots · 20 min

Start with these viewing controls:

```python
CHANNEL_INDEX = 0
START_S = 0.0
WINDOW_S = 5.0
```

Rerun the controls cell and the three plotting cells after a change.

1. **One channel:** a five-second raw waveform. Describe offsets, slow shifts, or sudden changes without diagnosing their source.
2. **All seven channels:** the same interval in seven panels. Each panel has its own labeled y-scale; compare numerical axes, not visual trace heights, when comparing amplitudes. No vertical offsets or normalization are applied to the data.
3. **Individual samples:** the first 0.1-second view, normally 25 points at 250 Hz. Adjacent dots are nominally 4 ms apart. The connecting lines are a visual aid, not extra measurements.

Now choose `CHANNEL_INDEX = 6`. Then try `START_S = 10` and `WINDOW_S = 2`, if your file is long enough. You should display 500 samples at 250 Hz. Changing the view does not change the recording.

## 5. Explain and save your result · 5 min

The notebook saves three PNG figures and `summary.json` under `outputs/notebooks/lesson-02/`. These runtime outputs are ignored by Git. Keep any *new* recording and its derived outputs private unless it receives separate publication authorization.

Submit the figures through your instructor's approved channel and briefly explain:

- the array shape and the two plot axes;
- why nominal sample time and the recorded clock are different evidence;
- why `P` is not automatically an event label; and
- which units, channel locations, and quality claims remain unverified.

You are ready for Lesson 3 when you can read and plot the recording without inventing its meaning. The next lesson asks which parts of a recording are trustworthy.

[← Lesson 1](lesson-01-from-synchronized-neurons-to-measurable-eeg.md) · [Next: Signal Quality Before Interpretation →](lesson-03-signal-quality-before-interpretation.md)
