"""
Tests for /v1/matrices — list, retrieve, create, update.
Rules under test:
  - Read endpoints are public (no auth required).
  - Create requires auth; caller becomes owner; source_type is always "custom".
  - PATCH requires auth + ownership; COMPADRE matrices are always read-only.
"""
import io
import json

MATRIX_PAYLOAD = {
    "species_accepted": "Canis lupus",
    "kingdom": "Animalia",
    "country_code": "ESP",
    "matrix_a": [[0.0, 3.0], [0.6, 0.8]],
    "stage_names": ["pup", "adult"],
    "visibility": "public",   # keep tests unauthenticated-friendly
}


# ---------------------------------------------------------------------------
# List  GET /v1/matrices
# ---------------------------------------------------------------------------

def test_list_empty(client):
    r = client.get("/v1/matrices")
    assert r.status_code == 200
    assert r.json() == []


def test_list_returns_created_matrix(client, alice, alice_matrix):
    r = client.get("/v1/matrices")
    assert r.status_code == 200
    ids = [m["id"] for m in r.json()]
    assert alice_matrix["id"] in ids


def test_list_filter_by_species(client, alice, alice_matrix):
    r = client.get("/v1/matrices?species=Homo")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["species_accepted"] == "Homo sapiens"


def test_list_filter_by_kingdom(client, alice, alice_matrix):
    r = client.get("/v1/matrices?kingdom=Animalia")
    assert r.status_code == 200
    assert all(m["kingdom"] == "Animalia" for m in r.json())


def test_list_filter_by_source_type(client, alice, alice_matrix, compadre_matrix_id):
    r = client.get("/v1/matrices?source_type=custom")
    assert r.status_code == 200
    assert all(m["source_type"] == "custom" for m in r.json())

    r = client.get("/v1/matrices?source_type=compadre")
    assert r.status_code == 200
    assert all(m["source_type"] == "compadre" for m in r.json())


def test_list_pagination(client, alice):
    for i in range(5):
        client.post("/v1/matrices", json={
            **MATRIX_PAYLOAD,
            "species_accepted": f"Species {i}",
        }, headers=alice["headers"])

    r = client.get("/v1/matrices?limit=3&skip=0")
    assert r.status_code == 200
    assert len(r.json()) == 3

    r = client.get("/v1/matrices?limit=3&skip=3")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_no_matrix_data_in_summary(client, alice, alice_matrix):
    """List endpoint returns MatrixSummary — no matrix_a/u/f fields, but has visibility."""
    r = client.get("/v1/matrices")
    assert r.status_code == 200
    item = r.json()[0]
    assert "matrix_a" not in item
    assert "matrix_u" not in item
    assert "visibility" in item


def test_list_mine_excludes_other_users_public_matrices(client, alice, bob, alice_matrix):
    """`mine=true` must only return the caller's own matrices, not matrices made
    visible to them (public/shared) by other users."""
    r = client.post("/v1/matrices", json={
        **MATRIX_PAYLOAD,
        "species_accepted": "Bob's public matrix",
        "visibility": "public",
    }, headers=bob["headers"])
    assert r.status_code == 201
    bob_matrix_id = r.json()["id"]

    r = client.get("/v1/matrices?mine=true", headers=alice["headers"])
    assert r.status_code == 200
    ids = [m["id"] for m in r.json()]
    assert alice_matrix["id"] in ids
    assert bob_matrix_id not in ids


def test_list_mine_without_auth_returns_empty(client, alice, alice_matrix):
    r = client.get("/v1/matrices?mine=true")
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# Retrieve  GET /v1/matrices/{id}
# ---------------------------------------------------------------------------

