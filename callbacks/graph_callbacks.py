"""
Graph generation callbacks for lickcalc webapp.
"""
import io
import json
import dash
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import logging

from app_instance import app
from trompy import lickcalc
from utils import validate_onset_offset_pairs, calculate_segment_stats, get_licks_for_burst_range, get_offsets_for_licks
from config_manager import config

@app.callback(Output('session-fig', 'figure'),
              Input('lick-data', 'data'),
              Input('session-fig-type', 'value'),
              Input('session-bin-slider-seconds', 'data'),
              Input('session-length-seconds', 'data'),
              Input('session-length-unit', 'value'))
def make_session_graph(jsonified_df, figtype, binsize_seconds, session_length_seconds, time_unit):
    
    if jsonified_df is None:
        raise PreventUpdate
    else:
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        lastlick = max(df["licks"]) if len(df) > 0 else 0
        
        # Use custom session length if provided, otherwise use last lick time
        plot_duration = session_length_seconds if session_length_seconds and session_length_seconds > 0 else lastlick
        
        # Convert data based on time unit for plotting
        if time_unit == 'min':
            scale_factor = 60
            time_label = 'Time (min)'
            plot_duration_scaled = plot_duration / scale_factor
            binsize_scaled = binsize_seconds / scale_factor
            licks_scaled = df["licks"] / scale_factor
        elif time_unit == 'hr':
            scale_factor = 3600
            time_label = 'Time (hr)'
            plot_duration_scaled = plot_duration / scale_factor
            binsize_scaled = binsize_seconds / scale_factor
            licks_scaled = df["licks"] / scale_factor
        else:  # time_unit == 's'
            scale_factor = 1
            time_label = 'Time (s)'
            plot_duration_scaled = plot_duration
            binsize_scaled = binsize_seconds
            licks_scaled = df["licks"]
        
        if figtype == "hist":
            # Create histogram with scaled data
            fig = px.histogram(df.assign(licks_scaled=licks_scaled),
                            x="licks_scaled",
                            range_x=[0, plot_duration_scaled],
                            nbins=int(plot_duration/binsize_seconds) if plot_duration > 0 and binsize_seconds > 0 else 1)
        
            fig.update_layout(
                transition_duration=500,
                xaxis_title=time_label,
                yaxis_title="Licks per {:.3g} {}".format(binsize_scaled, time_unit),
                showlegend=False)
        else:
            fig = px.line(x=licks_scaled, y=range(0, len(df["licks"])))
            
            fig.update_layout(
                transition_duration=500,
                xaxis_title=time_label,
                yaxis_title="Cumulative licks",
                showlegend=False,
                xaxis=dict(range=[0, plot_duration_scaled]))

        return fig

@app.callback(Output('session-length-input', 'value'),
              Input('lick-data', 'data'),
              State('custom-config-store', 'data'),
              prevent_initial_call=True)
def update_session_length_suggestion(jsonified_df, custom_config):
    """Auto-populate session length input based on config and data"""
    if jsonified_df is None:
        raise PreventUpdate
    
    # First, check if there's a custom config loaded with a session length
    if custom_config:
        session_length_custom = custom_config.get('session', {}).get('length', 'auto')
        # If custom config specifies a fixed value (not 'auto'), use it
        if session_length_custom != 'auto':
            try:
                # Return the custom config value, overriding auto-detection
                return int(session_length_custom) if session_length_custom else 3600
            except (ValueError, TypeError):
                # If custom config value is invalid, fall through to auto-detect
                pass
    
    # If no custom config, check default config for session length setting
    session_length_config = config.get('session.length', 'auto')
    
    # If default config specifies a fixed value, use it
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
              Input('lick-data', 'data'),
              Input('interburst-slider', 'value'),
              Input('minlicks-slider', 'value'),
              Input('longlick-threshold', 'value'),
              Input('remove-longlicks-checkbox', 'value'),
              State('offset-array', 'value'),
              State('data-store', 'data'))
