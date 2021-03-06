# -*- coding: utf-8 -*-
"""
This script was used to start a NI 6212 DAQ control loop.

This script uses 'fwp_old_daq' module, which is based on another group's
code. The goal was to write a control loop to raise an object a constant 
given velocity.

@author: Usuario
"""

import fwp_old_daq as old
import fwp_wavemaker as wm
import fwp_save as sav
import nidaqmx as nid
from nidaqmx import stream_readers as sr
from nidaqmx import stream_writers as sw
from nidaqmx.utils import flatten_channel_string
import numpy as np
from time import sleep

#%% Just turn on a PWM signal

pwm_channels = 'Dev1/ctr0' # Clock output
pwm_frequency = 100
pwm_duty_cycle = .5

with nid.Task() as task_co:
    
    # Configure clock output
    channels_co = old.pwm_outputs(
            task_co,
            physical_channels = pwm_channels,
            frequency = pwm_frequency,
            duty_cycle = pwm_duty_cycle
            )
    
    # Set contiuous PWM signal
    task_co.timing.cfg_implicit_timing(
            sample_mode = nid.constants.AcquisitionType.CONTINUOUS)
    
    # Create a PWM stream
    stream_co = sw.CounterWriter(task_co.out_stream)

    # Play    
    task_co.start()
    sleep(10)

#%% Change PWM mean value

pwm_channels = 'Dev1/ctr0' # Clock output
pwm_frequency = 100
pwm_duty_cycle = np.linspace(.1,1,10)

with nid.Task() as task_co:
    
    # Configure clock output
    channels_co = old.pwm_outputs(
            task_co,
            physical_channels = pwm_channels,
            frequency = pwm_frequency,
            duty_cycle = pwm_duty_cycle[0]
            )
    
    # Set contiuous PWM signal
    task_co.timing.cfg_implicit_timing(
            sample_mode = nid.constants.AcquisitionType.CONTINUOUS)
    
    # Create a PWM stream
    stream_co = sw.CounterWriter(task_co.out_stream)

    # Play    
    task_co.start()
    
    for dc in pwm_duty_cycle:
        sleep(3)
        channels_co.co_pulse_duty_cyc = dc
        stream_co.write_one_sample_pulse_frequency(
                frequency = channels_co.co_pulse_freq,
                duty_cycle = channels_co.co_pulse_duty_cyc
                )
        print("Hope I changed duty cycle to {:.2f} x'D".format(dc))
        sleep(3)
    task_co.stop()

#%% Moni's Voltage Control Loop --> streamers (pag 57)

name = 'V_Control_Loop'

# DAQ Configuration
samplerate = 400e3
mode = nid.constants.TerminalConfiguration.NRSE
number_of_channels=2
channels_to_read = ["Dev1/ai0", "Dev1/ai2"]
channels_to_write = ["Dev1/ao0", "Dev1/ao1"]

# Signal's Configuration
signal_frequency = 10
signal_pk_amplitude = 2
periods_to_measure = 50

# PID's Configuration
pidvalue=1
pidconstant=0.1

# ACTIVE CODE

# Other configuration
duration = periods_to_measure/signal_frequency
samples_to_measure = int(samplerate * duration/1000)
filename = sav.savefile_helper(dirname = name, 
                               filename_template = 'NChannels_{}.txt')
header = 'Time [s]\tData [V]'

# First I make a ramp
waveform= wm.Wave('triangular', frequency=10, amplitude=1)
output_array = waveform.evaluate_sr(sr=samplerate, duration=duration)

# Now I define a callback function
def callback(task_handle, every_n_samples_event_type,
             number_of_samples, callback_data):
    
    print('Every N Samples callback invoked.')

    samples = reader.read_many_sample(
            values_read, 
            number_of_samples_per_channel=number_of_samples,
            timeout=2)
    
    global output_array
    non_local_var['samples'].extend(samples)
    
    if max(samples) > (pidvalue+0.1):
        delta = max(samples) - pidvalue
        output_array -= pidconstant * delta
        
    elif max(samples) < (pidvalue-0.1):
         delta = pidvalue - max(samples)
         output_array += pidconstant * delta
         
    return 0

# Now I start the actual PID loop        
with nid.Task() as write_task, nid.Task() as read_task:

    # First I configure the reading
    read_task.ai_channels.add_ai_voltage_chan(
        flatten_channel_string(channels_to_read),
        max_val=10, min_val=-10)
    reader = sr.AnalogMultiChannelReader(read_task.in_stream)
    
    # Now I configure the writing
    write_task.ao_channels.add_ao_voltage_chan(
            flatten_channel_string(channels_to_write),
            max_val=10, min_val=-10)
    writer = sw.AnalogMultiChannelWriter(write_task.out_stream)

    # source task.
    # Start the read and write tasks before starting the sample clock
    # source task.

    read_task.start()
    read_task.register_every_n_samples_acquired_into_buffer_event(
            20, # Every 20 samples, call callback function
            callback) 
    
    write_task.start()
    writer.write_many_sample(output_array)

    values_read = np.zeros((number_of_channels, samples_to_measure),
                           dtype=np.float64)
    reader.read_many_sample(
        values_read, number_of_samples_per_channel=samples_to_measure,
        timeout=2)
        
    non_local_var = {'samples': []}     
    
#    np.testing.assert_allclose(values_read, rtol=0.05, atol=0.005)

## Save measurement
#
#nchannels = nchannels + 1
#print("For {} channels, signal has size {}".format(
#        nchannels,
#        np.size(signal)))
#time = np.linspace(0, duration, samples_to_measure)
#try:
#    data = np.zeros((values_read[0,:], values_read[:,0]+1))
#    data[:,0] = time
#    data[:,1:] = values_read[0,:]
#    data[:,2:] = values_read[1,:]
#    data[:,3:] = values_read[2,:]
#except IndexError:
#    data = np.array([time, signal]).T
#np.savetxt(filename(nchannels), data, header=header)