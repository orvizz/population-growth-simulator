"""
Integration tests for /v1/simulations.

Endpoints under test:
  POST   /v1/simulations/run        — ephemeral run, public
  POST   /v1/simulations            — run + store, auth required
  GET    /v1/simulations            — list own simulations, auth required
  GET    /v1/simulations/{id}       — get simulation, auth required + ownership
  GET    /v1/simulations/{id}/export
  POST   /v1/simulations/import
  DELETE /v1/simulations/{id}       — delete own simulation, auth required + ownership
"""
import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MATRIX_2X2 = [[0.0, 3.0], [0.6, 0.8]]
MATRIX_2X2_B = [[0.5, 0.1], [0.4, 0.7]]
VECTOR_2 = [10.0, 20.0]


@pytest.fixture
def alice_matrix_a(client, alice):
    """First custom 2×2 matrix owned by alice."""
    r = client.post("/v1/matrices", json={
        "species_accepted": "Felis catus",
        "kingdom": "Animalia",
        "matrix_a": MATRIX_2X2,
        "stage_names": ["kitten", "adult"],
    }, headers=alice["headers"])
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def alice_matrix_b(client, alice):
    """Second custom 2×2 matrix owned by alice (for stochastic tests)."""
    r = client.post("/v1/matrices", json={
        "species_accepted": "Felis catus variant",
        "kingdom": "Animalia",
        "matrix_a": MATRIX_2X2_B,
        "stage_names": ["kitten", "adult"],
    }, headers=alice["headers"])
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def alice_sim(client, alice, alice_matrix_a):
    """A stored deterministic simulation owned by alice."""
    r = client.post("/v1/simulations", json={
        "matrix_id": alice_matrix_a["id"],
        "initial_vector": VECTOR_2,
        "n_steps": 5,
        "name": "Alice det sim",
    }, headers=alice["headers"])
    assert r.status_code == 201
    return r.json()


# ---------------------------------------------------------------------------
# POST /v1/simulations/run  (ephemeral — public)
# ---------------------------------------------------------------------------

class TestRunEphemeral:
    def test_deterministic_no_auth_required(self, client, alice_matrix_a):
        r = client.post("/v1/simulations/run", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 4,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["stochastic"] is False
        assert data["matrix_id"] == alice_matrix_a["id"]
        assert len(data["result_history"]) == 5  # initial + 4 steps

    def test_stochastic_no_auth_required(self, client, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/simulations/run", json={
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 6,
            "random_seed": 42,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["stochastic"] is True
        assert data["matrix_id"] is None
        assert len(data["result_history"]) == 7

    def test_result_history_first_element_equals_initial_vector(self, client, alice_matrix_a):
        r = client.post("/v1/simulations/run", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 3,
        })
        assert r.status_code == 200
        assert r.json()["result_history"][0] == pytest.approx(VECTOR_2)

    def test_stochastic_reproducible_with_same_seed(self, client, alice_matrix_a, alice_matrix_b):
        payload = {
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 10,
            "random_seed": 99,
        }
        r1 = client.post("/v1/simulations/run", json=payload)
        r2 = client.post("/v1/simulations/run", json=payload)
        assert r1.json()["result_history"] == r2.json()["result_history"]

    def test_matrix_not_found_returns_404(self, client):
        r = client.post("/v1/simulations/run", json={
            "matrix_id": 999999,
            "initial_vector": VECTOR_2,
            "n_steps": 1,
        })
        assert r.status_code == 404

    def test_vector_size_mismatch_returns_400(self, client, alice_matrix_a):
        r = client.post("/v1/simulations/run", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": [1.0, 2.0, 3.0],  # 3 elements, matrix is 2×2
            "n_steps": 1,
        })
        assert r.status_code == 400

    def test_no_matrix_source_returns_422(self, client):
        r = client.post("/v1/simulations/run", json={
            "initial_vector": VECTOR_2,
            "n_steps": 1,
        })
        assert r.status_code == 422

    def test_both_matrix_id_and_matrix_ids_returns_422(self, client, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/simulations/run", json={
            "matrix_id": alice_matrix_a["id"],
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 1,
        })
        assert r.status_code == 422

    def test_single_matrix_in_matrix_ids_returns_422(self, client, alice_matrix_a):
        r = client.post("/v1/simulations/run", json={
            "matrix_ids": [alice_matrix_a["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 1,
        })
        assert r.status_code == 422

    def test_n_steps_zero_returns_422(self, client, alice_matrix_a):
        r = client.post("/v1/simulations/run", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 0,
        })
        assert r.status_code == 422

    def test_n_steps_exceeds_maximum_returns_422(self, client, alice_matrix_a):
        r = client.post("/v1/simulations/run", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 1001,
        })
        assert r.status_code == 422

    def test_stage_names_in_response(self, client, alice_matrix_a):
        r = client.post("/v1/simulations/run", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 1,
        })
        assert r.status_code == 200
        assert r.json()["stage_names"] == ["kitten", "adult"]

    def test_stochastic_dimension_mismatch_between_matrices_returns_400(self, client, alice, alice_matrix_a):
        # Create a 3×3 matrix
        r3 = client.post("/v1/matrices", json={
            "species_accepted": "Big species",
            "kingdom": "Animalia",
            "matrix_a": [[0.5, 0.1, 0.0], [0.2, 0.6, 0.1], [0.0, 0.1, 0.7]],
        }, headers=alice["headers"])
        assert r3.status_code == 201
        big_id = r3.json()["id"]

        r = client.post("/v1/simulations/run", json={
            "matrix_ids": [alice_matrix_a["id"], big_id],
            "initial_vector": VECTOR_2,
            "n_steps": 1,
        })
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# POST /v1/simulations  (run + store)
# ---------------------------------------------------------------------------

