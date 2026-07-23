# lickcalc Repository Architecture Summary

Last updated: 2026-07-23

## 1) What this app is

lickcalc is a Dash web application for rodent licking microstructure analysis. It loads lick timestamp files from several lab-specific formats, computes burst-level metrics (via trompy), renders multiple analysis plots, and exports both summary and underlying plotted data to Excel.

Core external analysis engine: trompy.lickcalc.

## 2) Runtime architecture

### Entry and app construction

- app.py
  - Imports app instance from app_instance.py.
  - Sets app layout from layout.py.
  - Imports callbacks package to register all callbacks.
  - Runs Dash with debug/hot reload from config.

- app_instance.py
  - Builds one global Dash app instance.
  - Reads title/debug settings through config_manager.ConfigManager.
  - Exposes server = app.server for deployment.

### Callback registration strategy

- callbacks/__init__.py imports:
  - callbacks/config_callbacks.py
  - callbacks/data_callbacks.py
  - callbacks/graph_callbacks.py
  - callbacks/export_callbacks.py
  - callbacks/about_callbacks.py

Import side effects register all Dash callbacks against the single global app.

## 3) UI layout and state model

### Main layout

- layout.py defines get_app_layout() and exports app_layout.
- The page is organized into:
  - file input + onset/offset selection
  - session plot controls/plot
  - microstructure controls/plots/tables
  - data export controls
  - results summary table + batch modal
  - fixed top-right Help, Load Config, About controls

### Dash stores used as state hubs

The app uses dcc.Store heavily as shared state:

- lick-data: current selected onset series (single column) as JSON DataFrame
- data-store: parsed uploaded file as dict of JSON DataFrames by column name
- figure-data-store: cached underlying data used for Excel export
- filename-store: uploaded filename
- session-duration-store: inferred session duration
- custom-config-store: uploaded YAML overrides
- session-length-seconds: normalized session length in seconds
- session-bin-slider-seconds: normalized bin size in seconds
- between-start-seconds / between-stop-seconds: normalized time-window bounds

Design intent: decouple expensive parsing/analysis from UI interactions and avoid recalculating from raw upload text each callback.

## 4) Configuration system

- config_manager.py
  - Loads config.yaml once at startup into a global config object.
  - Provides dot-path getter, app config getter, and slider config builders.
  - Has default fallback config when file missing/invalid.

- config.yaml
  - Controls default session settings, microstructure thresholds, file defaults, UI/debug behavior, and slider ranges.

- callbacks/config_callbacks.py
  - Supports runtime upload of custom YAML config to override controls.
  - Updates many UI controls in one multi-output callback.

Note: slider mark generation logic appears in more than one place (ConfigManager and config callback local helper), so behavior is mostly consistent but duplicated.

## 5) Data ingestion and validation pipeline

### Parsers

- utils/file_parsers.py provides parsers for:
  - med (column format)
  - med_array
  - csv/txt
  - coulbourn/colbourn
  - ohrbets
  - dd
  - km
  - ls

Common output contract: dict[column_name -> pandas DataFrame JSON (orient='split') with a single licks column].

### Validation

- utils/validation.py
  - validate_onset_times: monotonic increase check
  - validate_onset_offset_pairs:
    - allows off-by-one length and trims
    - fails on severe mismatches
    - checks temporal consistency (offset after onset)

### File load flow

- callbacks/data_callbacks.py
  - upload callback parses file based on selected file type.
  - populates onset/offset dropdown options.
  - defaults onset heuristically; defaults offset to none to reduce accidental contamination.
  - clears dependent stores when a new file is loaded.
  - validates loaded onset/offset data and shows status alerts.

## 6) Analysis and plotting pipeline

### Session-level plot

- callbacks/graph_callbacks.py
  - make_session_graph renders:
    - histogram OR cumulative curve
  - supports axis scaling in seconds/minutes/hours
  - uses session-length-seconds if provided; otherwise max lick time

### Microstructure plots

- Intraburst ILI histogram
- Lick-length histogram (requires offsets)
- Burst size histogram
- Weibull probability plot

These callbacks use trompy.lickcalc and include guards for:

- empty data
- missing/invalid offset columns
- severe onset/offset mismatches (cross-file contamination protection)
- too few bursts for Weibull parameter display (threshold from config)

