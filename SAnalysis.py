# -*- coding: utf-8 -*-
"""
This script is to analyse measurements made with NI DAQ.

@author: GrupoFWP
"""

import fwp_analysis as anly
import fwp_plot as fplt
import fwp_save as sav
import matplotlib.pyplot as plt
import numpy as np
import os
#import fwp_string as fstr
from scipy.signal import find_peaks

class Struct:
    def __init__(self):
        pass
    
    def __repr__(self):
        return str(vars(self))
#%% Samplerate_Sweep (by Val)
"""This script analyses a samplerate sweep for a fixed signal.

It makes an animation showing voltage vs time graphs for different 
samplerates. It plots main frequency and its Fourier amplitude as a 
function of samplerate.
"""

# PARAMETERS

# Main parameters
periods_to_meassure = 100
signal_frequency = 1.2e3

samplerate_min = 100
samplerate_max = 10e3
samplerate_n = 200

name = 'Samplerate_Sweep'

# Other parameters
samplerate = np.linspace(samplerate_min,
                         samplerate_max,
                         samplerate_n)
duration = periods_to_meassure / signal_frequency

folder = os.path.join(os.getcwd(),
                      'Measurements',
                      name)
filename = lambda samplerate : os.path.join(
        folder, 
        '{}_Hz.txt'.format(samplerate))

# ACTIVE CODE

all_time = []
all_voltage = []
for sr in samplerate:
    time, voltage = np.loadtxt(filename(sr), unpack=True)
    all_time.append(list(time))
    all_voltage.append(list(voltage))
del voltage, time

fig = plt.figure()
ax = plt.axes()
ax.set_xlabel("Tiempo (s)")
ax.set_ylabel("Voltaje (V)")
fplt.add_style(fig.number, linewidth=1)
animation = fplt.animation_2D(
        all_time, 
        all_voltage,
        label_function=lambda i : "Frec. muestreo {:.1f} Hz".format(
                samplerate[i]),
        frames_number=30,
        fps=10,
        new_figure=False)

sav.saveanimation(animation,
                  os.path.join(folder, 'Video.gif'))
# This doesn't work and I'm not sure why. It does work saving it as mp4.

samplerate, frequencies, fourier_peak = np.loadtxt(
        os.path.join(folder, 'Data.txt'), 
        unpack=True)

plt.figure()
plt.subplot(211)
plt.plot(samplerate, frequencies, '.')
plt.title("Fourier para frecuencia fija {} Hz".format(signal_frequency))
plt.ylabel('Frecuencia (Hz)')
plt.subplot(212)
plt.plot(samplerate, fourier_peak, '.', label='Amplitud de Fourier')
plt.ylabel("Amplitud (u.a.)")
plt.xlabel("Frecuencia de muestreo (Hz)")
fplt.add_style(linewidth=1)

#%% By Val

# PARAMETERS

# Main parameters
samplerate = 4e3

signal_frequency = 10
signal_pk_amplitude = 2
periods_to_measure = 10
#gen_port = 'ASRL1::INSTR'
#gen_totalchannels = 2

name = 'Multichannel_Settling_Time'
folder = os.path.join(os.getcwd(),
                      'Measurements',
                      name)
filename = lambda nchannels : os.path.join(
        folder, 
        'NChannels_{}.txt'.format(nchannels))

# Other parameters
channels = ["Dev20/ai0",
            "Dev20/ai1",
            "Dev20/ai9",
            "Dev20/ai3",
            "Dev20/ai8",
#            "Dev20/ai5",
#            "Dev20/ai6",
            "Dev20/ai11"]

signal_slope = signal_pk_amplitude * signal_frequency

all_data = {}
for nchannels in range(len(channels)):
    all_data.update({nchannels+1: np.loadtxt(filename(nchannels+1))})
    
plt.figure()
plt.plot(all_data[3][:,0], all_data[3][:,1:])



#%% Sample rate + frequency sweep (by Moni)
name = 'Frequency_Sweep'
folder = os.path.join(os.getcwd(),
                      'Measurements',
                      name)

#get only flies corresponding to raw data, not their Fourirer transform:
rawdata=[os.path.join(
        folder,f) for f in os.listdir(folder) if not f.endswith('Fourier.txt')].sort()
        
maxt= []

sr = [f.split('_')[2] for f in rawdata]
freqgen = [f.split('_')[5] for f in rawdata]

for f in rawdata:
    time,data=np.loadtxt(f, unpack=True)
#    np.append(sr,f.split('_')[2])
#    np.append(freqgen,f.split('_')[5])
    for i in range(2, len(data)-2):
        if data[i]>data[i-1] and data[i]>data[i+1] and data[i]>data[i-2] and data[i]>data[i+2]:
            np.append(maxt, time[i])


