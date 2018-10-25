# -*- coding: utf-8 -*-
"""
This script is to make measurements with a National Instruments DAQ.

@author: GrupoFWP
"""

import fwp_analysis as anly
import fwp_lab_instruments as ins
import fwp_save as sav
import matplotlib.pyplot as plt
import os
import nidaqmx as nid
import numpy as np
from time import sleep

#%% Only_One_Measure
"""
This script makes a voltage measurement.

It measures in NRSE mode. Then, it applies Fourier 
Transformation to get the main frequency and its Fourier intensity. It 
only plots the data.

Warnings
--------
Taken from 'github.com/DopplerPavlovTichno/Placa-adquisicion' f35f2c2
Subtly modified by FWP Group
"""

# PARAMETERS

# Main parameters
duration = 1
samplerate = 5e3

# Other parameters
samples_per_channel = samplerate * duration
time = np.arange(0, duration, 1/samplerate)
mode = nid.constants.TerminalConfiguration.NRSE # Terminal configuration
# DIFFERENTIAL, NRSE, RSE, PSEUDODIFFERENTIAL

# ACTIVE CODE

# Make a measurement using NI DAQ.
with nid.Task() as task:
    task.ai_channels.add_ai_voltage_chan(
            "Dev20/ai1", # analog input AI 1
            terminal_config=mode)
    task.timing.cfg_samp_clk_timing(
            samplerate,
            samps_per_chan=int(samples_per_channel))
    data = task.read(
            number_of_samples_per_channel=int(samples_per_channel))
    task.wait_until_done()

# Make Fourier transformation and get main frequency
fourier = np.abs(np.fft.rfft(data)) # Fourier transformation
fourier_frequencies = np.fft.rfftfreq(len(data), d=1./samplerate)
max_frequency = fourier_frequencies[np.argmax(fourier)]

# Plot data
plt.figure()
plt.plot(time, data)
plt.xlabel('Tiempo (s)')
plt.ylabel('Tensión (V)')

# Plot Fourier
plt.figure()
plt.plot(fourier_frequencies, fourier)
plt.xlabel('Frecuencia (Hz)')
plt.ylabel('Intensidad de Fourier (ua)')
plt.title('{}'.format(max_frequency))

#%% Samplerate_Sweep
"""This scripts makes a sampling rate sweep for a fixed signal.

This code saves all measurements. It also applies Fourier Transformation 
to them, to get the main frequency and its Fourier amplitude. Then, it 
saves main frequency and its Fourier amplitude along with samplig rate.
"""

# PARAMETERS

# Main parameters
periods_to_measure = 100
signal_frequency = 1.2e3

samplerate_min = 100
samplerate_max = 10e3
samplerate_n = 200
mode = nid.constants.TerminalConfiguration.NRSE

name = 'Samplerate_Sweep'

# Other parameters
samplerate = np.linspace(samplerate_min,
                         samplerate_max,
                         samplerate_n)
duration = periods_to_measure / signal_frequency

folder = os.path.join(os.getcwd(),
                      'Measurements',
                      name)
folder = sav.new_dir(folder)
filename = lambda samplerate : os.path.join(
        folder, 
        '{:.0f}_Hz.txt'.format(samplerate))
header = 'Time [s]\tData [V]'

# ACTUAL CODE
               
fourier_data = [] # contains sampling rate, main frequency and its power
with nid.Task() as task:
    
    task.ai_channels.add_ai_voltage_chan(
            "Dev20/ai3",
            terminal_config=mode)
    
    for sr in samplerate:
        print('Doing {}Hz'.format(sr))
        
        samples_to_measure = int(sr * duration)
        task.timing.cfg_samp_clk_timing(
                rate=sr,
                samps_per_chan=samples_to_measure)
        
        signal = task.read(
                number_of_samples_per_channel=samples_to_measure)
        task.wait_until_done()
        
        time = np.linspace(0, duration, samples_to_measure)
        np.savetxt(filename(sr), np.array([time, signal]).T, 
                   header=header)
        
        max_frequency, fourier_peak = anly.main_frequency(signal, sr)
        fourier_data.append((sr, max_frequency, fourier_peak))

