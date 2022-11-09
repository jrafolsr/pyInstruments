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
#import webbrowser
from pyvisa import ResourceManager
from time import sleep
global N_CLICK_PREVIOUS
N_CLICK_PREVIOUS = 0
# Local libraries
from pyInstruments.ivsweep import IVSweeperTask
from datetime import datetime
import getopt
import sys
from pathlib import Path

calc_status = lambda x:  bool(abs(int((1j**x).real)))

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Preparing the plot
plot_data = []

plot_layout = dict(margin =  {'l': 60, 'r': 60, 'b': 60, 't': 20},\
                   legend =  {'x': 0, 'y': 1, 'xanchor': 'left'},\
                   xaxis = dict(title =  "Voltage (V)"),\
                   yaxis = dict( title =  "Current (A)")
                   )
        
#%%
# Initalize the logging task with the default values
t = IVSweeperTask()

# Initialize some other variables
list_of_resources = ResourceManager().list_resources()
default_resource = [s for s in list_of_resources if 'GPIB' in s]
default_resource = None if len(default_resource) == 0 else default_resource[0]

app = dash.Dash(__name__, external_stylesheets = external_stylesheets)
app.title = 'IV sweeper'

app.layout = html.Div(children =  [

        html.Div(id='main-row', className = 'row', children = [
        html.Div(className = 'column left', children = [  
            daq.Indicator(id='my-daq-indicator',
              value=True,
              color="#FF6633",
    #          className="two columns",
              size = 25, style = {'width': '50px', 'display': 'inline-block', 'vertical-align':'middle'}
              ),
            html.H4('I-V Sweeper', style = {'display': 'inline-block','vertical-align':'middle'}),
    
                   
            dcc.Graph(id='live-update-graph', 
                  figure= { "data": plot_data,
                              "layout": plot_layout
                              }
                  ),
            html.Span(id = 'resource-selection', children = ['Sourcemeter address']),
                dcc.Dropdown(id  = 'resource-dropdown',
                options= [{'label' : name, 'value': name} for name in list_of_resources],
                value= default_resource,
                style = {'width' : '100%'},
                searchable = False
                ),
            html.Span(id = 'graph-options', children = ['Graph options']),
            dcc.RadioItems(id = 'select-scale',
                   options=[
                    {'label': 'linear', 'value': 'linear'},
                    {'label': 'log', 'value': 'log'},
                    ],
                    value = 'linear')
        ]),
        
        html.Div(className = 'column middle',  children = [
           daq.PowerButton(
              id='power-button',
              color =  "#FF5E5E",
              size = 60,
              on = False,
              label = 'Power OFF',
              labelPosition = 'top'
            ), 
           daq.StopButton(id='my-daq-startbutton',
              disabled = True,
              buttonText = 'Run',
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
           html.P(['Mode: ', 
             daq.BooleanSwitch(
                  id='mode-switch',
                  label = 'Step',
                  on = False,
                  disabled = False,
                ),
               ]),

         html.P(['Term: ', 
             daq.BooleanSwitch(
                  id='term-switch',
                  label = 'Front',
                  on = False,
                  disabled = False,
                ),
             ]),
           ]),
        
        html.Div(className = 'column right', children = [
            html.P( ['Start (V): ', 
                     dcc.Input(
                      id = "start-voltage",
                      type = 'number',
                      value = 0,
                      size = '5'
                     ),
                ]),
            html.P( ['Stop (V): ', 
                dcc.Input(
                      id = "stop-voltage",
                      type = 'number',
                      value = 1,
                      size = '5'
                     ),
                ]),
            html.P( ['Step (V): ', 
                dcc.Input(
                      id = "step-value",
                      type = 'number',
                      value = 0.1,
                      size = '5'
                     ),
                ]),
            html.P( ['Compliance (A): ', 
                dcc.Input(
                      id = "compliance-value",
                      type = 'number',
                      value = 0.1,
                      size = '5'
                     ),
                ]),
            html.P(['Sensing range: ',
                dcc.Dropdown(id = 'range-menu',
                    options=[
                        {'label': 'auto', 'value': 'auto'},
                        {'label': '1uA', 'value': 1.05e-6},
                        {'label': '10uA', 'value': 10.5e-6},
                        {'label': '100uA', 'value': 105e-6},
                        {'label': '1mA', 'value': 1.05e-3},
                        {'label': '10mA', 'value': 10.5e-3},
                        {'label': '100mA', 'value': 105e-3},
                        {'label': '1A', 'value': 1.05},
                        ],
                    value = 'auto',
                    style = dict(width = '150px')
                    )
                ]),
            html.P( ['Delay between steps (ms): ', 
                dcc.Input(
                      id = "delay-value",
                      type = 'number',
                      value = 100,
                      size = '10',
                      min = 0,
                      max = 1000,
                      placeholder = "0 for min delay"
                     ),
                ]),
            html.P('List of values:'),
            dcc.Textarea(
                id='sweeplist-value',
                value='0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0',
                style={'width': '100%', 'min-height': 50},
                disabled = True
                ),
            html.P(id="folder-html"),
            dcc.Input(id="folder-input",
                type="text",
                placeholder="Folder",
                value = str(Path.home() / 'Documents'),
                size = '100%',
                style =  {'width' : '100%'}),
            html.P(id="filename-html"),
            dcc.Input(id="filename-input",
                      type="text",
                      placeholder="Filename",
                      size = '100%',
                      value = 'iv_sweeper',
                      style =  {'width' : '100%'}),
            ])
        ]),
   ]) 
    

@app.callback([Output('live-update-graph', 'figure')],
               [Input('my-daq-startbutton', 'n_clicks'),
                Input('clear-button', 'n_clicks'),
                Input('select-scale', 'value')],
               [State('live-update-graph', 'figure'),
                State('folder-input', 'value'),
                State('filename-input', 'value')],
                prevent_initial_call = True)
def start_measurement(n_run, n_clear, scale_type, figure, folder, filename):
    
    # Determine which button has been clicked
    ctx = dash.callback_context

    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'my-daq-startbutton':
        timestamp = datetime.now().strftime("%Y-%m-%dT%Hh%Mm%Ss")  
        filename = timestamp + '_' + filename
        t.filename = filename
        t.folder = folder
        
        try:
            print('INFO: Measurement started...')
            t.run()
            x = list(t.voltage)
            y = list(t.intensity)
        except Exception as e:
             print('ERROR: An error occured in starting the instrument. Please restart it.')
             print(e)
             return True
    elif button_id == 'clear-button':
        figure['data'] = []
        x = []
        y = []
    
    elif button_id == 'select-scale':
        figure
        figure['layout']['yaxis']['type'] = scale_type
        return [figure]
    
    # Updatting the plot
    n_dataset = len(figure['data'])
    figure['data'].append(go.Scatter(x = x , y = y, name = f'dataset #{n_dataset}', mode = 'lines+markers'))
    figure['layout']['show_legend'] = True
    
    return  [figure]
        

     
@app.callback([Output('my-daq-indicator', 'color'),
               Output('power-button', 'label'),
               Output('my-daq-startbutton', 'disabled'),
               Output('mode-switch', 'disabled'),
               Output('term-switch', 'disabled')],
        [Input('power-button', 'on')],
         [State('my-daq-startbutton', 'n_clicks'),
          State('resource-dropdown', 'value'),
          State('start-voltage', 'value'),
          State('stop-voltage', 'value'),
          State('step-value', 'value'),
          State('compliance-value', 'value'),
          State('range-menu', 'value'),
          State('sweeplist-value', 'value'),
          State('delay-value', 'value')],
          prevent_initial_call = True)

def start_instrument(on, N, resource, start_value, stop_value, step_value, compliance_value, range_value, sweep_list, delay):
    color = dict(green = "#00cc96", red = '#FF6633')
    t.resource = resource
    sweep_list = [float(s.strip()) for s in sweep_list.strip().split(',')]
    t.configuration['sweep_list'] = sweep_list
    t.configuration['start'] = start_value
    t.configuration['stop'] = stop_value
    t.configuration['step'] = step_value
    t.configuration['cmpl'] = compliance_value
    t.configuration['ranging'] = range_value
    t.configuration['delay'] = delay/1000 if delay > 0 else 'auto'
    
    if on is None:
        return color['red'], 'Power OFF', True, False, False

    try:
        if on:
            label = 'Power ON'
            t.start_instrument()
            sleep(0.5)
            return color['green'], label, False,True, True
        else:
            print('INFO: Instrument is off')
            label = 'Power OFF'
            return color['red'], label, True, False, False
    
    except Exception as e:
        print('ERROR: An error occured in starting the instrument')
        print(e)
        return color['red'], 'Power OFF', True, False, False
    

@app.callback([Output('term-switch', 'label')],
        [Input('term-switch', 'on')])
def set_term(term):
    if term:
        term = 'REAR'
    else:
        term = 'FRONT'
    t.configuration['term'] = term
    return [term]

@app.callback([Output('mode-switch', 'label'),
               Output('sweeplist-value', 'disabled')],
        [Input('mode-switch', 'on')])
def set_mode(mode):
    if mode:
        mode = 'list'  
        disabled_list = False
    else:
        mode = 'step'
        disabled_list = True

    t.configuration['mode'] = mode
    
    return mode, disabled_list

@app.callback([Output('resource-dropdown', 'value'),
        Output('resource-dropdown', 'options')],
        [Input('refresh-button', 'n_clicks')])
def refresh_resources(n):
    list_of_resources = ResourceManager().list_resources()
    default_resource = [s for s in list_of_resources if 'GPIB' in s]
    default_resource = None if len(default_resource) == 0 else default_resource[0]
    
    return default_resource, [{'label' : name, 'value': name} for name in list_of_resources]


if __name__ == '__main__':
    # Default values
    debug = True
    port = 8054
    user_reloader = False
    argv = sys.argv[1:]
    
    try:
        options, args = getopt.getopt(argv, "p:d:r:",
                                   ["port =",
                                    "debug =",
                                    "user_reloader ="])
        
        
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

    