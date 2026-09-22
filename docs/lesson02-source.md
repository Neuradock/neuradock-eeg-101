# Lesson 2 reader provenance

The supplied source is `S2/S2_CP_evaluations_share.ipynb`, outside this tutorial
repository in the author's workspace. Its `data_reader` function locates `C`
columns in a `HEADER_DEF` header, groups seven values per sample, then transposes
the samples into a channels-by-samples NumPy array.

The lesson's `src/neuradock_eeg101/reading.py` retains this extraction mechanism,
but is explicitly an **adaptation**, not an unchanged copy:

- Header and row layouts are validated before extracting values.
- Malformed rows and non-finite values cause a visible failure, not silent omission.
- Original time strings and P values are retained separately from signal values.
- Failed rows do not automatically become experimental events.
- The reader does not assign scalp locations, units, a sampling rate, or physiology.
- No filtering, centering, normalization, or scaling is applied.

`scripts/lesson02_content.py` inserts the tested `data_reader` function source into
the notebook so students can inspect and execute the actual extraction code.
`tests/test_lesson02_notebook.py` guards against drift between that visible code
and the tested implementation and checks that the shared notebook has no outputs.

Local replay validation compares the adapted reader's complete EEG arrays against
the original function on both supplied S2 recordings. This comparison requires
the author's original files; it is not evidence that their redistribution is
authorized. Public data availability is described in
[`data/teaching/lesson-02/README.md`](../data/teaching/lesson-02/README.md).

Only the original notebook's reading core is reused. Its quality-scoring,
channel-selection, PSD, asymmetry, and treatment-comparison code are not part of
this introductory lesson. The revised notebook requires real data and has no
synthetic fallback. Test fixtures may contain fabricated values solely to test
parser failure cases; those fixtures are not the lesson's recording.