deltatau=np.zeros(len(maxt)-1)
for j in range(len(maxt)-1):
    deltatau=maxt[j]-maxt[j+1]

freqm=np.mean(deltatau)/2*np.pi


plt.figure()
plt.plot(freqm, frequencies, '.')
plt.title('Frecuencias')
plt.ylabel('Frecuencia a mano (Hz)')
plt.xlabel('Frecuencia gen (Hz)')
plt.grid()
plt.show()

#%% by Marcos

name = 'Frequency_Sweep'
folder = os.path.join(os.getcwd(),
                      'Measurements',
                      name)

# Por Fourier:
fourierfiles = sorted([os.path.join(
        folder,f) for f in os.listdir(folder) if f.endswith('Fourier.txt')])
    
f = fourierfiles[10]
actual_freq, fourier_freq, fourier_power = np.loadtxt(f, unpack=True)
#plt.stem(actual_freq, np.ones_like(actual_freq))
#plt.stem(fourier_freq, fourier_power)

plt.plot(actual_freq, fourier_freq,'-o')
plt.plot(actual_freq, actual_freq)
plt.xlabel('Actual frequency [Hz]')
plt.ylabel('Fourier calculated frequency [Hz]')
plt.legend(('Datos', 'Pendiente 1'))
plt.ylim((0, max(fourier_freq) * 1.1))
plt.title(os.path.basename(f))

#%% Por picos:
rawfiles = sorted([os.path.join(
        folder,f) for f in os.listdir(folder) if not f.endswith('Fourier.txt')])

# divide all file names by 
rawfiles_by_sr = {}
current_sr = None
temp = []

for f in rawfiles:
    this_sr = fstr.find_1st_number(os.path.basename(f))
    if current_sr == this_sr:
        temp.append(f)
    else:
        if len(temp)!=0:
            rawfiles_by_sr[current_sr] = temp
        current_sr = this_sr
        temp = [f]

# sorted list of sampling rates
samplingrates = sorted(list(rawfiles_by_sr.keys()))

cual = 10
archivos = rawfiles_by_sr[samplingrates[cual]]

signal_freqs = {}
#time, data = np.loadtxt(f, unpack=True)
for f in archivos:
    freq = fstr.find_numbers(f)[1]
    signal_freqs[freq] = Struct()
    signal_freqs[freq].file = f
    
    time, data = np.loadtxt(f, unpack=True)
    signal_freqs[freq].duration = time[-1]
    signal_freqs[freq].nperiods = len(find_peaks(data)[0])
    signal_freqs[freq].maybe_freq = len(find_peaks(data)[0])/time[-1]

#to be able to plot with lines, keys must be sorted
actual_freq = sorted(list(signal_freqs.keys()))

plt.plot(actual_freq, [signal_freqs[f].maybe_freq for f in actual_freq], '-o')

#%% interbuffer time

name = 'Interbuffer_Time'
folder = os.path.join(os.getcwd(),
                      'Measurements',
                      name)
                      
interbuferfile = os.path.join(
        folder,'Interbuffer_Time.txt')

time, voltage = np.loadtxt(interbuferfile, unpack=True)
dt=time[5]-time[4]

def Diffincent(u,dx):
    w=len(u)
    Diff=np.zeros(w)
    for i in range(w):
        if i == 0:
            Diff[0]=(u[1]-u[w-1])/(2*dx)
        elif i == w-1:
            Diff[i]=(u[0]-u[i-1])/(2*dx)
        else:
            Diff[i]=(u[i+1]-u[i-1])/(2*dx)
    return Diff

slopederivative=Diffincent(voltage,dt)
#%% 
plt.plot(time[2500:3800], slopederivative[2500:3800],'g-o')
#plt.plot(time[2500:3800], voltage[2500:3800])
plt.xlabel('Time')
plt.ylabel('First derivative of Signal')
plt.title(os.path.basename(f))
plt.grid()
plt.show()

#%% 
# Make Fourier transformation and get main frequency
samplerate = 400e3
fourier = np.abs(np.fft.rfft(voltage)) # Fourier transformation
fourier_frequencies = np.fft.rfftfreq(len(voltage), d=1./samplerate)
max_frequency = fourier_frequencies[np.argmax(fourier)]


# Plot Fourier
plt.figure()
plt.plot(fourier_frequencies[1000:2000], fourier[1000:2000])
plt.xlabel('Frecuencia (Hz)')
plt.ylabel('Intensidad de Fourier (ua)')
plt.title('{}'.format(max_frequency))


