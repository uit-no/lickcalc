"""
Export and results table callbacks for lickcalc webapp.
"""

import dash
from dash import dcc, html, Input, Output, State, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import io
import os
import tempfile
import zipfile
import logging
from datetime import datetime

from app_instance import app
from config_manager import config
try:
    from trompy import lickcalc  # type: ignore[import]
except Exception:
    def lickcalc(*args, **kwargs):  # type: ignore
        raise ImportError("The 'trompy' package is required for lick calculations. Please install it (see requirements.txt).")
from utils.file_parsers import (
    parse_medfile,
    parse_med_arraystyle,
    parse_csvfile,
    parse_ddfile,
    parse_kmfile,
    parse_ohrbets,
    parse_lsfile,
)
from utils import validate_onset_offset_pairs, calculate_mean_interburst_time
import base64
import re

def natural_sort_key(text):
    """
    Generate a key for natural sorting that handles numbers properly.
    Example: ['1', '2', '10', '20'] instead of ['1', '10', '2', '20']
    """
    def atoi(text):
        return int(text) if text.isdigit() else text.lower()
    return [atoi(c) for c in re.split(r'(\d+)', str(text))]

# Batch process placeholder callback
@app.callback(Output('table-status', 'children', allow_duplicate=True),
              Input('batch-process-btn', 'n_clicks'),
              prevent_initial_call=True)
def handle_batch_process(n_clicks):
    """Entry point for batch processing. Currently shows a status message.

    Future plan:
    - Open a modal to select a folder of files
    - Iterate over files using existing parsers and parameters
    - Append results to the results table and allow export
    """
    if not n_clicks:
        raise PreventUpdate

    status_msg = dbc.Alert(
        "Batch processing is not yet configured. This will process multiple files and add rows to the Results table.",
        color="secondary",
        dismissable=True,
        duration=4000
    )
    return status_msg

# Open/close batch modal
@app.callback(
    Output('batch-modal', 'is_open'),
    Input('batch-process-btn', 'n_clicks'),
    Input('batch-close-btn', 'n_clicks'),
    State('batch-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_batch_modal(open_clicks, close_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    return not is_open

# Clear batch modal data
@app.callback(
    Output('batch-upload', 'contents'),
    Output('batch-upload', 'filename'),
    Output('batch-export-excel', 'value'),
    Output('batch-include-all-sheets', 'value'),
    Output('batch-advanced-mode', 'value'),
    Output('batch-status', 'children'),
    Input('batch-clear-btn', 'n_clicks'),
    prevent_initial_call=True
)
def clear_batch_modal(n_clicks):
    """Reset all batch modal fields to their default values."""
    return None, None, [], ['all'], [], ""

# Display current file type in modal
@app.callback(
    Output('batch-file-type-display', 'children'),
    Input('input-file-type', 'value'),
)
def display_batch_file_type(file_type):
    # Handle None or missing file type by using default
    if not file_type:
        file_type = config.get('files.default_file_type', 'med')
    
    type_labels = {
        'med': 'Med (column)',
        'med_array': 'Med (array)',
        'csv': 'CSV/TXT',
        'ohrbets': 'OHRBETS',
        'dd': 'DD Lab',
        'km': 'KM Lab',
        'ls': 'LS Lab'
    }
    return type_labels.get(file_type, 'Not selected')

# Show uploaded file list in modal with parsing status
@app.callback(
    Output('batch-file-list', 'children'),
    Input('batch-upload', 'filename'),
    Input('batch-upload', 'contents'),
    Input('input-file-type', 'value'),
)
def show_batch_file_list(filenames, contents_list, input_file_type):
    if not filenames:
        return html.I("No files selected yet.")
    
    if not contents_list or not input_file_type:
        items = [html.Li(name) for name in (filenames if isinstance(filenames, list) else [filenames])]
        return html.Ul(items)
    
    # Ensure lists
    if not isinstance(filenames, list):
        filenames = [filenames]
    if not isinstance(contents_list, list):
        contents_list = [contents_list]
    
    # Try parsing each file and show status
    items = []
    for name, contents in zip(filenames, contents_list):
        try:
            # Quick parse attempt
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            f = io.StringIO(decoded.decode('utf-8', errors='ignore'))
            
            # Try to parse based on file type
            if input_file_type == 'med':
                data_array = parse_medfile(f)
            elif input_file_type == 'med_array':
                data_array = parse_med_arraystyle(f)
            elif input_file_type == 'csv':
                data_array = parse_csvfile(f)
            elif input_file_type == 'ohrbets':
                data_array = parse_ohrbets(f)
            elif input_file_type == 'dd':
                data_array = parse_ddfile(f)
            elif input_file_type == 'km':
                data_array = parse_kmfile(f)
            elif input_file_type == 'ls':
                tmp = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv')
                try:
                    tmp.write(decoded)
                    tmp.close()
                    data_array = parse_lsfile(tmp.name)
                finally:
                    try:
                        os.remove(tmp.name)
                    except Exception:
                        pass
            else:
                data_array = {}
            
            # Check if parse was successful
            if data_array and len(data_array) > 0:
                items.append(html.Li([
                    html.Span("✓ ", style={'color': 'green', 'fontWeight': 'bold'}),
                    html.Span(name, style={'color': 'green'})
                ]))
            else:
                items.append(html.Li([
                    html.Span("✗ ", style={'color': 'red', 'fontWeight': 'bold'}),
                    html.Span(name, style={'color': 'red'}),
                    html.Span(" (no data found)", style={'color': '#666', 'fontSize': '0.85em', 'fontStyle': 'italic'})
                ]))
        except Exception as e:
            items.append(html.Li([
                html.Span("✗ ", style={'color': 'red', 'fontWeight': 'bold'}),
                html.Span(name, style={'color': 'red'}),
                html.Span(f" (parse error)", style={'color': '#666', 'fontSize': '0.85em', 'fontStyle': 'italic'})
            ]))
    
    return html.Ul(items, style={'listStyleType': 'none', 'paddingLeft': '0'})

# Render advanced per-file selectors when Advanced mode is enabled
@app.callback(
    Output('batch-advanced-container', 'children'),
    Input('batch-advanced-mode', 'value'),
    Input('batch-upload', 'contents'),
    Input('batch-upload', 'filename'),
    Input('input-file-type', 'value'),
    prevent_initial_call=True
)
def render_batch_advanced_controls(adv_value, contents_list, filenames, input_file_type):
    try:
        if not adv_value or 'advanced' not in adv_value:
            return []
        if not contents_list or not filenames:
            return html.I("Upload files to configure per-file columns.")

        if not isinstance(contents_list, list):
            contents_list = [contents_list]
        if not isinstance(filenames, list):
            filenames = [filenames]

        controls = []
        union_columns = set()
        for contents, name in zip(contents_list, filenames):
            # Decode and parse quickly to get column names
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)

            # Build a file-like object when supported, else temp file for LS
            columns = []
            try:
                if input_file_type == 'med':
                    f = io.StringIO(decoded.decode('utf-8', errors='ignore'))
                    data_array = parse_medfile(f)
                elif input_file_type == 'med_array':
                    f = io.StringIO(decoded.decode('utf-8', errors='ignore'))
                    data_array = parse_med_arraystyle(f)
                elif input_file_type == 'csv':
                    f = io.StringIO(decoded.decode('utf-8', errors='ignore'))
                    data_array = parse_csvfile(f)
                elif input_file_type == 'ohrbets':
                    f = io.StringIO(decoded.decode('utf-8', errors='ignore'))
                    data_array = parse_ohrbets(f)
                elif input_file_type == 'dd':
                    f = io.StringIO(decoded.decode('utf-8', errors='ignore'))
                    data_array = parse_ddfile(f)
                elif input_file_type == 'km':
                    f = io.StringIO(decoded.decode('utf-8', errors='ignore'))
                    data_array = parse_kmfile(f)
                elif input_file_type == 'ls':
                    tmp = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv')
                    try:
                        tmp.write(decoded)
                        tmp.close()
                        data_array = parse_lsfile(tmp.name)
                    finally:
                        try:
                            os.remove(tmp.name)
                        except Exception:
                            pass
                else:
                    data_array = {}
            except Exception:
                data_array = {}

            if isinstance(data_array, dict):
                columns = list(data_array.keys())
            else:
                columns = []
            union_columns.update(columns)

            onset_dropdown = dcc.Dropdown(
                id={'type': 'batch-onset-multi', 'file': name},
                options=[{'label': col, 'value': col} for col in sorted(columns, key=natural_sort_key)],
                value=[],
                multi=True,
                placeholder='Select onset column(s)'
            )
            offset_dropdown = dcc.Dropdown(
                id={'type': 'batch-offset-multi', 'file': name},
                options=[{'label': col, 'value': col} for col in sorted(columns, key=natural_sort_key)],
                value=[],
                multi=True,
                placeholder='Select offset column(s) (optional)'
            )
            controls.append(
                dbc.Card([
                    dbc.CardHeader(html.Strong(str(name))),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([html.Label('Onset columns'), onset_dropdown], width=6),
                            dbc.Col([html.Label('Offset columns (optional)'), offset_dropdown], width=6),
                        ])
                    ], style={'paddingTop': '8px', 'paddingBottom': '8px'})
                ], style={'marginBottom': '8px'})
            )

        # Prepend global controls for quick apply-to-all
        global_controls = dbc.Card([
            dbc.CardHeader(html.Strong("Global selections")),
            dbc.CardBody([
                html.P("Pick columns once and apply to all files. Values not present in a file are ignored.", style={'color': '#6c757d'}),
                dbc.Row([
                    dbc.Col([
                        html.Label('Global onset columns'),
                        dcc.Dropdown(
                            id='batch-global-onset',
                            options=[{'label': c, 'value': c} for c in sorted(union_columns, key=natural_sort_key)],
                            value=[],
                            multi=True,
                            placeholder='Select onset column(s)'
                        )
                    ], width=6),
                    dbc.Col([
                        html.Label('Global offset columns (optional)'),
                        dcc.Dropdown(
                            id='batch-global-offset',
                            options=[{'label': c, 'value': c} for c in sorted(union_columns, key=natural_sort_key)],
                            value=[],
                            multi=True,
                            placeholder='Select offset column(s)'
                        )
                    ], width=6),
                ], className='g-2'),
                html.Div([
                    dbc.Button("Apply to all files", id='batch-apply-global', color='secondary', size='sm', className='mt-2')
                ])
            ])
        ], style={'marginBottom': '10px'})

        return [global_controls] + controls
    except Exception:
        return []

