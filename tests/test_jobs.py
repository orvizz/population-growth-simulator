"""
Integration tests for /v1/jobs endpoints.

Endpoints under test:
  POST   /v1/jobs/quasi-extinction  — create QE job, auth required → 202
  GET    /v1/jobs                   — list own jobs, auth required
  GET    /v1/jobs/{id}              — job detail, auth required + ownership
  DELETE /v1/jobs/{id}              — delete completed/failed job, auth required + ownership

Background execution note:
  The background task opens its own SessionLocal pointing to the main database.
  During integration tests, the main DB does not have the test-created jobs, so the
  background task is a no-op and jobs remain "pending" after creation.
  Tests that require a "completed" state use _force_job_status() to update the test DB
  directly, bypassing the HTTP layer.
"""
import os

import pytest

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

MATRIX_2X2_A = [[0.0, 3.0], [0.6, 0.8]]
MATRIX_2X2_B = [[0.5, 0.1], [0.4, 0.7]]
VECTOR_2 = [10.0, 20.0]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def alice_matrix_a(client, alice):
    r = client.post("/v1/matrices", json={
        "species_accepted": "Felis catus",
        "kingdom": "Animalia",
        "matrix_a": MATRIX_2X2_A,
        "stage_names": ["kitten", "adult"],
    }, headers=alice["headers"])
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def alice_matrix_b(client, alice):
    r = client.post("/v1/matrices", json={
        "species_accepted": "Felis catus variant",
        "kingdom": "Animalia",
        "matrix_a": MATRIX_2X2_B,
        "stage_names": ["kitten", "adult"],
    }, headers=alice["headers"])
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def alice_job(client, alice, alice_matrix_a, alice_matrix_b):
    """A quasi-extinction job created by alice (status will be 'pending')."""
    r = client.post("/v1/jobs/quasi-extinction", json={
        "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
        "initial_vector": VECTOR_2,
        "n_steps": 10,
        "n_runs": 20,
    }, headers=alice["headers"])
    assert r.status_code == 202
    return r.json()


def _db_url():
    """Build the test database URL (matrix_db_test)."""
    base = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}"
    )
    return f"{base}/matrix_db_test"


def _force_job_status(job_id: int, status: str, *, result=None, error=None) -> None:
    """Directly set a job's status in the test DB (bypasses the HTTP layer).

    Used to simulate a completed/failed job without running the actual background task.
    """
    from datetime import datetime

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from db.models import SimulationJob

    engine = create_engine(_db_url())
    Session = sessionmaker(bind=engine)
    with Session() as session:
        job = session.get(SimulationJob, job_id)
        if job is not None:
            job.status = status
            job.updated_at = datetime.utcnow()
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
            session.commit()
    engine.dispose()


# ---------------------------------------------------------------------------
# POST /v1/jobs/quasi-extinction
# ---------------------------------------------------------------------------

class TestCreateQuasiExtinctionJob:
    def test_requires_auth(self, client, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/jobs/quasi-extinction", json={
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 10,
            "n_runs": 20,
        })
        assert r.status_code == 401

    def test_returns_202_accepted(self, client, alice, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/jobs/quasi-extinction", json={
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 10,
            "n_runs": 20,
        }, headers=alice["headers"])
        assert r.status_code == 202

    def test_response_has_required_fields(self, client, alice, alice_job):
        for field in ("id", "job_type", "status", "created_at", "updated_at", "params"):
            assert field in alice_job, f"Missing field: {field}"

    def test_initial_status_is_pending(self, client, alice, alice_job):
        assert alice_job["status"] == "pending"

    def test_job_type_is_quasi_extinction(self, client, alice, alice_job):
        assert alice_job["job_type"] == "quasi_extinction"

    def test_params_snapshot_in_response(self, client, alice, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/jobs/quasi-extinction", json={
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 10,
            "n_runs": 20,
        }, headers=alice["headers"])
        assert r.status_code == 202
        data = r.json()
        assert data["params"]["n_runs"] == 20
        assert "extinction_threshold" not in data["params"]

    def test_matrices_snapshot_is_included(self, client, alice, alice_job):
        """matrices_snapshot must be stored in the job (immune to future matrix changes)."""
        assert alice_job["matrices_snapshot"] is not None
        assert len(alice_job["matrices_snapshot"]) == 2

    def test_missing_matrix_returns_404(self, client, alice, alice_matrix_a):
        r = client.post("/v1/jobs/quasi-extinction", json={
            "matrix_ids": [alice_matrix_a["id"], 999999],
            "initial_vector": VECTOR_2,
            "n_steps": 10,
            "n_runs": 20,
        }, headers=alice["headers"])
        assert r.status_code == 404

    def test_dimension_mismatch_between_matrices_returns_400(self, client, alice, alice_matrix_a):
        # Create a 3×3 matrix
        r3 = client.post("/v1/matrices", json={
            "species_accepted": "Big species",
            "kingdom": "Animalia",
            "matrix_a": [[0.5, 0.1, 0.0], [0.2, 0.6, 0.1], [0.0, 0.1, 0.7]],
        }, headers=alice["headers"])
        assert r3.status_code == 201
        big_id = r3.json()["id"]

        r = client.post("/v1/jobs/quasi-extinction", json={
            "matrix_ids": [alice_matrix_a["id"], big_id],
            "initial_vector": VECTOR_2,
            "n_steps": 10,
            "n_runs": 20,
        }, headers=alice["headers"])
        assert r.status_code == 400
        assert "dimension" in r.json()["detail"].lower()

    def test_vector_size_mismatch_returns_400(self, client, alice, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/jobs/quasi-extinction", json={
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": [1.0, 2.0, 3.0],  # 3 elements, matrices are 2×2
            "n_steps": 10,
            "n_runs": 20,
        }, headers=alice["headers"])
        assert r.status_code == 400

    def test_single_matrix_returns_422(self, client, alice, alice_matrix_a):
        """matrix_ids requires at least 2 matrices."""
        r = client.post("/v1/jobs/quasi-extinction", json={
            "matrix_ids": [alice_matrix_a["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 10,
            "n_runs": 20,
        }, headers=alice["headers"])
        assert r.status_code == 422

    def test_n_steps_above_max_returns_422(self, client, alice, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/jobs/quasi-extinction", json={
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 50001,
            "n_runs": 20,
        }, headers=alice["headers"])
        assert r.status_code == 422

    def test_n_runs_above_max_returns_422(self, client, alice, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/jobs/quasi-extinction", json={
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 10,
            "n_runs": 50001,  # max is 50000
        }, headers=alice["headers"])
        assert r.status_code == 422

    def test_n_runs_below_min_returns_422(self, client, alice, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/jobs/quasi-extinction", json={
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 10,
            "n_runs": 5,   # min is 10
        }, headers=alice["headers"])
        assert r.status_code == 422

    def test_invalid_token_returns_401(self, client, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/jobs/quasi-extinction", json={
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 10,
            "n_runs": 20,
        }, headers={"Authorization": "Bearer bad.token.here"})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /v1/jobs  (list)
