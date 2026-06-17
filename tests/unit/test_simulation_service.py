"""
Unit tests for SimulationService (api/services/simulation_service.py).

Repositories are replaced with MagicMock — no database needed.
"""
from datetime import datetime
from unittest.mock import MagicMock

import numpy as np
import pytest
from fastapi import HTTPException

from api.schemas import SimulationCreate, SimulationImport
from api.services.simulation_service import SimulationService


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


def _make_sim_run(**kwargs):
    defaults = {
        "id": 1,
        "user_id": 1,
        "name": "Test sim",
        "matrix_id": 1,
        "matrix_ids": None,
        "stochastic": False,
        "n_steps": 3,
        "random_seed": None,
        "stage_names": ["pup", "adult"],
        "initial_vector": [10.0, 20.0],
        "result_history": [[10.0, 20.0], [60.0, 22.0], [66.0, 53.6], [160.8, 82.48]],
        "created_at": datetime(2024, 1, 1),
        "matrices_snapshot": [[[0.0, 3.0], [0.6, 0.8]]],
        "matrix_sequence": None,
        "analytics": {
            "lambda_1": 1.46,
            "stable_stage_distribution": [0.4, 0.6],
            "reproductive_value": [1.0, 1.2],
            "sensitivities": [[0.1, 0.2], [0.3, 0.4]],
            "elasticities": [[0.1, 0.2], [0.3, 0.4]],
            "analytics_reliable": True,
        },
        "n_runs": None,
        "result_variance": None,
        "result_min_history": None,
        "result_max_history": None,
    }
    defaults.update(kwargs)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


def _make_service(matrix_repo=None, sim_repo=None):
    return SimulationService(
        matrix_repo=matrix_repo or MagicMock(),
        sim_repo=sim_repo or MagicMock(),
    )


# ---------------------------------------------------------------------------
# Core algorithms (static/classmethod — no mocks needed)
# ---------------------------------------------------------------------------

class TestToArray:
    def test_converts_none_to_zero(self):
        arr = SimulationService._to_array([[None, 1.0], [0.5, None]])
        assert arr[0, 0] == 0.0
        assert arr[1, 1] == 0.0

    def test_preserves_float_values(self):
        arr = SimulationService._to_array([[1.5, 2.0], [3.0, 4.5]])
        np.testing.assert_array_equal(arr, [[1.5, 2.0], [3.0, 4.5]])

    def test_returns_float_dtype(self):
        arr = SimulationService._to_array([[1, 2], [3, 4]])
        assert arr.dtype == float


class TestComputeDeterministic:
    def test_history_length_is_n_steps_plus_one(self):
        A = [[1.0, 0.0], [0.0, 1.0]]  # identity
        history = SimulationService._compute_deterministic(A, [1.0, 2.0], n_steps=5)
        assert len(history) == 6  # initial + 5 steps

    def test_identity_matrix_leaves_vector_unchanged(self):
        A = [[1.0, 0.0], [0.0, 1.0]]
        v0 = [3.0, 7.0]
        history = SimulationService._compute_deterministic(A, v0, n_steps=4)
        for step in history:
            assert step == pytest.approx(v0)

    def test_first_element_is_initial_vector(self):
        A = [[0.5, 0.0], [0.3, 0.8]]
        v0 = [100.0, 0.0]
        history = SimulationService._compute_deterministic(A, v0, n_steps=3)
        assert history[0] == pytest.approx(v0)

    def test_single_step_matches_manual_multiplication(self):
        A = [[0.0, 3.0], [0.6, 0.8]]
        v0 = [10.0, 20.0]
        history = SimulationService._compute_deterministic(A, v0, n_steps=1)
        expected = [0.0 * 10 + 3.0 * 20, 0.6 * 10 + 0.8 * 20]
        assert history[1] == pytest.approx(expected)

    def test_none_cells_treated_as_zero(self):
        A = [[None, 2.0], [1.0, None]]
        history = SimulationService._compute_deterministic(A, [1.0, 1.0], n_steps=1)
        assert history[1] == pytest.approx([2.0, 1.0])


