"""Propellant budget calculation service using the rocket equation.

This module implements sequential mass depletion calculations for satellite
maneuver planning, solving for total propellant using numerical methods.
"""

import math
from dataclasses import dataclass

# Standard gravitational acceleration (m/s²)
G0 = 9.80665


@dataclass
class ManeuverSpec:
    """Specification for a single maneuver."""

    name: str
    delta_v_mps: float
    isp_s: float
    occurrences: int = 1
    is_biprop: bool = False
    mixture_ratio_ox_to_fuel: float | None = None
    is_xenon: bool = False


@dataclass
class ManeuverCalcResult:
    """Result of propellant calculation for a single maneuver."""

    name: str
    delta_v_mps: float
    occurrences: int
    total_delta_v_mps: float
    propellant_kg: float
    m_before_kg: float
    m_after_kg: float
    ox_kg: float | None = None
    fuel_kg: float | None = None
    xenon_kg: float | None = None


@dataclass
class BudgetResult:
    """Complete propellant budget calculation result."""

    initial_mass_kg: float
    dry_mass_kg: float
    total_propellant_kg: float
    total_delta_v_mps: float
    maneuver_results: list[ManeuverCalcResult]
    converged: bool
    iterations: int


def compute_mass_ratio(delta_v_mps: float, isp_s: float) -> float:
    """Compute mass ratio from Tsiolkovsky rocket equation.

    m_before / m_after = exp(delta_v / (g0 * Isp))

    Args:
        delta_v_mps: Delta-V in m/s
        isp_s: Specific impulse in seconds

    Returns:
        Mass ratio (m_before / m_after)
    """
    if isp_s <= 0:
        raise ValueError("Isp must be positive")
    if delta_v_mps < 0:
        raise ValueError("Delta-V cannot be negative")
    if delta_v_mps == 0:
        return 1.0

    exhaust_velocity = G0 * isp_s
    return math.exp(delta_v_mps / exhaust_velocity)


def compute_propellant_for_maneuver(
    m_before_kg: float, delta_v_mps: float, isp_s: float
) -> tuple[float, float]:
    """Compute propellant mass and final mass for a single maneuver.

    Args:
        m_before_kg: Mass before maneuver (kg)
        delta_v_mps: Delta-V for maneuver (m/s)
        isp_s: Specific impulse (s)

    Returns:
        Tuple of (propellant_kg, m_after_kg)
    """
    mass_ratio = compute_mass_ratio(delta_v_mps, isp_s)
    m_after_kg = m_before_kg / mass_ratio
    propellant_kg = m_before_kg - m_after_kg
    return propellant_kg, m_after_kg


def compute_biprop_split(
    propellant_kg: float, mixture_ratio_ox_to_fuel: float
) -> tuple[float, float]:
    """Split bipropellant mass into oxidizer and fuel.

    Given mixture ratio MR = Ox/Fuel:
        fuel = prop / (1 + MR)
        ox = prop - fuel

    Args:
        propellant_kg: Total propellant mass (kg)
        mixture_ratio_ox_to_fuel: Oxidizer to fuel ratio

    Returns:
        Tuple of (fuel_kg, ox_kg)
    """
    if mixture_ratio_ox_to_fuel <= 0:
        raise ValueError("Mixture ratio must be positive")

    fuel_kg = propellant_kg / (1.0 + mixture_ratio_ox_to_fuel)
    ox_kg = propellant_kg - fuel_kg
    return fuel_kg, ox_kg


def _compute_propellant_given_initial_mass(
    initial_mass_kg: float,
    dry_mass_kg: float,
    maneuvers: list[ManeuverSpec],
) -> tuple[float, list[ManeuverCalcResult]]:
    """Compute total propellant and per-maneuver results given initial mass.

    Applies sequential mass depletion through all maneuvers.

    Args:
        initial_mass_kg: Starting wet mass (kg)
        dry_mass_kg: Satellite dry mass (kg)
        maneuvers: List of maneuver specifications

    Returns:
        Tuple of (total_propellant_kg, list of maneuver results)
    """
    m_current = initial_mass_kg
    total_propellant = 0.0
    results: list[ManeuverCalcResult] = []

    for maneuver in maneuvers:
        # Total delta-V for this maneuver type (accounting for occurrences)
        total_dv = maneuver.delta_v_mps * maneuver.occurrences
        m_before = m_current

        # Compute propellant for this maneuver
        prop_kg, m_after = compute_propellant_for_maneuver(m_current, total_dv, maneuver.isp_s)

        # Compute biprop split if applicable
        ox_kg: float | None = None
        fuel_kg: float | None = None
        xenon_kg: float | None = None
        if maneuver.is_biprop and maneuver.mixture_ratio_ox_to_fuel is not None:
            fuel_kg, ox_kg = compute_biprop_split(prop_kg, maneuver.mixture_ratio_ox_to_fuel)
        elif maneuver.is_xenon:
            xenon_kg = prop_kg

        results.append(
            ManeuverCalcResult(
                name=maneuver.name,
                delta_v_mps=maneuver.delta_v_mps,
                occurrences=maneuver.occurrences,
                total_delta_v_mps=total_dv,
                propellant_kg=prop_kg,
                m_before_kg=m_before,
                m_after_kg=m_after,
                ox_kg=ox_kg,
                fuel_kg=fuel_kg,
                xenon_kg=xenon_kg,
            )
        )

        total_propellant += prop_kg
        m_current = m_after

    return total_propellant, results


