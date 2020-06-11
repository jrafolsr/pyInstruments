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
from plotly import subplots
import plotly.graph_objs as go
from threading import Thread #, Timer
#import webbrowser
from visa import ResourceManager
from time import sleep
global N_CLICK_PREVIOUS
N_CLICK_PREVIOUS = 0
# Local libraries
from pyLab_v2.ivl_setups import ivl_setup_cc
from pyLab_v2 import global_settings_ivl as gs

      
PORT = 8051 # Where to open the app

gs.init()
calc_status = lambda x:  bool(abs(int((1j**x).real)))

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Preparing the plots (2 independent plots, in this case)
trace1 = go.Scatter(x=[], y=[], name = 'voltage', mode = 'lines+markers')
trace2 = go.Scatter(x=[], y=[], name = 'luminance', mode = 'lines+markers')
# Configuration and layout
fig = subplots.make_subplots(rows=2, cols=1, specs=[[{}], [{}]],
                          shared_xaxes=True, shared_yaxes=False,
                          vertical_spacing=0.1)
fig.append_trace(trace1, 1, 1)
fig.append_trace(trace2, 2, 1)
fig['layout'].update({'margin' : {'l': 60, 'r': 60, 'b': 60, 't': 20},
                            'legend' :  {'x': 0, 'y': 1, 'xanchor': 'left'}
                            }
                )
dic_title = { 'font' : {'size' : 18}}
fig.update_xaxes(title_text="Timestamp", title = dic_title, row=2, col=1)  
fig.update_yaxes(title_text="Voltage (V)",title = dic_title, row=1, col=1)               
fig.update_yaxes(title_text="Luminance (cd/m<sup>2</sup>)",title = dic_title, row=2, col=1)   
#%%
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(children =  [

        html.Div(className = 'row', children = [
        daq.Indicator(id='my-daq-indicator',
          value=True,
          color="#FF6633",
#          className="two columns",
          size = 25, style = {'width': '50px', 'display': 'inline-block', 'vertical-align':'middle'}
          ),
        html.H4('IVL characterisation', style = {'width': '40%', 'display': 'inline-block','vertical-align':'middle'})
        ]),
        html.Div(id='live-update-text', className = 'row', children  = [
        html.Div([        
        dcc.Graph(id='live-update-graph', 
              figure= fig,),
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
              style = {'width' : '25%', 'display': 'inline-block', 'vertical-align':'middle'}
            ), 
           daq.StopButton(id='my-daq-startbutton',
              disabled = True,
              buttonText = 'Start',
              n_clicks = 0,
              style = {'width' : '25%', 'display': 'inline-block', 'vertical-align':'middle'}
              ),
           daq.StopButton(id='my-daq-clearbutton',
             n_clicks = 0,
             buttonText = 'Clear',
             style = {'width' : '25%', 'display': 'inline-block', 'vertical-align':'middle'}
             )
           ]),
           html.Div([
           html.Div(style = {'width' : '50%', 'display': 'inline-block', 'vertical-align':'middle'}, children  = [
               daq.LEDDisplay(
                 id = 'my-current-V',
                 label = "Current voltage (V)",
                  labelPosition = 'bottom',
                 value = f'{0.00:05.2f}',
                 color= "#FF5E5E",
                 ),
               daq.LEDDisplay(
                 id = 'my-current-L',
                 label = "Current luminance (cd/m2)",
                  labelPosition = 'bottom',
                 value = f'{0.00:05.2f}',
                 color= "#FF5E5E",
                 )
           ]),
           daq.LEDDisplay(
                 id = 'my-current-I',
                 label = "Current intensity (mA)",
                  labelPosition = 'bottom',
                 value = f'{0.00:05.2f}',
                 color= "#FF5E5E",
                 style = {'width' : '50%', 'display': 'inline-block', 'vertical-align':'middle'}
                 )
           ]),
          html.Div(id  = 'extra-parameters', className = 'row', children = [
             daq.BooleanSwitch(
                  id='operating-mode-switch',
                  label = 'CC / CV',
                  on = False,
                  disabled = True,
                  style = {'width' : '25%', 'display': 'inline-block', 'vertical-align':'middle'}
                ),
            daq.PrecisionInput(
                id='current-input',
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
                      value = r'C:\Users\OPEGLAB\Documents\self-heating',
                      size = '100%',
                      style =  {'width' : '100%'}),
            html.Div(id="filename-html"),
            dcc.Input(id="filename-input",
                      type="text",
                      placeholder="Filename",
                      size = '100%',
                      value = 'ivl-curve',
                      style =  {'width' : '60%'})
          ])
        ],
        style = {'width' : '40%', 'height' : '100%', 'display': 'inline-block', 'vertical-align':'top'})
       ]),
    html.Div(id = 'source-selection', children = ['Sourcemeter address']),
    dcc.Dropdown(id  = 'dropdown-menu',
        options= [{'label' : name, 'value': name} for name in ResourceManager().list_resources()],
        value= 'GPIB0::24::INSTR',
        style = {'width' : '50%'},
        searchable = False
    ),

   ]) 
    
    
