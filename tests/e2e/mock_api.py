"""
Minimal FastAPI app that stands in for the real API during E2E tests.

Endpoints honour the real API contract (field names, HTTP status codes —
notably the 204 No Content + empty body returned by every DELETE endpoint)
so the Shiny frontend behaves exactly as in production.

Custom matrices, simulations, and quasi-extinction jobs are tracked in
process-memory dicts so create → list → delete round-trips work the way
the real API does. ``POST /_test/reset`` clears that state between tests.
"""
from fastapi import FastAPI, HTTPException, Request, Response

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

# A second static (COMPADRE-style) matrix, same shape/dimension as the first
# so stochastic Simulate and Quasi-Extinction flows — which require ≥2
# distinct matrices — can add both from a single search. Species name is
# deliberately different from the first so test_browse.py's strict-mode
# ".browse-row-species" locators keep matching exactly one "Abies alba" row.
_MATRIX_SUMMARY_2 = {**_MATRIX_SUMMARY, "id": 2, "species_accepted": "Picea abies"}
_MATRIX_DETAIL_2 = {**_MATRIX_DETAIL, "id": 2, "species_accepted": "Picea abies"}
_STATIC_MATRICES = {1: _MATRIX_DETAIL, 2: _MATRIX_DETAIL_2}

_CUSTOM_MATRIX_TEMPLATE = {
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

_SIM_RESULT_TEMPLATE = {
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
    "n_runs": None,
    "result_variance": None,
    "result_min_history": None,
    "result_max_history": None,
}

def _qe_result(n_stages: int) -> dict:
    """Build a result dict whose matrix/trajectory dimensions match
    n_stages — a mismatch (e.g. a 2-column trajectory for a 3-stage matrix)
    causes an IndexError in the frontend's chart renderer."""
    return {
        "quasi_extinction_probability": 0.2,
        "n_extinct": 2,
        "mean_final_population": 50.0,
        "std_final_population": 5.0,
        "average_matrix": [[0.2] * n_stages for _ in range(n_stages)],
        "mean_population_trajectory": [[10.0] * n_stages, [12.0] * n_stages],
    }


_JOB_TEMPLATE = {
    "job_type": "quasi_extinction",
    "status": "completed",
    "matrices_snapshot": [],
    "result": _qe_result(3),
    "error": None,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
}

_USER = {"id": 1, "username": "testuser", "email": "test@example.com"}

# ---------------------------------------------------------------------------
# Mutable per-process state — reset between tests via POST /_test/reset
# ---------------------------------------------------------------------------

_custom_matrices: dict[int, dict] = {}
_simulations: dict[int, dict] = {}
_jobs: dict[int, dict] = {}
_next_id = {"matrix": 100, "simulation": 100, "job": 100}


def _reset_state() -> None:
    _custom_matrices.clear()
    _simulations.clear()
    _jobs.clear()
    _next_id.update(matrix=100, simulation=100, job=100)


@app.post("/_test/reset")
def test_reset():
    """Test-only hook: clear in-memory state so each test starts clean."""
    _reset_state()
    return {"ok": True}


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
    if source_type == "custom":
        return list(_custom_matrices.values())
    return [_MATRIX_SUMMARY, _MATRIX_SUMMARY_2]


@app.get("/v1/matrices/count")
def count_matrices(species: str = "", kingdom: str = "", source_type: str = ""):
    return {"total": 2}


@app.get("/v1/matrices/{mid}")
def get_matrix(mid: int):
    if mid in _custom_matrices:
        return _custom_matrices[mid]
    return _STATIC_MATRICES.get(mid, _MATRIX_DETAIL)


@app.post("/v1/matrices")
async def create_matrix(request: Request):
    body = await request.json()
    mid = _next_id["matrix"]
    _next_id["matrix"] += 1
    matrix = {
        **_CUSTOM_MATRIX_TEMPLATE,
        "id": mid,
        "species_accepted": body.get("species_accepted") or f"Matrix #{mid}",
        "common_name": body.get("common_name"),
        "kingdom": body.get("kingdom"),
        "country_code": body.get("country_code"),
        "stage_names": body.get("stage_names") or _CUSTOM_MATRIX_TEMPLATE["stage_names"],
        "matrix_a": body.get("matrix_a") or _CUSTOM_MATRIX_TEMPLATE["matrix_a"],
        "matrix_u": body.get("matrix_u") or _CUSTOM_MATRIX_TEMPLATE["matrix_u"],
        "matrix_f": body.get("matrix_f") or _CUSTOM_MATRIX_TEMPLATE["matrix_f"],
        "visibility": body.get("visibility") or "private",
    }
    _custom_matrices[mid] = matrix
    return matrix


@app.patch("/v1/matrices/{mid}")
async def update_matrix(mid: int, request: Request):
    body = await request.json()
    if mid in _custom_matrices:
        _custom_matrices[mid].update({k: v for k, v in body.items() if v is not None})
        return _custom_matrices[mid]
    return _MATRIX_DETAIL


@app.delete("/v1/matrices/{mid}", status_code=204)
def delete_matrix(mid: int):
    _custom_matrices.pop(mid, None)
    return Response(status_code=204)


@app.get("/v1/simulations")
def list_simulations():
    return list(_simulations.values())


@app.post("/v1/simulations/run")
async def run_simulation(request: Request):
    body = await request.json()
    return {
        "id": 1,
        "name": "Sim #1",
        **_SIM_RESULT_TEMPLATE,
        "n_steps": body.get("n_steps", 20),
        "initial_vector": body.get("initial_vector", _SIM_RESULT_TEMPLATE["initial_vector"]),
    }


@app.post("/v1/simulations")
async def create_simulation(request: Request):
    body = await request.json()
    sid = _next_id["simulation"]
    _next_id["simulation"] += 1
    sim = {
        **_SIM_RESULT_TEMPLATE,
        "id": sid,
        "name": body.get("name") or f"Sim #{sid}",
        "matrix_id": body.get("matrix_id"),
        "matrix_ids": body.get("matrix_ids"),
        "stochastic": body.get("matrix_ids") is not None,
        "random_seed": body.get("random_seed"),
        "n_steps": body.get("n_steps", 20),
        "initial_vector": body.get("initial_vector", _SIM_RESULT_TEMPLATE["initial_vector"]),
    }
    _simulations[sid] = sim
    return sim


@app.get("/v1/simulations/{sid}")
def get_simulation(sid: int):
    if sid in _simulations:
        return _simulations[sid]
    return {"id": sid, "name": "Sim #1", **_SIM_RESULT_TEMPLATE}


@app.delete("/v1/simulations/{sid}", status_code=204)
def delete_simulation(sid: int):
    _simulations.pop(sid, None)
    return Response(status_code=204)


@app.post("/v1/jobs/quasi-extinction")
async def create_qe_job(request: Request):
    body = await request.json()
    jid = _next_id["job"]
    _next_id["job"] += 1
    stage_names = body.get("stage_names")
    n_stages = len(stage_names) if stage_names else 3
    job = {
        **_JOB_TEMPLATE,
        "id": jid,
        "result": _qe_result(n_stages),
        "params": {
            "matrix_ids": body.get("matrix_ids", []),
            "n_steps": body.get("n_steps", 50),
            "n_runs": body.get("n_runs", 500),
            "initial_vector": body.get("initial_vector", []),
            "stage_names": stage_names,
        },
    }
    _jobs[jid] = job
    return job


@app.get("/v1/jobs")
def list_jobs():
    return [
        {"id": j["id"], "status": j["status"], "created_at": j["created_at"]}
        for j in _jobs.values()
    ]


@app.get("/v1/jobs/{job_id}")
def get_job(job_id: int):
    if job_id in _jobs:
        return _jobs[job_id]
    return {**_JOB_TEMPLATE, "id": job_id, "params": {"matrix_ids": [1, 2]}}


@app.delete("/v1/jobs/{job_id}", status_code=204)
def delete_job(job_id: int):
    _jobs.pop(job_id, None)
    return Response(status_code=204)
