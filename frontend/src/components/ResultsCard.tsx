import { useState } from 'react';
import type { ComputeResponse, ManeuverResult } from '../types';
import { Card } from './Card';
import './ResultsCard.css';

interface ResultsCardProps {
  results: ComputeResponse;
}

/**
 * Format burn duration as hours:minutes or minutes:seconds
 */
function formatDuration(seconds: number): string {
  if (seconds >= 3600) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.round((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
  const minutes = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${minutes}m ${secs}s`;
}

/**
 * Calculate burn duration for a single HCT maneuver
 */
function calcBurnDuration(maneuverResult: ManeuverResult, frequencyDays: number): number | null {
  const thruster = maneuverResult.thruster;

  // Need thrust value to calculate
  if (thruster.thrust_n === null) {
    return null;
  }

  // yearly_delta_v = delta_v_mps (per-occurrence value, which represents yearly delta-V)
  const yearlyDeltaV = maneuverResult.delta_v_mps;
  const perBurnDeltaV = yearlyDeltaV * (frequencyDays / 365);

  // Apply efficiency to thrust (same factor used for Isp in propellant calc)
  const effectiveThrust = thruster.thrust_n * maneuverResult.thruster_efficiency;

  // Use m_before_kg as representative mass for the burn
  const massKg = maneuverResult.m_before_kg;

  const acceleration = effectiveThrust / massKg;  // m/s²
  const durationSeconds = perBurnDeltaV / acceleration;
  return durationSeconds;
}

export function ResultsCard({ results }: ResultsCardProps) {
  const {
    feasible,
    mass_margin_kg,
    initial_mass_kg,
    dry_mass_kg,
    total_propellant_kg,
    total_delta_v_mps,
    launch_option,
    maneuvers,
    hydrazine_total_kg,
    oxidizer_total_kg,
    xenon_total_kg,
    hydrazine_tank_capacity_kg,
    oxidizer_tank_capacity_kg,
    xenon_tank_capacity_kg,
    tank_constraints_violated,
  } = results;

  // State for HCT burn duration calculator
  const [skFrequency, setSkFrequency] = useState(7);

  // Check which propellant columns to show
  const hasBiprop = maneuvers.some((m) => m.ox_kg !== null);
  const hasXenon = maneuvers.some((m) => m.xenon_kg !== null);

  // Filter HCT/xenon maneuvers with NSSK or EWSK type and thrust data
  const hctSkManeuvers = maneuvers.filter(
    (m) =>
      m.thruster.thruster_type === 'electric_xenon' &&
      (m.maneuver_type === 'nssk' || m.maneuver_type === 'ewsk') &&
      m.thruster.thrust_n !== null
  );

  return (
    <Card title="Results" className="results-card">
      {/* Feasibility Banner */}
      <div className={`feasibility-banner ${feasible ? 'feasible' : 'infeasible'}`}>
        <div className="feasibility-status">
          {feasible ? '✓ FEASIBLE' : '✗ INFEASIBLE'}
        </div>
        <div className="feasibility-detail">
          Mass margin: {mass_margin_kg >= 0 ? '+' : ''}
          {mass_margin_kg.toFixed(1)} kg
          {!feasible && mass_margin_kg < 0 && (
            <span className="margin-warning">
              {' '}
              (exceeds {launch_option.name} capacity of{' '}
              {launch_option.delivered_mass_kg.toLocaleString()} kg)
            </span>
          )}
          {!feasible && tank_constraints_violated.length > 0 && (
            <span className="margin-warning">
              {' '}
              ({tank_constraints_violated.map(t => t.charAt(0).toUpperCase() + t.slice(1)).join(', ')} tank{tank_constraints_violated.length > 1 ? 's' : ''} exceeded)
            </span>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="results-summary">
        <div className="summary-item">
          <div className="summary-label">Initial Mass (Wet)</div>
          <div className="summary-value text-mono">
            {initial_mass_kg.toLocaleString(undefined, {
              maximumFractionDigits: 1,
            })}{' '}
            kg
          </div>
        </div>
        <div className="summary-item">
          <div className="summary-label">Dry Mass</div>
          <div className="summary-value text-mono">
            {dry_mass_kg.toLocaleString(undefined, {
              maximumFractionDigits: 1,
            })}{' '}
            kg
          </div>
        </div>
        <div className="summary-item highlight">
          <div className="summary-label">Total Propellant</div>
          <div className="summary-value text-mono">
            {total_propellant_kg.toLocaleString(undefined, {
              maximumFractionDigits: 1,
            })}{' '}
            kg
          </div>
        </div>
        <div className="summary-item">
          <div className="summary-label">Total ΔV</div>
          <div className="summary-value text-mono">
            {total_delta_v_mps.toLocaleString(undefined, {
              maximumFractionDigits: 1,
            })}{' '}
            m/s
          </div>
        </div>
      </div>

      {/* Tank Utilization */}
      <div className="tank-utilization">
        <h4>Tank Utilization</h4>
        <div className={`tank-row ${tank_constraints_violated.includes('hydrazine') ? 'exceeded' : ''}`}>
          <span className="tank-label">Hydrazine:</span>
          <span className="tank-value text-mono">
            {hydrazine_total_kg.toFixed(1)} / {hydrazine_tank_capacity_kg.toLocaleString()} kg
          </span>
          <span className="tank-percent text-mono">
            ({((hydrazine_total_kg / hydrazine_tank_capacity_kg) * 100).toFixed(1)}%)
          </span>
        </div>
        <div className={`tank-row ${tank_constraints_violated.includes('oxidizer') ? 'exceeded' : ''}`}>
          <span className="tank-label">Oxidizer:</span>
          <span className="tank-value text-mono">
            {oxidizer_total_kg.toFixed(1)} / {oxidizer_tank_capacity_kg.toLocaleString()} kg
          </span>
          <span className="tank-percent text-mono">
            ({((oxidizer_total_kg / oxidizer_tank_capacity_kg) * 100).toFixed(1)}%)
          </span>
        </div>
        <div className={`tank-row ${tank_constraints_violated.includes('xenon') ? 'exceeded' : ''}`}>
          <span className="tank-label">Xenon:</span>
          <span className="tank-value text-mono">
            {xenon_total_kg.toFixed(1)} / {xenon_tank_capacity_kg.toLocaleString()} kg
          </span>
          <span className="tank-percent text-mono">
            ({((xenon_total_kg / xenon_tank_capacity_kg) * 100).toFixed(1)}%)
          </span>
        </div>
      </div>

      {/* Per-Maneuver Breakdown */}
      <h4 className="breakdown-title">Per-Maneuver Breakdown</h4>
      <div className="breakdown-table-container">
        <table className="breakdown-table">
          <thead>
            <tr>
              <th>Maneuver</th>
              <th>Thruster</th>
              <th>ΔV (m/s)</th>
              <th>Propellant (kg)</th>
              {hasBiprop && (
                <>
                  <th>Ox (kg)</th>
                  <th>Fuel (kg)</th>
                </>
              )}
              {hasXenon && <th>Xenon (kg)</th>}
              <th>Mass Before</th>
              <th>Mass After</th>
            </tr>
          </thead>
          <tbody>
            {maneuvers.map((m, i) => (
              <tr key={i}>
                <td>
                  <div className="maneuver-name">{m.name}</div>
                  {m.occurrences > 1 && (
                    <div className="maneuver-occurrences">
                      ×{m.occurrences} @ {m.delta_v_mps} m/s each
                    </div>
                  )}
                </td>
                <td>
                  <div className="thruster-name">{m.thruster.name}</div>
                  <div className="thruster-isp">Isp: {m.thruster.isp_s}s</div>
                </td>
                <td className="text-mono text-right">{m.total_delta_v_mps.toFixed(1)}</td>
                <td className="text-mono text-right">{m.propellant_kg.toFixed(1)}</td>
                {hasBiprop && (
                  <>
                    <td className="text-mono text-right">
                      {m.ox_kg !== null ? m.ox_kg.toFixed(1) : '—'}
                    </td>
                    <td className="text-mono text-right">
                      {m.fuel_kg !== null ? m.fuel_kg.toFixed(1) : '—'}
                    </td>
                  </>
                )}
                {hasXenon && (
                  <td className="text-mono text-right">
                    {m.xenon_kg !== null ? m.xenon_kg.toFixed(1) : '—'}
                  </td>
                )}
                <td className="text-mono text-right">
                  {m.m_before_kg.toLocaleString(undefined, {
                    maximumFractionDigits: 1,
                  })}
                </td>
                <td className="text-mono text-right">
                  {m.m_after_kg.toLocaleString(undefined, {
                    maximumFractionDigits: 1,
                  })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* HCT Burn Duration Calculator - only shown for HCT NSSK/EWSK maneuvers */}
      {hctSkManeuvers.length > 0 && (
        <div className="burn-duration-calc">
          <h4>HCT Burn Duration Calculator</h4>
          <div className="frequency-input">
            <label htmlFor="sk-frequency">Station-Keeping Frequency:</label>
            <input
              id="sk-frequency"
              type="number"
              min={2}
              max={14}
              value={skFrequency}
              onChange={(e) => setSkFrequency(Math.max(2, Math.min(14, parseInt(e.target.value) || 7)))}
            />
            <span className="frequency-unit">days (2-14)</span>
          </div>
          <div className="breakdown-table-container">
            <table className="breakdown-table burn-duration-table">
              <thead>
                <tr>
                  <th>Maneuver</th>
                  <th>Yearly ΔV</th>
                  <th>Per-burn ΔV</th>
                  <th>Duration</th>
                </tr>
              </thead>
              <tbody>
                {hctSkManeuvers.map((m, i) => {
                  const yearlyDv = m.delta_v_mps;
                  const perBurnDv = yearlyDv * (skFrequency / 365);
                  const durationSec = calcBurnDuration(m, skFrequency);
                  return (
                    <tr key={i}>
                      <td>
                        <div className="maneuver-name">{m.name}</div>
                        <div className="thruster-isp">{m.thruster.name}</div>
                      </td>
                      <td className="text-mono text-right">{yearlyDv.toFixed(1)} m/s</td>
                      <td className="text-mono text-right">{perBurnDv.toFixed(2)} m/s</td>
                      <td className="text-mono text-right">
                        {durationSec !== null ? formatDuration(durationSec) : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Card>
  );
}