sav.savetext(os.path.join(folder, 'Data.txt'), 
             np.array(fourier_data),
             header=['Sampling rate (Hz)', 
                     'Main frequency (Hz)',
                     'Intensity'])

#%% Frequency_Sweep
"""This script makes a double sweep on frequency and samplerate.

For each samplerate, it sweeps on frequency. It saves all measurements. 
It also applies Fourier Transformation to get main frequency and its 
Fourier amplitude. For each samplerate, it saves main frequency and 
Fourier amplitude.
"""

# PARAMETERS

# Main parameters
samplerate_min = 10
samplerate_max = 400e3
samplerate_n = 20#100
mode = nid.constants.TerminalConfiguration.NRSE

signal_frequency_n = 50#500
port = 'USB::0x0699::0x0346::C034167::INSTR'

name = 'Frequency_Sweep'

# Other parameters
samplerate_step = int((samplerate_max - samplerate_min) / samplerate_n)
samplerate = np.arange(samplerate_min,
                       samplerate_max,
                       samplerate_step)

gen = ins.Gen(port=port, nchannels=1)

folder = os.path.join(os.getcwd(),
                      'Measurements',
                      name)
folder = sav.new_dir(folder)
filename = lambda samplerate, signal_frequency : os.path.join(
        folder, 
        'Sr_{:.0f}_Hz_Freq_{:.0f}_Hz.txt'.format(samplerate, 
                                                 signal_frequency))
filename_fourier = lambda samplerate : os.path.join(
        folder,
        'Sr_{:.0f}_Hz_Fourier.txt'.format(samplerate))
header = ['Time [s]', 'Data [V]']
header_fourier = ['Frequency (Hz)',
                  'Fourier frequency (Hz)',
                  'Fourier intensity (u.a.)']

# ACTIVE CODE

with nid.Task() as task:
    
    # Configure channel
    task.ai_channels.add_ai_voltage_chan(
            "Dev20/ai1",
            terminal_config=mode)
        
    for sr in samplerate:
        print('Doing SR {:.0f} Hz'.format(sr))
        
        # Make frequency array for a given samplerate
        signal_frequency_min = sr/10
        signal_frequency_max = 5*sr
        signal_frequency_step = samplerate_max - samplerate_min
        signal_frequency_step = int(signal_frequency_step / signal_frequency_n)
        signal_frequency = np.arange(signal_frequency_min,
                                     signal_frequency_max,
                                     signal_frequency_step)
        print('That leaves me on {} to {} Hz with a step {} Hz'.format(
                signal_frequency_min,
                signal_frequency_max,
                signal_frequency_step))
        
        # Configure clock and measurement
        duration = 10/signal_frequency_min
        samples_to_measure = int(sr * duration)
        task.timing.cfg_samp_clk_timing(
                rate=sr,
                samps_per_chan=samples_to_measure)

        fourier_data = []
        for freq in signal_frequency:
            print("There, doing {:.0f} Hz".format(freq))
            
            # Reconfigure function generator
            gen.output(True, channel=1, print_changes=False,
                       waveform='sin', frequency=freq, amplitude=2)

            # Measure with DAQ
            signal = task.read(
                    number_of_samples_per_channel=samples_to_measure)
            task.wait_until_done()

            # Save measurement
            time = np.linspace(0, duration, samples_to_measure)
            sav.savetext(filename(sr, freq),
                         np.array([time, signal]).T,
                         header=header)
            
            # Get main frequency and Fourier amplitude
            max_freq, fourier_peak = anly.main_frequency(signal, sr)
            fourier_data.append((freq, max_freq, fourier_peak))
            
            sleep(10e-3)

        # Save samplerate, main frequency and Fourier amplitude
        sav.savetext(filename_fourier(sr),
                     np.array(fourier_data), 
                     header=header_fourier)
gen.output(False)

gen.gen.close()

#%% Interbuffer_time
"""This script is designed to detect time delay between buffers on a fix signal.

It plays on a 10Hz, 2Vpp positive-slope ramp signal. It measures voltage vs 
time on one channel. Then it saves it.
"""

# PARAMETERS

# Main parameters
samplerate = 400e3
mode = nid.constants.TerminalConfiguration.NRSE

