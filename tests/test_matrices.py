"""
Tests for /v1/matrices — list, retrieve, create, update.
Rules under test:
  - Read endpoints are public (no auth required).
  - Create requires auth; caller becomes owner; source_type is always "custom".
  - PATCH requires auth + ownership; COMPADRE matrices are always read-only.
"""

MATRIX_PAYLOAD = {
    "species_accepted": "Canis lupus",
    "kingdom": "Animalia",
    "country_code": "ESP",
    "matrix_a": [[0.0, 3.0], [0.6, 0.8]],
    "stage_names": ["pup", "adult"],
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
    """List endpoint returns MatrixSummary — no matrix_a/u/f fields."""
    r = client.get("/v1/matrices")
    assert r.status_code == 200
    item = r.json()[0]
    assert "matrix_a" not in item
    assert "matrix_u" not in item


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


def test_get_matrix_no_auth_required(client, alice_matrix):
    """Read is public — no token needed."""
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
