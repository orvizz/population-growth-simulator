= Testing Strategy <testing>

== Philosophy

The test suite is designed around two guiding principles.

*Fast feedback.* Unit tests that require no external dependencies run first in
CI and can also be run locally in seconds. This allows developers to validate
logic changes without needing a running database.

*Realistic coverage.* Integration tests exercise the full HTTP stack against a
real PostgreSQL instance, catching issues that unit tests with mocked
repositories cannot detect (SQL query correctness, migration state, serialisation
round-trips).

== Test Layout

```
tests/
  conftest.py               — shared fixtures (DB setup, TestClient, users)
  test_auth.py              — integration tests for /v1/auth/*
  test_matrices.py          — integration tests for /v1/matrices/*
  test_simulations.py       — integration tests for /v1/simulations/*
  test_health.py            — integration test for /health
  unit/
    test_schemas.py         — unit tests for Pydantic schema validation
    test_matrix_service.py  — unit tests for MatrixService (mocked repo)
    test_auth_service.py    — unit tests for AuthService (mocked repo)
    test_simulation_service.py — unit tests for SimulationService (mocked repos)
```

== Unit Tests

Unit tests live in `tests/unit/` and run with no database. Repositories are
replaced with `unittest.mock.MagicMock` instances whose return values are
configured per test case. This isolates the service layer's logic from
persistence concerns.

=== Schema Validation Tests (`test_schemas.py`)

These tests exercise the Pydantic schema classes directly by constructing them
with various valid and invalid payloads and asserting the resulting
`ValidationError` messages or the parsed model fields.

=== Service Tests (`test_matrix_service.py`, `test_auth_service.py`, `test_simulation_service.py`)

Service tests follow a common pattern:

+ Create a `MagicMock` for each repository the service depends on.
+ Configure the mock's return values to represent the desired database state.
+ Instantiate the service with the mock repositories.
+ Call the service method and assert on the return value or on the exception
  raised.
+ Assert that the mock's methods were (or were not) called with the expected
  arguments.

The simulation service unit tests additionally exercise the core static
methods directly:

- `_to_array` — verifies that `None` cells map to `0.0` and that the array
  dtype is `float`.
- `_compute_deterministic` — verifies history length, initial vector
  preservation, identity matrix behaviour, and a manual single-step product.
- `_compute_stochastic` — verifies history length, seed reproducibility, and
  that different seeds produce different trajectories.
- `_validate_vector` — verifies that a correct dimension passes silently and
  that a mismatch raises `HTTP 400`.

== Integration Tests

Integration tests use FastAPI's `TestClient` backed by a real PostgreSQL
database (`matrix_db_test`). The test database is created fresh at the start of
the test session and dropped at the end. All tables are truncated before each
individual test, guaranteeing complete isolation between tests.

=== Shared Fixtures (`conftest.py`)

`conftest.py` provides the following fixtures, available to all integration
tests.

#table(
  columns: (auto, 1fr),
  inset: 8pt,
  align: left,
  table.header([*Fixture*], [*Description*]),
  [`client`],            [Truncates tables, wires the test DB, yields a `TestClient`],
  [`alice`],             [Registered user + auth headers],
  [`bob`],               [A second registered user for ownership tests],
  [`alice_matrix`],      [A custom matrix owned by alice (via API)],
  [`compadre_matrix_id`],[A COMPADRE matrix inserted directly into the test DB],
)

=== Simulation Integration Tests (`test_simulations.py`)

The simulation integration tests cover:

- *Ephemeral runs* — public access, correct history length, first element equals
  initial vector, reproducibility with the same seed, all error cases (matrix
  not found, vector mismatch, dimension mismatch between stochastic matrices,
  schema validation failures).
- *Stored runs* — authentication requirement, deterministic and stochastic
  persistence, auto-naming, invalid token rejection.
- *List* — authentication requirement, ownership isolation (each user sees only
  their own simulations), empty list, absence of `result_history` in list items.
- *Get* — full history returned, authentication requirement, 404 and 403 cases.
- *Export / import* — correct JSON structure, round-trip (export then re-import
  produces a second stored record), missing field rejection.
- *Delete* — resource removal confirmed by a subsequent GET, ownership guard,
  authentication requirement.

== Running the Tests

```bash
# Unit tests only — no database needed
python -m pytest tests/unit/ -v

# Full suite — requires PostgreSQL from .env
python -m pytest tests/ -v

# Single file
python -m pytest tests/test_simulations.py -v

# By name pattern
python -m pytest tests/ -k "stochastic"

# With coverage
python -m pytest tests/ --cov=api --cov=db --cov-report=term-missing
```

== Coverage

Coverage is measured with `pytest-cov` and reported to Codecov on every push
to `main`. The coverage run includes both unit and integration tests to
produce a combined report covering the `api/` and `db/` modules. The CI
pipeline generates both a terminal summary and an XML report consumed by the
Codecov action.
