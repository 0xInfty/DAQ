# -*- coding: utf-8 -*-
"""
This module contains tools for dealing with strings.

Some of its most useful tools are:

value_error : function
    Rounds up value and error of a measure. Also makes a latex string.
find_numbers : function
    Returns a list of numbers found on a given string.

@author: Vall
"""

import re
from tkinter import Tk

#%%

def copy(string):
    """Copies a string to the clipboard.
    
    Parameters
    ----------
    string : str
        The string to be copied.
    
    Returns
    -------
    nothing
    
    """
    
    r = Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(string)
    r.update() # now it stays on the clipboard
    r.destroy()
    
    print("Copied")

#%%

def error_value(X, dX, error_digits=1, units='',
                string_scale=True, one_point_scale=False, legend=False):
    """Rounds up value and error of a measure. Also makes a latex string.
    
    This function takes a measure and its error as input. Then, it 
    rounds up both of them in order to share the same amount of decimal 
    places.
    
    After that, it generates a latex string containing the rounded up 
    measure. For that, it can rewrite both value and error so that the 
    classical prefix scale of units can be applied.
    
    Parameters
    ----------
    X : float
        Measurement's value.
    dX : float
        Measurement's associated error.
    error_digits=2 : int, optional.
        Desired number of error digits.
    units='' : str, optional.
        Measurement's units.
    string_scale=True : bool, optional.
        Whether to apply the classical prefix scale or not.        
    one_point_scale=False : bool, optional.
        Applies prefix with one order less.
    legend=False : bool, optional.
        Says whether it is for the legend of a plot or not.
    
    Returns
    -------
    latex_str : str
        Latex string containing value and error.
    
    Examples
    --------
    >> error_value(1.325412, 0.2343413)
    '(1.33$\\pm$0.23)'
    >> error_value(1.325412, 0.2343413, error_digits=3)
    '(1.325$\\pm$0.234)'
    >> error_value(.133432, .00332, units='V')
    '\\mbox{(133.4$\\pm$3.3) mV}'
    >> error_value(.133432, .00332, one_point_scale=True, units='V')
    '\\mbox{(0.1334$\\pm$0.0033) V}'
    >> error_value(.133432, .00332, string_scale=False, units='V')
    '\\mbox{(1.334$\\pm$0.033)$10^-1$ V}'
    
    See Also
    --------
    copy
    
    """
    
    # First, I string-format the error to scientific notation with a 
    # certain number of digits
    if error_digits >= 1:
        aux = '{:.' + str(error_digits) + 'E}'
    else:
        print("Unvalid 'number_of_digits'! Changed to 1 digit")
        aux = '{:.0E}'
    error = aux.format(dX)
    error = error.split("E") # full error (string)
    
    error_order = int(error[1]) # error's order (int)
    error_value = error[0] # error's value (string)

    # Now I string-format the measure to scientific notation
    measure = '{:E}'.format(X)
    measure = measure.split("E") # full measure (string)
    measure_order = int(measure[1]) # measure's order (int)
    measure_value = float(measure[0]) # measure's value (string)
    
    # Second, I choose the scale I will put both measure and error on
    # If I want to use the string scale...
    if -12 <= measure_order < 12 and string_scale:
        prefix = ['p', 'n', r'$\mu$', 'm', '', 'k', 'M', 'G']
        scale = [-12, -9, -6, -3, 0, 3, 6, 9, 12]
        for i in range(8):
            if not one_point_scale:
                if scale[i] <= measure_order < scale[i+1]:
                    prefix = prefix[i] # prefix to the unit
                    scale = scale[i] # order of both measure and error
                    break
            else:
                if scale[i]-1 <= measure_order < scale[i+1]-1:
                    prefix = prefix [i]
                    scale = scale[i]
                    break
        used_string_scale = True
    # ...else, if I don't or can't...
    else:
        scale = measure_order
        prefix = ''
        used_string_scale = False
    
    # Third, I actually scale measure and error according to 'scale'
    # If error_order is smaller than scale...
    if error_order < scale:
        if error_digits - error_order + scale - 1 >= 0:
            aux = '{:.' + str(error_digits - error_order + scale - 1)
            aux = aux + 'f}'
            error_value = aux.format(
                    float(error_value) * 10**(error_order - scale))
            measure_value = aux.format(
                    measure_value * 10**(measure_order - scale))
        else:
            error_value = float(error_value) * 10**(error_order - scale)
            measure_value = float(measure_value)
            measure_value = measure_value * 10**(measure_order - scale)
    # Else, if error_order is equal or bigger than scale...
    else:
        aux = '{:.' + str(error_digits - 1) + 'f}'
        error_value = aux.format(
                float(error_value) * 10**(error_order - scale))
        measure_value = aux.format(
                float(measure_value) * 10**(measure_order - scale))
    
    # Forth, I generate a latex string. Ex.: '(1.34$pm$0.32) kV'
    latex_str = r'({}$\pm${})'.format(measure_value, error_value)
    if not used_string_scale and measure_order != 0:
        latex_str = latex_str + r'$10^{:.0f}$'.format(scale)      
    elif used_string_scale:
        latex_str = latex_str + ' ' + prefix
    if units != '':
        if latex_str[-1] == ' ':
            latex_str = latex_str + units
        else:
            latex_str = latex_str + ' ' + units
    if units != '' or prefix:
        if not legend:
            latex_str = r'\mbox{' + latex_str + '}'
                       
    return latex_str

