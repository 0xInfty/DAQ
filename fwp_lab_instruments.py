# -*- coding: utf-8 -*-
"""
This module defines classes to manipulate lab instruments via PyVisa.

Some of the most useful tools are:

resources : function
    Returns a list of tuples of connected 'INSTR' resources.
Osci : class
    Allows communication with a Tektronix Digital Oscilloscope.
Osci.measure : method
    Takes a measure of a certain type on a certain channel.
Gen : class
    Allows communication with Tektronix Function Generators.
Gen.output : method
    Turns on/off an output channel. Also configures it if needed.

@author: Vall
"""

from fwp_string import find_1st_number, string_recognizer
import numpy as np
import pyvisa as visa

#%%

def resources():
    
    """Returns a list of tuples of connected resources.
    
    Parameters
    ----------
    nothing
    
    Returns
    -------
    resources : list
        List of connected resources.
    
    """
    
    rm = visa.ResourceManager()
    resources = rm.list_resources()
    print(resources)
    
    return resources

#%%

class Osci:
    
    """Allows communication with a Tektronix Digital Oscilloscope.
    
    It allows communication with multiple models, based on the official 
    Programmer Guide (https://www.tek.com/oscilloscope/tds1000-manual).
    
        TBS1102/TBS1102B/TBS1102B-EDU,
        TBS1152/TBS1152B/TBS1152B-EDU,
        TBS1202B/TBS1202B-EDU,
        TDS210,
        TDS220/TDS224, 
        TDS1001/TDS1002/TDS1001B/TDS1002B/TDS1001C-EDU/TDS1002C-EDU,
        TDS1012/TDS1012B/TDS1012C-EDU, 
        TDS2002/TDS2004/TDS2002B/TDS2004B/TDS2001C/TDS2002C/TDS2004C,
        TDS2012/TDS2014/TDS2012B/TDS2014B/TDS2012C/TDS2014C/TDS2022C, 
        TDS2022/TDS2024/TDS2022B/TDS2024B,
        TPS2012/TPS2014/TPS2012B/TPS2014B,
        TPS2024/TPS2024B,
    
    Parameters
    ----------
    port : str
        Computer's port where the oscilloscope is connected.
        i.e.: 'USB0::0x0699::0x0363::C108013::INSTR'
    termination='\n' : str, optional
        VISA's character of line termination.
        i.e.: '\n'
    
    Attributes
    ----------
    Osci.osci : pyvisa.ResourceManager.open_resource() object
        PyVISA object that allows communication.
    Osci.config_measure : dic
        Immediate measurement's current configuration.
    
    Other Attributes
    ----------------
    Osci.port : str
        Computer's port where the oscilloscope is connected.
        i.e.: 'USB0::0x0699::0x0363::C108013::INSTR'
    Osci.print : bool
        Whether to print messages or not.
    
    Methods
    -------
    Osci.measure(str, int)
        Makes a measurement of a type 'str' on channel 'int'.
    
    Examples
    --------
    >> osci = Osci(port='USB0::0x0699::0x0363::C108013::INSTR')
    >> result, units = osci.measure('Min', 1, print_result=True)
    1.3241 V
    >> result
    1.3241
    >> units
    'V'   
    
    """

    def __init__(self, port, nchannels=2,
                 termination="\n", print_messages=False):
        
        """Defines oscilloscope object and opens it as Visa resource.
        
        It also defines the following attributes:
                'Osci.osci' (PyVISA object)
                'Osci.config_measure' (Measurement's current 
                configuration)
                'Osci.print' (Boolen permission to print)
        
        Parameters
        ---------
        port : str
            Computer's port where the oscilloscope is connected.
            i.e.: 'USB0::0x0699::0x0363::C108013::INSTR'
        nchannels=2 : int
            Total number of the oscilloscope's channels.
        
        Returns
        -------
        nothing
        
        """
        
        # Main Attribute
        rm = visa.ResourceManager()
        self.osci = rm.open_resource(port, 
                                     read_termination=termination)
        del rm
                
        print(self.osci.query('*IDN?'))
        
        # General Configuration
        self.osci.write('DAT:ENC RPB')
        self.osci.write('DAT:WID 1') # Binary transmission mode
        
        # Measurement Configuration                       
        self.__config_measure__() # Save measurement configuration
                       
        # Attribute Definitions
        self.print = print_messages
        self.channels = [i+1 for i in range(nchannels)]
        
    def screen(self, channels=[1,2]):
        
        """Takes a full measure of a signal on one or more channels.
        
        Parameters
        ----------
        channels=[1, 2] : int {1, 2, 3, 4}, str {'M'}, list, optional
            Number of the measure's channel, where 3 or 'M' both 
            stand for MATH.
        
        Returns
        -------
        result : int, float, list
            Measured value.
        
        See Also
        --------
        Osci.get_config_screen()
        
        """        

        # First I transform channel names
        channels = self.__channels__(channels)
        
        # Now I raise some warnings if a numpy array can't be created
        npoints = []
        dtime = []
        for ch in channels:
            if not self.config_screen['Display'][ch]:
                self.osci.write('SELECT:{} 1'.format(ch))
                self._config_screen(ch)
            npoints.append(self.config_screen[ch]['NPoints'])
            dtime.append(self.config_screen[ch]['XInterval'])
        if npoints != [npoints[0] for ch in channels]:
            return IndexError(
                    "{} have different number of points".format(
                            channels))
        if dtime != [dtime[0] for ch in channels]:
            return ValueError(
                    "{} have different number of points".format(
                            channels))
        # Next I stop acquiring
        self.osci.write('ACQ:STATE 0')
        
        # I measure (np.array that has time, channels on its columns)
        results = []
        results.append(np.linspace(0, npoints*dtime, dtime)) # time
        for ch in channels:
            self.osci.write('DATA:SOUR {}'.format(ch))
            data = self.osci.query_binary_values('CURV?', 
                                                 datatype='B', 
                                                 container=np.array)
            data = self.config_screen[ch]['FData'](data)
            results.append(data) # voltage data
        results = np.array(results).T
        
        # I keep acquiring
        self.osci.write('ACQ:STATE 1')
        
        return results

    def measure(self, **kwargs):
        
        """Takes a single measure on one or more channels.
        
        Parameters
        ----------
        mode : str, optional
            Key that configures the measure type.
            i.e.: 'Min', 'min', 'minimum', etc.
        channels : int {1, 2, 3, 4}, str {'M'}, list, optional
            Measurement's channel or channels.
            i.e.: 1, 'CH1', [1, 'MATH'], etc.
        
        Returns
        -------
        result : int, float, list
            Measured value (int/float) or values (list).
        
        See Also
        --------
        Osci._config_measure()
        Osci._channels()
        
        """
        
        # First, I set default to current configuration if none
        for key, value in self.config_measure.items():
            try:
                kwargs[key]
            except KeyError:
                kwargs[key] = value
        
        # Now I aconditionate the channels variable, if needed
        kwargs['channels'] = self.__channels__(kwargs['channels'])
        
        # Now I take one measure at a time
        results = []
        for ch in kwargs['channels']:
            self._config_measure(**dict(mode = kwargs['mode'],
                                        source = ch))
        
            result = float(self.osci.query('MEASU:IMM:VAL?'))
            units = self.osci.query('MEASU:IMM:UNI?')
        
            self.__print__("{} {}".format(result, units))
            
            results.append(result)
        
        # Finally, I return all measurements at the same time
        try:
            results[1]
        except IndexError:
            results = results[0]
        return results

    def trigger(self):