class TestRunAndStore:
    def test_deterministic_requires_auth(self, client, alice_matrix_a):
        r = client.post("/v1/simulations", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 3,
        })
        assert r.status_code == 401

    def test_deterministic_stored_and_returned(self, client, alice, alice_matrix_a):
        r = client.post("/v1/simulations", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 5,
            "name": "My sim",
        }, headers=alice["headers"])
        assert r.status_code == 201
        data = r.json()
        assert "id" in data
        assert data["stochastic"] is False
        assert data["matrix_id"] == alice_matrix_a["id"]
        assert data["n_steps"] == 5
        assert data["name"] == "My sim"
        assert len(data["result_history"]) == 6

    def test_stochastic_stored_and_returned(self, client, alice, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/simulations", json={
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 8,
            "random_seed": 7,
        }, headers=alice["headers"])
        assert r.status_code == 201
        data = r.json()
        assert data["stochastic"] is True
        assert set(data["matrix_ids"]) == {alice_matrix_a["id"], alice_matrix_b["id"]}
        assert data["random_seed"] == 7
        assert len(data["result_history"]) == 9

    def test_auto_name_assigned_when_name_omitted(self, client, alice, alice_matrix_a):
        r = client.post("/v1/simulations", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 1,
        }, headers=alice["headers"])
        assert r.status_code == 201
        assert r.json()["name"] is not None

    def test_invalid_token_returns_401(self, client, alice_matrix_a):
        r = client.post("/v1/simulations", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 1,
        }, headers={"Authorization": "Bearer bad.token.here"})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /v1/simulations  (list)
# ---------------------------------------------------------------------------

class TestListSimulations:
    def test_requires_auth(self, client):
        r = client.get("/v1/simulations")
        assert r.status_code == 401

    def test_returns_own_simulations_only(self, client, alice, bob, alice_matrix_a):
        # alice creates a sim
        client.post("/v1/simulations", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 2,
        }, headers=alice["headers"])

        alice_list = client.get("/v1/simulations", headers=alice["headers"])
        bob_list = client.get("/v1/simulations", headers=bob["headers"])

        assert alice_list.status_code == 200
        assert bob_list.status_code == 200
        assert len(alice_list.json()) == 1
        assert len(bob_list.json()) == 0

    def test_empty_list_before_any_runs(self, client, alice):
        r = client.get("/v1/simulations", headers=alice["headers"])
        assert r.status_code == 200
        assert r.json() == []

    def test_list_items_have_no_result_history(self, client, alice, alice_sim):
        r = client.get("/v1/simulations", headers=alice["headers"])
        assert r.status_code == 200
        for item in r.json():
            assert "result_history" not in item


