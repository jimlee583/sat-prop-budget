/** Thruster propellant types */
export type ThrusterType = 'chemical_mono' | 'chemical_biprop' | 'electric_xenon';

/** Standard maneuver types */
export type ManeuverType = 'orbit_transfer' | 'nssk' | 'ewsk' | 'disposal' | 'custom';

/** Thruster definition */
export interface Thruster {
  id: string;
  name: string;
  thruster_type: ThrusterType;
  isp_s: number;
  mixture_ratio_ox_to_fuel: number | null;
  thrust_n: number | null;
}

/** Launch vehicle injection option */
export interface LaunchOption {
  id: string;
  name: string;
  vehicle: string;
  delivered_mass_kg: number;
  dv_remaining_to_geo_mps: number;
  notes: string | null;
}

/** Input maneuver for computation */
export interface ManeuverInput {
  id: string; // Local ID for UI tracking
  name: string;
  maneuver_type: ManeuverType;
  delta_v_mps: number;
  thruster_id: string;
  occurrences: number;
  thruster_efficiency: number;
}

/** Computed result for a single maneuver */
export interface ManeuverResult {
  name: string;
  maneuver_type: ManeuverType;
  delta_v_mps: number;
  occurrences: number;
  total_delta_v_mps: number;
  thruster: Thruster;
  thruster_efficiency: number;
  propellant_kg: number;
  ox_kg: number | null;
  fuel_kg: number | null;
  xenon_kg: number | null;
  m_before_kg: number;
  m_after_kg: number;
}

/** Request body for propellant budget computation */
export interface ComputeRequest {
  dry_mass_kg: number;
  launch_option_id: string;
  maneuvers: Omit<ManeuverInput, 'id'>[];
  hydrazine_tank_capacity_kg: number;
  oxidizer_tank_capacity_kg: number;
  xenon_tank_capacity_kg: number;
}

/** Response from propellant budget computation */
export interface ComputeResponse {
  initial_mass_kg: number;
  dry_mass_kg: number;
  total_propellant_kg: number;
  total_delta_v_mps: number;
  feasible: boolean;
  mass_margin_kg: number;
  launch_option: LaunchOption;
  maneuvers: ManeuverResult[];
  hydrazine_total_kg: number;
  oxidizer_total_kg: number;
  xenon_total_kg: number;
  hydrazine_tank_capacity_kg: number;
  oxidizer_tank_capacity_kg: number;
  xenon_tank_capacity_kg: number;
  tank_constraints_violated: string[];
}

/** Thruster creation data */
export interface ThrusterCreate {
  name: string;
  thruster_type: ThrusterType;
  isp_s: number;
  mixture_ratio_ox_to_fuel?: number | null;
  thrust_n?: number | null;
}

/** Health check response */
export interface HealthResponse {
  status: string;
  version: string;
}
