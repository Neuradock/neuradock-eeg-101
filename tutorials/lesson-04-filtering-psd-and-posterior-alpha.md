# Lesson 4 — From EEG to Features: Understanding Alpha Power

**Core · real-recording replay · about 60 minutes · after Lesson 3**

[Open the notebook](../notebooks/04-from-eeg-to-features-understanding-alpha-power.ipynb) in VS Code, select the course kernel, and run the cells in order. This lesson follows one real recording through four steps:

**A usable continuous interval → its PSD → the 8–13 Hz area → Alpha power over time.**

The core feature is **absolute Alpha power**, measured in µV². We do not compare conditions here, require a 10 Hz peak, or turn Alpha into a health or mental-state score. Teach this version with the notebook and this page.

## 1. Start with the Lesson 3 quality decision · 10 min

Use the same bundled real `data/teaching/lesson-02/recording-01.txt` and acquisition settings as Lessons 2–3. Set `DATA_PATH` in the notebook or `NEURADOCK_LESSON04_FILE` before starting the kernel to inspect another authorized recording. Missing real data raises an error; no synthetic recording is substituted. See [data provenance and permissions](../data/teaching/lesson-02/README.md).

The data owner confirmed on 2026-09-21 that the two exact supplied S2 files already contain µV values. Their hashes, not just their filenames, identify that confirmation. A new file needs its own verified unit setting before Alpha power is calculated. Labels remain `Ch1`–`Ch7`: historical electrode positions and condition meanings are not established.

The notebook calls the reader and Lesson 3 gate itself; you do not need another notebook's kernel state or saved outputs. Reuse the resulting filtered signal and quality masks. The filter is the same fourth-order 1–50 Hz Butterworth bandpass with `filtfilt`; **do not add a second bandpass or a notch**. It is an offline operation, not a causal live filter. Globally excluded channels, rejected seconds, and the unassessed tail remain excluded.

Generate `01-usable-segment.png`. Identify the selected eligible channel and a continuous accepted four-second interval on the original nominal time axis. Do not stitch separated intervals together. Unknown units, all channels excluded, a recording shorter than four seconds, or no fully accepted four-second window cause an explicit error. Report that limitation instead of relaxing the gate to obtain a figure.

The defaults choose the **first eligible channel and first accepted window**, not the largest Alpha value. After the first run, try another eligible `CHANNEL_INDEX` or change `EXAMPLE_WINDOW` within the accepted-window list, then rerun. Keep QC thresholds unchanged.

## 2. Turn a waveform into a PSD · 15 min

Generate `02-eeg-to-psd.png`. The waveform shows how recorded voltage changes over time; the PSD shows how its estimated power is distributed over frequency.

The visible computation adapts the per-channel Welch loop from your original S2 `calculate_eeg_psd` function. The essential call remains:

```python
nperseg = fs * 2
frequencies, psd = welch(channel_data, fs=fs, nperseg=nperseg)
```

At 250 Hz, each Welch segment has 500 samples and the frequency-bin spacing is `250 / 500 = 0.5 Hz`. The analysis interval must be long enough; do not silently shorten the estimator on an undersized interval.

Read the PSD axes carefully: frequency is in Hz, while PSD is in **µV²/Hz**. Bin spacing is not a guarantee that two nearby physiological rhythms can be distinguished. A broad spectrum, a weak Alpha bump, or no clear Alpha peak are all possible real-data results.

Only the original Welch calculation is retained. File reading and the old `data_selecter` compaction are replaced by the strict reader and Lesson 3's timeline-preserving gate. See [source and adaptation notes](../docs/lesson04-source.md).

## 3. Measure the Alpha-band area · 20 min

Generate `03-alpha-power.png`. Shade 8–13 Hz on the PSD and calculate the area under that part of the curve:

```text
Alpha power = integral of PSD(f) from 8 to 13 Hz
```

The numerical calculation uses the trapezoidal rule on the PSD bins from 8 through 13 Hz, including both endpoints. PSD units are µV²/Hz; multiplying by frequency width gives **µV²**. This is different from Lesson 3's original detector metrics, which sum PSD bins without a frequency-width factor.

The selected band defines a feature, not a diagnosis. A nonzero area does not establish a distinct Alpha oscillation or tell us whether someone is relaxed, attentive, healthy, or responding to treatment. Keep the channel and selected interval alongside every reported number.

The figure also shows absolute Alpha power for eligible channels in this same interval; these are column-level comparisons, not a scalp map or condition contrast. Inspect the PSD before explaining the number. Do not automatically select its largest Alpha-band bin and call that a reliable individual Alpha frequency; the core notebook intentionally omits automatic peak extraction.

## 4. Follow Alpha power over time · 15 min

Generate `04-alpha-over-time.png`. Slide a **four-second window in one-second steps** along the original recording, plotting each estimate at its window's center. Each four-second feature window still uses two-second Welch segments internally: four seconds is the feature's time span, not a change to the 0.5 Hz PSD grid. An estimate summarizes its window; it is not instantaneous power.

A feature window is valid only when **100% of its samples pass the inherited gate** and its channel is eligible. This deliberately strict rule rejects any window crossing a rejected gap or the unassessed tail. Incomplete final windows are not padded. It does not use an 80% acceptance rule.

Show invalid windows as `NaN` gaps, not zeros or interpolated Alpha values. Zero would mean measured zero power; a gap means no accepted estimate. Preserve original time positions and do not connect across missing estimates.

Overlapping windows reuse samples. Ten accepted four-second windows do **not** imply 40 seconds of unique usable data. Report the union of samples covered by valid windows; that unique coverage cannot exceed the Lesson 3 gate's accepted duration. The windows are also not independent participants.

## Optional: relative Alpha, not another required feature

After the four core figures, the optional cell divides integrated 8–13 Hz power by integrated 1–45 Hz power for the same accepted interval. Relative Alpha is dimensionless and depends on both numerator and denominator. A zero or invalid denominator does not support a ratio.

This optional result adds no extra figure. Peak interpretation is discussion-only: the notebook does not force an `argmax` estimate or require a visible peak. Keep the required report focused on absolute Alpha power.

## Deliverable and the next lesson

The notebook writes four PNG figures, `summary.json`, and `alpha-features.npz` under the Git-ignored `outputs/notebooks/lesson-04/`. Keep private figures, feature arrays, and executed notebook outputs local. The lesson does not modify, copy, or upload the source recording.

Submit one short feature report with:

- the real-data source, confirmed units, generic channel label, and inherited filter/QC settings;
- the selected continuous interval, Welch segment length, and 0.5 Hz frequency spacing;
- absolute Alpha power in µV², with its shaded PSD;
- four-second feature-window validity, rejected gaps, and unique covered duration; and
- one observation and one limitation, without a condition or mental-state claim.

**Lesson 4:** measure one feature within one recording. **Lesson 5:** take that understanding to the official [NeuraDock EEG Workstation Agent](https://github.com/Neuradock/eeg-workstation-agent), connect a supervised NeuraDock station, and observe quality-gated Alpha feedback in its browser dashboard. Its displayed posterior Alpha ratio uses a rolling baseline; it is not this lesson's optional Alpha/total-power fraction. The guided Lesson 5 notebook does not require a real-recording replay or generate four more figures. The existing S2 files remain code-replay evidence, not a historical feedback experiment or a paired eyes-open/eyes-closed experiment.

[← Lesson 3](lesson-03-signal-quality-before-interpretation.md) · [Next: From Alpha Features to the NeuraDock Agent →](lesson-05-comparing-conditions-without-overclaiming.md)
