# Real recordings for Lessons 2–4

The data owner has approved public teaching release of the two exact source
files below. They were copied byte-for-byte from the supplied S2 materials;
the public names make the default lesson path clear. These are **human EEG
recordings**, not synthetic examples. Use is subject to the repository's
[academic and non-commercial license](../../../LICENSE.md).

| Public file | Supplied source | SHA-256 | Samples |
|---|---|---|---:|
| `recording-01.txt` | `S04_01.txt` | `1c7cf69cf4572aa96b3452f2febb176c8c2a024eaf0e95812b22edda881006bb` | 23,518 per channel |
| `recording-02.txt` | `S04_11.txt` | `23a8e68b331a86ed7eb79056b580a972bdb9ee74d189e881316f0c7ead35db54` | 29,822 per channel |

Both files use the supplied text header `HEADER_DEF,T,P,C,C,C,C,C,C,C,0`.
The original S2 notebook declares 250 Hz, and the data owner confirmed that
the stored EEG values are already microvolts (µV). Each parsed array has seven
rows, ordered exactly as the seven `C` columns appear in the file. The
historical electrode montage, reference, condition definitions, and meaning of
the `P` field have **not** been established by these files. Lessons label the
columns `Ch1`–`Ch7` and do not invent events or eyes-open/closed conditions.

From a fresh clone, open Lesson 2 and choose **Run All**; Lessons 3–4 then use
the same bundled `recording-01.txt` automatically. To inspect the second file,
set `DATA_PATH` in the notebook to
`data/teaching/lesson-02/recording-02.txt`, or set the documented
`NEURADOCK_LESSON02_FILE`, `NEURADOCK_LESSON03_FILE`, or
`NEURADOCK_LESSON04_FILE` environment variable. Do not change acquisition
settings or quality thresholds merely to make a plot look better.

No participant identity or experimental condition is attached to this
teaching release. Keep any *new* classroom capture private unless it receives
separate publication authorization.
