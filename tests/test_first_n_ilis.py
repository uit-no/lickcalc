import numpy as np
import unittest

from utils.calculations import compute_first_n_ili_summary


def _build_licks_with_removed_middle_burst():
    """Create licks where a short middle burst is removed by minburstlength.

    This guards against cross-burst slicing bugs where ILIs from removed bursts
    might leak into kept-burst first-n calculations.
    """
    burst_a = [0.00, 0.10, 0.20, 0.30]
    singleton = [1.30]  # short burst to be removed when minburstlength >= 3
    burst_b = [5.50, 5.62, 5.74, 5.86, 5.98]
    burst_c = [11.30, 11.42, 11.54, 11.66, 11.78]
    return burst_a + singleton + burst_b + burst_c


class TestFirstNIlis(unittest.TestCase):
    def test_first_n_matrix_values_stay_within_intraburst_threshold(self):
        ibi = 0.5
        summary = compute_first_n_ili_summary(
            lick_times=_build_licks_with_removed_middle_burst(),
            offset_times=None,
            ibi=ibi,
            minlicks=3,
            longlick_th=0.3,
            remove_long=False,
            n_ilis=10,
        )

        matrix = summary["matrix"]
        self.assertEqual(matrix.shape[1], 10)

        finite_vals = matrix[np.isfinite(matrix)]
        self.assertGreater(finite_vals.size, 0)
        self.assertTrue(np.all(finite_vals < ibi))
        self.assertTrue(np.all(finite_vals > 0.06))

    def test_first_n_sem_is_not_artificially_inflated_by_cross_burst_intervals(self):
        summary = compute_first_n_ili_summary(
            lick_times=_build_licks_with_removed_middle_burst(),
            offset_times=None,
            ibi=0.5,
            minlicks=3,
            longlick_th=0.3,
            remove_long=False,
            n_ilis=10,
        )

        sem = summary["sem"]
        finite_sem = sem[np.isfinite(sem)]

        # We should have at least one index with enough data for SEM.
        self.assertGreater(finite_sem.size, 0)

        # With tightly controlled synthetic ILIs (0.10-0.12), SEM should be small.
        self.assertLess(np.nanmax(finite_sem), 0.05)

    def test_first_n_mean_has_expected_prefix_on_controlled_data(self):
        # Two valid bursts after pre-ILI filtering with known first ILIs.
        # (The very first burst in a session has no pre_ili and is excluded by
        # trompy's default pre_ili > 4 criterion.)
        # Valid Burst A contributes [0.10, 0.10, 0.10]
        # Valid Burst B contributes [0.12, 0.12, 0.12, 0.12]
        licks = [
            0.00, 0.10,
            5.00, 5.10, 5.20, 5.30,
            10.50, 10.62, 10.74, 10.86, 10.98,
        ]

        summary = compute_first_n_ili_summary(
            lick_times=licks,
            offset_times=None,
            ibi=0.5,
            minlicks=3,
            longlick_th=0.3,
            remove_long=False,
            n_ilis=5,
        )

        mean = summary["mean"]
        self.assertEqual(mean.shape, (5,))

        # First 3 positions should be close to average of [0.10, 0.12] = 0.11
        self.assertTrue(np.isclose(mean[0], 0.11, atol=1e-6))
        self.assertTrue(np.isclose(mean[1], 0.11, atol=1e-6))
        self.assertTrue(np.isclose(mean[2], 0.11, atol=1e-6))


if __name__ == "__main__":
    unittest.main()
