"""Provides string representations of values using metric prefixes.

These functions are intended for reporting and summaries and not for precise calculations.  These functions
do mot make use of units.

Notes:
    1. Function round can have unexpected results as the underlying float binary representation is only an
    approximation of the represented float value.  Thus round(1.5) may yield value 1 or 2.
    https://docs.python.org/3/library/functions.html#round
    https://docs.python.org/3/tutorial/floatingpoint.html#tut-fp-issues
"""

_dec_prefix = ['k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
_dec_divider = [10**3, 10**6, 10**9, 10**12, 10**15, 10**18, 10**21, 10**24]
_dec_threshold = [10**7, 10**10, 10**13, 10**16, 10**19, 10**22, 10**25, 10**28]
_dec_max_idx = len(_dec_prefix) - 1

_bin_prefix = ['Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi']
_bin_divider = [2**10, 2**20, 2**30, 2**40, 2**50, 2**60, 2**70, 2**80]
_bin_threshold = [2**20*10, 2**30*10, 2**40*10, 2**50*10, 2**60*10, 2**70*10, 2**80*10, 2**90*10]
_bin_max_idx = len(_bin_prefix) - 1


# _____________________________________________________________________________
def to_binary_units(number) -> (str, str):
    if number < 10**3*10:
        return str(number), ''
    for i, n in enumerate(_bin_threshold):
        if number < n:
            break
    value = round(number / _bin_divider[i])
    return (str(value), _bin_prefix[i]) if value < 10**4 or i == _bin_max_idx else ('10', _bin_prefix[i + 1])


# _____________________________________________________________________________
def to_decimal_units(number) -> (str, str):
    if number < 10**4:
        return str(number), ''
    for i, n in enumerate(_dec_threshold):
        if number < n:
            break
    value = round(number / _dec_divider[i])
    return (str(value), _dec_prefix[i]) if value != 10**4 or i == _dec_max_idx else ('10', _dec_prefix[i + 1])



