"""In-memory data storage and launch option presets."""

from uuid import UUID

from app.models import LaunchOption, Thruster, ThrusterType

# --- Launch Vehicle Presets (editable placeholders) ---

LAUNCH_OPTIONS: dict[str, LaunchOption] = {
    "falcon9-gto-3500": LaunchOption(
        id="falcon9-gto-3500",
        name="Falcon 9 GTO - 3,500 kg",
        vehicle="SpaceX Falcon 9",
        delivered_mass_kg=3500.0,
        dv_remaining_to_geo_mps=1800.0,
        notes="Editable placeholder - standard GTO injection",
    ),
    "falcon9-gto-5500": LaunchOption(
        id="falcon9-gto-5500",
        name="Falcon 9 GTO - 5,500 kg",
        vehicle="SpaceX Falcon 9",
        delivered_mass_kg=5500.0,
        dv_remaining_to_geo_mps=1500.0,
        notes="Editable placeholder - supersync GTO",
    ),
    "h2a-gto": LaunchOption(
        id="h2a-gto",
        name="H-IIA 204 GTO",
        vehicle="MHI H-IIA",
        delivered_mass_kg=4100.0,
        dv_remaining_to_geo_mps=1800.0,
        notes="Editable placeholder - standard GTO",
    ),
    "h3-gto": LaunchOption(
        id="h3-gto",
        name="H3-24L GTO",
        vehicle="MHI H3",
        delivered_mass_kg=6500.0,
        dv_remaining_to_geo_mps=1500.0,
        notes="Editable placeholder - high performance config",
    ),
    "ariane6-gto-62": LaunchOption(
        id="ariane6-gto-62",
        name="Ariane 6 A62 GTO",
        vehicle="Ariane 6",
        delivered_mass_kg=4500.0,
        dv_remaining_to_geo_mps=1800.0,
        notes="Editable placeholder - 2 booster config",
    ),
    "ariane6-gto-64": LaunchOption(
        id="ariane6-gto-64",
        name="Ariane 6 A64 GTO",
        vehicle="Ariane 6",
        delivered_mass_kg=11500.0,
        dv_remaining_to_geo_mps=1500.0,
        notes="Editable placeholder - 4 booster config",
    ),
}


# --- In-Memory Thruster Storage ---

_thrusters: dict[UUID, Thruster] = {}


def get_all_thrusters() -> list[Thruster]:
    """Get all thrusters."""
    return list(_thrusters.values())


def get_thruster(thruster_id: UUID) -> Thruster | None:
    """Get a thruster by ID."""
    return _thrusters.get(thruster_id)


def create_thruster(thruster: Thruster) -> Thruster:
    """Create a new thruster."""
    _thrusters[thruster.id] = thruster
    return thruster


def update_thruster(thruster_id: UUID, updates: dict[str, object]) -> Thruster | None:
    """Update a thruster."""
    if thruster_id not in _thrusters:
        return None
    thruster = _thrusters[thruster_id]
    updated_data = thruster.model_dump()
    updated_data.update({k: v for k, v in updates.items() if v is not None})
    updated_thruster = Thruster(**updated_data)
    _thrusters[thruster_id] = updated_thruster
    return updated_thruster


def delete_thruster(thruster_id: UUID) -> bool:
    """Delete a thruster."""
    if thruster_id in _thrusters:
        del _thrusters[thruster_id]
        return True
    return False


def get_launch_option(option_id: str) -> LaunchOption | None:
    """Get a launch option by ID."""
    return LAUNCH_OPTIONS.get(option_id)


def get_all_launch_options() -> list[LaunchOption]:
    """Get all launch options."""
    return list(LAUNCH_OPTIONS.values())


# --- Initialize default thrusters ---


def init_default_thrusters() -> None:
    """Initialize default thrusters if none exist."""
    if not _thrusters:
        # REA mono-propellant thruster
        rea_mono = Thruster(
            name="REA 22N (Mono)",
            thruster_type=ThrusterType.CHEMICAL_MONO,
            isp_s=220.0,
            mixture_ratio_ox_to_fuel=None,
        )
        _thrusters[rea_mono.id] = rea_mono

        # LAE bi-propellant thruster
        lae_biprop = Thruster(
            name="LAE 490N (Biprop)",
            thruster_type=ThrusterType.CHEMICAL_BIPROP,
            isp_s=320.0,
            mixture_ratio_ox_to_fuel=0.8,
        )
        _thrusters[lae_biprop.id] = lae_biprop
