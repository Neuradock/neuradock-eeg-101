"""Execute the five course notebooks and save reviewable Jupyter outputs.

Run from the course environment after ``pip install -e \".[notebooks]\"``.
The Jupyter client is supplied by ipykernel. No live device is contacted.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from jupyter_client import KernelManager


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"
EXPECTED = (
    "01-how-spikes-become-an-eeg-like-signal.ipynb",
    "02-read-and-plot-your-neuradock-data.ipynb",
    "03-three-artifact-checks-one-quality-gate.ipynb",
    "04-from-eeg-to-features-understanding-alpha-power.ipynb",
    "05-from-alpha-features-to-the-neuradock-agent.ipynb",
)
OLD_LINKS = {
    "02-reading-neuradock-data.ipynb": EXPECTED[1],
    "05-eyes-open-closed-alpha.ipynb": EXPECTED[4],
}


def source_text(cell: dict) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def safe_text(value: str) -> str:
    return value.replace(str(ROOT), ".").replace(str(ROOT).replace("\\", "/"), ".")


def execute_one(path: Path) -> tuple[dict, int, int]:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONHASHSEED"] = "0"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["OMP_NUM_THREADS"] = "1"
    env["IPYTHONDIR"] = str(ROOT / "outputs" / ".ipython")
    env["JUPYTER_RUNTIME_DIR"] = str(ROOT / "outputs" / ".jupyter-runtime")

    manager = KernelManager(kernel_name="python3")
    manager.kernel_spec.argv[0] = sys.executable
    manager.start_kernel(cwd=str(ROOT), env=env)
    client = manager.client()
    client.start_channels()
    try:
        client.wait_for_ready(timeout=60)
        executed = 0
        images = 0
        for cell in notebook["cells"]:
            if cell.get("cell_type") == "markdown":
                text = source_text(cell)
                for old, new in OLD_LINKS.items():
                    text = text.replace(old, new)
                cell["source"] = text
                continue
            if cell.get("cell_type") != "code":
                continue
            cell["outputs"] = []
            cell["execution_count"] = None
            code = source_text(cell)
            if not code.strip():
                continue
            message_id = client.execute(code, store_history=True)
            while True:
                message = client.get_iopub_msg(timeout=180)
                if message.get("parent_header", {}).get("msg_id") != message_id:
                    continue
                kind = message["msg_type"]
                content = message["content"]
                if kind == "execute_input":
                    cell["execution_count"] = content["execution_count"]
                elif kind == "stream":
                    cell["outputs"].append({
                        "output_type": "stream",
                        "name": content["name"],
                        "text": safe_text(content["text"]),
                    })
                elif kind in ("display_data", "execute_result"):
                    data = content.get("data", {})
                    images += int("image/png" in data)
                    output = {
                        "output_type": kind,
                        "data": {k: safe_text(v) if isinstance(v, str) and k.startswith("text/") else v
                                 for k, v in data.items()},
                        "metadata": content.get("metadata", {}),
                    }
                    if kind == "execute_result":
                        output["execution_count"] = content["execution_count"]
                    cell["outputs"].append(output)
                elif kind == "clear_output":
                    cell["outputs"] = []
                elif kind == "error":
                    raise RuntimeError(
                        f"{path.name}, cell {cell.get('id')}: "
                        + "\n".join(content.get("traceback", []))
                    )
                elif kind == "status" and content.get("execution_state") == "idle":
                    break
            while True:
                reply = client.get_shell_msg(timeout=30)
                if reply.get("parent_header", {}).get("msg_id") == message_id:
                    break
            if reply["content"].get("status") != "ok":
                raise RuntimeError(f"Execution failed in {path.name}, cell {cell.get('id')}")
            executed += 1
        return notebook, executed, images
    finally:
        client.stop_channels()
        manager.shutdown_kernel(now=True)


def main() -> int:
    results = []
    for name in EXPECTED:
        path = NOTEBOOKS / name
        if not path.is_file():
            raise FileNotFoundError(path)
        notebook, executed, images = execute_one(path)
        results.append((path, notebook, executed, images))
        print(f"[PASS] {name}: {executed} code cells, {images} inline PNGs")
    for path, notebook, _, _ in results:
        path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Saved executed outputs to all five notebooks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
