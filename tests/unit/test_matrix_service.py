"""
Unit tests for MatrixService (api/services/matrix_service.py).

The repository is replaced with a MagicMock so no database is needed.
"""
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from api.schemas import MatrixCreate, MatrixUpdate
from api.services.matrix_service import MatrixService


def _make_matrix(**kwargs):
    """Build a minimal fake PopulationMatrix ORM object."""
    defaults = {
        "id": 1,
        "source_type": "custom",
        "owner_id": 42,
        "species_accepted": "Canis lupus",
        "common_name": None,
        "kingdom": "Animalia",
        "country_code": "ESP",
        "matrix_a": [[0.0, 3.0], [0.6, 0.8]],
        "matrix_u": None,
        "matrix_f": None,
        "stage_names": ["pup", "adult"],
        "metadata_": None,
        "created_at": datetime(2024, 1, 1),
    }
    defaults.update(kwargs)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


# ---------------------------------------------------------------------------
# get_matrix
# ---------------------------------------------------------------------------

class TestGetMatrix:
    def test_returns_record(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _make_matrix()
        svc = MatrixService(repo)
        result = svc.get_matrix(1)
        assert result.id == 1
        assert result.species_accepted == "Canis lupus"

    def test_raises_404_when_not_found(self):
        repo = MagicMock()
        repo.get_by_id.return_value = None
        svc = MatrixService(repo)
        with pytest.raises(HTTPException) as exc:
            svc.get_matrix(999)
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# create_matrix
# ---------------------------------------------------------------------------

class TestCreateMatrix:
    def test_delegates_to_repo_and_returns_record(self):
        repo = MagicMock()
        created = _make_matrix(id=7, owner_id=42)
        repo.create.return_value = created

        svc = MatrixService(repo)
        data = MatrixCreate(
            species_accepted="Canis lupus",
            kingdom="Animalia",
            matrix_a=[[0.0, 3.0], [0.6, 0.8]],
            stage_names=["pup", "adult"],
        )
        result = svc.create_matrix(data, owner_id=42)

        repo.create.assert_called_once()
        assert result.id == 7
        assert result.owner_id == 42


# ---------------------------------------------------------------------------
# update_matrix
# ---------------------------------------------------------------------------

class TestUpdateMatrix:
    def test_updates_own_custom_matrix(self):
        repo = MagicMock()
        original = _make_matrix(owner_id=42, source_type="custom")
        updated = _make_matrix(owner_id=42, source_type="custom", common_name="Wolf")
        repo.get_by_id.return_value = original
        repo.update.return_value = updated

        svc = MatrixService(repo)
        result = svc.update_matrix(1, MatrixUpdate(common_name="Wolf"), user_id=42)

        repo.update.assert_called_once()
        assert result.common_name == "Wolf"

    def test_raises_404_when_not_found(self):
        repo = MagicMock()
        repo.get_by_id.return_value = None
        svc = MatrixService(repo)
        with pytest.raises(HTTPException) as exc:
            svc.update_matrix(999, MatrixUpdate(common_name="X"), user_id=1)
        assert exc.value.status_code == 404

    def test_raises_403_for_compadre_matrix(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _make_matrix(source_type="compadre", owner_id=None)
        svc = MatrixService(repo)
        with pytest.raises(HTTPException) as exc:
            svc.update_matrix(1, MatrixUpdate(common_name="X"), user_id=42)
        assert exc.value.status_code == 403
        assert "read-only" in exc.value.detail.lower()

    def test_raises_403_when_not_owner(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _make_matrix(source_type="custom", owner_id=99)
        svc = MatrixService(repo)
        with pytest.raises(HTTPException) as exc:
            svc.update_matrix(1, MatrixUpdate(common_name="X"), user_id=42)
        assert exc.value.status_code == 403
        assert "own" in exc.value.detail.lower()

    def test_repo_update_not_called_on_error(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _make_matrix(source_type="compadre", owner_id=None)
        svc = MatrixService(repo)
        with pytest.raises(HTTPException):
            svc.update_matrix(1, MatrixUpdate(common_name="X"), user_id=42)
        repo.update.assert_not_called()


# ---------------------------------------------------------------------------
# list_matrices
# ---------------------------------------------------------------------------

class TestListMatrices:
    def test_returns_summary_records(self):
        repo = MagicMock()
        repo.list.return_value = [_make_matrix(id=1), _make_matrix(id=2)]
        svc = MatrixService(repo)
        results = svc.list_matrices()
        assert len(results) == 2
        assert results[0].id == 1

    def test_passes_filters_to_repo(self):
        repo = MagicMock()
        repo.list.return_value = []
        svc = MatrixService(repo)
        svc.list_matrices(species="Canis", kingdom="Animalia", source_type="custom", skip=10, limit=5)
        repo.list.assert_called_once_with(
            species="Canis",
            kingdom="Animalia",
            country_code=None,
            source_type="custom",
            skip=10,
            limit=5,
        )