#%%

def resistance(value, porcentual_error, extra_digits, min_division, 
               error_digits=2, units=r'$\Omega$', number_return=False):
        
    error = porcentual_error * value / 100
    error = error + extra_digits * min_division
    
    latex = error_value(value, error,
                        error_digits=error_digits,
                        units=units, string_scale=True)
    
    if number_return:
        return value, error
    else:
        return latex

#%%

def find_numbers(string):
    """Returns a list of numbers found on a given string
    
    Parameters
    ----------
    string: str
        The string where you search.
    
    Returns
    -------
    list
        A list of numbers (each an int or float).
    
    Raises
    ------
    "There's no number in this string" : TypeError
        If no number is found.

    """
    
    numbers = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", string)
    
    if not numbers:
        raise TypeError("There's no number in this string")
    
    for i, n in enumerate(numbers):
        if '.' in n:
            numbers[i] = float(n)
        else:
            numbers[i] = int(n) 
    
    return numbers

def find_1st_number(string):
    """Returns the first float or int number of a string
    
    Parameters
    ----------
    string: str
        The string where you search.
    
    Returns
    -------
    number: int, float
        The number you found.
    
    Raises
    ------
    "There's no number in this string" : TypeError
        If no number is found.

    """
    
    number = find_numbers(string)[0]
    
    return number

#%%

def counting_sufix(number):
    """Returns a number's suffix string to use for counting.
    
    Parameters
    ----------
    number: int, float
        Any number, though it is designed to work with integers.
    
    Returns
    -------
    ans: str
        A string representing the integer number plus a suffix.
    
    Examples
    --------
    >> counting_sufix(1)
    '1st'
    >> counting_sufix(22)
    '22nd'
    >> counting_sufix(1.56)
    '2nd'
    
    """
    
    number = round(number)
    unit = int(str(number)[-1])
    
    if unit == 1:
        ans = 'st'
    if unit == 2:
        ans = 'nd'
    if unit == 3:
        ans = 'rd'
    else:
        ans = 'th'
    
    return ans

#%%

def string_recognizer(string, partial_keys,
                      priorized_marker="&"):
    """This is a function that recognizes a string from partial keys.
    
    Parameters
    ----------
    string : str
        Word to be recognized.
    partial_keys : dic
        Dictionary used for recognizing. Its keys should be str or tuple.
    
    Returns
    -------
    dynamic
    
    Examples
    --------
    >> partial_keys = {'a' : 1,
                       ('b','c') : 2,
                       ('&', 'r') : 3,
                       ('&', 'li', 'le') : 4}
    >> string_recognizer('a', partial_keys)
    1
    >> string_recognizer('add', partial_keys)
    1
    >> string_reconizer('b', partial_keys)
    2
    >> string_reconizer('c', partial_keys)
    2
    >> string_recognizer('rat', partial_keys)
    3
    >> string_recognizer('lion', partial_keys)
    4
    >> string_reconizer('let', partial_keys)
    4
    >> string_recognizer('ale', partial_keys)
    4
    """
    
    # Obviously, if 'string' is already on the values of partial_keys...    
    if string in partial_keys.values():
        return string
    string = string.lower()
    
    # OK then! First of all, I force all keys to be tuple
    non_priorized_keys = {}
    for key, value in partial_keys.items():
        if not isinstance(key, tuple):
            print(key)
            non_priorized_keys.update({tuple([key]) : value})
        else:
            non_priorized_keys.update({key : value})
    
    # Next I priorize some keys
    priorized_keys = {}
    for key in non_priorized_keys.keys():
        for element in list(key):
            if priorized_marker in element:
                priorized_keys.update({key : non_priorized_keys[key]})
                break
    
    # Then I define only the others as non-priorized
    for key in priorized_keys.keys():
        non_priorized_keys.pop(key)
    
    # Now I check the priorized keys are exclusive
    for examined_key in priorized_keys.keys():
        for other_key in priorized_keys.keys():
            
            if other_key is not examined_key:
            
                for element in examined_key:
                    if element is priorized_marker:
                        continue                    
                    if element in list(other_key):
                        return KeyError(
                                "Priorized keys are not exclusive",
                                "because {} and {}".format(
                                        element,
                                        other_key))
    
    # Next I check non-priorized keys are exclusive
    for examined_key in non_priorized_keys.keys():
        for other_key in non_priorized_keys.keys():
            
            if other_key is not examined_key:
            
                for element in examined_key:
                    if element in list(other_key):
                        return KeyError("Non-Priorized keys are ",
                                        "not exclusive because ",
                                        "{} and {}".format(
                                                element,
                                                other_key))

    for key, value in priorized_keys.items():
        for a_key in list(key):
            if a_key in string:
                return value

    for key, value in non_priorized_keys.items():
        for a_key in list(key):
            if a_key in string:
                return value