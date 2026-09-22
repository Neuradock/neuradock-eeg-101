"""Original user-provided spike-to-EEG core, preserved without algorithm edits.

Source: S1/S1_1_EEG_source.ipynb, second code cell (zero-based index 1).
Only these two definitions are extracted; the original dashboard is not executed.
Function hashes and source provenance are recorded in docs/spike2eeg-source.json.
"""

import numpy as np


def simulate_spiking_neurons(N, active_num, target_freq, phase_variation, background_freq, duration=1.0, seed=42):
    np.random.seed(seed)
    T = 1.0 / target_freq if target_freq > 0 else float('inf')
    spikes = []
    
    for i in range(N):
        if i < active_num:
            phase = np.random.uniform(-phase_variation, phase_variation)
            n_cycles = int(duration * target_freq)
            base_times = np.arange(n_cycles) * T
            spike_times = base_times + (phase / (2 * np.pi * target_freq))
            spike_times = spike_times[spike_times < duration]
        else:
            isi = np.random.exponential(1/background_freq, size=int(1.5*background_freq*duration))
            spike_times = np.cumsum(isi)
            spike_times = spike_times[spike_times < duration]
        
        spikes.append(spike_times)
    
    return spikes


def generate_eeg(spike_trains, duration=1.0, sampling_rate=1000, seed=42):
    # 使用固定的随机种子确保权重一致
    rand_state = np.random.RandomState(seed)
    num_neurons = len(spike_trains)
    t = np.linspace(0, duration, int(sampling_rate*duration), endpoint=False)
    
    weights = rand_state.normal(loc=0.0, scale=1.0, size=num_neurons)
    
    tau = 0.02
    psp_time = np.arange(0, 0.1, 1/sampling_rate)
    psp = psp_time * np.exp(-psp_time/tau)
    psp /= np.max(psp)
    
    eeg = np.zeros_like(t)
    
    for i in range(num_neurons):
        spike_train = np.zeros_like(t)
        indices = np.round(spike_trains[i] * sampling_rate).astype(int)
        indices = indices[indices < len(t)]
        spike_train[indices] = 1.0
        
        contribution = np.convolve(spike_train, psp, mode='full')[:len(t)]
        eeg += weights[i] * contribution
    
    return t, eeg