# ---------------------------------------------------------------------------

class TestListJobs:
    def test_requires_auth(self, client):
        r = client.get("/v1/jobs")
        assert r.status_code == 401

    def test_empty_before_any_jobs(self, client, alice):
        r = client.get("/v1/jobs", headers=alice["headers"])
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_own_jobs(self, client, alice, alice_job):
        r = client.get("/v1/jobs", headers=alice["headers"])
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == alice_job["id"]

    def test_only_own_jobs_visible(self, client, alice, bob, alice_job):
        """bob's list should be empty even though alice has a job."""
        bob_r = client.get("/v1/jobs", headers=bob["headers"])
        assert bob_r.status_code == 200
        assert bob_r.json() == []

    def test_list_contains_summary_fields(self, client, alice, alice_job):
        r = client.get("/v1/jobs", headers=alice["headers"])
        item = r.json()[0]
        for field in ("id", "job_type", "status", "created_at", "updated_at"):
            assert field in item, f"Missing summary field: {field}"

    def test_list_does_not_include_result(self, client, alice, alice_job):
        """Summary list should not include the (potentially large) result dict."""
        r = client.get("/v1/jobs", headers=alice["headers"])
        item = r.json()[0]
        assert "result" not in item

    def test_list_does_not_include_matrices_snapshot(self, client, alice, alice_job):
        """Summary list should not include the matrices_snapshot blob."""
        r = client.get("/v1/jobs", headers=alice["headers"])
        item = r.json()[0]
        assert "matrices_snapshot" not in item

    def test_multiple_jobs_returned(self, client, alice, alice_matrix_a, alice_matrix_b):
        payload = {
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 5,
            "n_runs": 10,
        }
        client.post("/v1/jobs/quasi-extinction", json=payload, headers=alice["headers"])
        client.post("/v1/jobs/quasi-extinction", json=payload, headers=alice["headers"])

        r = client.get("/v1/jobs", headers=alice["headers"])
        assert r.status_code == 200
        assert len(r.json()) == 2


# ---------------------------------------------------------------------------
# GET /v1/jobs/{id}
# ---------------------------------------------------------------------------

