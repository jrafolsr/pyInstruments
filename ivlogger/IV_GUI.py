# -*- coding: utf-8 -*-
"""
Created on Fri Oct 11 09:47:49 2019

@author: JOANRR
"""
#%%
# Necessary as long as I'm working in folder nor added to the path by default
import sys
sys.path.append(r'C:\Users\OPEGLAB\Documents\lab-instrumentation')

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from threading import Thread #, Timer
#import webbrowser
from pyvisa import ResourceManager
from time import sleep
global N_CLICK_PREVIOUS
N_CLICK_PREVIOUS = 0
# Local libraries
from pyInstruments.ivlogger import iv_setup
from pyInstruments.ivlogger import global_settings_iv as gs
from datetime import datetime


  
PORT = 8053 # Where to open the app

gs.init()
calc_status = lambda x:  bool(abs(int((1j**x).real)))

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Preparing the plot
plot_data = [go.Scatter(x=[], y=[], name = 'voltage', mode = 'lines+markers')]

plot_layout = dict(margin =  {'l': 60, 'r': 60, 'b': 60, 't': 20},\
                   legend =  {'x': 0, 'y': 1, 'xanchor': 'left'},\
                   xaxis = dict(title =  "Timestamp"),\
                   yaxis = dict( title =  "Voltage (V)")
                   )
        
#%%
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'IV logger'

app.layout = html.Div(children =  [

        html.Div(className = 'row', children = [
        daq.Indicator(id='my-daq-indicator',
          value=True,
          color="#FF6633",
#          className="two columns",
          size = 25, style = {'width': '50px', 'display': 'inline-block', 'vertical-align':'middle'}
          ),
        html.H4('Keithley 2400 Time-Current-Voltage Logger', style = {'width': '40%', 'display': 'inline-block','vertical-align':'middle'})
        ]),
        html.Div(id='live-update-text', className = 'row', children  = [
        html.Div([        
        dcc.Graph(id='live-update-graph', 
              figure= { "data": plot_data,
                          "layout": plot_layout
                          }
              ),
        dcc.Interval(
            id='interval-component',
            interval = 1000, # in milliseconds
            n_intervals = 0,
            disabled = True
        )],
        style = {'width' : '60%', 'display': 'inline-block'}        
        ),
        
        html.Div(id = 'buttons-text', children = [
           html.Div(children = [
           daq.PowerButton(
              id='power-button',
              color =  "#FF5E5E",
              size = 60,
              on = False,
              style = {'width' : '25%', 'display': 'inline-block', 'vertical-align':'middle'}
            ), 
           daq.StopButton(id='my-daq-startbutton',
              disabled = True,
              buttonText = 'Start',
              n_clicks = 0,
              style = {'width' : '25%', 'display': 'inline-block', 'vertical-align':'middle'}
              ),
           daq.StopButton(id='clear-button',
             n_clicks = 0,
             buttonText = 'Clear',
             style = {'width' : '25%', 'display': 'inline-block', 'vertical-align':'middle'}
             )
           ]),
           html.Div(style = {'width' : '100%', 'display': 'inline-block', 'text-align':'center'}, children  = [
               daq.LEDDisplay(
                    id = 'my-current-V',
                    label = "Current voltage (V)",
                    labelPosition = 'top',
                    value = f'{0.00:05.2f}',
                    color= "#FF5E5E",
                     ),
               daq.LEDDisplay(
                    id = 'my-current-I',
                    label = "Current intensity (mA)",
                    labelPosition = 'top',
                    value = f'{0.00:05.2f}',
                    color= "#FF5E5E",
                    style = {'width' : '50%', 'display': 'inline-block', 'vertical-align':'middle'}
                    )
           ]),
          html.Div(id  = 'extra-parameters', className = 'row', children = [
             daq.BooleanSwitch(
                  id='mode-switch',
                  label = 'CC mode',
                  on = False,
                  disabled = False,
                  style = {'width' : '25%', 'display': 'inline-block', 'vertical-align':'middle'}
                ),
             daq.BooleanSwitch(
                  id='config-switch',
                  label = 'Config',
                  on = False,
                  disabled = False,
                  style = {'width' : '25%', 'display': 'inline-block', 'vertical-align':'middle'}
                ),
            daq.PrecisionInput(
                id='value-input',
                label = f'Current input is 0.00 mA',
                precision = 4,
                min = -10,
                max = 10,
                value = 0.000E0,
                style = {'width' : '50%', 'display': 'inline-block', 'vertical-align':'middle'}
            ),
            html.Div(id="folder-html"),
            dcc.Input(id="folder-input",
                      type="text",
                      placeholder="Folder",
                      value = r'C:\Users\OPEGLAB\Documents\data\goniospectrometer',
                      size = '100%',
                      style =  {'width' : '100%'}),
            html.Div(id="filename-html"),
            dcc.Input(id="filename-input",
                      type="text",
                      placeholder="Filename",
                      size = '100%',
                      value = 'iv_logger',
                      style =  {'width' : '60%'})
          ])
        ],
        style = {'width' : '40%', 'height' : '100%', 'display': 'inline-block', 'vertical-align':'top'})
       ]),
    html.Div(id = 'source-selection', children = ['Sourcemeter address']),
    dcc.Dropdown(id  = 'dropdown-menu',
        options= [{'label' : name, 'value': name} for name in ResourceManager().list_resources()],
        value= 'GPIB0::25::INSTR',
        style = {'width' : '50%'},
        searchable = False
    ),

   ]) 
    
    
