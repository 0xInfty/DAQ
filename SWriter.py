# -*- coding: utf-8 -*-
"""
Created on Wed Oct 17 16:19:03 2018

@author: Marcos
"""


import fwp_analysis as anly
import fwp_lab_instruments as ins
import fwp_save as sav
import matplotlib.pyplot as plt
import os
import nidaqmx as nid
import numpy as np
import fwp_wavemaker as wm


#%% Libraries for streamers
from nidaqmx.utils import flatten_channel_string
from nidaqmx.types import CtrFreq, CtrTime
from nidaqmx.stream_readers import AnalogSingleChannelReader, AnalogMultiChannelReader
from nidaqmx.stream_writers import AnalogSingleChannelWriter, AnalogMultiChannelWriter

#%% streamers (pag 57)
samplerate = 400e3
mode = nid.constants.TerminalConfiguration.NRSE

signal_frequency = 10
signal_pk_amplitude = 2
periods_to_measure = 50
name = 'Multichannel_Settling_Time'

# Other parameters
duration = periods_to_measure/signal_frequency
samples_to_measure = int(samplerate * duration/1000)

number_of_channels=3
channels_to_test = [
#                    "Dev20/ao0",
                    "Dev20/ao1",
#                    "Dev20/ao2",
                    ]

signal_slope = signal_pk_amplitude * signal_frequency

filename = sav.savefile_helper(name, 'NChannels_{}.txt')

header = 'Time [s]\tData [V]'

# ACTIVE CODE
seno = wm.Wave('sine', 100)
'''
class nidaqmx.stream_writers.AnalogMultiChannelWriter
write_many_sample(data, timeout=10.0)
data (numpy.ndarray) – Contains a 2D NumPy array of floating-point samples to
write to the task.
Each row corresponds to a channel in the task. Each column corresponds to a sample to
write to each channel. The order of the channels in the array corresponds to the order in
which you add the channels to the task.

'''
functionstowrite = seno.evaluate_sr(samplerate, duration=duration).T

with nid.Task() as write_task:
        write_task.ao_channels.add_ao_voltage_chan(
                flatten_channel_string(
                                channels_to_test),
                max_val=10, min_val=-10)
                
        writer = AnalogMultiChannelWriter(write_task.out_stream)
        values_to_test = functionstowrite
        writer.write_many_sample(values_to_test)
        # Start the read and write tasks before starting the sample clock
        # source task.
        write_task.start()
# Save measurement


#%% PWM

with nid.Task() as task:
#    task.co_channels.add_co_pulse_chan_time('Dev20/ctr0') #pin 38
#    sample = CtrTime(high_time=.001, low_time=.001)
#    sample = CtrTime()
    task.co_channels.add_co_pulse_chan_freq('Dev20/ctr0') # pin 38
    sample = CtrFreq(duty_cycle=.5, freq=20e3)
    task.write(sample)
