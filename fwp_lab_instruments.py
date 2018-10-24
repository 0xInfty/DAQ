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

from fwp_string import find_1st_number
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
        
        # Attribute Definitions
        self.print = print_messages
        self.channels = [i+1 for i in range(nchannels)]
        self.config_measure = self.get_config_measure()
        self.config_screen = self.get_config_screen()
        # This last lines save the current measurement configuration
        
        # Inner Attribute Definitions

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

        channels = self._channels_names(channels)         
        
        data = self.osci.query_binary_values('CURV?', datatype='B', container=np.array)
        data = yze + ymu * (data - yoff)
        
        tiempo = xze + np.arange(len(data)) * xin

    def measure(self, mtype, channels=1):
        
        """Takes a measure of a certain type on one or more channels.
        
        Parameters
        ----------
        mtype : str
            Key that configures the measure type.
            i.e.: 'Min', 'min', 'minimum', etc.
        channels=1 : int {1, 2, 3, 4}, str {'M'}, list, optional
            Number of the measure's channel, where 3 or 'M' both 
            stand for MATH.
        
        Returns
        -------
        result : int, float, list
            Measured value (int/float) or values (list).
        
        See Also
        --------
        Osci.re_config_measure()
        Osci.get_config_measure()
        
        """
        
        channels = self._channels_names(channels)
        
        results = []
        for ch in channels:
            self.re_config_measure(mtype, ch)
        
            result = float(self.osci.query('MEASU:IMM:VAL?'))
            units = self.osci.query('MEASU:IMM:UNI?')
        
            self._print("{} {}".format(result, units))
            
            results.append(result)
        
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
        self._print("Hey! This is missing. What a shame the Complains Department is closed!")
    
    def close(self):
        
        self.osci.close()
        
    def get_config_measure(self):
        
        """Returns the current measurements' configuration.
        
        Parameters
        ----------
        nothing
        
        Returns
        -------
        configuration : dict as {'Source': int, 'Type': str}
            It states the source and type of configured measurement.
            
        """
        
        configuration = {}
        
        aux = self.osci.query('MEASU:IMM:SOU?')
        if 'm' in aux:
            aux = 'M'
        else:
            aux = find_1st_number(aux)
        configuration.update({'Source': # channel
            self._channels_names(aux)}) 
        configuration.update({'Type': # type of measurement
            self.osci.query('MEASU:IMM:TYP?')})
    
        return configuration

    def re_config_measure(self, mtype, channel):
        """Reconfigures the measurement, if needed.
        
        Parameters
        ---------
        mtype : str
            Key that configures the measure type.
            i.e.: 'Min', 'min', 'minimum', etc.
        channel : str {'CH1', 'CH2', 'CH3', 'CH4', 'MATH'}
            Measure's channel.
        
        Returns
        -------
        nothing
        
        See Also
        --------
        Osci.get_config_measure()
        
        """
        
        # This has some keys to recognize measurement's type
        dic = {'mean': 'MEAN',
               'min': 'MINI',
               'max': 'MAXI',
               'freq': 'FREQ',
               'per': 'PER',
               'rms': 'RMS',
               'pk2': 'PK2',
               'amp': 'PK2', # absolute difference between max and min
               'ph': 'PHA',
               'crms': 'CRM', # RMS on the first complete period
               'cmean': 'CMEAN',
               'rise': 'RIS', # time betwee  10% and 90% on rising edge
               'fall': 'FALL',
               'low': 'LOW', # 0% reference
               'high': 'HIGH'} # 100% reference

        # Here is the algorithm to recognize measurement's type
        if 'c' in mtype.lower():
            if 'rms' in mtype.lower():
                aux = dic['crms']
            else:
                aux = dic['cmean']
        else:
            for key, value in dic.items():
                if key in mtype.lower():
                    aux = value
            if aux not in dic.values():
                aux = 'FREQ'
                print("Unrecognized measure type ('FREQ' as default).")
        
        # Now, reconfigure if needed
        if self.config_measure['Source'] != channel:
            self.osci.write('MEASU:IMM:SOU {}'.format(channel))
            self._print("Measure source changed to '{}'".format(channel))
        if self.config_measure['Type'] != aux:
            self.osci.write('MEASU:IMM:TYP {}'.format(aux))
            self._print("Measure type changed to '{}'".format(aux))
        
        self.config_measure = self.get_config_measure()
        
        return

    def get_config_screen(self):
        
        """Returns the current measurements' configuration.
        
        Parameters
        ----------
        nothing
        
        Returns
        -------
        configuration : dict as {'Source': int, 'Type': str}
            It states the source and type of configured measurement.
            
        """
        
        configuration = {}
        
        xze, xin, yze, ymu, yoff = self.osci.query_ascii_values(
                'WFMPRE:XZE?;XIN?;YZE?;YMU?;YOFF?;',
                separator=';')
    
        return configuration

    def _channels_names(self, channels_user):
        
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
    
        channels_osc = []
        for i, ch in enumerate(channels_user):
            try:
                ch = ch.lower()
                if 'm' in ch.lower():
                    channels_osc.append('MATH')
                else:
                    message = "Channel's elements should either"
                    message = message + "be int {1, 2}" 
                    message = message + "or include 'm'"
                    return ValueError(message)
            except SyntaxError:
                if ch not in self.channels:
                    message = "If channel's element is int,"
                    message = message + "should be on {}".format(
                            [i+1 for i in range(self._nchannels)])
                    return ValueError(message)
                channels_osc.append("CH{:.0f}".format(ch))
        
        return channels_osc
    
    def _print(self, message):
        
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