# Multiple components can update everytime interval gets fired.
@app.callback([Output('live-update-graph', 'figure'),
               Output('my-current-V', 'value'),
               Output('my-current-I', 'value')],
              [Input('interval-component', 'n_intervals'),
               Input('clear-button', 'n_clicks')],
              [State('live-update-graph', 'figure')])
def update_graph_live(n, n_clear,figure):
    # Collect some data
    global N_CLICK_PREVIOUS
    if n_clear > N_CLICK_PREVIOUS or len(gs.ETIME) > 500:
        print('INFO: Clearing plot')
        gs.ETIME.clear()
        gs.VOLTAGE.clear()
        gs.CURRENT.clear()
        N_CLICK_PREVIOUS += 1
    
    x = list(gs.ETIME)
    
    if gs.MODE == 'CV':
        y = list(gs.CURRENT)
        figure['layout']['yaxis']['title'] = 'Current (mA)'
    else:
        y = list(gs.VOLTAGE)
        figure['layout']['yaxis']['title'] = 'Voltage (V)'
       
#    figure.update_layout(show_legend = True)
    figure['data'][0]['x'] =  x
    figure['data'][0]['y'] = y

    if len(x) == 0:  led = ['00.00'] * 2
    else: led = [f'{gs.VOLTAGE[-1]:05.2f}', f'{gs.CURRENT[-1]*1000:05.2f}']
    
    return figure, led[0], led[1]

@app.callback([Output('my-daq-startbutton', 'buttonText'),
               Output('my-daq-indicator', 'color'),
               Output('interval-component', 'disabled'),
               Output('mode-switch', 'disabled'),
               Output('config-switch', 'disabled')],
               [Input('my-daq-startbutton', 'n_clicks')],
               [State('power-button', 'on'),
                State('dropdown-menu', 'value')],
                prevent_initial_call = True)
def change_status_on(N, on, resource):
    color = ["#00cc96", '#FF6633']
    label = 'Start'
    
    if on is False:
        return label, color[1], True, on, on
    
    status = calc_status(N + 1) and on
    
    try:
        if status is True:
            print('INFO: Measurement started...')
            gs.CONFIG_STATUS =  False
            gs.MEASUREMENT_ON =  True
            gs.set_configuration('resource1', resource)
            args, kwargs = gs.get_configuration()
            thread = Thread(target = iv_setup, args = args, kwargs = kwargs)
            thread.daemon = True
            thread.start()
            label = 'Stop'
        elif status is False:
            print('INFO: Instrument configured and ready!')
            gs.MEASUREMENT_ON =  False
            label = 'Start'
        else:
            pass
        
        return label, color[int(not status)], not status, on, on

    except Exception as e:
         print('ERROR: An error occured in starting the instrument')
         print(e)
         return label, color[1], True, True
     
@app.callback([Output('power-button', 'label'),
               Output('my-daq-startbutton', 'disabled'),
               Output('my-daq-startbutton', 'n_clicks')],
        [Input('power-button', 'on')],
         [State('dropdown-menu', 'value'),
          State('my-daq-startbutton', 'n_clicks'),
          State('config-switch', 'on')],
          prevent_initial_call = True)
def start_instrument(on, resource, N, config_flag):
    if on is None:
        return ['Power off'], True, 
    
    if config_flag:
        gs.set_configuration('interrupt_measurement', True)
    else:
        gs.set_configuration('interrupt_measurement', False)
    
    try:
        if on:
            label = 'Power ON'
            gs.CONFIG_STATUS = config_flag
            gs.set_configuration('resource1', resource)
            args, kwargs = gs.get_configuration()
            iv_setup(*args, **kwargs)
            sleep(0.5)
            return [label], False, N
        else:
            gs.MEASUREMENT_ON =  False
            gs.CONFIG_STATUS =  config_flag
            print('INFO: Instrument is off')
            label = 'Power OFF'
            return [label], True, 0
    except Exception as e:
        print('ERROR: An error occured in starting the instrument')
        print(e)
        return ['ERROR'], True, 0
    
@app.callback([Output('value-input', 'label'),
               Output('mode-switch', 'label')],
        [Input('value-input', 'value'),
         Input('mode-switch', 'on')],
         prevent_initial_call = True)
def set_value(value, mode):
    
    if mode:
        print(f'INFO: Setting the voltage to: {gs.SET_VALUE:.4g} V')
        labeli = f'Voltage input is {value:4.2f} V'
        gs.MODE = 'CV'
        gs.set_configuration('mode', 'CV')
        gs.set_configuration('cmpl', 0.05)
        labelm = 'CV mode'
    else:
        print(f'INFO: Setting the current to: {gs.SET_VALUE:.4g} mA')
        labeli = f'Current input is {value:4.2f} mA'
        gs.MODE = 'CC'
        gs.set_configuration('mode', 'CC')
        gs.set_configuration('cmpl', 21)
        labelm = 'CC mode'
        
    gs.SET_VALUE = value
    return labeli, labelm

@app.callback([Output('folder-html', 'children')],
        [Input('folder-input', 'value')])
def set_folder(value):
    gs.set_configuration('folder', value)
    children = f'Folder:  {value}'
    return [children]

@app.callback([Output('filename-html', 'children')],
        [Input('filename-input', 'value')])
def set_filename(value):
    timestamp = datetime.now().strftime("%Y-%m-%dT%Hh%Mm%Ss")  
    fname = timestamp + '_' + value
    gs.set_configuration('fname', fname)
    children = f'Filename:  {fname}'
    return [children]


#def open_browser(PORT):
#	webbrowser.open_new("http://127.0.0.1:{}/".format(PORT))

if __name__ == '__main__':
    try:
        app.run_server(debug = True, port = PORT)
    except KeyboardInterrupt as e:
        print(e)

    