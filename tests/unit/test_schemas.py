"""
Unit tests for Pydantic schemas (api/schemas.py).

No database or HTTP server required — pure validation logic.
"""
import pytest
from pydantic import ValidationError

from api.records import DeterministicAnalyticsRecord, StochasticAnalyticsRecord
from api.schemas import MatrixCreate, MatrixShareCreate, MatrixUpdate, QuasiExtinctionCreate, SimulationCreate, SimulationImport, StageConfig, UserCreate


# ---------------------------------------------------------------------------
# UserCreate
# ---------------------------------------------------------------------------

class TestUserCreate:
    def test_valid(self):
        u = UserCreate(username="alice", email="alice@example.com", password="password123")
        assert u.username == "alice"

    def test_username_too_short(self):
        with pytest.raises(ValidationError):
            UserCreate(username="ab", email="a@b.com", password="password123")

    def test_username_too_long(self):
        with pytest.raises(ValidationError):
            UserCreate(username="a" * 65, email="a@b.com", password="password123")

    def test_username_no_spaces(self):
        with pytest.raises(ValidationError):
            UserCreate(username="alice smith", email="a@b.com", password="password123")

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(username="alice", email="not-an-email", password="password123")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            UserCreate(username="alice", email="a@b.com", password="short")

    def test_password_too_long(self):
        with pytest.raises(ValidationError):
            UserCreate(username="alice", email="a@b.com", password="x" * 129)


# ---------------------------------------------------------------------------
# MatrixCreate
# ---------------------------------------------------------------------------

VALID_2X2 = [[0.0, 1.5], [0.8, 0.7]]
VALID_3X3 = [[0.0, 1.0, 2.0], [0.3, 0.0, 0.0], [0.0, 0.5, 0.6]]


class TestMatrixCreate:
    def test_valid_minimal(self):
        m = MatrixCreate(matrix_a=VALID_2X2)
        assert m.matrix_a == VALID_2X2
        assert m.matrix_u is None
        assert m.stage_names is None

    def test_valid_with_sub_matrices_and_stages(self):
        m = MatrixCreate(
            matrix_a=VALID_2X2,
            matrix_u=[[0.0, 0.0], [0.8, 0.7]],
            matrix_f=[[0.0, 1.5], [0.0, 0.0]],
            stage_names=["juvenile", "adult"],
        )
        assert len(m.stage_names) == 2

    def test_non_square_matrix_a(self):
        with pytest.raises(ValidationError, match="square"):
            MatrixCreate(matrix_a=[[1.0, 2.0, 3.0], [4.0, 5.0]])

    def test_empty_matrix_a(self):
        with pytest.raises(ValidationError):
            MatrixCreate(matrix_a=[])

    def test_matrix_u_wrong_dimension(self):
        with pytest.raises(ValidationError, match="2×2"):
            MatrixCreate(matrix_a=VALID_2X2, matrix_u=VALID_3X3)

    def test_matrix_f_wrong_dimension(self):
        with pytest.raises(ValidationError, match="2×2"):
            MatrixCreate(matrix_a=VALID_2X2, matrix_f=VALID_3X3)

    def test_stage_names_wrong_count(self):
        with pytest.raises(ValidationError, match="stage_names"):
            MatrixCreate(matrix_a=VALID_2X2, stage_names=["only_one"])

    def test_stage_names_match_dimension(self):
        m = MatrixCreate(matrix_a=VALID_3X3, stage_names=["s", "j", "a"])
        assert len(m.stage_names) == 3

    def test_matrix_a_missing(self):
        with pytest.raises(ValidationError):
            MatrixCreate()

    def test_none_values_allowed_in_cells(self):
        """Matrix cells may be None (missing entries in COMPADRE data)."""
        m = MatrixCreate(matrix_a=[[None, 1.5], [0.8, None]])
        assert m.matrix_a[0][0] is None


# ---------------------------------------------------------------------------
# MatrixUpdate
# ---------------------------------------------------------------------------

