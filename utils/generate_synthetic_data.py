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
    jitter: float,
    rng: Random,
) -> List[float]:
    """Create offset timestamps from onsets with small deterministic jitter.

    Offsets are constrained to stay strictly before the next onset when one
    exists, matching lickcalc validation expectations.
    """
    offsets: List[float] = []
    eps = 0.001
    for idx, onset in enumerate(onsets):
        dur = base_duration + rng.uniform(-jitter, jitter)
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
    clean_off = _offsets_from_onsets(clean_on, base_duration=0.060, jitter=0.004, rng=rng)

    boundary_on = [
        0.00,
        0.49,
        0.99,
        1.50,
        2.01,
        2.50,
        3.00,
        3.51,
        8.80,
        9.29,
        9.79,
        10.30,
    ]
    boundary_off = _offsets_from_onsets(boundary_on, base_duration=0.060, jitter=0.004, rng=rng)

    # Use slower intraburst timing here so ~0.30 s lick durations are valid
    # without offset/onset overlap.
    longlick_on = _build_burst_onsets(
        burst_sizes=[7, 8, 6],
        intra_ilis=[0.38, 0.42],
        interburst_gap=5.5,
        start_time=0.2,
    )
    longlick_off: List[float] = []
    duration_pattern = [0.29, 0.30, 0.31, 0.27, 0.33, 0.28]
    for idx, onset in enumerate(longlick_on):
        longlick_off.append(round(onset + duration_pattern[idx % len(duration_pattern)], 6))

    firstn_on = _build_burst_onsets(
        burst_sizes=[2, 4, 6, 8, 12, 3, 10],
        intra_ilis=[0.12, 0.12, 0.13, 0.14],
        interburst_gap=5.0,
        start_time=0.0,
    )
    firstn_off = _offsets_from_onsets(firstn_on, base_duration=0.060, jitter=0.006, rng=rng)

    return {
        "onset_clean": clean_on,
        "offset_clean": clean_off,
        "onset_ibi_boundary": boundary_on,
        "offset_ibi_boundary": boundary_off,
        "onset_longlick_boundary": longlick_on,
        "offset_longlick_boundary": longlick_off,
        "onset_firstn_depth": firstn_on,
        "offset_firstn_depth": firstn_off,
    }


def _build_validation_file(rng: Random) -> Dict[str, Sequence[float]]:
    """Validation stress cases: mismatch, ordering, monotonicity, sparse columns."""
    base_on = _build_burst_onsets(
        burst_sizes=[6, 7, 5],
        intra_ilis=[0.12, 0.12, 0.13],
        interburst_gap=5.4,
        start_time=0.0,
    )
    base_off = _offsets_from_onsets(base_on, base_duration=0.060, jitter=0.004, rng=rng)

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
    bad_order_off = [0.08, 0.09, 0.18, 0.34, 5.5, 5.69]

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

    firstn_lowvar_on = _build_burst_onsets(
        burst_sizes=[2, 6, 7, 8, 9, 10],
        intra_ilis=[0.12, 0.12],
        interburst_gap=5.2,
        start_time=0.0,
    )

    firstn_highvar_on = _build_burst_onsets(
        burst_sizes=[2, 6, 8, 10, 12],
        intra_ilis=[0.07, 0.12, 0.18, 0.24, 0.32, 0.41],
        interburst_gap=5.2,
        start_time=0.0,
    )

    dense_off = _offsets_from_onsets(dense_on, base_duration=0.060, jitter=0.006, rng=rng)
    firstn_lowvar_off = _offsets_from_onsets(firstn_lowvar_on, base_duration=0.060, jitter=0.004, rng=rng)

    return {
        "onset_sparse": sparse_on,
        "onset_dense": dense_on,
        "offset_dense": dense_off,
        "onset_trial_like": trial_like_on,
        "onset_firstn_lowvar": firstn_lowvar_on,
        "offset_firstn_lowvar": firstn_lowvar_off,
        "onset_firstn_highvar": firstn_highvar_on,
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
            "Contains ILIs around 0.49/0.50/0.51 s boundaries.",
            "Burst assignment changes around interburst threshold.",
        ],
        [
            "synthetic_core_cases.csv",
            "onset_longlick_boundary / offset_longlick_boundary",
            "threshold-boundary",
            "Lick durations around 0.29/0.30/0.31 s.",
            "Long-lick counts change near long-lick threshold.",
        ],
        [
            "synthetic_core_cases.csv",
            "onset_firstn_depth",
            "first-n",
            "Mixed burst depths for First n ILIs behavior.",
            "Higher n values reduce sample counts for late indices.",
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
        [
            "synthetic_analysis_cases.csv",
            "onset_firstn_lowvar",
            "first-n",
            "Low-variance first-n intraburst ILIs.",
            "Small SEM in First n ILIs plot.",
        ],
        [
            "synthetic_analysis_cases.csv",
            "onset_firstn_highvar",
            "first-n",
            "Wider intraburst ILI spread but still below typical IBI threshold.",
            "Larger SEM than low-variance case without threshold violations.",
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
