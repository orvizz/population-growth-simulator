"""
Minimal FastAPI app that stands in for the real API during E2E tests.

Every endpoint returns canned fixture data — no database, no auth logic.
The real API contract (field names, HTTP status codes) is honoured so the
Shiny frontend behaves exactly as in production.
"""
from fastapi import FastAPI, HTTPException, Request

app = FastAPI()

# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

_MATRIX_SUMMARY = {
    "id": 1,
    "species_accepted": "Abies alba",
    "common_name": "Silver fir",
    "kingdom": "Plantae",
    "country_code": "DEU",
    "source_type": "compadre",
    "stage_names": ["seedling", "juvenile", "adult"],
    "visibility": "public",
    "owner_id": None,
    "metadata": {},
}

_MATRIX_DETAIL = {
    **_MATRIX_SUMMARY,
    "matrix_a": [
        [0.20, 0.30, 0.50],
        [0.10, 0.40, 0.00],
        [0.00, 0.10, 0.80],
    ],
    "matrix_u": [
        [0.20, 0.30, 0.50],
        [0.10, 0.40, 0.00],
        [0.00, 0.10, 0.80],
    ],
    "matrix_f": [
        [0.00, 0.00, 0.00],
        [0.00, 0.00, 0.00],
        [0.00, 0.00, 0.00],
    ],
}

_CUSTOM_MATRIX = {
    "id": 2,
    "species_accepted": "Test species",
    "common_name": None,
    "kingdom": None,
    "country_code": None,
    "source_type": "custom",
    "stage_names": ["adult"],
    "visibility": "private",
    "owner_id": 1,
    "metadata": {},
    "matrix_a": [[0.5]],
    "matrix_u": [[0.5]],
    "matrix_f": [[0.0]],
}

_SIM_RESULT = {
    "id": 1,
    "name": "Sim #1",
    "matrix_id": 1,
    "matrix_ids": None,
    "stochastic": False,
    "random_seed": None,
    "n_steps": 20,
    "initial_vector": [100.0, 50.0, 10.0],
    "stage_names": ["seedling", "juvenile", "adult"],
    "result_history": [
        [100.0, 50.0, 10.0],
        [25.0,  30.0,  8.0],
        [20.0,  25.0, 24.5],
    ],
}

_USER = {"id": 1, "username": "testuser", "email": "test@example.com"}

_JOB = {
    "id": 1,
    "job_type": "quasi_extinction",
    "status": "pending",
    "params": {
        "matrix_ids": [1, 2],
        "n_runs": 100,
        "n_steps": 50,
        "extinction_threshold": 1.0,
        "initial_vector": [100.0, 50.0, 10.0],
    },
    "result": None,
    "error": None,
    "created_at": "2024-01-01T00:00:00",
}

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/auth/register")
async def register(request: Request):
    return _USER


@app.post("/v1/auth/login")
async def login(request: Request):
    """Return a mock token; reject username 'FAIL' to allow failure tests."""
    body = await request.form()
    if body.get("username") == "FAIL":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": "mock-token-e2e", "token_type": "bearer"}


@app.get("/v1/matrices")
def list_matrices(
    species: str = "",
    kingdom: str = "",
    source_type: str = "",
    country: str = "",
    limit: int = 100,
    skip: int = 0,
):
    # My-matrices tab filters by source_type=custom; return empty so the
    # sidebar doesn't show a COMPADRE entry in the user's personal list.
    if source_type == "custom":
        return []
    return [_MATRIX_SUMMARY]


@app.get("/v1/matrices/count")
def count_matrices(species: str = "", kingdom: str = "", source_type: str = ""):
    return {"total": 1}


@app.get("/v1/matrices/{mid}")
def get_matrix(mid: int):
    return _MATRIX_DETAIL


@app.post("/v1/matrices")
async def create_matrix(request: Request):
    return _CUSTOM_MATRIX


@app.patch("/v1/matrices/{mid}")
async def update_matrix(mid: int, request: Request):
    return _MATRIX_DETAIL


@app.delete("/v1/matrices/{mid}")
def delete_matrix(mid: int):
    return {"ok": True}


@app.get("/v1/simulations")
def list_simulations():
    return []


@app.post("/v1/simulations/run")
async def run_simulation(request: Request):
    body = await request.json()
    return {**_SIM_RESULT, "n_steps": body.get("n_steps", 20)}


@app.post("/v1/simulations")
async def create_simulation(request: Request):
    return _SIM_RESULT


@app.get("/v1/simulations/{sid}")
def get_simulation(sid: int):
    return _SIM_RESULT


@app.delete("/v1/simulations/{sid}")
def delete_simulation(sid: int):
    return {"ok": True}


@app.post("/v1/jobs/quasi-extinction")
async def create_qe_job(request: Request):
    return {**_JOB, "status": "pending"}


@app.get("/v1/jobs")
def list_jobs():
    return []


@app.get("/v1/jobs/{job_id}")
def get_job(job_id: int):
    return {**_JOB, "id": job_id}


@app.delete("/v1/jobs/{job_id}")
def delete_job(job_id: int):
    return {"ok": True}