class TestComputeStochastic:
    def test_run_matrix_sequence_length_equals_n_runs(self):
        A = [[1.0, 0.0], [0.0, 1.0]]
        B = [[2.0, 0.0], [0.0, 2.0]]
        mean_h, var_h, min_h, max_h, run_seq = SimulationService._compute_stochastic(
            matrices=[A, B], initial_vector=[1.0, 1.0], n_steps=5, n_runs=8, random_seed=0
        )
        assert len(run_seq) == 8
        assert all(idx in (0, 1) for idx in run_seq)

    def test_history_shapes(self):
        A = [[1.0, 0.0], [0.0, 1.0]]
        mean_h, var_h, min_h, max_h, _ = SimulationService._compute_stochastic(
            matrices=[A, A], initial_vector=[1.0, 2.0], n_steps=3, n_runs=5, random_seed=0
        )
        assert len(mean_h) == 4      # n_steps + 1
        assert len(mean_h[0]) == 2   # n_stages
        assert len(var_h) == 4
        assert len(min_h) == 4
        assert len(max_h) == 4

    def test_single_run_zero_variance(self):
        A = [[1.5, 0.0], [0.0, 1.5]]
        mean_h, var_h, min_h, max_h, _ = SimulationService._compute_stochastic(
            matrices=[A, A], initial_vector=[1.0, 1.0], n_steps=3, n_runs=1, random_seed=0
        )
        for row in var_h:
            assert all(abs(x) < 1e-12 for x in row)
        for t in range(4):
            assert mean_h[t] == pytest.approx(min_h[t])
            assert mean_h[t] == pytest.approx(max_h[t])

    def test_min_le_mean_le_max(self):
        A = [[2.0, 0.0], [0.0, 2.0]]
        B = [[0.5, 0.0], [0.0, 0.5]]
        mean_h, var_h, min_h, max_h, _ = SimulationService._compute_stochastic(
            matrices=[A, B], initial_vector=[10.0, 5.0], n_steps=5, n_runs=20, random_seed=42
        )
        for t in range(6):
            for i in range(2):
                assert min_h[t][i] <= mean_h[t][i] + 1e-10
                assert mean_h[t][i] <= max_h[t][i] + 1e-10

    def test_reproducible_with_seed(self):
        A = [[1.0, 0.0], [0.0, 1.0]]
        B = [[2.0, 0.0], [0.0, 2.0]]
        r1 = SimulationService._compute_stochastic([A, B], [1.0, 1.0], 5, 10, random_seed=77)
        r2 = SimulationService._compute_stochastic([A, B], [1.0, 1.0], 5, 10, random_seed=77)
        assert r1[0] == r2[0]   # same mean_h
        assert r1[4] == r2[4]   # same run_seq

    def test_all_runs_commit_to_single_matrix(self):
        """Each run should use ONE matrix for all steps: result is bimodal, never mixed."""
        A = [[2.0, 0.0], [0.0, 2.0]]   # doubles each step: v=[1,1] → [8,8] after 3 steps
        B = [[0.0, 0.0], [0.0, 0.0]]   # zeros out: v=[1,1] → [0,0] after 1 step
        mean_h, var_h, min_h, max_h, _ = SimulationService._compute_stochastic(
            matrices=[A, B], initial_vector=[1.0, 1.0], n_steps=3, n_runs=100, random_seed=0
        )
        # All runs start at 1.0
        assert mean_h[0][0] == pytest.approx(1.0)
        # After 3 steps: A-runs → 8.0, B-runs → 0.0. No intermediate values possible.
        assert min_h[3][0] == pytest.approx(0.0)
        assert max_h[3][0] == pytest.approx(8.0)


class TestValidateVector:
    def test_correct_dimension_passes(self):
        SimulationService._validate_vector([1.0, 2.0], dim=2)  # no exception

    def test_wrong_dimension_raises_400(self):
        with pytest.raises(HTTPException) as exc:
            SimulationService._validate_vector([1.0, 2.0, 3.0], dim=2)
        assert exc.value.status_code == 400
        assert "initial_vector" in exc.value.detail