#        osci.write('TRIG:MAI:MOD AUTO') # Option: NORM (waits for trig)
#        osci.write('TRIG:MAI:TYP EDGE')
#        osci.write('TRIG:MAI:LEV 5')
#        osci.write('TRIG:MAI:EDGE:SLO RIS')
#        osci.write('TRIG:MAI:EDGE:SOU CH1') # Option: EXT
#        osci.write('HOR:MAI:POS 0') # Makes the complete measure at once
        self.__print__("Hey! This is missing. What a shame the Complains Department is closed!")
    
    def close(self):
        
        """Closes VISA communication with oscilloscope.
        
        Parameters
        ----------
        nothing
        
        Returns
        -------
        nothing
        """
        
        self.osci.close()
        
    def __config_measure__(self, **kwargs):
        
        """Sets or reconfigures the current measurements' configuration.
        
        Parameters
        ----------
        mode : str, optional
            Measurement's type.
            i.e.: 'minimum', 'mean', 'max', etc.
        source : str, int, list, optional
            Measurement's source channel.
            i.e.: 'CH1', 'MATH'.
        
        Returns
        -------
        nothing
        
        Yields
        ------
        Osci.config_measure : attribute
        
        """
        
        # First of all, I define a dictionary of commands
        commands = dict(
                source = 'MEASU:IMM:SOU',
                mode = 'MEASU:IMM:TYPE',
                )
        
        # Now, if there aren't any kwargs...
        if not kwargs:
            try:
                # Try to set default kwargs as current configuration
                kwargs = self.config_measure
            except:
                # Get current configuration
                kwargs = {}
                for key, value in commands:
                    kwargs.update({key: self.osci.query(value+'?')})
                self.config_measure = kwargs
                
        # Otherwise, if there are kwargs...
        else:

            # I recognize measuring mode, if there's one
            if kwargs.get('mode') is not None:
                kwargs['mode'] = self.__measure_mode__(kwargs['mode'])
        
            # Now, reconfigure if needed
            for key, value in kwargs.items():
                if self.config_measure[key] != value:
                    self.osci.write(commands[key])
                    self.config_measure[key] = value

    def __get_config_screen__(self, channels=False):
        
        """Returns the current measurements' configuration.
        
        Parameters
        ----------
        nothing
        
        Returns
        -------
        configuration : dict as {'Source': int, 'Type': str}
            It states the source and type of configured measurement.
            
        """

        if not channels:
            channels = self.__channels__(self.channels)

        origin = self.osci.write('DATA:SOUR?')
        
        configuration = {}
        configuration.update({'Display' : {}})
        for ch in ['CH1', 'CH2', 'MATH']:
            configuration.update({ch : {}})
            
            # First I check whether this channel is being shown or not
            status = self.osci.query('SELECT:{} 1'.format(ch))
            configuration['Display'].update({ch : bool(int(status))})
            self.osci.write('SELECT:{} 1'.format(ch))
            self.osci.write('DATA:SOUR {}'.format(ch))
            
            # Now, I save some parameters
            xinterval = float(self.osci.query('WFMPRE:XIN?'))
            yzero, ymultiplier, yoffset = self.osci.query_ascii_values(
                    'WFMPRE:YZE?;YMU?;YOFF?',
                    separator=';')
            npoints = int(self.osci.query('WFMP:NR_Pt?'))
            configuration[ch].update({
                    'XIncrement' : xinterval,
                    'YZero' : yzero,
                    'YMultiplier' : ymultiplier,
                    'YOffset' : yoffset,
                    'NPoints' : npoints,
                    })
            
            # With that parameters, I define a calibration function
            def data_function(data):
                return yzero + ymultiplier * (data - yoffset)
            configuration[ch].update({'FData' : data_function})
            
            # Now I return to this channel's original status on screen
            self.osci.write('SELECT:{} {}'.format(ch, status))
        
        self.osci.write('DATA:SOUR {}'.format(origin))
    
        return configuration
            
    def __channels__(self, channels_user):
        
        """Aconditionates channel or channels' list.
        
        Parameters
        ----------
        chanels_user : int, list
            User's input channel/s.
        
        Returns
        -------
        channels_osc : str, list
            Oscilloscope's input channels.
        """
        
        try:
            channels_user[0]
        except:
            channels_user = [channels_user]
    
        key = {len(self.channels) + 1 : 'MATH'}
        key.update({ch : 'CH{}'.format(ch) for ch in self.channels})
        key.update({ch : 'ch{}'.format(ch) for ch in self.channels})
            
        channels_osc = []
        for ch in channels_user:
            try:
                if 'm' in ch.lower():
                    ch = 'MATH'
            except AttributeError:
                try:
                    ch = key[ch]
                except KeyError:
                    if ch not in key.values():
                        error = "Channel's element should either be on"
                        error = error + "{}".format(key)
                        error = error + "or should include 'm' or 'M'"
                        return ValueError(error)
            channels_osc.append(ch)
        
        return channels_osc


    def __measure_mode__(self, mode):
        
            # First I set a dictionary with regular expressions
            regular_expressions = {
                'me': 'MEAN',
                ('min', 'mn'): 'MINI',            
                ('max', 'mx'): 'MAXI',
                'fre': 'FREQ',
                'per': 'PER',
                'rms': 'RMS',
                ('pk2', 'amp', 'pea'): 'PK2',
                # absolute difference between max and min
                'ph': 'PHA',
                ('&', 'crms', 'cr'): 'CRM', 
                # RMS on the first complete period
                ('&', 'cmean', 'cm'): 'CMEAN',
                'ri': 'RIS', 
                # time betwee  10% and 90% on rising edge
                'fa': 'FALL',
                'l': 'LOW', # 0% reference
                'h': 'HIGH'} # 100% reference
            
            # Now I try to recognize the measuring mode
            mode = string_recognizer(mode, regular_expressions)
            # The key is used as a regular expression
            # The tuples include parallel regular expressions
            # Some lists of keys are searched first because of '&'
            
            return mode

    def __print__(self, message):
        
        """Doesn't print if Osci.print is False.
        
        Parameters
        ----------
        message : str
            Message to print.
        print_all=False : bool
            Indicates whether to print or not
        
        Returns
        -------
        nothing
        """
        
        if self.print:
            print(message)

