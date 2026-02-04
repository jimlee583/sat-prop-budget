"""Propellant budget computation endpoint."""

from fastapi import APIRouter, HTTPException, status

from app.data import get_launch_option, get_thruster
from app.models import (
    ComputeRequest,
    ComputeResponse,
    ManeuverResult,
    ThrusterType,
)
from app.services.prop_budget import (
    ManeuverSpec,
    check_feasibility,
    solve_propellant_budget,
)

router = APIRouter(tags=["compute"])


@router.post("/compute", response_model=ComputeResponse)
async def compute_propellant_budget(request: ComputeRequest) -> ComputeResponse:
    """Compute propellant budget for a mission.

    Calculates total propellant required, per-maneuver breakdown,
    and feasibility against the selected launch option.
    """
    # Validate launch option
    launch_option = get_launch_option(request.launch_option_id)
    if not launch_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Launch option '{request.launch_option_id}' not found",
        )

    # Validate thrusters and build maneuver specs
    maneuver_specs: list[ManeuverSpec] = []
    thruster_map: dict[str, object] = {}

    for maneuver in request.maneuvers:
        thruster = get_thruster(maneuver.thruster_id)
        if not thruster:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thruster '{maneuver.thruster_id}' not found",
            )

        thruster_map[str(maneuver.thruster_id)] = thruster

        is_biprop = thruster.thruster_type == ThrusterType.CHEMICAL_BIPROP
        is_xenon = thruster.thruster_type == ThrusterType.ELECTRIC_XENON
        effective_isp = thruster.isp_s * maneuver.thruster_efficiency
        maneuver_specs.append(
            ManeuverSpec(
                name=maneuver.name,
                delta_v_mps=maneuver.delta_v_mps,
                isp_s=effective_isp,
                occurrences=maneuver.occurrences,
                is_biprop=is_biprop,
                mixture_ratio_ox_to_fuel=thruster.mixture_ratio_ox_to_fuel if is_biprop else None,
                is_xenon=is_xenon,
            )
        )

    # Solve propellant budget
    try:
        result = solve_propellant_budget(
            dry_mass_kg=request.dry_mass_kg,
            maneuvers=maneuver_specs,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e

    if not result.converged:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Propellant budget calculation did not converge",
        )

    # Check feasibility
    mass_feasible, mass_margin = check_feasibility(
        result.initial_mass_kg, launch_option.delivered_mass_kg
    )

    # Calculate tank totals
    # Hydrazine = monoprop propellant + biprop fuel
    # Oxidizer = biprop oxidizer only
    # Xenon = electric xenon propellant
    hydrazine_total_kg = 0.0
    oxidizer_total_kg = 0.0
    xenon_total_kg = 0.0

    for i, maneuver in enumerate(request.maneuvers):
        calc_result = result.maneuver_results[i]
        thruster = get_thruster(maneuver.thruster_id)
        assert thruster is not None

        if thruster.thruster_type == ThrusterType.CHEMICAL_MONO:
            hydrazine_total_kg += calc_result.propellant_kg
        elif thruster.thruster_type == ThrusterType.CHEMICAL_BIPROP:
            hydrazine_total_kg += calc_result.fuel_kg or 0.0
            oxidizer_total_kg += calc_result.ox_kg or 0.0
        elif thruster.thruster_type == ThrusterType.ELECTRIC_XENON:
            xenon_total_kg += calc_result.xenon_kg or 0.0

    # Check tank constraints
    tank_constraints_violated: list[str] = []
    if hydrazine_total_kg > request.hydrazine_tank_capacity_kg:
        tank_constraints_violated.append("hydrazine")
    if oxidizer_total_kg > request.oxidizer_tank_capacity_kg:
        tank_constraints_violated.append("oxidizer")
    if xenon_total_kg > request.xenon_tank_capacity_kg:
        tank_constraints_violated.append("xenon")

    feasible = mass_feasible and len(tank_constraints_violated) == 0

    # Build response
    maneuver_results: list[ManeuverResult] = []
    for i, maneuver in enumerate(request.maneuvers):
        calc_result = result.maneuver_results[i]
        thruster = get_thruster(maneuver.thruster_id)
        assert thruster is not None  # Already validated above

        maneuver_results.append(
            ManeuverResult(
                name=maneuver.name,
                maneuver_type=maneuver.maneuver_type,
                delta_v_mps=calc_result.delta_v_mps,
                occurrences=calc_result.occurrences,
                total_delta_v_mps=calc_result.total_delta_v_mps,
                thruster=thruster,
                propellant_kg=calc_result.propellant_kg,
                ox_kg=calc_result.ox_kg,
                fuel_kg=calc_result.fuel_kg,
                xenon_kg=calc_result.xenon_kg,
                m_before_kg=calc_result.m_before_kg,
                m_after_kg=calc_result.m_after_kg,
            )
        )

    return ComputeResponse(
        initial_mass_kg=result.initial_mass_kg,
        dry_mass_kg=result.dry_mass_kg,
        total_propellant_kg=result.total_propellant_kg,
        total_delta_v_mps=result.total_delta_v_mps,
        feasible=feasible,
        mass_margin_kg=mass_margin,
        launch_option=launch_option,
        maneuvers=maneuver_results,
        hydrazine_total_kg=hydrazine_total_kg,
        oxidizer_total_kg=oxidizer_total_kg,
        xenon_total_kg=xenon_total_kg,
        hydrazine_tank_capacity_kg=request.hydrazine_tank_capacity_kg,
        oxidizer_tank_capacity_kg=request.oxidizer_tank_capacity_kg,
        xenon_tank_capacity_kg=request.xenon_tank_capacity_kg,
        tank_constraints_violated=tank_constraints_violated,
    )
