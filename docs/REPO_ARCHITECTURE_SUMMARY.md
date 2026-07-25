# lickcalc Repository Architecture Summary

Last updated: 2026-07-25

## Quick Resume Checklist

1. Open these files first:
  - layout.py
  - callbacks/graph_callbacks.py
  - callbacks/config_callbacks.py
  - utils/generate_synthetic_data.py
  - utils/calculations.py
  - config_manager.py
2. Confirm recent completed work:
  - Intercontact lengths plot is enabled and uses `intercontact_time`.
  - Intercontact histogram uses long-lick-threshold x-range and 0.01s bins.
  - Interburst slider marks are step-aligned and less crowded.
  - `First n ILIs` is implemented as a mean +/- SEM line plot.
  - First-n slider is shown only when `First n ILIs` is selected.
  - Config supports default plot selections and `first_n_ilis` default value.
  - Synthetic edge-case data generator is available and fixtures are regenerated.
  - **[2026-07-25] Fixed trial_like dataset burst analysis display**: make_burstprob_graph() now returns actual burst metrics (n_bursts, mean_licks_per_burst, mean_ibi) when burstprob is empty, instead of returning zeros.
  - **[2026-07-25] Removed firstnlowvar and firstn_highvar datasets** from synthetic data generation; analysis_cases now contains only: sparse, dense, trial_like.
  - **[2026-07-25] Moved synthetic data fixtures section** from main layout alert box to About dialog (under "Example Data Files" section).
  - **[2026-07-25] Updated citation** in About modal to 2026 bioRxiv: Volcko KL & McCutcheon JE (2026) *lickcalc*: bioRxiv, doi: https://doi.org/10.64898/2026.03.09.710511
  - **[2026-07-25] UI polish pass completed**: microstructure controls and graphs were adjusted for cleaner alignment and more compact plot sizing.
  - **[2026-07-25] Plot theme refresh completed**: modernized grid/axis styling, improved colorway, and plot background matched to app background.
  - **[2026-07-25] Weibull observed trace updated** from marker points to staircase (step-line) rendering.
  - **[2026-07-25] Dependency alignment update**: Dash raised to 4.4.1 and environment manifest constraints aligned with deployment requirements policy.
3. Main pending focus:
  - Expand/adjust synthetic fixtures and expected outcomes as new edge cases are discovered.
4. Keep guardrails in place:
  - Preserve onset/offset validation and severe mismatch protection.
5. Quick run:
  - `python app.py`

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
- First n ILIs line plot (mean with SEM shading, using trompy-compatible burst filtering)
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
- Added regression tests for first-n ILI computation path:
  - `tests/test_first_n_ilis.py` (unittest)
  - guards against cross-burst contamination in SEM path
  - verifies intraburst-threshold-constrained values and expected means on controlled synthetic inputs
- Environment note for running these tests:
  - tests were run successfully in conda env `default`
  - some other local envs may miss `yaml`, `dash`, or `trompy`

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

## 16) Session handoff notes (2026-07-24)

Compact deltas from recent editing work so development can resume quickly on another machine.

- Implemented intercontact lengths plot:
  - `longlick-fig-type` now includes `Intercontact lengths` (enabled).
  - `make_longlicks_graph` now renders a histogram from `lickdata["intercontact_time"]`.
  - Uses same x-axis and binning logic as lick lengths:
    - x-range based on long lick threshold
    - bins from `np.arange(0, longlick_th, 0.01)`
  - Main files:
    - layout.py
    - callbacks/graph_callbacks.py

- Improved Interburst slider ticks to match usable steps and avoid crushed labels:
  - New interburst-specific mark generators added in both startup/default config path and uploaded custom-config path.
  - Tick spacing now favors readable intervals (0.5s, then 1s, then coarser if needed), aligned to slider step multiples.
  - Main files:
    - config_manager.py
    - callbacks/config_callbacks.py

- Existing staged feature still pending:
  - None for first-n plotting: it is implemented and no longer placeholder.

- Stability guardrails retained:
  - Onset/offset validation with mismatch protection remains in plotting callbacks to avoid cross-file contamination effects.

### Additional completed deltas (same session)

- First n ILIs feature completed and hardened:
  - `intraburst-fig-type` includes selectable `first_n_ili` mode (enabled).
  - Added `first-n-ili-slider` (default 5), visible only in first-n mode.
  - Plot is a mean +/- SEM line chart (not histogram), styled with existing Plotly app conventions.
  - Reduced x-axis tick density for larger n to avoid label crowding.