def make_intraburstfreq_graph(jsonified_df, ibi_slider, minlicks_slider, longlick_slider, remove_longlicks, offset_key, jsonified_dict):
    # Use slider values directly
    ibi = ibi_slider
    minlicks = minlicks_slider
    longlick_th = longlick_slider
    remove_long = 'remove' in remove_longlicks
    
    if jsonified_df is None:
        raise PreventUpdate
    else:        
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        
        if len(df) == 0:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(title="No data available")
            return fig, "0", "0.00 Hz"
        
        lick_times = df["licks"].to_list()
        
        # Check if we have offset data available and checkbox is checked
        if remove_long and offset_key and offset_key != 'none' and jsonified_dict:
            try:
                import json
                data_array = json.loads(jsonified_dict)
                if offset_key in data_array:
                    offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
                    offset_times = offset_df["licks"].to_list()
                    
                    # Check for potential cross-file contamination before processing
                    if abs(len(lick_times) - len(offset_times)) > 1:
                        # Severe mismatch suggests cross-file contamination, wait for proper sync
                        raise PreventUpdate
                    
                    lickdata = lickcalc(lick_times, offset=offset_times, burstThreshold=ibi, 
                                      minburstlength=minlicks, longlickThreshold=longlick_th, remove_longlicks=remove_long)
                else:
                    lickdata = lickcalc(lick_times, burstThreshold=ibi, minburstlength=minlicks)
            except Exception as e:
                lickdata = lickcalc(lick_times, burstThreshold=ibi, minburstlength=minlicks)
        else:
            lickdata = lickcalc(lick_times, burstThreshold=ibi, minburstlength=minlicks)
            
        ilis = lickdata["ilis"]
        
        # Validate ilis data before creating histogram
        if ilis is None or len(ilis) == 0 or not hasattr(ilis, '__iter__'):
            # Return empty figure if no interlick intervals
            fig = go.Figure()
            fig.update_layout(
                title="No interlick intervals available",
                xaxis_title="Interlick interval (s)",
                yaxis_title="Frequency"
            )
        else:
            try:
                fig = px.histogram(ilis,
                                range_x=[0, 0.5],
                                nbins=50)
                
                fig.update_layout(
                    transition_duration=500,
                    title={
                        'text': "Intraburst lick frequency",
                        'x': 0.5,  # Center the title horizontally
                        'xanchor': 'center'
                    },
                    xaxis_title="Interlick interval (s)",
                    yaxis_title="Frequency",
                    showlegend=False,
                    # margin=dict(l=20, r=20, t=20, b=20),
                )
            except Exception as e:
                # If histogram creation fails, return empty figure
                fig = go.Figure()
                fig.update_layout(
                    title="Error creating interlick interval histogram",
                    xaxis_title="Interlick interval (s)",
                    yaxis_title="Frequency"
                )
        
        nlicks = "{}".format(lickdata['total'])
        if lickdata['freq'] is not None:
            freq = "{:.2f} Hz".format(lickdata['freq'])
        else:
            freq = "N/A"
        
        return fig, nlicks, freq

# Callback to sync input fields with sliders when sliders change
@app.callback(
    [Output('interburst-display', 'children'),
     Output('minlicks-display', 'children'),
     Output('longlick-display', 'children')],
    [Input('interburst-slider', 'value'),
     Input('minlicks-slider', 'value'),
     Input('longlick-threshold', 'value')]
)
def update_display_values(ibi_value, minlicks_value, longlick_value):
    """Update display fields when sliders change"""
    # Return values - the units are already handled in the HTML structure
    return str(ibi_value), str(minlicks_value), str(longlick_value)

@app.callback(Output('longlicks-fig', 'figure'),
              Output('nlonglicks', 'children'),
              Output('longlicks-max', 'children'),
              Input('offset-array', 'value'),
              Input('longlick-threshold', 'value'),
              Input('remove-longlicks-checkbox', 'value'),
              State('data-store', 'data'),
              State('lick-data', 'data'))