class TestMatrixUpdate:
    def test_empty_update_is_valid(self):
        """All fields optional — PATCH semantics."""
        m = MatrixUpdate()
        assert m.matrix_a is None

    def test_partial_update(self):
        m = MatrixUpdate(common_name="Wolf", country_code="ESP")
        assert m.common_name == "Wolf"
        assert m.matrix_a is None

    def test_non_square_matrix_a_rejected(self):
        with pytest.raises(ValidationError, match="square"):
            MatrixUpdate(matrix_a=[[1.0, 2.0, 3.0], [4.0, 5.0]])

    def test_empty_matrix_a_rejected(self):
        with pytest.raises(ValidationError):
            MatrixUpdate(matrix_a=[])

    def test_sub_matrix_dimension_mismatch(self):
        with pytest.raises(ValidationError):
            MatrixUpdate(matrix_a=VALID_2X2, matrix_u=VALID_3X3)

    def test_sub_matrix_provided_without_matrix_a(self):
        """Sub-matrices can be updated independently when matrix_a is not sent."""
        m = MatrixUpdate(matrix_u=VALID_2X2)
        assert m.matrix_u == VALID_2X2
        assert m.matrix_a is None


# ---------------------------------------------------------------------------
# Visibility — MatrixCreate and MatrixUpdate
# ---------------------------------------------------------------------------

class TestVisibilityField:
    def test_create_default_visibility_is_private(self):
        m = MatrixCreate(matrix_a=VALID_2X2)
        assert m.visibility == "private"

    def test_create_accepts_public(self):
        m = MatrixCreate(matrix_a=VALID_2X2, visibility="public")
        assert m.visibility == "public"

    def test_create_accepts_shared(self):
        m = MatrixCreate(matrix_a=VALID_2X2, visibility="shared")
        assert m.visibility == "shared"

    def test_create_rejects_invalid_visibility(self):
        with pytest.raises(ValidationError):
            MatrixCreate(matrix_a=VALID_2X2, visibility="hidden")

    def test_update_visibility_optional(self):
        m = MatrixUpdate()
        assert m.visibility is None

    def test_update_visibility_all_values_accepted(self):
        for v in ("private", "shared", "public"):
            m = MatrixUpdate(visibility=v)
            assert m.visibility == v

    def test_update_visibility_rejects_invalid(self):
        with pytest.raises(ValidationError):
            MatrixUpdate(visibility="secret")


# ---------------------------------------------------------------------------
# MatrixShareCreate
# ---------------------------------------------------------------------------

class TestMatrixShareCreate:
    def test_valid(self):
        s = MatrixShareCreate(username="bob")
        assert s.username == "bob"

    def test_empty_username_rejected(self):
        with pytest.raises(ValidationError):
            MatrixShareCreate(username="")

    def test_username_too_long_rejected(self):
        with pytest.raises(ValidationError):
            MatrixShareCreate(username="x" * 65)


# ---------------------------------------------------------------------------
# SimulationCreate
# ---------------------------------------------------------------------------

class TestSimulationCreate:
    def test_n_runs_default(self):
        data = SimulationCreate(matrix_ids=[1, 2], initial_vector=[1.0], n_steps=10)
        assert data.n_runs == 100

    def test_n_runs_custom(self):
        data = SimulationCreate(matrix_ids=[1, 2], initial_vector=[1.0], n_steps=10, n_runs=50)
        assert data.n_runs == 50

    def test_n_runs_too_low(self):
        with pytest.raises(ValidationError):
            SimulationCreate(matrix_ids=[1, 2], initial_vector=[1.0], n_steps=10, n_runs=5)

    def test_n_runs_too_high(self):
        with pytest.raises(ValidationError):
            SimulationCreate(matrix_ids=[1, 2], initial_vector=[1.0], n_steps=10, n_runs=1001)


# ---------------------------------------------------------------------------
# SimulationImport
# ---------------------------------------------------------------------------

_BASE_IMPORT = dict(
    stochastic=False,
    matrix_id=1,
    initial_vector=[10.0, 5.0],
    n_steps=5,
    result_history=[[10.0, 5.0], [8.0, 4.0]],
)


class TestSimulationImport:
    def test_format_version_1_valid(self):
        obj = SimulationImport(format_version="1", **_BASE_IMPORT)
        assert obj.format_version == "1"

    def test_format_version_2_valid(self):
        obj = SimulationImport(
            format_version="2",
            matrices_snapshot=[[[0.0, 1.5], [0.8, 0.7]]],
            matrix_sequence=None,
            analytics={"lambda_1": 1.05},
            **_BASE_IMPORT,
        )
        assert obj.format_version == "2"
        assert obj.matrices_snapshot is not None
        assert obj.analytics == {"lambda_1": 1.05}

    def test_format_version_unknown_rejected(self):
        with pytest.raises(ValidationError):
            SimulationImport(format_version="3", **_BASE_IMPORT)


# ---------------------------------------------------------------------------
# QuasiExtinctionCreate
# ---------------------------------------------------------------------------

