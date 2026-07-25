"""Generate compact synthetic CSV fixtures for lickcalc edge-case testing.

This script creates a small set of CSV files, each with multiple columns that
represent different edge cases. The goal is broad coverage with minimal files.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from random import Random
from typing import Dict, Iterable, List, Sequence
import math


DEFAULT_SEED = 20260724
DEFAULT_OUTPUT_DIR = Path("assets/examples/synthetic_edge_cases")


def _exp_decay_burst_sizes(
    n_bursts: int,
    max_size: int,
    min_size: int,
    decay: float,
) -> List[int]:
    """Generate integer burst sizes that follow an exponential decay shape."""
    if n_bursts <= 0:
        return []
    if min_size < 1:
        raise ValueError("min_size must be >= 1")
    if max_size < min_size:
        raise ValueError("max_size must be >= min_size")

    span = max_size - min_size
    sizes = [
        int(round(min_size + span * math.exp(-decay * i)))
        for i in range(n_bursts)
    ]
    # Keep monotonic non-increasing after rounding.
    for i in range(1, len(sizes)):
        if sizes[i] > sizes[i - 1]:
            sizes[i] = sizes[i - 1]
    sizes = [max(min_size, min(max_size, s)) for s in sizes]
    return sizes


def _build_burst_onsets(
    burst_sizes: Sequence[int],
    intra_ilis: Sequence[float],
    interburst_gap: float,
    start_time: float = 0.0,
) -> List[float]:
    """Build onset timestamps from burst sizes and repeating intra-burst ILIs."""
    if not intra_ilis:
        raise ValueError("intra_ilis must not be empty")

    times: List[float] = []
    t = float(start_time)
    il_idx = 0

    for b_idx, size in enumerate(burst_sizes):
        if size <= 0:
            continue

        times.append(round(t, 6))
        for _ in range(size - 1):
            t += float(intra_ilis[il_idx % len(intra_ilis)])
            times.append(round(t, 6))
            il_idx += 1

        if b_idx < len(burst_sizes) - 1:
            t += float(interburst_gap)

    return times


def _offsets_from_onsets(
    onsets: Sequence[float],
    base_duration: float,
    std_dev: float,
    rng: Random,
) -> List[float]:
    """Create offset timestamps from onsets with normal distribution of durations.

    Uses normal distribution to create broader distribution of lick durations
    (standard deviation of std_dev).
    Offsets are constrained to stay strictly before the next onset when one
    exists, matching lickcalc validation expectations.
    """
    offsets: List[float] = []
    eps = 0.001
    for idx, onset in enumerate(onsets):
        dur = base_duration + rng.gauss(0, std_dev)
        dur = max(0.01, dur)

        # Keep offset before next onset where possible.
        if idx < len(onsets) - 1:
            next_onset = float(onsets[idx + 1])
            max_dur = (next_onset - float(onset)) - eps
            if max_dur > 0:
                dur = min(dur, max_dur)

        offsets.append(round(float(onset) + dur, 6))
    return offsets


def _write_columns_csv(path: Path, columns: Dict[str, Sequence[float]]) -> None:
    """Write columns with unequal lengths to CSV (blank-padded rows)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = list(columns.keys())
    max_len = max((len(v) for v in columns.values()), default=0)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for i in range(max_len):
            row = []
            for h in headers:
                col = columns[h]
                row.append(col[i] if i < len(col) else "")
            writer.writerow(row)


