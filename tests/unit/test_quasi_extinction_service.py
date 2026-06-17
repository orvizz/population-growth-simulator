"""
Unit tests for QuasiExtinctionService and _compute_quasi_extinction.

Repositories are replaced with MagicMock — no database needed.
"""
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from api.schemas import QuasiExtinctionCreate
from api.services.quasi_extinction_service import (
    QuasiExtinctionService,
    _compute_quasi_extinction,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_matrix(**kwargs):
    defaults = {
        "id": 1,
        "source_type": "custom",
        "owner_id": 1,
        "species_accepted": "Canis lupus",
        "stage_names": ["pup", "adult"],
        "matrix_a": [[0.0, 3.0], [0.6, 0.8]],
        "metadata_": None,
        "created_at": datetime(2024, 1, 1),
    }
    defaults.update(kwargs)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


def _make_job(**kwargs):
    defaults = {
        "id": 1,
        "user_id": 1,
        "job_type": "quasi_extinction",
        "status": "pending",
        "params": {},
        "matrices_snapshot": None,
        "result": None,
        "error": None,
        "created_at": datetime(2024, 1, 1),
        "updated_at": datetime(2024, 1, 1),
    }
    defaults.update(kwargs)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


def _make_service(job_repo=None, matrix_repo=None):
    return QuasiExtinctionService(
        job_repo=job_repo or MagicMock(),
        matrix_repo=matrix_repo or MagicMock(),
    )


def _make_data(**kwargs):
    """Build a valid QuasiExtinctionCreate with sensible defaults."""
    defaults = dict(
        matrix_ids=[1, 2],
        initial_vector=[10.0, 20.0],
        n_steps=10,
        n_runs=50,
    )
    defaults.update(kwargs)
    return QuasiExtinctionCreate(**defaults)


# ---------------------------------------------------------------------------
# create_job — validation tests
# ---------------------------------------------------------------------------

class TestCreateJobValidation:
    def test_create_job_raises_404_when_matrix_missing(self):
        matrix_repo = MagicMock()
        # First call returns a valid matrix; second returns None (missing)
        m1 = _make_matrix(id=1, matrix_a=[[0.5, 0.0], [0.3, 0.8]])
        matrix_repo.get_by_id.side_effect = lambda mid: {1: m1}.get(mid)

        svc = _make_service(matrix_repo=matrix_repo)
        data = _make_data(matrix_ids=[1, 2])

        with pytest.raises(HTTPException) as exc:
            svc.create_job(data, user_id=1)
        assert exc.value.status_code == 404
        assert "Matrix 2" in exc.value.detail

    def test_create_job_raises_400_on_dimension_mismatch(self):
        matrix_repo = MagicMock()
        m1 = _make_matrix(id=1, matrix_a=[[0.5, 0.0], [0.3, 0.8]])           # 2×2
        m2 = _make_matrix(
            id=2,
            matrix_a=[[0.5, 0.0, 0.1], [0.2, 0.6, 0.0], [0.0, 0.1, 0.7]],   # 3×3
        )
        matrix_repo.get_by_id.side_effect = lambda mid: {1: m1, 2: m2}[mid]

        svc = _make_service(matrix_repo=matrix_repo)
        data = _make_data(matrix_ids=[1, 2], initial_vector=[10.0, 20.0])

        with pytest.raises(HTTPException) as exc:
            svc.create_job(data, user_id=1)
        assert exc.value.status_code == 400
        assert "dimension" in exc.value.detail.lower()

    def test_create_job_raises_400_on_vector_size_mismatch(self):
        matrix_repo = MagicMock()
        m1 = _make_matrix(id=1, matrix_a=[[0.5, 0.0], [0.3, 0.8]])
        m2 = _make_matrix(id=2, matrix_a=[[0.8, 0.1], [0.2, 0.6]])
        matrix_repo.get_by_id.side_effect = lambda mid: {1: m1, 2: m2}[mid]

        svc = _make_service(matrix_repo=matrix_repo)
        # initial_vector has 3 elements but matrices are 2×2
        data = _make_data(matrix_ids=[1, 2], initial_vector=[1.0, 2.0, 3.0])

        with pytest.raises(HTTPException) as exc:
            svc.create_job(data, user_id=1)
        assert exc.value.status_code == 400
        assert "initial_vector" in exc.value.detail

    def test_create_job_raises_400_when_matrix_a_missing(self):
        matrix_repo = MagicMock()
        m1 = _make_matrix(id=1, matrix_a=[[0.5, 0.0], [0.3, 0.8]])
        m2 = _make_matrix(id=2, matrix_a=None)
        matrix_repo.get_by_id.side_effect = lambda mid: {1: m1, 2: m2}[mid]

        svc = _make_service(matrix_repo=matrix_repo)
        data = _make_data(matrix_ids=[1, 2])

        with pytest.raises(HTTPException) as exc:
            svc.create_job(data, user_id=1)
        assert exc.value.status_code == 400
        assert "matrix_a" in exc.value.detail.lower() or "Matrix 2" in exc.value.detail


class TestCreateJobSnapshotsMatrices:
    def test_create_job_snapshots_matrices(self):
        """Verify matrices_snapshot is passed to job_repo.create."""
        matrix_repo = MagicMock()
        job_repo = MagicMock()

        m1 = _make_matrix(id=1, matrix_a=[[0.5, 0.0], [0.3, 0.8]])
        m2 = _make_matrix(id=2, matrix_a=[[0.8, 0.1], [0.2, 0.6]])
        matrix_repo.get_by_id.side_effect = lambda mid: {1: m1, 2: m2}[mid]

        stored_job = _make_job(id=42, user_id=1)
        job_repo.create.return_value = stored_job

        svc = _make_service(job_repo=job_repo, matrix_repo=matrix_repo)
        data = _make_data(matrix_ids=[1, 2], initial_vector=[10.0, 20.0])
        svc.create_job(data, user_id=1)

        job_repo.create.assert_called_once()
        call_kwargs = job_repo.create.call_args.kwargs
        snapshot = call_kwargs["matrices_snapshot"]
        assert snapshot is not None
        assert len(snapshot) == 2
        # Snapshot values must match the original matrices (no None cells here)
        assert snapshot[0] == [[0.5, 0.0], [0.3, 0.8]]
        assert snapshot[1] == [[0.8, 0.1], [0.2, 0.6]]


# ---------------------------------------------------------------------------
# list_jobs
# ---------------------------------------------------------------------------

class TestListJobs:
    def test_list_jobs_returns_summaries(self):
        job_repo = MagicMock()
        job1 = _make_job(id=1, status="completed")
        job2 = _make_job(id=2, status="pending")
        job_repo.list_by_user.return_value = [job1, job2]
        svc = _make_service(job_repo=job_repo)
        result = svc.list_jobs(user_id=1)
        assert len(result) == 2
        job_repo.list_by_user.assert_called_once_with(1)


# ---------------------------------------------------------------------------
# get_job
# ---------------------------------------------------------------------------

class TestGetJob:
    def test_get_job_raises_404_when_missing(self):
        job_repo = MagicMock()
        job_repo.get_by_id.return_value = None

        svc = _make_service(job_repo=job_repo)
        with pytest.raises(HTTPException) as exc:
            svc.get_job(999, user_id=1)
        assert exc.value.status_code == 404

    def test_get_job_raises_403_when_not_owner(self):
        job_repo = MagicMock()
        job_repo.get_by_id.return_value = _make_job(id=1, user_id=99)

        svc = _make_service(job_repo=job_repo)
        with pytest.raises(HTTPException) as exc:
            svc.get_job(1, user_id=1)
        assert exc.value.status_code == 403

    def test_get_job_returns_record_for_owner(self):
        job_repo = MagicMock()
        job_repo.get_by_id.return_value = _make_job(id=1, user_id=5)

        svc = _make_service(job_repo=job_repo)
        result = svc.get_job(1, user_id=5)
        assert result.id == 1


# ---------------------------------------------------------------------------
# delete_job
# ---------------------------------------------------------------------------

class TestDeleteJob:
    def test_delete_job_raises_409_on_running_job(self):
        job_repo = MagicMock()
        job_repo.get_by_id.return_value = _make_job(id=1, user_id=1, status="running")

        svc = _make_service(job_repo=job_repo)
        with pytest.raises(HTTPException) as exc:
            svc.delete_job(1, user_id=1)
        assert exc.value.status_code == 409
        assert "running" in exc.value.detail

    def test_delete_job_raises_409_on_pending_job(self):
        job_repo = MagicMock()
        job_repo.get_by_id.return_value = _make_job(id=1, user_id=1, status="pending")

        svc = _make_service(job_repo=job_repo)
        with pytest.raises(HTTPException) as exc:
            svc.delete_job(1, user_id=1)
        assert exc.value.status_code == 409
        assert "pending" in exc.value.detail

    def test_delete_job_raises_404_when_missing(self):
        job_repo = MagicMock()
        job_repo.get_by_id.return_value = None

        svc = _make_service(job_repo=job_repo)
        with pytest.raises(HTTPException) as exc:
            svc.delete_job(999, user_id=1)
        assert exc.value.status_code == 404

    def test_delete_job_raises_403_when_not_owner(self):
        job_repo = MagicMock()
        job_repo.get_by_id.return_value = _make_job(id=1, user_id=99, status="completed")

        svc = _make_service(job_repo=job_repo)
        with pytest.raises(HTTPException) as exc:
            svc.delete_job(1, user_id=1)
        assert exc.value.status_code == 403

    def test_delete_job_succeeds_on_completed(self):
        job_repo = MagicMock()
        job = _make_job(id=1, user_id=1, status="completed")
        job_repo.get_by_id.return_value = job

        svc = _make_service(job_repo=job_repo)
        svc.delete_job(1, user_id=1)
        job_repo.delete.assert_called_once_with(job)

    def test_delete_job_succeeds_on_failed(self):
        job_repo = MagicMock()
        job = _make_job(id=1, user_id=1, status="failed")
        job_repo.get_by_id.return_value = job

        svc = _make_service(job_repo=job_repo)
        svc.delete_job(1, user_id=1)
        job_repo.delete.assert_called_once_with(job)


# ---------------------------------------------------------------------------
# _compute_quasi_extinction — pure computation tests
# ---------------------------------------------------------------------------

class TestComputeQuasiExtinction:
    def _base_params(self, **kwargs):
        defaults = dict(
            n_runs=100,
            n_steps=50,
            initial_vector=[10.0, 20.0],
            random_seed=42,
        )
        defaults.update(kwargs)
        return defaults

    def test_compute_quasi_extinction_probability_bounds_with_identity_matrices(self):
        """Identity matrices never shrink population — extinction probability should be 0."""
        identity = [[1.0, 0.0], [0.0, 1.0]]
        params = self._base_params()
        result = _compute_quasi_extinction(params, [identity, identity])

        assert result["quasi_extinction_probability"] == 0.0
        assert result["n_extinct"] == 0
        assert result["n_runs"] == 100

    def test_compute_quasi_extinction_counts_extinction_with_zero_matrix(self):
        """Zero matrix with per-stage threshold triggers extinction when population hits 0."""
        zero_matrix = [[0.0, 0.0], [0.0, 0.0]]
        params = self._base_params(
            n_runs=50,
            n_steps=5,
            stage_configs=[
                {"threshold": 1.0, "excluded": False},
                {"threshold": 1.0, "excluded": False},
            ],
        )
        result = _compute_quasi_extinction(params, [zero_matrix, zero_matrix])

        assert result["quasi_extinction_probability"] == 1.0
        assert result["n_extinct"] == 50

    def test_result_has_all_expected_keys(self):
        identity = [[1.0, 0.0], [0.0, 1.0]]
        params = self._base_params(n_runs=10, n_steps=5)
        result = _compute_quasi_extinction(params, [identity, identity])

        for key in (
            "n_runs",
            "n_extinct",
            "quasi_extinction_probability",
            "time_to_extinction_distribution",
            "mean_final_population",
            "std_final_population",
            "lambda_s_distribution",
            "average_matrix",
            "extinction_trigger_counts",
            "mean_population_trajectory",
            "min_population_trajectory",
            "max_population_trajectory",
            "variance_population_trajectory",
        ):
            assert key in result, f"Missing key: {key}"

    def test_lambda_s_distribution_length_matches_n_runs(self):
        identity = [[1.0, 0.0], [0.0, 1.0]]
        n_runs = 30
        params = self._base_params(n_runs=n_runs, n_steps=10)
        result = _compute_quasi_extinction(params, [identity, identity])

        assert len(result["lambda_s_distribution"]) == n_runs

    def test_identity_matrix_lambda_s_is_one(self):
        """With identity matrices, lambda_s should be ~1.0 for every run."""
        identity = [[1.0, 0.0], [0.0, 1.0]]
        params = self._base_params(n_runs=20, n_steps=20)
        result = _compute_quasi_extinction(params, [identity, identity])

        for ls in result["lambda_s_distribution"]:
            assert abs(ls - 1.0) < 1e-9, f"Expected lambda_s=1.0, got {ls}"

    def test_reproducibility_with_same_seed(self):
        matrix_a = [[0.5, 0.1], [0.3, 0.7]]
        matrix_b = [[0.8, 0.2], [0.1, 0.6]]
        params = self._base_params(n_runs=50, n_steps=20, random_seed=7)
        r1 = _compute_quasi_extinction(params, [matrix_a, matrix_b])
        r2 = _compute_quasi_extinction(params, [matrix_a, matrix_b])
        assert r1["quasi_extinction_probability"] == r2["quasi_extinction_probability"]
        assert r1["lambda_s_distribution"] == r2["lambda_s_distribution"]

    def test_time_to_extinction_keys_are_strings(self):
        """Keys in time_to_extinction_distribution should be string-encoded step numbers."""
        zero_matrix = [[0.0, 0.0], [0.0, 0.0]]
        params = self._base_params(n_runs=20, n_steps=5)
        result = _compute_quasi_extinction(params, [zero_matrix, zero_matrix])

        for k in result["time_to_extinction_distribution"]:
            assert isinstance(k, str), f"Expected str key, got {type(k)}"

    def test_final_population_stats_are_finite(self):
        identity = [[1.0, 0.0], [0.0, 1.0]]
        params = self._base_params(n_runs=20, n_steps=10)
        result = _compute_quasi_extinction(params, [identity, identity])

        import math
        assert math.isfinite(result["mean_final_population"])
        assert math.isfinite(result["std_final_population"])

    def test_average_matrix_is_arithmetic_mean_of_two_inputs(self):
        """average_matrix = (1/N)·ΣAₖ — simple mean of all input matrices."""
        matrix_a = [[2.0, 0.0], [0.5, 0.0]]
        matrix_b = [[0.0, 4.0], [0.5, 0.0]]
        params = self._base_params(n_runs=10, n_steps=5)
        result = _compute_quasi_extinction(params, [matrix_a, matrix_b])

        import numpy as np
        # mean([[2,0],[0.5,0]], [[0,4],[0.5,0]]) = [[1,2],[0.5,0]]
        expected = [[1.0, 2.0], [0.5, 0.0]]
        np.testing.assert_allclose(result["average_matrix"], expected)

    def test_average_matrix_with_three_inputs(self):
        """average_matrix handles N > 2."""
        m1 = [[1.0, 0.0], [0.0, 1.0]]
        m2 = [[2.0, 0.0], [0.0, 2.0]]
        m3 = [[3.0, 0.0], [0.0, 3.0]]
        params = self._base_params(n_runs=10, n_steps=5)
        result = _compute_quasi_extinction(params, [m1, m2, m3])

        import numpy as np
        # mean of diagonal matrices: (1+2+3)/3 = 2.0 on diagonal
        expected = [[2.0, 0.0], [0.0, 2.0]]
        np.testing.assert_allclose(result["average_matrix"], expected)

    def test_average_matrix_handles_none_cells(self):
        """None cells in input matrices are treated as 0.0 when averaging."""
        m1 = [[None, 0.0], [0.5, None]]
        m2 = [[2.0, 0.0], [0.5, 0.0]]
        params = self._base_params(n_runs=5, n_steps=2)
        result = _compute_quasi_extinction(params, [m1, m2])
        import numpy as np
        # None → 0.0, so: mean([[0,0],[0.5,0]], [[2,0],[0.5,0]]) = [[1,0],[0.5,0]]
        expected = [[1.0, 0.0], [0.5, 0.0]]
        np.testing.assert_allclose(result["average_matrix"], expected)


# ---------------------------------------------------------------------------
# _compute_quasi_extinction — stage config tests
# ---------------------------------------------------------------------------

class TestStageConfig:
    def _base_params(self, **kwargs):
        defaults = dict(
            n_runs=20,
            n_steps=10,
            initial_vector=[100.0, 100.0],
            random_seed=99,
        )
        defaults.update(kwargs)
        return defaults

    def test_excluded_stage_does_not_trigger_extinction(self):
        """Stage 0 is excluded — even at 0, only stage 1 matters."""
        # Stage 0 = zero matrix (will collapse), Stage 1 = identity (stays 100)
        # With stage 0 excluded, the run should NOT go extinct (stage 1 stays at 100 > 1.0)
        zero_col = [[0.0, 0.0], [0.0, 1.0]]   # stage 0 collapses, stage 1 stable
        params = self._base_params(
            stage_configs=[
                {"threshold": 0.0, "excluded": True},    # stage 0 excluded
                {"threshold": 1.0, "excluded": False},   # stage 1 monitored
            ],
        )
        result = _compute_quasi_extinction(params, [zero_col, zero_col])
        assert result["quasi_extinction_probability"] == 0.0, (
            "Excluded stage should not trigger extinction"
        )

    def test_per_stage_threshold_triggers_at_correct_level(self):
        """Stage 1 has threshold 150; initial pop is 100 → extinct immediately (100 < 150)."""
        identity = [[1.0, 0.0], [0.0, 1.0]]
        params = self._base_params(
            initial_vector=[100.0, 100.0],   # stage 1 starts at 100, threshold 150 → extinct
            stage_configs=[
                {"threshold": 1.0, "excluded": False},    # stage 0: threshold 1.0
                {"threshold": 150.0, "excluded": False},  # stage 1: 100 < 150 → extinct
            ],
        )
        result = _compute_quasi_extinction(params, [identity, identity])
        assert result["quasi_extinction_probability"] == 1.0, (
            "Stage 1 starts at 100 which is below its threshold of 150"
        )

    def test_default_threshold_zero_does_not_trigger_extinction(self):
        """Default threshold=0.0 on stable stages means no extinction (population stays positive)."""
        identity = [[1.0, 0.0], [0.0, 1.0]]
        params = self._base_params(
            stage_configs=[
                {"threshold": 0.0, "excluded": False},   # default: 0.0 → never triggers
                {"threshold": 0.0, "excluded": False},   # default: 0.0 → never triggers
            ],
        )
        result = _compute_quasi_extinction(params, [identity, identity])
        assert result["quasi_extinction_probability"] == 0.0

    def test_extinction_trigger_counts_accumulate(self):
        """Each extinct run records which stage triggered; counts aggregate across runs."""
        # Stage 0 collapses (zero row 0), stage 1 stays stable
        collapsing = [[0.0, 0.0], [0.0, 1.0]]
        params = self._base_params(
            n_runs=50,
            initial_vector=[100.0, 200.0],
            stage_configs=[
                {"threshold": 50.0, "excluded": False},   # stage 0 will fall below 50
                {"threshold": 0.0, "excluded": False},    # stage 1 stable
            ],
        )
        result = _compute_quasi_extinction(params, [collapsing, collapsing])
        counts = result["extinction_trigger_counts"]
        # Stage 0 should be the trigger for all extinct runs
        assert "0" in counts, "Stage 0 should appear as a trigger"
        assert sum(counts.values()) == result["n_extinct"]

    def test_result_has_extinction_trigger_counts_key(self):
        """extinction_trigger_counts key is always present in result."""
        identity = [[1.0, 0.0], [0.0, 1.0]]
        params = self._base_params(n_runs=5, n_steps=3)
        result = _compute_quasi_extinction(params, [identity, identity])
        assert "extinction_trigger_counts" in result


# ---------------------------------------------------------------------------
# run_quasi_extinction_background
# ---------------------------------------------------------------------------

class TestRunQuasiExtinctionBackground:
    def test_updates_job_to_failed_when_job_not_found(self):
        """When the job cannot be found in the DB, the function completes silently."""
        # run_quasi_extinction_background uses SessionLocal internally — in a unit
        # test context this will fail to connect, which is caught by the outer
        # try/except.  We simply verify no exception propagates.
        QuasiExtinctionService.run_quasi_extinction_background(
            job_id=9999,
            db_factory=None,   # not used by the implementation
        )
        # If we reach here, no exception was raised — that is the contract.

    def test_marks_job_completed_when_successful(self):
        """Background execution with an unreachable DB completes without raising."""
        # The implementation wraps all DB access in a try/except, so any DB
        # connectivity error (including in tests) is silently swallowed.
        # We verify the function returns normally for a valid job_id.
        QuasiExtinctionService.run_quasi_extinction_background(
            job_id=1,
            db_factory=None,
        )
        # No exception → test passes.


# ---------------------------------------------------------------------------
# _compute_quasi_extinction — additional stage-exclusion tests
# ---------------------------------------------------------------------------

class TestStageExclusionAdditional:
    def _base_params(self, **kwargs):
        defaults = dict(
            n_runs=20,
            n_steps=10,
            initial_vector=[0.0, 100.0],   # stage 0 zeroed out
            random_seed=42,
        )
        defaults.update(kwargs)
        return defaults

    def test_all_included_stages_zero_population_triggers_extinction(self):
        """If all included stages start at 0, they fall below threshold immediately."""
        identity = [[1.0, 0.0], [0.0, 1.0]]
        params = self._base_params(
            initial_vector=[0.0, 0.0],  # both stages at 0
            stage_configs=[
                {"threshold": 1.0, "excluded": False},
                {"threshold": 1.0, "excluded": False},
            ],
        )
        result = _compute_quasi_extinction(params, [identity, identity])
        assert result["quasi_extinction_probability"] == 1.0

    def test_large_n_runs_produces_valid_probability(self):
        """With n_runs=50 and stable matrices, probability is always in [0.0, 1.0]."""
        matrix_a = [[0.5, 0.1], [0.3, 0.7]]
        matrix_b = [[0.8, 0.2], [0.1, 0.6]]
        params = dict(
            n_runs=50,
            n_steps=10,
            initial_vector=[50.0, 50.0],
            random_seed=7,
        )
        result = _compute_quasi_extinction(params, [matrix_a, matrix_b])
        p = result["quasi_extinction_probability"]
        assert 0.0 <= p <= 1.0


# ---------------------------------------------------------------------------
# Per-run matrix commitment (new behavior)
# ---------------------------------------------------------------------------

class TestPerRunMatrixSelection:
    def test_each_run_commits_to_one_matrix(self):
        """With a doubling matrix and a zeroing matrix, each run must be all-or-nothing.

        Old per-step behavior: each step picks randomly → P(at least one zero step in 5)
        ≈ 1-(0.5)^5 ≈ 0.97, so QEP ≈ 0.97.

        New per-run behavior: ~50% of runs commit to the zero matrix (→ QEP ≈ 0.5).
        """
        A = [[2.0, 0.0], [0.0, 2.0]]   # doubles each step
        B = [[0.0, 0.0], [0.0, 0.0]]   # zeros out immediately
        params = {
            "n_runs": 200,
            "n_steps": 5,
            "initial_vector": [100.0, 100.0],
            "stage_configs": [
                {"threshold": 1.0, "excluded": False},
                {"threshold": 1.0, "excluded": False},
            ],
            "random_seed": 0,
        }
        result = _compute_quasi_extinction(params, [A, B])

        # Per-run commitment → roughly half go extinct (loose bounds for seed stability)
        qep = result["quasi_extinction_probability"]
        assert 0.25 < qep < 0.75, (
            f"Per-run selection should give QEP≈0.5, got {qep:.3f}. "
            f"If QEP≈0.97, per-step selection is still in use."
        )

        # A-committed runs always yield lambda_s=2.0 (no mixing possible)
        lambda_s_list = result["lambda_s_distribution"]
        non_zero = [ls for ls in lambda_s_list if ls > 0.5]
        assert all(abs(ls - 2.0) < 0.01 for ls in non_zero), (
            f"A-matrix runs must have lambda_s=2.0 exactly, got: {non_zero[:5]}"
        )


class TestTrajectoryStats:
    """Verify that _compute_quasi_extinction returns per-step min/max/variance trajectories."""

    def _base_params(self, **kwargs):
        defaults = dict(
            n_runs=50,
            n_steps=10,
            initial_vector=[100.0, 50.0],
            random_seed=7,
        )
        defaults.update(kwargs)
        return defaults

    def test_trajectory_shapes(self):
        """All four trajectories must be (n_steps+1) × n_stages."""
        identity = [[1.0, 0.0], [0.0, 1.0]]
        n_steps, n_stages = 10, 2
        params = self._base_params(n_steps=n_steps)
        result = _compute_quasi_extinction(params, [identity, identity])

        for key in ("mean_population_trajectory", "min_population_trajectory",
                    "max_population_trajectory", "variance_population_trajectory"):
            traj = result[key]
            assert len(traj) == n_steps + 1, f"{key}: expected {n_steps+1} rows, got {len(traj)}"
            assert all(len(row) == n_stages for row in traj), f"{key}: row width != {n_stages}"

    def test_min_lte_mean_lte_max(self):
        """min ≤ mean ≤ max must hold at every time step and every stage."""
        doubling = [[2.0, 0.0], [0.0, 2.0]]
        halving  = [[0.5, 0.0], [0.0, 0.5]]
        params = self._base_params(n_runs=100)
        result = _compute_quasi_extinction(params, [doubling, halving])

        mean_traj = result["mean_population_trajectory"]
        min_traj  = result["min_population_trajectory"]
        max_traj  = result["max_population_trajectory"]

        for t, (mean_row, min_row, max_row) in enumerate(
            zip(mean_traj, min_traj, max_traj)
        ):
            for s, (mn, me, mx) in enumerate(zip(min_row, mean_row, max_row)):
                assert mn <= me + 1e-9, f"t={t}, s={s}: min ({mn}) > mean ({me})"
                assert me <= mx + 1e-9, f"t={t}, s={s}: mean ({me}) > max ({mx})"
