from dotenv import load_dotenv

load_dotenv()  # must run before any module reads os.environ

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.controllers import auth, jobs, matrices, simulations

app = FastAPI(
    title="Population Growth Simulator API",
    description="REST API for managing population matrices and running simulations.",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

import os

_origins = os.getenv("CORS_ORIGINS", "http://localhost,http://localhost:8080")
origins = [o.strip() for o in _origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(matrices.router)
app.include_router(simulations.router)
app.include_router(jobs.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
