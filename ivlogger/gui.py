# -*- coding: utf-8 -*-
"""
Created on Fri Oct 11 09:47:49 2019

@author: JOANRR
"""
#%%
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from threading import Thread #, Timer
#import webbrowser
from time import sleep
global N_CLICK_PREVIOUS
N_CLICK_PREVIOUS = 0
# Local libraries
from pyInstruments.ivlogger import IVLoggerTask
from datetime import datetime
import getopt
import sys
from pathlib import Path
from pyvisa import ResourceManager


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
# Initalize the logging task with the default values
t = IVLoggerTask()

# Initialize some other variables
list_of_resources = ResourceManager().list_resources()
default_resource = [s for s in list_of_resources if 'GPIB' in s]
default_resource = None if len(default_resource) == 0 else default_resource[0]

app = dash.Dash(__name__, external_stylesheets = external_stylesheets)
app.title = 'IV Logger'

app.layout = html.Div(children =  [

        html.Div(id='main-row', className = 'row', children = [
        html.Div(className = 'column left', children = [  
            daq.Indicator(id='my-daq-indicator',
              value=True,
              color="#FF6633",
    #          className="two columns",
              size = 25, style = {'width': '50px', 'display': 'inline-block', 'vertical-align':'middle'}
              ),
            html.H4('Keithley 2400 Time-Current-Voltage Logger', style = {'display': 'inline-block','vertical-align':'middle'}),
    
                   
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
                ),
            html.Span(id = 'resource-selection', children = ['Sourcemeter address']),
                dcc.Dropdown(id  = 'resource-dropdown',
                options= [{'label' : name, 'value': name} for name in list_of_resources],
                value= default_resource,
                style = {'width' : '100%'},
                searchable = False
                ),
        ]),
        
        html.Div(className = 'column middle',  children = [
           daq.PowerButton(
              id='power-button',
              color =  "#FF5E5E",
              size = 60,
              on = False,
            ), 
           daq.StopButton(id='my-daq-startbutton',
              disabled = True,
              buttonText = 'Start',
              n_clicks = 0,
              ),
           daq.StopButton(id='clear-button',
             n_clicks = 0,
             buttonText = 'Clear',
             ),
           daq.StopButton(id='refresh-button',
             n_clicks = 0,
             buttonText = 'Refresh',
             ),
           daq.BooleanSwitch(
                  id='mode-switch',
                  label = 'CC mode',
                  on = False,
                  disabled = False,
                ),
             daq.BooleanSwitch(
                  id='config-switch',
                  label = 'Configurate',
                  on = True,
                  disabled = False,
                ),
             daq.BooleanSwitch(
                  id='term-switch',
                  label = 'REAR',
                  on = True,
                  disabled = False,
                ),
           ]),
        html.Div(className = 'column right', children = [
            daq.PrecisionInput(
                 id='value-input',
                 label = 'Current input is 0.00 mA',
                 precision = 4,
                 min = -10,
                 max = 50,
                 value = 0.000E0,
                 size = 100,
                 ),
            html.Br(),
            html.P("Voltage (V)"),
            daq.LEDDisplay(
                 id = 'my-current-V',
#                 label = "Voltage (V)",
#                 labelPosition = 'top',
                 value = f'{0.00:05.2f}',
                 color= "#FF5E5E",
                 size = 40
                  ),
            html.Br(),
            html.P("Current (mA)"),
            daq.LEDDisplay(
                 id = 'my-current-I',
#                 label = "Current (mA)",
#                 labelPosition = 'top',
                 value = f'{0.00:05.2f}',
                 color= "#FF5E5E",
                 size = 40
                 ),
            html.Br(),
            html.P(id="folder-html"),
            dcc.Input(id="folder-input",
                type="text",
                placeholder="Folder",
                value = str(Path.home() / 'Documents'),
                # value = r'C:\Users\JOANRR\Documents\Python Scripts\data',
                size = '100',
                style =  {'width' : '100%'}),
            html.Br(),
            html.P(id="filename-html"),
            dcc.Input(id="filename-input",
                      type="text",
                      placeholder="Filename",
                      size = '100',
                      value = 'iv_logger',
                      style =  {'width' : '100%'})
            ])
        ]),
   ]) 
    
    
# Multiple components can update everytime interval gets fired.
@app.callback([Output('live-update-graph', 'figure'),
               Output('my-current-V', 'value'),
               Output('my-current-I', 'value')],
              [Input('interval-component', 'n_intervals'),
               Input('clear-button', 'n_clicks')],
              [State('live-update-graph', 'figure')])
def update_graph_live(n, n_clear,figure):
    # Determine which button has been clicked
    ctx = dash.callback_context

    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
              
    if button_id == 'clear-button' or len(t.time) > 500:
        print('INFO: Clearing plot')  
        t.time.clear()
        t.voltage.clear()
        t.intensity.clear()
        
    x = list(t.time)
    
    if t.mode == 'CV':
        y = list(t.intensity)
        figure['layout']['yaxis']['title'] = 'Current (mA)'
    else:
        y = list(t.voltage)
        figure['layout']['yaxis']['title'] = 'Voltage (V)'
        
    figure['data'][0]['x'] =  x
    figure['data'][0]['y'] = y

    if len(t.time) == 0:  led = ['00.00'] * 2
    else: led = [f'{t.voltage[-1]:05.2f}', f'{t.intensity[-1]*1000:05.2f}']
    
    return figure, led[0], led[1]