def make_longlicks_graph(offset_key, longlick_slider, remove_longlicks, jsonified_dict, jsonified_df):
    # Use slider value directly
    longlick_th = longlick_slider
    remove_long = 'remove' in remove_longlicks
    
    if jsonified_df is None:
        raise PreventUpdate
    
    # Check if offset data is available
    if offset_key is None or offset_key == 'none':
        # Return figure with message similar to Weibull plot style
        fig = go.Figure()
        fig.update_layout(
            title={
                'text': "No lick duration data available",
                'x': 0.5,  # Center the title horizontally
                'xanchor': 'center'
            },
            annotations=[
                dict(
                    x=0.5,
                    y=0.5,
                    xref="paper",
                    yref="paper",
                    text="No lick duration data available<br>Offsets required",
                    showarrow=False,
                    font=dict(size=16, color="gray"),
                    xanchor="center",
                    yanchor="middle"
                )
            ],
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            height=400,  # Match other plot heights
            margin=dict(l=40, r=40, t=60, b=40)  # Standard margins
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
        
        # Critical fix: Check for potential cross-file contamination
        # If severe length mismatch, likely old data - skip validation
        if abs(len(onset) - len(offset)) > 1:
            # Severe mismatch suggests cross-file contamination, wait for proper data sync
            raise PreventUpdate
        
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
        
        lickdata = lickcalc(onset, offset=offset, longlickThreshold=longlick_th, remove_longlicks=remove_long)
        
        # Simple validation of the result
        if lickdata is None:
            logging.error("lickcalc returned None")
            fig = go.Figure()
            fig.update_layout(title="Analysis Error")
            return fig, "Error", "Error"
        
        if "licklength" not in lickdata:
            logging.error(f"licklength key not found in lickdata. Available keys: {list(lickdata.keys())}")
            fig = go.Figure()
            fig.update_layout(title="Analysis Error")
            return fig, "Error", "Error"
            
        licklength = lickdata["licklength"]
        
        if licklength is None:
            logging.error("licklength is None")
            fig = go.Figure()
            fig.update_layout(title="Analysis Error") 
            return fig, "Error", "Error"
        
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
        
        # Handle case where longlicks might be None (no licks above threshold)
        longlicks_array = lickdata["longlicks"]
        nlonglicks = "{}".format(len(longlicks_array) if longlicks_array is not None else 0)
        longlick_max = "{:.2f}".format(np.max(licklength)) if len(licklength) > 0 else "0.00"
        
        return fig, nlonglicks, longlick_max
        
    except Exception as e:
        logging.error(f"Error in longlicks callback: {e}")
        logging.error(f"Error details - offset_key: {offset_key}, jsonified_dict type: {type(jsonified_dict)}")
        if jsonified_dict:
            try:
                data_array = json.loads(jsonified_dict)
                logging.error(f"Available keys in data_array: {list(data_array.keys())}")
                if offset_key in data_array:
                    offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
                    logging.error(f"Offset data shape: {offset_df.shape}, first few values: {offset_df.head()}")
            except Exception as parse_error:
                logging.error(f"Error parsing data for debugging: {parse_error}")
        
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
              Input('minlicks-slider', 'value'),
              Input('longlick-threshold', 'value'),
              Input('remove-longlicks-checkbox', 'value'),
              State('offset-array', 'value'),
              State('data-store', 'data'))