class TestGetJob:
    def test_requires_auth(self, client, alice_job):
        r = client.get(f"/v1/jobs/{alice_job['id']}")
        assert r.status_code == 401

    def test_returns_job_by_id(self, client, alice, alice_job):
        r = client.get(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == alice_job["id"]
        assert data["status"] == "pending"

    def test_response_includes_params(self, client, alice, alice_job):
        r = client.get(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])
        assert r.status_code == 200
        data = r.json()
        assert "params" in data
        assert "matrix_ids" in data["params"]

    def test_response_includes_matrices_snapshot(self, client, alice, alice_job):
        r = client.get(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])
        assert r.status_code == 200
        data = r.json()
        assert "matrices_snapshot" in data
        assert data["matrices_snapshot"] is not None
        assert len(data["matrices_snapshot"]) == 2

    def test_result_is_none_for_pending_job(self, client, alice, alice_job):
        r = client.get(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])
        assert r.json()["result"] is None

    def test_error_is_none_for_pending_job(self, client, alice, alice_job):
        r = client.get(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])
        assert r.json()["error"] is None

    def test_not_found_returns_404(self, client, alice):
        r = client.get("/v1/jobs/999999", headers=alice["headers"])
        assert r.status_code == 404

    def test_other_user_cannot_access(self, client, bob, alice_job):
        r = client.get(f"/v1/jobs/{alice_job['id']}", headers=bob["headers"])
        assert r.status_code == 403

    def test_completed_job_has_result(self, client, alice, alice_job):
        """After forcing completed status, result should appear in the response."""
        fake_result = {
            "n_runs": 20,
            "n_extinct": 3,
            "quasi_extinction_probability": 0.15,
            "time_to_extinction_distribution": {},
            "mean_final_population": 42.0,
            "std_final_population": 5.0,
            "lambda_s_distribution": [1.1] * 20,
        }
        _force_job_status(alice_job["id"], "completed", result=fake_result)

        r = client.get(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "completed"
        assert data["result"] is not None
        assert data["result"]["quasi_extinction_probability"] == pytest.approx(0.15)

    def test_failed_job_has_error(self, client, alice, alice_job):
        """After forcing failed status, error should appear in the response."""
        _force_job_status(alice_job["id"], "failed", error="Something went wrong")

        r = client.get(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "failed"
        assert data["error"] == "Something went wrong"

    def test_completed_job_result_has_full_structure(self, client, alice, alice_job):
        """Completed job result includes all expected quasi-extinction output keys."""
        fake_result = {
            "n_runs": 20,
            "n_extinct": 3,
            "quasi_extinction_probability": 0.15,
            "time_to_extinction_distribution": {"5": 2, "8": 1},
            "mean_final_population": 42.0,
            "std_final_population": 5.0,
            "lambda_s_distribution": [1.1] * 20,
            "average_matrix": [[0.25, 0.20], [0.15, 0.75]],
            "extinction_trigger_counts": {"0": 3},
        }
        _force_job_status(alice_job["id"], "completed", result=fake_result)
        r = client.get(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])
        assert r.status_code == 200
        result = r.json()["result"]
        for key in (
            "n_runs", "n_extinct", "quasi_extinction_probability",
            "time_to_extinction_distribution",
            "mean_final_population", "std_final_population",
            "lambda_s_distribution", "average_matrix", "extinction_trigger_counts",
        ):
            assert key in result, f"Missing result key: {key}"
        assert result["average_matrix"] is not None
        assert result["extinction_trigger_counts"] == {"0": 3}


# ---------------------------------------------------------------------------
# DELETE /v1/jobs/{id}
# ---------------------------------------------------------------------------

class TestDeleteJob:
    def test_requires_auth(self, client, alice_job):
        r = client.delete(f"/v1/jobs/{alice_job['id']}")
        assert r.status_code == 401

    def test_pending_job_cannot_be_deleted(self, client, alice, alice_job):
        """Deleting a pending job must return 409 Conflict."""
        r = client.delete(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])
        assert r.status_code == 409
        assert "pending" in r.json()["detail"].lower()

    def test_not_found_returns_404(self, client, alice):
        r = client.delete("/v1/jobs/999999", headers=alice["headers"])
        assert r.status_code == 404

    def test_other_user_cannot_delete(self, client, bob, alice_job):
        r = client.delete(f"/v1/jobs/{alice_job['id']}", headers=bob["headers"])
        assert r.status_code == 403

    def test_delete_completed_job_returns_204(self, client, alice, alice_job):
        _force_job_status(alice_job["id"], "completed", result={"n_runs": 10})

        r = client.delete(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])
        assert r.status_code == 204

    def test_deleted_completed_job_no_longer_accessible(self, client, alice, alice_job):
        _force_job_status(alice_job["id"], "completed", result={"n_runs": 10})

        client.delete(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])

        r = client.get(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])
        assert r.status_code == 404

    def test_delete_failed_job_returns_204(self, client, alice, alice_job):
        _force_job_status(alice_job["id"], "failed", error="Computation error")

        r = client.delete(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])
        assert r.status_code == 204

    def test_deleted_job_disappears_from_list(self, client, alice, alice_job):
        _force_job_status(alice_job["id"], "completed", result={"n_runs": 10})
        client.delete(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])

        r = client.get("/v1/jobs", headers=alice["headers"])
        ids = [j["id"] for j in r.json()]
        assert alice_job["id"] not in ids

    def test_running_job_cannot_be_deleted(self, client, alice, alice_job):
        """Jobs with status='running' are also not deletable (same as pending)."""
        _force_job_status(alice_job["id"], "running")

        r = client.delete(f"/v1/jobs/{alice_job['id']}", headers=alice["headers"])
        assert r.status_code == 409
