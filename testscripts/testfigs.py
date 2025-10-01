import base64
import datetime
import io
import string

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.exceptions import PreventUpdate

import plotly.graph_objects as go
import plotly.express as px

import pandas as pd

import trompy as tp


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
       
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=False
    ),
    dcc.Dropdown(id='input-file-type',
                 options=[
                     {'label': 'Med Associates', 'value': 'med'},
                     {'label': 'DD Lab', 'value': 'dd'}],
                 value='med',
                     ),
    
    html.H1(id='filename', children='Hello Dash'),
    
    dcc.Graph(id='session-fig'),
    
    dcc.Graph(id='burst-graphs'),

    # dcc.Store inside the app that stores the intermediate value
    dcc.Store(id='lick-data')
    
])

def parse_medfile(f):
    
    sessionToExtract=1

    f.seek(0)
    filerows = f.readlines()[8:]
    datarows = [tp.isnumeric(x) for x in filerows]
    matches = [i for i,x in enumerate(datarows) if x == 0.3]
    if sessionToExtract > len(matches):
        print('Session ' + str(sessionToExtract) + ' does not exist.')
    
    varstart = matches[sessionToExtract - 1]    
    medvars = {}
   
    k = int(varstart + 27)
    for i in range(26):
        medvarsN = int(datarows[varstart + i + 1])
        if medvarsN > 1:
            medvars[string.ascii_uppercase[i]] = datarows[k:k + int(medvarsN)]
        k = k + medvarsN

    for val in medvars.values():
        val.pop(0)

    return medvars


@app.callback(Output('lick-data', 'data'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'),
              State('input-file-type', 'value'))
def load_and_clean_data(list_of_contents, list_of_names, list_of_dates, input_file_type):
    if list_of_contents is None:
        raise PreventUpdate
    else:
        content_type, content_string = list_of_contents.split(',')
        decoded = base64.b64decode(content_string)
        f = io.StringIO(decoded.decode('utf-8'))
        
        if input_file_type == 'med':
            data = parse_medfile(f)
            # Need to get all med arrays and assign properly, deal with offset licks etc
            df = pd.DataFrame(data["E"])
        
        jsonified_df = df.to_json(orient='split')
            
        return jsonified_df

@app.callback(Output('session-fig', 'figure'),
              Output('filename', 'children'),
              Input('lick-data', 'data'))
def make_session_graph(jsonified_df):
    
    df = pd.read_json(jsonified_df, orient='split')
    lickdata = tp.lickCalc(df[0].to_list())
    
    fig = px.histogram(df)

    fig.update_layout(transition_duration=500)
    
    print("is this working")
    return fig, "hey there"

@app.callback(Output('burst-graphs', 'figure'),
              Input('lick-data', 'data'))
def make_burst_graphs(jsonified_df):
    df = pd.read_json(jsonified_df, orient='split')
    lickdata = tp.lickCalc(df[0].to_list())
    print("To do")
    
    # make subplots???
    
    fig = px.histogram(lickdata["bLicks"])
    
    return fig
    

    

if __name__ == '__main__':
#    app.run_server(debug=True, dev_tools_hot_reload=False)
    app.run_server(debug=True)