def make_bursthist_graph(jsonified_df, ibi_slider, minlicks_slider, longlick_slider, remove_longlicks, offset_key, jsonified_dict):
    # Use slider values directly
    ibi = ibi_slider
    minlicks = minlicks_slider
    longlick_th = longlick_slider
    remove_long = 'remove' in remove_longlicks
    if jsonified_df is None:
        raise PreventUpdate
    else:
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        
        if len(df) == 0:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(title="No data available")
            return fig
        
        # Check if we have offset data available and checkbox is checked
        if remove_long and offset_key and offset_key != 'none' and jsonified_dict:
            try:
                import json
                data_array = json.loads(jsonified_dict)
                if offset_key in data_array:
                    offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
                    offset_times = offset_df["licks"].to_list()
                    
                    # Check for potential cross-file contamination before processing
                    lick_times = df["licks"].to_list()
                    if abs(len(lick_times) - len(offset_times)) > 1:
                        # Severe mismatch suggests cross-file contamination, wait for proper sync
                        raise PreventUpdate
                    
                    lickdata = lickcalc(lick_times, offset=offset_times, burstThreshold=ibi, 
                                      minburstlength=minlicks, longlickThreshold=longlick_th, remove_longlicks=remove_long)
                else:
                    lickdata = lickcalc(df["licks"].to_list(), burstThreshold=ibi, minburstlength=minlicks)
            except Exception as e:
                lickdata = lickcalc(df["licks"].to_list(), burstThreshold=ibi, minburstlength=minlicks)
        else:
            lickdata = lickcalc(df["licks"].to_list(), burstThreshold=ibi, minburstlength=minlicks)
    
        bursts=lickdata['bLicks']
        
        if len(bursts) == 0:
            fig = go.Figure()
            fig.update_layout(title="No bursts found with current parameters")
            return fig

        # Additional safety check for valid burst data before creating histogram
        if not bursts or not all(isinstance(x, (int, float)) and x > 0 for x in bursts):
            fig = go.Figure()
            fig.update_layout(title="Invalid burst data")
            return fig

        try:
            fig = px.histogram(bursts,
                                range_x=[1, max(bursts)],
                                nbins=int(np.max(bursts)))
        except Exception as e:
            # If histogram creation fails, return empty figure
            fig = go.Figure()
            fig.update_layout(title="Error creating burst histogram")
            return fig
        
        # fig.update_traces(mode='markers', marker_line_width=2, marker_size=10)
        
        fig.update_layout(
            transition_duration=500,
            title={
                'text': "Burst frequency histogram",
                'x': 0.5,  # Center the title horizontally
                'xanchor': 'center'
            },
            xaxis_title="Burst size",
            yaxis_title="Frequency",
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
              Input('minlicks-slider', 'value'),
              Input('longlick-threshold', 'value'),
              Input('remove-longlicks-checkbox', 'value'),
              State('offset-array', 'value'),
              State('data-store', 'data'))
