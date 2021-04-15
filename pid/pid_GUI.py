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
import TemperatureController
from collections import deque
from visa import ResourceManager

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
        daq.Indicator(id='my-daq-indicator',
          value=True,
          color="#FF6633",
#          className="two columns",
          size = 25, style = {'width': '50px', 'display': 'inline-block', 'vertical-align':'middle'}
          ),
        html.H4('Temperature stage PID setup', style = {'width': '40%', 'display': 'inline-block','vertical-align':'middle'})
        ]),
        html.Div(id='live-update-text', className = 'row', children  = [
            html.Div([        
                dcc.Graph(id='live-update-graph', 
                      figure= {"layout": plot_layout
                                  }
                      ),
                dcc.Interval(
                    id='interval-component',
                    interval = 1000, # in milliseconds
                    n_intervals = 0,
                    disabled = True
                    )
                ],
            style = {'width' : '60%', 'display': 'inline-block'}        
        ),
        
        html.Div(id = 'buttons-text', children = [
           html.Div(children = [
               daq.PowerButton(
                  id='power-button',
                  on = None,
                  color =  "#FF5E5E",
                  style = {'width' : '25%', 'display': 'inline-block', 'vertical-align':'middle'}
                ), 
               daq.StopButton(id='my-daq-startbutton',
                  buttonText = 'Start',
                  n_clicks = 0,
                  style = {'width' : '25%', 'display': 'inline-block', 'vertical-align':'middle'}
                  ),
               daq.StopButton(id='my-daq-clearbutton',
                 n_clicks = 0,
                 buttonText = 'Clear',
                 style = {'width' : '25%', 'display': 'inline-block', 'vertical-align':'middle'}
                 )
           ],\
            style = {'padding-top' : '10px', 'padding-bottom' : '10px'}
            ),
           html.Div([
               daq.LEDDisplay(
                 id = 'my-curent-T',
                 label = "Current temperature (°C)",
                 labelPosition = 'top',
                 value = f'{0.00:05.2f}',
                 color= "#FF5E5E",
                 style = {'width' : '50%', 'display': 'inline-block', 'vertical-align':'top'}
                 ),
               html.Div( [
                       html.P(id = 'label-setpoint', children = 'Temperature setpoint is 20.00 °C'),
                       dcc.Input(
                           id='set-setpoint',
                           type = 'number',
                           min = 0,
                           max = 100,
                           value = 20.00,
                           debounce = True,
                           size = '25px'
                       )],
                       style = {'width' : '50%', 'display': 'inline-block', 'vertical-align':'top'}),
           ], style = {'padding-top' : '10px', 'padding-bottom' : '10px'}),
          html.Div(id  = 'extra-parameters', className = 'row', children = [
             daq.BooleanSwitch(
                  id='cooling-switch',
                  label = 'Cooling?',
                  on = False,
                  disabled = True,
                  style = {'width' : '50%', 'display': 'inline-block', 'vertical-align':'middle'}
                ),
            daq.NumericInput(
                id='max-power',
                label = 'Max. action (V)',
                min = 0.0,
                max = 21.00,
                value = 5.00,
                style = {'width' : '50%', 'display': 'inline-block', 'vertical-align':'top'}
            )
          ],
            style = {'padding-top' : '10px', 'padding-bottom' : '10px'}),
      html.Div([
          dcc.RadioItems(
             id = 'rtd-type',
            options=[
                {'label': 'Pt100', 'value': 100},
                {'label': 'Pt1000', 'value': 1000}
            ],
            value = 100
        ) 
              ]),
          
       html.Div([
            html.Span('Multimeter address'),
            dcc.Dropdown(id  = 'dropdown-multimeter',
                options = [{'label' : name, 'value': name} for name in lresources],
                value = 'GPIB0::23::INSTR' if 'GPIB0::23::INSTR' in lresources else None,
                placeholder = 'Multimeter address',
                style = {'width' : '200'},
                searchable = False
            ),
            html.Span('Power source address:'),
            dcc.Dropdown(id  = 'dropdown-sourcemeter',
                options = [{'label' : name, 'value': name} for name in lresources],
                value ='GPIB0::5::INSTR' if 'GPIB0::5::INSTR' in lresources else None,
                placeholder = 'Sourcemeter address',
                style = {'width' : '200'},
                searchable = False
            )],
             style = {'padding-top' : '10px', 'padding-bottom' : '10px', 'width': '80%'})           

        ],
        style = {'width' : '40%', 'height' : '100%', 'display': 'inline-block', 'vertical-align':'top'})
       ]),        
   ]) 
    
    
# Multiple components can update everytime interval gets fired.
@app.callback([Output('live-update-graph', 'figure'),
               Output('my-curent-T', 'value')],
              [Input('interval-component', 'n_intervals'),
               Input('my-daq-clearbutton', 'n_clicks')],
              [State('live-update-graph', 'figure')])
def update_graph_live(n, n_clear,figure):
    # Collect some data
    global N_CLICK_PREVIOUS
    tstamp = datetime.datetime.now() #.strftime("%d-%m-%YT %H:%M:%S.%f")
    if n_clear > N_CLICK_PREVIOUS:
        print('Clearing')
        figure['data'][0]['x'] = []
        figure['data'][0]['y'] = []
        figure['data'][1]['y'] = []
        N_CLICK_PREVIOUS += 1

    temperature = p.current_T
    setpoint = p.setpoint
    
    if n == 0:
        x = deque([],MAX_LENGTH)
        y = deque([],MAX_LENGTH)
        y2 = deque([],MAX_LENGTH)
    else:
        x = deque(figure['data'][0]['x'], MAX_LENGTH)
        y = deque(figure['data'][0]['y'], MAX_LENGTH)
        y2 = deque(figure['data'][1]['y'], MAX_LENGTH)
        x.append(tstamp)
        y.append(temperature)
        y2.append(setpoint)

    
#    figure.update_layout(show_legend = True)
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
               [State('power-button', 'on')])
def change_status_on(N, on):
    color = ["#00cc96", '#FF6633']
    label = 'Start'
    if on is None:
        return label, color[1], True
    if on is False:
        return label, color[1], True
    
    status = calc_status(N + 1) and on
    try:
        if status is True:
            print('INFO: Instrument started...')
            p.pid_on()
            p.run()
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
    p.pid_setpoint(value)
    label = f'Temperature setpoint is {p.setpoint:5.2f} °C'
    return [label]

@app.callback([Output('power-button', 'label'),
               Output('my-daq-startbutton', 'disabled'),
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
        return ['Power off'], True, 0, False
    
    try:
        if on:
            p.configurate(setpoint, not cooling, max_power, mult_addr, source_addr, R0)
            label = 'Power ON'
            return [label], False, N, True
        else:
            label = 'Power OFF'
            return [label], True, 0, False
        
    except Exception as e:
        print('ERROR: An error occured in starting the instrument')
        print(e)
        return ['ERROR'], True, 0, False
    
@app.callback([Input('max-power', 'value')])
def max_power(value):
    p.max_poutput = value


if __name__ == '__main__':
    try:
        app.run_server(debug = True, port = 8052, use_reloader = False)
    except KeyboardInterrupt as e:
        print(e)
    