# ---------------------------------------------------------------------------
# GET /v1/simulations/{id}
# ---------------------------------------------------------------------------

class TestGetSimulation:
    def test_returns_full_simulation_with_history(self, client, alice, alice_sim):
        r = client.get(f"/v1/simulations/{alice_sim['id']}", headers=alice["headers"])
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == alice_sim["id"]
        assert "result_history" in data
        assert len(data["result_history"]) == 6  # n_steps=5, so 6 entries

    def test_requires_auth(self, client, alice_sim):
        r = client.get(f"/v1/simulations/{alice_sim['id']}")
        assert r.status_code == 401

    def test_not_found_returns_404(self, client, alice):
        r = client.get("/v1/simulations/999999", headers=alice["headers"])
        assert r.status_code == 404

    def test_other_user_cannot_access(self, client, bob, alice_sim):
        r = client.get(f"/v1/simulations/{alice_sim['id']}", headers=bob["headers"])
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /v1/simulations/{id}/export
# ---------------------------------------------------------------------------

class TestExportSimulation:
    def test_export_returns_correct_structure(self, client, alice, alice_sim):
        r = client.get(f"/v1/simulations/{alice_sim['id']}/export", headers=alice["headers"])
        assert r.status_code == 200
        data = r.json()
        assert data["format_version"] == "2"
        assert "result_history" in data
        assert "exported_at" in data
        assert "matrices_snapshot" in data
        assert "matrix_sequence" in data
        assert "analytics" in data
        assert data["stochastic"] is False
        assert data["n_steps"] == 5

    def test_export_requires_auth(self, client, alice_sim):
        r = client.get(f"/v1/simulations/{alice_sim['id']}/export")
        assert r.status_code == 401

    def test_export_not_found_returns_404(self, client, alice):
        r = client.get("/v1/simulations/999999/export", headers=alice["headers"])
        assert r.status_code == 404

    def test_export_other_user_returns_403(self, client, bob, alice_sim):
        r = client.get(f"/v1/simulations/{alice_sim['id']}/export", headers=bob["headers"])
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /v1/simulations/import
# ---------------------------------------------------------------------------

class TestImportSimulation:
    def _export_payload(self, sim_id, matrix_id):
        return {
            "format_version": "1",
            "name": "Imported sim",
            "stochastic": False,
            "matrix_id": matrix_id,
            "matrix_ids": None,
            "initial_vector": VECTOR_2,
            "n_steps": 3,
            "random_seed": None,
            "stage_names": ["kitten", "adult"],
            "result_history": [
                [10.0, 20.0], [60.0, 22.0], [66.0, 53.6], [160.8, 82.48]
            ],
        }

    def test_import_requires_auth(self, client, alice_matrix_a):
        payload = self._export_payload(sim_id=1, matrix_id=alice_matrix_a["id"])
        r = client.post("/v1/simulations/import", json=payload)
        assert r.status_code == 401

    def test_import_stores_simulation(self, client, alice, alice_matrix_a):
        payload = self._export_payload(sim_id=1, matrix_id=alice_matrix_a["id"])
        r = client.post("/v1/simulations/import", json=payload, headers=alice["headers"])
        assert r.status_code == 201
        data = r.json()
        assert "id" in data
        assert data["name"] == "Imported sim"
        assert data["n_steps"] == 3
        assert data["stochastic"] is False

    def test_imported_simulation_appears_in_list(self, client, alice, alice_matrix_a):
        payload = self._export_payload(sim_id=1, matrix_id=alice_matrix_a["id"])
        client.post("/v1/simulations/import", json=payload, headers=alice["headers"])

        r = client.get("/v1/simulations", headers=alice["headers"])
        assert r.status_code == 200
        assert any(s["name"] == "Imported sim" for s in r.json())

    def test_import_missing_result_history_returns_422(self, client, alice, alice_matrix_a):
        payload = self._export_payload(sim_id=1, matrix_id=alice_matrix_a["id"])
        del payload["result_history"]
        r = client.post("/v1/simulations/import", json=payload, headers=alice["headers"])
        assert r.status_code == 422

    def test_roundtrip_export_then_import(self, client, alice, alice_sim):
        """Export a stored sim and re-import it — should produce a second stored record."""
        export_r = client.get(f"/v1/simulations/{alice_sim['id']}/export", headers=alice["headers"])
        assert export_r.status_code == 200

        import_payload = {k: v for k, v in export_r.json().items() if k != "exported_at"}
        import_payload["name"] = "Roundtrip copy"

        import_r = client.post("/v1/simulations/import", json=import_payload, headers=alice["headers"])
        assert import_r.status_code == 201
        assert import_r.json()["name"] == "Roundtrip copy"

        list_r = client.get("/v1/simulations", headers=alice["headers"])
        assert len(list_r.json()) == 2


