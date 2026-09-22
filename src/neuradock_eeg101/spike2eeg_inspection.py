"""Inspect source contributions by calling, not rewriting, the original core."""

import numpy as np

from .spike2eeg import generate_eeg


def isolated_neuron_signal(spike_trains, neuron_index, duration, sampling_rate, seed=42):
    """Keep one neuron's events, preserving its index and the full weight draw.

    Empty trains silence other inputs without shortening or reordering the list.
    All rounding, convolution, signed weights, and boundary behavior remain in
    the original generate_eeg function. The supplied trains are never modified.
    """
    isolated = [np.array([], dtype=float) for _ in spike_trains]
    isolated[neuron_index] = np.asarray(spike_trains[neuron_index])
    return generate_eeg(isolated, duration=duration, sampling_rate=sampling_rate, seed=seed)


def neuron_contributions(spike_trains, duration, sampling_rate, seed=42):
    """Return each source's weighted contribution using the original generator."""
    return np.array([
        isolated_neuron_signal(spike_trains, i, duration, sampling_rate, seed)[1]
        for i in range(len(spike_trains))
    ])