class TestSnapshotMatrices:
    def test_wraps_single_matrix_in_list(self):
        m = [[0.0, 3.0], [0.6, 0.8]]
        result = SimulationService.snapshot_matrices([m])
        assert len(result) == 1
        assert result[0] == [[0.0, 3.0], [0.6, 0.8]]

    def test_converts_none_to_zero(self):
        m = [[None, 3.0], [0.6, None]]
        result = SimulationService.snapshot_matrices([m])
        assert result[0][0][0] == 0.0
        assert result[0][1][1] == 0.0

    def test_multiple_matrices_preserved(self):
        m1 = [[0.5, 0.0], [0.3, 0.8]]
        m2 = [[0.8, 0.1], [0.2, 0.6]]
        result = SimulationService.snapshot_matrices([m1, m2])
        assert len(result) == 2


# ---------------------------------------------------------------------------
# run_ephemeral — deterministic
# ---------------------------------------------------------------------------

class TestRunEphemeralDeterministic:
    def _data(self, **kw):
        return SimulationCreate(matrix_id=1, initial_vector=[10.0, 20.0], n_steps=3, **kw)

    def test_returns_result_with_correct_shape(self):
        matrix_repo = MagicMock()
        matrix_repo.get_by_id.return_value = _make_matrix()
        svc = _make_service(matrix_repo=matrix_repo)
        result = svc.run_ephemeral(self._data())
        assert result.stochastic is False
        assert result.matrix_id == 1
        assert result.matrix_ids is None
        assert len(result.result_history) == 4  # initial + 3 steps

    def test_raises_404_when_matrix_not_found(self):
        matrix_repo = MagicMock()
        matrix_repo.get_by_id.return_value = None
        svc = _make_service(matrix_repo=matrix_repo)
        with pytest.raises(HTTPException) as exc:
            svc.run_ephemeral(self._data())
        assert exc.value.status_code == 404

    def test_raises_400_when_matrix_a_is_empty(self):
        matrix_repo = MagicMock()
        matrix_repo.get_by_id.return_value = _make_matrix(matrix_a=None)
        svc = _make_service(matrix_repo=matrix_repo)
        with pytest.raises(HTTPException) as exc:
            svc.run_ephemeral(self._data())
        assert exc.value.status_code == 400

    def test_raises_400_when_vector_size_mismatches(self):
        matrix_repo = MagicMock()
        matrix_repo.get_by_id.return_value = _make_matrix(matrix_a=[[0.5, 0.0], [0.3, 0.8]])
        svc = _make_service(matrix_repo=matrix_repo)
        data = SimulationCreate(matrix_id=1, initial_vector=[1.0, 2.0, 3.0], n_steps=1)
        with pytest.raises(HTTPException) as exc:
            svc.run_ephemeral(data)
        assert exc.value.status_code == 400

    def test_stage_names_and_species_forwarded(self):
        matrix_repo = MagicMock()
        m = _make_matrix(stage_names=["s1", "s2"], species_accepted="Felis catus")
        matrix_repo.get_by_id.return_value = m
        svc = _make_service(matrix_repo=matrix_repo)
        result = svc.run_ephemeral(self._data())
        assert result.stage_names == ["s1", "s2"]
        assert result.species_accepted == "Felis catus"


# ---------------------------------------------------------------------------
# run_ephemeral — stochastic
# ---------------------------------------------------------------------------

