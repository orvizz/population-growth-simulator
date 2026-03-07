"""
Integration tests for matrix visibility and share management.

Covers:
  - Private matrices hidden from anonymous and other users
  - Public matrices visible to everyone
  - Shared matrices visible to owner and explicitly shared users only
  - Visibility change via PATCH
  - Auto-promotion / auto-demotion of visibility when shares are added/removed
  - Share endpoints: list, add, remove
  - Access control on share endpoints
"""

MATRIX_PAYLOAD = {
    "species_accepted": "Felis catus",
    "kingdom": "Animalia",
    "matrix_a": [[0.0, 2.0], [0.5, 0.9]],
    "stage_names": ["kitten", "adult"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_matrix(client, headers, visibility="private", **extra):
    r = client.post("/v1/matrices", json={**MATRIX_PAYLOAD, "visibility": visibility, **extra},
                    headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Visibility filtering — GET /v1/matrices
# ---------------------------------------------------------------------------

class TestListVisibilityFiltering:
    def test_private_matrix_hidden_from_anonymous(self, client, alice):
        _create_matrix(client, alice["headers"], visibility="private")
        r = client.get("/v1/matrices")
        assert r.status_code == 200
        assert all(m["visibility"] != "private" or m["owner_id"] is None for m in r.json())

    def test_private_matrix_hidden_from_other_user(self, client, alice, bob):
        _create_matrix(client, alice["headers"], visibility="private")
        r = client.get("/v1/matrices", headers=bob["headers"])
        ids_visible_to_bob = [m["id"] for m in r.json()]
        # Bob should not see Alice's private matrices
        alice_matrices = client.get("/v1/matrices", headers=alice["headers"]).json()
        private_ids = [m["id"] for m in alice_matrices if m["visibility"] == "private"]
        for pid in private_ids:
            assert pid not in ids_visible_to_bob

    def test_private_matrix_visible_to_owner(self, client, alice):
        m = _create_matrix(client, alice["headers"], visibility="private")
        r = client.get("/v1/matrices", headers=alice["headers"])
        assert any(x["id"] == m["id"] for x in r.json())

    def test_public_matrix_visible_to_anonymous(self, client, alice):
        m = _create_matrix(client, alice["headers"], visibility="public")
        r = client.get("/v1/matrices")
        assert any(x["id"] == m["id"] for x in r.json())

    def test_public_matrix_visible_to_other_user(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"], visibility="public")
        r = client.get("/v1/matrices", headers=bob["headers"])
        assert any(x["id"] == m["id"] for x in r.json())

    def test_shared_matrix_visible_to_shared_user(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"], visibility="private")
        client.post(f"/v1/matrices/{m['id']}/shares",
                    json={"username": "bob"}, headers=alice["headers"])
        r = client.get("/v1/matrices", headers=bob["headers"])
        assert any(x["id"] == m["id"] for x in r.json())

    def test_shared_matrix_hidden_from_non_shared_user(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"], visibility="shared",
                           species_accepted="Lynx lynx")
        # Share with alice herself — just to set state; bob is NOT shared with
        r = client.get("/v1/matrices", headers=bob["headers"])
        assert not any(x["id"] == m["id"] for x in r.json())

    def test_list_response_includes_visibility_field(self, client, alice):
        _create_matrix(client, alice["headers"], visibility="public")
        r = client.get("/v1/matrices")
        assert r.status_code == 200
        assert all("visibility" in m for m in r.json())


# ---------------------------------------------------------------------------
# Visibility filtering — GET /v1/matrices/{id}
# ---------------------------------------------------------------------------

class TestGetMatrixVisibility:
    def test_private_matrix_returns_403_for_anonymous(self, client, alice):
        m = _create_matrix(client, alice["headers"], visibility="private")
        r = client.get(f"/v1/matrices/{m['id']}")
        assert r.status_code == 403

    def test_private_matrix_returns_403_for_other_user(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"], visibility="private")
        r = client.get(f"/v1/matrices/{m['id']}", headers=bob["headers"])
        assert r.status_code == 403

    def test_private_matrix_accessible_by_owner(self, client, alice):
        m = _create_matrix(client, alice["headers"], visibility="private")
        r = client.get(f"/v1/matrices/{m['id']}", headers=alice["headers"])
        assert r.status_code == 200

    def test_public_matrix_accessible_without_auth(self, client, alice):
        m = _create_matrix(client, alice["headers"], visibility="public")
        r = client.get(f"/v1/matrices/{m['id']}")
        assert r.status_code == 200

    def test_shared_matrix_accessible_by_shared_user(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"], visibility="private")
        client.post(f"/v1/matrices/{m['id']}/shares",
                    json={"username": "bob"}, headers=alice["headers"])
        r = client.get(f"/v1/matrices/{m['id']}", headers=bob["headers"])
        assert r.status_code == 200

    def test_shared_matrix_returns_403_for_non_shared_user(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"], visibility="shared",
                           species_accepted="Lynx pardinus")
        r = client.get(f"/v1/matrices/{m['id']}", headers=bob["headers"])
        assert r.status_code == 403

    def test_response_includes_visibility_field(self, client, alice):
        m = _create_matrix(client, alice["headers"], visibility="public")
        r = client.get(f"/v1/matrices/{m['id']}")
        assert "visibility" in r.json()


# ---------------------------------------------------------------------------
# Changing visibility — PATCH /v1/matrices/{id}
# ---------------------------------------------------------------------------

class TestChangeVisibility:
    def test_owner_can_make_private_public(self, client, alice):
        m = _create_matrix(client, alice["headers"], visibility="private")
        r = client.patch(f"/v1/matrices/{m['id']}", json={"visibility": "public"},
                         headers=alice["headers"])
        assert r.status_code == 200
        assert r.json()["visibility"] == "public"

    def test_owner_can_make_public_private(self, client, alice):
        m = _create_matrix(client, alice["headers"], visibility="public")
        r = client.patch(f"/v1/matrices/{m['id']}", json={"visibility": "private"},
                         headers=alice["headers"])
        assert r.status_code == 200
        assert r.json()["visibility"] == "private"

    def test_non_owner_cannot_change_visibility(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"], visibility="public")
        r = client.patch(f"/v1/matrices/{m['id']}", json={"visibility": "private"},
                         headers=bob["headers"])
        assert r.status_code == 403

    def test_invalid_visibility_value_rejected(self, client, alice):
        m = _create_matrix(client, alice["headers"], visibility="private")
        r = client.patch(f"/v1/matrices/{m['id']}", json={"visibility": "secret"},
                         headers=alice["headers"])
        assert r.status_code == 422

    def test_changing_to_private_removes_shares(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"], visibility="private")
        client.post(f"/v1/matrices/{m['id']}/shares",
                    json={"username": "bob"}, headers=alice["headers"])
        # Bob can access it now
        assert client.get(f"/v1/matrices/{m['id']}", headers=bob["headers"]).status_code == 200

        # Owner reverts to private
        client.patch(f"/v1/matrices/{m['id']}", json={"visibility": "private"},
                     headers=alice["headers"])
        # Bob can no longer access it
        assert client.get(f"/v1/matrices/{m['id']}", headers=bob["headers"]).status_code == 403
        # Shares list is now empty
        shares = client.get(f"/v1/matrices/{m['id']}/shares",
                            headers=alice["headers"]).json()
        assert shares == []


# ---------------------------------------------------------------------------
# Share endpoints
# ---------------------------------------------------------------------------

class TestShareEndpoints:
    # --- POST /v1/matrices/{id}/shares ---

    def test_add_share_auto_promotes_private_to_shared(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"], visibility="private")
        r = client.post(f"/v1/matrices/{m['id']}/shares",
                        json={"username": "bob"}, headers=alice["headers"])
        assert r.status_code == 201
        assert r.json()["shared_with_username"] == "bob"
        # Visibility was promoted
        updated = client.get(f"/v1/matrices/{m['id']}", headers=alice["headers"]).json()
        assert updated["visibility"] == "shared"

    def test_add_share_requires_auth(self, client, alice):
        m = _create_matrix(client, alice["headers"])
        r = client.post(f"/v1/matrices/{m['id']}/shares", json={"username": "bob"})
        assert r.status_code == 401

    def test_add_share_requires_ownership(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"], visibility="public")
        r = client.post(f"/v1/matrices/{m['id']}/shares",
                        json={"username": "alice"}, headers=bob["headers"])
        assert r.status_code == 403

    def test_add_share_unknown_user_returns_404(self, client, alice):
        m = _create_matrix(client, alice["headers"])
        r = client.post(f"/v1/matrices/{m['id']}/shares",
                        json={"username": "nobody_here"}, headers=alice["headers"])
        assert r.status_code == 404

    def test_add_share_with_self_returns_400(self, client, alice):
        m = _create_matrix(client, alice["headers"])
        r = client.post(f"/v1/matrices/{m['id']}/shares",
                        json={"username": "alice"}, headers=alice["headers"])
        assert r.status_code == 400

    def test_add_duplicate_share_returns_409(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"])
        client.post(f"/v1/matrices/{m['id']}/shares",
                    json={"username": "bob"}, headers=alice["headers"])
        r = client.post(f"/v1/matrices/{m['id']}/shares",
                        json={"username": "bob"}, headers=alice["headers"])
        assert r.status_code == 409

    # --- GET /v1/matrices/{id}/shares ---

    def test_list_shares_returns_shared_users(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"])
        client.post(f"/v1/matrices/{m['id']}/shares",
                    json={"username": "bob"}, headers=alice["headers"])
        r = client.get(f"/v1/matrices/{m['id']}/shares", headers=alice["headers"])
        assert r.status_code == 200
        usernames = [s["shared_with_username"] for s in r.json()]
        assert "bob" in usernames

    def test_list_shares_requires_auth(self, client, alice):
        m = _create_matrix(client, alice["headers"])
        r = client.get(f"/v1/matrices/{m['id']}/shares")
        assert r.status_code == 401

    def test_list_shares_requires_ownership(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"])
        r = client.get(f"/v1/matrices/{m['id']}/shares", headers=bob["headers"])
        assert r.status_code == 403

    def test_list_shares_empty_by_default(self, client, alice):
        m = _create_matrix(client, alice["headers"])
        r = client.get(f"/v1/matrices/{m['id']}/shares", headers=alice["headers"])
        assert r.status_code == 200
        assert r.json() == []

    # --- DELETE /v1/matrices/{id}/shares/{uid} ---

    def test_remove_share_revokes_access(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"])
        client.post(f"/v1/matrices/{m['id']}/shares",
                    json={"username": "bob"}, headers=alice["headers"])
        bob_id = client.get(f"/v1/matrices/{m['id']}/shares",
                            headers=alice["headers"]).json()[0]["shared_with_user_id"]

        r = client.delete(f"/v1/matrices/{m['id']}/shares/{bob_id}",
                          headers=alice["headers"])
        assert r.status_code == 204
        # Bob can no longer access it
        assert client.get(f"/v1/matrices/{m['id']}", headers=bob["headers"]).status_code == 403

    def test_remove_last_share_demotes_to_private(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"])
        client.post(f"/v1/matrices/{m['id']}/shares",
                    json={"username": "bob"}, headers=alice["headers"])
        bob_id = client.get(f"/v1/matrices/{m['id']}/shares",
                            headers=alice["headers"]).json()[0]["shared_with_user_id"]
        client.delete(f"/v1/matrices/{m['id']}/shares/{bob_id}",
                      headers=alice["headers"])
        updated = client.get(f"/v1/matrices/{m['id']}", headers=alice["headers"]).json()
        assert updated["visibility"] == "private"

    def test_remove_share_requires_auth(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"])
        client.post(f"/v1/matrices/{m['id']}/shares",
                    json={"username": "bob"}, headers=alice["headers"])
        bob_id = client.get(f"/v1/matrices/{m['id']}/shares",
                            headers=alice["headers"]).json()[0]["shared_with_user_id"]
        r = client.delete(f"/v1/matrices/{m['id']}/shares/{bob_id}")
        assert r.status_code == 401

    def test_remove_share_requires_ownership(self, client, alice, bob):
        m = _create_matrix(client, alice["headers"])
        client.post(f"/v1/matrices/{m['id']}/shares",
                    json={"username": "bob"}, headers=alice["headers"])
        bob_id = client.get(f"/v1/matrices/{m['id']}/shares",
                            headers=alice["headers"]).json()[0]["shared_with_user_id"]
        r = client.delete(f"/v1/matrices/{m['id']}/shares/{bob_id}",
                          headers=bob["headers"])
        assert r.status_code == 403

    def test_remove_nonexistent_share_returns_404(self, client, alice):
        m = _create_matrix(client, alice["headers"])
        r = client.delete(f"/v1/matrices/{m['id']}/shares/999999",
                          headers=alice["headers"])
        assert r.status_code == 404