#%% Interchanneltime: cargo variables

name = 'Interchannel_Time'
folder = os.path.join(os.getcwd(),
                      'Measurements',
                      name)
                      
interchannelfile1 = os.path.join(
        folder,'NChannels_1.txt')
time1, voltage1ch1 = np.loadtxt(interchannelfile1, unpack=True)

interchannelfile2 = os.path.join(
        folder,'NChannels_2.txt')
time2, voltage2ch1,voltage2ch2 = np.loadtxt(interchannelfile2, unpack=True)

interchannelfile3 = os.path.join(
        folder,'NChannels_3.txt')
time3, voltage3ch1,voltage3ch2,voltage3ch3 = np.loadtxt(interchannelfile3, unpack=True)

interchannelfile4 = os.path.join(
        folder,'NChannels_4.txt')
time4, voltage4ch1, voltage4ch2, voltage4ch3, voltage4ch4 = np.loadtxt(interchannelfile4, unpack=True)

interchannelfile5 = os.path.join(
        folder,'NChannels_5.txt')
time5, voltage5ch1, voltage5ch2, voltage5ch3, voltage5ch4, voltage5ch5 = np.loadtxt(interchannelfile5, unpack=True)

interchannelfile6 = os.path.join(
        folder,'NChannels_6.txt')
time6, voltage6ch1, voltage6ch2, voltage6ch3, voltage6ch4, voltage6ch5, voltage6ch6 = np.loadtxt(interchannelfile6, unpack=True)


#%% 

plt.plot(time2[1400:1700], voltage2ch1[1400:1700],'r-')
plt.plot(time2[1400:1700], voltage2ch2[1400:1700],'b-')
plt.xlabel('Time')
plt.ylabel('coltage')
plt.grid()
plt.show()

#%% prueba 2

name = 'Interchannel_Time'
folder = os.path.join(os.getcwd(),
                      'Measurements',
                      name)
interchanneltime=[[],[],[],[],[]]
#I've got 5 files with multiple channel adquisition. I want to see how interchannel value changes.
for i in range(5):
    interchannelfile = os.path.join(folder,'NChannels_{}.txt'.format(i+2)) #I choose the corresponding file
    datos= np.loadtxt(interchannelfile, unpack=True) # I load the file data
    time=datos[0,:]#first set of values are time
    voltage = [datos[d, :] for d in range(1, datos.shape[0])] #the rest are the voltages for each channel
    deltavector=np.zeros_like(voltage)# I create an array to store values of voltage differences
    interchannelvoltage=np.zeros(len(voltage))#i create array to store mean voltage difference
    for j in range(len(voltage)): #for each column, that is to say for each channel
        if j < len(voltage)-1: #if not the las channel
            deltavector[j,:]=voltage[j+1]-voltage[j]
        else: #if last channel
            deltavector[j,:]=voltage[j]-voltage[0]
        interchannelvoltage[j]=np.mean(deltavector[j,:])#mean voltage difference between channels
    interchanneltime[i]=interchannelvoltage/(2*10)#I store the values outside loop
    


#%% 
name = 'Settling_Time'
folder = os.path.join(os.getcwd(),
                      'Measurements',
                      name)
                      
settimefile = os.path.join(
        folder,'Settling_Time.txt')

time, voltage = np.loadtxt(settimefile, unpack=True)
#dt=time[5]-time[4]
#
#def Diffincent(u,dx):
#    w=len(u)
#    Diff=np.zeros(w)
#    for i in range(w):
#        if i == 0:
#            Diff[0]=(u[1]-u[w-1])/(2*dx)
#        elif i == w-1:
#            Diff[i]=(u[0]-u[i-1])/(2*dx)
#        else:
#            Diff[i]=(u[i+1]-u[i-1])/(2*dx)
#    return Diff
#
#slopederivative=Diffincent(voltage,dt)
#%% 
a=65350
b=85250
timezoom=time[a:b]
voltagezoom=voltage[a:b]
plt.plot(timezoom, voltagezoom,'g')
plt.xlabel('Time')
plt.ylabel('voltage')
plt.grid()
plt.show()

#%% 
def step_info(t,yout):
    print "Overshoot: %f%s"%((yout.max()/yout[-1]-1)*100,'%')
    print "Rise Time: %fs"%(t[next(i for i in range(0,len(yout)-1) if yout[i]>yout[-1]*.90)]-t[0])
    print "Settling Time: %fs"%(t[next(len(yout)-i for i in range(2,len(yout)-1) if abs(yout[-i]/yout[-1])>1.02)]-t[0])

step_info(timezoom,voltagezoom)    
    

    
    
    
    
    
    
    
    
    
    
    
    