# Multiple components can update everytime interval gets fired.
@app.callback([Output('live-update-graph', 'figure'),
               Output('my-current-V', 'value'),
                Output('my-current-L', 'value'),
                Output('my-current-I', 'value')],
              [Input('interval-component', 'n_intervals'),
               Input('my-daq-clearbutton', 'n_clicks')],
              [State('live-update-graph', 'figure')])
def update_graph_live(n, n_clear,figure):
    # Collect some data
    global N_CLICK_PREVIOUS
    if n_clear > N_CLICK_PREVIOUS or len(gs.ETIME) > 500:
        print('INFO: Clearing plot')
        gs.ETIME.clear()
        gs.VOLTAGE.clear()
        gs.LUMINANCE.clear()
        gs.CURRENT.clear()
        N_CLICK_PREVIOUS += 1
    
    x = list(gs.ETIME)
    y = list(gs.VOLTAGE)
    y2 = list(gs.LUMINANCE)
    
    
#    figure.update_layout(show_legend = True)
    figure['data'][0]['x'] =  x
    figure['data'][0]['y'] = y
    figure['data'][1]['x'] = x
    figure['data'][1]['y'] = y2

    if len(x) == 0:  led = ['00.00'] * 3
    else: led = [f'{y[-1]:05.2f}', f'{y2[-1]:05.2f}',f'{gs.CURRENT[-1]*1000:05.2f}']

    return figure, led[0], led[1], led[2]

@app.callback([Output('my-daq-startbutton', 'buttonText'),
               Output('my-daq-indicator', 'color'),
               Output('interval-component', 'disabled')],
               [Input('my-daq-startbutton', 'n_clicks')],
                [State('power-button', 'on'),
                State('dropdown-menu', 'value')])
def change_status_on(N, on, resource):
    color = ["#00cc96", '#FF6633']
    label = 'Start'
    if on is None:
        return label, color[1], True
    if on is False:
        return label, color[1], True
    
    status = calc_status(N + 1) and on
    try:
        if status is True:
            print('INFO: Measurement started...')
            gs.CONFIG_STATUS =  False
            gs.MEASUREMENT_ON =  True
            gs.set_configuration('resource1', resource)
            thread = Thread(target = ivl_setup_cc, args = gs.get_configuration())
            thread.daemon = True
            thread.start()
            label = 'Stop'
        elif status is False:
            print('INFO: Instrument configured and ready!')
            gs.MEASUREMENT_ON =  False
            label = 'Start'
        else:
            pass
        
        return label, color[int(not status)], not status

    except Exception as e:
         print('ERROR: An error occured in starting the instrument')
         print(e)
         return label, color[1], True
     
@app.callback([Output('power-button', 'label'),
               Output('my-daq-startbutton', 'disabled'),
               Output('my-daq-startbutton', 'n_clicks')],
        [Input('power-button', 'on')],
         [State('dropdown-menu', 'value'),
          State('my-daq-startbutton', 'n_clicks')])
def start_instrument(on, resource, N):
    if on is None:
        return ['Power off'], True, 0
    try:
        if on:
            label = 'Power ON'
            gs.CONFIG_STATUS =  True
            gs.set_configuration('resource1', resource)
            ivl_setup_cc(*gs.get_configuration())
            sleep(0.5)
            return [label], False, N
        else:
            gs.MEASUREMENT_ON =  False
            gs.CONFIG_STATUS =  True
            print('INFO: Instrument is off')
            label = 'Power OFF'
            return [label], True, 0
    except Exception as e:
        print('ERROR: An error occured in starting the instrument')
        print(e)
        return ['ERROR'], True
    
@app.callback([Output('current-input', 'label')],
        [Input('current-input', 'value')])
def set_current(value):
    gs.SET_CURRENT = value
    print(f'INFO: Setting the current to: {gs.SET_CURRENT:.4g} mA')
    gs.set_configuration('current', value)
    label = f'Current input is {value:4.2f} mA'
    return [label]
@app.callback([Output('folder-html', 'children')],
        [Input('folder-input', 'value')])
def set_folder(value):
    gs.set_configuration('folder', value)
    children = f'Folder name is:  {value}'
    return [children]
@app.callback([Output('filename-html', 'children')],
        [Input('filename-input', 'value')])
def set_filename(value):
    gs.set_configuration('fname', value)
    children = f'Filename name is:  {value}'
    return [children]

#def open_browser(PORT):
#	webbrowser.open_new("http://127.0.0.1:{}/".format(PORT))

if __name__ == '__main__':
#    Timer(1, open_browser, args = (PORT,)).start();
    app.run_server(debug=True, port = PORT)
    