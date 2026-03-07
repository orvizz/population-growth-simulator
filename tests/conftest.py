"""
Shared fixtures for the test suite.

Test database: matrix_db_test (created/dropped per session).
Each test gets a clean slate — all tables are truncated before it runs.
"""
import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

_base = (
    f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}"
)
_ADMIN_URL = f"{_base}/postgres"
_TEST_DB_URL = f"{_base}/matrix_db_test"


# ---------------------------------------------------------------------------
# Session-scoped: create the test database once for the whole test run
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def test_database():
    admin = create_engine(_ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = 'matrix_db_test'"
        ))
        conn.execute(text("DROP DATABASE IF EXISTS matrix_db_test"))
        conn.execute(text("CREATE DATABASE matrix_db_test"))
    admin.dispose()

    from db.models import Base
    engine = create_engine(_TEST_DB_URL)
    Base.metadata.create_all(engine)
    engine.dispose()

    yield

    admin = create_engine(_ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = 'matrix_db_test'"
        ))
        conn.execute(text("DROP DATABASE IF EXISTS matrix_db_test"))
    admin.dispose()


# ---------------------------------------------------------------------------
# Function-scoped: clean tables + TestClient per test
# ---------------------------------------------------------------------------

@pytest.fixture
def client(test_database):
    from db.models import Base
    from api.main import app
    from api.deps import get_db

    engine = create_engine(_TEST_DB_URL)
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    # Truncate all tables in dependency order
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


# ---------------------------------------------------------------------------
# Convenience fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def alice(client):
    """Registered user + auth headers."""
    client.post("/v1/auth/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "password123",
    })
    r = client.post("/v1/auth/login", data={"username": "alice", "password": "password123"})
    token = r.json()["access_token"]
    return {"headers": {"Authorization": f"Bearer {token}"}, "username": "alice"}


@pytest.fixture
def bob(client):
    """A second registered user — used to test ownership guards."""
    client.post("/v1/auth/register", json={
        "username": "bob",
        "email": "bob@example.com",
        "password": "password123",
    })
    r = client.post("/v1/auth/login", data={"username": "bob", "password": "password123"})
    token = r.json()["access_token"]
    return {"headers": {"Authorization": f"Bearer {token}"}, "username": "bob"}


@pytest.fixture
def compadre_matrix_id(test_database):
    """Insert a COMPADRE-style matrix directly and return its id."""
    from db.models import PopulationMatrix

    engine = create_engine(_TEST_DB_URL)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        m = PopulationMatrix(
            source_type="compadre",
            owner_id=None,
            species_accepted="Abies balsamea",
            kingdom="Plantae",
            matrix_a=[[0.5, 0.0], [0.3, 0.8]],
            stage_names=["seedling", "adult"],
            metadata_={"MatrixID": 99999},
            visibility="public",   # COMPADRE is always public
        )
        session.add(m)
        session.commit()
        matrix_id = m.id
    engine.dispose()
    return matrix_id


@pytest.fixture
def alice_matrix(client, alice):
    """A public custom matrix owned by alice (used by tests that don't care about visibility)."""
    r = client.post("/v1/matrices", json={
        "species_accepted": "Homo sapiens",
        "kingdom": "Animalia",
        "matrix_a": [[0.0, 2.5], [0.8, 0.9]],
        "stage_names": ["juvenile", "adult"],
        "visibility": "public",
    }, headers=alice["headers"])
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def alice_private_matrix(client, alice):
    """A private custom matrix owned by alice."""
    r = client.post("/v1/matrices", json={
        "species_accepted": "Vulpes vulpes",
        "kingdom": "Animalia",
        "matrix_a": [[0.0, 2.0], [0.5, 0.8]],
        "stage_names": ["kit", "adult"],
        "visibility": "private",
    }, headers=alice["headers"])
    assert r.status_code == 201
    return r.json()
