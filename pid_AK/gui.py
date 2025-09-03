# -*- coding: utf-8 -*-
"""
Created on Fri Oct 11 09:47:49 2019

@author: JOANRR
"""
import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
from dash.dependencies import Input, Output, State
from pyInstruments.pid import TemperatureController
from threading  import Thread
from collections import deque
from pyvisa import ResourceManager
import getopt
import sys


global N_CLICK_PREVIOUS, MAX_LENGTH
N_CLICK_PREVIOUS = 0
MAX_LENGTH = 500


# Listing the available resources
lresources = ResourceManager().list_resources()

# Initialize the pid task

p = TemperatureController()

# Preparing the plot
plot_layout = dict(margin =  {'l': 60, 'r': 60, 'b': 60, 't': 20},\
                   legend =  {'x': 0, 'y': 1, 'xanchor': 'left'},\
                   xaxis = dict(title =  "Timestamp", font = dict(size = 24)),\
                   yaxis = dict( title =  "Temperature (°C)", font = dict(size = 24))
                   )


calc_status = lambda x:  bool(abs(int((1j**x).real)))

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets = external_stylesheets)
app.title = 'PID'
app.layout = html.Div(children =  [

        html.Div(className = 'row', children = [
        html.Div(className = 'column left', children = [
            daq.Indicator(id='my-daq-indicator',
              value=True,
              color="#FF6633",
    #          className="two columns",
              size = 25, style = {'width': '50px', 'display': 'inline-block', 'vertical-align':'middle'}
              ),
            html.H4('Temperature stage PID setup', style = {'display': 'inline-block','vertical-align':'middle'}),  
            dcc.Graph(id='live-update-graph', 
                  figure= {"layout": plot_layout
                              }
                  ),
            dcc.Interval(
                id='interval-component',
                interval = 1000, # in milliseconds
                n_intervals = 0,
                disabled = True
                ),
            html.Span('Multimeter address:'),
            dcc.Dropdown(id  = 'dropdown-multimeter',
                options = [{'label' : name, 'value': name} for name in lresources],
                value = 'GPIB0::23::INSTR' if 'GPIB0::23::INSTR' in lresources else None,
                placeholder = 'Multimeter address',
                style = {'width' : '80%', 'min-width' : '150px'},
                searchable = False
            ),
            html.Span('Power source address:'),
            dcc.Dropdown(id  = 'dropdown-sourcemeter',
                options = [{'label' : name, 'value': name} for name in lresources],
                value ='GPIB0::5::INSTR' if 'GPIB0::5::INSTR' in lresources else None,
                placeholder = 'Sourcemeter address',
                style = {'width' : '80%', 'min-width' : '150px'},
                searchable = False
                )
            ]),
        html.Div(className = 'column middle', children = [
               daq.PowerButton(
                  id='power-button',
                  on = None,
                  color =  "#FF5E5E",
                ), 
               daq.StopButton(id='my-daq-startbutton',
                  buttonText = 'Start',
                  n_clicks = 0,
                  ),
               daq.StopButton(id='my-daq-clearbutton',
                 n_clicks = 0,
                 buttonText = 'Clear',
                 ),
              daq.StopButton(id='refresh-button',
                 n_clicks = 0,
                 buttonText = 'Refresh',
                 ),
              html.P(['Sensor type:',
                  dcc.RadioItems(
                     id = 'rtd-type',
                    options=[
                        {'label': 'Pt100', 'value': 100},
                        {'label': 'Pt1000', 'value': 1000}
                        ],
                    value = 100
                    ),
              daq.BooleanSwitch(
                  id='cooling-switch',
                  label = 'Cooling?',
                  on = False,
                  disabled = True,
                  ),
              daq.NumericInput(
                    id='max-power',
                    label = 'Max. action (V)',
                    min = 0.0,
                    max = 21.00,
                    value = 5.00,
                    )
              ]),
           ]),
           html.Div( className = 'column right', children = [
               html.Div([
                   html.P(id = 'label-setpoint', children = 'Temperature setpoint is 20.00 °C'),
                   dcc.Input(
                       id='set-setpoint',
                       type = 'number',
                       min = 0,
                       max = 100,
                       value = 20.00,
                       debounce = True,
                       size = '10'
                      ),
                   html.Br(),
                   html.Br(),
                   html.P('Current temperature (°C)'),
                   daq.LEDDisplay(
                         id = 'my-curent-T',
                         labelPosition = 'top',
                         value = f'{0.00:05.2f}',
                         color= "#FF5E5E",
                         ),
               ], style ={'padding-top' : '25px', 'text-align' : 'center'})
           ]),
        ])
       ])
    
    