periods_to_measure = 10
signal_config = dict(
        frequency = 100000, #Hz
        amplitude = 2, #Vpp
        waveform = 'ram100'
        )

gen = ins.Gen('USB::0x0699::0x0346::C034167::INSTR', nchannels=1)

name = 'Interbuffer_Time'

# Other parameters
duration = periods_to_measure/signal_frequency
samples_to_measure = int(samplerate * duration)

filename=sav.savefile_helper(name,'signal_{}Hz_{}Vpp.txt')
header = 'Time [s]\tData [V]'
footer = 'Signal: {frequency:.0f}Hz, {amplitude}Vpp, {waveform}'.format(**signal_config)

# ACTIVE CODE

#gen.output(True, waveform='ramp', 
#           frequency=signal_frequency,
#           amplitude=2)
with nid.Task() as task: 
    
    # Configure channel
    
    
    task.ai_channels.add_ai_voltage_chan(
            "Dev20/ai1",
            terminal_config=mode)
    
    task.timing.cfg_samp_clk_timing(
            rate=samplerate,
            samps_per_chan=samples_to_measure)

    gen.output(True, **signal_config)
    
    signal = task.read(
            number_of_samples_per_channel=samples_to_measure)
    
    task.wait_until_done()

# Save measurement
time = np.linspace(0, duration, samples_to_measure)
np.savetxt(filename(signal_config['frequency'], signal_config['amplitude']),
           np.array([time, signal]).T,
           header=header, footer=footer)

gen.gen.close()
#%% Settling_Time
"""This script is designed to measure settling time for fixed conditions.

It plays on a low-frequency square wave. And this wave is measured at 
maximum samplerate in order to watch the time it takes for the NI DAQ 
to fixe to minimum and maximum voltage. This script saves time and 
voltage.

Warnings
--------
Could ask what voltage the DAQ is used to measure:
>>> with nid.Task() as task:
>>>     task.ai_channels.add_ai_voltage_chan(
>>>             "Dev20/ai1",
>>>             terminal_config=mode)
>>>     print("Vmax = ", task.ai_channels.ai_voltage_chan.ai_max)
>>>     print("Vmin = ", task.ai_channels.ai_voltage_chan.ai_min)
"""

# PARAMETERS

# Main parameters
samplerate = 400e3
mode = nid.constants.TerminalConfiguration.NRSE

signal_frequency = 10#500
periods_to_measure = 10

name = 'Settling_Time'

# Other parameters
duration = periods_to_measure/signal_frequency
samples_to_measure = int(samplerate * duration)

folder = os.path.join(os.getcwd(),
                      'Measurements',
                      name)
folder = sav.new_dir(folder)
filename=os.path.join(folder, name + '.txt')
header = 'Time [s]\tData [V]'

# ACTIVE CODE

#gen.output(True, waveform='square', 
#           frequency=signal_frequency,
#           amplitude=2)
with nid.Task() as task:
    
    # Configure channel
    task.ai_channels.add_ai_voltage_chan(
            "Dev20/ai1",
            terminal_config=mode)
    
    task.timing.cfg_samp_clk_timing(
            rate=samplerate,
            samps_per_chan=samples_to_measure)

    signal = task.read(
            number_of_samples_per_channel=samples_to_measure)
    task.wait_until_done()

# Save measurement
time = np.linspace(0, duration, samples_to_measure)
np.savetxt(filename,
           np.array([time, signal]).T,
           header=header)

#%% Interchannel_Time
"""This script is designed to measure interchannel time-delay.

It plays on a low-frequency ramp wave (sawtooth like). And this wave is 
measured at maximum samplerate in order to watch the time it takes for 
the NI DAQ to fix to another channel.

This is repeated on a sweep for different number of channels. For each 
of them, it saves time and voltage.

"""

# PARAMETERS

# Main parameters
samplerate = 100e3
mode = nid.constants.TerminalConfiguration.NRSE

signal_config = dict(
        frequency = 50e3, #Hz
        amplitude = 2, #Vpp
        waveform = 'ram100'
        )

gen = ins.Gen('USB::0x0699::0x0346::C034167::INSTR', nchannels=1)

periods_to_measure = 10

name = 'Interchannel_Time_{:.0f}Hz'.format(signal_config['frequency'])