def solve_propellant_budget(
    dry_mass_kg: float,
    maneuvers: list[ManeuverSpec],
    tolerance: float = 1e-6,
    max_iterations: int = 100,
    initial_upper_bound: float = 20000.0,
) -> BudgetResult:
    """Solve for total propellant budget using bisection method.

    The problem: We need to find initial_mass = dry_mass + propellant_total,
    but propellant_total depends on initial_mass through sequential maneuvers.

    We solve f(m0) = 0 where:
        f(m0) = (m0 - dry_mass) - sum(propellant_i(m0))

    Using bisection between [dry_mass, dry_mass + upper_bound].

    Args:
        dry_mass_kg: Satellite dry mass (kg)
        maneuvers: List of maneuver specifications
        tolerance: Convergence tolerance (kg)
        max_iterations: Maximum bisection iterations
        initial_upper_bound: Initial guess for max propellant (kg)

    Returns:
        BudgetResult with converged solution
    """
    if dry_mass_kg <= 0:
        raise ValueError("Dry mass must be positive")
    if not maneuvers:
        raise ValueError("At least one maneuver is required")

    # Total delta-V for reference
    total_delta_v = sum(m.delta_v_mps * m.occurrences for m in maneuvers)

    # Handle zero delta-V case
    if total_delta_v == 0:
        _, results = _compute_propellant_given_initial_mass(dry_mass_kg, dry_mass_kg, maneuvers)
        return BudgetResult(
            initial_mass_kg=dry_mass_kg,
            dry_mass_kg=dry_mass_kg,
            total_propellant_kg=0.0,
            total_delta_v_mps=0.0,
            maneuver_results=results,
            converged=True,
            iterations=0,
        )

    def residual(m0: float) -> float:
        """Compute f(m0) = available_propellant - required_propellant."""
        available_prop = m0 - dry_mass_kg
        required_prop, _ = _compute_propellant_given_initial_mass(m0, dry_mass_kg, maneuvers)
        return available_prop - required_prop

    # Bisection bounds
    m_low = dry_mass_kg + 1e-6  # Just above dry mass
    m_high = dry_mass_kg + initial_upper_bound

    # Expand upper bound if needed
    while residual(m_high) < 0 and m_high < dry_mass_kg + 1e9:
        m_high *= 2

    # Bisection iteration
    iterations = 0
    converged = False

    for iterations in range(1, max_iterations + 1):
        m_mid = (m_low + m_high) / 2
        f_mid = residual(m_mid)

        if abs(f_mid) < tolerance:
            converged = True
            break

        if f_mid > 0:
            # Too much propellant available, reduce initial mass
            m_high = m_mid
        else:
            # Not enough propellant, increase initial mass
            m_low = m_mid

    # Final computation with converged mass
    final_m0 = (m_low + m_high) / 2
    total_propellant, maneuver_results = _compute_propellant_given_initial_mass(
        final_m0, dry_mass_kg, maneuvers
    )

    return BudgetResult(
        initial_mass_kg=final_m0,
        dry_mass_kg=dry_mass_kg,
        total_propellant_kg=total_propellant,
        total_delta_v_mps=total_delta_v,
        maneuver_results=maneuver_results,
        converged=converged,
        iterations=iterations,
    )


def check_feasibility(
    initial_mass_kg: float, delivered_mass_capability_kg: float
) -> tuple[bool, float]:
    """Check if the propellant budget is feasible for the launch option.

    Args:
        initial_mass_kg: Required initial (wet) mass (kg)
        delivered_mass_capability_kg: Launch vehicle payload capability (kg)

    Returns:
        Tuple of (is_feasible, mass_margin_kg)
        Positive margin means feasible with margin remaining.
        Negative margin means infeasible by that amount.
    """
    mass_margin = delivered_mass_capability_kg - initial_mass_kg
    is_feasible = mass_margin >= 0
    return is_feasible, mass_margin