def _build_core_file(rng: Random) -> Dict[str, Sequence[float]]:
    """Core behavior cases: clean data and threshold boundaries."""
    weibull_decay_sizes = _exp_decay_burst_sizes(
        n_bursts=20,
        max_size=24,
        min_size=3,
        decay=0.15,
    )

    clean_on = _build_burst_onsets(
        burst_sizes=weibull_decay_sizes,
        intra_ilis=[0.12, 0.12, 0.13],
        interburst_gap=5.2,
        start_time=0.0,
    )
    clean_off = _offsets_from_onsets(clean_on, base_duration=0.060, std_dev=0.010, rng=rng)

    # Construct ~500+ licks with gap hierarchy that produces:
    # - 25-30 bursts at 0.25s IBI (most sensitive)
    # - 2-3 gaps > 3s to test very high IBI thresholds
    # Each burst: 12-26 licks spaced at 0.12s (intra-burst ILI)
    # Note: gap_before values are adjusted by -0.12 to account for the increment after final lick
    boundary_on_builder: List[float] = []
    t = 0.0
    
    # Define 28 burst sizes and corresponding gap-before values
    # Includes gaps: >= 1.0, [0.75, 1.0), [0.5, 0.75), [0.25, 0.5), and > 3s
    burst_configs = [
        (15, 0.0),      # Burst 1: no gap before
        (18, 1.03),     # Gap 1: produces ILI ~1.15 >= 1.0
        (12, 0.93),     # Gap 2: produces ILI ~1.05 >= 1.0
        (20, 0.23),     # Gap 3: produces ILI ~0.35 in [0.25, 0.5)
        (14, 0.30),     # Gap 4: produces ILI ~0.42 in [0.25, 0.5)
        (16, 1.08),     # Gap 5: produces ILI ~1.20 >= 1.0
        (22, 0.91),     # Gap 6: produces ILI ~1.03 >= 1.0
        (19, 0.43),     # Gap 7: produces ILI ~0.55 in [0.5, 0.75)
        (17, 0.76),     # Gap 8: produces ILI ~0.88 in [0.75, 1.0)
        (21, 0.28),     # Gap 9: produces ILI ~0.40 in [0.25, 0.5)
        (13, 0.98),     # Gap 10: produces ILI ~1.10 >= 1.0
        (25, 0.96),     # Gap 11: produces ILI ~1.08 >= 1.0
        (18, 0.58),     # Gap 12: produces ILI ~0.70 in [0.5, 0.75)
        (20, 0.97),     # Gap 13: produces ILI ~1.09 >= 1.0
        (16, 0.20),     # Gap 14: produces ILI ~0.32 in [0.25, 0.5)
        (24, 1.00),     # Gap 15: produces ILI ~1.12 >= 1.0
        (14, 0.80),     # Gap 16: produces ILI ~0.92 in [0.75, 1.0)
        (19, 0.36),     # Gap 17: produces ILI ~0.48 in [0.25, 0.5)
        (22, 0.99),     # Gap 18: produces ILI ~1.11 >= 1.0
        (26, 0.89),     # Gap 19: produces ILI ~1.01 >= 1.0
        (15, 0.35),     # Gap 20: produces ILI ~0.47 in [0.25, 0.5)
        (23, 3.21),     # Gap 21: produces ILI ~3.33 > 3.0 (large gap)
        (20, 0.62),     # Gap 22: produces ILI ~0.74 in [0.5, 0.75)
        (18, 1.04),     # Gap 23: produces ILI ~1.16 >= 1.0
        (21, 0.28),     # Gap 24: produces ILI ~0.40 in [0.25, 0.5)
        (17, 3.89),     # Gap 25: produces ILI ~4.01 > 3.0 (large gap)
        (24, 0.75),     # Gap 26: produces ILI ~0.87 in [0.75, 1.0)
        (19, 0.43),     # Gap 27: produces ILI ~0.55 in [0.5, 0.75)
    ]
    
    for burst_size, gap_before in burst_configs:
        t += gap_before  # Add gap before burst
        for _ in range(burst_size):
            boundary_on_builder.append(round(t, 6))
            t += 0.12  # Intra-burst ILI
    
    boundary_on = boundary_on_builder
    boundary_off = _offsets_from_onsets(boundary_on, base_duration=0.060, std_dev=0.010, rng=rng)

    # Longlick boundary: mix of ~15 long-duration licks + ~100 standard-distribution licks
    # Create long-duration licks individually, spaced far apart to prevent offset overlap
    long_durations = [
        # 0.3-1.0s range (10 durations)
        0.32, 0.38, 0.45, 0.52, 0.62, 0.72, 0.82, 0.92, 0.35, 0.55,
        # 1.0s+ range (5 durations)
        1.2, 2.8, 5.5, 12.3, 28.5,
    ]
    special_longlick_on: List[float] = []
    special_longlick_off: List[float] = []
    
    current_time = 0.2
    for duration in long_durations:
        special_longlick_on.append(current_time)
        special_longlick_off.append(round(current_time + duration, 6))
        # Space next lick far enough to avoid overlap (duration + 0.5s buffer)
        current_time += duration + 0.5

    # Standard distribution bursts (~100 licks total)
    standard_longlick_on = _build_burst_onsets(
        burst_sizes=[12, 14, 11, 13, 12, 11, 14, 12],  # 8 bursts ~= 99 licks
        intra_ilis=[0.12, 0.12, 0.13],
        interburst_gap=3.5,
        start_time=current_time + 5.0,  # Start after long licks
    )
    standard_longlick_off = _offsets_from_onsets(standard_longlick_on, base_duration=0.060, std_dev=0.010, rng=rng)

    # Combine both sets
    longlick_on = list(special_longlick_on) + list(standard_longlick_on)
    longlick_off = list(special_longlick_off) + list(standard_longlick_off)

    return {
        "onset_clean": clean_on,
        "offset_clean": clean_off,
        "onset_ibi_boundary": boundary_on,
        "offset_ibi_boundary": boundary_off,
        "onset_longlick_boundary": longlick_on,
        "offset_longlick_boundary": longlick_off,
    }