def make_burstprob_graph(jsonified_df, ibi_slider, minlicks_slider, longlick_slider, remove_longlicks, offset_key, jsonified_dict):
    # Use slider values directly
    ibi = ibi_slider
    minlicks = minlicks_slider
    longlick_th = longlick_slider
    remove_long = 'remove' in remove_longlicks
    if jsonified_df is None:
        raise PreventUpdate
    else:
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        
        if len(df) == 0:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(title="No data available")
            return fig, "0", "0.00", "0.00", "0.00", "0.00"
        
        lick_times = df["licks"].to_list()
        
        # Check if we have offset data available and checkbox is checked
        if remove_long and offset_key and offset_key != 'none' and jsonified_dict:
            try:
                import json
                data_array = json.loads(jsonified_dict)
                if offset_key in data_array:
                    offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
                    offset_times = offset_df["licks"].to_list()
                    lickdata = lickcalc(lick_times, offset=offset_times, burstThreshold=ibi, 
                                      minburstlength=minlicks, longlickThreshold=longlick_th, remove_longlicks=remove_long)
                else:
                    lickdata = lickcalc(lick_times, burstThreshold=ibi, minburstlength=minlicks)
            except Exception as e:
                lickdata = lickcalc(lick_times, burstThreshold=ibi, minburstlength=minlicks)
        else:
            lickdata = lickcalc(lick_times, burstThreshold=ibi, minburstlength=minlicks)
    
        if lickdata['burstprob'] is None or len(lickdata['burstprob'][0]) == 0:
            fig = go.Figure()
            fig.update_layout(title="No bursts found with current parameters")
            return fig, "0", "0.00", "0.00", "0.00", "0.00"
        
        # Check if we have enough bursts for Weibull analysis
        min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
        num_bursts = lickdata['bNum']
        
        if num_bursts < min_bursts_required:
            fig = go.Figure()
            fig.update_layout(
                title={
                    'text': f"Too few bursts for Weibull analysis ({num_bursts} < {min_bursts_required})",
                    'x': 0.5,  # Center the title horizontally
                    'xanchor': 'center'
                },
                annotations=[
                    dict(
                        x=0.5,
                        y=0.5,
                        xref="paper",
                        yref="paper",
                        text=f"Too few bursts ({num_bursts})<br>Weibull analysis requires ≥{min_bursts_required} bursts",
                        showarrow=False,
                        font=dict(size=16, color="gray"),
                        xanchor="center",
                        yanchor="middle"
                    )
                ],
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                height=400,  # Match other plot heights
                margin=dict(l=40, r=40, t=60, b=40)  # Standard margins
            )
            
            bNum = "{}".format(lickdata['bNum'])
            bMean = "{:.2f}".format(lickdata['bMean'])
            return fig, bNum, bMean, "N/A", "N/A", "N/A"
        
        # Check if Weibull parameters are None (too few bursts for Weibull analysis)
        if lickdata['weib_alpha'] is None or lickdata['weib_beta'] is None or lickdata['weib_rsq'] is None:
            fig = go.Figure()
            fig.update_layout(
                title={
                    'text': "Too few bursts for Weibull analysis",
                    'x': 0.5,  # Center the title horizontally
                    'xanchor': 'center'
                },
                annotations=[
                    dict(
                        x=0.5,
                        y=0.5,
                        xref="paper",
                        yref="paper",
                        text="Too few bursts<br>Weibull analysis requires more data",
                        showarrow=False,
                        font=dict(size=16, color="gray"),
                        xanchor="center",
                        yanchor="middle"
                    )
                ],
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                height=400,  # Match other plot heights
                margin=dict(l=40, r=40, t=60, b=40)  # Standard margins
            )
            
            bNum = "{}".format(lickdata['bNum'])
            bMean = "{:.2f}".format(lickdata['bMean'])
            return fig, bNum, bMean, "N/A", "N/A", "N/A"
        
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
        
        # Handle None values for Weibull parameters gracefully
        alpha = "{:.2f}".format(lickdata['weib_alpha']) if lickdata['weib_alpha'] is not None else "N/A"
        beta = "{:.2f}".format(lickdata['weib_beta']) if lickdata['weib_beta'] is not None else "N/A"
        rsq = "{:.2f}".format(lickdata['weib_rsq']) if lickdata['weib_rsq'] is not None else "N/A"

        return fig , bNum, bMean, alpha, beta, rsq

# Data collection callback to store figure data for export
@app.callback(Output('figure-data-store', 'data'),
              Input('lick-data', 'data'),
              Input('session-bin-slider-seconds', 'data'),
              Input('interburst-slider', 'value'),
              Input('minlicks-slider', 'value'),
              Input('longlick-threshold', 'value'),
              Input('remove-longlicks-checkbox', 'value'),
              Input('session-length-seconds', 'data'),
              State('data-store', 'data'),
              State('offset-array', 'value'))