@app.callback([Output('my-daq-startbutton', 'buttonText'),
               Output('my-daq-indicator', 'color'),
               Output('interval-component', 'disabled'),
               Output('mode-switch', 'disabled'),
               Output('config-switch', 'disabled'),
               Output('term-switch', 'disabled')],
               [Input('my-daq-startbutton', 'n_clicks')],
               [State('power-button', 'on'),
                State('value-input', 'value'),
                State('config-switch', 'on')],
                prevent_initial_call = True)
def start_measurement(N, on, value, config_flag):
    color = ["#00cc96", '#FF6633']
    label = 'Start'
    
    if on is False:
        return label, color[1], True, on, on, on
    
    status = calc_status(N + 1) and on
    
    try:
        if status is True:
            print('INFO: Measurement started...')
            thread = Thread(target = t.run, args = (value,), kwargs = dict(interrupt_measurement = not config_flag, dt_fix = False))
            thread.daemon = True
            thread.start()
            label = 'Stop'
        elif status is False:
            t.measurement_off()
            label = 'Start'
        else:
            pass
        
        return label, color[int(not status)], not status, on, on, on

    except Exception as e:
         print('ERROR: An error occured in starting the instrument. Please restart it.')
         print(e)
         return label, color[1], on, on, on
     
@app.callback([Output('power-button', 'label'),
               Output('my-daq-startbutton', 'disabled'),
               Output('my-daq-startbutton', 'n_clicks')],
        [Input('power-button', 'on')],
         [State('my-daq-startbutton', 'n_clicks'),
          State('config-switch', 'on')],
          prevent_initial_call = True)
def start_instrument(on, N, config_flag):
    if on is None:
        return ['Power off'], True, 
    
    t.config_flag = config_flag
    
    try:
        if on:
            label = 'Power ON'
            t.start_instrument()
            sleep(0.5)
            return [label], False, N
        else:
            t.measurement_off()
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
        print(f'INFO: Setting the voltage to: {value:.4g} V')
        labeli = f'Voltage input is {value:4.2f} V'       
        labelm = 'CV mode'
        t.value = value
        t.mode = 'CV'
        t.configuration['cmpl'] = 0.05
    else:
        print(f'INFO: Setting the current to: {value:.4g} mA')
        labelm = 'CC mode'
        labeli = f'Current input is {value:4.2f} mA'
        t.value = value
        t.mode = 'CC'
        t.configuration['cmpl'] = 21
        
    return labeli, labelm

@app.callback([Output('term-switch', 'label')],
        [Input('term-switch', 'on')])
def set_term(term):
    if term:
        term = 'REAR'
    else:
        term = 'FRONT'
    t.configuration['term'] = term
    
    return [term]


@app.callback([Output('folder-html', 'children')],
        [Input('folder-input', 'value')])
def set_folder(folder):
    children = 'Folder:'
    t.folder = folder
    return [children]

@app.callback([Output('filename-html', 'children')],
        [Input('filename-input', 'value')])
def set_filename(filename):
    timestamp = datetime.now().strftime("%Y-%m-%dT%Hh%Mm%Ss")  
    filename = timestamp + '_' + filename
    t.filename = filename
    children = 'Filename:'
    return [children]


@app.callback([Output('resource-selection', 'children')],
        [Input('resource-dropdown', 'value')])
def set_resource(resource):
    children = f'Sourcemeter addres: {resource}'
    t.resource = resource
    return [children]

@app.callback([Output('resource-dropdown', 'value'),
        Output('resource-dropdown', 'options')],
        [Input('refresh-button', 'n_clicks')],
        prevent_initial_call = True)
def refresh_resources(n):
    list_of_resources = ResourceManager().list_resources()
    default_resource = [s for s in list_of_resources if 'GPIB0' in s]
    default_resource = None if len(default_resource) == 0 else default_resource[0]
    
    return default_resource, [{'label' : name, 'value': name} for name in list_of_resources]
#def open_browser(PORT):
#	webbrowser.open_new("http://127.0.0.1:{}/".format(PORT))

if __name__ == '__main__':
    # Default values
    debug = True
    port = 8053
    user_reloader = False
    argv = sys.argv[1:]
    
    try:
        options, args = getopt.getopt(argv, "p:d:r:",
                                   ["port =",
                                    "debug =",
                                    "user_reloader = "])
        
        
        for name, value in options:
            if name in ['-d', '--debug']:
                if value.lower() in ['true', '1']:
                    debug = True
                else:
                    debug = False       
            elif name in ['-p', '--port']:
                port = value
            elif name in ['-r', '--user_reloader']:
                if value.lower() in ['true', '1']:
                    user_reloader = True
                else:
                    user_reloader = False
                
        app.run_server(debug = debug, port = port, use_reloader = user_reloader)
        
    except KeyboardInterrupt:
        print("Program terminated.")
    except Exception as e:
        print(e)

    