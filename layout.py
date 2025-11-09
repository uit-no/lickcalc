"""
Layout definition for lickcalc webapp.
Contains all the UI components and structure.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table

from config_manager import config
from tooltips import (
    get_binsize_tooltip, 
    get_ibi_tooltip, 
    get_minlicks_tooltip,
    get_longlick_tooltip, 
    get_table_tooltips, 
    get_onset_tooltip, 
    get_offset_tooltip, 
    get_session_length_tooltip, 
    TOOLTIP_TEXTS
)

# Get table cells and tooltips
table_cells, table_tooltips = get_table_tooltips()


def get_app_layout():
    """
    Returns the main layout for the lickcalc webapp.
    """
    return dbc.Container([
dcc.Store(id='lick-data'),
    dcc.Store(id='data-store'),
    dcc.Store(id='figure-data-store'),  # Store for figure underlying data
    dcc.Store(id='filename-store'),  # Store for uploaded filename
    dcc.Store(id='session-duration-store'),  # Store for total session duration
    dcc.Store(id='custom-config-store'),  # Store for custom config values
    dcc.Store(id='session-length-seconds'),  # Store for session length in seconds (latent variable)
    dcc.Store(id='between-start-seconds'),  # Store for between start time in seconds
    dcc.Store(id='between-stop-seconds'),  # Store for between stop time in seconds
    # 'between' refers to 'between times analysis' or 'time range filtering' for session/epoch selection
    html.Div(
    [
        # Floating buttons at top right - vertically arranged
        html.Div([
            # Help button
            html.A(
                "📖 Help", 
                href="/help", 
                target="_blank",
                className="btn btn-outline-primary btn-sm",
                style={
                    "position": "fixed", 
                    "top": "10px", 
                    "right": "10px",
                    "z-index": "9999",
                    "text-decoration": "none",
                    "width": "120px"
                }
            ),
            # Config upload button
            dcc.Upload(
                id='upload-config',
                children=html.Div(
                    id='config-button-content',
                    children="📁 Load Config",
                    className="btn btn-outline-primary btn-sm",
                    style={
                        "cursor": "pointer",
                        "text-align": "center",
                        "white-space": "nowrap"
                    }
                ),
                multiple=False,
                style={
                    "position": "fixed",
                    "top": "45px",
                    "right": "10px",
                    "z-index": "9999",
                    "width": "120px"
                }
            ),
            # About button
            html.Button(
                "ℹ️ About",
                id="about-button",
                className="btn btn-outline-primary btn-sm",
                style={
                    "position": "fixed",
                    "top": "80px",
                    "right": "10px",
                    "z-index": "9999",
                    "width": "120px"
                }
            ),
        ]),
        # About modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("About lickcalc")),
            dbc.ModalBody([
                html.H5("Version", className="mt-3"),
                html.P(id="about-version", style={"font-family": "monospace", "font-size": "1.1em"}),
                
                html.H5("Citation", className="mt-4"),
                html.P([
                    "If you use lickcalc in your research, please cite:",
                ]),
                html.Div([
                    html.P([
                        html.Strong("Volcko KL & McCutcheon JE (2025). "),
                        "lickcalc: Easy analysis of lick microstructure in experiments of rodent ingestive behaviour. ",
                        html.Em("Journal of Open Source Software"),
                        ", xxxxx. ",
                        html.A(
                            "https://doi.org/10.21105/joss.xxxxx",
                            href="https://doi.org/10.21105/joss.xxxxx",
                            target="_blank"
                        )
                    ], style={"padding": "10px", "background-color": "#f8f9fa", "border-radius": "5px"}),
                ]),
                
                html.H5("GitHub Repository", className="mt-4"),
                html.P([
                    "Source code, documentation, and issue tracker:",
                ]),
                html.A(
                    "https://github.com/uit-no/lickcalc",
                    href="https://github.com/uit-no/lickcalc",
                    target="_blank",
                    className="btn btn-outline-primary btn-sm"
                ),
                
                html.H5("Example Data Files", className="mt-4"),
                html.P([
                    "Download example data files to try out lickcalc:",
                ]),
                html.Button(
                    "📥 Download Example Files",
                    id="download-examples-button",
                    className="btn btn-outline-success btn-sm"
                ),
                dcc.Download(id="download-examples"),
                
                html.H5("License", className="mt-4"),
                html.P("lickcalc is open source software licensed under the GPL-3.0 License."),
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="about-close", className="ml-auto")
            ),
        ],
        id="about-modal",
        size="lg",
        is_open=False,
        ),
        
        dbc.Row(children=[
            dbc.Col(html.H1("lickcalc"), width=12),
        ]),
        dbc.Row(
            dbc.Col(html.Div(
                '''
                    This app lets you load in timestamps of licks from behavioural
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
                                  {'label': 'Med (column-based)', 'value': 'med'},
                                  {'label': 'Med (array-based)', 'value': 'med_array'},
                                  {'label': 'CSV/TXT', 'value': 'csv'},
                                  {'label': 'DD Lab', 'value': 'dd'},
                                  {'label': 'KM Lab', 'value': 'km'},
                                  {'label': 'OHRBETS', 'value': 'ohrbets'},],
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
                dbc.Row([
                    dbc.Col([
                        dbc.Input(
                            id='session-length-input',
                            type='number',
                            value=config.get('session.length', 3600) if config.get('session.length', 'auto') != 'auto' else 3600,
                            min=1,
                            step=1,
                            placeholder="Duration",
                            style={'width': '100%'}
                        )
                    ], width=7),
                    dbc.Col([
                        dcc.Dropdown(
                            id='session-length-unit',
                            options=[
                                {'label': 's', 'value': 's'},
                                {'label': 'min', 'value': 'min'},
                                {'label': 'hr', 'value': 'hr'}
                            ],
                            value=config.get('session.length_unit', 's'),
                            clearable=False,
                            style={'width': '100%'}
                        )
                    ], width=5)
                ], className="g-1")
            ], width=2),
            get_session_length_tooltip()[1],
            dbc.Col([
                html.Div(id='binsize-label-container', children=[
                    get_binsize_tooltip()[0],
                    get_binsize_tooltip()[1],
                ]),
                dcc.Slider(
                    id='session-bin-slider',
                    **config.get_slider_config('session_bin')),
                dcc.Store(id='session-bin-slider-seconds', data=config.get_slider_config('session_bin')['value'])  # Store actual value in seconds
            ], width=6),
            ]),
        
        # Add spacing before microstructural analysis section
        dbc.Row(dbc.Col(html.Hr(), width=12), style={'margin-top': '30px'}),  # Separator line
        dbc.Row(dbc.Col(html.H2("Microstructural analysis"), width='auto')),
        
        # Controls for microstructural analysis
        dbc.Row(children=[
            dbc.Col([
                get_ibi_tooltip()[0],
                get_ibi_tooltip()[1],
                dbc.Row([
                    dbc.Col([
                        dcc.Slider(id='interburst-slider',
                            tooltip={"placement": "bottom", "always_visible": False},
                            **config.get_slider_config('interburst'))
                    ], width=9),
                    dbc.Col([
                        html.Div([
                            html.Span(
                                id='interburst-display',
                                children=str(config.get_slider_config('interburst')['value']),
                                style={'font-weight': 'bold', 'font-size': '16px'}
                            ),
                            html.Span(' s', style={'font-size': '16px', 'font-weight': 'bold', 'color': '#6c757d', 'margin-left': '2px'})
                        ], style={
                            'text-align': 'center',
                            'padding': '6px 4px',
                            'background-color': '#f8f9fa',
                            'border': '1px solid #dee2e6',
                            'border-radius': '4px',
                            'color': '#495057',
                            'margin-top': '5px',
                            'margin-left': '-5px'  # Pull slightly closer to slider
                        })
                    ], width=3)
                ])
            ], width=4, style={'padding-right': '20px'}),  # Add spacing to the right
            dbc.Col([
                get_minlicks_tooltip()[0],
                get_minlicks_tooltip()[1],
                dbc.Row([
                    dbc.Col([
                        dcc.Slider(id='minlicks-slider',
                                  tooltip={"placement": "bottom", "always_visible": False},
                                  **config.get_slider_config('minlicks'))
                    ], width=9),
                    dbc.Col([
                        html.Div(
                            id='minlicks-display',
                            children=str(config.get_slider_config('minlicks')['value']),
                            style={
                                'text-align': 'center',
                                'padding': '6px 4px',
                                'background-color': '#f8f9fa',
                                'border': '1px solid #dee2e6',
                                'border-radius': '4px',
                                'font-weight': 'bold',
                                'font-size': '16px',
                                'color': '#495057',
                                'margin-top': '5px',
                                'margin-left': '-5px'  # Pull slightly closer to slider
                            }
                        )
                    ], width=3)
                ])
            ], width=4, style={'padding-right': '20px'}),  # Add spacing to the right
            dbc.Col([
                get_longlick_tooltip()[0],
                get_longlick_tooltip()[1],
                dbc.Row([
                    dbc.Col([
                        dcc.Slider(
                            id='longlick-threshold',
                            tooltip={"placement": "bottom", "always_visible": False},
                            **config.get_slider_config('longlick'))
                    ], width=9),
                    dbc.Col([
                        html.Div([
                            html.Span(
                                id='longlick-display',
                                children=str(config.get_slider_config('longlick')['value']),
                                style={'font-weight': 'bold', 'font-size': '16px'}
                            ),
                            html.Span(' s', style={'font-size': '16px', 'font-weight': 'bold', 'color': '#6c757d', 'margin-left': '2px'})
                        ], style={
                            'text-align': 'center',
                            'padding': '6px 4px',
                            'background-color': '#f8f9fa',
                            'border': '1px solid #dee2e6',
                            'border-radius': '4px',
                            'color': '#495057',
                            'margin-top': '5px',
                            'margin-left': '-5px'  # Pull slightly closer to slider
                        })
                    ], width=3)
                ]),
                # Move the remove long licks checkbox below the slider and value box
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Span("Remove long licks", style={'font-size': '16px', 'color': '#495057'}),  # Not bold, larger font
                            html.Span(" ⓘ", id="remove-longlicks-help", 
                                    style={"color": "#007bff", "cursor": "help", "margin-left": "8px"}),
                            dbc.Checklist(
                                id='remove-longlicks-checkbox',
                                options=[{'label': '', 'value': 'remove'}],  # Empty label since we have text above
                                value=[],  # Default unchecked
                                inline=True,
                                style={'margin-left': '10px', 'display': 'inline-block'}
                            ),
                            dbc.Tooltip(
                                "Removes licks longer than the threshold from analysis. "
                                "Requires offset data to calculate lick durations. "
                                "Only affects long lick duration analysis when offset data is available.",
                                target="remove-longlicks-help",
                                placement="top"
                            )
                        ], style={'margin-top': '15px', 'display': 'flex', 'align-items': 'center'})
                    ], width=12)
                ])
            ], width=4, id='longlick-controls-column'),  # Add ID for visibility control
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
                html.Label("Analysis epoch(s):", style={'font-weight': 'bold'}),
                dcc.Dropdown(
                    id='division-number',
                    options=[
                        {'label': 'Whole session', 'value': 'whole_session'},
                        {'label': 'Divide by 2', 'value': 2},
                        {'label': 'Divide by 3', 'value': 3},
                        {'label': 'Divide by 4', 'value': 4},
                        {'label': 'First n bursts', 'value': 'first_n_bursts'},
                        {'label': 'Between times', 'value': 'between'},
                        {'label': 'Trial-based', 'value': 'trial_based'}
                    ],
                    value='whole_session',
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
            ], width=3, id='division-method-col', style={'display': 'none'}),
            dbc.Col([
                html.Label("n bursts:", style={'font-weight': 'bold'}),
                dcc.Dropdown(
                    id='n-bursts-number',
                    options=[{'label': str(i), 'value': i} for i in range(1, 11)],
                    value=3,
                    style={'margin-top': '5px'}
                )
            ], width=2, id='n-bursts-col', style={'display': 'none'}),
            dbc.Col([
                html.Label("Start:", style={'font-weight': 'bold'}),
                dbc.Input(
                    id='between-start-time',
                    type='number',
                    value=0,
                    min=0,
                    step=1,
                    style={'margin-top': '5px'}
                )
            ], width=2, id='between-start-col', style={'display': 'none'}),
            dbc.Col([
                html.Label("Stop:", style={'font-weight': 'bold'}),
                dbc.Input(
                    id='between-stop-time',
                    type='number',
                    value=3600,
                    min=0,
                    step=1,
                    style={'margin-top': '5px'}
                )
            ], width=2, id='between-stop-col', style={'display': 'none'}),
            dbc.Col([
                html.Label("Unit:", style={'font-weight': 'bold'}),
                dcc.Dropdown(
                    id='between-time-unit',
                    options=[
                        {'label': 's', 'value': 's'},
                        {'label': 'min', 'value': 'min'},
                        {'label': 'hr', 'value': 'hr'}
                    ],
                    value='s',
                    clearable=False,
                    style={'margin-top': '5px'}
                )
            ], width=1, id='between-unit-col', style={'display': 'none'}),
            dbc.Col([
                html.Label("Trial Detection:", style={'font-weight': 'bold'}),
                dcc.Dropdown(
                    id='trial-detection-method',
                    options=[
                        {'label': 'Auto-detect', 'value': 'auto'},
                        {'label': 'Load trial times', 'value': 'load'}
                    ],
                    value='auto',
                    style={'margin-top': '5px'}
                )
            ], width=2, id='trial-detection-col', style={'display': 'none'}),
            dbc.Col([
                html.Label("Trials Detected:", style={'font-weight': 'bold'}),
                html.Div(
                    id='trials-detected-display',
                    children='No trials detected',
                    style={
                        'margin-top': '5px',
                        'padding': '6px 12px',
                        'background-color': '#f8f9fa',
                        'border': '1px solid #dee2e6',
                        'border-radius': '4px',
                        'text-align': 'center',
                        'font-size': '14px',
                        'color': '#6c757d',
                        'min-height': '38px',
                        'display': 'flex',
                        'align-items': 'center',
                        'justify-content': 'center'
                    }
                )
            ], width=2, id='trials-detected-col', style={'display': 'none'}),
            dbc.Col([
                html.Div([
                    html.Label("ITI (s)", style={'font-weight': 'bold', 'display': 'inline-block'}),
                    html.Span(" ⓘ", id="trial-iti-help", 
                             style={"color": "#007bff", "cursor": "help", "margin-left": "5px"}),
                    dbc.Tooltip(
                        "This should be the minimum ITI expected in the data.",
                        target="trial-iti-help",
                        placement="top"
                    )
                ]),
                dbc.Input(
                    id='trial-min-iti',
                    type='number',
                    value=60,
                    min=0,
                    step=1,
                    style={'margin-top': '5px'}
                )
            ], width=2, id='trial-min-iti-col', style={'display': 'none'}),
            dbc.Col([
                html.Div([
                    html.Label("Crop trials", style={'font-weight': 'bold', 'display': 'inline-block'}),
                    html.Span(" ⓘ", id="crop-trials-help", 
                             style={"color": "#007bff", "cursor": "help", "margin-left": "5px"}),
                    dbc.Tooltip(
                        "Excludes the last burst from each trial if there is more than 1 burst.",
                        target="crop-trials-help",
                        placement="top"
                    )
                ]),
                dbc.Checklist(
                    id='trial-exclude-last-burst',
                    options=[{'label': '', 'value': 'exclude'}],
                    value=[],
                    inline=True,
                    style={'margin-top': '5px'}
                )
            ], width=2, id='trial-exclude-col', style={'display': 'none'}),
            dbc.Col([
                html.Label("\u00A0", style={'font-weight': 'bold'}),  # Non-breaking space for alignment
                html.Button(
                    'Load Trial Types',
                    id='load-trial-types-btn',
                    n_clicks=0,
                    className='btn btn-secondary btn-sm',
                    style={'margin-top': '5px', 'width': '100%'}
                )
            ], width=2, id='trial-load-col', style={'display': 'none'}),
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
                html.Button(
                    'Batch Process',
                    id='batch-process-btn',
                    n_clicks=0,
                    className='btn btn-outline-secondary',
                    style={'margin-left': '10px'}
                ),
                dcc.Download(id="download-table"),
                html.Div(id='table-status', style={'margin-top': '10px'})
            ], width=12)
        ], style={'margin-bottom': '20px'}),

        # Batch processing modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Batch Process Files")),
            dbc.ModalBody([
                html.P("Select a folder or multiple files to process with the current settings."),
                dcc.Upload(
                    id='batch-upload',
                    children=html.Div([
                        'Drag and drop or ', html.A('Select multiple files')
                    ]),
                    multiple=True,
                    style={
                        'width': '100%',
                        'height': '80px',
                        'lineHeight': '80px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px 0'
                    }
                ),
                html.Div(id='batch-file-list', style={'maxHeight': '150px', 'overflowY': 'auto', 'border': '1px solid #eee', 'padding': '8px', 'borderRadius': '4px'}),
                dbc.Checklist(
                    id='batch-export-excel',
                    options=[{'label': ' Also export an Excel per file', 'value': 'export'}],
                    value=[],
                    switch=True,
                    style={'marginTop': '10px'}
                ),
                dbc.Checklist(
                    id='batch-include-all-sheets',
                    options=[{'label': ' Export all sheets (ignore selections above)', 'value': 'all'}],
                    value=['all'],
                    switch=True,
                    style={'marginTop': '6px'}
                ),
                dbc.Spinner(
                    children=html.Div(id='batch-status'),
                    size='sm',
                    color='primary',
                    delay_show=250,
                    fullscreen=False,
                    spinner_style={'marginTop': '10px'}
                )
            ]),
            dbc.ModalFooter([
                dbc.Button("Start Processing", id="batch-start-btn", color="primary", className="me-2"),
                dbc.Button("Close", id="batch-close-btn", color="secondary")
            ]),
        ], id='batch-modal', is_open=False),
        dcc.Download(id='download-batch-zip'),
        
        # Results table
        dbc.Row(dbc.Col([
            dash_table.DataTable(
                id='results-table',
                columns=[
                    {'name': 'ID', 'id': 'id', 'type': 'text', 'editable': True},
                    {'name': 'Source File', 'id': 'source_filename', 'type': 'text', 'editable': False},
                    {'name': 'Onset array', 'id': 'onset_array', 'type': 'text'},
                    {'name': 'Start Time (s)', 'id': 'start_time', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                    {'name': 'End Time (s)', 'id': 'end_time', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                    {'name': 'Duration (s)', 'id': 'duration', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                    {'name': 'IBI (s)', 'id': 'interburst_interval', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                    {'name': 'Min Burst Size', 'id': 'min_burst_size', 'type': 'numeric', 'format': {'specifier': '.0f'}},
                    {'name': 'Long Lick Threshold (s)', 'id': 'longlick_threshold', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                    {'name': 'Total Licks', 'id': 'total_licks', 'type': 'numeric', 'format': {'specifier': '.0f'}},
                    {'name': 'Intraburst Freq (Hz)', 'id': 'intraburst_freq', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                    {'name': 'N Bursts', 'id': 'n_bursts', 'type': 'numeric', 'format': {'specifier': '.0f'}},
                    {'name': 'Mean Licks/Burst', 'id': 'mean_licks_per_burst', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                    {'name': 'Weibull Alpha', 'id': 'weibull_alpha', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                    {'name': 'Weibull Beta', 'id': 'weibull_beta', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                    {'name': 'Weibull R²', 'id': 'weibull_rsq', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                    {'name': 'N Long Licks', 'id': 'n_long_licks', 'type': 'numeric', 'format': {'specifier': '.0f'}},
                    {'name': 'Max Lick Duration (s)', 'id': 'max_lick_duration', 'type': 'numeric', 'format': {'specifier': '.4f'}},
                    {'name': 'Long Licks Removed?', 'id': 'long_licks_removed', 'type': 'text'}
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


# For easy import
app_layout = get_app_layout()