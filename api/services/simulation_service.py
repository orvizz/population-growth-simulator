"""
SimulationService — business logic for running and storing population simulations.

Algorithm
---------
Deterministic: v(t+1) = A @ v(t)
Stochastic:    at each step, pick one matrix uniformly at random, then v(t+1) = A_i @ v(t)

None cells in a matrix are treated as 0.0 (common in COMPADRE incomplete entries).
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
from fastapi import HTTPException, status

from api.records import SimulationRecord, SimulationRunResult, SimulationSummaryRecord
from api.repositories.matrix_repository import MatrixRepository
from api.repositories.simulation_repository import SimulationRepository
from api.schemas import SimulationCreate, SimulationImport
from api.services.analytics_service import (
    compute_deterministic_analytics,
    compute_stochastic_analytics,
)


def _auto_name() -> str:
    return f"Simulation {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"


class SimulationService:
    def __init__(self, matrix_repo: MatrixRepository, sim_repo: SimulationRepository) -> None:
        self._matrices = matrix_repo
        self._sims = sim_repo

    # ------------------------------------------------------------------
    # Ephemeral run (no DB write — public endpoint)
    # ------------------------------------------------------------------

    def run_ephemeral(self, data: SimulationCreate) -> SimulationRunResult:
        """Compute simulation without storing. No authentication required."""
        if data.is_stochastic:
            return self._ephemeral_stochastic(data)
        return self._ephemeral_deterministic(data)

    # ------------------------------------------------------------------
    # Run + store (auth required)
    # ------------------------------------------------------------------

    def run(self, data: SimulationCreate, *, user_id: int) -> SimulationRecord:
        if data.is_stochastic:
            return self._run_stochastic(data, user_id=user_id)
        return self._run_deterministic(data, user_id=user_id)

    # ------------------------------------------------------------------
    # Import from exported file (auth required)
    # ------------------------------------------------------------------

    def import_simulation(self, data: SimulationImport, *, user_id: int) -> SimulationRecord:
        name = data.name or _auto_name()
        run = self._sims.create(
            user_id=user_id,
            name=name,
            matrix_id=data.matrix_id,
            matrix_ids=data.matrix_ids,
            stochastic=data.stochastic,
            random_seed=data.random_seed,
            initial_vector=data.initial_vector,
            n_steps=data.n_steps,
            result_history=data.result_history,
            stage_names=data.stage_names,
            matrices_snapshot=data.matrices_snapshot,
            matrix_sequence=data.matrix_sequence,
            analytics=data.analytics,
        )
        return SimulationRecord.model_validate(run)

    # ------------------------------------------------------------------
    # Export as dict (auth required)
    # ------------------------------------------------------------------

    def export(self, sim_id: int, *, user_id: int) -> dict:
        run = self._sims.get_by_id(sim_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Simulation not found")
        if run.user_id != user_id:
            raise HTTPException(status_code=403, detail="You do not own this simulation")
        return {
            "format_version": "2",
            "name": run.name,
            "stochastic": run.stochastic,
            "matrix_id": run.matrix_id,
            "matrix_ids": run.matrix_ids,
            "initial_vector": run.initial_vector,
            "n_steps": run.n_steps,
            "random_seed": run.random_seed,
            "stage_names": run.stage_names,
            "result_history": run.result_history,
            "matrices_snapshot": run.matrices_snapshot,
            "matrix_sequence": run.matrix_sequence,
            "analytics": run.analytics,
            "exported_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def list_for_user(self, user_id: int) -> list[SimulationSummaryRecord]:
        runs = self._sims.list_by_user(user_id)
        return [SimulationSummaryRecord.model_validate(r) for r in runs]

    def get(self, sim_id: int, *, user_id: int) -> SimulationRecord:
        run = self._sims.get_by_id(sim_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Simulation not found")
        if run.user_id != user_id:
            raise HTTPException(status_code=403, detail="You do not own this simulation")
        return SimulationRecord.model_validate(run)

    def delete(self, sim_id: int, *, user_id: int) -> None:
        run = self._sims.get_by_id(sim_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Simulation not found")
        if run.user_id != user_id:
            raise HTTPException(status_code=403, detail="You do not own this simulation")
        self._sims.delete(run)

    # ------------------------------------------------------------------
    # Private — ephemeral helpers
    # ------------------------------------------------------------------

    def _ephemeral_deterministic(self, data: SimulationCreate) -> SimulationRunResult:
        matrix = self._matrices.get_by_id(data.matrix_id)
        if matrix is None:
            raise HTTPException(status_code=404, detail="Matrix not found")
        if not matrix.matrix_a:
            raise HTTPException(status_code=400, detail="Matrix has no matrix_a defined")
        self._validate_vector(data.initial_vector, len(matrix.matrix_a))
        history = self._compute_deterministic(matrix.matrix_a, data.initial_vector, data.n_steps)
        matrices_snapshot = self._snapshot_matrices([matrix.matrix_a])
        analytics = self._compute_analytics(matrices_snapshot, None, history, matrix.stage_names)
        return SimulationRunResult(
            stochastic=False,
            matrix_id=data.matrix_id,
            matrix_ids=None,
            random_seed=None,
            initial_vector=data.initial_vector,
            n_steps=data.n_steps,
            result_history=history,
            stage_names=matrix.stage_names,
            species_accepted=matrix.species_accepted,
            matrices_snapshot=matrices_snapshot,
            analytics=analytics,
        )

    def _ephemeral_stochastic(self, data: SimulationCreate) -> SimulationRunResult:
        matrices = [self._matrices.get_by_id(mid) for mid in data.matrix_ids]
        for mid, m in zip(data.matrix_ids, matrices):
            if m is None:
                raise HTTPException(status_code=404, detail=f"Matrix {mid} not found")
            if not m.matrix_a:
                raise HTTPException(status_code=400, detail=f"Matrix {mid} has no matrix_a defined")
        dims = [len(m.matrix_a) for m in matrices]
        if len(set(dims)) > 1:
            raise HTTPException(status_code=400, detail=f"All matrices must have the same dimension — got {set(dims)}")
        self._validate_vector(data.initial_vector, dims[0])
        history, matrix_sequence = self._compute_stochastic(
            [m.matrix_a for m in matrices], data.initial_vector, data.n_steps, data.random_seed
        )
        matrices_snapshot = self._snapshot_matrices([m.matrix_a for m in matrices])
        analytics = self._compute_analytics(matrices_snapshot, matrix_sequence, history, matrices[0].stage_names)
        return SimulationRunResult(
            stochastic=True,
            matrix_id=None,
            matrix_ids=data.matrix_ids,
            random_seed=data.random_seed,
            initial_vector=data.initial_vector,
            n_steps=data.n_steps,
            result_history=history,
            stage_names=matrices[0].stage_names,
            species_accepted=matrices[0].species_accepted,
            matrices_snapshot=matrices_snapshot,
            analytics=analytics,
        )

    # ------------------------------------------------------------------
    # Private — stored run helpers
    # ------------------------------------------------------------------

    def _run_deterministic(self, data: SimulationCreate, *, user_id: int) -> SimulationRecord:
        matrix = self._matrices.get_by_id(data.matrix_id)
        if matrix is None:
            raise HTTPException(status_code=404, detail="Matrix not found")
        if not matrix.matrix_a:
            raise HTTPException(status_code=400, detail="Matrix has no matrix_a defined")
        self._validate_vector(data.initial_vector, len(matrix.matrix_a))
        history = self._compute_deterministic(matrix.matrix_a, data.initial_vector, data.n_steps)
        matrices_snapshot = self._snapshot_matrices([matrix.matrix_a])
        analytics = self._compute_analytics(matrices_snapshot, None, history, matrix.stage_names)
        run = self._sims.create(
            user_id=user_id,
            name=data.name or _auto_name(),
            matrix_id=matrix.id,
            matrix_ids=None,
            stochastic=False,
            random_seed=None,
            initial_vector=data.initial_vector,
            n_steps=data.n_steps,
            result_history=history,
            stage_names=matrix.stage_names,
            matrices_snapshot=matrices_snapshot,
            analytics=analytics,
        )
        return SimulationRecord.model_validate(run)

    def _run_stochastic(self, data: SimulationCreate, *, user_id: int) -> SimulationRecord:
        matrices = [self._matrices.get_by_id(mid) for mid in data.matrix_ids]
        for mid, m in zip(data.matrix_ids, matrices):
            if m is None:
                raise HTTPException(status_code=404, detail=f"Matrix {mid} not found")
            if not m.matrix_a:
                raise HTTPException(status_code=400, detail=f"Matrix {mid} has no matrix_a defined")
        dims = [len(m.matrix_a) for m in matrices]
        if len(set(dims)) > 1:
            raise HTTPException(status_code=400, detail=f"All matrices must have the same dimension — got {set(dims)}")
        self._validate_vector(data.initial_vector, dims[0])
        history, matrix_sequence = self._compute_stochastic(
            [m.matrix_a for m in matrices], data.initial_vector, data.n_steps, data.random_seed
        )
        matrices_snapshot = self._snapshot_matrices([m.matrix_a for m in matrices])
        analytics = self._compute_analytics(matrices_snapshot, matrix_sequence, history, matrices[0].stage_names)
        run = self._sims.create(
            user_id=user_id,
            name=data.name or _auto_name(),
            matrix_id=None,
            matrix_ids=data.matrix_ids,
            stochastic=True,
            random_seed=data.random_seed,
            initial_vector=data.initial_vector,
            n_steps=data.n_steps,
            result_history=history,
            stage_names=matrices[0].stage_names,
            matrices_snapshot=matrices_snapshot,
            matrix_sequence=matrix_sequence,
            analytics=analytics,
        )
        return SimulationRecord.model_validate(run)

    # ------------------------------------------------------------------
    # Core algorithms
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_vector(vector: list[float], dim: int) -> None:
        if len(vector) != dim:
            raise HTTPException(
                status_code=400,
                detail=f"initial_vector has {len(vector)} elements but matrix is {dim}×{dim}",
            )

    @staticmethod
    def _to_array(matrix_a: list) -> np.ndarray:
        return np.array(
            [[0.0 if v is None else float(v) for v in row] for row in matrix_a],
            dtype=float,
        )

    @classmethod
    def _compute_deterministic(cls, matrix_a: list, initial_vector: list[float], n_steps: int) -> list[list[float]]:
        A = cls._to_array(matrix_a)
        v = np.array(initial_vector, dtype=float)
        history = [v.tolist()]
        for _ in range(n_steps):
            v = A @ v
            history.append(v.tolist())
        return history

    @classmethod
    def _compute_stochastic(
        cls, matrices: list[list], initial_vector: list[float], n_steps: int, random_seed: int | None
    ) -> tuple[list[list[float]], list[int]]:
        rng = np.random.default_rng(random_seed)
        arrays = [cls._to_array(m) for m in matrices]
        v = np.array(initial_vector, dtype=float)
        history = [v.tolist()]
        matrix_sequence = []
        for _ in range(n_steps):
            idx = int(rng.integers(len(arrays)))
            matrix_sequence.append(idx)
            v = arrays[idx] @ v
            history.append(v.tolist())
        return history, matrix_sequence

    @staticmethod
    def _snapshot_matrices(matrix_a_list: list[list]) -> list[list[list[float]]]:
        """Snapshot matrix_a values as plain lists (immune to future DB edits).

        Always returns a list, even for deterministic (one-element list).
        None cells are treated as 0.0, consistent with the COMPADRE convention used throughout this codebase.
        """
        return [
            [[0.0 if v is None else float(v) for v in row] for row in m]
            for m in matrix_a_list
        ]

    def _compute_analytics(
        self,
        matrices_snapshot: list[list[list[float]]],
        matrix_sequence: list[int] | None,
        result_history: list[list[float]],
        stage_names: list[str] | None,
    ) -> dict:
        """Delegate analytics computation to AnalyticsService.

        For deterministic runs (matrix_sequence=None): uses the single snapshotted matrix.
        For stochastic runs: uses the full sequence and history.
        """
        try:
            if matrix_sequence is None:
                # Deterministic: single matrix
                return compute_deterministic_analytics(matrices_snapshot[0], stage_names)
            else:
                # Stochastic
                return compute_stochastic_analytics(
                    matrices_snapshot, matrix_sequence, result_history, stage_names
                )
        except Exception:
            return None
