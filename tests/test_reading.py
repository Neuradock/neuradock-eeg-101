import ast
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from neuradock_eeg101.reading import data_reader, describe_p_field, inspect_timing


ROOT = Path(__file__).resolve().parents[1]
USB_HEADER = "HEADER_DEF,T,P,C,C,C,C,C,C,C,0"


def _bt_header() -> str:
    fields = ["HEADER_DEF", "T", "P"]
    for _ in range(5):
        fields.extend(["C"] * 7 + ["0"])
    return ",".join(fields)


class ReadingTests(unittest.TestCase):
    def _write(self, text: str) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "recording.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def test_usb_preserves_clock_p_and_channel_orientation(self):
        path = self._write(
            USB_HEADER + "\n"
            "12:00:00.000,255,1,2,3,4,5,6,7,0\n"
            "12:00:00.004,0,11,12,13,14,15,16,17,0\n"
        )
        data, info = data_reader(path)
        self.assertEqual(data.shape, (7, 2))
        np.testing.assert_array_equal(data[:, 0], np.arange(1, 8))
        np.testing.assert_array_equal(data[:, 1], np.arange(11, 18))
        self.assertEqual(info["raw_timestamps"], ["12:00:00.000", "12:00:00.004"])
        self.assertEqual(info["p_fields"], ["255", "0"])
        self.assertEqual(info["samples_per_packet"], 1)
        self.assertEqual(info["malformed_rows"], [])
        self.assertEqual(info["events"], [])

    def test_bluetooth_five_groups_are_extracted_and_transposed(self):
        row = ["5.0", "7"]
        expected = []
        for group in range(5):
            sample = [group * 10 + channel for channel in range(1, 8)]
            expected.append(sample)
            row.extend([str(value) for value in sample] + ["0"])
        path = self._write(_bt_header() + "\n" + ",".join(row) + "\n")
        data, info = data_reader(path)
        np.testing.assert_array_equal(data, np.asarray(expected, dtype=float).T)
        self.assertEqual(info["samples_per_packet"], 5)
        self.assertEqual(info["packet_count"], 1)
        self.assertEqual(info["raw_timestamps"], ["5.0"])
        self.assertEqual(info["sample_packet_indices"], [0] * 5)
        self.assertEqual(info["packet_line_numbers"], [2])

    def test_shifted_or_truncated_header_is_rejected(self):
        shifted = self._write("HEADER_DEF,T,P,0,C,C,C,C,C,C,C,0\n")
        with self.assertRaisesRegex(ValueError, "Header must be exactly"):
            data_reader(shifted)
        truncated = self._write("HEADER_DEF,T,P,C,C,C,C,C,C,0\n")
        with self.assertRaisesRegex(ValueError, "Header must be exactly"):
            data_reader(truncated)

    def test_strict_rows_raise_and_nonstrict_rows_are_reported(self):
        path = self._write(
            USB_HEADER + "\n"
            "0.0,0,1,2,3,4,5,6,7,0\n"
            "0.1,1,1,2,3,4,5,6\n"
            "0.2,2,nan,2,3,4,5,6,7,0\n"
        )
        with self.assertRaisesRegex(ValueError, "2 malformed row"):
            data_reader(path)
        data, info = data_reader(path, strict=False)
        self.assertEqual(data.shape, (7, 1))
        self.assertEqual([row["line_number"] for row in info["malformed_rows"]], [3, 4])
        self.assertIn("fields", info["malformed_rows"][0]["reason"])
        self.assertIn("finite", info["malformed_rows"][1]["reason"])

    def test_only_an_explicit_prefix_creates_an_event(self):
        text = (USB_HEADER + "\n"
                "0.0,0,1,2,3,4,5,6,7,0\n"
                "EVENT,trial-start\n"
                "0.1,1,2,3,4,5,6,7,8,0\n")
        path = self._write(text)
        with self.assertRaisesRegex(ValueError, "malformed row"):
            data_reader(path)
        data, info = data_reader(path, event_prefix="EVENT,")
        self.assertEqual(data.shape, (7, 2))
        self.assertEqual(info["sample_packet_indices"], [0, 1])
        self.assertEqual(info["packet_line_numbers"], [2, 4])
        self.assertEqual(info["events"], [
            {"sample_index": 1, "label": "trial-start", "line_number": 3}
        ])
        self.assertEqual(info["malformed_rows"], [])
        with self.assertRaisesRegex(ValueError, "event_prefix"):
            data_reader(path, event_prefix="  ")

    def test_timing_summaries_are_json_safe_and_do_not_interpolate(self):
        clock = inspect_timing(
            ["12:00:00.000", "12:00:00.004", "12:00:00.008"],
            timestamp_format="clock_hms_ms",
        )
        self.assertEqual(clock["status"], "parsed")
        self.assertTrue(clock["monotonic_increasing"])
        self.assertAlmostEqual(clock["median_packet_interval_s"], 0.004)
        self.assertAlmostEqual(clock["first_to_last_span_s"], 0.008)
        self.assertAlmostEqual(clock["minimum_packet_interval_s"], 0.004)
        self.assertAlmostEqual(clock["maximum_packet_interval_s"], 0.004)
        self.assertEqual(clock["duplicate_interval_count"], 0)
        self.assertEqual(clock["backward_interval_count"], 0)
        self.assertFalse(clock["within_packet_interpolation"])
        self.assertFalse(clock["midnight_rollover_applied"])
        unknown = inspect_timing(["clock-text"], timestamp_format="unknown")
        self.assertEqual(unknown["status"], "uninterpreted")
        json.dumps(clock, allow_nan=False)
        json.dumps(unknown, allow_nan=False)

    def test_timing_reports_duplicates_and_backward_steps_without_rollover(self):
        summary = inspect_timing(
            ["12:00:00.000", "12:00:00.004", "12:00:00.004", "12:00:00.002"],
            timestamp_format="clock_hms_ms",
        )
        self.assertFalse(summary["monotonic_increasing"])
        self.assertEqual(summary["duplicate_interval_count"], 1)
        self.assertEqual(summary["backward_interval_count"], 1)
        self.assertEqual(summary["nonpositive_interval_count"], 2)
        self.assertAlmostEqual(summary["minimum_packet_interval_s"], -0.002)
        self.assertAlmostEqual(summary["maximum_packet_interval_s"], 0.004)
        self.assertAlmostEqual(summary["first_to_last_span_s"], 0.002)
        self.assertFalse(summary["midnight_rollover_applied"])

    def test_p_summary_reports_counter_evidence_not_events(self):
        summary = describe_p_field(["254.000", "255.000", "0.000", "1.000"])
        self.assertTrue(summary["counter_like"])
        self.assertEqual(summary["plus_one_mod_256_fraction"], 1.0)
        self.assertEqual(summary["wrap_255_to_0_count"], 1)
        self.assertEqual(summary["experimental_events_inferred"], 0)
        json.dumps(summary, allow_nan=False)

    def test_p_summary_rejects_fractional_and_nonfinite_values(self):
        summary = describe_p_field(["1.0", "1.5", "nan", "inf"])
        self.assertFalse(summary["counter_like"])
        self.assertEqual(summary["integer_count"], 1)
        self.assertEqual(summary["invalid_count"], 3)
        json.dumps(summary, allow_nan=False)

    def test_original_s2_reader_numeric_output_matches_when_available(self):
        s2 = ROOT.parent / "S2"
        notebook_path = s2 / "S2_CP_evaluations_share.ipynb"
        recordings = sorted(s2.glob("*.txt"))
        if not notebook_path.is_file() or not recordings:
            self.skipTest("Local S2 originals are not available in this checkout")
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        function_node = None
        for cell in notebook["cells"]:
            if cell.get("cell_type") != "code":
                continue
            source = "".join(cell.get("source", []))
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            function_node = next((node for node in tree.body
                                  if isinstance(node, ast.FunctionDef)
                                  and node.name == "data_reader"), function_node)
            if function_node is not None:
                break
        self.assertIsNotNone(function_node)
        module = ast.Module(body=[function_node], type_ignores=[])
        namespace = {"np": np}
        exec(compile(ast.fix_missing_locations(module), str(notebook_path), "exec"), namespace)
        for recording in recordings:
            expected, _ = namespace["data_reader"](str(recording))
            actual, info = data_reader(recording)
            np.testing.assert_array_equal(actual, expected)
            self.assertEqual(info["malformed_rows"], [])
            self.assertTrue(describe_p_field(info["p_fields"])["counter_like"])


if __name__ == "__main__":
    unittest.main()