def test_get_matrix(client, alice_matrix):
    r = client.get(f"/v1/matrices/{alice_matrix['id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["species_accepted"] == "Homo sapiens"
    assert data["matrix_a"] is not None
    assert data["source_type"] == "custom"


def test_get_matrix_not_found(client):
    r = client.get("/v1/matrices/999999")
    assert r.status_code == 404


def test_get_compadre_matrix(client, compadre_matrix_id):
    r = client.get(f"/v1/matrices/{compadre_matrix_id}")
    assert r.status_code == 200
    assert r.json()["source_type"] == "compadre"


def test_get_public_matrix_no_auth_required(client, alice_matrix):
    """Public matrices are readable without a token."""
    r = client.get(f"/v1/matrices/{alice_matrix['id']}")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Create  POST /v1/matrices
# ---------------------------------------------------------------------------

def test_create_matrix(client, alice):
    r = client.post("/v1/matrices", json=MATRIX_PAYLOAD, headers=alice["headers"])
    assert r.status_code == 201
    data = r.json()
    assert data["source_type"] == "custom"
    assert data["owner_id"] is not None
    assert data["species_accepted"] == MATRIX_PAYLOAD["species_accepted"]
    assert data["matrix_a"] == MATRIX_PAYLOAD["matrix_a"]


def test_create_sets_caller_as_owner(client, alice, bob):
    r_alice = client.post("/v1/auth/register", json={})  # alice already registered via fixture
    # get alice's id from a matrix she creates
    r = client.post("/v1/matrices", json=MATRIX_PAYLOAD, headers=alice["headers"])
    alice_owner_id = r.json()["owner_id"]

    r = client.post("/v1/matrices", json=MATRIX_PAYLOAD, headers=bob["headers"])
    bob_owner_id = r.json()["owner_id"]

    assert alice_owner_id != bob_owner_id


def test_create_requires_auth(client):
    r = client.post("/v1/matrices", json=MATRIX_PAYLOAD)
    assert r.status_code == 401


def test_create_requires_matrix_a(client, alice):
    payload = {k: v for k, v in MATRIX_PAYLOAD.items() if k != "matrix_a"}
    r = client.post("/v1/matrices", json=payload, headers=alice["headers"])
    assert r.status_code == 422


def test_create_invalid_token(client):
    r = client.post("/v1/matrices", json=MATRIX_PAYLOAD,
                    headers={"Authorization": "Bearer totally.invalid.token"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Update  PATCH /v1/matrices/{id}
# ---------------------------------------------------------------------------

def test_patch_matrix(client, alice, alice_matrix):
    r = client.patch(
        f"/v1/matrices/{alice_matrix['id']}",
        json={"common_name": "Human", "country_code": "ESP"},
        headers=alice["headers"],
    )
    assert r.status_code == 200
    data = r.json()
    assert data["common_name"] == "Human"
    assert data["country_code"] == "ESP"
    # Untouched fields are preserved
    assert data["species_accepted"] == alice_matrix["species_accepted"]
    assert data["matrix_a"] == alice_matrix["matrix_a"]


def test_patch_only_sent_fields_change(client, alice, alice_matrix):
    """PATCH must not zero-out fields that were not included in the request."""
    r = client.patch(
        f"/v1/matrices/{alice_matrix['id']}",
        json={"common_name": "Human"},
        headers=alice["headers"],
    )
    assert r.status_code == 200
    assert r.json()["kingdom"] == alice_matrix["kingdom"]


def test_patch_requires_auth(client, alice_matrix):
    r = client.patch(f"/v1/matrices/{alice_matrix['id']}", json={"common_name": "X"})
    assert r.status_code == 401


def test_patch_requires_ownership(client, alice_matrix, bob):
    """Bob cannot edit Alice's matrix."""
    r = client.patch(
        f"/v1/matrices/{alice_matrix['id']}",
        json={"common_name": "Hacked"},
        headers=bob["headers"],
    )
    assert r.status_code == 403


def test_patch_compadre_blocked(client, alice, compadre_matrix_id):
    """COMPADRE matrices are read-only for everyone, including authenticated users."""
    r = client.patch(
        f"/v1/matrices/{compadre_matrix_id}",
        json={"common_name": "Hacked"},
        headers=alice["headers"],
    )
    assert r.status_code == 403
    assert "read-only" in r.json()["detail"].lower()


def test_patch_not_found(client, alice):
    r = client.patch("/v1/matrices/999999", json={"common_name": "X"}, headers=alice["headers"])
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Validation  — matrix shape errors surfaced through the HTTP layer
# ---------------------------------------------------------------------------

def test_create_non_square_matrix_rejected(client, alice):
    r = client.post("/v1/matrices", json={
        **MATRIX_PAYLOAD,
        "matrix_a": [[1.0, 2.0, 3.0], [4.0, 5.0]],
    }, headers=alice["headers"])
    assert r.status_code == 422


def test_create_sub_matrix_dimension_mismatch(client, alice):
    r = client.post("/v1/matrices", json={
        **MATRIX_PAYLOAD,
        "matrix_u": [[0.0, 0.0, 0.0], [0.3, 0.0, 0.0], [0.0, 0.5, 0.6]],  # 3x3 vs 2x2
    }, headers=alice["headers"])
    assert r.status_code == 422


def test_create_stage_names_count_mismatch(client, alice):
    r = client.post("/v1/matrices", json={
        **MATRIX_PAYLOAD,
        "stage_names": ["only_one"],  # matrix_a is 2×2
    }, headers=alice["headers"])
    assert r.status_code == 422


def test_create_with_all_sub_matrices(client, alice):
    r = client.post("/v1/matrices", json={
        **MATRIX_PAYLOAD,
        "matrix_u": [[0.0, 0.0], [0.6, 0.8]],
        "matrix_f": [[0.0, 3.0], [0.0, 0.0]],
    }, headers=alice["headers"])
    assert r.status_code == 201
    data = r.json()
    assert data["matrix_u"] is not None
    assert data["matrix_f"] is not None


def test_create_with_null_matrix_cells(client, alice):
    """Matrix cells may be null (missing entries present in COMPADRE data)."""
    r = client.post("/v1/matrices", json={
        **MATRIX_PAYLOAD,
        "matrix_a": [[None, 3.0], [0.6, 0.8]],
    }, headers=alice["headers"])
    assert r.status_code == 201
    assert r.json()["matrix_a"][0][0] is None


# ---------------------------------------------------------------------------
# Filtering  — country_code filter
# ---------------------------------------------------------------------------

def test_list_filter_by_country_code(client, alice):
    client.post("/v1/matrices", json={**MATRIX_PAYLOAD, "country_code": "ESP"}, headers=alice["headers"])
    client.post("/v1/matrices", json={**MATRIX_PAYLOAD, "country_code": "DEU"}, headers=alice["headers"])

    r = client.get("/v1/matrices?country_code=ESP")
    assert r.status_code == 200
    assert all(m["country_code"] == "ESP" for m in r.json())


def test_list_limit_enforced(client, alice):
    r = client.get("/v1/matrices?limit=201")
    assert r.status_code == 422


def test_list_skip_negative_rejected(client):
    r = client.get("/v1/matrices?skip=-1")
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Count  GET /v1/matrices/count
# ---------------------------------------------------------------------------

class TestCountMatrices:
    def test_count_returns_total(self, client, alice, alice_matrix):
        r = client.get("/v1/matrices/count")
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert data["total"] >= 1

    def test_count_with_species_filter(self, client, alice, alice_matrix):
        r = client.get("/v1/matrices/count?species=Homo")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_count_with_nonexistent_species_returns_zero(self, client, alice, alice_matrix):
        r = client.get("/v1/matrices/count?species=Zzzznotarealspecies")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_count_requires_no_auth(self, client, alice, alice_matrix):
        """Count endpoint is public."""
        r = client.get("/v1/matrices/count")
        assert r.status_code == 200

    def test_count_filter_by_kingdom(self, client, alice, alice_matrix, compadre_matrix_id):
        r = client.get("/v1/matrices/count?kingdom=Animalia")
        assert r.status_code == 200
        assert r.json()["total"] == 1

        r = client.get("/v1/matrices/count?kingdom=Plantae")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_count_filter_by_source_type(self, client, alice, alice_matrix, compadre_matrix_id):
        r = client.get("/v1/matrices/count?source_type=custom")
        assert r.status_code == 200
        assert r.json()["total"] == 1

        r = client.get("/v1/matrices/count?source_type=compadre")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_count_respects_visibility(self, client, alice, alice_matrix, alice_private_matrix):
        """Private matrices are not counted for anonymous callers."""
        r = client.get("/v1/matrices/count")
        assert r.status_code == 200
        assert r.json()["total"] == 1  # only the public one


# ---------------------------------------------------------------------------
# Export  GET /v1/matrices/{id}/export
# ---------------------------------------------------------------------------

class TestExportMatrix:
    def test_export_json_returns_200(self, client, alice_matrix):
        r = client.get(f"/v1/matrices/{alice_matrix['id']}/export")
        assert r.status_code == 200

    def test_export_json_has_format_version_1(self, client, alice_matrix):
        r = client.get(f"/v1/matrices/{alice_matrix['id']}/export")
        assert r.status_code == 200
        data = r.json()
        assert data["format_version"] == "1"

    def test_export_json_includes_matrix_a(self, client, alice_matrix):
        r = client.get(f"/v1/matrices/{alice_matrix['id']}/export")
        assert r.status_code == 200
        data = r.json()
        assert "matrix_a" in data
        assert data["matrix_a"] is not None

    def test_export_csv_returns_text_csv_content_type(self, client, alice_matrix):
        r = client.get(f"/v1/matrices/{alice_matrix['id']}/export?format=csv")
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")

    def test_export_csv_header_row_contains_stage_names(self, client, alice_matrix):
        r = client.get(f"/v1/matrices/{alice_matrix['id']}/export?format=csv")
        assert r.status_code == 200
        first_line = r.text.split("\n")[0]
        assert "juvenile" in first_line
        assert "adult" in first_line

    def test_export_csv_data_rows_count_matches_dimension(self, client, alice_matrix):
        """2×2 matrix → header + 2 data rows = 3 non-empty lines."""
        r = client.get(f"/v1/matrices/{alice_matrix['id']}/export?format=csv")
        assert r.status_code == 200
        lines = [line for line in r.text.split("\n") if line.strip()]
        assert len(lines) == 3  # header + 2 data rows

    def test_export_private_matrix_anonymous_returns_403(self, client, alice_private_matrix):
        r = client.get(f"/v1/matrices/{alice_private_matrix['id']}/export")
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Import  POST /v1/matrices/import
# ---------------------------------------------------------------------------

class TestImportMatrices:
    def _json_file(self, matrix_a, species="Test sp", stage_names=None):
        """Helper to build a JSON file payload."""
        payload = {"matrix_a": matrix_a, "species_accepted": species}
        if stage_names:
            payload["stage_names"] = stage_names
        return ("file.json", io.BytesIO(json.dumps(payload).encode()), "application/json")

    def test_import_single_json_creates_matrix(self, client, alice):
        f = self._json_file([[0.5, 0.0], [0.3, 0.8]], species="Imported sp", stage_names=["s1", "s2"])
        r = client.post(
            "/v1/matrices/import",
            files=[("files", f)],
            headers=alice["headers"],
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data["created"]) == 1
        assert data["errors"] == []
        assert data["created"][0]["species_accepted"] == "Imported sp"

    def test_import_requires_auth(self, client):
        f = ("f.json", io.BytesIO(json.dumps({"matrix_a": [[1.0]]}).encode()), "application/json")
        r = client.post("/v1/matrices/import", files=[("files", f)])
        assert r.status_code == 401

    def test_import_invalid_json_recorded_as_error(self, client, alice):
        f = ("bad.json", io.BytesIO(b"not-json"), "application/json")
        r = client.post("/v1/matrices/import", files=[("files", f)], headers=alice["headers"])
        assert r.status_code == 200
        data = r.json()
        assert data["created"] == []
        assert len(data["errors"]) == 1
        assert data["errors"][0]["filename"] == "bad.json"

    def test_import_missing_matrix_a_recorded_as_error(self, client, alice):
        f = ("no_a.json", io.BytesIO(json.dumps({"species_accepted": "X"}).encode()), "application/json")
        r = client.post("/v1/matrices/import", files=[("files", f)], headers=alice["headers"])
        assert r.status_code == 200
        data = r.json()
        assert data["created"] == []
        assert len(data["errors"]) == 1
        assert data["errors"][0]["filename"] == "no_a.json"

    def test_import_sets_source_type_custom(self, client, alice):
        """source_type in the file is informational — imported matrices are always 'custom'."""
        payload = {"matrix_a": [[0.5]], "source_type": "compadre"}
        f = ("m.json", io.BytesIO(json.dumps(payload).encode()), "application/json")
        r = client.post("/v1/matrices/import", files=[("files", f)], headers=alice["headers"])
        assert r.status_code == 200
        created = r.json()["created"]
        assert len(created) == 1
        assert created[0]["source_type"] == "custom"

    def test_import_multiple_files_partial_success(self, client, alice):
        """Valid + invalid files: one created, one error."""
        good = ("good.json", io.BytesIO(json.dumps({"matrix_a": [[0.5]]}).encode()), "application/json")
        bad  = ("bad.json",  io.BytesIO(b"not-json"), "application/json")
        r = client.post(
            "/v1/matrices/import",
            files=[("files", good), ("files", bad)],
            headers=alice["headers"],
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data["created"]) == 1
        assert len(data["errors"]) == 1
        assert data["errors"][0]["filename"] == "bad.json"


# ---------------------------------------------------------------------------
# Delete  DELETE /v1/matrices/{id}
# ---------------------------------------------------------------------------

class TestDeleteMatrix:
    def test_delete_own_matrix_returns_204(self, client, alice, alice_matrix):
        r = client.delete(f"/v1/matrices/{alice_matrix['id']}", headers=alice["headers"])
        assert r.status_code == 204

    def test_delete_requires_auth(self, client, alice_matrix):
        r = client.delete(f"/v1/matrices/{alice_matrix['id']}")
        assert r.status_code == 401

    def test_delete_not_found_returns_404(self, client, alice):
        r = client.delete("/v1/matrices/999999", headers=alice["headers"])
        assert r.status_code == 404

    def test_other_user_cannot_delete_returns_403(self, client, bob, alice_matrix):
        r = client.delete(f"/v1/matrices/{alice_matrix['id']}", headers=bob["headers"])
        assert r.status_code == 403

    def test_cannot_delete_compadre_matrix_returns_403(self, client, alice, compadre_matrix_id):
        r = client.delete(f"/v1/matrices/{compadre_matrix_id}", headers=alice["headers"])
        assert r.status_code == 403

    def test_deleted_matrix_no_longer_in_list(self, client, alice, alice_matrix):
        client.delete(f"/v1/matrices/{alice_matrix['id']}", headers=alice["headers"])
        r = client.get("/v1/matrices")
        ids = [m["id"] for m in r.json()]
        assert alice_matrix["id"] not in ids

    def test_delete_second_time_returns_404(self, client, alice, alice_matrix):
        client.delete(f"/v1/matrices/{alice_matrix['id']}", headers=alice["headers"])
        r = client.delete(f"/v1/matrices/{alice_matrix['id']}", headers=alice["headers"])
        assert r.status_code == 404
