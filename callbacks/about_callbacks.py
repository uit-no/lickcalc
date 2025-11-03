"""
About modal callbacks for lickcalc webapp.
"""
from dash import Input, Output, State

from app_instance import app
from _version import __version__


@app.callback(
    Output("about-modal", "is_open"),
    Output("about-version", "children"),
    Input("about-button", "n_clicks"),
    Input("about-close", "n_clicks"),
    State("about-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_about_modal(about_clicks, close_clicks, is_open):
    """Toggle the About modal and populate version information."""
    version_text = f"v{__version__}"
    
    # Toggle modal state
    if about_clicks or close_clicks:
        return not is_open, version_text
    
    return is_open, version_text