# ---------------------------------------------------------------------------
# Analytics and snapshot fields — added in v2
# ---------------------------------------------------------------------------

class TestAnalyticsAndSnapshotFields:
    """Verify that analytics and matrices_snapshot are present and structurally correct
    in all relevant responses (ephemeral run, stored deterministic, stored stochastic)."""

    def test_ephemeral_run_includes_matrices_snapshot(self, client, alice_matrix_a):
        r = client.post("/v1/simulations/run", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 5,
        })
        assert r.status_code == 200
        data = r.json()
        assert "matrices_snapshot" in data
        assert data["matrices_snapshot"] is not None
        assert len(data["matrices_snapshot"]) == 1
        assert data["matrices_snapshot"][0] == MATRIX_2X2

    def test_ephemeral_deterministic_run_includes_analytics(self, client, alice_matrix_a):
        r = client.post("/v1/simulations/run", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 5,
        })
        assert r.status_code == 200
        analytics = r.json()["analytics"]
        assert analytics is not None
        assert "lambda_1" in analytics
        assert isinstance(analytics["lambda_1"], float)

    def test_deterministic_analytics_has_all_fields(self, client, alice_matrix_a):
        r = client.post("/v1/simulations/run", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 5,
        })
        analytics = r.json()["analytics"]
        for key in (
            "lambda_1",
            "stable_stage_distribution",
            "reproductive_value",
            "sensitivities",
            "elasticities",
            "analytics_reliable",
        ):
            assert key in analytics, f"Missing analytics key: {key}"

    def test_deterministic_elasticities_sum_to_one(self, client, alice_matrix_a):
        r = client.post("/v1/simulations/run", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 5,
        })
        elasticities = r.json()["analytics"]["elasticities"]
        total = sum(v for row in elasticities for v in row)
        assert abs(total - 1.0) < 1e-6

    def test_deterministic_stable_stage_distribution_sums_to_one(self, client, alice_matrix_a):
        r = client.post("/v1/simulations/run", json={
            "matrix_id": alice_matrix_a["id"],
            "initial_vector": VECTOR_2,
            "n_steps": 5,
        })
        ssd = r.json()["analytics"]["stable_stage_distribution"]
        assert abs(sum(ssd) - 1.0) < 1e-6

    def test_ephemeral_stochastic_run_includes_analytics(self, client, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/simulations/run", json={
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 30,
            "random_seed": 42,
        })
        assert r.status_code == 200
        analytics = r.json()["analytics"]
        assert analytics is not None
        assert "lambda_s" in analytics
        assert isinstance(analytics["lambda_s"], float)

    def test_stochastic_analytics_has_all_fields(self, client, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/simulations/run", json={
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 30,
            "random_seed": 7,
        })
        analytics = r.json()["analytics"]
        for key in (
            "lambda_s",
            "mean_matrix",
            "lambda_1_of_mean",
            "elasticities_of_mean",
            "stable_stage_distribution_of_mean",
            "analytics_reliable",
        ):
            assert key in analytics, f"Missing stochastic analytics key: {key}"

    def test_stored_deterministic_sim_includes_analytics(self, client, alice, alice_sim):
        r = client.get(f"/v1/simulations/{alice_sim['id']}", headers=alice["headers"])
        assert r.status_code == 200
        data = r.json()
        assert "analytics" in data
        assert data["analytics"] is not None
        assert "lambda_1" in data["analytics"]

    def test_stored_deterministic_sim_includes_matrices_snapshot(self, client, alice, alice_sim):
        r = client.get(f"/v1/simulations/{alice_sim['id']}", headers=alice["headers"])
        data = r.json()
        assert "matrices_snapshot" in data
        assert data["matrices_snapshot"] is not None
        assert len(data["matrices_snapshot"]) == 1

    def test_stored_deterministic_sim_matrix_sequence_is_none(self, client, alice, alice_sim):
        """Deterministic runs have no per-step matrix choices → matrix_sequence should be None."""
        r = client.get(f"/v1/simulations/{alice_sim['id']}", headers=alice["headers"])
        data = r.json()
        assert data["matrix_sequence"] is None

    def test_stored_stochastic_sim_has_matrix_sequence(self, client, alice, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/simulations", json={
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 8,
            "random_seed": 7,
        }, headers=alice["headers"])
        assert r.status_code == 201
        sim_id = r.json()["id"]

        r = client.get(f"/v1/simulations/{sim_id}", headers=alice["headers"])
        data = r.json()
        assert "matrix_sequence" in data
        assert data["matrix_sequence"] is not None
        assert len(data["matrix_sequence"]) == 8  # one index per step
        assert all(idx in (0, 1) for idx in data["matrix_sequence"])

    def test_stored_stochastic_sim_has_stochastic_analytics(self, client, alice, alice_matrix_a, alice_matrix_b):
        r = client.post("/v1/simulations", json={
            "matrix_ids": [alice_matrix_a["id"], alice_matrix_b["id"]],
            "initial_vector": VECTOR_2,
            "n_steps": 30,
            "random_seed": 7,
        }, headers=alice["headers"])
        assert r.status_code == 201
        sim_id = r.json()["id"]

        r = client.get(f"/v1/simulations/{sim_id}", headers=alice["headers"])
        analytics = r.json()["analytics"]
        assert analytics is not None
        assert "lambda_s" in analytics

    def test_import_v2_preserves_analytics_and_snapshot(self, client, alice, alice_sim):
        """Full v2 roundtrip: export → import → verify new fields survive the round-trip."""
        export_r = client.get(f"/v1/simulations/{alice_sim['id']}/export", headers=alice["headers"])
        assert export_r.status_code == 200
        export_data = export_r.json()
        assert export_data["format_version"] == "2"
        assert export_data["analytics"] is not None

        import_payload = {k: v for k, v in export_data.items() if k != "exported_at"}
        import_payload["name"] = "V2 import copy"

        import_r = client.post("/v1/simulations/import", json=import_payload, headers=alice["headers"])
        assert import_r.status_code == 201
        imported = import_r.json()
        assert imported["matrices_snapshot"] is not None
        assert imported["analytics"] is not None


