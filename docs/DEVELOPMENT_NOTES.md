# Development Notes

Last updated: 2026-07-25

## What changed in the UI/plots

- Remove long licks control moved below the microstructure stats table.
- Graph heights were reduced to a more compact layout.
- First-n ILIs slider alignment behavior was fixed by using a matching spacer in the adjacent graph column only when needed.
- Plot styling was modernized:
  - cleaner grid/axis defaults
  - updated colorway
  - plot background set to white to match app background
- Weibull observed data is now rendered as a staircase step line (not circle markers).

## Dependency/deployment decisions

- Dash was updated to 4.4.1.
- Azure staging deploy installs dependencies from requirements.txt.
- requirements.txt is treated as deployment source of truth.
- environment.yml was aligned to reduce drift:
  - dash-bootstrap-components >= 1.5.0
  - trompy >= 0.17.1

## Future continuation checklist

1. If continuing visual polish, tune one area at a time:
   - graph grid/axis contrast
   - color accents
   - table/control styling
2. If adding dark mode later, do it in two phases:
   - phase 1: app background + Plotly theme toggle
   - phase 2: controls/tables/tooltips polish
3. Before each release/deploy, run a smoke check:
   - upload and parse sample files
   - confirm all five core graphs render and update
   - confirm results table append and export still work

## Files touched in this phase

- layout.py
- callbacks/data_callbacks.py
- callbacks/graph_callbacks.py
- requirements.txt
- environment.yml
- CHANGELOG.md
