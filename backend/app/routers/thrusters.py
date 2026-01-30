"""Thruster management endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.data import (
    create_thruster,
    delete_thruster,
    get_all_thrusters,
    get_thruster,
    update_thruster,
)
from app.models import Thruster, ThrusterCreate, ThrusterType, ThrusterUpdate

router = APIRouter(prefix="/thrusters", tags=["thrusters"])


@router.get("", response_model=list[Thruster])
async def list_thrusters() -> list[Thruster]:
    """Get all user-defined thrusters."""
    return get_all_thrusters()


@router.get("/{thruster_id}", response_model=Thruster)
async def get_thruster_by_id(thruster_id: UUID) -> Thruster:
    """Get a specific thruster by ID."""
    thruster = get_thruster(thruster_id)
    if not thruster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thruster {thruster_id} not found",
        )
    return thruster


@router.post("", response_model=Thruster, status_code=status.HTTP_201_CREATED)
async def create_new_thruster(thruster_data: ThrusterCreate) -> Thruster:
    """Create a new thruster."""
    # Validate mixture ratio for biprop
    if thruster_data.thruster_type == ThrusterType.CHEMICAL_BIPROP:
        if thruster_data.mixture_ratio_ox_to_fuel is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Mixture ratio is required for bipropellant thrusters",
            )
    elif thruster_data.mixture_ratio_ox_to_fuel is not None:
        # Clear mixture ratio for mono thrusters
        thruster_data = ThrusterCreate(
            name=thruster_data.name,
            thruster_type=thruster_data.thruster_type,
            isp_s=thruster_data.isp_s,
            mixture_ratio_ox_to_fuel=None,
        )

    thruster = Thruster(**thruster_data.model_dump())
    return create_thruster(thruster)


@router.put("/{thruster_id}", response_model=Thruster)
async def update_existing_thruster(thruster_id: UUID, updates: ThrusterUpdate) -> Thruster:
    """Update an existing thruster."""
    existing = get_thruster(thruster_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thruster {thruster_id} not found",
        )

    # Determine final thruster type
    final_type = updates.thruster_type if updates.thruster_type else existing.thruster_type

    # Validate mixture ratio for biprop
    if final_type == ThrusterType.CHEMICAL_BIPROP:
        final_mr = updates.mixture_ratio_ox_to_fuel
        if final_mr is None:
            final_mr = existing.mixture_ratio_ox_to_fuel
        if final_mr is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Mixture ratio is required for bipropellant thrusters",
            )

    updated = update_thruster(thruster_id, updates.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thruster {thruster_id} not found",
        )
    return updated


@router.delete("/{thruster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_thruster(thruster_id: UUID) -> None:
    """Delete a thruster."""
    if not delete_thruster(thruster_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thruster {thruster_id} not found",
        )