class TestRunEphemeralStochastic:
    def _data(self, **kw):
        return SimulationCreate(matrix_ids=[1, 2], initial_vector=[10.0, 20.0], n_steps=5, **kw)

    def _two_matrices(self, matrix_repo):
        m1 = _make_matrix(id=1, matrix_a=[[0.5, 0.0], [0.3, 0.8]])
        m2 = _make_matrix(id=2, matrix_a=[[0.8, 0.1], [0.2, 0.6]])
        matrix_repo.get_by_id.side_effect = lambda mid: {1: m1, 2: m2}[mid]
        return m1, m2

    def test_returns_stochastic_result(self):
        matrix_repo = MagicMock()
        self._two_matrices(matrix_repo)
        svc = _make_service(matrix_repo=matrix_repo)
        result = svc.run_ephemeral(self._data(random_seed=42))
        assert result.stochastic is True
        assert result.matrix_id is None
        assert result.matrix_ids == [1, 2]
        assert len(result.result_history) == 6

    def test_raises_404_when_any_matrix_not_found(self):
        matrix_repo = MagicMock()
        matrix_repo.get_by_id.side_effect = lambda mid: _make_matrix(id=mid) if mid == 1 else None
        svc = _make_service(matrix_repo=matrix_repo)
        with pytest.raises(HTTPException) as exc:
            svc.run_ephemeral(self._data())
        assert exc.value.status_code == 404

    def test_raises_400_when_any_matrix_a_missing(self):
        matrix_repo = MagicMock()
        m1 = _make_matrix(id=1, matrix_a=[[0.5, 0.0], [0.3, 0.8]])
        m2 = _make_matrix(id=2, matrix_a=None)
        matrix_repo.get_by_id.side_effect = lambda mid: {1: m1, 2: m2}[mid]
        svc = _make_service(matrix_repo=matrix_repo)
        with pytest.raises(HTTPException) as exc:
            svc.run_ephemeral(self._data())
        assert exc.value.status_code == 400

    def test_raises_400_on_dimension_mismatch_between_matrices(self):
        matrix_repo = MagicMock()
        m1 = _make_matrix(id=1, matrix_a=[[0.5, 0.0], [0.3, 0.8]])           # 2×2
        m2 = _make_matrix(id=2, matrix_a=[[0.5, 0.0, 0.1], [0.2, 0.6, 0.0], [0.0, 0.1, 0.7]])  # 3×3
        matrix_repo.get_by_id.side_effect = lambda mid: {1: m1, 2: m2}[mid]
        svc = _make_service(matrix_repo=matrix_repo)
        with pytest.raises(HTTPException) as exc:
            svc.run_ephemeral(self._data())
        assert exc.value.status_code == 400

    def test_raises_400_when_vector_size_mismatches(self):
        matrix_repo = MagicMock()
        m1 = _make_matrix(id=1, matrix_a=[[0.5, 0.0], [0.3, 0.8]])
        m2 = _make_matrix(id=2, matrix_a=[[0.8, 0.1], [0.2, 0.6]])
        matrix_repo.get_by_id.side_effect = lambda mid: {1: m1, 2: m2}[mid]
        svc = _make_service(matrix_repo=matrix_repo)
        data = SimulationCreate(matrix_ids=[1, 2], initial_vector=[1.0, 2.0, 3.0], n_steps=1)
        with pytest.raises(HTTPException) as exc:
            svc.run_ephemeral(data)
        assert exc.value.status_code == 400

    def test_reproducible_with_same_seed(self):
        matrix_repo = MagicMock()
        m1 = _make_matrix(id=1, matrix_a=[[0.5, 0.0], [0.3, 0.8]])
        m2 = _make_matrix(id=2, matrix_a=[[0.8, 0.1], [0.2, 0.6]])
        matrix_repo.get_by_id.side_effect = lambda mid: {1: m1, 2: m2}[mid]
        svc = _make_service(matrix_repo=matrix_repo)
        r1 = svc.run_ephemeral(self._data(random_seed=7))
        r2 = svc.run_ephemeral(self._data(random_seed=7))
        assert r1.result_history == r2.result_history

    def test_result_includes_stochastic_stats(self):
        matrix_repo = MagicMock()
        self._two_matrices(matrix_repo)
        svc = _make_service(matrix_repo=matrix_repo)
        result = svc.run_ephemeral(self._data(random_seed=42))
        assert result.n_runs == 100          # default n_runs
        assert result.result_variance is not None
        assert result.result_min_history is not None
        assert result.result_max_history is not None
        assert len(result.result_variance) == 6       # n_steps + 1
        assert len(result.result_min_history) == 6
        assert len(result.result_max_history) == 6

    def test_stochastic_stats_shape_matches_n_steps(self):
        matrix_repo = MagicMock()
        self._two_matrices(matrix_repo)
        svc = _make_service(matrix_repo=matrix_repo)
        data = SimulationCreate(
            matrix_ids=[1, 2], initial_vector=[10.0, 20.0], n_steps=12, random_seed=1,
        )
        result = svc.run_ephemeral(data)
        assert len(result.result_history) == 13        # n_steps + 1
        assert len(result.result_variance) == 13
        assert len(result.result_min_history) == 13
        assert len(result.result_max_history) == 13


