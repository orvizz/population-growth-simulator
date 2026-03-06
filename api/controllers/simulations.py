"""
Simulations controller — HTTP concerns only.

Parses requests, delegates to SimulationService, returns records.
No business logic, no DB access.
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from api.records import SimulationRecord, SimulationRunResult, SimulationSummaryRecord, UserRecord
from api.schemas import SimulationCreate, SimulationImport
from api.deps import get_current_user, get_simulation_service
from api.services.simulation_service import SimulationService

router = APIRouter(prefix="/v1/simulations", tags=["simulations"])


# Public — no auth required
@router.post("/run", response_model=SimulationRunResult, status_code=status.HTTP_200_OK)
def run_simulation_ephemeral(
    body: SimulationCreate,
    service: SimulationService = Depends(get_simulation_service),
):
    """Compute a simulation without storing it. Available to anonymous users."""
    return service.run_ephemeral(body)


# Auth required
@router.post("", response_model=SimulationRecord, status_code=status.HTTP_201_CREATED)
def run_and_save_simulation(
    body: SimulationCreate,
    current_user: UserRecord = Depends(get_current_user),
    service: SimulationService = Depends(get_simulation_service),
):
    """Run a simulation and persist it to the user's library."""
    return service.run(body, user_id=current_user.id)


@router.get("", response_model=list[SimulationSummaryRecord])
def list_simulations(
    current_user: UserRecord = Depends(get_current_user),
    service: SimulationService = Depends(get_simulation_service),
):
    return service.list_for_user(current_user.id)


@router.get("/{sim_id}", response_model=SimulationRecord)
def get_simulation(
    sim_id: int,
    current_user: UserRecord = Depends(get_current_user),
    service: SimulationService = Depends(get_simulation_service),
):
    return service.get(sim_id, user_id=current_user.id)


@router.get("/{sim_id}/export")
def export_simulation(
    sim_id: int,
    current_user: UserRecord = Depends(get_current_user),
    service: SimulationService = Depends(get_simulation_service),
):
    """Return the simulation as a JSON-serialisable dict for client-side download."""
    return service.export(sim_id, user_id=current_user.id)


@router.post("/import", response_model=SimulationRecord, status_code=status.HTTP_201_CREATED)
def import_simulation(
    body: SimulationImport,
    current_user: UserRecord = Depends(get_current_user),
    service: SimulationService = Depends(get_simulation_service),
):
    """Restore a simulation from an exported JSON file into the user's library."""
    return service.import_simulation(body, user_id=current_user.id)


@router.delete("/{sim_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_simulation(
    sim_id: int,
    current_user: UserRecord = Depends(get_current_user),
    service: SimulationService = Depends(get_simulation_service),
):
    service.delete(sim_id, user_id=current_user.id)