def collect_figure_data(jsonified_df, bin_size_seconds, ibi_slider, minlicks_slider, longlick_slider, remove_longlicks, session_length_seconds, jsonified_dict, offset_key):
    """Collect underlying data from all figures for export"""
    import json
    # Use slider values directly
    ibi = ibi_slider
    minlicks = minlicks_slider
    longlick_th = longlick_slider
    remove_long = 'remove' in remove_longlicks
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
        
        # Session histogram data (use session_length_seconds for display range if specified)
        max_time = session_length_seconds if session_length_seconds and session_length_seconds > 0 else max(lick_times)
        hist_counts, hist_edges = np.histogram(lick_times, bins=int(max_time/bin_size_seconds) if max_time > 0 and bin_size_seconds > 0 else 1, range=(0, max_time))
        hist_centers = (hist_edges[:-1] + hist_edges[1:]) / 2
        figure_data['session_hist'] = {
            'bin_centers': hist_centers.tolist(),
            'counts': hist_counts.tolist(),
            'bin_size_seconds': bin_size_seconds
        }
        
        # Intraburst frequency data (ILIs)
        # Check if we have offset data available and checkbox is checked
        if remove_long and offset_key and offset_key != 'none' and jsonified_dict:
            try:
                data_array = json.loads(jsonified_dict)
                if offset_key in data_array:
                    offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
                    offset_times = offset_df["licks"].to_list()
                    lickdata = lickcalc(lick_times, offset=offset_times, burstThreshold=ibi, 
                                      minburstlength=minlicks, longlickThreshold=longlick_th, remove_longlicks=remove_long)
                else:
                    lickdata = lickcalc(lick_times, burstThreshold=ibi, minburstlength=minlicks)
            except Exception:
                lickdata = lickcalc(lick_times, burstThreshold=ibi, minburstlength=minlicks)
        else:
            lickdata = lickcalc(lick_times, burstThreshold=ibi, minburstlength=minlicks)
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
        # Use the same lickdata result from intraburst calculation for consistency
        burst_lickdata = lickdata
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
            
            # Get interburst intervals (IBIs) from lickcalc output
            interburst_intervals = burst_lickdata.get('IBIs', [])
            
            figure_data['burst_details'] = {
                'burst_numbers': list(range(1, len(burst_starts) + 1)),
                'n_licks': burst_licks,
                'start_times': burst_starts,
                'end_times': burst_ends,
                'durations': burst_durations
            }
            
            # Store interburst intervals separately for Excel export
            figure_data['interburst_intervals'] = {
                'intervals': interburst_intervals
            }
        else:
            figure_data['burst_details'] = None
            figure_data['interburst_intervals'] = None
        
        # Summary statistics - check minimum burst threshold for Weibull parameters
        min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
        num_bursts = burst_lickdata['bNum']
        
        # Calculate mean interburst time from lickcalc IBIs output
        mean_interburst_time = None
        ibis = burst_lickdata.get('IBIs', [])
        if ibis is not None and len(ibis) > 0:
            mean_interburst_time = np.mean(ibis)
        
        figure_data['summary_stats'] = {
            'total_licks': burst_lickdata['total'],
            'intraburst_freq': burst_lickdata['freq'],
            'n_bursts': burst_lickdata['bNum'],
            'mean_licks_per_burst': burst_lickdata['bMean'],
            'mean_interburst_time': mean_interburst_time,
            'weibull_alpha': burst_lickdata['weib_alpha'] if (burst_lickdata['weib_alpha'] is not None and num_bursts >= min_bursts_required) else None,
            'weibull_beta': burst_lickdata['weib_beta'] if (burst_lickdata['weib_beta'] is not None and num_bursts >= min_bursts_required) else None,
            'weibull_rsq': burst_lickdata['weib_rsq'] if (burst_lickdata['weib_rsq'] is not None and num_bursts >= min_bursts_required) else None,
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
                            
                        lickdata_with_offset = lickcalc(onset_times, offset=offset_times, longlickThreshold=longlick_th)
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
                        
                        # Update long lick statistics in summary (handle case where longlicks might be None)
                        longlicks_array = lickdata_with_offset["longlicks"]
                        figure_data['summary_stats']['n_long_licks'] = len(longlicks_array) if longlicks_array is not None else 0
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