class TestRunEphemeralDeterministicStochasticStats:
    def test_deterministic_result_has_no_stochastic_stats(self):
        matrix_repo = MagicMock()
        matrix_repo.get_by_id.return_value = _make_matrix()
        svc = _make_service(matrix_repo=matrix_repo)
        data = SimulationCreate(matrix_id=1, initial_vector=[10.0, 20.0], n_steps=3)
        result = svc.run_ephemeral(data)
        assert result.n_runs is None
        assert result.result_variance is None
        assert result.result_min_history is None
        assert result.result_max_history is None


# ---------------------------------------------------------------------------
# run (stored) — deterministic
# ---------------------------------------------------------------------------

class TestRunDeterministic:
    def test_creates_sim_run_and_returns_record(self):
        matrix_repo = MagicMock()
        sim_repo = MagicMock()
        matrix_repo.get_by_id.return_value = _make_matrix()
        stored = _make_sim_run()
        sim_repo.create.return_value = stored

        svc = _make_service(matrix_repo=matrix_repo, sim_repo=sim_repo)
        data = SimulationCreate(matrix_id=1, initial_vector=[10.0, 20.0], n_steps=3)
        result = svc.run(data, user_id=1)

        sim_repo.create.assert_called_once()
        call_kwargs = sim_repo.create.call_args.kwargs
        assert call_kwargs["user_id"] == 1
        assert call_kwargs["stochastic"] is False
        assert call_kwargs["matrix_id"] == 1
        assert call_kwargs["matrix_ids"] is None
        assert result.id == stored.id

    def test_uses_custom_name_when_provided(self):
        matrix_repo = MagicMock()
        sim_repo = MagicMock()
        matrix_repo.get_by_id.return_value = _make_matrix()
        sim_repo.create.return_value = _make_sim_run(name="My run")

        svc = _make_service(matrix_repo=matrix_repo, sim_repo=sim_repo)
        data = SimulationCreate(matrix_id=1, initial_vector=[10.0, 20.0], n_steps=1, name="My run")
        svc.run(data, user_id=1)

        assert sim_repo.create.call_args.kwargs["name"] == "My run"

    def test_auto_name_used_when_name_is_none(self):
        matrix_repo = MagicMock()
        sim_repo = MagicMock()
        matrix_repo.get_by_id.return_value = _make_matrix()
        sim_repo.create.return_value = _make_sim_run()

        svc = _make_service(matrix_repo=matrix_repo, sim_repo=sim_repo)
        data = SimulationCreate(matrix_id=1, initial_vector=[10.0, 20.0], n_steps=1)
        svc.run(data, user_id=1)

        name = sim_repo.create.call_args.kwargs["name"]
        assert name is not None and name.startswith("Simulation ")


# ---------------------------------------------------------------------------
# run (stored) — stochastic
# ---------------------------------------------------------------------------

class TestRunStochastic:
    def test_creates_stochastic_sim_run(self):
        matrix_repo = MagicMock()
        sim_repo = MagicMock()
        m1 = _make_matrix(id=1, matrix_a=[[0.5, 0.0], [0.3, 0.8]])
        m2 = _make_matrix(id=2, matrix_a=[[0.8, 0.1], [0.2, 0.6]])
        matrix_repo.get_by_id.side_effect = lambda mid: {1: m1, 2: m2}[mid]
        stored = _make_sim_run(stochastic=True, matrix_id=None, matrix_ids=[1, 2])
        sim_repo.create.return_value = stored

        svc = _make_service(matrix_repo=matrix_repo, sim_repo=sim_repo)
        data = SimulationCreate(matrix_ids=[1, 2], initial_vector=[10.0, 20.0], n_steps=5, random_seed=42)
        result = svc.run(data, user_id=1)

        call_kwargs = sim_repo.create.call_args.kwargs
        assert call_kwargs["stochastic"] is True
        assert call_kwargs["matrix_ids"] == [1, 2]
        assert call_kwargs["random_seed"] == 42
        assert result.stochastic is True


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

