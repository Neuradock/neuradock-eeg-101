"""Deterministic contracts for Lesson 4's source-faithful spectral helper."""

import json
import unittest

import numpy as np
from scipy.signal import welch

from neuradock_eeg101.alpha_features import (
    analyze_alpha_windows,
    calculate_segment_psd,
    integrate_band,
)


FS = 250


def _sine_data(seconds: int, amplitude_uv: float = 10.0) -> np.ndarray:
    time = np.arange(seconds * FS) / FS
    return np.tile(amplitude_uv * np.sin(2 * np.pi * 10.0 * time), (7, 1))


class AlphaFeatureTests(unittest.TestCase):
    def test_welch_matches_original_s2_per_channel_loop(self):
        rng = np.random.default_rng(1203)
        segment = rng.normal(size=(7, 1000))
        expected_freq = None
        expected_psds = []
        for i in range(segment.shape[0]):
            channel_data = segment[i, :]
            f, psd = welch(channel_data, fs=FS, nperseg=FS * 2)
            if expected_freq is None:
                expected_freq = f
            expected_psds.append(psd)
        actual_freq, actual_psd = calculate_segment_psd(segment)
        np.testing.assert_array_equal(actual_freq, expected_freq)
        np.testing.assert_array_equal(actual_psd, np.array(expected_psds))
        self.assertEqual(actual_psd.shape, (7, 251))

    def test_known_ten_hz_power_and_no_forced_peak(self):
        data = _sine_data(5)
        keep = np.ones(data.shape[1], dtype=bool)
        bad = np.zeros(7, dtype=bool)
        result = analyze_alpha_windows(data, keep, bad, unit_confirmed=True)
        self.assertEqual(result["summary"]["valid_windows"], 2)
        np.testing.assert_allclose(result["alpha_power_uv2"], 50.0, rtol=0.02)
        self.assertEqual(result["summary"]["alpha_band_hz"], [8.0, 13.0])
        self.assertFalse(result["summary"]["alpha_peak_frequency_reported"])
        self.assertEqual(result["summary"]["alpha_power_unit"], "µV²")
        json.dumps(result["summary"], allow_nan=False)

    def test_one_rejected_sample_invalidates_overlapping_windows_without_splicing(self):
        data = _sine_data(10)
        keep = np.ones(data.shape[1], dtype=bool)
        keep[1200] = False
        result = analyze_alpha_windows(
            data, keep, np.zeros(7, dtype=bool), unit_confirmed=True)
        np.testing.assert_array_equal(
            result["starts"], np.arange(0, 1501, 250))
        np.testing.assert_array_equal(
            result["valid_window_mask"],
            [True, False, False, False, False, True, True])
        self.assertEqual(result["summary"]["valid_windows"], 3)
        self.assertEqual(result["summary"]["gate_accepted_samples"], 2499)
        self.assertEqual(result["summary"]["coverage_samples"], 2250)
        self.assertTrue(result["coverage_mask"][:1000].all())
        self.assertFalse(result["coverage_mask"][1000:1250].any())
        self.assertTrue(result["coverage_mask"][1250:].all())
        self.assertTrue(np.isnan(result["alpha_power_uv2"][:, 1:5]).all())
        self.assertTrue(np.isnan(result["psd_by_window"][:, 1:5]).all())

    def test_bad_channel_is_excluded_even_when_temporal_window_is_valid(self):
        data = _sine_data(4)
        bad = np.array([False, True, False, False, False, False, False])
        result = analyze_alpha_windows(
            data, np.ones(data.shape[1], dtype=bool), bad, unit_confirmed=True)
        self.assertTrue(np.isnan(result["alpha_power_uv2"][1]).all())
        self.assertTrue(np.isnan(result["psd_by_window"][1]).all())
        self.assertTrue(np.isfinite(result["alpha_power_uv2"][0]).all())
        self.assertEqual(result["summary"]["bad_channel_indices"], [1])
        self.assertEqual(result["summary"]["eligible_channel_indices"],
                         [0, 2, 3, 4, 5, 6])

    def test_integrate_band_uses_trapezoid_and_inclusive_bins(self):
        freq = np.arange(0.0, 21.0, 1.0)
        psd = np.ones((2, freq.size), dtype=float)
        np.testing.assert_array_equal(integrate_band(freq, psd), [5.0, 5.0])
        with self.assertRaisesRegex(ValueError, "at least two PSD bins"):
            integrate_band(freq, psd, band=(8.1, 9.1))
        with self.assertRaisesRegex(ValueError, "band edges must align"):
            integrate_band(freq, psd, band=(8.1, 12.9))
        with self.assertRaisesRegex(ValueError, "band edges must align"):
            analyze_alpha_windows(
                _sine_data(4), np.ones(1000, dtype=bool),
                np.zeros(7, dtype=bool), welch_s=0.8,
                unit_confirmed=True)

    def test_zero_power_is_valid_without_inventing_an_alpha_peak(self):
        data = np.zeros((7, 1000), dtype=float)
        result = analyze_alpha_windows(
            data, np.ones(1000, dtype=bool), np.zeros(7, dtype=bool),
            unit_confirmed=True)
        np.testing.assert_array_equal(result["alpha_power_uv2"], 0.0)
        self.assertFalse(result["summary"]["alpha_peak_frequency_reported"])

    def test_input_arrays_are_unchanged(self):
        data = _sine_data(5)
        keep = np.ones(data.shape[1], dtype=bool)
        bad = np.zeros(7, dtype=bool)
        original_data, original_keep, original_bad = data.copy(), keep.copy(), bad.copy()
        analyze_alpha_windows(data, keep, bad, unit_confirmed=True)
        np.testing.assert_array_equal(data, original_data)
        np.testing.assert_array_equal(keep, original_keep)
        np.testing.assert_array_equal(bad, original_bad)

    def test_rejects_unknown_units_all_bad_and_no_valid_continuous_window(self):
        data = _sine_data(5)
        keep = np.ones(data.shape[1], dtype=bool)
        bad = np.zeros(7, dtype=bool)
        with self.assertRaisesRegex(ValueError, "Confirmed microvolt units"):
            analyze_alpha_windows(data, keep, bad)
        with self.assertRaisesRegex(ValueError, "Confirmed microvolt units"):
            analyze_alpha_windows(data, keep, bad, unit_confirmed="False")
        with self.assertRaisesRegex(ValueError, "All channels are bad"):
            analyze_alpha_windows(data, keep, np.ones(7, dtype=bool), unit_confirmed=True)
        keep[750] = False
        with self.assertRaisesRegex(ValueError, "No fully accepted continuous"):
            analyze_alpha_windows(data, keep, bad, unit_confirmed=True)

    def test_rejects_short_windows_wrong_shapes_nonfinite_and_unaligned_durations(self):
        data = _sine_data(4)
        keep = np.ones(data.shape[1], dtype=bool)
        bad = np.zeros(7, dtype=bool)
        with self.assertRaisesRegex(ValueError, "integer fs=250"):
            calculate_segment_psd(data, fs=250.0)
        with self.assertRaisesRegex(ValueError, "positive and an exact number"):
            calculate_segment_psd(data, welch_s=1e-13)
        with self.assertRaisesRegex(ValueError, "positive duration"):
            calculate_segment_psd(data, welch_s=np.bool_(True))
        with self.assertRaisesRegex(ValueError, "no silent shortening"):
            calculate_segment_psd(data[:, :499])
        with self.assertRaisesRegex(ValueError, "shorter than one complete"):
            analyze_alpha_windows(data[:, :999], keep[:999], bad, unit_confirmed=True)
        with self.assertRaisesRegex(ValueError, "boolean array"):
            analyze_alpha_windows(data, keep.astype(int), bad, unit_confirmed=True)
        with self.assertRaisesRegex(ValueError, "boolean array"):
            analyze_alpha_windows(data, keep, bad.astype(int), unit_confirmed=True)
        with self.assertRaisesRegex(ValueError, "at least welch_s"):
            analyze_alpha_windows(data, keep, bad, window_s=1.0,
                                  unit_confirmed=True)
        with self.assertRaisesRegex(ValueError, "exact number of samples"):
            analyze_alpha_windows(data, keep, bad, window_s=4.001,
                                  unit_confirmed=True)
        with self.assertRaisesRegex(ValueError, "must not exceed window_s"):
            analyze_alpha_windows(data, keep, bad, step_s=5.0,
                                  unit_confirmed=True)
        corrupted = data.copy()
        corrupted[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "non-finite"):
            analyze_alpha_windows(corrupted, keep, bad, unit_confirmed=True)


if __name__ == "__main__":
    unittest.main()