### Trial and segmentation helpers

- utils/calculations.py includes reusable logic:
  - detect_trials(min_iti)
  - analyze_trial(...)
  - calculate_segment_stats(...)
  - get_licks_for_burst_range(...)
  - get_offsets_for_licks(...)

In addition to whole-session mode, the app supports:

- divide by N (time or burst divisions)
- first N bursts
- between start/stop times
- trial-based analysis (auto trial detection by ITI)

## 7) Results table and export workflows

### Figure-data collection

- graph_callbacks.collect_figure_data stores raw plotted arrays + summary stats.
- This is the base for single-file Excel export.

### Single-file export

- export_callbacks.export_to_excel
  - Exports Summary + selected sheets (histograms, burst probability/details, IBIs, lick lengths).
  - Uses figure-data-store.

### Results table

- export_callbacks.add_to_results_table
  - Recomputes stats for selected epoch mode and appends rows to results-table-store.
- update_results_table appends aggregate stats rows:
  - Sum, Mean, SD, N, SE
- supports row deletion, clear-all, and export selected/full table.

### Batch mode

- Implemented in export_callbacks.py through modal callbacks.
- Supports multi-file parsing, optional advanced per-file onset/offset selection, and optional per-file Excel generation zipped for download.
- Includes robust offset auto-detection fallback and validation checks.

Observed nuance: one status callback still labels batch processing as not configured, while full batch processing logic is present elsewhere in the same file.

## 8) Help system

- data_callbacks.py defines Flask route:
  - /help -> render_template('help.html')
- templates/help.html composes chapter partials from templates/help_chapters/*.html.
- manage_help.py provides helper CLI to list/create/stats chapter files.

This is a clean modular documentation setup separate from Dash callback code.

## 9) About/version/example download

- callbacks/about_callbacks.py
  - toggles About modal
  - displays version from _version.py
  - serves downloadable example zip from assets/examples/example-files.zip

## 10) Dependencies and environment

- requirements.txt for pip installs.
- environment.yml for conda/mamba environment.
- pixi.toml also exists but currently has unusual pinned versions (notably pandas >=3 spec).

Primary runtime stack:

- dash
- dash-bootstrap-components
- plotly
- pandas
- numpy
- pyyaml
- openpyxl
- trompy

## 11) Tests and quality posture

- tests/test_config.py exists, but is a print-based smoke script rather than assertion-based pytest coverage.
- No broader automated tests currently visible for parsers, callbacks, or calculations.

## 12) Practical extension map (where to add features)

- New UI controls or sections:
  - layout.py
  - tooltips.py for explanatory text

- New parser/file format:
  - utils/file_parsers.py
  - wire parser into:
    - data_callbacks load callback
    - export_callbacks batch parsing paths
  - update file type dropdown options in layout.py

- New analysis metric:
  - utils/calculations.py for reusable computation
  - graph_callbacks.py for visualization
  - export_callbacks.py for table/export inclusion

- New config option:
  - config.yaml + ConfigManager defaults/getters
  - consume in layout or callbacks
  - optionally support custom YAML upload path in config_callbacks.py

- New export sheet:
  - graph_callbacks.collect_figure_data (capture raw arrays)
  - export_callbacks.export_to_excel (write worksheet)

- Help/documentation changes:
  - templates/help_chapters/*.html
  - templates/help.html TOC/include entries

## 13) Known technical debt and risks to watch

- Heavy callback complexity in export_callbacks.py (very large file, high branching).
- Duplicated slider-mark generation logic.
- Mixed user messaging around batch readiness vs implemented functionality.
- Data interchange via JSON-encoded DataFrames across callbacks is practical but fragile if schema changes.
- Limited automated tests for parsing/analysis edge cases.

## 14) Recommended next refactor steps (optional)

1. Split export_callbacks.py into smaller domain files:
   - batch callbacks
   - table callbacks
   - excel export callbacks
2. Add parser unit tests with representative files from data/.
3. Add integration tests for epoch modes and long-lick behavior.
4. Centralize slider mark generation in ConfigManager only.
5. Add a typed data contract for Store payloads (at least documented schema constants).

## 15) Quick run notes

- Local run:
  - conda/mamba env from environment.yml
  - python app.py
- App default URL:
  - http://localhost:8050

