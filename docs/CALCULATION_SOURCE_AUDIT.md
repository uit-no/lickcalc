# Calculation Source Audit: trompy vs In-App Logic

Date: 2026-07-26

Scope reviewed:
- `utils/calculations.py`
- `callbacks/graph_callbacks.py`
- `callbacks/export_callbacks.py`
- `callbacks/data_callbacks.py`
- `layout.py` (results table columns)

Goal:
- Verify whether app calculations use `trompy`'s `lickcalc` behavior (desired) or local app-side math.

## Executive Summary

- Core microstructure metrics are primarily produced by `trompy.lickcalc`.
- Several displayed/exported values are local post-processing of `lickcalc` outputs (formatting, filtering, means, thresholds).
- A small set of calculations are fully in-app by design (trial detection, first-n-ILI fallback path, table aggregate rows, time-range metadata).

## Parameter/Calculation Results

| Parameter/Calculation | Primary Source | Status | Risk/Consistency | Notes |
|---|---|---|---|---|
| `interburst_interval` (IBI input) | UI/config parameter passed into `lickcalc` as `burstThreshold` | Mixed | Low | Not computed; user/app parameter forwarded to `lickcalc`. |
| `min_burst_size` input | UI/config parameter passed into `lickcalc` as `minburstlength` | Mixed | Low | Not computed; user/app parameter forwarded to `lickcalc`. |
| `longlick_threshold` input | UI/config parameter passed into `lickcalc` as `longlickThreshold` | Mixed | Low | Not computed; user/app parameter forwarded to `lickcalc`. |
| `total_licks` | `lickcalc(...)["total"]` | trompy | Low | Core metric comes from `trompy`. |
| `intraburst_freq` (whole/between/divisions/trial stats) | Usually `lickcalc(...)["freq"]` | trompy | Low | Most paths use direct `trompy` value. |
| `intraburst_freq` (First n bursts mode) | Local recomputation from `lickcalc` ILIs | In-app derived | Medium | App computes using first-n burst ILIs `< IBI`; can differ from `trompy` internals in edge cases. |
| `n_bursts` | `lickcalc(...)["bNum"]` | trompy | Low | Direct `trompy` output. |
| `mean_licks_per_burst` | `lickcalc(...)["bMean"]` | trompy | Low | Direct `trompy` output. |
| `mean_interburst_time` | `np.mean(lickcalc(...)["IBIs"])` | In-app derived | Low | Uses `trompy` IBI array but mean is computed in-app. |
| `weibull_alpha` | `lickcalc(...)["weib_alpha"]` | trompy | Low | App additionally masks to `NaN` if bursts below threshold. |
| `weibull_beta` | `lickcalc(...)["weib_beta"]` | trompy | Low | App additionally masks to `NaN` if bursts below threshold. |
| `weibull_rsq` | `lickcalc(...)["weib_rsq"]` | trompy | Low | App additionally masks to `NaN` if bursts below threshold. |
| `n_long_licks` | `len(lickcalc(...)["longlicks"])` | In-app derived | Low | Count operation is local; source list comes from `trompy`. |
| `max_lick_duration` | `np.max(lickcalc(...)["licklength"])` | In-app derived | Low | Max operation is local; durations come from `trompy`. |
| `licklength_mode` | `lickcalc(...)["licklength_mode"]` then scaled to ms | In-app derived | Low | Value from `trompy`; conversion/formatting local. |
| `intercontact_mode` | `lickcalc(...)["intercontact_mode"]` then scaled to ms | In-app derived | Low | Value from `trompy`; conversion/formatting local. |
| `long_licks_removed` flag (table) | Local boolean string (`Yes`/`No`) | In-app | Low | Metadata label only. |
| `start_time` / `end_time` / `duration` (table rows) | Local segmentation metadata | In-app | Medium | Derived from full session, between-times, trial boundaries, or division bins; values depend on app slicing policy. |
| Time divisions | `lickcalc(..., time_divisions=N)` | trompy | Low | Division metrics come from `enhanced_results['time_divisions']`. |
| Burst divisions | `lickcalc(..., burst_divisions=N)` | trompy | Low | Division metrics come from `enhanced_results['burst_divisions']`. |
| Between-times analysis | Local filtering + `lickcalc` on subset | Mixed | Medium | Subset selection in-app, microstructure on subset via `trompy`; boundary inclusivity can change counts near edges. |
| Trial-based analysis | Local trial detection + per-trial `lickcalc` | Mixed | Medium | Trial boundaries from in-app `detect_trials`; per-trial stats from `trompy`. |
| Trials detected display (`n_trials`) | `detect_trials` in app | In-app | Low | Pure UI/helper calculation. |
| Session histogram | Local `numpy.histogram` on onset times | In-app | Low | Visualization/export data, not `lickcalc`. |
| Intraburst ILI histogram | Local `numpy.histogram` on `lickcalc()['ilis']` | In-app derived | Low | ILIs from `trompy`, bins/counts in-app. |
| Burst histogram | Local `numpy.histogram` on `lickcalc()['bLicks']` | In-app derived | Low | Burst sizes from `trompy`, binning in-app. |
| Burst probability curve points | `lickcalc()['burstprob']` | trompy | Low | Direct use of `trompy` burst probability outputs. |
| Weibull fit line in plot | `trompy.weib_davis(...)` | trompy | Low | Fit rendering uses `trompy` function with `lickcalc` params. |
| Burst details table (start/end/duration per burst) | `bStart`, `bEnd`, `bLicks` + local duration subtraction | In-app derived | Low | Burst boundaries from `trompy`; durations computed locally. |
| First-n ILI line plot means | `Lickcalc.get_first_n_ilis_in_bursts` when available | trompy-preferred | Low | Preferred source is `trompy` API on `Lickcalc` object. |
| First-n ILI line plot fallback means/SEM | Local fallback from `burst_inds`/`burst_licks` and filtered ILIs | In-app | High | Used when method unavailable/fails; likely but not guaranteed to match `trompy` exactly under all edge cases. |
| Results-table aggregate rows (`Sum`, `Mean`, `SD`, `N`, `SE`) | pandas/numpy in app | In-app | Low | Post-hoc summary statistics across rows. |

## Direct Answer to Requested Check

The app does use `trompy.lickcalc` for the core lick microstructure calculations (total licks, burst count/size metrics, intraburst frequency in most modes, Weibull parameters, long-lick primitives, and division outputs).

However, there are intentional in-app calculations layered on top for:
- segmentation and metadata (time windows, trials, labels, durations),
- display/export transformations (means, counts, maxima, ms conversion, histogram bins),
- first-n-bursts intraburst frequency recomputation,
- first-n-ILI fallback and SEM,
- table-level aggregate statistics.

So behavior is best described as: **trompy core + local post-processing/segmentation**.

## Notable Implementation Detail

- `calculate_mean_interburst_time` exists in `utils/calculations.py` but is currently unused; most code paths compute mean IBI directly from `lickcalc()['IBIs']` using `np.mean(...)`.