# Other parameters
duration = periods_to_measure/signal_frequency
samples_to_measure = int(samplerate * duration)
channels = [
            "Dev20/ai0",
            "Dev20/ai1",
            "Dev20/ai2",
#            "Dev20/ai3",
#            "Dev20/ai4",
#            "Dev20/ai5",
            "Dev20/ai9 ",
#            "Dev20/ai11"
            ]

signal_slope = signal_config['frequency'] * signal_config['amplitude']

filename = sav.savefile_helper(name,'NChannels_{}_signal_{:.0f}Hz.txt')

def headermaker(nchannels, channels=channels):
    header = 'time[s]'
    for ch in channels[:nchannels]:
        header += '\t ch {} [V]'.format(ch.split('/')[-1])
    return header

footer = 'samplingrate={:.0f}Hz, mode={}, Vpp={amplitude}V, signal_freq={frequency:.0f}Hz, waveform={waveform}'.format(
            samplerate,
            str(mode).split('.')[-1],
            **signal_config)

# ACTIVE CODE

gen.output(True, **signal_config)

with nid.Task() as task:

    for nchannels, channel in enumerate(channels):
        
        # Configure channel
        task.ai_channels.add_ai_voltage_chan(
                channel,
                terminal_config=mode)
#                ai_max=2,
#                ai_min=-2)
        
        # Set sampling_rate and samples per channel
        task.timing.cfg_samp_clk_timing(
                rate=samplerate,
                samps_per_chan=samples_to_measure)
        
        # Measure
        signal = task.read(
                number_of_samples_per_channel=samples_to_measure)
        task.wait_until_done()
        
        # Save measurement
        nchannels += 1
        print("For {} channels, signal has size {}".format(
                nchannels,
                np.size(signal)))
        time = np.expand_dims(np.linspace(0, duration, samples_to_measure), axis=0)
        
        data = np.array(signal).T
        if data.ndim==1:
            data = np.expand_dims(data, axis=0).T

        data = np.concatenate((time.T, data), axis=1)
        
        np.savetxt(filename(nchannels, signal_frequency), data,
                   header=headermaker(nchannels),
                   footer=footer)

gen.gen.close()
#%% Interchannel_Time_Order
"""This script is designed to measure interchannel time-delay.

It generates a low-frequency ramp wave (sawtooth like). And this wave is 
measured at maximum samplerate in order to watch the time it takes for 
the NI DAQ to fix to another channel.

This is repeated on a sweep for different order of channels. For each 
of them, it saves time and voltage.

"""

# PARAMETERS

# Main parameters
samplerate = 100e3
mode = nid.constants.TerminalConfiguration.NRSE

signal_config = dict(
        frequency = 10e3, #Hz
        amplitude = 2, #Vpp
        waveform = 'ram100'
        )
gen_totalchannels = 1
gen = ins.Gen('USB::0x0699::0x0346::C034167::INSTR', nchannels=gen_totalchannels)

periods_to_measure = 10

name = 'Interchannel_Time_Order_{:.0f}Hz'.format(signal_config['frequency'])

channels_key = ["Dev20/ai3", "Dev20/ai0", "Dev20/ai1", "Dev20/ai2"]
#"Dev20/ai3", # rojo
#"Dev20/ai0", #naranja
#"Dev20/ai1", #amarillo
#"Dev20/ai2", #blanco
channels_order = [[0,1,2,3],
                  [3,2,1,0],
                  [0,3,1,2],
                  [0,2,1,3]]

# Other parameters
duration = periods_to_measure/signal_frequency
samples_to_measure = int(samplerate * duration)

channels = {i:ch for i, ch in enumerate(channels_key)}

folder = os.path.join(os.getcwd(),
                      'Measurements',
                      name)
folder = sav.new_dir(folder)
filename = lambda order : os.path.join(
        folder, 
        'Channels_{}_{:.0f}Hz.txt'.format(
                ''.join([str(i) for i in order]),
                signal_config['frequency']))
        
def headermaker(order, channels=channels):
    header = 'time[s]'
    for key in order:
        header += '\t ch {} [V]'.format(channels[key].split('/')[-1])
    return header

