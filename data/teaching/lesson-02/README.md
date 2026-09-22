# Lesson 2 real-recording location

Lesson 2 requires a **real NeuraDock text recording**. There is no synthetic
fallback. The public teaching-data path expected by the notebook is:

```text
data/teaching/lesson-02/recording-01.txt
```

## Current availability

This directory currently contains **no recording**. Publication clearance for the
supplied S2 recordings is pending. Do not assume that a file available in the
author's workspace is licensed for public redistribution.

For local work, the notebook can read the original `../S2/S04_01.txt` directly,
without modifying or copying it. Otherwise, set `DATA_PATH` in the notebook or
the `NEURADOCK_LESSON02_FILE` environment variable to an authorized real file.
Missing data raises an explicit error; no simulated substitute is generated.

## Before publishing a real teaching recording

The data owner must confirm participant consent/other applicable authorization,
de-identification (including metadata), and permission for public teaching and
redistribution. Record the dataset license, provenance, acquisition settings,
channel mapping, amplitude units, and the meanings of T/P/event fields alongside
the released file. Public release must also be reconciled with the repository's
[data policy](../../README.md); the current policy does not permit committing
participant raw recordings.

Changing a filename does not establish de-identification. Keep private data out
of commits while permission is unresolved. Figures and executed notebook outputs
remain local under the ignored `outputs/` directory.
