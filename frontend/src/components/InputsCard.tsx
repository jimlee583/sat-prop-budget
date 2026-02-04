import type { LaunchOption } from '../types';
import { Card } from './Card';
import './InputsCard.css';

interface InputsCardProps {
  dryMass: number;
  setDryMass: (mass: number) => void;
  launchOptions: LaunchOption[];
  selectedLaunchOption: string;
  onLaunchOptionChange: (id: string) => void;
  hydrazineTankCapacity: number;
  setHydrazineTankCapacity: (capacity: number) => void;
  oxidizerTankCapacity: number;
  setOxidizerTankCapacity: (capacity: number) => void;
  xenonTankCapacity: number;
  setXenonTankCapacity: (capacity: number) => void;
}

export function InputsCard({
  dryMass,
  setDryMass,
  launchOptions,
  selectedLaunchOption,
  onLaunchOptionChange,
  hydrazineTankCapacity,
  setHydrazineTankCapacity,
  oxidizerTankCapacity,
  setOxidizerTankCapacity,
  xenonTankCapacity,
  setXenonTankCapacity,
}: InputsCardProps) {
  const selectedOption = launchOptions.find((o) => o.id === selectedLaunchOption);

  return (
    <Card title="Mission Parameters">
      <div className="inputs-form">
        <div className="form-group">
          <label htmlFor="dry-mass">Satellite Dry Mass (kg)</label>
          <input
            id="dry-mass"
            type="number"
            value={dryMass}
            onChange={(e) => setDryMass(Number(e.target.value))}
            min={1}
            max={50000}
            step={10}
          />
          <span className="form-hint">Mass without propellant</span>
        </div>

        <div className="form-group">
          <label htmlFor="launch-option">Launch Vehicle / Injection</label>
          <select
            id="launch-option"
            value={selectedLaunchOption}
            onChange={(e) => onLaunchOptionChange(e.target.value)}
          >
            {launchOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.name}
              </option>
            ))}
          </select>
          {selectedOption && (
            <div className="launch-details">
              <div className="detail-row">
                <span className="detail-label">Vehicle:</span>
                <span className="detail-value">{selectedOption.vehicle}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Payload to GTO:</span>
                <span className="detail-value text-mono">
                  {selectedOption.delivered_mass_kg.toLocaleString()} kg
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">ΔV to GEO:</span>
                <span className="detail-value text-mono">
                  {selectedOption.dv_remaining_to_geo_mps.toLocaleString()} m/s
                </span>
              </div>
              {selectedOption.notes && (
                <div className="detail-notes">{selectedOption.notes}</div>
              )}
            </div>
          )}
        </div>

        <div className="form-group">
          <label>Tank Capacities</label>
          <div className="tank-inputs">
            <div className="tank-input">
              <label htmlFor="hydrazine-tank">Hydrazine Tank (kg)</label>
              <input
                id="hydrazine-tank"
                type="number"
                value={hydrazineTankCapacity}
                onChange={(e) => setHydrazineTankCapacity(Number(e.target.value))}
                min={1}
                max={100000}
                step={100}
              />
            </div>
            <div className="tank-input">
              <label htmlFor="oxidizer-tank">Oxidizer Tank (kg)</label>
              <input
                id="oxidizer-tank"
                type="number"
                value={oxidizerTankCapacity}
                onChange={(e) => setOxidizerTankCapacity(Number(e.target.value))}
                min={1}
                max={100000}
                step={100}
              />
            </div>
            <div className="tank-input">
              <label htmlFor="xenon-tank">Xenon Tank (kg)</label>
              <input
                id="xenon-tank"
                type="number"
                value={xenonTankCapacity}
                onChange={(e) => setXenonTankCapacity(Number(e.target.value))}
                min={1}
                max={100000}
                step={10}
              />
            </div>
          </div>
          <span className="form-hint">Monoprop + biprop fuel use Hydrazine tank</span>
        </div>
      </div>
    </Card>
  );
}
