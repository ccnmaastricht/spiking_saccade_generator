from saccade_generator_single_side import saccade_generator_single_side
from saccade_generator import construct_saccade_generator
from population_parameters import EBN_parameters

import nest
import numpy as np
from matplotlib import pyplot as plt

def eval_saccades(stim_times, target_points, N_vp = 2, msd = 1234):
    '''
    Evaluate performance of saccade generator

    Parameters
    ----------
    stim_times : np.array
        times at which saccade is initated

    target_point : np.ndarray
        target point of saccade

    N_vp : int
        number of virtual processes for nest simulation

    msd : int
        random seed for nest simulation

    Returns
    -------
    saccade_targets : np.ndarray
        point to which eye moves due to saccade

    error : float
        error between saccade_target and target_point
    '''

    min_stim_strength = 300.0
    max_stim_strength = 960.0

    diff_stim_strength = max_stim_strength - min_stim_strength

    stim_duration = 75.

    num_stims = len(stim_times)

    nest.ResetKernel()
    nest.SetKernelStatus({'local_num_threads' : N_vp})
    pyrngs = [np.random.RandomState(s) for s in range(msd, msd+N_vp)]
    nest.SetKernelStatus({'rng_seeds' : range(msd+N_vp+1, msd+2*N_vp+1)})

    saccade_generator = construct_saccade_generator()

    stimuli_l = nest.Create('dc_generator', num_stims)
    stimuli_r = nest.Create('dc_generator', num_stims)
    stimuli_u = nest.Create('dc_generator', num_stims)
    stimuli_d = nest.Create('dc_generator', num_stims)

    spike_detector_l = nest.Create('spike_detector', 1)
    spike_detector_r = nest.Create('spike_detector', 1)
    spike_detector_u = nest.Create('spike_detector', 1)
    spike_detector_d = nest.Create('spike_detector', 1)


    x_coord = np.copy(target_points[0])
    y_coord = np.copy(target_points[1])

    x_coord_shift = np.roll(np.copy(x_coord), 1)
    y_coord_shift = np.roll(np.copy(y_coord), 1)


    x_coord_shift[0] = 0
    y_coord_shift[0] = 0

    x_displacements = x_coord - x_coord_shift
    y_displacements = y_coord - y_coord_shift

    # generate inputs to saccade generator
    for i, time, in enumerate(stim_times):

        l_stim_size = 0.
        r_stim_size = 0.
        u_stim_size = 0.
        d_stim_size = 0.

        if x_displacements[i] > 0.:
            r_stim_size = x_displacements[i]*diff_stim_strength + min_stim_strength
            l_stim_size = 0.
        elif x_displacements[i] < 0:
            l_stim_size = (-1)*x_displacements[i]*diff_stim_strength + min_stim_strength
            r_stim_size = 0.
        else :
            l_stim_size = 0.
            r_stim_size = 0.

        if y_displacements[i] > 0.:
            u_stim_size = y_displacements[i]*diff_stim_strength + min_stim_strength
            d_stim_size = 0.
        elif y_displacements[i] < 0:
            d_stim_size = (-1)*y_displacements[i]*diff_stim_strength + min_stim_strength
            u_stim_size = 0.
        else :
            d_stim_size = 0.
            u_stim_size = 0.

        nest.SetStatus([stimuli_l[i]], {'amplitude' : l_stim_size,
                                        'start' : time,
                                        'stop' : time + stim_duration})

        nest.SetStatus([stimuli_r[i]], {'amplitude' : r_stim_size,
                                        'start' : time,
                                        'stop' : time + stim_duration})

        nest.SetStatus([stimuli_u[i]], {'amplitude' : u_stim_size,
                                        'start' : time,
                                        'stop' : time + stim_duration})

        nest.SetStatus([stimuli_d[i]], {'amplitude' : d_stim_size,
                                        'start' : time,
                                        'stop' : time + stim_duration})

    nest.Connect(stimuli_l, saccade_generator['horizontal']['LLBN_l'],
                 'all_to_all')
    nest.Connect(stimuli_r, saccade_generator['horizontal']['LLBN_r'],
                 'all_to_all')
    nest.Connect(stimuli_u, saccade_generator['vertical']['LLBN_u'],
                 'all_to_all')
    nest.Connect(stimuli_d, saccade_generator['vertical']['LLBN_d'],
                 'all_to_all')

    nest.Connect(saccade_generator['horizontal']['LLBN_l'], spike_detector_l)
    nest.Connect(saccade_generator['horizontal']['LLBN_r'], spike_detector_r)
    nest.Connect(saccade_generator['vertical']['LLBN_u'], spike_detector_u)
    nest.Connect(saccade_generator['vertical']['LLBN_d'], spike_detector_d)


    nest.Simulate(stim_times[-1] + 400.)

    spike_times_l = nest.GetStatus(spike_detector_l, 'events')[0]['times']
    spike_times_r = nest.GetStatus(spike_detector_r, 'events')[0]['times']
    spike_times_u = nest.GetStatus(spike_detector_u, 'events')[0]['times']
    spike_times_d = nest.GetStatus(spike_detector_d, 'events')[0]['times']

    # calculate saccade sizes
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

    saccade_displacements = np.zeros((2, num_stims))

    for i, stim_time in enumerate(stim_times):

        mask_l = (stim_time <= spike_times_l)*(spike_times_l <= stim_time + 200.)
        mask_r = (stim_time <= spike_times_r)*(spike_times_r <= stim_time + 200.)
        mask_u = (stim_time <= spike_times_u)*(spike_times_u <= stim_time + 200.)
        mask_d = (stim_time <= spike_times_d)*(spike_times_d <= stim_time + 200.)

        saccadic_spikes_l = spike_times_l[mask_l]
        saccadic_spikes_r = spike_times_r[mask_r]
        saccadic_spikes_u = spike_times_u[mask_u]
        saccadic_spikes_d = spike_times_d[mask_d]

        num_saccadic_spikes_l = np.size(saccadic_spikes_l)
        num_saccadic_spikes_r = np.size(saccadic_spikes_r)
        num_saccadic_spikes_u = np.size(saccadic_spikes_u)
        num_saccadic_spikes_d = np.size(saccadic_spikes_d)

        rate_l = num_saccadic_spikes_l/size_EBN/10
        rate_r = num_saccadic_spikes_r/size_EBN/10
        rate_u = num_saccadic_spikes_u/size_EBN/10
        rate_d = num_saccadic_spikes_d/size_EBN/10

        saccadic_size_l = dist(stim(rate_l))
        saccadic_size_r = dist(stim(rate_r))
        saccadic_size_u = dist(stim(rate_u))
        saccadic_size_d = dist(stim(rate_d))


        x_saccade_disp = saccadic_size_r - saccadic_size_l
        y_saccade_disp = saccadic_size_u - saccadic_size_d

        saccade_displacements[0][i] = x_saccade_disp
        saccade_displacements[1][i] = y_saccade_disp

    x_diff = saccade_displacements[0] - x_displacements
    y_diff = saccade_displacements[1] - y_displacements

    diffs = np.concatenate([x_diff, y_diff])

    rmse = np.sqrt((diffs**2).mean())

    return saccade_displacements, rmse


