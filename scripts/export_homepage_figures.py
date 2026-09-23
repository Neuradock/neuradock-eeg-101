"""Copy selected saved notebook PNG outputs into the README's figure directory.

Run from any directory with ``python scripts/export_homepage_figures.py``.
Uses only the standard library; does not execute or modify notebooks, source data,
or image pixels. These are replay results from the bundled approved recording.
The historical montage is unconfirmed, so source plots retain Ch1--Ch7 labels.

Each selection records a zero-based notebook cell index and output index, the
expected execution count, and the plot's original save name. Source checks make
notebook structure changes fail explicitly instead of silently choosing a new plot.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "figures" / "homepage"
SELECTIONS = (
    {
        "notebook": "02-read-and-plot-your-neuradock-data.ipynb",
        "cell_index": 15,
        "output_index": 0,
        "execution_count": 9,
        "source_marker": 'show_and_save(fig, "01-single-channel.png")',
        "filename": "recording-preview.png",
        "description": "Raw, unfiltered single-channel waveform from the real recording",
    },
    {
        "notebook": "03-three-artifact-checks-one-quality-gate.ipynb",
        "cell_index": 18,
        "output_index": 0,
        "execution_count": 12,
        "source_marker": 'show_and_save(fig, "05-quality-gate.png")',
        "filename": "quality-preview.png",
        "description": "Channel flags, temporal quality gate, and accepted raw samples",
    },
    {
        "notebook": "04-from-eeg-to-features-understanding-alpha-power.ipynb",
        "cell_index": 13,
        "output_index": 1,
        "execution_count": 8,
        "source_marker": 'show_and_save(fig, "03-alpha-power.png")',
        "filename": "alpha-preview.png",
        "description": "8--13 Hz PSD area and absolute Alpha power on eligible channels",
    },
)


def main() -> None:
    exports = []
    for selection in SELECTIONS:
        path = ROOT / "notebooks" / selection["notebook"]
        notebook = json.loads(path.read_text(encoding="utf-8"))
        cell = notebook["cells"][selection["cell_index"]]
        if (
            cell.get("cell_type") != "code"
            or cell.get("execution_count") != selection["execution_count"]
            or selection["source_marker"] not in "".join(cell["source"])
        ):
            raise ValueError(f"Notebook source changed; review selection for {path.name}")
        output = cell["outputs"][selection["output_index"]]
        encoded = output["data"]["image/png"]
        if isinstance(encoded, list):
            encoded = "".join(encoded)
        png = base64.b64decode("".join(encoded.split()), validate=True)
        if not png.startswith(b"\x89PNG\r\n\x1a\n") or png[12:16] != b"IHDR":
            raise ValueError(f"Selected output is not a PNG: {path.name}")
        width, height = struct.unpack(">II", png[16:24])
        exports.append((selection, png, width, height))

    # Validate every source before replacing any exported figure.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for selection, png, width, height in exports:
        target = OUTPUT_DIR / selection["filename"]
        target.write_bytes(png)
        digest = hashlib.sha256(png).hexdigest()
        print(f"{target.relative_to(ROOT).as_posix()}: {width}x{height}, {len(png)} bytes")
        print(
            f"  {selection['notebook']}, cell[{selection['cell_index']}], "
            f"output[{selection['output_index']}], In[{selection['execution_count']}]"
        )
        print(f"  {selection['description']}; SHA-256 {digest}")


if __name__ == "__main__":
    main()
