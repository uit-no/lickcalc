import base64
import io
import json
import logging

import dash
from dash import dcc, html, dash_table, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

import plotly.graph_objects as go
import plotly.express as px

import pandas as pd
import numpy as np

from helperfx import parse_medfile, parse_csvfile, parse_ddfile
from trompy import lickCalc

from tooltips import (get_binsize_tooltip, get_ibi_tooltip, get_minlicks_tooltip, 
                     get_longlick_tooltip, get_table_tooltips, get_onset_tooltip, get_offset_tooltip, get_session_length_tooltip)
from config_manager import config

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Set to WARNING to reduce noise in production
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        # logging.FileHandler('lickcalc.log')  # Uncomment to log to file
    ]
)

# Get app configuration
app_config = config.get_app_config()
app = dash.Dash(__name__, title=app_config['title'], prevent_initial_callbacks=True)

# Get table cells and tooltips
table_cells, table_tooltips = get_table_tooltips()

app.layout = dbc.Container([
    dcc.Store(id='lick-data'),
    dcc.Store(id='data-store'),
    dcc.Store(id='figure-data-store'),  # Store for figure underlying data
    dcc.Store(id='filename-store'),  # Store for uploaded filename
    dcc.Store(id='session-duration-store'),  # Store for total session duration
    html.Div(
    [
        # Help button positioned at top right of entire page
        html.A(
            "📖 Help", 
            href="/help", 
            target="_blank",
            className="btn btn-info btn-sm",
            style={
                "position": "fixed", 
                "top": "10px", 
                "right": "10px",
                "z-index": "9999",
                "text-decoration": "none"
            }
        ),
        
        dbc.Row(children=[
            dbc.Col(html.H1("lickcalc"), width=12),
        ]),
        dbc.Row(
            dbc.Col(html.Div(
                '''
                    This app lets you load in timestamps of licks from behavioral
                    experiments in rodents and performs microstructure analysis
                    on it.
                '''
                             ), width="auto")
        ),
        
        # Add spacing between description and controls
        html.Div(style={'margin-top': '20px'}),
        
        dbc.Row(children=[
                
            dbc.Col([
                html.Div(id='filetypeLbl', children="File type"),
            ], width=1),
            dbc.Col([
                dcc.Dropdown(id='input-file-type',
                              options=[
                                  {'label': 'Med Associates', 'value': 'med'},
                                  {'label': 'CSV/TXT', 'value': 'csv'},
                                  {'label': 'DD Lab', 'value': 'dd'}],
                              value=config.get('files.default_file_type', 'med')),
            ], width=2),
            dbc.Col([
                html.Div(id='fileloadLbl', children="No file loaded yet"),
            ], width=3),
            
            dbc.Col([
                get_onset_tooltip()[0],
                get_onset_tooltip()[1],
            ], width=1),
            
            dbc.Col([
                dcc.Dropdown(id='onset-array',
                             options=[
                                 {'label': 'No file loaded', 'value': 'none'}],
                             value='none',
                             placeholder="Select onset column..."),
            ], width=2),

            dbc.Col([
                get_offset_tooltip()[0],
                get_offset_tooltip()[1],
            ], width=1),
            
            dbc.Col([
                dcc.Dropdown(id='offset-array',
                             options=[
                                 {'label': 'No file loaded', 'value': 'none'}],
                             value='none',
                             placeholder="Select offset column..."),
            ], width=2),
          
          ]),
        dbc.Row(
            dbc.Col(
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
                ))),
        
        # Data validation status display
        dbc.Row([
            dbc.Col([
                html.Div(id='validation-status', style={'margin': '10px 0'})
            ], width=12)
        ]),
        
        dbc.Row(
            dbc.Col(
                dcc.Graph(id='session-fig'))),
        dbc.Row(children=[
            dbc.Col([
                html.Label("Plot Type:", style={'font-weight': 'bold', 'margin-bottom': '5px'}),
                dcc.RadioItems(
                    id='session-fig-type',
                    options=[
                        {"label": "Standard histogram", "value": "hist"},
                        {"label": "Cumulative plot", "value": "cumul"}],
                    value=config.get('session.fig_type', 'hist'))
                ], width=3),
            dbc.Col([
                get_session_length_tooltip()[0],
                dbc.Input(
                    id='session-length-input',
                    type='number',
                    value=config.get('session.length', 3600) if config.get('session.length', 'auto') != 'auto' else 3600,
                    min=1,
                    step=1,
                    placeholder="Session duration in seconds",
                    style={'width': '100%'}
                )
            ], width=2),
            get_session_length_tooltip()[1],
            dbc.Col(get_binsize_tooltip()[0], width=2),
            get_binsize_tooltip()[1],
            dbc.Col(
                dcc.Slider(
                    id='session-bin-slider',
                    **config.get_slider_config('session_bin')),
                width=4),
            ]),
        
        # Add spacing before microstructural analysis section
        dbc.Row(dbc.Col(html.Hr(), width=12), style={'margin-top': '30px'}),  # Separator line
        dbc.Row(dbc.Col(html.H2("Microstructural analysis"), width='auto')),
        
        # Controls for microstructural analysis
        dbc.Row(children=[
            dbc.Col([
                get_ibi_tooltip()[0],
                get_ibi_tooltip()[1],
                dcc.Slider(id='interburst-slider',              
                    **config.get_slider_config('interburst'))
            ], width=4),
            dbc.Col([
                get_minlicks_tooltip()[0],
                get_minlicks_tooltip()[1],
                dcc.Slider(id='minlicks-slider',
                          **config.get_slider_config('minlicks'))
            ], width=4),
            dbc.Col([
                get_longlick_tooltip()[0],
                get_longlick_tooltip()[1],
                dcc.Slider(
                    id='longlick-threshold',
                    **config.get_slider_config('longlick'))
            ], width=4),
        ], style={'margin-bottom': '20px'}),
        
        dbc.Row(children=[
            dbc.Col(
                dcc.Graph(id='intraburst-fig'),
                width=4),
            dbc.Col(
                dcc.Graph(id='longlicks-fig'),
                width=4),
            dbc.Col([
                dbc.Table([
                    html.Tr([html.Th("Property"), html.Th("Value")]),
                    html.Tr([table_cells[0], html.Td(id="total-licks")]),  # Total licks
                    html.Tr([table_cells[1], html.Td(id="intraburst-freq")]),  # Intraburst frequency
                    html.Tr([table_cells[2], html.Td(id="nlonglicks")]),  # No. of long licks
                    html.Tr([html.Td("Maximum long lick"), html.Td(id="longlicks-max")]),
                    ],
                    striped=True, hover=True, bordered=True),
                # Add tooltips
                table_tooltips[0],  # Total licks tooltip
                table_tooltips[1],  # Intraburst frequency tooltip
                table_tooltips[2],  # No. of long licks tooltip
            ], width=4),
    ]),
        
        dbc.Row(children=[
            dbc.Col(
                dcc.Graph(id='bursthist-fig'),
                width=4),
            dbc.Col(
                dcc.Graph(id='burstprob-fig'),
                width=4),
            dbc.Col([
                dbc.Table([
                    html.Tr([html.Th("Property"), html.Th("Value")]),
                    html.Tr([html.Td("No. of bursts"), html.Td(id="nbursts")]),
                    html.Tr([table_cells[3], html.Td(id="licks-per-burst")]),  # Mean licks per burst
                    html.Tr([table_cells[4], html.Td(id="weibull-alpha")]),  # Weibull: Alpha
                    html.Tr([table_cells[5], html.Td(id="weibull-beta")]),  # Weibull: Beta
                    html.Tr([table_cells[6], html.Td(id="weibull-rsq")]),  # Weibull: r-squared
                    ],
                    striped=True, hover=True, bordered=True),
                # Add tooltips
                table_tooltips[3],  # Mean licks per burst tooltip
                table_tooltips[4],  # Weibull: Alpha tooltip
                table_tooltips[5],  # Weibull: Beta tooltip
                table_tooltips[6],  # Weibull: r-squared tooltip
            ], width=4),
            
            ]),
        
        # Data Output Section
        dbc.Row(dbc.Col(html.Hr(), width=12), style={'margin-top': '30px'}),  # Separator line
        dbc.Row(dbc.Col(html.H2("Data Output"), width='auto')),
        
        dbc.Row(children=[
            # Animal ID input
            dbc.Col([
                html.Label("Animal ID:", style={'font-weight': 'bold'}),
                dcc.Input(
                    id='animal-id-input',
                    type='text',
                    value=config.get('output.default_animal_id', 'ID1'),
                    placeholder='Enter animal ID...',
                    style={'width': '100%', 'margin-top': '5px'}
                )
            ], width=2),
            
            # Data selection checkboxes
            dbc.Col([
                html.Label("Include in Excel Export:", style={'font-weight': 'bold'}),
                dbc.Checklist(
                    id='export-data-checklist',
                    options=[
                        {'label': 'Session Histogram Data', 'value': 'session_hist'},
                        {'label': 'Intraburst Frequency Data', 'value': 'intraburst_freq'},
                        {'label': 'Lick Lengths Data', 'value': 'lick_lengths'},
                        {'label': 'Burst Histogram Data', 'value': 'burst_hist'},
                        {'label': 'Burst Probability Data', 'value': 'burst_prob'},
                        {'label': 'Burst Details Data', 'value': 'burst_details'}
                    ],
                    value=['session_hist', 'intraburst_freq'],  # Default selections
                    inline=False,
                    style={'margin-top': '5px'}
                )
            ], width=4),
            
            # Output controls
            dbc.Col([
                html.Label("Export Options:", style={'font-weight': 'bold'}),
                html.Br(),
                html.Button(
                    'Export Data to Excel', 
                    id='export-btn', 
                    n_clicks=0,
                    className='btn btn-primary',
                    style={'margin-top': '10px', 'margin-right': '10px'}
                ),
                dcc.Download(id="download-excel"),
                html.Div(id='export-status', style={'margin-top': '10px'})
            ], width=3)
        ], style={'margin-bottom': '20px'}),
        
        # Results Table Section
        dbc.Row(dbc.Col(html.Hr(), width=12), style={'margin-top': '30px'}),  # Separator line
        dbc.Row(dbc.Col(html.H2("Results Summary"), width='auto')),
        
        # Division controls for temporal/burst analysis
        dbc.Row(children=[
            dbc.Col([
                html.Label("Divide Session:", style={'font-weight': 'bold'}),
                dcc.Dropdown(
                    id='division-number',
                    options=[
                        {'label': 'Whole session', 'value': 1},
                        {'label': 'Divide in 2', 'value': 2},
                        {'label': 'Divide in 3', 'value': 3},
                        {'label': 'Divide in 4', 'value': 4}
                    ],
                    value=1,
                    style={'margin-top': '5px'}
                )
            ], width=3),
            dbc.Col([
                html.Label("Division Method:", style={'font-weight': 'bold'}),
                dcc.Dropdown(
                    id='division-method',
                    options=[
                        {'label': 'By Time', 'value': 'time'},
                        {'label': 'By Burst Number', 'value': 'bursts'}
                    ],
                    value='time',
                    style={'margin-top': '5px'}
                )
            ], width=3),
        ], style={'margin-bottom': '20px'}),
        
        dbc.Row(children=[
            # Add to table button
            dbc.Col([
                html.Button(
                    'Add Current Results to Table', 
                    id='add-to-table-btn', 
                    n_clicks=0,
                    className='btn btn-success',
                    style={'margin-right': '10px'}
                ),
                html.Button(
                    'Delete Selected Row', 
                    id='delete-row-btn', 
                    n_clicks=0,
                    className='btn btn-danger',
                    style={'margin-right': '10px'}
                ),
                html.Button(
                    'Clear All Results', 
                    id='clear-all-btn', 
                    n_clicks=0,
                    className='btn btn-warning',
                    style={'margin-right': '10px'}
                ),
                html.Button(
                    'Export Selected Row', 
                    id='export-row-btn', 
                    n_clicks=0,
                    className='btn btn-info',
                    style={'margin-right': '10px'}
                ),
                html.Button(
                    'Export Full Table', 
                    id='export-table-btn', 
                    n_clicks=0,
                    className='btn btn-primary'
                ),
                dcc.Download(id="download-table"),
                html.Div(id='table-status', style={'margin-top': '10px'})
            ], width=12)
        ], style={'margin-bottom': '20px'}),
        
        # Results table
        dbc.Row(dbc.Col([
            dash_table.DataTable(
                id='results-table',
                columns=[
                    {'name': 'ID', 'id': 'id', 'type': 'text', 'editable': True},
                    {'name': 'Source File', 'id': 'source_filename', 'type': 'text', 'editable': False},
                    {'name': 'Start Time (s)', 'id': 'start_time', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                    {'name': 'End Time (s)', 'id': 'end_time', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                    {'name': 'Duration (s)', 'id': 'duration', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                    {'name': 'Total Licks', 'id': 'total_licks', 'type': 'numeric', 'format': {'specifier': '.0f'}},
                    {'name': 'Intraburst Freq (Hz)', 'id': 'intraburst_freq', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                    {'name': 'N Bursts', 'id': 'n_bursts', 'type': 'numeric', 'format': {'specifier': '.0f'}},
                    {'name': 'Mean Licks/Burst', 'id': 'mean_licks_per_burst', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                    {'name': 'Weibull Alpha', 'id': 'weibull_alpha', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                    {'name': 'Weibull Beta', 'id': 'weibull_beta', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                    {'name': 'Weibull R²', 'id': 'weibull_rsq', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                    {'name': 'N Long Licks', 'id': 'n_long_licks', 'type': 'numeric', 'format': {'specifier': '.0f'}},
                    {'name': 'Max Lick Duration (s)', 'id': 'max_lick_duration', 'type': 'numeric', 'format': {'specifier': '.4f'}}
                ],
                data=[],
                editable=True,
                row_selectable='single',
                selected_rows=[],
                style_cell={
                    'textAlign': 'center',
                    'padding': '12px',
                    'fontFamily': 'Arial',
                    'fontSize': '12px',
                    'minHeight': '40px'
                },
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold',
                    'height': '50px'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    },
                    {
                        'if': {'filter_query': '{id} contains "Sum"'},
                        'backgroundColor': '#f0f8e6',
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {'filter_query': '{id} contains "Mean"'},
                        'backgroundColor': '#e6f3ff',
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {'filter_query': '{id} contains "SD"'},
                        'backgroundColor': '#ffe6e6',
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {'filter_query': '{id} contains "SE"'},
                        'backgroundColor': '#e6ffe6',
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {'filter_query': '{id} contains "N"'},
                        'backgroundColor': '#fff2e6',
                        'fontWeight': 'bold'
                    }
                ],
                style_table={
                    'overflowX': 'auto',
                    'minHeight': '300px',
                    'border': '1px solid #dee2e6',
                    'borderRadius': '5px'
                },
                page_size=20,  # Show more rows to prevent cut-off appearance
                fill_width=True
            )
        ], width=12)),
        
        # Add some buffer space below the table
        dbc.Row(dbc.Col(html.Div(style={'height': '50px'}), width=12)),
        
        # Store for results table data
        dcc.Store(id='results-table-store', data=[]),
        
        
])])

# Flask route to serve help file
@app.server.route('/help')
def serve_help():
    """Serve the help documentation page"""
    from flask import send_from_directory
    return send_from_directory('assets', 'help.html')
    
@app.callback(Output('data-store', 'data'),
              Output('fileloadLbl', 'children'),
              Output('onset-array', 'options'),
              Output('onset-array', 'value'),
              Output('offset-array', 'options'),
              Output('offset-array', 'value'),
              Output('filename-store', 'data'),
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
            data_array = parse_medfile(f)
        elif input_file_type == 'csv':
            data_array = parse_csvfile(f)
        elif input_file_type == 'dd':
            data_array = parse_ddfile(f)
        
        # Create options for dropdowns
        column_names = list(data_array.keys())
        
        # For onset array, include all columns
        onset_options = [{'label': key, 'value': key} for key in column_names]
        
        # For offset array, include all columns plus "None" option
        offset_options = [{'label': 'None (onset only)', 'value': 'none'}] + [{'label': key, 'value': key} for key in column_names]
        
        # Set default values
        if len(column_names) > 0:
            # Try to find common column names for onsets
            onset_default = None
            for potential_name in ['licks', 'onset', 'timestamps', 'time', 'Col. 1', column_names[0]]:
                if potential_name in column_names:
                    onset_default = potential_name
                    break
            if onset_default is None:
                onset_default = column_names[0]
            
            # Try to find common column names for offsets
            offset_default = 'none'
            for potential_name in ['offset', 'offsets', 'end', 'stop', 'Col. 2']:
                if potential_name in column_names:
                    offset_default = potential_name
                    break
        else:
            onset_default = 'none'
            offset_default = 'none'
        
        jsonified_dict = json.dumps(data_array)
        
        file_info = f"Loaded: {list_of_names} ({len(column_names)} columns)"
            
        return jsonified_dict, file_info, onset_options, onset_default, offset_options, offset_default, list_of_names

# Callback to validate onset/offset data and display status
@app.callback(Output('validation-status', 'children'),
              Input('data-store', 'data'),
              Input('onset-array', 'value'),
              Input('offset-array', 'value'),
              prevent_initial_call=True)
def update_validation_status(data_store, onset_key, offset_key):
    """Display validation status for onset/offset data"""
    if not data_store or not onset_key or onset_key == 'none':
        return ""
    
    if not offset_key or offset_key == 'none':
        return dbc.Alert(
            "ℹ️ Onset-only data loaded (no offset column selected). Lick duration analysis will not be available.",
            color="info",
            dismissable=True
        )
    
    try:
        data_array = json.loads(data_store)
        
        if onset_key not in data_array or offset_key not in data_array:
            return ""
        
        # Get the data
        onset_df = pd.read_json(io.StringIO(data_array[onset_key]), orient='split')
        offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
        
        onset_times = onset_df["licks"].to_list()
        offset_times = offset_df["licks"].to_list()
        
        # Validate the data
        validation = validate_onset_offset_pairs(onset_times, offset_times)
        
        if validation['valid']:
            if "Warning" in validation['message']:
                return dbc.Alert(
                    f"⚠️ Data loaded with warnings: {validation['message']}",
                    color="warning",
                    dismissable=True
                )
            else:
                return dbc.Alert(
                    f"✅ Data validation successful: {validation['message']}",
                    color="success",
                    dismissable=True
                )
        else:
            return dbc.Alert(
                f"❌ Data validation failed: {validation['message']}",
                color="danger",
                dismissable=True
            )
            
    except Exception as e:
        return dbc.Alert(
            f"❌ Error during validation: {str(e)}",
            color="danger",
            dismissable=True
        )

@app.callback(Output('lick-data', 'data'),
              Output('session-duration-store', 'data'),
              Input('data-store', 'data'),
              Input('onset-array', 'value'))
def get_lick_data(jsonified_dict, df_key):
    if jsonified_dict is None:
        raise PreventUpdate
    
    data_array = json.loads(jsonified_dict)
    jsonified_df = data_array[df_key]
    
    # Get session duration
    df = pd.read_json(io.StringIO(jsonified_df), orient='split')
    session_duration = max(df["licks"]) if len(df) > 0 else 3600  # Default to 1 hour if no data

    return jsonified_df, session_duration

@app.callback(Output('session-fig', 'figure'),
              Input('lick-data', 'data'),
              Input('session-fig-type', 'value'),
              Input('session-bin-slider', 'value'),
              Input('session-length-input', 'value'))
def make_session_graph(jsonified_df, figtype, binsize, session_length):
    
    if jsonified_df is None:
        raise PreventUpdate
    else:
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        lastlick = max(df["licks"]) if len(df) > 0 else 0
        
        # Use custom session length if provided, otherwise use last lick time
        plot_duration = session_length if session_length and session_length > 0 else lastlick
        
        if figtype == "hist":
            fig = px.histogram(df,
                            x="licks",
                            range_x=[0, plot_duration],
                            nbins=int(plot_duration/binsize) if plot_duration > 0 else 1)
        
            fig.update_layout(
                transition_duration=500,
                xaxis_title="Time (s)",
                yaxis_title="Licks per {} s".format(binsize),
                showlegend=False)
        else:
            fig = px.line(x=df["licks"], y=range(0, len(df["licks"])))
            
            fig.update_layout(
                transition_duration=500,
                xaxis_title="Time (s)",
                yaxis_title="Cumulative licks",
                showlegend=False,
                xaxis=dict(range=[0, plot_duration]))

        return fig

@app.callback(Output('session-length-input', 'value'),
              Input('lick-data', 'data'),
              prevent_initial_call=True)
def update_session_length_suggestion(jsonified_df):
    """Auto-populate session length input based on config and data"""
    if jsonified_df is None:
        raise PreventUpdate
    
    # Check config for session length setting
    session_length_config = config.get('session.length', 'auto')
    
    # If config specifies a fixed value, use it
    if session_length_config != 'auto':
        try:
            # Try to convert config value to number
            return int(session_length_config)
        except (ValueError, TypeError):
            # If config value is invalid, fall back to auto
            pass
    
    # Auto-detect from data
    df = pd.read_json(io.StringIO(jsonified_df), orient='split')
    if len(df) > 0:
        last_lick = max(df["licks"])
        # Round up to nearest minute for convenience
        suggested_length = int((last_lick // 60 + 1) * 60)
        return suggested_length
    else:
        return 3600  # Default to 1 hour

@app.callback(Output('intraburst-fig', 'figure'),
              Output('total-licks', 'children'),
              Output('intraburst-freq', 'children'),
              Input('lick-data', 'data'))
def make_intraburstfreq_graph(jsonified_df):
    if jsonified_df is None:
        raise PreventUpdate
    else:        
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        
        if len(df) == 0:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(title="No data available")
            return fig, "0", "0.00 Hz"
        
        lickdata = lickCalc(df["licks"].to_list())
 
        ilis = lickdata["ilis"]

        fig = px.histogram(ilis,
                        range_x=[0, 0.5],
                        nbins=50)
    
        fig.update_layout(
            transition_duration=500,
            title="Intraburst lick frequency",
            xaxis_title="Interlick interval (s)",
            yaxis_title="Frequency",
            showlegend=False,
            # margin=dict(l=20, r=20, t=20, b=20),
            )
        
        nlicks = "{}".format(lickdata['total'])
        freq = "{:.2f} Hz".format(lickdata['freq'])
        
        return fig, nlicks, freq

# Helper function for onset/offset validation
def validate_onset_offset_pairs(onset_times, offset_times):
    """
    Validate that onset and offset times form proper lick pairs.
    
    Returns:
        dict: Contains 'valid', 'message', 'corrected_onset', 'corrected_offset'
    """
    if not onset_times or not offset_times:
        return {
            'valid': False,
            'message': "Empty onset or offset data",
            'corrected_onset': onset_times,
            'corrected_offset': offset_times
        }
    
    original_onset_len = len(onset_times)
    original_offset_len = len(offset_times)
    
    # Make copies for potential correction
    corrected_onset = onset_times.copy()
    corrected_offset = offset_times.copy()
    
    # Handle length mismatches first
    if abs(len(corrected_onset) - len(corrected_offset)) > 1:
        return {
            'valid': False,
            'message': f"Severe length mismatch: {original_onset_len} onsets vs {original_offset_len} offsets. Arrays differ by more than 1.",
            'corrected_onset': corrected_onset,
            'corrected_offset': corrected_offset
        }
    
    # Handle length difference of 1
    if len(corrected_onset) - len(corrected_offset) == 1:
        # One more onset than offset - remove last onset
        corrected_onset = corrected_onset[:-1]
    elif len(corrected_offset) - len(corrected_onset) == 1:
        # One more offset than onset - remove last offset
        corrected_offset = corrected_offset[:-1]
    
    # Now check temporal order
    warnings = []
    errors = []
    
    for i in range(len(corrected_onset)):
        onset_time = corrected_onset[i]
        offset_time = corrected_offset[i]
        
        # Check if offset comes after onset
        if offset_time <= onset_time:
            errors.append(f"Pair {i+1}: Offset ({offset_time:.3f}s) is not after onset ({onset_time:.3f}s)")
        
        # Check if this offset comes before next onset (no overlap)
        if i < len(corrected_onset) - 1:
            next_onset = corrected_onset[i + 1]
            if offset_time >= next_onset:
                warnings.append(f"Pair {i+1}: Offset ({offset_time:.3f}s) occurs after or at next onset ({next_onset:.3f}s)")
    
    # Determine overall validity
    if errors:
        return {
            'valid': False,
            'message': f"Temporal order errors found: {'; '.join(errors[:3])}{'...' if len(errors) > 3 else ''}",
            'corrected_onset': corrected_onset,
            'corrected_offset': corrected_offset
        }
    elif warnings:
        return {
            'valid': True,
            'message': f"Warning - overlapping licks detected: {'; '.join(warnings[:2])}{'...' if len(warnings) > 2 else ''}",
            'corrected_onset': corrected_onset,
            'corrected_offset': corrected_offset
        }
    else:
        length_msg = ""
        if original_onset_len != len(corrected_onset):
            length_msg = f" (adjusted from {original_onset_len} to {len(corrected_onset)} onsets)"
        elif original_offset_len != len(corrected_offset):
            length_msg = f" (adjusted from {original_offset_len} to {len(corrected_offset)} offsets)"
            
        return {
            'valid': True,
            'message': f"Valid onset/offset pairs{length_msg}",
            'corrected_onset': corrected_onset,
            'corrected_offset': corrected_offset
        }

@app.callback(Output('longlicks-fig', 'figure'),
              Output('nlonglicks', 'children'),
              Output('longlicks-max', 'children'),
              Input('offset-array', 'value'),
              Input('longlick-threshold', 'value'),
              State('data-store', 'data'),
              State('lick-data', 'data'),)
def make_longlicks_graph(offset_key, longlick_th, jsonified_dict, jsonified_df):
    if jsonified_df is None:
        raise PreventUpdate
    
    # Check if offset data is available
    if offset_key is None or offset_key == 'none':
        # Return empty figure when no offset data is available
        fig = go.Figure()
        fig.update_layout(
            title="Lick Duration Analysis",
            xaxis_title="Lick length (s)",
            yaxis_title="Frequency",
            annotations=[
                dict(
                    text="Offset data required for lick duration analysis",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, xanchor='center', yanchor='middle',
                    showarrow=False,
                    font=dict(size=14, color="gray")
                )
            ]
        )
        return fig, "N/A", "N/A"
    
    try:        
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        
        data_array = json.loads(jsonified_dict)
        
        # Check if the offset key exists in the data
        if offset_key not in data_array:
            fig = go.Figure()
            fig.update_layout(
                title="Lick Duration Analysis",
                annotations=[
                    dict(
                        text=f"Offset column '{offset_key}' not found in data",
                        xref="paper", yref="paper",
                        x=0.5, y=0.5, xanchor='center', yanchor='middle',
                        showarrow=False,
                        font=dict(size=14, color="red")
                    )
                ]
            )
            return fig, "N/A", "N/A"
        
        offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
        
        if len(df) == 0:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(title="No data available")
            return fig, "0", "0.00"
        
        onset=df["licks"].to_list()
        offset=offset_df["licks"].to_list()
        
        # Validate onset/offset pairs
        validation = validate_onset_offset_pairs(onset, offset)
        
        if not validation['valid']:
            # Show error for invalid data
            logging.error(f"Onset/offset validation failed: {validation['message']}")
            fig = go.Figure()
            fig.update_layout(
                title="Lick Duration Analysis - Data Validation Error",
                annotations=[
                    dict(
                        text=f"Data validation error: {validation['message']}",
                        xref="paper", yref="paper",
                        x=0.5, y=0.5, xanchor='center', yanchor='middle',
                        showarrow=False,
                        font=dict(size=12, color="red")
                    )
                ]
            )
            return fig, "Error", "Error"
        
        # Use corrected arrays
        onset = validation['corrected_onset']
        offset = validation['corrected_offset']
        
        # Log validation message (could be warning about overlaps)
        if "Warning" in validation['message']:
            logging.warning(f"Onset/offset validation: {validation['message']}")
        else:
            logging.info(f"Onset/offset validation: {validation['message']}")
        
        lickdata = lickCalc(onset, offset=offset, longlickThreshold=longlick_th)
        licklength = lickdata["licklength"]
        
        if len(licklength) == 0:
            fig = go.Figure()
            fig.update_layout(title="No lick length data available")
            return fig, "0", "0.00"
        
        counts, bins = np.histogram(licklength, bins=np.arange(0, longlick_th, 0.01))
        bins = 0.5 * (bins[:-1] + bins[1:])
        
        fig = px.bar(x=bins, y=counts)
    
        fig.update_layout(
            transition_duration=500,
            title="Lick lengths",
            xaxis_title="Lick length (s)",
            yaxis_title="Frequency",
            showlegend=False,
            # margin=dict(l=20, r=20, t=20, b=20),
            )
        
        nlonglicks = "{}".format(len(lickdata["longlicks"]))
        longlick_max = "{:.2f}".format(np.max(licklength)) if len(licklength) > 0 else "0.00"
        
        return fig, nlonglicks, longlick_max
        
    except Exception as e:
        logging.error(f"Error in longlicks callback: {e}")
        fig = go.Figure()
        fig.update_layout(
            title="Lick Duration Analysis - Error",
            annotations=[
                dict(
                    text=f"Error processing lick duration data: {str(e)}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, xanchor='center', yanchor='middle',
                    showarrow=False,
                    font=dict(size=12, color="red")
                )
            ]
        )
        return fig, "Error", "Error"

@app.callback(Output('bursthist-fig', 'figure'),
              Input('lick-data', 'data'),
              Input('interburst-slider', 'value'),
              Input('minlicks-slider', 'value'))
def make_bursthist_graph(jsonified_df, ibi, minlicks):
    if jsonified_df is None:
        raise PreventUpdate
    else:
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        
        if len(df) == 0:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(title="No data available")
            return fig
        
        lickdata = lickCalc(df["licks"].to_list(), burstThreshold=ibi, minburstlength=minlicks)
    
        bursts=lickdata['bLicks']
        
        if len(bursts) == 0:
            fig = go.Figure()
            fig.update_layout(title="No bursts found with current parameters")
            return fig

        fig = px.histogram(bursts,
                            range_x=[1, max(bursts)],
                            nbins=int(np.max(bursts)))
        
        # fig.update_traces(mode='markers', marker_line_width=2, marker_size=10)
        
        fig.update_layout(
            transition_duration=500,
            title="Burst frequency histogram",
            xaxis_title="Frequency",
            yaxis_title="Burst size",
            showlegend=False)

        return fig

@app.callback(Output('burstprob-fig', 'figure'),
              Output('nbursts', 'children'),
              Output('licks-per-burst', 'children'),
              Output('weibull-alpha', 'children'),
              Output('weibull-beta', 'children'),
              Output('weibull-rsq', 'children'),
              Input('lick-data', 'data'),
              Input('interburst-slider', 'value'),
              Input('minlicks-slider', 'value'))
def make_burstprob_graph(jsonified_df, ibi, minlicks):
    if jsonified_df is None:
        raise PreventUpdate
    else:
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        
        if len(df) == 0:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(title="No data available")
            return fig, "0", "0.00", "0.00", "0.00", "0.00"
        
        lickdata = lickCalc(df["licks"].to_list(), burstThreshold=ibi, minburstlength=minlicks)
    
        if len(lickdata['burstprob'][0]) == 0:
            fig = go.Figure()
            fig.update_layout(title="No bursts found with current parameters")
            return fig, "0", "0.00", "0.00", "0.00", "0.00"
        
        x=lickdata['burstprob'][0]
        y=lickdata['burstprob'][1]

        fig = px.scatter(x=x,y=y)
        
        fig.update_traces(mode='markers', marker_line_width=2, marker_size=10)
        
        fig.update_layout(
            title="Weibull probability plot",
            xaxis_title="Burst size (n)",
            yaxis_title="Probability of burst>n",
            showlegend=False)

        bNum = "{}".format(lickdata['bNum'])
        bMean = "{:.2f}".format(lickdata['bMean'])      
        alpha = "{:.2f}".format(lickdata['weib_alpha'])
        beta = "{:.2f}".format(lickdata['weib_beta'])
        rsq = "{:.2f}".format(lickdata['weib_rsq'])


        return fig , bNum, bMean, alpha, beta, rsq

# Data collection callback to store figure data for export
@app.callback(Output('figure-data-store', 'data'),
              Input('lick-data', 'data'),
              Input('session-bin-slider', 'value'),
              Input('interburst-slider', 'value'),
              Input('minlicks-slider', 'value'),
              Input('longlick-threshold', 'value'),
              Input('session-length-input', 'value'),
              State('data-store', 'data'),
              State('offset-array', 'value'))
def collect_figure_data(jsonified_df, bin_size, ibi, minlicks, longlick_th, session_length, jsonified_dict, offset_key):
    """Collect underlying data from all figures for export"""
    if jsonified_df is None:
        raise PreventUpdate
    
    figure_data = {}
    
    try:
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        
        if len(df) == 0:
            # Return minimal data if no licks
            figure_data['summary_stats'] = {
                'total_licks': 0,
                'intraburst_freq': 0,
                'n_bursts': 0,
                'mean_licks_per_burst': 0,
                'weibull_alpha': 0,
                'weibull_beta': 0,
                'weibull_rsq': 0,
                'n_long_licks': 0,
                'max_lick_duration': 0
            }
            return figure_data
        
        lick_times = df["licks"].to_list()
        
        if not lick_times:  # If no licks in data
            figure_data['summary_stats'] = {
                'total_licks': 0,
                'intraburst_freq': 0,
                'n_bursts': 0,
                'mean_licks_per_burst': 0,
                'weibull_alpha': 0,
                'weibull_beta': 0,
                'weibull_rsq': 0,
                'n_long_licks': 0,
                'max_lick_duration': 0
            }
            return figure_data
        
        # Session histogram data (use session_length for display range if specified)
        max_time = session_length if session_length and session_length > 0 else max(lick_times)
        hist_counts, hist_edges = np.histogram(lick_times, bins=int(max_time/bin_size) if max_time > 0 else 1, range=(0, max_time))
        hist_centers = (hist_edges[:-1] + hist_edges[1:]) / 2
        figure_data['session_hist'] = {
            'bin_centers': hist_centers.tolist(),
            'counts': hist_counts.tolist(),
            'bin_size_seconds': bin_size
        }
        
        # Intraburst frequency data (ILIs)
        lickdata = lickCalc(lick_times)
        ilis = lickdata["ilis"]
        ili_counts, ili_edges = np.histogram(ilis, bins=50, range=(0, 0.5))
        ili_centers = (ili_edges[:-1] + ili_edges[1:]) / 2
        figure_data['intraburst_freq'] = {
            'ili_centers': ili_centers.tolist(),
            'counts': ili_counts.tolist(),
            'raw_ilis': ilis
        }
        
        # Initialize lick lengths data as None
        figure_data['lick_lengths'] = None
        
        # Burst data
        burst_lickdata = lickCalc(lick_times, burstThreshold=ibi, minburstlength=minlicks)
        bursts = burst_lickdata['bLicks']
        
        # Burst histogram data
        burst_counts, burst_edges = np.histogram(bursts, bins=int(np.max(bursts)), range=(1, max(bursts)))
        burst_centers = (burst_edges[:-1] + burst_edges[1:]) / 2
        figure_data['burst_hist'] = {
            'burst_sizes': burst_centers.tolist(),
            'counts': burst_counts.tolist(),
            'raw_burst_sizes': bursts
        }
        
        # Burst probability data
        x_prob, y_prob = burst_lickdata['burstprob']
        figure_data['burst_prob'] = {
            'burst_sizes': x_prob,
            'probabilities': y_prob
        }
        
        # Burst details data - individual burst information
        if burst_lickdata['bNum'] > 0:  # Only if bursts were detected
            burst_starts = burst_lickdata['bStart']
            burst_ends = burst_lickdata['bEnd']
            burst_licks = burst_lickdata['bLicks']
            
            # Calculate burst durations
            burst_durations = [end - start for start, end in zip(burst_starts, burst_ends)]
            
            figure_data['burst_details'] = {
                'burst_numbers': list(range(1, len(burst_starts) + 1)),
                'n_licks': burst_licks,
                'start_times': burst_starts,
                'end_times': burst_ends,
                'durations': burst_durations
            }
        else:
            figure_data['burst_details'] = None
        
        # Summary statistics
        figure_data['summary_stats'] = {
            'total_licks': burst_lickdata['total'],
            'intraburst_freq': burst_lickdata['freq'],
            'n_bursts': burst_lickdata['bNum'],
            'mean_licks_per_burst': burst_lickdata['bMean'],
            'weibull_alpha': burst_lickdata['weib_alpha'],
            'weibull_beta': burst_lickdata['weib_beta'],
            'weibull_rsq': burst_lickdata['weib_rsq'],
            'n_long_licks': 'N/A (requires offset data)',
            'max_lick_duration': 'N/A (requires offset data)'
        }
        
        # Process offset data if available for lick lengths and long lick statistics
        if offset_key and offset_key != 'none' and jsonified_dict:
            try:
                data_array = json.loads(jsonified_dict)
                
                # Check if the offset key exists in the data
                if offset_key not in data_array:
                    logging.warning(f"Offset key '{offset_key}' not found in data")
                    figure_data['summary_stats']['n_long_licks'] = 'N/A (offset column not found)'
                    figure_data['summary_stats']['max_lick_duration'] = 'N/A (offset column not found)'
                else:
                    offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
                    offset_times = offset_df["licks"].to_list()
                    
                    # Validate onset/offset pairs
                    validation = validate_onset_offset_pairs(lick_times, offset_times)
                    
                    if validation['valid']:
                        # Use validated/corrected arrays
                        onset_times = validation['corrected_onset']
                        offset_times = validation['corrected_offset']
                        
                        # Log validation message
                        if "Warning" in validation['message']:
                            logging.warning(f"Data export validation: {validation['message']}")
                        else:
                            logging.info(f"Data export validation: {validation['message']}")
                            
                        lickdata_with_offset = lickCalc(onset_times, offset=offset_times, longlickThreshold=longlick_th)
                        licklength = lickdata_with_offset["licklength"]
                        
                        # Create lick lengths histogram data
                        ll_counts, ll_edges = np.histogram(licklength, bins=np.arange(0, longlick_th, 0.01))
                        ll_centers = (ll_edges[:-1] + ll_edges[1:]) / 2
                        figure_data['lick_lengths'] = {
                            'duration_centers': ll_centers.tolist(),
                            'counts': ll_counts.tolist(),
                            'raw_durations': licklength,
                            'threshold': longlick_th
                        }
                        
                        # Update long lick statistics in summary
                        figure_data['summary_stats']['n_long_licks'] = len(lickdata_with_offset["longlicks"])
                        figure_data['summary_stats']['max_lick_duration'] = np.max(licklength) if len(licklength) > 0 else 0
                        
                        logging.debug(f"Calculated n_long_licks = {figure_data['summary_stats']['n_long_licks']}")
                        logging.debug(f"Calculated max_lick_duration = {figure_data['summary_stats']['max_lick_duration']}")
                    else:
                        # Validation failed - log the issue and set error status
                        logging.error(f"Onset/offset validation failed for data export: {validation['message']}")
                        figure_data['summary_stats']['n_long_licks'] = f'N/A (validation failed: {validation["message"][:50]}...)'
                        figure_data['summary_stats']['max_lick_duration'] = 'N/A (validation failed)'
                    
            except (ValueError, KeyError, TypeError) as e:
                logging.error(f"Error processing offset data: {e}")
                figure_data['summary_stats']['n_long_licks'] = 'N/A (error)'
                figure_data['summary_stats']['max_lick_duration'] = 'N/A (error)'
        
    except (ValueError, KeyError, TypeError) as e:
        logging.error(f"Error collecting figure data: {e}")
        figure_data = {}
    
    return figure_data

# Helper functions for temporal/burst division analysis
def calculate_segment_stats(segment_licks, segment_offsets, ibi, minlicks, longlick_th):
    """Calculate statistics for a segment of licks"""
    if not segment_licks:
        return {
            'total_licks': 0,
            'intraburst_freq': np.nan,
            'n_bursts': 0,
            'mean_licks_per_burst': np.nan,
            'weibull_alpha': np.nan,
            'weibull_beta': np.nan,
            'weibull_rsq': np.nan,
            'n_long_licks': np.nan,
            'max_lick_duration': np.nan
        }
    
    # Calculate basic burst statistics
    burst_lickdata = lickCalc(segment_licks, burstThreshold=ibi, minburstlength=minlicks)
    
    stats = {
        'total_licks': burst_lickdata['total'],
        'intraburst_freq': burst_lickdata['freq'],
        'n_bursts': burst_lickdata['bNum'],
        'mean_licks_per_burst': burst_lickdata['bMean'],
        'weibull_alpha': burst_lickdata['weib_alpha'],
        'weibull_beta': burst_lickdata['weib_beta'],
        'weibull_rsq': burst_lickdata['weib_rsq'],
        'n_long_licks': np.nan,
        'max_lick_duration': np.nan
    }
    
    # Calculate long lick statistics if offset data available
    if segment_offsets:
        # Validate onset/offset pairs for this segment
        validation = validate_onset_offset_pairs(segment_licks, segment_offsets)
        
        if validation['valid']:
            try:
                # Use validated arrays
                validated_onsets = validation['corrected_onset']
                validated_offsets = validation['corrected_offset']
                
                lickdata_with_offset = lickCalc(validated_onsets, offset=validated_offsets, longlickThreshold=longlick_th)
                licklength = lickdata_with_offset["licklength"]
                stats['n_long_licks'] = len(lickdata_with_offset["longlicks"])
                stats['max_lick_duration'] = np.max(licklength) if len(licklength) > 0 else np.nan
                
                # Log validation warnings for segments
                if "Warning" in validation['message']:
                    logging.debug(f"Segment validation warning: {validation['message']}")
                    
            except (ValueError, TypeError, KeyError) as e:
                logging.warning(f"Could not calculate lick durations for burst range: {e}")
        else:
            logging.warning(f"Segment onset/offset validation failed: {validation['message']}")
            # Leave as NaN to indicate validation failure
    
    return stats

def get_licks_for_burst_range(lick_times, start_burst, end_burst, ibi, minlicks):
    """Get lick times that belong to a specific range of bursts"""
    if not lick_times or start_burst >= end_burst:
        return []
    
    # Calculate bursts for the whole session first
    burst_lickdata = lickCalc(lick_times, burstThreshold=ibi, minburstlength=minlicks)
    total_bursts = burst_lickdata.get('bNum', 0)
    
    if total_bursts == 0:
        # No bursts detected, fall back to time-based division
        session_duration = lick_times[-1] - lick_times[0] if len(lick_times) > 1 else 0
        if session_duration == 0:
            return lick_times if start_burst == 0 else []
            
        # Simple time-based fallback
        start_proportion = start_burst / max(end_burst, 1)
        end_proportion = end_burst / max(end_burst, 1)
        start_time = lick_times[0] + start_proportion * session_duration
        end_time = lick_times[0] + end_proportion * session_duration
        
        return [t for t in lick_times if start_time <= t < end_time]
    
    # We have bursts - extract them properly
    # The key insight: re-run lickCalc on the full data to get clean burst boundaries
    # Then extract the licks that belong to our target burst range
    
    # Ensure valid burst range
    start_burst = max(0, min(start_burst, total_bursts))
    end_burst = max(start_burst, min(end_burst, total_bursts))
    
    if start_burst == end_burst:
        return []
    
    # Get burst start times from the burst analysis
    burst_start_times = burst_lickdata.get('bStart', [])
    burst_end_times = burst_lickdata.get('bEnd', [])
    
    if not burst_start_times or not burst_end_times:
        # Fallback to proportional time-based approach
        start_proportion = start_burst / total_bursts
        end_proportion = end_burst / total_bursts
        session_duration = lick_times[-1] - lick_times[0]
        start_time = lick_times[0] + start_proportion * session_duration
        end_time = lick_times[0] + end_proportion * session_duration
        return [t for t in lick_times if start_time <= t <= end_time]
    
    # Extract the time boundaries for our burst range
    if start_burst < len(burst_start_times):
        range_start_time = float(burst_start_times[start_burst])
    else:
        range_start_time = lick_times[0]
    
    if end_burst - 1 < len(burst_end_times):
        range_end_time = float(burst_end_times[end_burst - 1])
    else:
        range_end_time = lick_times[-1]
    
    # Return licks within this time range
    return [t for t in lick_times if range_start_time <= t <= range_end_time]

def get_offsets_for_licks(original_licks, original_offsets, segment_licks):
    """Get corresponding offset times for a segment of licks"""
    if not original_offsets or not segment_licks:
        return None
    
    # Find indices of segment licks in original lick list
    segment_indices = []
    for seg_lick in segment_licks:
        try:
            idx = original_licks.index(seg_lick)
            segment_indices.append(idx)
        except ValueError:
            continue
    
    # Return corresponding offsets
    if segment_indices and len(original_offsets) > max(segment_indices):
        return [original_offsets[i] for i in segment_indices if i < len(original_offsets)]
    
    return None

# Excel export callback
@app.callback(Output("download-excel", "data"),
              Output("export-status", "children"),
              Input('export-btn', 'n_clicks'),
              State('animal-id-input', 'value'),
              State('export-data-checklist', 'value'),
              State('figure-data-store', 'data'),
              State('filename-store', 'data'),
              prevent_initial_call=True)
def export_to_excel(n_clicks, animal_id, selected_data, figure_data, source_filename):
    """Export selected data to Excel with multiple sheets"""
    if n_clicks == 0 or not figure_data:
        raise PreventUpdate
    
    try:
        # Create Excel writer object
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lickcalc_Export_{animal_id}_{timestamp}.xlsx"
        
        # Create a BytesIO buffer
        import io
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main summary sheet
            if 'summary_stats' in figure_data:
                stats = figure_data['summary_stats']
                summary_df = pd.DataFrame([
                    ['Animal ID', animal_id],
                    ['Source Filename', source_filename if source_filename else 'N/A'],
                    ['Export Date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    ['Total Licks', stats.get('total_licks', 'N/A')],
                    ['Intraburst Frequency (Hz)', f"{stats.get('intraburst_freq', 'N/A'):.3f}" if stats.get('intraburst_freq') else 'N/A'],
                    ['Number of Bursts', stats.get('n_bursts', 'N/A')],
                    ['Mean Licks per Burst', f"{stats.get('mean_licks_per_burst', 'N/A'):.2f}" if stats.get('mean_licks_per_burst') else 'N/A'],
                    ['Weibull Alpha', f"{stats.get('weibull_alpha', 'N/A'):.3f}" if stats.get('weibull_alpha') else 'N/A'],
                    ['Weibull Beta', f"{stats.get('weibull_beta', 'N/A'):.3f}" if stats.get('weibull_beta') else 'N/A'],
                    ['Weibull R-squared', f"{stats.get('weibull_rsq', 'N/A'):.3f}" if stats.get('weibull_rsq') else 'N/A'],
                    ['Number of Long Licks', stats.get('n_long_licks', 'N/A')],
                    ['Maximum Lick Duration (s)', f"{stats.get('max_lick_duration', 'N/A'):.4f}" if isinstance(stats.get('max_lick_duration'), (int, float)) else stats.get('max_lick_duration', 'N/A')]
                ], columns=['Property', 'Value'])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Export selected figure data
            if 'session_hist' in selected_data and 'session_hist' in figure_data:
                data = figure_data['session_hist']
                df = pd.DataFrame({
                    'Time_Bin_Center_s': data['bin_centers'],
                    'Lick_Count': data['counts']
                })
                df.to_excel(writer, sheet_name='Session_Histogram', index=False)
            
            if 'intraburst_freq' in selected_data and 'intraburst_freq' in figure_data:
                data = figure_data['intraburst_freq']
                df = pd.DataFrame({
                    'ILI_Bin_Center_s': data['ili_centers'],
                    'Frequency': data['counts']
                })
                df.to_excel(writer, sheet_name='Intraburst_Frequency', index=False)
            
            if 'lick_lengths' in selected_data and figure_data.get('lick_lengths'):
                data = figure_data['lick_lengths']
                df = pd.DataFrame({
                    'Duration_Bin_Center_s': data['duration_centers'],
                    'Frequency': data['counts']
                })
                df.to_excel(writer, sheet_name='Lick_Lengths', index=False)
            
            if 'burst_hist' in selected_data and 'burst_hist' in figure_data:
                data = figure_data['burst_hist']
                df = pd.DataFrame({
                    'Burst_Size': data['burst_sizes'],
                    'Frequency': data['counts']
                })
                df.to_excel(writer, sheet_name='Burst_Histogram', index=False)
            
            if 'burst_prob' in selected_data and 'burst_prob' in figure_data:
                data = figure_data['burst_prob']
                df = pd.DataFrame({
                    'Burst_Size': data['burst_sizes'],
                    'Probability': data['probabilities']
                })
                df.to_excel(writer, sheet_name='Burst_Probability', index=False)
            
            if 'burst_details' in selected_data and figure_data.get('burst_details'):
                data = figure_data['burst_details']
                df = pd.DataFrame({
                    'Burst_Number': data['burst_numbers'],
                    'N_Licks': data['n_licks'],
                    'Start_Time_s': data['start_times'],
                    'End_Time_s': data['end_times'],
                    'Duration_s': data['durations']
                })
                df.to_excel(writer, sheet_name='Burst_Details', index=False)
        
        # Get the value from the buffer
        output.seek(0)
        excel_data = output.getvalue()
        
        status_msg = dbc.Alert(
            f"✅ Successfully exported data for {animal_id} to {filename}",
            color="success",
            dismissable=True,
            duration=4000
        )
        
        return dcc.send_bytes(excel_data, filename), status_msg
        
    except Exception as e:
        error_msg = dbc.Alert(
            f"❌ Export failed: {str(e)}",
            color="danger",
            dismissable=True,
            duration=4000
        )
        return None, error_msg

# Results table callbacks

# Add current results to table
@app.callback(Output('results-table-store', 'data'),
              Output('table-status', 'children'),
              Input('add-to-table-btn', 'n_clicks'),
              State('animal-id-input', 'value'),
              State('figure-data-store', 'data'),
              State('results-table-store', 'data'),
              State('filename-store', 'data'),
              State('division-number', 'value'),
              State('division-method', 'value'),
              State('session-length-input', 'value'),
              State('data-store', 'data'),
              State('onset-array', 'value'),
              State('offset-array', 'value'),
              State('interburst-slider', 'value'),
              State('minlicks-slider', 'value'),
              State('longlick-threshold', 'value'),
              prevent_initial_call=True)
def add_to_results_table(n_clicks, animal_id, figure_data, existing_data, source_filename, 
                        division_number, division_method, session_length, data_store, onset_key, offset_key,
                        ibi, minlicks, longlick_th):
    """Add current analysis results to the results table with optional divisions"""
    if n_clicks == 0 or not figure_data or 'summary_stats' not in figure_data:
        raise PreventUpdate
    
    try:
        # If no division (whole session), recalculate with proper onset/offset validation
        if division_number == 1:
            # Load the data and recalculate to ensure proper long lick statistics
            import json
            data_array = json.loads(data_store)
            df = pd.read_json(io.StringIO(data_array[onset_key]), orient='split')
            lick_times = df["licks"].to_list()
            
            # Get offset data if available
            offset_times = None
            if offset_key and offset_key != 'none':
                offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
                offset_times = offset_df["licks"].to_list()
            
            # For whole session: start time is always 0, end time uses session length input
            start_time = 0
            
            # Use session length from input box, or fall back to max lick time
            if session_length and session_length > 0:
                end_time = session_length
            else:
                end_time = max(lick_times) if lick_times else 0
            
            # Recalculate stats with proper onset/offset validation
            try:
                # Use enhanced lickCalc with current parameters to get accurate long lick stats
                enhanced_results = lickCalc(
                    licks=lick_times,
                    offset=offset_times if offset_times else [],
                    burstThreshold=ibi,
                    minburstlength=minlicks,
                    longlickThreshold=longlick_th
                )
                
                # Create new row with recalculated stats
                new_row = {
                    'id': animal_id or 'Unknown',
                    'source_filename': source_filename if source_filename else 'N/A',
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'total_licks': enhanced_results.get('total', np.nan),
                    'intraburst_freq': enhanced_results.get('freq', np.nan),
                    'n_bursts': enhanced_results.get('bNum', np.nan),
                    'mean_licks_per_burst': enhanced_results.get('bMean', np.nan),
                    'weibull_alpha': enhanced_results.get('weib_alpha', np.nan),
                    'weibull_beta': enhanced_results.get('weib_beta', np.nan),
                    'weibull_rsq': enhanced_results.get('weib_rsq', np.nan),
                    'n_long_licks': len(enhanced_results.get('longlicks', [])) if offset_times else np.nan,
                    'max_lick_duration': np.max(enhanced_results.get('licklength', [])) if offset_times and enhanced_results.get('licklength') is not None and len(enhanced_results.get('licklength', [])) > 0 else np.nan
                }
                
            except Exception as e:
                logging.error(f"Error recalculating whole session stats: {e}")
                # Fall back to figure_data stats - check if they contain valid long lick data
                stats = figure_data['summary_stats']
                
                # Try to get properly calculated long lick values from figure_data
                n_long_licks = np.nan
                max_lick_duration = np.nan
                
                if isinstance(stats.get('n_long_licks'), (int, float)):
                    n_long_licks = stats.get('n_long_licks')
                elif offset_times:
                    # If figure_data doesn't have proper values but we have offset data, try a quick calculation
                    try:
                        temp_results = lickCalc(lick_times, offset=offset_times, longlickThreshold=longlick_th)
                        n_long_licks = len(temp_results.get('longlicks', []))
                        licklength_array = temp_results.get('licklength', [])
                        if licklength_array is not None and len(licklength_array) > 0:
                            max_lick_duration = np.max(licklength_array)
                    except:
                        pass
                
                # Only use figure_data value if we haven't calculated it above
                if max_lick_duration is np.nan and isinstance(stats.get('max_lick_duration'), (int, float)):
                    max_lick_duration = stats.get('max_lick_duration')
                
                new_row = {
                    'id': animal_id or 'Unknown',
                    'source_filename': source_filename if source_filename else 'N/A',
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'total_licks': stats.get('total_licks', np.nan),
                    'intraburst_freq': stats.get('intraburst_freq', np.nan),
                    'n_bursts': stats.get('n_bursts', np.nan),
                    'mean_licks_per_burst': stats.get('mean_licks_per_burst', np.nan),
                    'weibull_alpha': stats.get('weibull_alpha', np.nan),
                    'weibull_beta': stats.get('weibull_beta', np.nan),
                    'weibull_rsq': stats.get('weibull_rsq', np.nan),
                    'n_long_licks': n_long_licks,
                    'max_lick_duration': max_lick_duration
                }
            
            # Add to existing data
            updated_data = existing_data.copy() if existing_data else []
            updated_data.append(new_row)
            
            status_msg = dbc.Alert(
                f"✅ Added results for {animal_id} to table",
                color="success",
                dismissable=True,
                duration=3000
            )
            
            return updated_data, status_msg
        
        else:
            # Handle divisions - need to reanalyze data in segments
            if not data_store or not onset_key:
                raise Exception("No data available for division analysis")
            
            import json
            data_array = json.loads(data_store)
            df = pd.read_json(io.StringIO(data_array[onset_key]), orient='split')
            lick_times = df["licks"].to_list()
            
            # Get offset data if available
            offset_times = None
            if offset_key and offset_key != 'none':
                offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
                offset_times = offset_df["licks"].to_list()
                
                # Adjust arrays if needed
                if len(lick_times) - len(offset_times) == 1:
                    lick_times = lick_times[:-1]
                elif len(lick_times) != len(offset_times):
                    lick_times = lick_times[:len(offset_times)]
            
            # Calculate divisions using enhanced lickCalc function
            division_rows = []
            
            # Use enhanced lickCalc with division parameters
            if division_method == 'time':
                # Calculate with time divisions
                enhanced_results = lickCalc(
                    licks=lick_times,
                    offset=offset_times if offset_times else [],
                    burstThreshold=ibi,
                    minburstlength=minlicks,
                    longlickThreshold=longlick_th,
                    time_divisions=division_number,
                    session_length=session_length if session_length and session_length > 0 else None
                )
                
                # Convert trompy division results to webapp format
                if 'time_divisions' in enhanced_results:
                    # Determine the total session duration for proper time division calculation
                    total_session_duration = session_length if session_length and session_length > 0 else max(lick_times) if lick_times else 0
                    division_duration = total_session_duration / division_number
                    
                    for i, div in enumerate(enhanced_results['time_divisions']):
                        # Ensure divisions start from 0 and cover the full session
                        division_start = i * division_duration
                        division_end = (i + 1) * division_duration
                        
                        division_rows.append({
                            'id': f"{animal_id}_T{div['division_number']}" if animal_id else f"T{div['division_number']}",
                            'source_filename': f"{source_filename} (Time {div['division_number']}/{division_number}: {division_start:.0f}-{division_end:.0f}s)" if source_filename else f"Time {div['division_number']}/{division_number} ({division_start:.0f}-{division_end:.0f}s)",
                            'start_time': division_start,
                            'end_time': division_end,
                            'duration': division_duration,
                            'total_licks': div['total_licks'],
                            'intraburst_freq': div['intraburst_freq'],
                            'n_bursts': div['n_bursts'],
                            'mean_licks_per_burst': div['mean_licks_per_burst'],
                            'weibull_alpha': div['weibull_alpha'],
                            'weibull_beta': div['weibull_beta'],
                            'weibull_rsq': div['weibull_rsq'],
                            'n_long_licks': div['n_long_licks'],
                            'max_lick_duration': div['max_lick_duration']
                        })
            
            elif division_method == 'bursts':
                # Calculate with burst divisions
                enhanced_results = lickCalc(
                    licks=lick_times,
                    offset=offset_times if offset_times else [],
                    burstThreshold=ibi,
                    minburstlength=minlicks,
                    longlickThreshold=longlick_th,
                    burst_divisions=division_number
                )
                
                # Convert trompy division results to webapp format
                if 'burst_divisions' in enhanced_results:
                    for div in enhanced_results['burst_divisions']:
                        bursts_in_segment = div['end_burst'] - div['start_burst']
                        division_rows.append({
                            'id': f"{animal_id}_B{div['division_number']}" if animal_id else f"B{div['division_number']}",
                            'source_filename': f"{source_filename} (Bursts {div['start_burst']+1}-{div['end_burst']}, {bursts_in_segment} bursts)" if source_filename else f"Bursts {div['start_burst']+1}-{div['end_burst']} ({bursts_in_segment} bursts)",
                            'start_time': div['start_time'],
                            'end_time': div['end_time'],
                            'duration': div['duration'],
                            'total_licks': div['total_licks'],
                            'intraburst_freq': div['intraburst_freq'],
                            'n_bursts': div['n_bursts'],
                            'mean_licks_per_burst': div['mean_licks_per_burst'],
                            'weibull_alpha': div['weibull_alpha'],
                            'weibull_beta': div['weibull_beta'],
                            'weibull_rsq': div['weibull_rsq'],
                            'n_long_licks': div['n_long_licks'],
                            'max_lick_duration': div['max_lick_duration']
                        })
                else:
                    # Handle case where no burst divisions could be created (e.g., no bursts)
                    for i in range(division_number):
                        division_rows.append({
                            'id': f"{animal_id}_B{i+1}" if animal_id else f"B{i+1}",
                            'source_filename': f"{source_filename} (Bursts {i+1}/{division_number} - no bursts found)" if source_filename else f"Bursts {i+1}/{division_number} (no bursts found)",
                            'start_time': 0,
                            'end_time': 0,
                            'duration': 0,
                            'total_licks': 0,
                            'intraburst_freq': float('nan'),
                            'n_bursts': 0,
                            'mean_licks_per_burst': float('nan'),
                            'weibull_alpha': float('nan'),
                            'weibull_beta': float('nan'),
                            'weibull_rsq': float('nan'),
                            'n_long_licks': 0,
                            'max_lick_duration': float('nan')
                        })
            
            # Add all division rows to existing data
            updated_data = existing_data.copy() if existing_data else []
            updated_data.extend(division_rows)
            
            status_msg = dbc.Alert(
                f"✅ Added {len(division_rows)} divided results for {animal_id} to table",
                color="success",
                dismissable=True,
                duration=3000
            )
            
            return updated_data, status_msg
        
    except Exception as e:
        error_msg = dbc.Alert(
            f"❌ Failed to add results: {str(e)}",
            color="danger",
            dismissable=True,
            duration=4000
        )
        return existing_data, error_msg

# Update table display with statistics
@app.callback(Output('results-table', 'data'),
              Input('results-table-store', 'data'))
def update_results_table(stored_data):
    """Update the displayed table with stored data plus statistics"""
    if not stored_data:
        # Return placeholder empty rows to make the table look more complete
        empty_rows = []
        for i in range(5):  # Add 5 empty placeholder rows
            empty_row = {
                'id': '',
                'source_filename': '',
                'start_time': None,
                'end_time': None,
                'duration': None,
                'total_licks': None,
                'intraburst_freq': None,
                'n_bursts': None,
                'mean_licks_per_burst': None,
                'weibull_alpha': None,
                'weibull_beta': None,
                'weibull_rsq': None,
                'n_long_licks': None,
                'max_lick_duration': None
            }
            empty_rows.append(empty_row)
        return empty_rows
    
    # Create copy of data
    table_data = stored_data.copy()
    
    # Calculate statistics (ignoring NaN values)
    if len(table_data) > 1:  # Only add stats if there's more than one row
        numeric_columns = ['start_time', 'end_time', 'duration', 'total_licks', 'intraburst_freq', 'n_bursts', 'mean_licks_per_burst', 
                          'weibull_alpha', 'weibull_beta', 'weibull_rsq', 'n_long_licks', 'max_lick_duration']
        
        # Convert data to DataFrame for easier calculation
        df = pd.DataFrame(table_data)
        
        # Calculate statistics
        stats_rows = []
        
        # Sum (for appropriate columns)
        sum_row = {'id': 'Sum', 'source_filename': ''}
        # Only sum certain columns that make sense to sum
        summable_columns = ['duration', 'total_licks', 'n_bursts', 'n_long_licks']
        for col in numeric_columns:
            if col in summable_columns:
                sum_row[col] = df[col].sum() if not df[col].isna().all() else None
            else:
                sum_row[col] = None  # Don't sum rates, ratios, or other derived metrics
        stats_rows.append(sum_row)
        
        # Mean
        mean_row = {'id': 'Mean', 'source_filename': ''}
        for col in numeric_columns:
            if col in df.columns:
                values = pd.to_numeric(df[col], errors='coerce')
                mean_val = values.mean()
                mean_row[col] = mean_val if not pd.isna(mean_val) else np.nan
        stats_rows.append(mean_row)
        
        # Standard Deviation
        sd_row = {'id': 'SD', 'source_filename': ''}
        for col in numeric_columns:
            if col in df.columns:
                values = pd.to_numeric(df[col], errors='coerce')
                sd_val = values.std()
                sd_row[col] = sd_val if not pd.isna(sd_val) else np.nan
        stats_rows.append(sd_row)
        
        # N (count of non-NaN values)
        n_row = {'id': 'N', 'source_filename': ''}
        for col in numeric_columns:
            if col in df.columns:
                values = pd.to_numeric(df[col], errors='coerce')
                n_val = values.count()
                n_row[col] = n_val
        stats_rows.append(n_row)
        
        # Standard Error
        se_row = {'id': 'SE', 'source_filename': ''}
        for col in numeric_columns:
            if col in df.columns:
                values = pd.to_numeric(df[col], errors='coerce')
                sd_val = values.std()
                n_val = values.count()
                se_val = sd_val / np.sqrt(n_val) if n_val > 0 and not pd.isna(sd_val) else np.nan
                se_row[col] = se_val if not pd.isna(se_val) else np.nan
        stats_rows.append(se_row)
        
        # Add separator and stats
        table_data.extend(stats_rows)
    
    return table_data

# Delete selected row
@app.callback(Output('results-table-store', 'data', allow_duplicate=True),
              Output('table-status', 'children', allow_duplicate=True),
              Input('delete-row-btn', 'n_clicks'),
              State('results-table', 'selected_rows'),
              State('results-table-store', 'data'),
              prevent_initial_call=True)
def delete_selected_row(n_clicks, selected_rows, stored_data):
    """Delete selected row from the results table"""
    if n_clicks == 0 or not selected_rows or not stored_data:
        raise PreventUpdate
    
    try:
        selected_idx = selected_rows[0]
        
        # Don't allow deletion of statistics rows
        if selected_idx >= len(stored_data):
            error_msg = dbc.Alert(
                "❌ Cannot delete statistics rows",
                color="warning",
                dismissable=True,
                duration=3000
            )
            return stored_data, error_msg
        
        # Remove the selected row
        updated_data = stored_data.copy()
        deleted_id = updated_data[selected_idx].get('id', 'Unknown')
        del updated_data[selected_idx]
        
        status_msg = dbc.Alert(
            f"✅ Deleted row for {deleted_id}",
            color="info",
            dismissable=True,
            duration=3000
        )
        
        return updated_data, status_msg
        
    except Exception as e:
        error_msg = dbc.Alert(
            f"❌ Failed to delete row: {str(e)}",
            color="danger",
            dismissable=True,
            duration=4000
        )
        return stored_data, error_msg

# Clear all results
@app.callback(Output('results-table-store', 'data', allow_duplicate=True),
              Output('table-status', 'children', allow_duplicate=True),
              Input('clear-all-btn', 'n_clicks'),
              prevent_initial_call=True)
def clear_all_results(n_clicks):
    """Clear all results from the table"""
    if n_clicks == 0:
        raise PreventUpdate
    
    status_msg = dbc.Alert(
        "✅ All results cleared from table",
        color="info",
        dismissable=True,
        duration=3000
    )
    
    return [], status_msg

# Export selected row
@app.callback(Output("download-table", "data"),
              Output('table-status', 'children', allow_duplicate=True),
              Input('export-row-btn', 'n_clicks'),
              Input('export-table-btn', 'n_clicks'),
              State('results-table', 'selected_rows'),
              State('results-table-store', 'data'),
              prevent_initial_call=True)
def export_table_data(export_row_clicks, export_table_clicks, selected_rows, stored_data):
    """Export selected row or full table to Excel"""
    ctx = dash.callback_context
    if not ctx.triggered or not stored_data:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if button_id == 'export-row-btn':
            if not selected_rows:
                error_msg = dbc.Alert(
                    "❌ Please select a row to export",
                    color="warning",
                    dismissable=True,
                    duration=3000
                )
                return None, error_msg
            
            selected_idx = selected_rows[0]
            if selected_idx >= len(stored_data):
                error_msg = dbc.Alert(
                    "❌ Cannot export statistics rows individually",
                    color="warning",
                    dismissable=True,
                    duration=3000
                )
                return None, error_msg
            
            # Export single row
            export_data = [stored_data[selected_idx]]
            row_id = export_data[0].get('id', 'Unknown')
            filename = f"lickcalc_SingleRow_{row_id}_{timestamp}.xlsx"
            success_msg = f"✅ Exported row for {row_id}"
            
        else:  # export-table-btn
            # Export full table
            export_data = stored_data.copy()
            filename = f"lickcalc_ResultsTable_{timestamp}.xlsx"
            success_msg = f"✅ Exported full table ({len(stored_data)} rows)"
        
        # Create Excel file
        df = pd.DataFrame(export_data)
        
        # Create a BytesIO buffer
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Results', index=False)
        
        output.seek(0)
        excel_data = output.getvalue()
        
        status_msg = dbc.Alert(
            success_msg,
            color="success",
            dismissable=True,
            duration=4000
        )
        
        return dcc.send_bytes(excel_data, filename), status_msg
        
    except Exception as e:
        error_msg = dbc.Alert(
            f"❌ Export failed: {str(e)}",
            color="danger",
            dismissable=True,
            duration=4000
        )
        return None, error_msg

if __name__ == '__main__':
    app.run(debug=app_config['debug'], dev_tools_hot_reload=app_config['hot_reload'])
    
"""
TO DO:
    Add log scale option for y axis on intraburst frequency

    8. change slider dynamically to match different length files, e.g. 24h data gets 1, 2, 3, 4 h etc'
    12. multiple sessions in medfiles
    16. make histograms look the same, i.e. space between bars

    
For the histogram bin size, specify if its in minutes or seconds
"intraburst lick frequency" is average number of licks / second, might be nice to have that as a description somewhere to make it super clear what it is

Would be nice to have the sliders for setting intraburst lick interval and minimum licks/burst higher on the page
Maybe an explanation of what the Weibul plot is?
Definition of what a "long lick" is? And perhaps an option to set that, and an option to remove long licks from the data?

    
    
    
"""
    