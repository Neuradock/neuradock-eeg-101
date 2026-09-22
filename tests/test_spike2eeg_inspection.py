"""Check visible source decomposition against the preserved spike2eeg core."""

import unittest

import numpy as np

from neuradock_eeg101.spike2eeg import generate_eeg, simulate_spiking_neurons
from neuradock_eeg101.spike2eeg_inspection import (
    isolated_neuron_signal,
    neuron_contributions,
)


BASE = {
    "N": 20,
    "active_num": 12,
    "target_freq": 10.0,
    "phase_variation": np.pi / 4,
    "background_freq": 5.0,
    "duration": 2.0,
}


class Spike2EEGInspectionTests(unittest.TestCase):
    def test_visible_contributions_sum_to_full_original_output(self):
        spikes = simulate_spiking_neurons(**BASE, seed=42)
        _, original = generate_eeg(spikes, duration=2, sampling_rate=1000, seed=42)
        contributions = neuron_contributions(spikes, duration=2, sampling_rate=1000, seed=42)
        self.assertEqual(contributions.shape, (20, 2000))
        np.testing.assert_allclose(contributions.sum(axis=0), original, rtol=1e-13, atol=1e-13)

    def test_inspection_preserves_inputs_and_negative_index_behavior(self):
        spikes = simulate_spiking_neurons(**BASE, seed=42)
        before = [train.copy() for train in spikes]
        self.assertGreater(sum(np.count_nonzero(train < 0) for train in spikes), 0)
        neuron_contributions(spikes, duration=2, sampling_rate=1000)
        for original, after in zip(before, spikes):
            np.testing.assert_array_equal(original, after)
        negative = [np.array([]), np.array([-0.02]), np.array([0.3])]
        wrapped = [np.array([]), np.array([1.98]), np.array([0.3])]
        _, actual = isolated_neuron_signal(negative, 1, duration=2, sampling_rate=1000)
        _, expected = isolated_neuron_signal(wrapped, 1, duration=2, sampling_rate=1000)
        np.testing.assert_array_equal(actual, expected)
        self.assertTrue(np.all(actual[:1980] == 0))
        self.assertGreater(np.max(np.abs(actual[1981:])), 0)
        self.assertEqual(negative[1][0], -0.02)

    def test_isolating_neuron_one_preserves_its_signed_weight(self):
        spikes = [np.array([]) for _ in range(20)]
        spikes[1] = np.array([0.4])
        time, actual = isolated_neuron_signal(spikes, 1, duration=2, sampling_rate=1000, seed=42)
        weights = np.random.RandomState(42).normal(0, 1, 20)
        self.assertLess(weights[1], 0)
        self.assertAlmostEqual(actual[420], weights[1])
        self.assertAlmostEqual(time[420], 0.420)
        _, incorrectly_reindexed = generate_eeg([spikes[1]], duration=2, sampling_rate=1000, seed=42)
        self.assertGreater(incorrectly_reindexed[420], 0)
        self.assertFalse(np.allclose(actual, incorrectly_reindexed))

    def test_isolated_event_has_exact_original_fixed_kernel(self):
        spikes = [np.array([]) for _ in range(20)]
        spikes[0] = np.array([0.5968635029711842])
        _, actual = isolated_neuron_signal(spikes, 0, duration=2, sampling_rate=1000, seed=42)
        kernel_time = np.arange(0, 0.1, 0.001)
        kernel = kernel_time * np.exp(-kernel_time / 0.02)
        kernel /= kernel.max()
        weight = np.random.RandomState(42).normal(0, 1, 20)[0]
        expected = np.zeros(2000)
        expected[597:697] = weight * kernel
        np.testing.assert_allclose(actual, expected, rtol=1e-13, atol=1e-13)
        self.assertEqual(int(np.argmax(actual)), 617)

    def test_silent_sources_introduce_no_independent_noise(self):
        empty = [np.array([]) for _ in range(20)]
        rows = neuron_contributions(empty, duration=2, sampling_rate=1000, seed=42)
        np.testing.assert_array_equal(rows, np.zeros((20, 2000)))
        _, total = generate_eeg(empty, duration=2, sampling_rate=1000, seed=42)
        np.testing.assert_array_equal(total, rows.sum(axis=0))

    def test_frequency_sets_intervals_and_phase_spread_keeps_periods(self):
        for frequency in (5.0, 10.0):
            for phase_spread in (0.0, np.pi):
                with self.subTest(frequency=frequency, phase_spread=phase_spread):
                    spikes = simulate_spiking_neurons(
                        **dict(BASE, target_freq=frequency, phase_variation=phase_spread), seed=42
                    )
                    for train in spikes[: BASE["active_num"]]:
                        self.assertEqual(len(train), int(BASE["duration"] * frequency))
                        np.testing.assert_allclose(np.diff(train), 1 / frequency, atol=1e-13)
                    if phase_spread == 0:
                        np.testing.assert_array_equal(spikes[0], spikes[1])
                    else:
                        self.assertNotEqual(spikes[0][0], spikes[1][0])


if __name__ == "__main__":
    unittest.main()
