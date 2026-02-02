import type { ComputeResponse } from '../types';
import { Card } from './Card';
import './ResultsCard.css';

interface ResultsCardProps {
  results: ComputeResponse;
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
  } = results;

  // Calculate totals for biprop and xenon
  const totalOx = maneuvers.reduce((sum, m) => sum + (m.ox_kg ?? 0), 0);
  const totalFuel = maneuvers.reduce((sum, m) => sum + (m.fuel_kg ?? 0), 0);
  const totalXenon = maneuvers.reduce((sum, m) => sum + (m.xenon_kg ?? 0), 0);
  const hasBiprop = maneuvers.some((m) => m.ox_kg !== null);
  const hasXenon = maneuvers.some((m) => m.xenon_kg !== null);

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
          {!feasible && (
            <span className="margin-warning">
              {' '}
              (exceeds {launch_option.name} capacity of{' '}
              {launch_option.delivered_mass_kg.toLocaleString()} kg)
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

      {/* Biprop Totals */}
      {hasBiprop && (
        <div className="biprop-summary">
          <h4>Bipropellant Totals</h4>
          <div className="biprop-row">
            <span>Total Oxidizer:</span>
            <span className="text-mono">{totalOx.toFixed(1)} kg</span>
          </div>
          <div className="biprop-row">
            <span>Total Fuel:</span>
            <span className="text-mono">{totalFuel.toFixed(1)} kg</span>
          </div>
        </div>
      )}

      {/* Xenon Totals */}
      {hasXenon && (
        <div className="biprop-summary">
          <h4>Xenon Totals</h4>
          <div className="biprop-row">
            <span>Total Xenon:</span>
            <span className="text-mono">{totalXenon.toFixed(1)} kg</span>
          </div>
        </div>
      )}

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
    </Card>
  );
}