if __name__ == '__main__':

    stim_times = np.asarray([2000., 2600., 3300., 4000., 4500., 5200., 5800.,
                             6400., 6900.])
    target_points = np.asarray([[0.5, 0.1, -0.5, -0.2, 0.3, 0.7, 0.7, 0.25, -0.2],
                                [0.5, 0.2, -0.1, -0.5, -0.1, -0.6, -0.2,
                                 -0.68, -1.]])

    saccade_displacements, rmse = eval_saccades(stim_times, target_points)

    print(f'RMSE : {rmse}')

    color_list = ['r', 'b', 'g', 'c', 'm', 'y', 'k', 'tab:orange', 'tab:pink']
    plt.title(f'Performance of saccade generator, RMSE : {rmse}')
    num_stims = len(stim_times)
    for i in range(num_stims):
        if i == 0:
            plt.plot(target_points[0][i], target_points[1][i], marker = 'X',
                     color = color_list[i], label = 'True position of target')
            plt.plot(saccade_displacements[0][i],
                     saccade_displacements[1][i], marker = '*', color =
                     color_list[i], label = 'Position generated by saccade generator')
        else:
            plt.plot(target_points[0][i], target_points[1][i], marker = 'X',
                     color = color_list[i])
            plt.plot(saccade_displacements[0][i]+target_points[0][i-1],
                     saccade_displacements[1][i]+target_points[1][i-1], marker
                     = '*', color = color_list[i])
    plt.legend()
    plt.xticks([])
    plt.yticks([])
    plt.show()