def _build_validation_file(rng: Random) -> Dict[str, Sequence[float]]:
    """Validation stress cases: mismatch, ordering, monotonicity, sparse columns."""
    base_on = _build_burst_onsets(
        burst_sizes=[6, 7, 5],
        intra_ilis=[0.12, 0.12, 0.13],
        interburst_gap=5.4,
        start_time=0.0,
    )
    base_off = _offsets_from_onsets(base_on, base_duration=0.060, std_dev=0.010, rng=rng)

    offby1_on = list(base_on)
    offby1_on.append(round(offby1_on[-1] + 0.11, 6))

    mismatch_on = list(base_on)
    mismatch_off = list(base_off[:6])

    nonmonotonic_on = list(base_on)
    if len(nonmonotonic_on) >= 5:
        nonmonotonic_on[4] = round(nonmonotonic_on[3] - 0.02, 6)

    duplicate_on = list(base_on)
    if len(duplicate_on) >= 4:
        duplicate_on[3] = duplicate_on[2]

    single_value_on = [0.0]

    bad_order_on = [0.0, 0.10, 0.20, 0.30, 5.6, 5.7]
    # Intentionally create invalid offset-onset relationships: some offsets <= onset
    bad_order_off = [0.05, 0.08, 0.25, 0.28, 5.55, 5.75]  # Pairs 0,1 have offset < onset

    return {
        "onset_offby1": offby1_on,
        "offset_offby1": base_off,
        "onset_severe_mismatch": mismatch_on,
        "offset_severe_mismatch": mismatch_off,
        "onset_nonmonotonic": nonmonotonic_on,
        "onset_duplicates": duplicate_on,
        "onset_single_value": single_value_on,
        "onset_offset_bad_order": bad_order_on,
        "offset_bad_order": bad_order_off,
    }


def _build_analysis_file(rng: Random) -> Dict[str, Sequence[float]]:
    """Analysis stress: sparse/dense/trial-like and first-n variance profiles."""
    sparse_on = _build_burst_onsets(
        burst_sizes=[2, 2, 2, 3],
        intra_ilis=[0.14],
        interburst_gap=12.0,
        start_time=0.0,
    )

    dense_on = _build_burst_onsets(
        burst_sizes=_exp_decay_burst_sizes(
            n_bursts=20,
            max_size=26,
            min_size=3,
            decay=0.13,
        ),
        intra_ilis=[0.12, 0.12, 0.12],
        interburst_gap=5.3,
        start_time=0.0,
    )

    trial_like_on = []
    t = 0.0
    for _ in range(4):
        trial_like_on.extend([round(t + x, 6) for x in [0.0, 0.11, 0.21, 0.32, 0.43, 0.55]])
        t += 80.0

    dense_off = _offsets_from_onsets(dense_on, base_duration=0.060, std_dev=0.010, rng=rng)
    trial_like_off = _offsets_from_onsets(trial_like_on, base_duration=0.060, std_dev=0.010, rng=rng)

    return {
        "onset_sparse": sparse_on,
        "onset_dense": dense_on,
        "offset_dense": dense_off,
        "onset_trial_like": trial_like_on,
        "offset_trial_like": trial_like_off,
    }