- Fixed first-n variability bug source:
  - Root cause was app-side SEM reconstruction windowing crossing burst boundaries when bursts were filtered.
  - Moved first-n summary logic into reusable utility:
    - `utils.calculations.compute_first_n_ili_summary(...)`
  - Callback now consumes that utility, ensuring burst-size-based slicing and threshold filtering consistency.

- Config system expanded:
  - Added `microstructure.first_n_ilis` default.
  - Added `plots.*` defaults:
    - `plots.intraburst_fig_type`
    - `plots.longlick_fig_type`
    - `plots.bursthist_fig_type`
    - `plots.burstprob_fig_type`
  - Custom YAML upload path updates these controls live.
  - Updated docs/examples:
    - `config.yaml`
    - `custom_config_example.yaml`
    - `docs/CONFIG_README.md`
    - `README.md` quick config key reference table.

- Synthetic edge-case fixture workflow added:
  - New generator source:
    - `utils/generate_synthetic_data.py`
  - Generated fixture outputs:
    - `assets/examples/synthetic_edge_cases/synthetic_core_cases.csv`
    - `assets/examples/synthetic_edge_cases/synthetic_validation_cases.csv`
    - `assets/examples/synthetic_edge_cases/synthetic_analysis_cases.csv`
    - `assets/examples/synthetic_edge_cases/synthetic_manifest.csv`
  - In-app discoverability:
    - layout banner with links to the synthetic files and manifest.

- Synthetic timing tuning completed:
  - Offset generation now enforces `offset < next onset` for non-intentional cases.
  - Baseline physiological targets tuned for key onset/offset pairs:
    - lick length mode approximately 50-70 ms
    - intercontact mode approximately 60 ms
    - intraburst frequency approximately 6.5-8.5 Hz
  - Weibull-ready profiles added:
    - key datasets now use ~20 bursts with exponentially decaying burst sizes
    - verified to produce non-null Weibull parameters in local checks.

### Cross-machine continuation notes

1. Regenerate synthetic fixtures after editing generator logic:
  - `python utils/generate_synthetic_data.py`
2. Primary fixture directory to sync/copy between machines:
  - `assets/examples/synthetic_edge_cases/`
3. If first-n regression work continues, run:
  - `python -m unittest tests.test_first_n_ilis -v`
4. If a target machine has env mismatch errors (missing `yaml`/`trompy`/`dash`), switch to an env that includes dependencies before validation.

## 17) Session handoff notes (2026-07-25)

Compact deltas from UI and dependency updates completed after the 2026-07-24 handoff.

- Microstructure layout adjustments:
  - Moved Remove long licks control below the microstructure stats table (instead of above the long-lick threshold slider).
  - Reduced key graph heights to a squatter layout (session plot and microstructure plots).
  - Main file:
    - `layout.py`

- First-n slider alignment fix:
  - Avoided permanent misalignment caused by always reserving slider space in only one column.
  - Implemented synchronized spacer logic so columns stay aligned only when First n ILIs slider is visible.
  - Main files:
    - `layout.py`
    - `callbacks/data_callbacks.py`

- Plot aesthetics refresh:
  - Added a custom default Plotly template for cleaner grid/axis styling and updated colorway.
  - Set `paper_bgcolor` and `plot_bgcolor` to white to match app background.
  - Main file:
    - `callbacks/graph_callbacks.py`

- Weibull plot tweak:
  - Changed observed series from circle markers to a staircase-style step line (`line_shape='hv'`).
  - Main file:
    - `callbacks/graph_callbacks.py`

- Dependency and deployment consistency:
  - Dash updated to `4.4.1` in deployment-facing dependency manifest.
  - Confirmed Azure staging workflow installs from `requirements.txt`.
  - Aligned `environment.yml` constraints for `dash-bootstrap-components` and `trompy` to reduce drift with requirements-based deployment behavior.
  - Main files:
    - `requirements.txt`
    - `environment.yml`
    - `.github/workflows/p-resapp-staging-deploy.yml`

### Suggested next continuation steps

1. If more visual polish is desired, tune only one dimension at a time:
  - axis/grid contrast
  - colorway accents
  - table/control surface styling
2. If dark mode is revisited later, implement in two phases:
  - phase 1: app/page + Plotly theme toggle
  - phase 2: controls/tables/tooltips full polish
3. Keep dependency manifests synchronized when updating runtime packages:
  - `requirements.txt` (deployment source of truth)
  - `environment.yml` (local conda/mamba parity)
4. Before release/deploy, run a focused smoke test:
  - file upload
  - session/intraburst/longlick/burst plots
  - results table append/export
  - Weibull step-trace rendering


