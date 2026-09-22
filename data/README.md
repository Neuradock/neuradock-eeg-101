# Teaching data

This repository includes two real NeuraDock text recordings under
[`data/teaching/lesson-02/`](teaching/lesson-02/). The data owner has confirmed
that these exact files may be published for this course. Their hashes and known
acquisition facts are recorded in that directory's README. The repository's
[academic and non-commercial license](../LICENSE.md) applies to the released
teaching files.

Lesson 1 generates a deterministic simulation and does not use human EEG.
Lessons 2–4 use `recording-01.txt` by default, so they run from a fresh clone
without another download. `recording-02.txt` is an optional second real input.
Lesson 5's guide and worksheet need no recording; a live experiment requires a
connected device and the separate NeuraDock Agent.

Release approval for these two files does **not** authorize publication of any
other participant recording. Keep new captures and executed notebook outputs in
ignored local paths such as `outputs/`, `data/private/`, or `captures/` until
their own consent, ethics, de-identification, and redistribution checks are
complete. Do not commit names, consent forms, study keys, or clinical details.

The historical electrode montage and experimental condition labels of these
recordings remain unconfirmed. Use `Ch1`–`Ch7` as column labels, not assumed
scalp locations. The raw `T` and `P` fields do not by themselves establish
precise timing or experimental events. These files are for teaching signal
inspection and sensor-level methods, not diagnosis or neurofeedback validation.
