# Testing

The test suite uses **pytest** with FastAPI's built-in `TestClient`. Tests run against a dedicated PostgreSQL database (`matrix_db_test`) created automatically at the start of each run and dropped at the end. No test data ever touches the production `matrix_db`.

---

## Prerequisites

- PostgreSQL container running: `docker compose up -d db`
- Dev dependencies installed:

```bash
pip install -r requirements-dev.txt
```

---

## Running the tests

### Full suite

```bash
python -m pytest tests/ -v
```

### Single file

```bash
python -m pytest tests/test_matrices.py -v
```

### Single test

```bash
python -m pytest tests/test_matrices.py::test_patch_compadre_blocked -v
```

### Stop on first failure

```bash
python -m pytest tests/ -x
```

### With short summary (no verbose)

```bash
python -m pytest tests/
```

Expected output on a passing run:

```
31 passed in ~31s
```

---

## Test structure

```
tests/
├── conftest.py          # DB setup, shared fixtures
├── test_health.py       # /health endpoint
├── test_auth.py         # /v1/auth/register and /v1/auth/login
└── test_matrices.py     # /v1/matrices CRUD and access guards
```

### `conftest.py` — how isolation works

| Fixture | Scope | What it does |
|---|---|---|
| `test_database` | session | Creates `matrix_db_test`, builds all tables, drops DB on teardown |
| `client` | function | Truncates all tables, injects test DB into FastAPI DI, returns `TestClient` |
| `alice` | function | Registers a user and returns auth headers |
| `bob` | function | Second user — used to test ownership guards |
| `compadre_matrix_id` | function | Inserts a COMPADRE-style matrix directly (bypasses API) |
| `alice_matrix` | function | Creates a custom matrix owned by alice via the API |

Every test gets a completely empty database. Fixtures compose so a test can declare `(client, alice, compadre_matrix_id)` and get all three without writing any setup code.

---

## What is tested

### `test_health.py` (1 test)

| Test | Verifies |
|---|---|
| `test_health` | `GET /health` returns `200 {"status": "ok"}` |

### `test_auth.py` (8 tests)

| Test | Verifies |
|---|---|
| `test_register_success` | 201, returns user fields, password never exposed |
| `test_register_duplicate_username` | 409 with "username" in detail |
| `test_register_duplicate_email` | 409 with "email" in detail |
| `test_register_password_too_short` | 422 from Pydantic validation |
| `test_register_invalid_email` | 422 from Pydantic email validation |
| `test_login_success` | 200, returns `access_token` and `token_type` |
| `test_login_wrong_password` | 401 |
| `test_login_nonexistent_user` | 401 |

### `test_matrices.py` (22 tests)

#### List `GET /v1/matrices`

| Test | Verifies |
|---|---|
| `test_list_empty` | Empty DB returns `[]` |
| `test_list_returns_created_matrix` | Created matrix appears in list |
| `test_list_filter_by_species` | `?species=` partial match works |
| `test_list_filter_by_kingdom` | `?kingdom=` exact match works |
| `test_list_filter_by_source_type` | `?source_type=compadre/custom` separates correctly |
| `test_list_pagination` | `skip` and `limit` work correctly |
| `test_list_no_matrix_data_in_summary` | List response omits `matrix_a`/`matrix_u` (summary only) |

#### Retrieve `GET /v1/matrices/{id}`

| Test | Verifies |
|---|---|
| `test_get_matrix` | 200, full data including `matrix_a` |
| `test_get_matrix_not_found` | 404 for non-existent id |
| `test_get_compadre_matrix` | COMPADRE matrices are publicly readable |
| `test_get_matrix_no_auth_required` | Read is public — no token needed |

#### Create `POST /v1/matrices`

| Test | Verifies |
|---|---|
| `test_create_matrix` | 201, `source_type=custom`, `owner_id` set |
| `test_create_sets_caller_as_owner` | Alice and Bob get different `owner_id` values |
| `test_create_requires_auth` | 401 without token |
| `test_create_requires_matrix_a` | 422 if `matrix_a` missing |
| `test_create_invalid_token` | 401 for malformed token |

#### Update `PATCH /v1/matrices/{id}`

| Test | Verifies |
|---|---|
| `test_patch_matrix` | 200, updated fields reflect new values |
| `test_patch_only_sent_fields_change` | Omitted fields are not nulled out |
| `test_patch_requires_auth` | 401 without token |
| `test_patch_requires_ownership` | Bob gets 403 on Alice's matrix |
| `test_patch_compadre_blocked` | Any user gets 403 with "read-only" in detail |
| `test_patch_not_found` | 404 for non-existent id |

---

## Known warnings

The suite currently emits `DeprecationWarning: datetime.datetime.utcnow()` from SQLAlchemy internals. This is a SQLAlchemy issue with Python 3.12+ and does not affect test results. It will be resolved in a future SQLAlchemy release.

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `connection refused` | PostgreSQL not running | `docker compose up -d db` |
| `database "matrix_db_test" already exists` | Previous run crashed before teardown | `docker compose exec db psql -U postgres -c "DROP DATABASE matrix_db_test;"` |
| `ModuleNotFoundError: api` | Not running from project root | `cd` to project root before running pytest |
| Tests slow (>60s) | First run builds the test DB | Normal — subsequent runs are faster |
