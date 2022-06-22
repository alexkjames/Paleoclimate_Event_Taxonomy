import os
import lipd as lpd
import numpy as np
import pyleoclim as pyleo
import plotly.express as px

from IPython.display import clear_output

def _get_tso_indices(tso,val_num = None, time_num = None):

    for idx, ts in enumerate(tso):
        var = ts['paleoData_variableName']
        print(f'{idx} : {var}')

    if val_num is None:
        val_num = input('Select the index of the value axis: ')

        try:
            val_num = int(val_num)
        except ValueError:
            clear_output()
            print('Value index passed could not be coaxed into integer, please pass an integer \n')
            val_num,time_num = _get_tso_indices(tso)

    if time_num is None:
        time_num = input('Select the index of the time axis: ')

        try:
            time_num = int(time_num)
        except ValueError:
            clear_output()
            print('Time index passed could not be coaxed into integer, please pass an integer \n')
            val_num,time_num = _get_tso_indices(tso)
    
    if time_num == val_num:
        clear_output()
        print('Value and time indices are identical, please re-enter selections \n')
        val_num,time_num = _get_tso_indices(tso)

    return val_num, time_num

def _get_event_time(series,event_start=None,event_end=None):

    if event_start is None:

        event_start = input('When does the event begin in units of the time axis: ')

        try:
            event_start = float(event_start)
        except ValueError:
            clear_output()
            print('Event start time passed could not be coaxed into float, please pass a float or integer \n')
            event_start,event_end = _get_event_time(series)

    if event_end is None:

        event_end = input('When does the event end in units of the time axis: ')

        try:
            event_end = float(event_end)
        except ValueError:
            clear_output()
            print('Event end time passed could not be coaxed into float, please pass a float or integer \n')
            event_start,event_end = _get_event_time(series,event_start)
    
    series_slice = series.slice((event_start,event_end))

    if series_slice.time.size == 0:
        clear_output()
        print('Series sliced with these times returned an empty array, please double check entries \n')
        event_start,event_end = _get_event_time(series)

    return event_start, event_end

def _get_amp_time(series,timing=None,amp=None,id=None):

    if timing is None:

        timing = input(f'Enter {id} event timing: ')

        try:
            timing = float(timing)
        except ValueError:
            if id == 'Middle' and not timing:
                timing = None
            else:
                clear_output()
                print(f'{id} event timing passed could not be coaxed into float, please pass a float or integer \n')
                timing,amp = _get_amp_time(series,id=id)
    
    if amp is None:

        amp = input(f'Enter {id} event amplitude: ')

        try:
            amp = float(amp)
        except ValueError:
            if id == 'Middle' and not amp:
                amp = None
            else:
                clear_output()
                print(f'{id} event amplitude passed could not be coaxed into float, please pass a float or integer \n')
                timing, amp = _get_amp_time(series,timing,id=id)

    return timing, amp

def _get_event_stats(series):

    beg_timing, beg_amp = _get_amp_time(series,id='Beginning')
    mid_timing, mid_amp = _get_amp_time(series,id='Middle')
    end_timing, end_amp = _get_amp_time(series,id='End')

    if type(mid_timing) != type(mid_amp):
        clear_output()
        print('Type of mid timing and mid amp do not match, please re-enter types.')
        mid_timing, mid_amp = _get_amp_time(series,id='Middle')

    return beg_timing, beg_amp, mid_timing, mid_amp, end_timing, end_amp

def load_data(load_pathname):
    '''Function to load  data

    Parameters
    ----------

    load_pathname : str
        Full path to lipd file to be loaded

    Returns
    -------

    series : pyleoclim.Series
        Series object to be used for labeling and check data functions
    '''

    #Change directory shenanigans necessary due to lipd switching directories after loading
    working_dir = os.getcwd()

    file = lpd.readLipd(load_pathname)

    tso = lpd.extractTs(file)

    os.chdir(working_dir)

    val_num,time_num = _get_tso_indices(tso)

    series = pyleo.Series(time=tso[time_num]['paleoData_values'],value=tso[val_num]['paleoData_values'],
                     time_name = tso[time_num]['paleoData_variableName'],value_name=tso[val_num]['paleoData_variableName'],
                     time_unit = tso[time_num]['paleoData_units'], value_unit=tso[val_num]['paleoData_units']).standardize().convert_time_unit('yr BP')

    return series

def visualize(series):
    '''Function to visualize data

    Parameters
    ----------

    series : pyleoclim.series
        Series object from data loading step

    '''
    series = series.interp(step=1)
    fig = px.line(x=series.time, y=series.value, 
                    labels = {'x':f'{series.time_name} [{series.time_unit}]','y':f'{series.value_name} [{series.value_unit}]'}, 
                    title='Plot for labeling')

    fig.show()

