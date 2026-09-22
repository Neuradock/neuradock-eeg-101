# Lesson 4: Alpha-feature provenance and boundaries

## Original source and retained calculation

The user-supplied local source is `../S2/S2_CP_evaluations_share.ipynb`, outside
this tutorial repository. Its `calculate_eeg_psd(data_path, fs)` function begins
at source line 5 in the notebook cell with zero-based index 2 (a code cell). This path is provenance, not a public
download link; neither the original notebook nor its embedded outputs are copied
into the course repository.

Source identities recorded from the supplied file:

| Object | SHA-256 |
|---|---|
| Complete source notebook bytes | `60f6fcf44da2ed3413f7c76fba681912cc67a7e86afd8febfb78740d6d6e6d8e` |
| `calculate_eeg_psd` source text | `01563a3e193d45bae4e5c7f7220e92a369b0f3e63b46d678a48222454743d91a` |

The function-text hash is over the UTF-8 encoding of Python
`ast.get_source_segment` for that function. It is not a hash of a replacement
helper or a claim that the whole function is unchanged.

The original function reads the file, calls `data_selecter`, and then computes
Welch PSD for each selected channel. Lesson 4 preserves that **Welch loop**:

```python
nperseg = fs * 2
for i in range(n_channels):
    channel_data = continuous_data[i, :]
    f, psd = welch(channel_data, fs=fs, nperseg=nperseg)
    # Retain the frequency vector and append this channel's PSD.
```

The course implementation is an **adaptation**, not a verbatim copy of the
complete function. It accepts an already selected continuous array rather than
calling the old file reader or `data_selecter`. It validates the input and avoids
compacting rejected intervals. At 250 Hz, `nperseg=500` gives a 0.5 Hz frequency
grid. The source calculation is not silently shortened for insufficient input.

The feature helpers live in
[`src/neuradock_eeg101/alpha_features.py`](../src/neuradock_eeg101/alpha_features.py).
The [Lesson 4 notebook](../notebooks/04-filtering-psd-alpha.ipynb) makes the
calculation visible and generates its own real-data figures.

The example defaults to the first eligible column and first accepted
four-second feature window, not the maximum-power channel or interval.
`CHANNEL_INDEX` and `EXAMPLE_WINDOW` expose that choice for student inspection.

## Input and Lesson 3 inheritance

Use one real file through the strict Lesson 2 reader and the
[Lesson 3 quality gate](lesson03-source.md), called within this notebook rather
than loaded from another notebook's state. The two exact supplied S2 files have
owner-confirmed µV units dated 2026-09-21, tied to their SHA-256 identities in
the Lesson 3 source notes. New files need their own unit confirmation before
absolute Alpha power is calculated. Historical electrode placement remains
unconfirmed, so report Ch1–Ch7 rather than inferred posterior labels.

Reuse the Lesson 3 filtered array: fourth-order Butterworth 1–50 Hz bandpass with
offline `filtfilt`. Do not add a second filtering pass, a 50 Hz notch, or the old
1–45 Hz preprocessing path. Preserve the raw recording separately. Filtering is
noncausal and can affect transients and boundaries; do not process concatenated
unrelated blocks as one continuous signal.

Globally excluded channels cannot contribute feature values. The temporal gate,
unassessed tail, and original sample positions remain intact. An Alpha input
interval must be continuous and fully accepted. No source file is modified,
rescaled, copied, or uploaded by this lesson.

## Feature definition and units

The required feature is the numerical integral of PSD from 8 through 13 Hz:

```text
absolute Alpha power = integral[8,13] PSD(f) df
```

PSD is µV²/Hz; this integrated area is µV². `integrate_band` uses SciPy's
`trapezoid` with the actual frequency values and includes the 8 and 13 Hz bins.
Unlike Lesson 3's detector scores, this is not a bare sum of PSD bins. Retain the
same definition for every reported interval.

The optional relative feature divides integrated 8–13 Hz power by integrated
1–45 Hz power on the same accepted data. It is dimensionless and requires a
positive finite denominator. It does not produce another required figure.
Automatic Alpha-peak extraction is deliberately omitted: an argmax always
returns a bin, even when the spectrum contains no convincing Alpha peak.

## Four-second feature windows, one-second steps

The time course uses complete four-second windows at one-second steps, retaining
two-second Welch segments within each window and plotting each estimate at its
window center. A window is accepted only when
**all of its samples pass QC** and its channel remains eligible. This 100% rule
is intentionally stricter than an 80%-accepted-samples workflow: it prevents an
FFT from silently bridging rejected gaps or including rejected samples.

- Reject windows crossing any rejected interval or the unassessed tail.
- Do not pad incomplete windows, concatenate accepted pieces, or interpolate missing feature values.
- Preserve invalid positions as `NaN` gaps on the original nominal time axis.
- Report unique sample coverage as the union of accepted windows, not the number of windows multiplied by four seconds.
- That unique covered duration must not exceed the inherited gate's accepted duration.

Overlapping estimates reuse samples and are not independent observations or
additional participants. Unknown units, all channels excluded, a recording
shorter than four seconds, or no fully accepted continuous four-second window
produce explicit errors. Report the unavailable feature and its reason rather
than changing the gate to force a number.

## Reproducibility, privacy, and curriculum scope

File selection checks `NEURADOCK_LESSON04_FILE`, then
`NEURADOCK_LESSON03_FILE`, then `NEURADOCK_LESSON02_FILE`, then an available
`data/teaching/lesson-02/recording-01.txt`, otherwise the author's local
`../S2/S04_01.txt`. Missing real data is an error; there is no synthetic fallback.
See [approved teaching-data provenance](../data/teaching/lesson-02/README.md).
Only the two listed recordings are released for teaching; new captures need
their own publication authorization.

The [60-minute tutorial](../tutorials/lesson-04-filtering-psd-and-posterior-alpha.md)
produces four figures under the ignored `outputs/notebooks/lesson-04/`:

1. `01-usable-segment.png`
2. `02-eeg-to-psd.png`
3. `03-alpha-power.png`
4. `04-alpha-over-time.png`

`summary.json` records the declared methods and results. `alpha-features.npz`
retains feature arrays, window positions and validity, coverage, and excluded
channels. Do not commit executed real-data outputs or these derived arrays. The
earlier Lesson 4 PPT and synthetic reference images are not this revised lesson.

Lesson 4 describes a feature within one recording. The final Lesson 5 introduces
the official [NeuraDock EEG Workstation Agent](https://github.com/Neuradock/eeg-workstation-agent)
and its quality-gated browser dashboard. The Agent's posterior Alpha ratio uses
a rolling baseline, not this lesson's optional Alpha/total-power fraction or
the former course app's fixed personal calibration. Lesson 5's guide needs no
recording; its live experiment requires a supervised NeuraDock station. The S2
filenames do not establish eyes-open/closed conditions, participant pairing, or
a montage. Alpha power alone is not a measure
of health, relaxation, attention, cognitive load, or treatment effectiveness;
nonzero band area does not prove a distinct Alpha oscillation.
