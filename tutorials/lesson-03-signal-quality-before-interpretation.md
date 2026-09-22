# Lesson 3 — Three Artifact Checks, One Quality Gate

**Core · real-recording replay · about 60 minutes · after Lesson 2**

[Open the notebook](../notebooks/03-signal-quality-control.ipynb) in VS Code and select the course kernel. This lesson asks: **which intervals should we inspect before interpreting EEG features?**

Use the same real recording as Lesson 2. Follow the official NeuraDock quality-check code, calculate its three visible metrics, and inspect the corresponding waveforms. Do not add artificial artifacts to make a rule trigger. An unflagged result is also a result.

The notebook and this page replace the earlier synthetic demonstration. The older shared CLI QC implementation and its synthetic reference figures are not this lesson's algorithm.

## 1. Confirm the input and algorithm · 5 min

By default, the notebook uses the bundled real `data/teaching/lesson-02/recording-01.txt` from Lesson 2. Set `NEURADOCK_LESSON03_FILE` before starting the kernel to inspect another authorized recording; it also accepts `NEURADOCK_LESSON02_FILE`. See [recording provenance](../data/teaching/lesson-02/README.md). A missing recording stops the lesson; there is no synthetic fallback.

The data owner confirmed on 2026-09-21 that both supplied S2 files, `S04_01.txt` and `S04_11.txt`, already contain microvolt values. No additional amplitude conversion is needed for those exact files. The notebook recognizes their hashes; for a new file, set `UNIT_CONFIRMED = True` only after independently verifying µV. With unknown units, metrics are reference-only and the gate reports no accepted duration. Keep `Ch1`–`Ch7` until historical electrode placement is verified. A filename or seven-column header does not establish a montage.

Lesson 3 uses the MIT-licensed `eeg_quality_check` and `clean_eeg_data` functions from the official repository at a pinned commit, rather than an approximate replacement. Read the [source and boundary notes](../docs/lesson03-source.md) for provenance and the separate safeguards around those functions.

## 2. Compare raw and filtered data · 10 min

The official check first applies a fourth-order Butterworth 1–50 Hz bandpass with forward-and-backward `filtfilt`. It then evaluates complete, non-overlapping **one-second segments: 250 samples at 250 Hz**. Keep this duration fixed for the lesson.

Generate `01-raw-and-filtered.png`. Compare the same channel and interval before and after filtering. Raw data remain available and unchanged. The quality metrics below use the **filtered** samples, not the raw recording.

This is offline, noncausal filtering, not a live-feedback algorithm. Filtering can alter transients and edge samples; it does not prove that contamination has been removed. No notch is added. The bandpass itself affects frequencies near 50 Hz, so this metric is not an independent measure of raw electrical interference.

## 3. Three checks, three visible results · 20 min

### A. Inspect the line-noise rule

For each channel and second, the original code estimates a Welch PSD and sums its bins from 49 through 51 Hz:

```text
line_metric = sum(PSD bins from 49 to 51 Hz)
line_flag = line_metric > 10
```

Generate `02-line-noise.png`. Read the metric values and the threshold together, then locate any flagged second in the waveform.

The metric is a **PSD-bin sum**, retaining units of µV²/Hz, not an integrated band power in µV². Do not silently replace the sum with an integral while reusing the original threshold. Passing this rule means only that this filtered metric did not exceed its cutoff.

### B. Inspect high-frequency activity

The second original rule uses another PSD-bin sum:

```text
high_frequency_metric = sum(PSD bins from 20 to 40 Hz)
high_frequency_flag = high_frequency_metric > 20
```

Generate `03-high-frequency.png`. The upstream code calls this an EMG check. In your explanation, use **high-frequency activity / possible muscle contamination**: this range is not specific to muscle, and the rule does not establish the cause.

Do not invent a contaminated example if the current file does not cross the threshold. Report what the actual recording shows.

### C. Count amplitude outliers

For each filtered one-second segment, count samples whose absolute amplitude reaches 100 µV:

```text
outlier_count = count(abs(filtered_samples) >= 100)
amplitude_flag = outlier_count > 2
```

Generate `04-amplitude-outliers.png`. Distinguish the two comparisons: a sample at exactly 100 µV counts; exactly two outliers do not trigger the segment rule.

A large excursion is an observation, not proof of electrode detachment or amplifier saturation. Inspect the raw and filtered traces before proposing an acquisition check.

## 4. Understand the quality gate · 15 min

Generate `05-quality-gate.png` and follow the decisions:

1. A channel-second is flagged if **any** of the three rules triggers: logical OR.
2. A channel becomes a bad-channel candidate when its flagged-segment fraction is **greater than 0.40**.
3. Those candidate channels are excluded from the upstream segment-selection vote. A second is retained only when no remaining voting channel is flagged.

Report the excluded channels alongside the retained fraction. A high retained fraction does not mean that every channel is acceptable. There is no validated 0–100 quality score or physiological-normality classification.

The teaching wrapper keeps the original time axis and explicit masks. It does not join separated retained intervals into a continuous trace. If every channel is excluded, it retains **nothing** instead of treating an empty vote as success. An incomplete final second is reported as **unassessed**, not clean. Filtering and interpretation should not bridge unrelated experimental blocks.

## 5. Change one threshold and explain the result · 10 min

Generate `06-threshold-experiment.png` to compare each detector's flagged fraction at 0.5×, 1×, and 2× its original threshold. The denominator is all assessed channel-seconds, not participants or the fraction of elapsed time retained. Keep the recording, filter, sample rate, and one-second segmentation fixed. State your prediction first, then compare the detector flags.

For the amplitude detector, the tested count thresholds are 1, 2, and 4; the sample-amplitude cutoff stays at 100 µV. This experiment does not rerun the quality gate or change voting-channel membership. It is a sensitivity exercise, not a search for the largest retained fraction. Recomputing channel exclusion would add another changing decision and can make final retention nonmonotonic.

## Deliverable and limits

The notebook saves six PNG figures, `summary.json`, and `quality-masks.npz` under the Git-ignored `outputs/notebooks/lesson-03/`. The masks record assessed samples, temporal acceptance, excluded channels, and accepted channel-samples without shortening the timeline. Keep the tracked notebook free of private outputs. Source recordings are neither modified nor copied into the repository by this lesson.

Submit a short report through your instructor's approved channel, identifying:

- real-data source, units, sample rate, filtering stage, and one-second segmentation;
- the three metrics, exact thresholds, and one inspected interval;
- excluded channel indices, retained time, and the unassessed tail;
- what changed in the threshold experiment; and
- whether you would proceed with stated limits or inspect/reacquire more data.

These are workflow heuristics, not universal EEG standards. No flag proves a cause, and no unflagged result proves clean brain activity. The lesson does not diagnose health, attention, emotion, or treatment effects. The next lesson explains spectral estimation in more depth.

[← Lesson 2](lesson-02-inside-a-neuradock-recording.md) · [Next: Filtering, Welch PSD, and Posterior Alpha →](lesson-04-filtering-psd-and-posterior-alpha.md)
