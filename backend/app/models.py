"""Pydantic models for the Satellite Propellant Budget Calculator."""

from enum import Enum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ThrusterType(str, Enum):
    """Thruster propellant type."""

    CHEMICAL_MONO = "chemical_mono"
    CHEMICAL_BIPROP = "chemical_biprop"
    ELECTRIC_XENON = "electric_xenon"


class ManeuverType(str, Enum):
    """Standard maneuver types."""

    ORBIT_TRANSFER = "orbit_transfer"
    NSSK = "nssk"
    EWSK = "ewsk"
    DISPOSAL = "disposal"
    CUSTOM = "custom"


# --- Thruster Models ---


class ThrusterBase(BaseModel):
    """Base thruster model."""

    name: Annotated[str, Field(min_length=1, max_length=100)]
    thruster_type: ThrusterType
    isp_s: Annotated[float, Field(gt=0, le=5000, description="Specific impulse in seconds")]
    mixture_ratio_ox_to_fuel: Annotated[
        float | None, Field(gt=0, le=10, description="Oxidizer to fuel ratio (biprop only)")
    ] = None


class ThrusterCreate(ThrusterBase):
    """Model for creating a thruster."""

    pass


class ThrusterUpdate(BaseModel):
    """Model for updating a thruster."""

    name: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    thruster_type: ThrusterType | None = None
    isp_s: Annotated[float | None, Field(gt=0, le=5000)] = None
    mixture_ratio_ox_to_fuel: Annotated[float | None, Field(gt=0, le=10)] = None


class Thruster(ThrusterBase):
    """Thruster with ID."""

    id: UUID = Field(default_factory=uuid4)


# --- Launch Option Models ---


class LaunchOption(BaseModel):
    """Launch vehicle injection option."""

    id: str
    name: str
    vehicle: str
    delivered_mass_kg: Annotated[float, Field(gt=0, description="Payload to transfer orbit (kg)")]
    dv_remaining_to_geo_mps: Annotated[
        float, Field(ge=0, description="Delta-V remaining to reach GEO (m/s)")
    ]
    notes: str | None = None


# --- Maneuver Models ---


class ManeuverInput(BaseModel):
    """Input maneuver for computation."""

    name: Annotated[str, Field(min_length=1, max_length=100)]
    maneuver_type: ManeuverType = ManeuverType.CUSTOM
    delta_v_mps: Annotated[float, Field(ge=0, description="Delta-V in m/s")]
    thruster_id: UUID
    occurrences: Annotated[int, Field(ge=1, le=10000, description="Number of occurrences")] = 1
    thruster_efficiency: Annotated[
        float, Field(ge=0, le=1, description="Thruster efficiency factor (0-1)")
    ] = 1.0


class ManeuverResult(BaseModel):
    """Computed result for a single maneuver."""

    name: str
    maneuver_type: ManeuverType
    delta_v_mps: float
    occurrences: int
    total_delta_v_mps: float
    thruster: Thruster
    propellant_kg: float
    ox_kg: float | None = None
    fuel_kg: float | None = None
    xenon_kg: float | None = None
    m_before_kg: float
    m_after_kg: float


# --- Compute Request/Response ---


class ComputeRequest(BaseModel):
    """Request body for propellant budget computation."""

    dry_mass_kg: Annotated[float, Field(gt=0, le=50000, description="Satellite dry mass (kg)")]
    launch_option_id: str
    maneuvers: Annotated[list[ManeuverInput], Field(min_length=1)]


class ComputeResponse(BaseModel):
    """Response from propellant budget computation."""

    initial_mass_kg: float
    dry_mass_kg: float
    total_propellant_kg: float
    total_delta_v_mps: float
    feasible: bool
    mass_margin_kg: float
    launch_option: LaunchOption
    maneuvers: list[ManeuverResult]


# --- Health Check ---


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
