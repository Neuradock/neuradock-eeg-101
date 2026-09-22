import ast
import hashlib
import json
import unittest
from pathlib import Path

import numpy as np

from neuradock_eeg101.quality_gate import gate_from_metrics, run_quality_gate
from neuradock_eeg101.vendor.quality_tools import clean_eeg_data


def _metrics(segments: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return tuple(np.zeros((7, segments), dtype=float) for _ in range(3))


class QualityGateTests(unittest.TestCase):
    def test_unknown_units_compute_diagnostics_without_retention_claim(self):
        data = np.zeros((7, 500), dtype=float)
        result = run_quality_gate(data, unit_confirmed=False)
        self.assertEqual(result["filtered"].shape, data.shape)
        self.assertEqual(result["metrics"][0].shape, (7, 2))
        self.assertFalse(result["keep_mask"].any())
        self.assertEqual(result["summary"]["status"], "units_unconfirmed")
        self.assertIsNone(result["summary"]["accepted_samples"])
        self.assertIsNone(result["summary"]["retention_rate"])
        json.dumps(result["summary"], allow_nan=False)

    def test_incomplete_tail_is_unassessed_and_not_accepted(self):
        data = np.zeros((7, 550), dtype=float)
        result = gate_from_metrics(data, _metrics(2), unit_confirmed=True)
        self.assertTrue(result["assessed_mask"][:500].all())
        self.assertFalse(result["assessed_mask"][500:].any())
        self.assertTrue(result["keep_mask"][:500].all())
        self.assertFalse(result["keep_mask"][500:].any())
        self.assertEqual(result["summary"]["unassessed_tail_samples"], 50)
        self.assertEqual(result["summary"]["accepted_samples"], 500)
        self.assertAlmostEqual(result["summary"]["retention_rate"], 500 / 550)
        self.assertEqual(result["summary"]["status"], "warning")

    def test_all_bad_channels_are_unusable_not_fully_retained(self):
        data = np.zeros((7, 500), dtype=float)
        metrics = tuple(np.full((7, 2), 100.0) for _ in range(3))
        result = gate_from_metrics(data, metrics, unit_confirmed=True)
        self.assertTrue(result["bad_channel_mask"].all())
        self.assertTrue(result["rejected_segments"].all())
        self.assertFalse(result["keep_mask"].any())
        self.assertEqual(result["summary"]["accepted_samples"], 0)
        self.assertEqual(result["summary"]["status"], "unusable")

    def test_bad_channels_are_excluded_from_segment_voting(self):
        data = np.zeros((7, 750), dtype=float)
        line, emg, outlier = _metrics(3)
        line[0, :] = 11.0  # Ch1 is globally bad and must not reject every segment.
        emg[1, 0] = 21.0  # Ch2 remains globally good and rejects only segment zero.
        result = gate_from_metrics(
            data, (line, emg, outlier), unit_confirmed=True)
        np.testing.assert_array_equal(
            result["bad_channel_mask"], [True, False, False, False, False, False, False])
        np.testing.assert_array_equal(result["rejected_segments"], [True, False, False])
        self.assertFalse(result["keep_mask"][:250].any())
        self.assertTrue(result["keep_mask"][250:].all())
        self.assertEqual(result["summary"]["accepted_samples"], 500)

    def test_wrapper_matches_official_cleaner_in_an_ordinary_full_second_case(self):
        data = np.zeros((7, 750), dtype=float)
        line, high_frequency, outlier = _metrics(3)
        line[0, :] = 11.0
        high_frequency[1, 0] = 21.0
        _, official_keep, official_info = clean_eeg_data(
            data, (line, high_frequency, outlier), (10.0, 20.0, 2.0),
            segment_length=250, bad_channel_ratio=0.4)
        result = gate_from_metrics(
            data, (line, high_frequency, outlier), unit_confirmed=True)
        np.testing.assert_array_equal(result["keep_mask"], official_keep)
        self.assertEqual(
            np.flatnonzero(result["bad_channel_mask"]).tolist(),
            official_info["bad_channels"],
        )
        self.assertEqual(
            np.flatnonzero(result["rejected_segments"]).tolist(),
            official_info["rejected_segment_indices"],
        )

    def test_fixed_bad_mask_supports_monotonic_threshold_comparison(self):
        data = np.zeros((7, 750), dtype=float)
        line, emg, outlier = _metrics(3)
        line[0] = [6.0, 11.0, 21.0]
        fixed = np.zeros(7, dtype=bool)
        counts = []
        for scale in (0.5, 1.0, 2.0):
            result = gate_from_metrics(
                data, (line, emg, outlier), unit_confirmed=True,
                thresholds=(10.0 * scale, 20.0 * scale, 2.0 * scale),
                fixed_bad_channel_mask=fixed)
            counts.append(result["summary"]["metric_flag_counts"]["line_noise_49_51_hz"])
            np.testing.assert_array_equal(result["bad_channel_mask"], fixed)
        self.assertEqual(counts, [3, 2, 1])

    def test_input_and_metric_contracts_are_strict(self):
        with self.assertRaisesRegex(ValueError, "shape"):
            run_quality_gate(np.zeros((6, 500)), unit_confirmed=True)
        with self.assertRaisesRegex(ValueError, "fs=250"):
            run_quality_gate(np.zeros((7, 500)), fs=200, unit_confirmed=True)
        with self.assertRaisesRegex(ValueError, "integer fs=250"):
            run_quality_gate(np.zeros((7, 500)), fs=250.0, unit_confirmed=True)
        with self.assertRaisesRegex(TypeError, "must be a boolean"):
            run_quality_gate(np.zeros((7, 500)), unit_confirmed="False")
        bad = np.zeros((7, 500)); bad[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "non-finite"):
            run_quality_gate(bad, unit_confirmed=True)
        with self.assertRaisesRegex(ValueError, "three finite arrays"):
            gate_from_metrics(np.zeros((7, 500)), _metrics(1), unit_confirmed=True)

    def test_threshold_boundaries_match_pinned_strict_comparisons(self):
        data = np.zeros((7, 250), dtype=float)
        line, high_frequency, outlier = _metrics(1)
        line[0, 0] = 10.0
        high_frequency[1, 0] = 20.0
        outlier[2, 0] = 2.0
        at_boundary = gate_from_metrics(
            data, (line, high_frequency, outlier), unit_confirmed=True)
        self.assertFalse(at_boundary["issue_mask"].any())
        line[0, 0] = np.nextafter(10.0, np.inf)
        high_frequency[1, 0] = np.nextafter(20.0, np.inf)
        outlier[2, 0] = 3.0
        above_boundary = gate_from_metrics(
            data, (line, high_frequency, outlier), unit_confirmed=True)
        self.assertTrue(above_boundary["metric_flags"][0][0, 0])
        self.assertTrue(above_boundary["metric_flags"][1][1, 0])
        self.assertTrue(above_boundary["metric_flags"][2][2, 0])

    def test_vendored_function_hashes_match_provenance_manifest(self):
        root = Path(__file__).resolve().parents[1]
        source_path = root / "src" / "neuradock_eeg101" / "vendor" / "quality_tools.py"
        manifest_path = source_path.with_name("QUALITY_TOOLS_PROVENANCE.json")
        source = source_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        tree = ast.parse(source)
        functions = {
            node.name: ast.get_source_segment(source, node)
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for name, expected in manifest["function_sha256"].items():
            actual = hashlib.sha256(functions[name].encode("utf-8")).hexdigest()
            self.assertEqual(actual, expected)

    def test_summary_is_json_safe_and_uses_generic_channel_labels(self):
        result = gate_from_metrics(
            np.zeros((7, 250)), _metrics(1), unit_confirmed=True)
        encoded = json.dumps(result["summary"], allow_nan=False)
        self.assertEqual(result["summary"]["channel_labels"], [
            "Ch1", "Ch2", "Ch3", "Ch4", "Ch5", "Ch6", "Ch7"])
        self.assertNotIn("Oz", encoded)


if __name__ == "__main__":
    unittest.main()
