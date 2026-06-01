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
        extinction_threshold=1.0,
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
            extinction_threshold=1.0,
            random_seed=42,
        )
        defaults.update(kwargs)
        return defaults

    def test_compute_quasi_extinction_probability_bounds_with_identity_matrices(self):
        """Identity matrices never shrink population — extinction probability should be 0."""
        identity = [[1.0, 0.0], [0.0, 1.0]]
        params = self._base_params(
            extinction_threshold=0.5,  # well below initial_vector sum (30)
        )
        result = _compute_quasi_extinction(params, [identity, identity])

        assert result["quasi_extinction_probability"] == 0.0
        assert result["n_extinct"] == 0
        assert result["n_runs"] == 100

    def test_compute_quasi_extinction_counts_extinction_with_zero_matrix(self):
        """Zero matrix drives population to zero — all runs should go extinct."""
        zero_matrix = [[0.0, 0.0], [0.0, 0.0]]
        params = self._base_params(
            extinction_threshold=1.0,
            n_runs=50,
            n_steps=5,
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
            "extinction_threshold",
            "time_to_extinction_distribution",
            "mean_final_population",
            "std_final_population",
            "lambda_s_distribution",
            "average_matrix",
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
