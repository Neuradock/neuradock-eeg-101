from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import random
import sys
import traceback


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NOTEBOOK_DIR = ROOT / "notebooks"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "notebook-execution"

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("PYTHONHASHSEED", "0")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")


def _source_text(cell: dict) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def _under_outputs(path: Path) -> bool:
    try:
        path.resolve().relative_to((ROOT / "outputs").resolve())
        return True
    except ValueError:
        return False


def _reset_runtime() -> None:
    random.seed(0)
    try:
        import numpy as np

        np.random.seed(0)
    except ImportError:
        pass
    try:
        import matplotlib.pyplot as plt

        plt.close("all")
    except ImportError:
        pass


def execute_notebook(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    namespace = {
        "__builtins__": __builtins__,
        "__file__": str(path),
        "__name__": f"__notebook_{path.stem.replace('-', '_')}__",
    }
    _reset_runtime()

    cell_results: list[dict] = []
    notebook_status = "pass"
    for cell_index, cell in enumerate(payload.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        source = _source_text(cell)
        if not source.strip():
            continue
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()
        result = {
            "cell_index": cell_index,
            "cell_id": cell.get("id", f"cell-{cell_index}"),
            "status": "pass",
        }
        try:
            compiled = compile(source, f"{path.name}:cell-{cell_index}", "exec")
            with redirect_stdout(captured_stdout), redirect_stderr(captured_stderr):
                exec(compiled, namespace, namespace)
        except Exception:
            result["status"] = "fail"
            result["traceback"] = traceback.format_exc()
            notebook_status = "fail"
        stdout = captured_stdout.getvalue()
        stderr = captured_stderr.getvalue()
        if stdout:
            result["stdout"] = stdout
        if stderr:
            result["stderr"] = stderr
        cell_results.append(result)
        if result["status"] == "fail":
            break

    return {
        "notebook": str(path.relative_to(ROOT)).replace("\\", "/"),
        "status": notebook_status,
        "code_cells_executed": len(cell_results),
        "cells": cell_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute the five core EEG 101 notebooks without rewriting them."
    )
    parser.add_argument("--notebooks-dir", type=Path, default=DEFAULT_NOTEBOOK_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--include-legacy", action="store_true",
                        help="Also execute the retained 06–08 supplemental notebooks.")
    parser.add_argument(
        "--include-appendices",
        action="store_true",
        help="Also execute the optional notebook in notebooks/appendix.",
    )
    args = parser.parse_args()

    notebook_dir = args.notebooks_dir.resolve()
    output_dir = args.output_dir.resolve()
    if not _under_outputs(output_dir):
        parser.error("--output-dir must be inside the repository's ignored outputs/ directory")

    core_notebooks = sorted(path for path in notebook_dir.glob("*.ipynb")
                            if path.name[:2] in {"01", "02", "03", "04", "05"})
    if len(core_notebooks) != 5:
        print(
            f"Expected 5 core notebooks in {notebook_dir}, found {len(core_notebooks)}",
            file=sys.stderr,
        )
        return 2
    notebooks = list(core_notebooks)
    if args.include_legacy:
        legacy = sorted(path for path in notebook_dir.glob("*.ipynb")
                        if path.name[:2] in {"06", "07", "08"})
        if len(legacy) != 3:
            print("Expected 3 retained supplemental notebooks (06–08).", file=sys.stderr)
            return 2
        notebooks.extend(legacy)
    if args.include_appendices:
        appendix_dir = notebook_dir / "appendix"
        appendix_notebooks = sorted(appendix_dir.glob("*.ipynb"))
        if len(appendix_notebooks) != 1:
            print(
                f"Expected 1 appendix notebook in {appendix_dir}, "
                f"found {len(appendix_notebooks)}",
                file=sys.stderr,
            )
            return 2
        notebooks.extend(appendix_notebooks)

    expected_count = 5 + (3 if args.include_legacy else 0) + (1 if args.include_appendices else 0)

    output_dir.mkdir(parents=True, exist_ok=True)
    original_cwd = Path.cwd()
    reports: list[dict] = []
    try:
        os.chdir(ROOT)
        if str(ROOT / "src") not in sys.path:
            sys.path.insert(0, str(ROOT / "src"))
        for notebook in notebooks:
            report = execute_notebook(notebook)
            reports.append(report)
            marker = "PASS" if report["status"] == "pass" else "FAIL"
            print(f"[{marker}] {report['notebook']} ({report['code_cells_executed']} code cells)")
            if report["status"] == "fail":
                failed = next(cell for cell in report["cells"] if cell["status"] == "fail")
                print(failed["traceback"], file=sys.stderr)
    finally:
        os.chdir(original_cwd)

    failures = [report["notebook"] for report in reports if report["status"] == "fail"]
    execution_report = {
        "schema_version": "1.0",
        "deterministic_environment": {
            "matplotlib_backend": os.environ["MPLBACKEND"],
            "python_hash_seed": os.environ["PYTHONHASHSEED"],
            "openblas_threads": os.environ["OPENBLAS_NUM_THREADS"],
            "omp_threads": os.environ["OMP_NUM_THREADS"],
        },
        "notebooks_expected": expected_count,
        "notebooks_executed": len(reports),
        "appendices_included": args.include_appendices,
        "legacy_supplements_included": args.include_legacy,
        "failures": failures,
        "results": reports,
    }
    report_path = output_dir / "execution-report.json"
    report_path.write_text(
        json.dumps(execution_report, indent=2, sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )
    print(f"Execution report: {report_path.relative_to(ROOT)}")
    if failures:
        print(f"Notebook execution failed: {len(failures)} notebook(s)", file=sys.stderr)
        return 1
    print(f"Notebook execution passed: {expected_count}/{expected_count} notebooks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
