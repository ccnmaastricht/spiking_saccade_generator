# Spiking Saccade Generator

## Introduction
This repository contains an implementation of a spiking neural network model of the saccade generator in the reticular formation inspired by *A neural model of the saccade generator in the reticular formation* by Gancarz and Grossberg, Neural Networks, 1998.  

The spiking neural network consists of four recurrently connected populations of spiking neurons which are interconnected in a population-specific manner (see figure). 
These populations correspond to populations of neurons found in the reticular formation exhibiting similar responses in electrophysiological experiments (see, e.g., *The brainstem burst generator for saccadic eye movements* by Scudder et al., Exp Brain Res, 2002, for a review) and are believed to play different roles in the saccade generation process. 
The four populations are long-lead burst neurons (LLBN), excitatory and inhibitory burst neurons (EBN, IBN), and omni-pause neurons (OPN). 
The EBN and IBN together form a population of short-lead burst neurons (SLBN).

Electrophysiological studies show that in the time between two saccades the OPN fire regularly and inhibit the EBN. 
Upon initiation of the saccade generation process by a signal to LLBN encoding the desired displacement of the saccadic jump, the LLBN inhibit the OPN and excite the EBN. 
Due to the disinhibition of the EBN via the OPN and the direct excitation, the EBN themselves begin to burst. 
The activity of the EBN is not only passed to the motor neurons but also directed to the IBN, which in turn inhibit the LLBN. 
Due to the absence of inhibition the OPN become active again and deactivate the EBN.
This leads to a reset of the circuit to a state qualitatively identical to the initial one.

The interconnections between the four populations are schematically depicted below:  
![](figures/burst_generator.png)  
This fundamental building block takes responsibility for the movement of the eyes in **one** direction, e.g. horizontally left or vertically downwards.
To build a complete saccade generator, one first patches together two of these fundamental building blocks collapsing the two OPN populations into one, thereby obtaining a saccade generator for either horizontal or vertical saccades. 
For the second axis, one just duplicates this circuit.
In the model, the LLBN and the SLBN consist of two interconnected populations of excitatory and inhibitory multi-timescale adaptive threshold model neurons (see *Made-to-order spiking neuron model equipped with a multi-timescale adaptive threshold* by Kobayashi et al., Front Comp Neurosci, 2009) exhibiting bursty behaviour.
The activity of the excitatory subpopulation (EBN) of the SLBN determines the size of the saccades.
The OPN consist of two interconnected populations of excitatory and inhibitory leaky integrate-and-fire neurons.
The IBN consist of one interconnected population of inhibitory multi-timescale adaptive threshold neurons again showing bursty behavior.

The network satisfies Dale's principle and qualitatively takes different neuron characteristics (the distinction between bursting and non-bursting neurons) found in the reticular formation into account.
Our model differs from the one described by Gancarz and Grossberg in the respect that they model the saccade generator with neural populations, i.e. they represent the network with a system of coupled differential equations where each population is described via one of these equations.
Our network, however, is more biologically plausible since it operates with spiking neurons which not only satisfy Dale's principle
but also exhibit bursty dynamics, motivated by the neurons found in the saccade generator.
All simulations were carried out with NEST 2.18 using the PyNEST interface (Jordan et al., NEST 2.18.0. Zenodo, 2019, 10.5281/zenodo.2605422).
## Results
The constructed network exhibits the reset property described above if provided with sustained input.  
![](figures/response_saccade_generator_populations.png)  
Moreover, the EBN show a linear response upon sufficiently strong stimulation of the LLBN.  
![](figures/response_saccade_generator_ebn.png)  
This allows for a linear readout of the activity of the EBN to determine the saccade size.  
Building a complete saccade generator, one obtains the following:  
![](figures/performance_saccade_generator.png)

