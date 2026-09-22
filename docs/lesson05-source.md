# Lesson 5 — Agent handoff, provenance, and boundaries

## Current delivery

The final core lesson is **From Alpha Features to the NeuraDock Agent**.
Its stable notebook and tutorial filenames are historical; their current content
is an English guided application lab, not an eyes-open/closed comparison or a
second implementation of neurofeedback.

The runtime lives in the official
[Neuradock/eeg-workstation-agent](https://github.com/Neuradock/eeg-workstation-agent)
repository. The course points students there and does not vendor the new
dashboard or install the Agent as a course dependency.

The reviewed Agent revision is
[`96a56e738dc9b442ac99ad2d3980423aa367854b`](https://github.com/Neuradock/eeg-workstation-agent/tree/96a56e738dc9b442ac99ad2d3980423aa367854b).
[PR #2](https://github.com/Neuradock/eeg-workstation-agent/pull/2) was verified
merged into `main` on 2026-09-22. The latest clone instructions use the maintained
default branch; record `git rev-parse HEAD` for each classroom run. For exact
reproduction of this reviewed snapshot, check out the full revision above.
The package version alone may not distinguish untagged source revisions.

The screenshot at `figures/lesson-05-agent.png` is copied from that Agent's
`docs/images/alpha-experience.png`. It is an actual **synthetic-demo** capture,
not participant EEG, a fabricated live result, or evidence of hardware validation.

## Modes and verification scope

- **Course notebook: `code_only`.** Two standard-library cells print an environment
  check and a blank observation sheet. No EEG is loaded, simulated, analyzed, or
  streamed; no server, installation, audio, or hardware connection is started.
- **Optional Agent preview: `simulation`.** The explicit `serve` command without
  a file uses generated test signals. This is interface preparation, not a
  replacement for the real recordings in Lessons 2–4.
- **Agent live experience: `live_device`, pending actual setup validation.**
  It needs confirmed endpoints, consent, a real NeuraDock device, valid sample
  delivery, and quality checks. Neither running the notebook nor a preview
  verifies this mode.

The notebook keeps output cells empty in Git. The previous requirement for a
real-recording input, four generated figures, a fixed calibration stage, and a
local audio/desktop feedback app no longer applies to the core Lesson 5.
Legacy course feedback modules and their tests are preserved; their settings
must not be presented as the current Agent's behavior.

## Feature and processing differences

The Agent's authoritative implementation and guide are:

- [Online processor at the reviewed revision](https://github.com/Neuradock/eeg-workstation-agent/blob/96a56e738dc9b442ac99ad2d3980423aa367854b/src/neuradock_agent/online.py)
- [Hardware profile](https://github.com/Neuradock/eeg-workstation-agent/blob/96a56e738dc9b442ac99ad2d3980423aa367854b/src/neuradock_agent/profile.py)
- [Alpha Experience guide](https://github.com/Neuradock/eeg-workstation-agent/blob/main/docs/alpha-experience.md)
- [Scientific boundaries](https://github.com/Neuradock/eeg-workstation-agent/blob/main/context/scientific-boundaries.md)

The current canonical live profile is CP5, CP6, PO3, PO4, O1, Oz, O2 at 250 Hz
in µV. Historical S2 recordings keep their previously established provenance
limits; a current profile does not prove an older recording's scalp montage.

Lesson 4 estimates integrated absolute Alpha in µV² from a selected channel in an
offline recording. The Agent adds completed trailing windows, posterior channel
aggregation, its own online preprocessing/QC, and an application state. This is
a conceptual continuation, not a promise of numerically identical output.

The displayed multiplier is the current posterior Alpha relative to a rolling
log-median reference, derived as `10 ** (-alpha_suppression_from_baseline)`.
It requires three accepted finite positive-power windows and uses up to 600
accepted window values, including the current value. It is not a frozen reference,
not Alpha/total spectral power, not a dB readout, and not the old course tone mapping.
Window warmup and rejected/stale/disconnected states must leave feedback unavailable.

## Human use, privacy, and stop behavior

The Connect device dialog generates terminal instructions; it does not execute
them or connect directly to hardware. Pause freezes displayed history and hides
feedback but does not stop live acquisition. Ctrl+C stops the Agent server; a
separate acquisition application has its own stop controls.

The optional Agent `doctor` command saves raw EEG and a report under `runs/`.
Instructors must obtain recording permission, control local retention, and keep
these files out of GitHub. The notebook does not invoke this command.

Alpha is a sensor-level feature, not a validated relaxation, attention, emotion,
or health score. An educational observation with stable eye state does not
demonstrate feedback-specific learning, clinical efficacy, or a treatment dose.
Institutions can share devices; this course's NeuraDock integration does not imply
that other hardware cannot implement EEG feedback.

## Authoring and checks

`scripts/lesson05_content.py` builds the notebook from the tutorial's shared text
and inserts two safe code cells at named authoring markers. This keeps GitHub and
VS Code instructions aligned.

Run `python scripts/generate_notebooks.py --check` to check source alignment.
Run `python scripts/verify_lesson05.py` for a real local Jupyter-kernel check;
`--notebook-cwd` also checks execution from the notebook folder. No recording
argument is needed. Verification reports stay under ignored `outputs/`.

Jupyter's local kernel transport is not an EEG device connection. Unit/kernel
checks verify the handoff notebook only; the Agent has its own test suite and CI.
The earlier Lesson 5 PPT and comparison figures remain legacy, not current
teaching evidence.