# ---------------------------------------------------------------------------
# DELETE /v1/simulations/{id}
# ---------------------------------------------------------------------------

class TestDeleteSimulation:
    def test_delete_own_simulation(self, client, alice, alice_sim):
        r = client.delete(f"/v1/simulations/{alice_sim['id']}", headers=alice["headers"])
        assert r.status_code == 204

        r = client.get(f"/v1/simulations/{alice_sim['id']}", headers=alice["headers"])
        assert r.status_code == 404

    def test_delete_requires_auth(self, client, alice_sim):
        r = client.delete(f"/v1/simulations/{alice_sim['id']}")
        assert r.status_code == 401

    def test_delete_not_found_returns_404(self, client, alice):
        r = client.delete("/v1/simulations/999999", headers=alice["headers"])
        assert r.status_code == 404

    def test_other_user_cannot_delete(self, client, bob, alice_sim):
        r = client.delete(f"/v1/simulations/{alice_sim['id']}", headers=bob["headers"])
        assert r.status_code == 403

    def test_deleted_simulation_no_longer_in_list(self, client, alice, alice_sim):
        client.delete(f"/v1/simulations/{alice_sim['id']}", headers=alice["headers"])
        list_r = client.get("/v1/simulations", headers=alice["headers"])
        ids = [s["id"] for s in list_r.json()]
        assert alice_sim["id"] not in ids