footer = 'samplingrate={:.0f}Hz, mode={}, Vpp={amplitude}V, signal_freq={frequency:.0f}Hz, waveform={waveform}'.format(
            samplerate,
            str(mode).split('.')[-1],
            **signal_config)

# ACTIVE CODE

gen.output(True, **signal_config)

for order in channels_order:
    
    with nid.Task() as task:

#        task.ai_channels.ai_max = 5
#        task.ai_channels.ai_min = -5
        
        for key in order:
        
            # Configure channel
            task.ai_channels.add_ai_voltage_chan(
                    channels[key],
                    terminal_config=mode,
                    min_val=-5,
                    max_val=5)
        
        # Set sampling_rate and samples per channel
        task.timing.cfg_samp_clk_timing(
                rate=samplerate,
                samps_per_chan=samples_to_measure)

        # Measure
        signal = task.read(
                number_of_samples_per_channel=samples_to_measure)
        task.wait_until_done()
        
        # Save measurement
        time = np.expand_dims(np.linspace(0, duration, samples_to_measure),
                              axis=0)
        
        data = np.array(signal).T
        if data.ndim==1:
            data = np.expand_dims(data, axis=0).T

        data = np.concatenate((time.T, data), axis=1)
        
        np.savetxt(filename(order), data,
                   header=headermaker(order),
                   footer=footer)

gen.output(False)
gen.gen.close()

#%% Libraries for streamers
from nidaqmx.utils import flatten_channel_string
from nidaqmx.stream_readers import (AnalogSingleChannelReader, AnalogMultiChannelReader)
#from nidaqmx.stream_writers import (AnalogSingleChannelWriter, AnalogMultiChannelWriter)

#%% streamers (pag 57)
samplerate = 400e3
mode = nid.constants.TerminalConfiguration.NRSE

signal_frequency = 10
signal_pk_amplitude = 2
periods_to_measure = 50
gen_port = 'ASRL1::INSTR'
gen_totalchannels = 2 # Ojo que no siempre hay dos canales

name = 'Multichannel_Settling_Time'

# Other parameters
duration = periods_to_measure/signal_frequency
samples_to_measure = int(samplerate * duration/1000)

number_of_channels=3
channels_to_test = [
                    "Dev20/ai0",
                    "Dev20/ai1",
                    "Dev20/ai2",
                    ]

gen = ins.Gen(port=gen_port, nchannels=gen_totalchannels)
signal_slope = signal_pk_amplitude * signal_frequency

#folder = os.path.join(os.getcwd(),
#                      'Measurements',
#                      name)
#folder = sav.new_dir(folder)
#filename = lambda nchannels : os.path.join(
#        folder, 
#        'NChannels_{}.txt'.format(nchannels))
filename = sav.savefile_helper(dirname = name, 
                               filename_template = 'NChannels_{}.txt')

header = 'Time [s]\tData [V]'

# ACTIVE CODE

gen.output(True, waveform='ramp100', 
           frequency=signal_frequency,
           amplitude=2)

with nid.Task() as read_task:

    read_task.ai_channels.add_ai_voltage_chan(
        flatten_channel_string(channels_to_test),
        max_val=10, min_val=-10)
    reader = AnalogMultiChannelReader(read_task.in_stream)

    # Start the read and write tasks before starting the sample clock
    # source task.
    read_task.start()

    values_read = np.zeros(
        (number_of_channels, samples_to_measure), dtype=np.float64)
    reader.read_many_sample(
        values_read, number_of_samples_per_channel=samples_to_measure,
        timeout=2)

    #np.testing.assert_allclose(values_read, rtol=0.05, atol=0.005)
# Save measurement

nchannels = nchannels + 1
print("For {} channels, signal has size {}".format(
        nchannels,
        np.size(signal)))
time = np.linspace(0, duration, samples_to_measure)
try:
    data = np.zeros((values_read[0,:], values_read[:,0]+1))
    data[:,0] = time
    data[:,1:] = values_read[0,:]
    data[:,2:] = values_read[1,:]
    data[:,3:] = values_read[2,:]
except IndexError:
    data = np.array([time, signal]).T
np.savetxt(filename(nchannels), data, header=header)

gen.output(False)
gen.gen.close()