class TestGet:
    def test_returns_simulation_record(self):
        sim_repo = MagicMock()
        sim_repo.get_by_id.return_value = _make_sim_run(user_id=1)
        svc = _make_service(sim_repo=sim_repo)
        result = svc.get(1, user_id=1)
        assert result.id == 1

    def test_raises_404_when_not_found(self):
        sim_repo = MagicMock()
        sim_repo.get_by_id.return_value = None
        svc = _make_service(sim_repo=sim_repo)
        with pytest.raises(HTTPException) as exc:
            svc.get(999, user_id=1)
        assert exc.value.status_code == 404

    def test_raises_403_when_not_owner(self):
        sim_repo = MagicMock()
        sim_repo.get_by_id.return_value = _make_sim_run(user_id=99)
        svc = _make_service(sim_repo=sim_repo)
        with pytest.raises(HTTPException) as exc:
            svc.get(1, user_id=1)
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:
    def test_deletes_own_simulation(self):
        sim_repo = MagicMock()
        run = _make_sim_run(user_id=1)
        sim_repo.get_by_id.return_value = run
        svc = _make_service(sim_repo=sim_repo)
        svc.delete(1, user_id=1)
        sim_repo.delete.assert_called_once_with(run)

    def test_raises_404_when_not_found(self):
        sim_repo = MagicMock()
        sim_repo.get_by_id.return_value = None
        svc = _make_service(sim_repo=sim_repo)
        with pytest.raises(HTTPException) as exc:
            svc.delete(999, user_id=1)
        assert exc.value.status_code == 404
        sim_repo.delete.assert_not_called()

    def test_raises_403_when_not_owner(self):
        sim_repo = MagicMock()
        sim_repo.get_by_id.return_value = _make_sim_run(user_id=99)
        svc = _make_service(sim_repo=sim_repo)
        with pytest.raises(HTTPException) as exc:
            svc.delete(1, user_id=1)
        assert exc.value.status_code == 403
        sim_repo.delete.assert_not_called()


# ---------------------------------------------------------------------------
# list_for_user
# ---------------------------------------------------------------------------

class TestListForUser:
    def test_returns_summary_records(self):
        sim_repo = MagicMock()
        sim_repo.list_by_user.return_value = [_make_sim_run(id=1), _make_sim_run(id=2)]
        svc = _make_service(sim_repo=sim_repo)
        results = svc.list_for_user(user_id=1)
        assert len(results) == 2
        sim_repo.list_by_user.assert_called_once_with(1)

    def test_empty_list_returned_when_no_simulations(self):
        sim_repo = MagicMock()
        sim_repo.list_by_user.return_value = []
        svc = _make_service(sim_repo=sim_repo)
        assert svc.list_for_user(user_id=1) == []


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------

class TestExport:
    def test_returns_export_dict_with_expected_keys(self):
        sim_repo = MagicMock()
        run = _make_sim_run(user_id=1)
        sim_repo.get_by_id.return_value = run
        svc = _make_service(sim_repo=sim_repo)
        data = svc.export(1, user_id=1)
        for key in ("format_version", "name", "stochastic", "matrix_id", "matrix_ids",
                    "initial_vector", "n_steps", "random_seed", "stage_names",
                    "result_history", "matrices_snapshot", "matrix_sequence", "analytics",
                    "exported_at"):
            assert key in data

    def test_raises_404_when_not_found(self):
        sim_repo = MagicMock()
        sim_repo.get_by_id.return_value = None
        svc = _make_service(sim_repo=sim_repo)
        with pytest.raises(HTTPException) as exc:
            svc.export(999, user_id=1)
        assert exc.value.status_code == 404

    def test_raises_403_when_not_owner(self):
        sim_repo = MagicMock()
        sim_repo.get_by_id.return_value = _make_sim_run(user_id=99)
        svc = _make_service(sim_repo=sim_repo)
        with pytest.raises(HTTPException) as exc:
            svc.export(1, user_id=1)
        assert exc.value.status_code == 403

    def test_format_version_is_string_two(self):
        sim_repo = MagicMock()
        sim_repo.get_by_id.return_value = _make_sim_run(user_id=1)
        svc = _make_service(sim_repo=sim_repo)
        data = svc.export(1, user_id=1)
        assert data["format_version"] == "2"
        assert "matrices_snapshot" in data
        assert "matrix_sequence" in data
        assert "analytics" in data

    def test_format_version_2_has_exported_at(self):
        sim_repo = MagicMock()
        sim_repo.get_by_id.return_value = _make_sim_run(user_id=1)
        svc = _make_service(sim_repo=sim_repo)
        result = svc.export(1, user_id=1)
        assert "exported_at" in result

    def test_export_includes_analytics_when_present(self):
        sim_repo = MagicMock()
        run = _make_sim_run(user_id=1, analytics={"lambda1": 1.05})
        sim_repo.get_by_id.return_value = run
        svc = _make_service(sim_repo=sim_repo)
        result = svc.export(1, user_id=1)
        assert result["analytics"]["lambda1"] == pytest.approx(1.05)


