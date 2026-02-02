import { useState } from 'react';
import * as api from '../api';
import type { Thruster, ThrusterCreate, ThrusterType } from '../types';
import { Card } from './Card';
import './ThrustersManager.css';

interface ThrustersManagerProps {
  thrusters: Thruster[];
  onThrustersChange: () => void;
}

interface ThrusterFormData {
  name: string;
  thruster_type: ThrusterType;
  isp_s: string;
  mixture_ratio_ox_to_fuel: string;
}

const emptyForm: ThrusterFormData = {
  name: '',
  thruster_type: 'chemical_mono',
  isp_s: '220',
  mixture_ratio_ox_to_fuel: '0.8',
};

export function ThrustersManager({
  thrusters,
  onThrustersChange,
}: ThrustersManagerProps) {
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<ThrusterFormData>(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const resetForm = () => {
    setFormData(emptyForm);
    setShowForm(false);
    setEditingId(null);
    setError(null);
  };

  const startEdit = (thruster: Thruster) => {
    setFormData({
      name: thruster.name,
      thruster_type: thruster.thruster_type,
      isp_s: String(thruster.isp_s),
      mixture_ratio_ox_to_fuel: String(thruster.mixture_ratio_ox_to_fuel ?? 0.8),
    });
    setEditingId(thruster.id);
    setShowForm(true);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaving(true);

    try {
      const data: ThrusterCreate = {
        name: formData.name.trim(),
        thruster_type: formData.thruster_type,
        isp_s: parseFloat(formData.isp_s),
        mixture_ratio_ox_to_fuel:
          formData.thruster_type === 'chemical_biprop'
            ? parseFloat(formData.mixture_ratio_ox_to_fuel)
            : null,
      };

      if (editingId) {
        await api.updateThruster(editingId, data);
      } else {
        await api.createThruster(data);
      }

      onThrustersChange();
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save thruster');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this thruster?')) return;

    try {
      await api.deleteThruster(id);
      onThrustersChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete thruster');
    }
  };

  return (
    <Card title="Thrusters">
      <div className="thrusters-list">
        {thrusters.map((thruster) => (
          <div key={thruster.id} className="thruster-item">
            <div className="thruster-info">
              <div className="thruster-name">{thruster.name}</div>
              <div className="thruster-details">
                <span className="thruster-type">
                  {thruster.thruster_type === 'chemical_mono'
                    ? 'Mono'
                    : thruster.thruster_type === 'chemical_biprop'
                      ? 'Biprop'
                      : 'Xenon'}
                </span>
                <span className="thruster-isp text-mono">
                  Isp: {thruster.isp_s}s
                </span>
                {thruster.mixture_ratio_ox_to_fuel !== null && (
                  <span className="thruster-mr text-mono">
                    MR: {thruster.mixture_ratio_ox_to_fuel}
                  </span>
                )}
              </div>
            </div>
            <div className="thruster-actions">
              <button
                className="btn-secondary btn-sm"
                onClick={() => startEdit(thruster)}
              >
                Edit
              </button>
              <button
                className="btn-danger btn-sm"
                onClick={() => handleDelete(thruster.id)}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {!showForm && (
        <button
          className="btn-primary add-thruster-btn"
          onClick={() => setShowForm(true)}
        >
          + Add Thruster
        </button>
      )}

      {showForm && (
        <form className="thruster-form" onSubmit={handleSubmit}>
          <h3 className="form-title">
            {editingId ? 'Edit Thruster' : 'New Thruster'}
          </h3>

          {error && <div className="form-error">{error}</div>}

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="thruster-name">Name</label>
              <input
                id="thruster-name"
                type="text"
                value={formData.name}
                onChange={(e) =>
                  setFormData((f) => ({ ...f, name: e.target.value }))
                }
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="thruster-type">Type</label>
              <select
                id="thruster-type"
                value={formData.thruster_type}
                onChange={(e) =>
                  setFormData((f) => ({
                    ...f,
                    thruster_type: e.target.value as ThrusterType,
                  }))
                }
              >
                <option value="chemical_mono">Monopropellant</option>
                <option value="chemical_biprop">Bipropellant</option>
                <option value="electric_xenon">Electric (Xenon)</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="thruster-isp">Isp (s)</label>
              <input
                id="thruster-isp"
                type="number"
                value={formData.isp_s}
                onChange={(e) =>
                  setFormData((f) => ({ ...f, isp_s: e.target.value }))
                }
                min={50}
                max={5000}
                step={1}
                required
              />
            </div>
          </div>

          {formData.thruster_type === 'chemical_biprop' && (
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="thruster-mr">Mixture Ratio (Ox/Fuel)</label>
                <input
                  id="thruster-mr"
                  type="number"
                  value={formData.mixture_ratio_ox_to_fuel}
                  onChange={(e) =>
                    setFormData((f) => ({
                      ...f,
                      mixture_ratio_ox_to_fuel: e.target.value,
                    }))
                  }
                  min={0.1}
                  max={10}
                  step={0.1}
                  required
                />
                <span className="form-hint">e.g., 0.8 for N2O4/N2H4</span>
              </div>
            </div>
          )}

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={resetForm}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? 'Saving...' : editingId ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      )}
    </Card>
  );
}
