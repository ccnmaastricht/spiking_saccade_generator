from population_parameters import EBN_parameters
import numpy as np

def saccadic_size_single_side(stim_times, spike_times, scale = 1):
    '''
    Determine size of saccade upon stimulation of saccade generator

    Parameters
    ----------
    stim_times : np.array
        times when stimulations to generate saccades

    spike_times : np.array
        array of spike times of EBNs

    scale : float
        determine size of ouput

    Return
    ------
    saccadic_sizes : np.array
        sizes of saccades
    '''

    y_intercept = -6.929000047679375
    slope = 0.02500284479148012

    min_stim = 300.
    max_stim = 960.
    diff_stim = max_stim - min_stim

    stim = lambda response : (response - y_intercept)/slope

    def dist(stim):

        dist = (stim - min_stim)/diff_stim

        if dist < 0:
            dist = 0
        elif dist > 1:
            dist = 1

        return dist

    size_EBN = EBN_parameters['n_ex']

    saccades_sizes = []

    for stim_time in stim_times:

        mask = (stim_time <= spike_times)*(spike_times <= stim_time + 200.)
        saccadic_spikes = spike_times[mask]

        num_saccadic_spikes = np.size(saccadic_spikes)
        rate = num_saccadic_spikes/size_EBN

        saccadic_size = dist(stim(rate))

        saccades_sizes.append(saccadic_size)

    return np.asarray(saccades_sizes)


