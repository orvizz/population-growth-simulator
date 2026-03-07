"""
Unit tests for MatrixService (api/services/matrix_service.py).

The repositories are replaced with MagicMock so no database is needed.
"""
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from api.schemas import MatrixCreate, MatrixShareCreate, MatrixUpdate
from api.services.matrix_service import MatrixService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_share(matrix_id=1, shared_with_user_id=99, username="carol"):
    s = MagicMock()
    s.matrix_id = matrix_id
    s.shared_with_user_id = shared_with_user_id
    s.shared_with_user.username = username
    return s


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
        "visibility": "public",
        "shares": [],
        "created_at": datetime(2024, 1, 1),
    }
    defaults.update(kwargs)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


def _svc(repo=None, user_repo=None):
    return MatrixService(repo or MagicMock(), user_repo or MagicMock())


# ---------------------------------------------------------------------------
# get_matrix
# ---------------------------------------------------------------------------

class TestGetMatrix:
    def test_returns_record_for_public_matrix(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _make_matrix(visibility="public")
        result = _svc(repo).get_matrix(1)
        assert result.id == 1
        assert result.species_accepted == "Canis lupus"

    def test_raises_404_when_not_found(self):
        repo = MagicMock()
        repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            _svc(repo).get_matrix(999)
        assert exc.value.status_code == 404

    def test_private_matrix_accessible_by_owner(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _make_matrix(visibility="private", owner_id=42)
        result = _svc(repo).get_matrix(1, caller_id=42)
        assert result.id == 1

    def test_private_matrix_denied_for_anonymous(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _make_matrix(visibility="private", owner_id=42)
        with pytest.raises(HTTPException) as exc:
            _svc(repo).get_matrix(1, caller_id=None)
        assert exc.value.status_code == 403

    def test_private_matrix_denied_for_other_user(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _make_matrix(visibility="private", owner_id=42, shares=[])
        with pytest.raises(HTTPException) as exc:
            _svc(repo).get_matrix(1, caller_id=99)
        assert exc.value.status_code == 403

    def test_shared_matrix_accessible_by_shared_user(self):
        repo = MagicMock()
        share = _make_share(shared_with_user_id=99)
        repo.get_by_id.return_value = _make_matrix(
            visibility="shared", owner_id=42, shares=[share]
        )
        result = _svc(repo).get_matrix(1, caller_id=99)
        assert result.id == 1

    def test_shared_matrix_denied_for_non_shared_user(self):
        repo = MagicMock()
        share = _make_share(shared_with_user_id=99)
        repo.get_by_id.return_value = _make_matrix(
            visibility="shared", owner_id=42, shares=[share]
        )
        with pytest.raises(HTTPException) as exc:
            _svc(repo).get_matrix(1, caller_id=55)
        assert exc.value.status_code == 403

    def test_shared_matrix_accessible_by_owner(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _make_matrix(visibility="shared", owner_id=42, shares=[])
        result = _svc(repo).get_matrix(1, caller_id=42)
        assert result.id == 1


# ---------------------------------------------------------------------------
# list_matrices
# ---------------------------------------------------------------------------

class TestListMatrices:
    def test_returns_summary_records(self):
        repo = MagicMock()
        repo.list.return_value = [_make_matrix(id=1), _make_matrix(id=2)]
        results = _svc(repo).list_matrices()
        assert len(results) == 2
        assert results[0].id == 1

    def test_passes_filters_and_caller_id_to_repo(self):
        repo = MagicMock()
        repo.list.return_value = []
        _svc(repo).list_matrices(
            caller_id=7,
            species="Canis",
            kingdom="Animalia",
            source_type="custom",
            skip=10,
            limit=5,
        )
        repo.list.assert_called_once_with(
            caller_id=7,
            species="Canis",
            kingdom="Animalia",
            country_code=None,
            source_type="custom",
            skip=10,
            limit=5,
        )

    def test_passes_none_caller_id_when_anonymous(self):
        repo = MagicMock()
        repo.list.return_value = []
        _svc(repo).list_matrices()
        call_kwargs = repo.list.call_args.kwargs
        assert call_kwargs["caller_id"] is None


# ---------------------------------------------------------------------------
# create_matrix
# ---------------------------------------------------------------------------

class TestCreateMatrix:
    def test_delegates_to_repo_and_returns_record(self):
        repo = MagicMock()
        repo.create.return_value = _make_matrix(id=7, owner_id=42, visibility="private")
        data = MatrixCreate(
            species_accepted="Canis lupus",
            kingdom="Animalia",
            matrix_a=[[0.0, 3.0], [0.6, 0.8]],
            stage_names=["pup", "adult"],
        )
        result = _svc(repo).create_matrix(data, owner_id=42)
        repo.create.assert_called_once()
        assert result.id == 7

    def test_passes_visibility_to_repo(self):
        repo = MagicMock()
        repo.create.return_value = _make_matrix(visibility="public")
        data = MatrixCreate(matrix_a=[[1.0]], visibility="public")
        _svc(repo).create_matrix(data, owner_id=1)
        _, kwargs = repo.create.call_args
        assert kwargs["visibility"] == "public"

    def test_default_visibility_is_private(self):
        repo = MagicMock()
        repo.create.return_value = _make_matrix(visibility="private")
        data = MatrixCreate(matrix_a=[[1.0]])   # no visibility → default "private"
        _svc(repo).create_matrix(data, owner_id=1)
        _, kwargs = repo.create.call_args
        assert kwargs["visibility"] == "private"


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
        result = _svc(repo).update_matrix(1, MatrixUpdate(common_name="Wolf"), user_id=42)
        repo.update.assert_called_once()
        assert result.common_name == "Wolf"

    def test_can_update_visibility(self):
        repo = MagicMock()
        original = _make_matrix(owner_id=42, visibility="private", shares=[])
        updated = _make_matrix(owner_id=42, visibility="public")
        repo.get_by_id.return_value = original
        repo.update.return_value = updated
        result = _svc(repo).update_matrix(1, MatrixUpdate(visibility="public"), user_id=42)
        assert result.visibility == "public"

    def test_changing_to_private_purges_shares(self):
        repo = MagicMock()
        share = _make_share(shared_with_user_id=99)
        original = _make_matrix(owner_id=42, visibility="shared", shares=[share])
        repo.get_by_id.return_value = original
        repo.update.return_value = _make_matrix(owner_id=42, visibility="private", shares=[])
        _svc(repo).update_matrix(1, MatrixUpdate(visibility="private"), user_id=42)
        repo.remove_share.assert_called_once_with(1, 99)

    def test_raises_404_when_not_found(self):
        repo = MagicMock()
        repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            _svc(repo).update_matrix(999, MatrixUpdate(common_name="X"), user_id=1)
        assert exc.value.status_code == 404

    def test_raises_403_for_compadre_matrix(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _make_matrix(source_type="compadre", owner_id=None)
        with pytest.raises(HTTPException) as exc:
            _svc(repo).update_matrix(1, MatrixUpdate(common_name="X"), user_id=42)
        assert exc.value.status_code == 403
        assert "read-only" in exc.value.detail.lower()

    def test_raises_403_when_not_owner(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _make_matrix(source_type="custom", owner_id=99)
        with pytest.raises(HTTPException) as exc:
            _svc(repo).update_matrix(1, MatrixUpdate(common_name="X"), user_id=42)
        assert exc.value.status_code == 403

    def test_repo_update_not_called_on_error(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _make_matrix(source_type="compadre", owner_id=None)
        with pytest.raises(HTTPException):
            _svc(repo).update_matrix(1, MatrixUpdate(common_name="X"), user_id=42)
        repo.update.assert_not_called()


# ---------------------------------------------------------------------------
# share_matrix
# ---------------------------------------------------------------------------

class TestShareMatrix:
    def _setup(self, *, owner_id=42, visibility="private", shares=None,
               target_id=99, target_username="carol", existing_share=None):
        repo = MagicMock()
        user_repo = MagicMock()
        matrix = _make_matrix(id=1, owner_id=owner_id, visibility=visibility,
                               shares=shares or [])
        repo.get_by_id.return_value = matrix
        target = MagicMock()
        target.id = target_id
        target.username = target_username
        user_repo.get_by_username.return_value = target
        repo.get_share.return_value = existing_share
        new_share = _make_share(shared_with_user_id=target_id, username=target_username)
        repo.add_share.return_value = new_share
        return repo, user_repo, matrix

    def test_happy_path_returns_share_record(self):
        repo, user_repo, _ = self._setup()
        result = MatrixService(repo, user_repo).share_matrix(
            1, MatrixShareCreate(username="carol"), user_id=42
        )
        assert result.shared_with_user_id == 99
        assert result.shared_with_username == "carol"

    def test_auto_promotes_private_to_shared(self):
        repo, user_repo, matrix = self._setup(visibility="private")
        MatrixService(repo, user_repo).share_matrix(
            1, MatrixShareCreate(username="carol"), user_id=42
        )
        repo.update.assert_called_once_with(matrix, {"visibility": "shared"})

    def test_already_public_not_demoted(self):
        repo, user_repo, _ = self._setup(visibility="public")
        MatrixService(repo, user_repo).share_matrix(
            1, MatrixShareCreate(username="carol"), user_id=42
        )
        repo.update.assert_not_called()

    def test_raises_404_matrix_not_found(self):
        repo, user_repo = MagicMock(), MagicMock()
        repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            MatrixService(repo, user_repo).share_matrix(
                999, MatrixShareCreate(username="carol"), user_id=42
            )
        assert exc.value.status_code == 404

    def test_raises_403_when_not_owner(self):
        repo, user_repo, _ = self._setup(owner_id=99)
        with pytest.raises(HTTPException) as exc:
            MatrixService(repo, user_repo).share_matrix(
                1, MatrixShareCreate(username="carol"), user_id=42
            )
        assert exc.value.status_code == 403

    def test_raises_403_for_compadre(self):
        repo, user_repo = MagicMock(), MagicMock()
        repo.get_by_id.return_value = _make_matrix(source_type="compadre", owner_id=None)
        with pytest.raises(HTTPException) as exc:
            MatrixService(repo, user_repo).share_matrix(
                1, MatrixShareCreate(username="carol"), user_id=42
            )
        assert exc.value.status_code == 403

    def test_raises_404_target_user_not_found(self):
        repo, user_repo = MagicMock(), MagicMock()
        repo.get_by_id.return_value = _make_matrix(owner_id=42)
        user_repo.get_by_username.return_value = None
        repo.get_share.return_value = None
        with pytest.raises(HTTPException) as exc:
            MatrixService(repo, user_repo).share_matrix(
                1, MatrixShareCreate(username="nobody"), user_id=42
            )
        assert exc.value.status_code == 404

    def test_raises_400_share_with_self(self):
        repo, user_repo = MagicMock(), MagicMock()
        repo.get_by_id.return_value = _make_matrix(owner_id=42)
        target = MagicMock()
        target.id = 42      # same as owner
        target.username = "alice"
        user_repo.get_by_username.return_value = target
        with pytest.raises(HTTPException) as exc:
            MatrixService(repo, user_repo).share_matrix(
                1, MatrixShareCreate(username="alice"), user_id=42
            )
        assert exc.value.status_code == 400

    def test_raises_409_duplicate_share(self):
        repo, user_repo, _ = self._setup(existing_share=_make_share())
        with pytest.raises(HTTPException) as exc:
            MatrixService(repo, user_repo).share_matrix(
                1, MatrixShareCreate(username="carol"), user_id=42
            )
        assert exc.value.status_code == 409


# ---------------------------------------------------------------------------
# unshare_matrix
# ---------------------------------------------------------------------------

class TestUnshareMatrix:
    def test_happy_path_removes_share(self):
        repo, user_repo = MagicMock(), MagicMock()
        share = _make_share(shared_with_user_id=99)
        matrix = _make_matrix(owner_id=42, visibility="shared", shares=[])
        repo.get_by_id.return_value = matrix
        repo.get_share.return_value = share
        # After removal, refresh returns no shares
        matrix.shares = []
        MatrixService(repo, user_repo).unshare_matrix(1, shared_user_id=99, user_id=42)
        repo.remove_share.assert_called_once_with(1, 99)

    def test_auto_demotes_to_private_when_last_share_removed(self):
        repo, user_repo = MagicMock(), MagicMock()
        share = _make_share(shared_with_user_id=99)
        matrix = _make_matrix(owner_id=42, visibility="shared", shares=[])
        repo.get_by_id.return_value = matrix
        repo.get_share.return_value = share
        # After refresh: no more shares
        matrix.shares = []
        MatrixService(repo, user_repo).unshare_matrix(1, shared_user_id=99, user_id=42)
        repo.update.assert_called_once_with(matrix, {"visibility": "private"})

    def test_no_demotion_when_shares_remain(self):
        repo, user_repo = MagicMock(), MagicMock()
        remaining = _make_share(shared_with_user_id=55)
        matrix = _make_matrix(owner_id=42, visibility="shared", shares=[remaining])
        repo.get_by_id.return_value = matrix
        repo.get_share.return_value = _make_share(shared_with_user_id=99)
        MatrixService(repo, user_repo).unshare_matrix(1, shared_user_id=99, user_id=42)
        repo.update.assert_not_called()

    def test_raises_404_matrix_not_found(self):
        repo, user_repo = MagicMock(), MagicMock()
        repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            MatrixService(repo, user_repo).unshare_matrix(999, shared_user_id=99, user_id=42)
        assert exc.value.status_code == 404

    def test_raises_403_when_not_owner(self):
        repo, user_repo = MagicMock(), MagicMock()
        repo.get_by_id.return_value = _make_matrix(owner_id=99)
        with pytest.raises(HTTPException) as exc:
            MatrixService(repo, user_repo).unshare_matrix(1, shared_user_id=55, user_id=42)
        assert exc.value.status_code == 403

    def test_raises_404_share_not_found(self):
        repo, user_repo = MagicMock(), MagicMock()
        repo.get_by_id.return_value = _make_matrix(owner_id=42)
        repo.get_share.return_value = None
        with pytest.raises(HTTPException) as exc:
            MatrixService(repo, user_repo).unshare_matrix(1, shared_user_id=99, user_id=42)
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# list_shares
# ---------------------------------------------------------------------------

class TestListShares:
    def test_returns_share_records(self):
        repo, user_repo = MagicMock(), MagicMock()
        share = _make_share(shared_with_user_id=99, username="carol")
        repo.get_by_id.return_value = _make_matrix(owner_id=42, shares=[share])
        results = MatrixService(repo, user_repo).list_shares(1, user_id=42)
        assert len(results) == 1
        assert results[0].shared_with_user_id == 99
        assert results[0].shared_with_username == "carol"

    def test_returns_empty_when_no_shares(self):
        repo, user_repo = MagicMock(), MagicMock()
        repo.get_by_id.return_value = _make_matrix(owner_id=42, shares=[])
        results = MatrixService(repo, user_repo).list_shares(1, user_id=42)
        assert results == []

    def test_raises_404_matrix_not_found(self):
        repo, user_repo = MagicMock(), MagicMock()
        repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            MatrixService(repo, user_repo).list_shares(999, user_id=42)
        assert exc.value.status_code == 404

    def test_raises_403_when_not_owner(self):
        repo, user_repo = MagicMock(), MagicMock()
        repo.get_by_id.return_value = _make_matrix(owner_id=99)
        with pytest.raises(HTTPException) as exc:
            MatrixService(repo, user_repo).list_shares(1, user_id=42)
        assert exc.value.status_code == 403