#%%

class Gen:
    
    """Allows communication with Tektronix Function Generators.
    
    It allows communication with multiple models, based on the official 
    programming manual (https://www.tek.com/signal-generator/afg3000-
    manual/afg3000-series-2)
    
        AFG3011;
        AFG3021B;
        AFG3022B;
        AFG3101;
        AFG3102;
        AFG3251;
        AFG3252.

    Parameters
    ----------
    port : str
        Computer's port where the oscilloscope is connected.
        i.e.: 'USB0::0x0699::0x0363::C108013::INSTR'
    
    Attributes
    ----------
    Gen.port : str
        Computer's port where the oscilloscope is connected.
        i.e.: 'USB0::0x0699::0x0363::C108013::INSTR'
    Gen.gen : pyvisa.ResourceManager.open_resource() object
        PyVISA object that allows communication.
    Gen.config_output : dic
        Outputs' current configuration.
    
    Methods
    -------
    Gen.output(1, int, waveform=str)
        Turns on channel 'int' with a signal descripted by 'str'.
    Gen.output(0, int)
        Turns off channel 'int'.
    Gen.config_output[int]['Status']
        Returns bool saying whether channel 'int' is on or off.
    
    Examples
    --------
    >> gen = Gen(port='USB0::0x0699::0x0363::C108013::INSTR')
    >> Gen.output(1, 1, waveform='sin', frequency=1e3)
    {turns on channel 1 with a 1kHz sinusoidal wave}
    >> Gen.output(1, 1, waveform='squ')
    {keeps channel 1 on but modifies waveform to a square wave}
    >> Gen.output(0)
    {turns off channel 1}
    
    Further Development
    -------------------
    1) Should add an order that sets the apparatus on remote mode, so 
    that you can't change the configuration manually.
    2) Could define an internal class for its channels so that you can 
    set 'gen.ch1.output' = True to turn it on or ask freq = 
    gen.ch1.frequency to get part of its configuration.
    3) Should add a 'gen.close()' instead of 'gen.gen.close'

    """
    
    def __init__(self, port, nchannels):

        """Defines oscilloscope object and opens it as Visa resource.
        
        It also defines the following attributes:
                'Gen.port' (PC's port where it is connected)
                'Gen.osci' (PyVISA object)
                'Gen.config_output' (Outputs' current 
                configuration)
        
        Parameters
        ----------
        port : str
            Computer's port where the oscilloscope is connected.
            i.e.: 'USB0::0x0699::0x0346::C036493::INSTR'
        
        Returns
        -------
        nothing
        
        See Also
        --------
        Gen.get_config_output()
        
        """
        
        rm = visa.ResourceManager()
        gen = rm.open_resource(port, read_termination="\n")
        print(gen.query('*IDN?'))
        
        self.port = port
        self.nchannels = nchannels
        self.gen = gen
        self.config_output = self.get_config_output()
    
    def output(self, status, channel=1, 
               print_changes=False, **output_config):
        
        """Turns on/off an output channel. Also configures it if needed.
                
        Parameters
        ----------
        status : bool
            Says whether to turn on (True) or off (False).
        channel : int {1, 2}, optional
            Number of output channel to be turn on or off.
        print_changes=True : bool, optional
            Says whether to print changes when output is reconfigured.
        waveform : str, optional
            Output's waveform (if none, applies current configuration).
        frequency : int, float, optional
            Output's frequency in Hz (if none, current configuration).
        amplitude : int, float, optional
            Output's amplitude in Vpp (if none, current configuration).
        offset : int, float, optional
            Output's offset in V (if none, current configuration).
        phase : int, flot, optional
            Output's phase expressed in radians and multiples of pi 
            (if none, applies current configuration).
        
        Returns
        -------
        nothing
        
        Examples
        --------
        >> gen = Gen()
        >> gen.output(True, amplitude=2)
        {turns on channel 1 and plays a sinusoidal 1kHz and 2Vpp wave}
        >> gen.output(0)
        {turns off channel 1}
        >> gen.output(1)
        {turns on channel 1 with the same wave as before}
        >> gen.output(True, waveform='squ75')
        {turns on channel 1 with asymmetric square 1kHz and 1Vpp wave}
        >> gen.output(True, waveform='ram50')
        {turns on channel 1 with triangular 1kHz and 1Vpp wave}
        >> gen.output(True, waveform='ram0')
        {turns on channel 1 with positive ramp}
        
        See Also
        --------
        Gen.get_config_output()
        Gen.re_config_output()
        
        """
        
        if channel not in [1, 2]:
            print("Unrecognized output channel (default 'CH1')")
            channel = 1
        
        # This is a list of possibles kwargs
        keys = ['waveform', 'frequency', 'amplitude', 'offset', 'phase']
        
        # I assign 'None' to empty kwargs
        for key in keys:
            try:
                output_config[key]
                print("Changing {} on CH{}".format(key, channel))
            except KeyError:
                output_config[key] = None

        
        self.re_config_output(channel=channel,
                              waveform=output_config['waveform'],
                              frequency=output_config['frequency'],
                              amplitude=output_config['amplitude'],
                              offset=output_config['offset'],
                              phase=output_config['phase'],
                              print_changes=print_changes)
        
        self.gen.write('OUTP{}:STAT {}'.format(channel, int(status)))
        # If output=True, turns on. Otherwise, turns off.
        
        if status:
            print('Output CH{} ON'.format(channel))
            self.config_output[channel]['Status'] = True
        else:
            print('Output CH{} OFF'.format(channel))
            self.config_output[channel]['Status'] = False
            
    def get_config_output(self):
        
        """Returns current outputs' configuration on a dictionary.
        
        Parameters
        ----------
        nothing
        
        Returns
        -------
        configuration : dic
            Current outputs' configuration.
            i.e.: {1:{
                      'Status': True,
                      'Waveform': 'SIN',
                      'RAMP Symmetry': 50.0,
                      'PULS Duty Cycle': 50.0,
                      'Frequency': 1000.0,
                      'Amplitude': 1.0,
                      'Offset': 0.0,
                      'Phase': 0.0}}

        """
        
        configuration = {i: dict() for i in range(1, self.nchannels+1)}
        
        for channel in range(1, self.nchannels+1):
            
            # On or off?
            configuration[channel].update({'Status': bool(int(
                self.gen.query('OUTP{}:STAT?'.format(channel))))})
            
            # Waveform configuration
            configuration[channel].update({'Waveform': 
                self.gen.query('SOUR{}:FUNC:SHAP?'.format(channel))})
            
            # Special configuration for RAMP
            if configuration[channel]['Waveform'] == 'RAMP':
                aux = self.gen.query('SOUR{}:FUNC:RAMP:SYMM?'.format(
                        channel)) # NOT SURE I SHOULD USE IF
                configuration[channel]['RAMP Symmetry'] = find_1st_number(aux)
            else:
                configuration[channel]['RAMP Symmetry'] =  50.0
            
            # Special configuration for SQU
            if configuration[channel]['Waveform'] == 'PULS':
                aux = self.gen.query('SOUR{}:PULS:DCYC?'.format(
                        channel))
                configuration.update({'PULS Duty Cycle':
                             find_1st_number(aux)})
            else:
                configuration[channel]['PULS Duty Cycle'] = 50.0
            
            # Frequency configuration
            aux = self.gen.query('SOUR{}:FREQ?'.format(channel))
            configuration[channel]['Frequency'] = find_1st_number(
                    aux)
            
            # Amplitude configuration
            aux = self.gen.query('SOUR{}:VOLT:LEV:IMM:AMPL?'.format(
                    channel))
            configuration[channel]['Amplitude'] = find_1st_number(
                    aux)
            
            # Offset configuration
            aux = self.gen.query('SOUR{}:VOLT:LEV:IMM:OFFS?'.format(
                    channel))
            configuration[channel]['Offset'] = find_1st_number(aux)
            
            # Phase configuration
            aux = self.gen.query('SOUR{}:PHAS?'.format(channel))
            configuration[channel]['Phase'] = find_1st_number(aux)
        
        return configuration
    
    def re_config_output(self, channel=1, waveform='sin', frequency=1e3, 
                         amplitude=1, offset=0, phase=0, 
                         print_changes=False):

        """Reconfigures an output channel, if needed.
                
        Variables
        ---------
        channel : int {1, 2}, optional
            Number of output channel to be turn on or off.
        waveform='sin' : str, optional
            Output's waveform.
        frequency=1e3 : int, float, optional
            Output's frequency in Hz.
        amplitude=1 : int, float, optional
            Output's amplitude in Vpp.
        offset=0 : int, float, optional
            Output's offset in V.
        phase=0 : int, flot, optional
            Output's phase in multiples of pi.
        print_changes=False: bool, optional.
            Says whether to print changes or not if output reconfigured.
        
        Returns
        -------
        nothing
        
        See Also
        --------
        Gen.output()
        Gen.re_config_output()
        
        """

        # These are some keys that help recognize the waveform
        dic = {'sin': 'SIN',
               'sq': 'PULS',
               'pul': 'PULS',
               'tr' : 'RAMP', # ramp and triangle
               'ram': 'RAMP', 
               'lo': 'LOR', # lorentzian
               'sinc': 'SINC', # sinx/x
               'g': 'GAUS'} # gaussian
        
        if channel not in range(1, self.nchannels+1):
            print("Unrecognized output channel ('CH1' as default).")
            channel = 1

        # This is the algorithm to recognize the waveform
        if waveform is not None:
            aux = 0
            waveform = waveform.lower()
            if 'sq' in waveform:
                try:
                    aux = find_1st_number(waveform)
                    if aux != 50:
                        aux = 'PULS'
                    else:
                        aux = 'SQU'
                except TypeError:
                    aux = 'SQU'
            elif 'c' in waveform:
                aux = 'SINC'
            else:
                for key, value in dic.items():
                    if key in waveform:
                        aux = value
                if aux not in dic.values():
                    aux = 'SIN'
                    print("Unrecognized Waveform ('SIN' as default).")    
        else:
            waveform = self.config_output[channel]['Waveform']
            aux = waveform
        
        if self.config_output[channel]['Waveform'] != aux:
            self.gen.write('SOUR{}:FUNC:SHAP {}'.format(channel, aux))
            if print_changes:
                print("CH{}'s Waveform changed to '{}'".format(
                        channel, 
                        aux))

        if 'sq' in waveform or 'pul' in waveform:
            try:
                aux = find_1st_number(waveform)
            except TypeError:
                aux = 50.0
                print("Unasigned PULS Duty Cycle (default '50.0')")
            if self.config_output[channel]['PULS Duty Cycle'] != aux:
                self.gen.write('SOUR{}:PULS:DCYC {:.1f}'.format(
                        channel,
                        aux))
                if print_changes:
                    print("CH{}'s PULS Duty Cycle changed to \
                          {}%".format(channel, aux))

        elif 'ram' in waveform:
            try:
                aux = find_1st_number(waveform)
            except TypeError:
                aux = 50.0
                print("Unasigned RAMP Symmetry (default '50.0')")
            if self.config_output[channel]['RAMP Symmetry'] != aux:
                self.gen.write('SOUR{}:FUNC:RAMP:SYMM {:.1f}'.format(
                        channel,
                        aux))
                if print_changes:
                    print("CH{}'s RAMP Symmetry changed to \
                          {}%".format(channel, aux))
        
        if frequency is not None:
            if self.config_output[channel]['Frequency'] != frequency:
                self.gen.write('SOUR{}:FREQ {}'.format(channel, frequency))
                if print_changes:
                    print("CH{}'s Frequency changed to {} Hz".format(
                            channel,
                            frequency))
        
        if amplitude is not None:
            if self.config_output[channel]['Amplitude'] != amplitude:
                self.gen.write('SOUR{}:VOLT:LEV:IMM:AMPL {}'.format(
                    channel,
                    amplitude))
                if print_changes:
                    print("CH{}'s Amplitude changed to {} V".format(
                            channel,
                            amplitude))
        
        if offset is not None:
            if self.config_output[channel]['Offset'] != offset:
                self.gen.write('SOUR{}:VOLT:LEV:IMM:OFFS {}'.format(
                    channel,
                    offset))
                if print_changes:
                    print("CH{}'s Offset changed to {} V".format(
                            channel,
                            offset))
                    
        if phase is not None:
            if self.config_output[channel]['Phase'] != phase:
                self.gen.write('SOUR{}:PHAS {}'.format(
                    channel,
                    phase))
                if print_changes:
                    print("CH{}'s Phase changed to {} PI".format(
                            channel,
                            phase))
    
        self.config_output = self.get_config_output()
        
        return
    