def _manifest_rows() -> Iterable[List[str]]:
    """Rows for manifest.csv describing each scenario and expected behavior."""
    rows = [
        [
            "synthetic_core_cases.csv",
            "onset_clean / offset_clean",
            "baseline",
            "Clean onset+offset data with 20 bursts following exponential burst-size decay.",
            "All plots stable; validation passes. Targets: licklength mode ~50-70 ms, intercontact mode ~60 ms, intraburst freq ~6.5-8.5 Hz.",
        ],
        [
            "synthetic_core_cases.csv",
            "onset_ibi_boundary",
            "threshold-boundary",
            "500+ licks in 28 bursts (12-26 licks each) with ILI distribution: 10 gaps >= 1.0s, 2 gaps in [0.75-1.0), 2 gaps in [0.5-0.75), 6 gaps in [0.25-0.5), 2 gaps > 3.0s.",
            "At 0.25s: ~28 bursts. At 0.5s: ~21 bursts. At 0.75s: ~18 bursts. At 1.0s: ~15 bursts. At 3.0s: ~13 bursts. Tests IBI threshold sensitivity across full range including very high thresholds.",
        ],
        [
            "synthetic_core_cases.csv",
            "onset_longlick_boundary / offset_longlick_boundary",
            "threshold-boundary",
            "Lick durations around 0.29/0.30/0.31 s.",
            "Long-lick counts change near long-lick threshold.",
        ],
        [
            "synthetic_validation_cases.csv",
            "onset_offby1 / offset_offby1",
            "validation",
            "Onsets exceed offsets by exactly one entry.",
            "Off-by-one trim path should pass with warning/info.",
        ],
        [
            "synthetic_validation_cases.csv",
            "onset_severe_mismatch / offset_severe_mismatch",
            "validation",
            "Large onset/offset length mismatch.",
            "Validation should fail severe mismatch guardrail.",
        ],
        [
            "synthetic_validation_cases.csv",
            "onset_nonmonotonic",
            "validation",
            "Contains decreasing timestamp.",
            "Monotonicity validation should fail.",
        ],
        [
            "synthetic_validation_cases.csv",
            "onset_duplicates",
            "validation",
            "Contains repeated timestamp.",
            "May pass monotonic non-decreasing checks but stresses edge handling.",
        ],
        [
            "synthetic_validation_cases.csv",
            "onset_offset_bad_order / offset_bad_order",
            "validation",
            "Some offsets are <= onset.",
            "Onset/offset temporal consistency should fail.",
        ],
        [
            "synthetic_analysis_cases.csv",
            "onset_sparse",
            "analysis",
            "Few licks and small bursts with long gaps.",
            "Limited burst metrics and sparse histograms.",
        ],
        [
            "synthetic_analysis_cases.csv",
            "onset_dense / offset_dense",
            "analysis",
            "High-frequency licking with 20 bursts following exponential burst-size decay.",
            "Stress histogram/binning and long-lick logic under load. Targets: licklength mode ~50-70 ms, intercontact mode ~60 ms, intraburst freq ~6.5-8.5 Hz.",
        ],
        [
            "synthetic_analysis_cases.csv",
            "onset_trial_like",
            "analysis",
            "Large gaps approximately every 80 s.",
            "Trial detection should identify multiple trials.",
        ],
    ]
    return rows


def _write_manifest_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = ["file", "columns", "category", "description", "expected_behavior"]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in _manifest_rows():
            writer.writerow(row)


def generate_synthetic_edge_case_files(output_dir: Path, seed: int = DEFAULT_SEED) -> List[Path]:
    """Generate the three compact synthetic CSV fixtures plus manifest."""
    rng = Random(seed)

    output_dir.mkdir(parents=True, exist_ok=True)

    core_path = output_dir / "synthetic_core_cases.csv"
    validation_path = output_dir / "synthetic_validation_cases.csv"
    analysis_path = output_dir / "synthetic_analysis_cases.csv"
    manifest_path = output_dir / "synthetic_manifest.csv"

    _write_columns_csv(core_path, _build_core_file(rng))
    _write_columns_csv(validation_path, _build_validation_file(rng))
    _write_columns_csv(analysis_path, _build_analysis_file(rng))
    _write_manifest_csv(manifest_path)

    return [core_path, validation_path, analysis_path, manifest_path]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic edge-case CSV files for lickcalc.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR.as_posix()})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Deterministic random seed (default: {DEFAULT_SEED})",
    )
    args = parser.parse_args()

    created = generate_synthetic_edge_case_files(output_dir=args.output_dir, seed=args.seed)
    print("Created synthetic fixtures:")
    for p in created:
        print(f" - {p.as_posix()}")


if __name__ == "__main__":
    main()
