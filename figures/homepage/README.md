# Notebook result previews

These three PNG files are copied byte-for-byte from saved `image/png` outputs in
the executed course notebooks. They are **replay results from an approved bundled
real recording**, not simulated signals or live-device validation. The export
does not rerun analysis, modify recordings or notebooks, crop images, or redraw
plots. The historical electrode montage is unconfirmed; the plots retain the
notebooks' column labels (`Ch1`–`Ch7`).

Run from the repository root using Python (standard library only):

```bash
python scripts/export_homepage_figures.py
```

The script checks each selected cell's execution count and plotting source
marker before exporting. If notebook cells or output order change, review and
update the selections in the script. It reports image dimensions, byte counts,
source locations, and SHA-256 hashes.

Cell and output indices below are **zero-based**. `In[...]` is the saved code-cell
execution count.

| Preview | Notebook source | Cell / output / execution | What it shows |
| --- | --- | --- | --- |
| [recording-preview.png](recording-preview.png) | [Lesson 2](../../notebooks/02-read-and-plot-your-neuradock-data.ipynb) | `cell[15]`, `output[0]`, `In[9]` | Five seconds of raw, unfiltered `Ch1` voltage, including large amplitude changes; original figure `01-single-channel.png`. |
| [quality-preview.png](quality-preview.png) | [Lesson 3](../../notebooks/03-three-artifact-checks-one-quality-gate.ipynb) | `cell[18]`, `output[0]`, `In[12]` | Flags from the three checks, temporal acceptance on eligible channels, and accepted raw samples on the original timeline; original figure `05-quality-gate.png`. |
| [alpha-preview.png](alpha-preview.png) | [Lesson 4](../../notebooks/04-from-eeg-to-features-understanding-alpha-power.ipynb) | `cell[13]`, `output[1]`, `In[8]` | The 8–13 Hz PSD area and absolute Alpha power for eligible columns in one accepted 19–23 second interval; original figure `03-alpha-power.png`. |

The homepage uses these as clickable visual previews. Open the linked notebook
for readable plots, processing settings, data context, and interpretation.

## Decorative course banner

`course-banner.png` is a decorative header generated with the built-in ImageGen
tool. Its abstract lines are an illustration, not EEG data. The course title is
also supplied as image alternative text in the homepage. The three scientific
previews above are independent, unchanged notebook results.

The generation specification is preserved in [banner-prompt.md](banner-prompt.md).