# Apply global selections to all per-file dropdowns
@app.callback(
    Output({'type': 'batch-onset-multi', 'file': ALL}, 'value'),
    Output({'type': 'batch-offset-multi', 'file': ALL}, 'value'),
    Input('batch-apply-global', 'n_clicks'),
    State('batch-global-onset', 'value'),
    State('batch-global-offset', 'value'),
    State({'type': 'batch-onset-multi', 'file': ALL}, 'options'),
    State({'type': 'batch-offset-multi', 'file': ALL}, 'options'),
    prevent_initial_call=True
)
def apply_global_to_all(n_clicks, global_onsets, global_offsets, onset_options_list, offset_options_list):
    if not n_clicks:
        raise PreventUpdate
    # Helper to filter selected values by available options for each file
    def _filter_values(selected, options):
        if not options:
            return []
        allowed = set([opt.get('value') for opt in options if isinstance(opt, dict) and 'value' in opt])
        return [v for v in (selected or []) if v in allowed]

    onset_values = [
        _filter_values(global_onsets, opts) for opts in (onset_options_list or [])
    ]
    offset_values = [
        _filter_values(global_offsets, opts) for opts in (offset_options_list or [])
    ]
    return onset_values, offset_values

# Process uploaded files using current settings and append rows
@app.callback(
    Output('results-table-store', 'data', allow_duplicate=True),
    Output('batch-status', 'children', allow_duplicate=True),
    Output('download-batch-zip', 'data'),
    Input('batch-start-btn', 'n_clicks'),
    State('batch-upload', 'contents'),
    State('batch-upload', 'filename'),
    State('batch-export-excel', 'value'),
    # Current settings
    State('interburst-slider', 'value'),
    State('minlicks-slider', 'value'),
    State('longlick-threshold', 'value'),
    State('remove-longlicks-checkbox', 'value'),
    State('input-file-type', 'value'),
    State('results-table-store', 'data'),
    # Epoch selection states
    State('division-number', 'value'),
    State('division-method', 'value'),
    State('n-bursts-number', 'value'),
    State('session-length-seconds', 'data'),
    State('between-start-seconds', 'data'),
    State('between-stop-seconds', 'data'),
    # Trial-based states
    State('trial-detection-method', 'value'),
    State('trial-min-iti', 'value'),
    State('trial-exclude-last-burst', 'value'),
    # Export preferences to mirror single-file export
    State('export-data-checklist', 'value'),
    State('animal-id-input', 'value'),
    State('session-bin-slider-seconds', 'data'),
    State('batch-include-all-sheets', 'value'),
    # Advanced mode selections
    State('batch-advanced-mode', 'value'),
    State({'type': 'batch-onset-multi', 'file': ALL}, 'value'),
    State({'type': 'batch-onset-multi', 'file': ALL}, 'id'),
    State({'type': 'batch-offset-multi', 'file': ALL}, 'value'),
    State({'type': 'batch-offset-multi', 'file': ALL}, 'id'),
    prevent_initial_call=True
)
def batch_process_files(n_clicks, contents_list, filenames, export_opts, ibi, minlicks, longlick_th, remove_long_vals, input_file_type, existing_data,
                        division_number=None, division_method='time', n_bursts_number=3, session_length_seconds=None,
                        between_start=None, between_stop=None,
                        trial_detection_method=None, trial_min_iti=None, trial_crop_last_burst=None,
                        selected_export=None, animal_id_base=None, bin_size_seconds=None, include_all_vals=None,
                        adv_mode=None, onset_values_list=None, onset_ids=None, offset_values_list=None, offset_ids=None):
    if not n_clicks:
        raise PreventUpdate
    if not contents_list or not filenames:
        return dash.no_update, dbc.Alert("Please select one or more files first.", color="warning", dismissable=True)

    if not isinstance(contents_list, list):
        contents_list = [contents_list]
    if not isinstance(filenames, list):
        filenames = [filenames]

    remove_long = 'remove' in (remove_long_vals or [])

    updated_data = existing_data.copy() if existing_data else []
    processed = 0
    added_rows = 0
    errors = []
    excel_files = []  # list of tuples (filename, bytes)

    total_files = len(filenames)
    # Prepare lookup of advanced selections per file
    advanced_enabled = adv_mode is not None and ('advanced' in (adv_mode or []))
    onset_by_file = {}
    offset_by_file = {}
    if advanced_enabled and onset_values_list is not None and onset_ids is not None:
        for vals, cid in zip(onset_values_list, onset_ids):
            try:
                fname = cid.get('file') if isinstance(cid, dict) else None
                if fname is not None:
                    onset_by_file[str(fname)] = vals or []
            except Exception:
                continue
    if advanced_enabled and offset_values_list is not None and offset_ids is not None:
        for vals, cid in zip(offset_values_list, offset_ids):
            try:
                fname = cid.get('file') if isinstance(cid, dict) else None
                if fname is not None:
                    offset_by_file[str(fname)] = vals or []
            except Exception:
                continue

    for contents, name in zip(contents_list, filenames):
        try:
            # Decode content
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            f = io.StringIO(decoded.decode('utf-8', errors='ignore'))

            # Parse based on selected type
            # Parse based on selected type (ordered to mirror dropdown: med, med_array, csv, ohrbets, dd, km, ls)
            if input_file_type == 'med':
                data_array = parse_medfile(f)
            elif input_file_type == 'med_array':
                data_array = parse_med_arraystyle(f)
            elif input_file_type == 'csv':
                data_array = parse_csvfile(f)
            elif input_file_type == 'ohrbets':
                data_array = parse_ohrbets(f)
            elif input_file_type == 'dd':
                data_array = parse_ddfile(f)
            elif input_file_type == 'km':
                data_array = parse_kmfile(f)
            elif input_file_type == 'ls':
                # LS parser expects a file path; write contents to a temporary file
                tmp = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv')
                try:
                    tmp.write(decoded)
                    tmp.close()
                    data_array = parse_lsfile(tmp.name)
                finally:
                    try:
                        os.remove(tmp.name)
                    except Exception:
                        pass
            else:
                raise ValueError(f"Unknown file type: {input_file_type}")

            # Choose onset column and optional offset
            cols = list(data_array.keys())
            if not cols:
                raise ValueError("No columns found after parsing")

            # Default onset key selection similar to single-file handler
            onset_key = None
            for cand in ['licks', 'onset', 'timestamps', 'time', 'Col. 1', cols[0]]:
                if cand in cols:
                    onset_key = cand
                    break
            if onset_key is None:
                onset_key = cols[0]

            offset_key = None
            for cand in ['offset', 'offsets', 'end', 'stop', 'Col. 2']:
                if cand in cols and cand != onset_key:
                    offset_key = cand
                    break

            # Convert JSON strings to arrays
            df_on = pd.read_json(io.StringIO(data_array[onset_key]), orient='split')
            lick_times = df_on['licks'].to_list()
            if not lick_times:
                raise ValueError("Empty onset array")

            # Attempt robust auto-detection of offset in batch mode
            def _is_valid_offset_candidate(col_key: str) -> bool:
                if col_key == onset_key:
                    return False
                try:
                    df_off_c = pd.read_json(io.StringIO(data_array[col_key]), orient='split')
                    off_times = df_off_c['licks'].to_list()
                    # Accept equal or off-by-one length
                    if abs(len(lick_times) - len(off_times)) > 1:
                        return False
                    # For each pair, require: off[i] >= onset[i] and if onset[i+1] exists then off[i] <= onset[i+1]
                    n = min(len(lick_times), len(off_times))
                    for i in range(n):
                        if off_times[i] < lick_times[i]:
                            return False
                        if i + 1 < len(lick_times) and off_times[i] > lick_times[i + 1]:
                            return False
                    return True
                except Exception:
                    return False

            # If name-based match failed, scan other columns
            if not offset_key:
                # Prefer name-like candidates that pass validation
                preferred = [c for c in ['offset', 'offsets', 'end', 'stop', 'Col. 2'] if c in cols and c != onset_key]
                for cand in preferred:
                    if _is_valid_offset_candidate(cand):
                        offset_key = cand
                        break
                # Else any other column that passes validation
                if not offset_key:
                    for col in cols:
                        if _is_valid_offset_candidate(col):
                            offset_key = col
                            break

            offset_times = []
            if offset_key:
                df_off = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
                offset_times = df_off['licks'].to_list()
                # Align arrays if off-by-one
                if len(lick_times) - len(offset_times) == 1:
                    lick_times = lick_times[:-1]
                elif len(lick_times) != len(offset_times):
                    min_len = min(len(lick_times), len(offset_times))
                    lick_times = lick_times[:min_len]
                    offset_times = offset_times[:min_len]

            # Build list of (onset_key, lick_times, offset_times) to process
            pairs_to_process = []
            if advanced_enabled and str(name) in onset_by_file and onset_by_file[str(name)]:
                selected_onsets = onset_by_file[str(name)]
                selected_offsets = offset_by_file.get(str(name), [])

                # Helper to choose a compatible offset for a given onset
                def choose_offset_for_onset(onset_k: str):
                    if not selected_offsets:
                        return None
                    for cand in selected_offsets:
                        if cand not in data_array or cand == onset_k:
                            continue
                        try:
                            df_off_c = pd.read_json(io.StringIO(data_array[cand]), orient='split')
                            off_times = df_off_c['licks'].to_list()
                            df_on_c = pd.read_json(io.StringIO(data_array[onset_k]), orient='split')
                            on_times = df_on_c['licks'].to_list()
                            # Basic validation like earlier
                            if abs(len(on_times) - len(off_times)) > 1:
                                continue
                            ok = True
                            n = min(len(on_times), len(off_times))
                            for i in range(n):
                                if off_times[i] < on_times[i]:
                                    ok = False
                                    break
                                if i + 1 < len(on_times) and off_times[i] > on_times[i + 1]:
                                    ok = False
                                    break
                            if ok:
                                return cand
                        except Exception:
                            continue
                    return None

                for ok in selected_onsets:
                    if ok not in data_array:
                        continue
                    # Build per-onset lick/offset arrays
                    df_on_sel = pd.read_json(io.StringIO(data_array[ok]), orient='split')
                    lt = df_on_sel['licks'].to_list()
                    ot_list = []
                    off_sel_key = choose_offset_for_onset(ok)
                    if off_sel_key:
                        df_off_sel = pd.read_json(io.StringIO(data_array[off_sel_key]), orient='split')
                        ot_list = df_off_sel['licks'].to_list()
                        if len(lt) - len(ot_list) == 1:
                            lt = lt[:-1]
                        elif len(lt) != len(ot_list):
                            m = min(len(lt), len(ot_list))
                            lt = lt[:m]
                            ot_list = ot_list[:m]
                    pairs_to_process.append((ok, lt, ot_list))
            else:
                pairs_to_process.append((onset_key, lick_times, offset_times))

            rows_for_file = []

            # Process each selected onset/offset pair (or the default one)
            for onset_key, lick_times, offset_times in pairs_to_process:

                # Respect epoch selection
                if division_number == 'first_n_bursts':
                    enhanced = lickcalc(
                        licks=lick_times,
                        offset=offset_times if offset_times else [],
                        burstThreshold=ibi,
                        minburstlength=minlicks,
                        longlickThreshold=longlick_th,
                        only_return_first_n_bursts=n_bursts_number,
                        remove_longlicks=remove_long if offset_times else False
                    )
                    # Compute first-n metrics similar to single-file callback
                    burst_licks = enhanced.get('bLicks', [])
                    burst_start = enhanced.get('bStart', [])
                    burst_end = enhanced.get('bEnd', [])
                    all_ilis = enhanced.get('ilis', [])

                    total_licks_first_n = sum(burst_licks) if burst_licks else 0
                    start_time = burst_start[0] if burst_start else 0
                    end_time = burst_end[-1] if burst_end else 0
                    duration = end_time - start_time if burst_start and burst_end else 0

                    # Intraburst frequency from first n bursts
                    if burst_licks and all_ilis is not None and len(all_ilis) > 0:
                        end_of_nth_burst = total_licks_first_n
                        first_n_ilis = all_ilis[:end_of_nth_burst-1] if end_of_nth_burst > 1 else []
                        intraburst_ilis = first_n_ilis[first_n_ilis < ibi] if len(first_n_ilis) > 0 else []
                        if len(intraburst_ilis) > 0:
                            mean_ili = np.mean(intraburst_ilis)
                            intraburst_freq = 1.0 / mean_ili if mean_ili > 0 else 0
                        else:
                            intraburst_freq = 0
                    else:
                        intraburst_freq = 0

                    rows_for_file.append({
                        'id': f"{name}_F{n_bursts_number}",
                        'source_filename': f"{name} (First {n_bursts_number} bursts)",
                        'onset_array': onset_key,
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': duration,
                        'interburst_interval': ibi,
                        'min_burst_size': minlicks,
                        'longlick_threshold': longlick_th,
                        'total_licks': total_licks_first_n,
                        'intraburst_freq': intraburst_freq,
                        'n_bursts': enhanced.get('bNum', 0),
                        'mean_licks_per_burst': enhanced.get('bMean', 0),
                        'mean_interburst_time': np.mean(enhanced.get('IBIs', [])) if enhanced.get('IBIs') is not None and len(enhanced.get('IBIs', [])) > 0 else np.nan,
                        'weibull_alpha': np.nan,
                        'weibull_beta': np.nan,
                        'weibull_rsq': np.nan,
                        'n_long_licks': len(enhanced.get('longlicks', [])) if offset_times and enhanced.get('longlicks') is not None else 0,
                        'max_lick_duration': np.max(enhanced.get('licklength', [])) if offset_times and enhanced.get('licklength') is not None and len(enhanced.get('licklength', [])) > 0 else np.nan,
                        'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
                    })

                elif isinstance(division_number, int) and division_number > 1:
                    # Numeric divisions
                    if division_method == 'time':
                        enhanced = lickcalc(
                            licks=lick_times,
                            offset=offset_times if offset_times else [],
                            burstThreshold=ibi,
                            minburstlength=minlicks,
                            longlickThreshold=longlick_th,
                            time_divisions=division_number,
                            session_length=session_length_seconds if session_length_seconds and session_length_seconds > 0 else None,
                            remove_longlicks=remove_long if offset_times else False
                        )
                        if 'time_divisions' in enhanced:
                            total_session_duration = session_length_seconds if session_length_seconds and session_length_seconds > 0 else (max(lick_times) if lick_times else 0)
                            division_duration = total_session_duration / division_number if division_number else 0
                            min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                            for i, div in enumerate(enhanced['time_divisions']):
                                div_n_bursts = div['n_bursts']
                                division_start = i * division_duration
                                division_end = (i + 1) * division_duration
                                rows_for_file.append({
                                    'id': f"{name}_T{div['division_number']}",
                                    'source_filename': f"{name} (Time {div['division_number']}/{division_number}: {division_start:.0f}-{division_end:.0f}s)",
                                    'onset_array': onset_key,
                                    'start_time': division_start,
                                    'end_time': division_end,
                                    'duration': division_duration,
                                    'interburst_interval': ibi,
                                    'min_burst_size': minlicks,
                                    'longlick_threshold': longlick_th,
                                    'total_licks': div['total_licks'],
                                    'intraburst_freq': div['intraburst_freq'],
                                    'n_bursts': div['n_bursts'],
                                    'mean_licks_per_burst': div['mean_licks_per_burst'],
                                    'mean_interburst_time': div.get('mean_interburst_time', np.nan),
                                    'weibull_alpha': div['weibull_alpha'] if (div['weibull_alpha'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                                    'weibull_beta': div['weibull_beta'] if (div['weibull_beta'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                                    'weibull_rsq': div['weibull_rsq'] if (div['weibull_rsq'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                                    'n_long_licks': div['n_long_licks'],
                                    'max_lick_duration': div['max_lick_duration'],
                                    'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
                                })
                    else:  # division_method == 'bursts'
                        enhanced = lickcalc(
                            licks=lick_times,
                            offset=offset_times if offset_times else [],
                            burstThreshold=ibi,
                            minburstlength=minlicks,
                            longlickThreshold=longlick_th,
                            burst_divisions=division_number,
                            remove_longlicks=remove_long if offset_times else False
                        )
                        if 'burst_divisions' in enhanced:
                            min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                            for div in enhanced['burst_divisions']:
                                bursts_in_segment = div['end_burst'] - div['start_burst']
                                div_n_bursts = div['n_bursts']
                                rows_for_file.append({
                                    'id': f"{name}_B{div['division_number']}",
                                    'source_filename': f"{name} (Bursts {div['start_burst']+1}-{div['end_burst']}, {bursts_in_segment} bursts)",
                                    'onset_array': onset_key,
                                    'start_time': div['start_time'],
                                    'end_time': div['end_time'],
                                    'duration': div['duration'],
                                    'interburst_interval': ibi,
                                    'min_burst_size': minlicks,
                                    'longlick_threshold': longlick_th,
                                    'total_licks': div['total_licks'],
                                    'intraburst_freq': div['intraburst_freq'],
                                    'n_bursts': div['n_bursts'],
                                    'mean_licks_per_burst': div['mean_licks_per_burst'],
                                    'mean_interburst_time': div.get('mean_interburst_time', np.nan),
                                    'weibull_alpha': div['weibull_alpha'] if (div['weibull_alpha'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                                    'weibull_beta': div['weibull_beta'] if (div['weibull_beta'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                                    'weibull_rsq': div['weibull_rsq'] if (div['weibull_rsq'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                                    'n_long_licks': div['n_long_licks'],
                                    'max_lick_duration': div['max_lick_duration'],
                                    'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
                                })
                        else:
                            # No bursts case: still add placeholders for consistency
                            for i in range(division_number):
                                rows_for_file.append({
                                    'id': f"{name}_B{i+1}",
                                    'source_filename': f"{name} (Bursts {i+1}/{division_number} - no bursts found)",
                                    'onset_array': onset_key,
                                    'start_time': 0,
                                    'end_time': 0,
                                    'duration': 0,
                                    'interburst_interval': ibi,
                                    'min_burst_size': minlicks,
                                    'longlick_threshold': longlick_th,
                                    'total_licks': 0,
                                    'intraburst_freq': 0,
                                    'n_bursts': 0,
                                    'mean_licks_per_burst': 0,
                                    'weibull_alpha': 0,
                                    'weibull_beta': 0,
                                    'weibull_rsq': 0,
                                    'n_long_licks': 0,
                                    'max_lick_duration': 0,
                                    'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
                                })
                
                elif division_number == 'between':
                    # Between times analysis
                    start_time = between_start if between_start is not None else 0
                    stop_time = between_stop if between_stop is not None else (session_length_seconds if session_length_seconds else (max(lick_times) if lick_times else 0))
                    
                    # Validate times
                    if stop_time < start_time:
                        errors.append(f"{name}: Stop time ({stop_time}) must be greater than or equal to start time ({start_time})")
                        continue
                    
                    # Filter lick times to the specified range
                    filtered_lick_times = [t for t in lick_times if start_time <= t < stop_time]
                    
                    # Filter offset times to match (if applicable)
                    filtered_offset_times = None
                    if offset_times:
                        valid_indices = [i for i, t in enumerate(lick_times) if start_time <= t < stop_time]
                        filtered_offset_times = [offset_times[i] for i in valid_indices if i < len(offset_times)]
                        
                        # Adjust if filtered arrays are mismatched by 1
                        if len(filtered_lick_times) - len(filtered_offset_times) == 1:
                            filtered_lick_times = filtered_lick_times[:-1]
                        elif len(filtered_lick_times) != len(filtered_offset_times):
                            filtered_lick_times = filtered_lick_times[:len(filtered_offset_times)]
                    
                    # Calculate analysis for filtered time range
                    enhanced = lickcalc(
                        licks=filtered_lick_times,
                        offset=filtered_offset_times if filtered_offset_times else [],
                        burstThreshold=ibi,
                        minburstlength=minlicks,
                        longlickThreshold=longlick_th,
                        remove_longlicks=remove_long if filtered_offset_times else False
                    )
                    
                    min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                    num_bursts = enhanced.get('bNum', 0)
                    
                    rows_for_file.append({
                        'id': f"{name}_BT",
                        'source_filename': f"{name} (Between {start_time:.0f}-{stop_time:.0f}s)",
                        'onset_array': onset_key,
                        'start_time': start_time,
                        'end_time': stop_time,
                        'duration': stop_time - start_time,
                        'interburst_interval': ibi,
                        'min_burst_size': minlicks,
                        'longlick_threshold': longlick_th,
                        'total_licks': enhanced.get('total', 0),
                        'intraburst_freq': enhanced.get('freq', 0),
                        'n_bursts': enhanced.get('bNum', 0),
                        'mean_licks_per_burst': enhanced.get('bMean', 0),
                        'mean_interburst_time': np.mean(enhanced.get('IBIs', [])) if enhanced.get('IBIs') is not None and len(enhanced.get('IBIs', [])) > 0 else np.nan,
                        'weibull_alpha': enhanced.get('weib_alpha', np.nan) if (enhanced.get('weib_alpha') is not None and num_bursts >= min_bursts_required) else np.nan,
                        'weibull_beta': enhanced.get('weib_beta', np.nan) if (enhanced.get('weib_beta') is not None and num_bursts >= min_bursts_required) else np.nan,
                        'weibull_rsq': enhanced.get('weib_rsq', np.nan) if (enhanced.get('weib_rsq') is not None and num_bursts >= min_bursts_required) else np.nan,
                        'n_long_licks': len(enhanced.get('longlicks', [])) if filtered_offset_times and enhanced.get('longlicks') is not None else 0,
                        'max_lick_duration': np.max(enhanced.get('licklength', [])) if filtered_offset_times and enhanced.get('licklength') is not None and len(enhanced.get('licklength', [])) > 0 else np.nan,
                        'long_licks_removed': 'Yes' if (remove_long and filtered_offset_times) else 'No'
                    })

                else:
                    # Whole session
                    results = lickcalc(
                        licks=lick_times,
                        offset=offset_times if offset_times else [],
                        burstThreshold=ibi,
                        minburstlength=minlicks,
                        longlickThreshold=longlick_th,
                        remove_longlicks=remove_long if offset_times else False
                    )
                    start_time = 0
                    # Use session length from input if available, otherwise fall back to max lick time
                    if session_length_seconds and session_length_seconds > 0:
                        end_time = session_length_seconds
                    else:
                        end_time = max(lick_times) if (lick_times is not None and len(lick_times) > 0) else 0
                    min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                    num_bursts = results.get('bNum', 0)
                    rows_for_file.append({
                        'id': name,
                        'source_filename': name,
                        'onset_array': onset_key,
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': end_time - start_time,
                        'interburst_interval': ibi,
                        'min_burst_size': minlicks,
                        'longlick_threshold': longlick_th,
                        'total_licks': results.get('total', np.nan),
                        'intraburst_freq': results.get('freq', np.nan),
                        'n_bursts': results.get('bNum', np.nan),
                        'mean_licks_per_burst': results.get('bMean', np.nan),
                        'mean_interburst_time': np.mean(results.get('IBIs', [])) if results.get('IBIs') is not None and len(results.get('IBIs', [])) > 0 else np.nan,
                        'weibull_alpha': results.get('weib_alpha', np.nan) if (results.get('weib_alpha') is not None and num_bursts >= min_bursts_required) else np.nan,
                        'weibull_beta': results.get('weib_beta', np.nan) if (results.get('weib_beta') is not None and num_bursts >= min_bursts_required) else np.nan,
                        'weibull_rsq': results.get('weib_rsq', np.nan) if (results.get('weib_rsq') is not None and num_bursts >= min_bursts_required) else np.nan,
                        'n_long_licks': len(results.get('longlicks', [])) if offset_times else np.nan,
                        'max_lick_duration': np.max(results.get('licklength', [])) if offset_times and results.get('licklength') is not None and len(results.get('licklength', [])) > 0 else np.nan,
                        'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
                    })

            # Commit rows for this file
            if rows_for_file:
                updated_data.extend(rows_for_file)
                added_rows += len(rows_for_file)
                processed += 1

                # If export per file requested, create a full Excel per file (same as single-file export)
                if export_opts and 'export' in export_opts:
                    try:
                        # Build figure data analogous to collect_figure_data for this file (whole session)
                        file_licks = lick_times
                        file_offsets = offset_times if offset_times else []

                        # Histogram (session)
                        max_time = session_length_seconds if session_length_seconds and session_length_seconds > 0 else (max(file_licks) if (file_licks is not None and len(file_licks) > 0) else 0)
                        if not bin_size_seconds or bin_size_seconds <= 0:
                            # Sensible fallback bin size: 1s
                            bin_size_seconds = 1
                        hist_counts, hist_edges = np.histogram(file_licks, bins=int(max_time/bin_size_seconds) if max_time > 0 else 1, range=(0, max_time))
                        hist_centers = (hist_edges[:-1] + hist_edges[1:]) / 2

                        # Main lickcalc for bursts and ILIs (respect remove_long only if offsets available)
                        if ('remove' in (remove_long_vals or [])) and file_offsets:
                            main_lc = lickcalc(file_licks, offset=file_offsets, burstThreshold=ibi, minburstlength=minlicks, longlickThreshold=longlick_th, remove_longlicks=True)
                        else:
                            main_lc = lickcalc(file_licks, burstThreshold=ibi, minburstlength=minlicks)

                        # Intraburst frequency histogram
                        ilis = main_lc.get('ilis', []) if main_lc else []
                        ili_counts, ili_edges = np.histogram(ilis, bins=50, range=(0, 0.5)) if isinstance(ilis, (list, np.ndarray)) and len(ilis) > 0 else (np.array([]), np.array([0, 0.5]))
                        ili_centers = (ili_edges[:-1] + ili_edges[1:]) / 2 if len(ili_edges) > 1 else np.array([])

                        # Burst-related
                        bursts = main_lc.get('bLicks', []) if main_lc else []
                        if isinstance(bursts, (list, np.ndarray)) and len(bursts) > 0 and np.max(bursts) >= 1:
                            burst_counts, burst_edges = np.histogram(bursts, bins=int(np.max(bursts)), range=(1, max(bursts)))
                            burst_centers = (burst_edges[:-1] + burst_edges[1:]) / 2
                        else:
                            burst_counts, burst_centers = np.array([]), np.array([])

                        burstprob = main_lc.get('burstprob', ([], [])) if main_lc else ([], [])
                        b_starts = main_lc.get('bStart', []) if main_lc else []
                        b_ends = main_lc.get('bEnd', []) if main_lc else []
                        b_nums = main_lc.get('bNum', 0) if main_lc else 0
                        b_mean = main_lc.get('bMean', np.nan) if main_lc else np.nan

                        # Weibull guard
                        min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                        weib_alpha = main_lc.get('weib_alpha') if (main_lc and b_nums >= min_bursts_required) else None
                        weib_beta = main_lc.get('weib_beta') if (main_lc and b_nums >= min_bursts_required) else None
                        weib_rsq = main_lc.get('weib_rsq') if (main_lc and b_nums >= min_bursts_required) else None

                        # Lick lengths if offsets available and valid
                        lick_lengths_centers = np.array([])
                        lick_lengths_counts = np.array([])
                        n_long_licks = 'N/A (requires offset data)'
                        max_lick_duration = 'N/A (requires offset data)'
                        if file_offsets:
                            try:
                                validation = validate_onset_offset_pairs(file_licks, file_offsets)
                                if validation['valid']:
                                    v_on = validation['corrected_onset']
                                    v_off = validation['corrected_offset']
                                    lc_off = lickcalc(v_on, offset=v_off, longlickThreshold=longlick_th)
                                    licklength = lc_off.get('licklength', [])
                                    if isinstance(licklength, (list, np.ndarray)) and len(licklength) > 0:
                                        ll_counts, ll_edges = np.histogram(licklength, bins=np.arange(0, longlick_th, 0.01))
                                        lick_lengths_counts = ll_counts
                                        lick_lengths_centers = (ll_edges[:-1] + ll_edges[1:]) / 2
                                        longlicks_array = lc_off.get('longlicks')
                                        n_long_licks = len(longlicks_array) if longlicks_array is not None else 0
                                        max_lick_duration = np.max(licklength)
                            except Exception:
                                pass

                        # Prepare Excel
                        xls_buf = io.BytesIO()
                        with pd.ExcelWriter(xls_buf, engine='openpyxl') as writer:
                            # Summary
                            animal_id_for_file = (animal_id_base + '_' if animal_id_base else '') + str(name)
                            from datetime import datetime as _dt
                            summary_df = pd.DataFrame([
                                ['Animal ID', animal_id_for_file],
                                ['Source Filename', name],
                                ['Export Date', _dt.now().strftime('%Y-%m-%d %H:%M:%S')],
                                ['Total Licks', main_lc.get('total', 'N/A') if main_lc else 'N/A'],
                                ['Intraburst Frequency (Hz)', f"{main_lc.get('freq', 0):.3f}" if main_lc and main_lc.get('freq') else 'N/A'],
                                ['Number of Bursts', main_lc.get('bNum', 'N/A') if main_lc else 'N/A'],
                                ['Mean Licks per Burst', f"{b_mean:.2f}" if pd.notna(b_mean) else 'N/A'],
                                ['Weibull Alpha', 'N/A (insufficient bursts)' if weib_alpha is None else f"{weib_alpha:.3f}"],
                                ['Weibull Beta', 'N/A (insufficient bursts)' if weib_beta is None else f"{weib_beta:.3f}"],
                                ['Weibull R-squared', 'N/A (insufficient bursts)' if weib_rsq is None else f"{weib_rsq:.3f}"],
                                ['Number of Long Licks', n_long_licks],
                                ['Maximum Lick Duration (s)', f"{max_lick_duration:.4f}" if isinstance(max_lick_duration, (int, float)) else max_lick_duration]
                            ], columns=['Property', 'Value'])
                            summary_df.to_excel(writer, sheet_name='Summary', index=False)

                            include_all = include_all_vals is not None and 'all' in include_all_vals
                            # Session Histogram
                            if include_all or (selected_export and 'session_hist' in selected_export):
                                if len(hist_centers) > 0:
                                    pd.DataFrame({'Time_Bin_Center_s': hist_centers, 'Lick_Count': hist_counts}).to_excel(writer, sheet_name='Session_Histogram', index=False)

                            # Intraburst Frequency
                            if include_all or (selected_export and 'intraburst_freq' in selected_export):
                                if len(ili_centers) > 0:
                                    pd.DataFrame({'ILI_Bin_Center_s': ili_centers, 'Frequency': ili_counts}).to_excel(writer, sheet_name='Intraburst_Frequency', index=False)

                            # Lick Lengths
                            if (include_all or (selected_export and 'lick_lengths' in selected_export)) and len(lick_lengths_centers) > 0:
                                pd.DataFrame({'Duration_Bin_Center_s': lick_lengths_centers, 'Frequency': lick_lengths_counts}).to_excel(writer, sheet_name='Lick_Lengths', index=False)

                            # Burst Histogram
                            if include_all or (selected_export and 'burst_hist' in selected_export):
                                if len(burst_centers) > 0:
                                    pd.DataFrame({'Burst_Size': burst_centers, 'Frequency': burst_counts}).to_excel(writer, sheet_name='Burst_Histogram', index=False)

                            # Burst Probability
                            if include_all or (selected_export and 'burst_prob' in selected_export):
                                if burstprob and isinstance(burstprob, (list, tuple)) and len(burstprob) == 2 and len(burstprob[0]) > 0:
                                    pd.DataFrame({'Burst_Size': burstprob[0], 'Probability': burstprob[1]}).to_excel(writer, sheet_name='Burst_Probability', index=False)

                            # Burst Details
                            if include_all or (selected_export and 'burst_details' in selected_export):
                                if len(b_starts) > 0:
                                    pd.DataFrame({
                                        'Burst_Number': list(range(1, len(b_starts) + 1)),
                                        'N_Licks': bursts,
                                        'Start_Time_s': b_starts,
                                        'End_Time_s': b_ends,
                                        'Duration_s': [end - start for start, end in zip(b_starts, b_ends)]
                                    }).to_excel(writer, sheet_name='Burst_Details', index=False)

                        xls_buf.seek(0)
                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        safe_name = str(name).replace('/', '_').replace('\\', '_')
                        excel_name = f"lickcalc_{safe_name}_{ts}.xlsx"
                        excel_files.append((excel_name, xls_buf.read()))
                    except Exception as ex:
                        errors.append(f"{name}: Excel export failed - {str(ex)}")

        except Exception as e:
            errors.append(f"{name}: {str(e)} - Try selecting a different file type if parsing failed.")

    status_children = []
    if processed:
        status_children.append(dbc.Alert(f"✅ Processed {processed} file(s), added {added_rows} row(s)", color="success", dismissable=True, duration=5000))
        # Add a simple progress bar snapshot
        progress_pct = int((processed / total_files) * 100) if total_files else 0
        status_children.append(
            dbc.Progress(
                value=progress_pct,
                color="success" if not errors else "warning",
                striped=False,
                animated=False,
                label=f"{processed}/{total_files} files"
            )
        )
    if errors:
        error_content = [
            html.H5("⚠️ Some files could not be processed", className="alert-heading"),
            html.Hr(),
        ]
        for error in errors:
            error_content.append(html.P(error, className="mb-1"))
        error_content.append(html.Hr())
        error_content.append(html.P([
            html.Strong("Tip: "),
            "If files failed to parse, try changing the File Type dropdown in this modal to match your data format."
        ], className="mb-0"))
        status_children.append(dbc.Alert(error_content, color="warning", dismissable=True))

    # If Excel files were created, zip and trigger download
    if excel_files:
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
            for fname, fbytes in excel_files:
                zf.writestr(fname, fbytes)
        zip_buf.seek(0)
        zip_name = f"lickcalc_batch_excels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        return updated_data, status_children, dcc.send_bytes(zip_buf.getvalue(), zip_name)

    return updated_data, status_children, None

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
                
                # Check minimum burst threshold for Weibull analysis in export
                min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                export_n_bursts = stats.get('n_bursts', 0)
                
                # Format Weibull parameters based on burst threshold
                weibull_alpha_text = 'N/A (insufficient bursts)' if export_n_bursts < min_bursts_required else (f"{stats.get('weibull_alpha', 'N/A'):.3f}" if stats.get('weibull_alpha') else 'N/A')
                weibull_beta_text = 'N/A (insufficient bursts)' if export_n_bursts < min_bursts_required else (f"{stats.get('weibull_beta', 'N/A'):.3f}" if stats.get('weibull_beta') else 'N/A')
                weibull_rsq_text = 'N/A (insufficient bursts)' if export_n_bursts < min_bursts_required else (f"{stats.get('weibull_rsq', 'N/A'):.3f}" if stats.get('weibull_rsq') else 'N/A')
                
                summary_df = pd.DataFrame([
                    ['Animal ID', animal_id],
                    ['Source Filename', source_filename if source_filename else 'N/A'],
                    ['Export Date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    ['Total Licks', stats.get('total_licks', 'N/A')],
                    ['Intraburst Frequency (Hz)', f"{stats.get('intraburst_freq', 'N/A'):.3f}" if stats.get('intraburst_freq') else 'N/A'],
                    ['Number of Bursts', stats.get('n_bursts', 'N/A')],
                    ['Mean Licks per Burst', f"{stats.get('mean_licks_per_burst', 'N/A'):.2f}" if stats.get('mean_licks_per_burst') else 'N/A'],
                    ['Mean Interburst Interval (s)', f"{stats.get('mean_interburst_time', 'N/A'):.3f}" if stats.get('mean_interburst_time') else 'N/A'],
                    ['Weibull Alpha', weibull_alpha_text],
                    ['Weibull Beta', weibull_beta_text],
                    ['Weibull R-squared', weibull_rsq_text],
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
            
            # Add interburst intervals sheet if selected
            if 'interburst_intervals' in selected_data and figure_data.get('interburst_intervals') and figure_data['interburst_intervals'].get('intervals'):
                ibis = figure_data['interburst_intervals']['intervals']
                df = pd.DataFrame({
                    'Interval_Number': list(range(1, len(ibis) + 1)),
                    'Interburst_Interval_s': ibis
                })
                df.to_excel(writer, sheet_name='Interburst_Intervals', index=False)
        
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
              State('n-bursts-number', 'value'),
              State('session-length-seconds', 'data'),
              State('data-store', 'data'),
              State('onset-array', 'value'),
              State('offset-array', 'value'),
              State('interburst-slider', 'value'),
              State('minlicks-slider', 'value'),
              State('longlick-threshold', 'value'),
              State('remove-longlicks-checkbox', 'value'),
              State('between-start-seconds', 'data'),
              State('between-stop-seconds', 'data'),
              State('trial-detection-method', 'value'),
              State('trial-min-iti', 'value'),
              State('trial-exclude-last-burst', 'value'),
              prevent_initial_call=True)
def add_to_results_table(n_clicks, animal_id, figure_data, existing_data, source_filename, 
                        division_number, division_method, n_bursts_number, session_length_seconds, data_store, onset_key, offset_key,
                        ibi_slider, minlicks_slider, longlick_slider, remove_longlicks, between_start, between_stop,
                        trial_detection_method, trial_min_iti, trial_crop_last_burst):
    """Add current analysis results to the results table with optional divisions"""
    # Use slider values directly
    ibi = ibi_slider
    minlicks = minlicks_slider
    longlick_th = longlick_slider
    remove_long = 'remove' in remove_longlicks
    
    if n_clicks == 0 or not figure_data or 'summary_stats' not in figure_data:
        raise PreventUpdate
    
    try:
        # If no division (whole session), recalculate with proper onset/offset validation
        if division_number == 'whole_session':
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
            
            # Use session length from input box (already converted to seconds), or fall back to max lick time
            if session_length_seconds and session_length_seconds > 0:
                end_time = session_length_seconds
            else:
                end_time = max(lick_times) if lick_times else 0
            
            # Recalculate stats with proper onset/offset validation
            try:
                # Use enhanced lickcalc with current parameters to get accurate long lick stats
                enhanced_results = lickcalc(
                    licks=lick_times,
                    offset=offset_times if offset_times else [],
                    burstThreshold=ibi,
                    minburstlength=minlicks,
                    longlickThreshold=longlick_th,
                    remove_longlicks=remove_long if offset_times else False
                )
                
                # Create new row with recalculated stats
                # Check minimum burst threshold for Weibull analysis
                min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                num_bursts = enhanced_results.get('bNum', 0)
                
                new_row = {
                    'id': animal_id or 'Unknown',
                    'source_filename': source_filename if source_filename else 'N/A',
                    'onset_array': onset_key,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'interburst_interval': ibi,
                    'min_burst_size': minlicks,
                    'longlick_threshold': longlick_th,
                    'total_licks': enhanced_results.get('total', np.nan),
                    'intraburst_freq': enhanced_results.get('freq', np.nan),
                    'n_bursts': enhanced_results.get('bNum', np.nan),
                    'mean_licks_per_burst': enhanced_results.get('bMean', np.nan),
                    'mean_interburst_time': np.mean(enhanced_results.get('IBIs', [])) if enhanced_results.get('IBIs') is not None and len(enhanced_results.get('IBIs', [])) > 0 else np.nan,
                    'weibull_alpha': enhanced_results.get('weib_alpha', np.nan) if (enhanced_results.get('weib_alpha') is not None and num_bursts >= min_bursts_required) else np.nan,
                    'weibull_beta': enhanced_results.get('weib_beta', np.nan) if (enhanced_results.get('weib_beta') is not None and num_bursts >= min_bursts_required) else np.nan,
                    'weibull_rsq': enhanced_results.get('weib_rsq', np.nan) if (enhanced_results.get('weib_rsq') is not None and num_bursts >= min_bursts_required) else np.nan,
                    'n_long_licks': len(enhanced_results.get('longlicks', [])) if offset_times else np.nan,
                    'max_lick_duration': np.max(enhanced_results.get('licklength', [])) if offset_times and enhanced_results.get('licklength') is not None and len(enhanced_results.get('licklength', [])) > 0 else np.nan,
                    'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
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
                        temp_results = lickcalc(lick_times, offset=offset_times, longlickThreshold=longlick_th)
                        n_long_licks = len(temp_results.get('longlicks', []))
                        licklength_array = temp_results.get('licklength', [])
                        if licklength_array is not None and len(licklength_array) > 0:
                            max_lick_duration = np.max(licklength_array)
                    except Exception:
                        pass
                
                # Only use figure_data value if we haven't calculated it above
                if max_lick_duration is np.nan and isinstance(stats.get('max_lick_duration'), (int, float)):
                    max_lick_duration = stats.get('max_lick_duration')
                
                # Check minimum burst threshold for Weibull analysis in fallback case too
                min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                fallback_n_bursts = stats.get('n_bursts', 0)
                
                new_row = {
                    'id': animal_id or 'Unknown',
                    'source_filename': source_filename if source_filename else 'N/A',
                    'onset_array': onset_key,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'interburst_interval': ibi,
                    'min_burst_size': minlicks,
                    'longlick_threshold': longlick_th,
                    'total_licks': stats.get('total_licks', np.nan),
                    'intraburst_freq': stats.get('intraburst_freq', np.nan),
                    'n_bursts': stats.get('n_bursts', np.nan),
                    'mean_licks_per_burst': stats.get('mean_licks_per_burst', np.nan),
                    'mean_interburst_time': stats.get('mean_interburst_time', np.nan),
                    'weibull_alpha': stats.get('weibull_alpha', np.nan) if (stats.get('weibull_alpha') is not None and fallback_n_bursts >= min_bursts_required) else np.nan,
                    'weibull_beta': stats.get('weibull_beta', np.nan) if (stats.get('weibull_beta') is not None and fallback_n_bursts >= min_bursts_required) else np.nan,
                    'weibull_rsq': stats.get('weibull_rsq', np.nan) if (stats.get('weibull_rsq') is not None and fallback_n_bursts >= min_bursts_required) else np.nan,
                    'n_long_licks': n_long_licks,
                    'max_lick_duration': max_lick_duration,
                    'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
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
            
            # Calculate divisions using enhanced lickcalc function
            division_rows = []
            
            # Check if it's "First n bursts" analysis
            if division_number == 'first_n_bursts':
                # Calculate for first n bursts only
                enhanced_results = lickcalc(
                    licks=lick_times,
                    offset=offset_times if offset_times else [],
                    burstThreshold=ibi,
                    minburstlength=minlicks,
                    longlickThreshold=longlick_th,
                    only_return_first_n_bursts=n_bursts_number,
                    remove_longlicks=remove_long if offset_times else False
                )
                
                # Calculate correct values for first n bursts based on burst information
                burst_licks = enhanced_results.get('bLicks', [])  # Number of licks in each burst
                burst_start = enhanced_results.get('bStart', [])  # Start time of each burst
                burst_end = enhanced_results.get('bEnd', [])      # End time of each burst
                all_ilis = enhanced_results.get('ilis', [])      # All interlick intervals
                
                # Calculate total licks from first n bursts
                total_licks_first_n = sum(burst_licks) if burst_licks else 0
                
                # Calculate start and end times
                start_time = burst_start[0] if burst_start else 0
                end_time = burst_end[-1] if burst_end else 0
                duration = end_time - start_time if burst_start and burst_end else 0
                
                # Calculate intraburst frequency from first n bursts only (using only intraburst ILIs)
                if burst_licks and all_ilis is not None and len(all_ilis) > 0:
                    # Get the end index of the nth burst (total licks in first n bursts)
                    end_of_nth_burst = total_licks_first_n
                    # Get ILIs only from the first n bursts (ILIs array is one element shorter than licks)
                    first_n_ilis = all_ilis[:end_of_nth_burst-1] if end_of_nth_burst > 1 else []
                    
                    # Filter to include only intraburst ILIs (< interburst interval threshold)
                    intraburst_ilis = first_n_ilis[first_n_ilis < ibi] if len(first_n_ilis) > 0 else []
                    
                    if len(intraburst_ilis) > 0:
                        mean_intraburst_ili = np.mean(intraburst_ilis)
                        intraburst_freq = 1.0 / mean_intraburst_ili if mean_intraburst_ili > 0 else 0
                    else:
                        intraburst_freq = 0
                else:
                    intraburst_freq = 0
                
                # Create single row for first n bursts analysis
                # Note: Weibull parameters are excluded for first n bursts as they require full session data
                division_rows.append({
                    'id': f"{animal_id}_F{n_bursts_number}" if animal_id else f"F{n_bursts_number}",
                    'source_filename': f"{source_filename} (First {n_bursts_number} bursts)" if source_filename else f"First {n_bursts_number} bursts",
                    'onset_array': onset_key,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': duration,
                    'interburst_interval': ibi,
                    'min_burst_size': minlicks,
                    'longlick_threshold': longlick_th,
                    'total_licks': total_licks_first_n,
                    'intraburst_freq': intraburst_freq,
                    'n_bursts': enhanced_results.get('bNum', 0),
                    'mean_licks_per_burst': enhanced_results.get('bMean', 0),
                    'mean_interburst_time': np.mean(enhanced_results.get('IBIs', [])) if enhanced_results.get('IBIs') is not None and len(enhanced_results.get('IBIs', [])) > 0 else np.nan,
                    'weibull_alpha': np.nan,  # Excluded for first n bursts analysis
                    'weibull_beta': np.nan,   # Excluded for first n bursts analysis
                    'weibull_rsq': np.nan,    # Excluded for first n bursts analysis
                    'n_long_licks': len(enhanced_results.get('longlicks', [])) if offset_times and enhanced_results.get('longlicks') is not None else 0,
                    'max_lick_duration': np.max(enhanced_results.get('licklength', [])) if offset_times and enhanced_results.get('licklength') is not None and len(enhanced_results.get('licklength', [])) > 0 else np.nan,
                    'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
                })
            
            # Handle "Trial-based" analysis
            elif division_number == 'trial_based':
                from utils.calculations import detect_trials, analyze_trial
                
                # Get trial parameters
                min_iti = trial_min_iti if trial_min_iti and trial_min_iti > 0 else 60
                crop_last_burst = trial_crop_last_burst if trial_crop_last_burst else []
                detection_method = trial_detection_method or 'auto'
                
                # Detect trials (auto) or handle loaded trials (future)
                if detection_method == 'auto':
                    trial_info = detect_trials(lick_times, min_iti)
                else:
                    # For now, we don't support loading custom trial times here
                    raise Exception("'Load trial times' not implemented yet")
                
                if trial_info['n_trials'] == 0:
                    # Graceful fallback: treat the whole session as one trial
                    trial_info = {
                        'n_trials': 1,
                        'trial_boundaries': [(0, len(lick_times))],
                        'trial_start_times': [float(lick_times[0]) if lick_times else 0.0],
                        'trial_end_times': [float(lick_times[-1]) if lick_times else 0.0]
                    }
                
                # Analyze each trial
                for i, (start_idx, end_idx) in enumerate(trial_info['trial_boundaries']):
                    trial_stats = analyze_trial(
                        lick_times=np.array(lick_times),
                        lick_offsets=np.array(offset_times) if offset_times else None,
                        trial_idx=i,
                        start_idx=start_idx,
                        end_idx=end_idx,
                        ibi=ibi,
                        minlicks=minlicks,
                        longlick_th=longlick_th,
                        remove_long=remove_long if offset_times else False,
                        crop_last_burst='exclude' in crop_last_burst if isinstance(crop_last_burst, list) else False
                    )
                    
                    # Add to division rows
                    division_rows.append({
                        'id': f"{animal_id}_Trial{trial_stats['trial_number']}" if animal_id else f"Trial{trial_stats['trial_number']}",
                        'source_filename': f"{source_filename} (Trial {trial_stats['trial_number']}/{trial_info['n_trials']})" if source_filename else f"Trial {trial_stats['trial_number']}/{trial_info['n_trials']}",
                        'onset_array': onset_key,
                        'start_time': trial_stats['start_time'],
                        'end_time': trial_stats['end_time'],
                        'duration': trial_stats['duration'],
                        'interburst_interval': ibi,
                        'min_burst_size': minlicks,
                        'longlick_threshold': longlick_th,
                        'total_licks': trial_stats['total_licks'],
                        'intraburst_freq': trial_stats['intraburst_freq'],
                        'n_bursts': trial_stats['n_bursts'],
                        'mean_licks_per_burst': trial_stats['mean_licks_per_burst'],
                        'mean_interburst_time': trial_stats.get('mean_interburst_time', np.nan),
                        'weibull_alpha': trial_stats['weibull_alpha'],
                        'weibull_beta': trial_stats['weibull_beta'],
                        'weibull_rsq': trial_stats['weibull_rsq'],
                        'n_long_licks': trial_stats['n_long_licks'],
                        'max_lick_duration': trial_stats['max_lick_duration'],
                        'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
                    })
            
            # Handle "Between times" analysis
            elif division_number == 'between':
                # Get start and stop times, with validation
                start_time = between_start if between_start is not None else 0
                stop_time = between_stop if between_stop is not None else (session_length_seconds if session_length_seconds else (max(lick_times) if (lick_times is not None and len(lick_times) > 0) else 0))
                
                # Ensure stop is after start
                if stop_time < start_time:
                    raise Exception(f"Stop time ({stop_time}) must be greater than or equal to start time ({start_time})")
                
                # Filter lick times to the specified range
                filtered_lick_times = [t for t in lick_times if start_time <= t < stop_time]
                
                # Filter offset times to match (if applicable)
                filtered_offset_times = None
                if offset_times:
                    # Create list of valid indices where lick time is within range
                    valid_indices = [i for i, t in enumerate(lick_times) if start_time <= t < stop_time]
                    filtered_offset_times = [offset_times[i] for i in valid_indices if i < len(offset_times)]
                    
                    # Adjust if filtered arrays are mismatched by 1
                    if len(filtered_lick_times) - len(filtered_offset_times) == 1:
                        filtered_lick_times = filtered_lick_times[:-1]
                    elif len(filtered_lick_times) != len(filtered_offset_times):
                        filtered_lick_times = filtered_lick_times[:len(filtered_offset_times)]
                
                # Calculate analysis for filtered time range
                enhanced_results = lickcalc(
                    licks=filtered_lick_times,
                    offset=filtered_offset_times if filtered_offset_times else [],
                    burstThreshold=ibi,
                    minburstlength=minlicks,
                    longlickThreshold=longlick_th,
                    remove_longlicks=remove_long if filtered_offset_times else False
                )
                
                # Check minimum burst threshold for Weibull analysis
                min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                num_bursts = enhanced_results.get('bNum', 0)
                
                # Create single row for between times analysis
                division_rows.append({
                    'id': f"{animal_id}_BT" if animal_id else "BT",
                    'source_filename': f"{source_filename} (Between {start_time:.0f}-{stop_time:.0f}s)" if source_filename else f"Between {start_time:.0f}-{stop_time:.0f}s",
                    'onset_array': onset_key,
                    'start_time': start_time,
                    'end_time': stop_time,
                    'duration': stop_time - start_time,
                    'interburst_interval': ibi,
                    'min_burst_size': minlicks,
                    'longlick_threshold': longlick_th,
                    'total_licks': enhanced_results.get('total', 0),
                    'intraburst_freq': enhanced_results.get('freq', 0),
                    'n_bursts': enhanced_results.get('bNum', 0),
                    'mean_licks_per_burst': enhanced_results.get('bMean', 0),
                    'mean_interburst_time': np.mean(enhanced_results.get('IBIs', [])) if enhanced_results.get('IBIs') is not None and len(enhanced_results.get('IBIs', [])) > 0 else np.nan,
                    'weibull_alpha': enhanced_results.get('weib_alpha', np.nan) if (enhanced_results.get('weib_alpha') is not None and num_bursts >= min_bursts_required) else np.nan,
                    'weibull_beta': enhanced_results.get('weib_beta', np.nan) if (enhanced_results.get('weib_beta') is not None and num_bursts >= min_bursts_required) else np.nan,
                    'weibull_rsq': enhanced_results.get('weib_rsq', np.nan) if (enhanced_results.get('weib_rsq') is not None and num_bursts >= min_bursts_required) else np.nan,
                    'n_long_licks': len(enhanced_results.get('longlicks', [])) if filtered_offset_times and enhanced_results.get('longlicks') is not None else 0,
                    'max_lick_duration': np.max(enhanced_results.get('licklength', [])) if filtered_offset_times and enhanced_results.get('licklength') is not None and len(enhanced_results.get('licklength', [])) > 0 else np.nan,
                    'long_licks_removed': 'Yes' if (remove_long and filtered_offset_times) else 'No'
                })
                
            # Use enhanced lickcalc with division parameters for numeric divisions
            elif isinstance(division_number, int) and division_number > 1:
                if division_method == 'time':
                    # Calculate with time divisions
                    enhanced_results = lickcalc(
                        licks=lick_times,
                        offset=offset_times if offset_times else [],
                        burstThreshold=ibi,
                        minburstlength=minlicks,
                        longlickThreshold=longlick_th,
                        time_divisions=division_number,
                        session_length=session_length_seconds if session_length_seconds and session_length_seconds > 0 else None,
                        remove_longlicks=remove_long if offset_times else False
                    )
                
                # Convert trompy division results to webapp format
                if 'time_divisions' in enhanced_results:
                    # Determine the total session duration for proper time division calculation
                    total_session_duration = session_length_seconds if session_length_seconds and session_length_seconds > 0 else max(lick_times) if lick_times else 0
                    division_duration = total_session_duration / division_number
                    
                    for i, div in enumerate(enhanced_results['time_divisions']):
                        # Ensure divisions start from 0 and cover the full session
                        division_start = i * division_duration
                        division_end = (i + 1) * division_duration
                        
                        # Check minimum burst threshold for Weibull analysis
                        min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                        div_n_bursts = div['n_bursts']
                        
                        division_rows.append({
                            'id': f"{animal_id}_T{div['division_number']}" if animal_id else f"T{div['division_number']}",
                            'source_filename': f"{source_filename} (Time {div['division_number']}/{division_number}: {division_start:.0f}-{division_end:.0f}s)" if source_filename else f"Time {div['division_number']}/{division_number} ({division_start:.0f}-{division_end:.0f}s)",
                            'start_time': division_start,
                            'end_time': division_end,
                            'duration': division_duration,
                            'interburst_interval': ibi,
                            'min_burst_size': minlicks,
                            'longlick_threshold': longlick_th,
                            'total_licks': div['total_licks'],
                            'intraburst_freq': div['intraburst_freq'],
                            'n_bursts': div['n_bursts'],
                            'mean_licks_per_burst': div['mean_licks_per_burst'],
                            'mean_interburst_time': div.get('mean_interburst_time', np.nan),
                            'weibull_alpha': div['weibull_alpha'] if (div['weibull_alpha'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                            'weibull_beta': div['weibull_beta'] if (div['weibull_beta'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                            'weibull_rsq': div['weibull_rsq'] if (div['weibull_rsq'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                            'n_long_licks': div['n_long_licks'],
                            'max_lick_duration': div['max_lick_duration'],
                            'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
                        })
            
                elif division_method == 'bursts':
                    # Calculate with burst divisions
                    enhanced_results = lickcalc(
                        licks=lick_times,
                        offset=offset_times if offset_times else [],
                        burstThreshold=ibi,
                        minburstlength=minlicks,
                        longlickThreshold=longlick_th,
                        burst_divisions=division_number,
                        remove_longlicks=remove_long if offset_times else False
                    )
                    
                    # Convert trompy division results to webapp format
                    if 'burst_divisions' in enhanced_results:
                        for div in enhanced_results['burst_divisions']:
                            bursts_in_segment = div['end_burst'] - div['start_burst']
                            
                            # Check minimum burst threshold for Weibull analysis
                            min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                            div_n_bursts = div['n_bursts']
                            
                            division_rows.append({
                                'id': f"{animal_id}_B{div['division_number']}" if animal_id else f"B{div['division_number']}",
                                'source_filename': f"{source_filename} (Bursts {div['start_burst']+1}-{div['end_burst']}, {bursts_in_segment} bursts)" if source_filename else f"Bursts {div['start_burst']+1}-{div['end_burst']} ({bursts_in_segment} bursts)",
                                'start_time': div['start_time'],
                                'end_time': div['end_time'],
                                'duration': div['duration'],
                                'interburst_interval': ibi,
                                'min_burst_size': minlicks,
                                'longlick_threshold': longlick_th,
                                'total_licks': div['total_licks'],
                                'intraburst_freq': div['intraburst_freq'],
                                'n_bursts': div['n_bursts'],
                                'mean_licks_per_burst': div['mean_licks_per_burst'],
                                'mean_interburst_time': div.get('mean_interburst_time', np.nan),
                                'weibull_alpha': div['weibull_alpha'] if (div['weibull_alpha'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                                'weibull_beta': div['weibull_beta'] if (div['weibull_beta'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                                'weibull_rsq': div['weibull_rsq'] if (div['weibull_rsq'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                                'n_long_licks': div['n_long_licks'],
                                'max_lick_duration': div['max_lick_duration'],
                                'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
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
                                'interburst_interval': ibi,
                                'min_burst_size': minlicks,
                                'longlick_threshold': longlick_th,
                                'total_licks': 0,
                                'intraburst_freq': 0,
                                'n_bursts': 0,
                                'mean_licks_per_burst': 0,
                                'mean_interburst_time': np.nan,
                                'weibull_alpha': 0,
                                'weibull_beta': 0,
                                'weibull_rsq': 0,
                                'n_long_licks': 0,
                                'max_lick_duration': 0,
                                'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
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
                'interburst_interval': None,
                'min_burst_size': None,
                'longlick_threshold': None,
                'total_licks': None,
                'intraburst_freq': None,
                'n_bursts': None,
                'mean_licks_per_burst': None,
                'mean_interburst_time': None,
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
        numeric_columns = ['duration', 'total_licks', 'intraburst_freq', 'n_bursts', 'mean_licks_per_burst', 
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
