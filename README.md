# NeuraDock EEG 101

Five hands-on EEG lessons: build a signal model, read a real recording, check its quality, measure Alpha power, and explore the official NeuraDock Agent.

## Start here

1. [Open Lesson 1](notebooks/01-how-spikes-become-an-eeg-like-signal.ipynb) on GitHub to preview its executed figures. Lessons 2–4 also include saved outputs from the bundled, owner-approved recording. The saved outputs are examples; rerun the notebooks to create your own results.
2. To run the course, clone this repository, install its Python environment using [the commands below](#run-in-vs-code), and open the whole folder in VS Code.
3. Work through the five notebooks in order. Lessons 1–4 need no device. Lesson 5 guides a supervised live observation with a NeuraDock device; its notebook runs safely without one.

> **Want to try EEG from your own brain?** Finish the lessons, then use a NeuraDock device with the [EEG Workstation Agent](https://github.com/Neuradock/eeg-workstation-agent) for a supervised live Alpha experiment. **[Subscribe on Crowd Supply for hardware launch updates →](https://www.crowdsupply.com/neuradock/neuradock-eeg-workstation)** A university may also provide a shared device. The Crowd Supply page currently offers updates, not immediate purchase or device access.

**Use:** academic and non-commercial only. Commercial use needs a separate license; see [LICENSE.md](LICENSE.md). The course is source-available, not OSI open source. The vendored quality-check code retains its separate MIT license.

## The five lessons

| Lesson | Open in VS Code | What you will do |
|---|---|---|
| 1 · How Spikes Become an EEG-Like Signal | [Notebook](notebooks/01-how-spikes-become-an-eeg-like-signal.ipynb) · [Tutorial](tutorials/lesson-01-from-synchronized-neurons-to-measurable-eeg.md) · [10-slide deck](slides/01-from-synchronized-neurons-to-measurable-eeg.pptx) | Follow prescribed spikes through responses and a signed population sum. **Simulation; arbitrary units.** |
| 2 · Read and Plot Your NeuraDock Data | [Notebook](notebooks/02-read-and-plot-your-neuradock-data.ipynb) · [Tutorial](tutorials/lesson-02-inside-a-neuradock-recording.md) | Parse and plot a real NeuraDock text file without inventing channel labels or events. |
| 3 · Three Artifact Checks, One Quality Gate | [Notebook](notebooks/03-three-artifact-checks-one-quality-gate.ipynb) · [Tutorial](tutorials/lesson-03-signal-quality-before-interpretation.md) | Apply the three artifact checks and preserve rejected time intervals. |
| 4 · From EEG to Features: Understanding Alpha Power | [Notebook](notebooks/04-from-eeg-to-features-understanding-alpha-power.ipynb) · [Tutorial](tutorials/lesson-04-filtering-psd-and-posterior-alpha.md) | Estimate Welch PSD and absolute 8–13 Hz Alpha power from accepted continuous data. |
| 5 · From Alpha Features to the NeuraDock Agent | [Notebook](notebooks/05-from-alpha-features-to-the-neuradock-agent.ipynb) · [Tutorial](tutorials/lesson-05-comparing-conditions-without-overclaiming.md) | Open the official Agent; observe live Alpha and quality only when real hardware is available. |

Each notebook contains its lesson explanation, code, and a saved example execution. The tutorial pages are readable companions, not extra prerequisites. Lesson 5's saved output is an environment check and a blank observation sheet; it is not live EEG.

## How this repository fits with the others

| Repository | Use it for |
|---|---|
| **This course** | Five sequenced lessons, teaching notebooks, approved example data, and lecture materials. |
| [`eeg-workstation-python`](https://github.com/Neuradock/eeg-workstation-python) | General Python reading and analysis tools outside the lesson sequence. |
| [`eeg-workstation-examples`](https://github.com/Neuradock/eeg-workstation-examples) | Standalone EEG experiment and application examples. |
| [`eeg-workstation-data`](https://github.com/Neuradock/eeg-workstation-data) | Additional public recordings and their provenance. |
| [`eeg-workstation-agent`](https://github.com/Neuradock/eeg-workstation-agent) | The separate real-time application used in Lesson 5; install it in its own environment. |

The [complete five-lesson lecture deck](slides/00-neuradock-eeg-101-five-lesson-lecture.pptx) has 30 editable slides with result charts and speaker notes. It covers the learning goals and outcomes for Lessons 1–5; the Lesson 1 deck above is a shorter companion for that session.

## Run in VS Code

Install Python 3.10 or newer and the VS Code Python and Jupyter extensions. Open this entire repository folder in VS Code, then create a course environment:

```powershell
git clone https://github.com/Neuradock/neuradock-eeg-101.git
cd neuradock-eeg-101
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[notebooks]"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On macOS/Linux, use `./.venv/bin/python` instead. In VS Code choose **Select Kernel → Python Environments → .venv**, open each notebook in order, and choose **Run All**. For a command-line check of all five notebooks, run `.\.venv\Scripts\python.exe scripts\execute_notebooks.py` on Windows or `./.venv/bin/python scripts/execute_notebooks.py` on macOS/Linux. Generated figures and summaries stay in the ignored `outputs/` folder. Maintainers can refresh the committed example outputs with `python scripts/publish_notebook_outputs.py` after checking the teaching-data provenance and reviewing the rendered notebooks.

Lessons 2–4 use the bundled, owner-approved real file [`recording-01.txt`](data/teaching/lesson-02/recording-01.txt) by default, so a fresh clone needs no separate data download. [`recording-02.txt`](data/teaching/lesson-02/recording-02.txt) is an optional second recording. There is no synthetic fallback in these lessons. The source materials state 250 Hz, and the data owner confirmed the stored EEG values are already µV; see the [data provenance and hashes](data/teaching/lesson-02/README.md). The historical montage and experimental conditions are not established, so the lessons use `Ch1`–`Ch7` rather than invented electrode positions or events.

## What a result means

Lesson 1 is a deterministic teaching simulation. Lessons 2–4 replay an existing recording and report sensor-column observations, not diagnoses or a relaxation score. Lesson 5's optional **SYNTHETIC DEMO** previews the Agent UI only; a supervised live experiment requires a connected device, fresh samples, and acceptable signal quality. Live hardware validation is not claimed by this code release. Read [scientific boundaries](docs/SCIENTIFIC_BOUNDARIES.md) and the [data policy](data/README.md) before adapting a lesson to a study.

For classroom kits or commercial licensing, contact [business@neuradock.com](mailto:business@neuradock.com). To hear when NeuraDock hardware launches, [subscribe on Crowd Supply](https://www.crowdsupply.com/neuradock/neuradock-eeg-workstation).
