# NeuraDock EEG 101

Five hands-on lessons for undergraduate EEG learning: from model spikes to a real recording, quality checks, Alpha power, and the official NeuraDock Agent.

> **Want to try EEG from your own brain?** Finish the lessons, then use a NeuraDock device with the [EEG Workstation Agent](https://github.com/Neuradock/eeg-workstation-agent) for a supervised live Alpha experiment. **[Subscribe on Crowd Supply for hardware launch updates →](https://www.crowdsupply.com/neuradock/neuradock-eeg-workstation)** A university may also provide a shared device. The Crowd Supply page currently offers updates, not immediate purchase or device access.

**Use:** academic and non-commercial only. Commercial use needs a separate license; see [LICENSE.md](LICENSE.md). The course is source-available, not OSI open source. The vendored quality-check code retains its separate MIT license.

## The five lessons

| Lesson | Open in VS Code | What you will do |
|---|---|---|
| 1 · Spikes to a signal | [Notebook](notebooks/01-from-synchrony-to-eeg.ipynb) · [Tutorial](tutorials/lesson-01-from-synchronized-neurons-to-measurable-eeg.md) · [10-slide deck](slides/01-from-synchronized-neurons-to-measurable-eeg.pptx) | Follow prescribed spikes through responses and a signed population sum. **Simulation; arbitrary units.** |
| 2 · Read a recording | [Notebook](notebooks/02-reading-neuradock-data.ipynb) · [Tutorial](tutorials/lesson-02-inside-a-neuradock-recording.md) | Parse and plot a real NeuraDock text file without inventing channel labels or events. |
| 3 · Check quality | [Notebook](notebooks/03-signal-quality-control.ipynb) · [Tutorial](tutorials/lesson-03-signal-quality-before-interpretation.md) | Apply the three artifact checks and preserve rejected time intervals. |
| 4 · Measure Alpha | [Notebook](notebooks/04-filtering-psd-alpha.ipynb) · [Tutorial](tutorials/lesson-04-filtering-psd-and-posterior-alpha.md) | Estimate Welch PSD and absolute 8–13 Hz Alpha power from accepted continuous data. |
| 5 · Try the Agent | [Notebook](notebooks/05-eyes-open-closed-alpha.ipynb) · [Tutorial](tutorials/lesson-05-comparing-conditions-without-overclaiming.md) | Open the official Agent; observe live Alpha and quality only when real hardware is available. |

Each notebook contains its lesson explanation and code. The tutorial pages are readable companions, not extra prerequisites. Lesson 5's notebook only checks the environment and prints a blank observation sheet; it does not connect to hardware. The Agent application lives in its [own repository](https://github.com/Neuradock/eeg-workstation-agent).

## Run in VS Code

Install Python 3.10 or newer and the VS Code Python and Jupyter extensions. Open this entire repository folder in VS Code, then create a course environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[notebooks]"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On macOS/Linux, use `./.venv/bin/python` instead. In VS Code choose **Select Kernel → Python Environments → .venv**, open Lesson 1, and choose **Run All**. Generated figures and summaries stay in the ignored `outputs/` folder.

Lessons 2–4 require the **same authorized real recording**; they have no synthetic fallback. This repository intentionally does not publish a participant's raw EEG. Obtain an authorized file with documented units and acquisition settings from your instructor, then set `DATA_PATH` in the notebook or `NEURADOCK_LESSON02_FILE` before starting its kernel. See the [real-data note](data/teaching/lesson-02/README.md). An unknown file's amplitude unit must be confirmed before Lesson 3 quality thresholds or Lesson 4 features can be interpreted. Historical S2 files use generic `Ch1`–`Ch7` labels; do not infer electrode positions or experimental conditions from a filename.

## What a result means

Lesson 1 is a deterministic teaching simulation. Lessons 2–4 replay an existing recording and report sensor-column observations, not diagnoses or a relaxation score. Lesson 5's optional **SYNTHETIC DEMO** previews the Agent UI only; a supervised live experiment requires a connected device, fresh samples, and acceptable signal quality. Live hardware validation is not claimed by this code release. Read [scientific boundaries](docs/SCIENTIFIC_BOUNDARIES.md) and the [data policy](data/README.md) before adapting a lesson to a study.

For classroom kits or commercial licensing, contact [business@neuradock.com](mailto:business@neuradock.com). To hear when NeuraDock hardware launches, [subscribe on Crowd Supply](https://www.crowdsupply.com/neuradock/neuradock-eeg-workstation).