## Usage
In order to use the saccade generator one needs to first add the base directory to one's PYTHONPATH. If one is in the base directory of the spiking saccade generator, one just needs to execute the following (on a Unix-like system):
```
export PYTHONPATH=$PWD:$PYTHONPATH
``` 
Setting up the spiking saccade generator works as follows:
```
from saccade_generator import construct_saccade_generator
from helpers.i_o_scripts import stim_amp, saccadic_size_single_side
import nest

sg = construct_saccade_generator()

# fetch horizontal and vertical saccade generators
horizontal_sg = sg['horizontal']
vertical_sg = sg['vertical']

# fetch compartments controlling one extraocular muscle

# input populations
left_llbn = horizontal_sg['LLBN_l']
right_llbn = horizontal_sg['LLBN_r']
up_llbn = vertical_sg['LLBN_u']
down_llbn = vertical_sg['LLBN_d']

# output populations
left_ebn = horizontal_sg['EBN_l']
right_ebn = horizontal_sg['EBN_r']
up_ebn = vertical_sg['EBN_u']
down_ebn = vertical_sg['EBN_d']
```
In order to perform a saccade from the point (0,0) to (0.7,-0.2), where the maximal saccade size is 1.3, one needs to first provide the saccade generator with the proper input and then determine the readout from the recorded activity of the EBN:
```
# determine amplitude size of stimulation
amplitude_right = stim_amp(0.7, 1.3)
amplitude_down = stim_amp(0.2, 1.3)

# define start time and duration of stimulation
stim_time = 2000.
stim_duration = 75.

# create stimuli
dc_generator_right = nest.Create('dc_generator', 1)
dc_generator_up = nest.Create('dc_generator',1)

nest.SetStatus(dc_generator_right, {'amplitude' : stim_amp,
				    'start' : stim_time,
				    'stop' : stim_time + stim_duration}

nest.SetStatus(dc_generator_down, {'amplitude' : stim_amp,
				 'start' : stim_time,
				 'stop' : stim_time + stim_duration}

# create recording devices
spike_detector_right = nest.Create('spike_detector', 1)
spike_detector_left = nest.Create('spike_detector', 1)
spike_detector_up = nest.Create('spike_detector', 1)
spike_detector_down = nest.Create('spike_detector', 1)

# connect devices
nest.Connect(dc_generator_right, right_llbn)
nest.Connect(dc_generator_down, up_llbn)

nest.Connect(left_ebn, spike_detector_left)
nest.Connect(right_ebn, spike_detector_right)
nest.Connect(up_ebn, spike_detector_up)
nest.Connect(down_ebn, spike_detector_down)

# simulate
nest.Simulate(stim_time + 400.)

spike_times_left = nest.GetStatus(spike_detector_left, 'events')[0]
spike_times_right = nest.GetStatus(spike_detector_right, 'events')[0]
spike_times_up = nest.GetStatus(spike_detector_up, 'events')[0]
spike_times_down = nest.GetStatus(spike_detector_down, 'events')[0]

# obtain saccade size
saccade_size_left = saccadic_size_single_side([stim_time], spike_times_left, 1.3)
saccade_size_right = saccadic_size_single_side([stim_time], spike_times_right, 1.3)
saccade_size_up = saccadic_size_single_side([stim_time], spike_times_up, 1.3)
saccade_size_down = saccadic_size_single_side([stim_time], spike_times_down, 1.3)

saccade_displacement_x = saccade_size_right - saccade_size_left
saccade_displacement_y = saccade_size_up - saccade_size_down
```
For a more detailed description see the documentation in the code.  
To elicit a saccade, say, to the left one needs to provide the left LLBN with a DC input for 75 ms.  
The stimulus strength provided to the saccade generator to produce a saccade of a given size needs to be first normed by the maximal saccade size.  
This normed value then can be used to determine the amplitude of the direct current.  
The spikes of the EBN are counted in a time window of 200 ms after the sitmulus onset. Using this data, one calculates the population-averaged firing rate and from this may obtain the relative size of the saccade. 
To get the actual size, the produced values need to be scaled by the maximal saccade size.  
For more information see the evaluation scripts **saccade_generator_eval.py** and **saccade_generator_single_side_eval.py** as well as **i_o_scripts** in ./helpers.

## Requirements
See environment.yml.

## Contributors
Code written by Anno Kurth with support from Sacha van Albada.

## License
CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/, see License.md).

## Acknowledgments
This work was supported by the European Union Horizon 2020 research and innovation program (Grant 737691, Human Brain Project SGA2).