# Multiple components can update everytime interval gets fired.
@app.callback([Output('live-update-graph', 'figure'),
               Output('my-curent-T', 'value')],
              [Input('interval-component', 'n_intervals'),
               Input('my-daq-clearbutton', 'n_clicks')],
              [State('live-update-graph', 'figure')])
def update_graph_live(n, n_clear,figure):
    # Determine which button has been clicked
    ctx = dash.callback_context

    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'interval-component':
        tstamp = datetime.datetime.now() #.strftime("%d-%m-%YT %H:%M:%S.%f")
 
        x = deque(figure['data'][0]['x'], MAX_LENGTH)
        y = deque(figure['data'][0]['y'], MAX_LENGTH)
        y2 = deque(figure['data'][1]['y'], MAX_LENGTH)
        x.append(tstamp)
        y.append( p.current_T)
        y2.append(p.setpoint)
    elif button_id == 'my-daq-clearbutton':
        print('Clearing')
        x = []
        y = []
        y2 = []
    else:
        x = y = y2 = []

    figure['data'] = [{
        'x': list(x),
        'y': list(y),
        'name': 'Current T',
        'mode': 'lines+markers',
        'type': 'scatter'
    },
    {
        'x': list(x),
        'y': list(y2),
        'name': 'Setpoint T',
        'mode': 'lines+markers',
        'type': 'scatter'
    }]
    
    if len(x) == 0:  Tstring = '00.00'
    else: Tstring = '{0:05.2f}'.format(y[-1])

    return figure, Tstring

@app.callback([Output('my-daq-startbutton', 'buttonText'),
               Output('my-daq-indicator', 'color'),
               Output('interval-component', 'disabled')],
               [Input('my-daq-startbutton', 'n_clicks')],
               prevent_initial_call = True)
def start_measurement(N):
    color = ["#00cc96", '#FF6633']
    label = 'Start'
 
    status = calc_status(N + 1)
    try:
        if status is True:
            print('INFO: Instrument started...')
            p.pid_on()
            t = Thread(target = p.run)
            t.daemon = True
            t.start()
            label = 'Stop'
        elif status is False:
            print('INFO: Instrument configured and ready!')
            p.pid_off()
            label = 'Start'
        else:
            pass
        
        return label, color[int(not status)], not status
    except Exception as e:
        print('ERROR: An error occured in starting the instrument')
        print(e)
        return label, color[1], True

@app.callback([Output('label-setpoint', 'children')],
              [Input('set-setpoint', 'value')])
def write_setpoint(value):
    p.setpoint = value
    label = f'Temperature setpoint is {p.setpoint:5.2f} °C'
    return [label]

@app.callback([Output('my-daq-startbutton', 'disabled'),
               Output('my-daq-startbutton', 'n_clicks'),
               Output('cooling-switch', 'disabled')],
              [Input('power-button', 'on')],
              [State('my-daq-startbutton', 'n_clicks'),
               State('set-setpoint', 'value'),
               State('cooling-switch', 'on'),
               State('max-power', 'value'),
               State('dropdown-multimeter', 'value'),
               State('dropdown-sourcemeter', 'value'),
               State('rtd-type', 'value')])
def start_instrument(on, N, setpoint, cooling, max_power, mult_addr, source_addr, R0):
    """The cooling flag needs to be denied, as the TemperatureController.config() ask if HEATING, just the opposite"""
    
    if on is None:
        return True, 0, False
    
    try:
        if on:
            p.configurate(setpoint, not cooling, max_power, mult_addr, source_addr, R0)
            
            return False, N, True
        else:

            return True, 0, False
        
    except Exception as e:
        print('ERROR: An error occured in starting the instrument')
        print(e)
        return True, 0, False
    
@app.callback([Output('max-power', 'label')],
        [Input('max-power', 'value')])
def max_power(value):
    p.max_poutput = value
    label = 'Max. action (V)'
    return [label]

@app.callback([Output('dropdown-multimeter', 'value'),
                Output('dropdown-multimeter', 'options'),
                Output('dropdown-sourcemeter', 'value'),
                Output('dropdown-sourcemeter', 'options')],
        [Input('refresh-button', 'n_clicks')])
def refresh_resources(n):
    list_of_resources = ResourceManager().list_resources()
    default_resources = [s for s in list_of_resources if 'GPIB' in s]
    if len(default_resources) > 1:
        sourcemeter_resource = default_resources[0]
        multimeter_resource = default_resources[1]
    else:
        sourcemeter_resource = None
        multimeter_resource = None
        
    options =  [{'label' : name, 'value': name} for name in list_of_resources]
    
    return multimeter_resource, options, sourcemeter_resource, options

if __name__ == '__main__':
    
    # Default values
    debug = True
    port = 8052
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
