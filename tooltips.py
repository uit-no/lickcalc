"""
Tooltip definitions for the lickcalc web application.
This file contains all the help text and tooltip configurations.
"""

import dash_bootstrap_components as dbc
from dash import html

# Tooltip text definitions
TOOLTIP_TEXTS = {
    'binsize': (
        "Time window for grouping licks in the histogram. "
        "Smaller bins show more detailed temporal patterns, larger bins show overall trends."
    ),
    'ibi': (
        "The time threshold (in seconds) used to separate lick bursts. "
        "Licks separated by more than this interval are considered part of different bursts."
    ),
    'minlicks': (
        "The minimum number of licks required to be considered a burst. "
        "Groups with fewer licks than this threshold are excluded from burst analysis."
    ),
    'longlick': (
        "Duration threshold to classify a lick as 'long'. "
        "Licks longer than this duration are counted separately and may indicate different licking behavior."
    ),
    'total_licks': "Total number of lick events detected in the session.",
    'freq': (
        "Average licking frequency during bursts (licks per second). "
        "This measures how fast the animal licks when actively licking."
    ),
    'nlonglicks': (
        "Number of licks that exceed the long lick threshold duration. "
        "These may represent different licking behaviors or incomplete licks."
    ),
    'licks_burst': "Average number of licks in each burst episode.",
    'weibull_alpha': "Weibull distribution shape parameter. Describes the shape of the burst size distribution.",
    'weibull_beta': "Weibull distribution scale parameter. Related to the characteristic burst size.",
    'weibull_rsq': (
        "Goodness of fit (R²) for the Weibull distribution model. "
        "Values closer to 1.0 indicate better fit to the theoretical distribution."
    ),
    'onset_array': (
        "Select the data column containing lick onset timestamps. "
        "These are the times when licks begin."
    ),
    'offset_array': (
        "Select the data column containing lick offset timestamps. "
        "These are the times when licks end. Optional - used for lick duration analysis."
    ),
}

# Helper function to create a labeled element with tooltip
def create_labeled_element_with_tooltip(label_text, element_id, tooltip_key, placement="top"):
    """
    Creates a label with an info icon and tooltip.
    
    Args:
        label_text (str): The text to display as the label
        element_id (str): The ID for the help icon (should be unique)
        tooltip_key (str): Key to look up tooltip text in TOOLTIP_TEXTS
        placement (str): Tooltip placement ("top", "bottom", "left", "right")
    
    Returns:
        list: [label_div, tooltip_component]
    """
    label_div = html.Div([
        html.Span(label_text),
        html.Span(" ⓘ", id=element_id, style={"color": "#007bff", "cursor": "help", "margin-left": "5px"})
    ])
    
    tooltip = dbc.Tooltip(
        TOOLTIP_TEXTS[tooltip_key],
        target=element_id,
        placement=placement
    )
    
    return label_div, tooltip

# Helper function to create table cell with tooltip
def create_table_cell_with_tooltip(cell_text, cell_id, tooltip_key, placement="left"):
    """
    Creates a table cell with tooltip.
    
    Args:
        cell_text (str): The text to display in the cell
        cell_id (str): The ID for the help icon
        tooltip_key (str): Key to look up tooltip text in TOOLTIP_TEXTS
        placement (str): Tooltip placement
    
    Returns:
        list: [table_cell, tooltip_component]
    """
    table_cell = html.Td([
        html.Span(cell_text),
        html.Span(" ⓘ", id=cell_id, style={"color": "#007bff", "cursor": "help", "margin-left": "5px"})
    ])
    
    tooltip = dbc.Tooltip(
        TOOLTIP_TEXTS[tooltip_key],
        target=cell_id,
        placement=placement
    )
    
    return table_cell, tooltip

# Pre-configured tooltip components
def get_binsize_tooltip():
    return create_labeled_element_with_tooltip("Bin size (seconds)", "binsize-help", "binsize", "top")

def get_ibi_tooltip():
    return create_labeled_element_with_tooltip("Interburst lick interval (s)", "ibi-help", "ibi", "top")

def get_minlicks_tooltip():
    return create_labeled_element_with_tooltip("Minimum licks/burst", "minlicks-help", "minlicks", "top")

def get_longlick_tooltip():
    return create_labeled_element_with_tooltip("Long lick threshold (s)", "longlick-help", "longlick", "top")

def get_onset_tooltip():
    return create_labeled_element_with_tooltip("Onset array", "onset-help", "onset_array", "top")

def get_offset_tooltip():
    return create_labeled_element_with_tooltip("Offset array", "offset-help", "offset_array", "top")

# Table cell tooltips
def get_table_tooltips():
    """Returns all table cell tooltips as a list."""
    cells_and_tooltips = [
        create_table_cell_with_tooltip("Total licks", "total-licks-help", "total_licks"),
        create_table_cell_with_tooltip("Intraburst frequency", "freq-help", "freq"),
        create_table_cell_with_tooltip("No. of long licks", "nlonglicks-help", "nlonglicks"),
        create_table_cell_with_tooltip("Mean licks per burst", "licks-burst-help", "licks_burst"),
        create_table_cell_with_tooltip("Weibull: Alpha", "weibull-alpha-help", "weibull_alpha"),
        create_table_cell_with_tooltip("Weibull: Beta", "weibull-beta-help", "weibull_beta"),
        create_table_cell_with_tooltip("Weibull: r-squared", "weibull-rsq-help", "weibull_rsq"),
    ]
    
    # Separate cells and tooltips
    cells = [item[0] for item in cells_and_tooltips]
    tooltips = [item[1] for item in cells_and_tooltips]
    
    return cells, tooltips