# ---------------------------------------------------------------------------
# import_simulation
# ---------------------------------------------------------------------------

class TestImportSimulation:
    def test_stores_and_returns_record(self):
        sim_repo = MagicMock()
        stored = _make_sim_run(id=5, user_id=2)
        sim_repo.create.return_value = stored

        svc = _make_service(sim_repo=sim_repo)
        data = SimulationImport(
            stochastic=False,
            matrix_id=1,
            initial_vector=[10.0, 20.0],
            n_steps=3,
            result_history=[[10.0, 20.0], [60.0, 22.0], [66.0, 53.6], [160.8, 82.48]],
            name="Restored run",
        )
        result = svc.import_simulation(data, user_id=2)

        sim_repo.create.assert_called_once()
        assert result.id == 5

    def test_auto_name_generated_when_name_is_none(self):
        sim_repo = MagicMock()
        sim_repo.create.return_value = _make_sim_run()

        svc = _make_service(sim_repo=sim_repo)
        data = SimulationImport(
            stochastic=False,
            matrix_id=1,
            initial_vector=[10.0, 20.0],
            n_steps=1,
            result_history=[[10.0, 20.0], [60.0, 22.0]],
        )
        svc.import_simulation(data, user_id=1)

        name = sim_repo.create.call_args.kwargs["name"]
        assert name is not None and name.startswith("Simulation ")

    def test_import_v1_uses_none_for_v2_fields(self):
        """A v1 payload (no analytics/snapshot) passes None for those fields."""
        sim_repo = MagicMock()
        sim_repo.create.return_value = _make_sim_run()

        svc = _make_service(sim_repo=sim_repo)
        data = SimulationImport(
            format_version="1",
            stochastic=False,
            matrix_id=1,
            initial_vector=[10.0, 20.0],
            n_steps=3,
            result_history=[[10.0, 20.0], [60.0, 22.0], [66.0, 53.6], [160.8, 82.48]],
        )
        svc.import_simulation(data, user_id=1)

        call_kwargs = sim_repo.create.call_args.kwargs
        assert call_kwargs["analytics"] is None
        assert call_kwargs["matrices_snapshot"] is None

    def test_import_v2_forwards_snapshot(self):
        """A v2 payload with matrices_snapshot passes it through to repo.create."""
        sim_repo = MagicMock()
        sim_repo.create.return_value = _make_sim_run()

        svc = _make_service(sim_repo=sim_repo)
        snapshot = [[0.5, 0.0], [0.0, 0.5]]
        data = SimulationImport(
            format_version="2",
            stochastic=False,
            matrix_id=1,
            initial_vector=[10.0, 20.0],
            n_steps=1,
            result_history=[[10.0, 20.0], [60.0, 22.0]],
            matrices_snapshot=[snapshot],
        )
        svc.import_simulation(data, user_id=1)

        call_kwargs = sim_repo.create.call_args.kwargs
        assert call_kwargs["matrices_snapshot"] == [snapshot]