class TestQuasiExtinctionCreate:
    def test_requires_at_least_2_matrices(self):
        with pytest.raises(ValidationError):
            QuasiExtinctionCreate(
                matrix_ids=[1],
                initial_vector=[10.0, 5.0],
                n_steps=100,
            )

    def test_n_runs_bounds(self):
        base = dict(matrix_ids=[1, 2], initial_vector=[10.0, 5.0], n_steps=100)
        with pytest.raises(ValidationError):
            QuasiExtinctionCreate(n_runs=5, **base)
        with pytest.raises(ValidationError):
            QuasiExtinctionCreate(n_runs=5001, **base)
        obj = QuasiExtinctionCreate(n_runs=500, **base)
        assert obj.n_runs == 500

    def test_extinction_threshold_must_be_positive(self):
        base = dict(matrix_ids=[1, 2], initial_vector=[10.0, 5.0], n_steps=100)
        with pytest.raises(ValidationError):
            QuasiExtinctionCreate(extinction_threshold=0.0, **base)
        obj = QuasiExtinctionCreate(extinction_threshold=0.001, **base)
        assert obj.extinction_threshold == pytest.approx(0.001)

    def test_defaults(self):
        obj = QuasiExtinctionCreate(
            matrix_ids=[1, 2],
            initial_vector=[10.0, 5.0],
            n_steps=100,
        )
        assert obj.n_runs == 500
        assert obj.extinction_threshold == pytest.approx(1.0)

    def test_stage_configs_length_mismatch_raises(self):
        with pytest.raises(ValidationError, match="stage_configs"):
            QuasiExtinctionCreate(
                matrix_ids=[1, 2],
                initial_vector=[10.0, 5.0],       # 2 elements
                n_steps=10,
                stage_configs=[                    # 3 elements → mismatch
                    {"threshold": None, "excluded": False},
                    {"threshold": None, "excluded": False},
                    {"threshold": None, "excluded": False},
                ],
            )

    def test_stage_names_length_mismatch_raises(self):
        with pytest.raises(ValidationError, match="stage_names"):
            QuasiExtinctionCreate(
                matrix_ids=[1, 2],
                initial_vector=[10.0, 5.0],       # 2 elements
                n_steps=10,
                stage_names=["a", "b", "c"],       # 3 names → mismatch
            )

    def test_all_stages_excluded_raises(self):
        with pytest.raises(ValidationError, match="excluded"):
            QuasiExtinctionCreate(
                matrix_ids=[1, 2],
                initial_vector=[10.0, 5.0],
                n_steps=10,
                stage_configs=[
                    {"threshold": None, "excluded": True},
                    {"threshold": None, "excluded": True},
                ],
            )


# ---------------------------------------------------------------------------
# DeterministicAnalyticsRecord
# ---------------------------------------------------------------------------

class TestDeterministicAnalyticsRecord:
    def test_det_analytics_round_trip(self):
        data = dict(
            lambda_1=1.05,
            stable_stage_distribution=[0.6, 0.4],
            reproductive_value=[1.0, 1.2],
            sensitivities=[[0.1, 0.2], [0.3, 0.4]],
            elasticities=[[0.05, 0.15], [0.3, 0.5]],
            analytics_reliable=True,
            stage_names=["juvenile", "adult"],
        )
        rec = DeterministicAnalyticsRecord(**data)
        serialized = rec.model_dump()
        assert serialized["lambda_1"] == pytest.approx(1.05)
        assert serialized["analytics_reliable"] is True
        assert serialized["stage_names"] == ["juvenile", "adult"]
        assert len(serialized["sensitivities"]) == 2


# ---------------------------------------------------------------------------
# StochasticAnalyticsRecord
# ---------------------------------------------------------------------------

class TestStochasticAnalyticsRecord:
    def test_stoch_analytics_round_trip(self):
        data = dict(
            lambda_s=0.98,
            mean_matrix=[[0.1, 0.9], [0.5, 0.5]],
            lambda_1_of_mean=1.02,
            elasticities_of_mean=[[0.1, 0.4], [0.3, 0.2]],
            stable_stage_distribution_of_mean=[0.55, 0.45],
            analytics_reliable=True,
            stage_names=["seed", "seedling"],
        )
        rec = StochasticAnalyticsRecord(**data)
        serialized = rec.model_dump()
        assert serialized["lambda_s"] == pytest.approx(0.98)
        assert serialized["analytics_reliable"] is True
        assert serialized["stage_names"] == ["seed", "seedling"]
        assert len(serialized["mean_matrix"]) == 2
