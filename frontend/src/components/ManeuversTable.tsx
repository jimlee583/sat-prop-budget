import type { ManeuverInput, ManeuverType, Thruster } from '../types';
import { Card } from './Card';
import './ManeuversTable.css';

interface ManeuversTableProps {
  maneuvers: ManeuverInput[];
  thrusters: Thruster[];
  onAdd: () => void;
  onUpdate: (id: string, updates: Partial<ManeuverInput>) => void;
  onDelete: (id: string) => void;
  onMove: (id: string, direction: 'up' | 'down') => void;
}

const MANEUVER_TYPES: { value: ManeuverType; label: string }[] = [
  { value: 'orbit_transfer', label: 'Orbit Transfer' },
  { value: 'nssk', label: 'NSSK' },
  { value: 'ewsk', label: 'EWSK' },
  { value: 'disposal', label: 'Disposal' },
  { value: 'custom', label: 'Custom' },
];

export function ManeuversTable({
  maneuvers,
  thrusters,
  onAdd,
  onUpdate,
  onDelete,
  onMove,
}: ManeuversTableProps) {
  const totalDeltaV = maneuvers.reduce(
    (sum, m) => sum + m.delta_v_mps * m.occurrences,
    0
  );

  return (
    <Card title="Mission Maneuvers">
      <div className="maneuvers-table-container">
        <table className="maneuvers-table">
          <thead>
            <tr>
              <th style={{ width: '40px' }}></th>
              <th>Name</th>
              <th>Type</th>
              <th>ΔV (m/s)</th>
              <th>Count</th>
              <th>Total ΔV</th>
              <th>Thruster</th>
              <th>Efficiency</th>
              <th style={{ width: '60px' }}></th>
            </tr>
          </thead>
          <tbody>
            {maneuvers.map((maneuver, index) => (
              <tr key={maneuver.id}>
                <td className="reorder-cell">
                  <div className="reorder-buttons">
                    <button
                      className="btn-icon btn-secondary"
                      onClick={() => onMove(maneuver.id, 'up')}
                      disabled={index === 0}
                      title="Move up"
                    >
                      ▲
                    </button>
                    <button
                      className="btn-icon btn-secondary"
                      onClick={() => onMove(maneuver.id, 'down')}
                      disabled={index === maneuvers.length - 1}
                      title="Move down"
                    >
                      ▼
                    </button>
                  </div>
                </td>
                <td>
                  <input
                    type="text"
                    value={maneuver.name}
                    onChange={(e) =>
                      onUpdate(maneuver.id, { name: e.target.value })
                    }
                    className="cell-input"
                  />
                </td>
                <td>
                  <select
                    value={maneuver.maneuver_type}
                    onChange={(e) =>
                      onUpdate(maneuver.id, {
                        maneuver_type: e.target.value as ManeuverType,
                      })
                    }
                    className="cell-select"
                  >
                    {MANEUVER_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    type="number"
                    value={maneuver.delta_v_mps}
                    onChange={(e) =>
                      onUpdate(maneuver.id, {
                        delta_v_mps: parseFloat(e.target.value) || 0,
                      })
                    }
                    min={0}
                    step={1}
                    className="cell-input cell-input-number"
                  />
                </td>
                <td>
                  <input
                    type="number"
                    value={maneuver.occurrences}
                    onChange={(e) =>
                      onUpdate(maneuver.id, {
                        occurrences: parseInt(e.target.value) || 1,
                      })
                    }
                    min={1}
                    step={1}
                    className="cell-input cell-input-number cell-input-small"
                  />
                </td>
                <td className="text-mono">
                  {(maneuver.delta_v_mps * maneuver.occurrences).toFixed(1)}
                </td>
                <td>
                  <select
                    value={maneuver.thruster_id}
                    onChange={(e) =>
                      onUpdate(maneuver.id, { thruster_id: e.target.value })
                    }
                    className="cell-select"
                  >
                    {thrusters.map((thruster) => (
                      <option key={thruster.id} value={thruster.id}>
                        {thruster.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    type="number"
                    value={maneuver.thruster_efficiency}
                    onChange={(e) =>
                      onUpdate(maneuver.id, {
                        thruster_efficiency: parseFloat(e.target.value) || 0,
                      })
                    }
                    min={0}
                    max={1}
                    step={0.01}
                    className="cell-input cell-input-number cell-input-small"
                  />
                </td>
                <td>
                  <button
                    className="btn-danger btn-sm"
                    onClick={() => onDelete(maneuver.id)}
                    title="Delete maneuver"
                  >
                    ✕
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={5} className="total-label">
                Total Delta-V:
              </td>
              <td className="total-value text-mono">{totalDeltaV.toFixed(1)}</td>
              <td colSpan={3}></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <button className="btn-primary add-maneuver-btn" onClick={onAdd}>
        + Add Maneuver
      </button>
    </Card>
  );
}