def label_data(series):
    '''Function to label events in timeseries data using lipd files

    Parameters
    ----------

    series : pyleo.Series
        Series object from data loading step

    Returns
    -------

    res : dict
        Dictionary of all labels created
    
    '''

    event_start, event_end = _get_event_time(series)

    beg_timing, beg_amp, mid_timing, mid_amp, end_timing, end_amp = _get_event_stats(series)

    res = {
        'event_start' : event_start,
        'event_end' : event_end,
        'beg_timing' : beg_timing,
        'beg_amp' : beg_amp,
        'mid_timing' : mid_timing,
        'mid_amp' : mid_amp,
        'end_timing' : end_timing,
        'end_amp' : end_amp
    }

    return res


def gen_fit(series,res,v_shift = None):
    '''Function to generate and check the fit of idealized shape as its been defined

    Parameters
    ----------

    series : pyleo.Series
        Series object from data loading step

    res : dict
        Res object from data labeling step, or dict containing:
            event_start, event_end, beg_timing, beg_amp, mid_timing, mid_amp, end_timing, end_amp as keys

    v_shift : float
        Amount to shift event up or down to assist with fitting. Optional

    Returns
    -------

    idealized_series : pyleo.Series
        Idealized series generated using event stats. If v_shift is passed it is not included in this series

    stats : dict
        Dictionary of idealized event statistics
    
    '''

    series = series.interp(step=1)
    
    event_start_index = np.where(series.time==res['event_start'])[0][0]

    synth_time = series.time
    synth_val = np.zeros(synth_time.size) + series.value[event_start_index]

    beg_i = event_start_index
    beg_f = np.where(synth_time==res['beg_timing'])[0][0]
    beg_dur = beg_f-beg_i
    beg_delta = res['beg_amp'] - synth_val[beg_i]

    synth_val[int(beg_i):int(beg_f)] = np.arange(beg_dur)*(beg_delta/beg_dur) + synth_val[beg_i]

    mid_i = beg_f
    mid_f = np.where(synth_time==res['mid_timing'])[0][0]
    mid_dur = mid_f - mid_i
    mid_delta = res['mid_amp'] - res['beg_amp']

    synth_val[int(mid_i):int(mid_f)] = np.arange(mid_dur)*(mid_delta/mid_dur) + res['beg_amp']

    end_i = mid_f
    end_f = np.where(synth_time==res['end_timing'])[0][0]
    end_dur = end_f-end_i
    end_delta = res['end_amp'] - res['mid_amp']

    synth_val[int(end_i):int(end_f)] = np.arange(end_dur)*(end_delta/end_dur) + res['mid_amp']

    synth_val[int(end_f):] = synth_val[int(end_f)-1]

    idealized_series = pyleo.Series(synth_time,synth_val,label='Idealized event')

    if v_shift:
        synth_val += v_shift

    synth_series = pyleo.Series(synth_time,synth_val,label='Idealized event')
    interp_series = series.interp(step=1)

    fig = px.line(labels = ('{series.time_name} {series.time_units}','{series.value_name} {series.value_units}'),
                  title="Idealized vs. Real Event")

    fig.add_scatter(x=interp_series.time, y=interp_series.value, name='Original Series')
    fig.add_scatter(x=synth_series.time, y = synth_series.value, name = 'Idealized Event Series')

    fig.show()

    stats ={
            'beg_dur' : float(beg_dur),
            'beg_amp' : float(res['beg_amp'] - synth_val[beg_i]),
            'mid_dur' : float(mid_dur),
            'mid_amp' : float(res['mid_amp'] - synth_val[beg_i]),
            'end_dur' : float(end_dur),
            'end_amp' : float(res['end_amp'] - synth_val[beg_i]),
            'event_start' : float(res['event_start']),
            'event_end' : float(res['event_end'])
        }

    return stats

def save_data(series,stats,load_path,save_path):
    '''Function to save labelled event series and idealized shape statistics

    Parameters
    ----------

    idealized_series : pyleo.Series
        Idealized version of the event in series format generated by gen_fit

    stats : dict
        Dictionary generated by gen_fit containing: beg_dur, beg_amp, mid_dur, mid_amp, end_dur, end_amp, event_start, event_end
    
    load_path : str
        Path to original lipd file

    save_path : str
        Path to lipd file to be generated
    '''

    load_file = lpd.readLipd(load_path)

    labels = np.zeros(series.time.size)
    labels[(series.time >= stats['event_start']) & (series.time <= stats['event_end'])] = 1
    label_list = list(labels)

    C = {}
    C['number'] = len(list(load_file['paleoData']['paleo0']['measurementTable']['paleo0measurement0']['columns'].keys()))+1
    C['units'] = 'NA'
    C['values'] = label_list
    C['variableName'] = 'event'
    C['variableType'] = 'inferred'
    C['event_metadata'] = {}

    for key in list(stats.keys()):
        C['event_metadata'][key] = stats[key]

    load_file['paleoData']['paleo0']['measurementTable']['paleo0measurement0']['columns']['event'] = C

    lpd.validate(load_file,detailed=True)

    lpd.writeLipd(load_file,save_path)
    

