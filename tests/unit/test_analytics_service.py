"""
Unit tests for api/services/analytics_service.py.

All tests use a 2×2 Leslie matrix A = [[0.0, 3.0], [0.6, 0.8]] whose
dominant eigenvalue is ≈ 1.4659. No database or HTTP layer is touched.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from api.services.analytics_service import (
    compute_deterministic_analytics,
    compute_stochastic_analytics,
)

# ---------------------------------------------------------------------------
# Shared fixtures / constants
# ---------------------------------------------------------------------------

A2x2 = [[0.0, 3.0], [0.6, 0.8]]  # 2×2 Leslie matrix used throughout

# Pre-compute expected dominant eigenvalue once so all tests share the same reference.
_EIGVALS_2x2 = np.linalg.eigvals(np.array(A2x2, dtype=float))
LAMBDA_1_EXPECTED = float(_EIGVALS_2x2[np.argmax(_EIGVALS_2x2.real)].real)  # ≈ 1.4659


# ---------------------------------------------------------------------------
# compute_deterministic_analytics
# ---------------------------------------------------------------------------

class TestDeterministicAnalytics:

    def test_lambda_1_correct(self):
        """λ₁ must match the dominant eigenvalue from np.linalg.eigvals."""
        result = compute_deterministic_analytics(A2x2)
        assert result["lambda_1"] == pytest.approx(LAMBDA_1_EXPECTED, rel=1e-6)

    def test_stable_stage_sums_to_one(self):
        """stable_stage_distribution must sum to 1.0."""
        result = compute_deterministic_analytics(A2x2)
        dist = result["stable_stage_distribution"]
        assert sum(dist) == pytest.approx(1.0, abs=1e-9)

    def test_stable_stage_non_negative(self):
        """All entries in stable_stage_distribution must be ≥ 0."""
        result = compute_deterministic_analytics(A2x2)
        assert all(v >= 0 for v in result["stable_stage_distribution"])

    def test_elasticities_sum_to_one(self):
        """Sum of all elasticity entries must equal ≈ 1.0 for a non-negative matrix."""
        result = compute_deterministic_analytics(A2x2)
        total = sum(cell for row in result["elasticities"] for cell in row)
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_none_cells_treated_as_zero(self):
        """A matrix with None cells should produce the same result as explicit 0.0 cells."""
        A_with_none = [[None, 3.0], [0.6, 0.8]]
        result_none = compute_deterministic_analytics(A_with_none)
        result_zero = compute_deterministic_analytics(A2x2)
        assert result_none["lambda_1"] == pytest.approx(result_zero["lambda_1"], rel=1e-9)
        for r_none, r_zero in zip(result_none["stable_stage_distribution"],
                                  result_zero["stable_stage_distribution"]):
            assert r_none == pytest.approx(r_zero, abs=1e-9)

    def test_stage_names_passthrough(self):
        """stage_names must be returned unchanged in the result dict."""
        names = ["juvenile", "adult"]
        result = compute_deterministic_analytics(A2x2, stage_names=names)
        assert result["stage_names"] == names

    def test_stage_names_none_passthrough(self):
        """When no stage_names provided, result['stage_names'] must be None."""
        result = compute_deterministic_analytics(A2x2)
        assert result["stage_names"] is None

    def test_analytics_reliable_true_for_deterministic(self):
        """analytics_reliable must be True for a well-conditioned matrix."""
        result = compute_deterministic_analytics(A2x2)
        assert result["analytics_reliable"] is True

    def test_sensitivities_shape(self):
        """sensitivities must be a 2×2 list for a 2×2 input matrix."""
        result = compute_deterministic_analytics(A2x2)
        S = result["sensitivities"]
        assert len(S) == 2
        assert all(len(row) == 2 for row in S)

    def test_reproductive_value_normalised_first_element_one(self):
        """reproductive_value must have first element equal to 1.0."""
        result = compute_deterministic_analytics(A2x2)
        assert result["reproductive_value"][0] == pytest.approx(1.0, abs=1e-9)

    def test_reproductive_value_non_negative(self):
        """All entries in reproductive_value must be ≥ 0."""
        result = compute_deterministic_analytics(A2x2)
        assert all(v >= 0 for v in result["reproductive_value"])

    def test_zero_matrix_analytics_reliable_false(self):
        """A zero matrix has λ₁ = 0, so analytics_reliable must be False."""
        zero = [[0.0, 0.0], [0.0, 0.0]]
        result = compute_deterministic_analytics(zero)
        assert result["analytics_reliable"] is False
        # Sensitivities and elasticities must all be zero
        assert all(cell == 0.0 for row in result["sensitivities"] for cell in row)
        assert all(cell == 0.0 for row in result["elasticities"] for cell in row)


# ---------------------------------------------------------------------------
# compute_stochastic_analytics
# ---------------------------------------------------------------------------

class TestStochasticAnalytics:

    # Two slightly different 2×2 matrices for stochastic tests
    A0 = [[0.0, 3.0], [0.6, 0.8]]
    A1 = [[0.0, 2.5], [0.5, 0.9]]

    def _run_sim(self, matrices, seq, n_steps, seed=42):
        """Helper: runs the deterministic algorithm to build result_history."""
        rng = np.random.default_rng(seed)
        arrays = [np.array([[0.0 if v is None else float(v) for v in row] for row in m], dtype=float)
                  for m in matrices]
        v = np.array([10.0, 5.0], dtype=float)
        history = [v.tolist()]
        for idx in seq:
            v = arrays[idx] @ v
            history.append(v.tolist())
        return history

    def test_lambda_s_positive(self):
        """λ_s must be positive for a growing population."""
        seq = [0] * 50
        history = self._run_sim([self.A0, self.A1], seq, n_steps=50)
        result = compute_stochastic_analytics(
            [self.A0, self.A1], seq, history
        )
        assert result["lambda_s"] > 0

    def test_mean_matrix_weighted_correctly(self):
        """With matrix_sequence = [0, 0, 0, 1], mean_matrix = 0.75*A0 + 0.25*A1."""
        seq = [0, 0, 0, 1]
        history = self._run_sim([self.A0, self.A1], seq, n_steps=4)
        result = compute_stochastic_analytics(
            [self.A0, self.A1], seq, history
        )
        A0_arr = np.array(self.A0, dtype=float)
        A1_arr = np.array(self.A1, dtype=float)
        expected = (0.75 * A0_arr + 0.25 * A1_arr).tolist()
        for row_r, row_e in zip(result["mean_matrix"], expected):
            for val_r, val_e in zip(row_r, row_e):
                assert val_r == pytest.approx(val_e, abs=1e-9)

    def test_analytics_reliable_false_when_few_steps(self):
        """analytics_reliable must be False when len(matrix_sequence) < threshold."""
        seq = [0] * 5  # 5 steps < default threshold of 20
        history = self._run_sim([self.A0, self.A1], seq, n_steps=5)
        result = compute_stochastic_analytics(
            [self.A0, self.A1], seq, history, n_steps_threshold=20
        )
        assert result["analytics_reliable"] is False

    def test_analytics_reliable_true_when_enough_steps(self):
        """analytics_reliable must be True when len(matrix_sequence) >= threshold."""
        seq = [0] * 20
        history = self._run_sim([self.A0, self.A1], seq, n_steps=20)
        result = compute_stochastic_analytics(
            [self.A0, self.A1], seq, history, n_steps_threshold=20
        )
        assert result["analytics_reliable"] is True

    def test_lambda_s_formula_constant_sequence(self):
        """When all steps use the same matrix, λ_s ≈ λ₁ of that matrix.

        For a constant sequence the stochastic and deterministic growth rates
        converge (they are identical in the limit). With 200 steps from a
        starting vector not aligned with the dominant eigenvector there may
        still be a small transient error; we use a relaxed tolerance of 1%.
        """
        seq = [0] * 200
        history = self._run_sim([self.A0, self.A1], seq, n_steps=200)
        result = compute_stochastic_analytics(
            [self.A0, self.A1], seq, history
        )
        det = compute_deterministic_analytics(self.A0)
        lambda_1 = det["lambda_1"]
        # Relative error must be within 1%
        assert abs(result["lambda_s"] - lambda_1) / lambda_1 < 0.01

    def test_stage_names_passthrough(self):
        """stage_names must be returned unchanged."""
        seq = [0] * 25
        history = self._run_sim([self.A0, self.A1], seq, n_steps=25)
        names = ["juvenile", "adult"]
        result = compute_stochastic_analytics(
            [self.A0, self.A1], seq, history, stage_names=names
        )
        assert result["stage_names"] == names

    def test_elasticities_of_mean_sum_to_one(self):
        """Elasticities of Ā must sum to ≈ 1.0 (non-negative irreducible mean matrix)."""
        seq = [0] * 50
        history = self._run_sim([self.A0, self.A1], seq, n_steps=50)
        result = compute_stochastic_analytics(
            [self.A0, self.A1], seq, history
        )
        total = sum(cell for row in result["elasticities_of_mean"] for cell in row)
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_stable_stage_distribution_of_mean_sums_to_one(self):
        """stable_stage_distribution_of_mean must sum to 1."""
        seq = [0, 1] * 30  # alternating
        history = self._run_sim([self.A0, self.A1], seq, n_steps=60)
        result = compute_stochastic_analytics(
            [self.A0, self.A1], seq, history
        )
        dist = result["stable_stage_distribution_of_mean"]
        assert sum(dist) == pytest.approx(1.0, abs=1e-9)
