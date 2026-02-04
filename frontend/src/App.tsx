import { useCallback, useEffect, useState } from 'react';
import * as api from './api';
import type {
  ComputeResponse,
  LaunchOption,
  ManeuverInput,
  ManeuverType,
  Thruster,
} from './types';
import { Card } from './components/Card';
import { InputsCard } from './components/InputsCard';
import { ThrustersManager } from './components/ThrustersManager';
import { ManeuversTable } from './components/ManeuversTable';
import { ResultsCard } from './components/ResultsCard';
import './App.css';

function generateId(): string {
  return Math.random().toString(36).substring(2, 11);
}

function App() {
  // Data from API
  const [launchOptions, setLaunchOptions] = useState<LaunchOption[]>([]);
  const [thrusters, setThrusters] = useState<Thruster[]>([]);

  // User inputs
  const [dryMass, setDryMass] = useState(2000);
  const [selectedLaunchOption, setSelectedLaunchOption] = useState('');
  const [maneuvers, setManeuvers] = useState<ManeuverInput[]>([]);
  const [hydrazineTankCapacity, setHydrazineTankCapacity] = useState(2000);
  const [oxidizerTankCapacity, setOxidizerTankCapacity] = useState(1500);
  const [xenonTankCapacity, setXenonTankCapacity] = useState(500);

  // Computation results
  const [results, setResults] = useState<ComputeResponse | null>(null);
  const [computing, setComputing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Loading state
  const [loading, setLoading] = useState(true);

  // Load initial data
  useEffect(() => {
    async function loadData() {
      try {
        const [options, thrusterList] = await Promise.all([
          api.getLaunchOptions(),
          api.getThrusters(),
        ]);
        setLaunchOptions(options);
        setThrusters(thrusterList);

        // Set defaults
        if (options.length > 0) {
          setSelectedLaunchOption(options[0].id);
        }

        // Create default maneuvers if thrusters exist
        if (thrusterList.length > 0) {
          const bipropThruster = thrusterList.find(
            (t) => t.thruster_type === 'chemical_biprop'
          );
          const monoThruster = thrusterList.find(
            (t) => t.thruster_type === 'chemical_mono'
          );

          const selectedOption = options[0];
          const defaultManeuvers: ManeuverInput[] = [];

          // Orbit transfer using biprop (or mono if no biprop)
          const transferThruster = bipropThruster || monoThruster;
          if (transferThruster) {
            defaultManeuvers.push({
              id: generateId(),
              name: 'GTO to GEO Transfer',
              maneuver_type: 'orbit_transfer',
              delta_v_mps: selectedOption?.dv_remaining_to_geo_mps || 1800,
              thruster_id: transferThruster.id,
              occurrences: 1,
              thruster_efficiency: 1,
            });
          }

          // NSSK using mono
          if (monoThruster) {
            defaultManeuvers.push({
              id: generateId(),
              name: 'North-South Station Keeping',
              maneuver_type: 'nssk',
              delta_v_mps: 50,
              thruster_id: monoThruster.id,
              occurrences: 15,
              thruster_efficiency: 1,
            });

            defaultManeuvers.push({
              id: generateId(),
              name: 'East-West Station Keeping',
              maneuver_type: 'ewsk',
              delta_v_mps: 2,
              thruster_id: monoThruster.id,
              occurrences: 15,
              thruster_efficiency: 1,
            });

            defaultManeuvers.push({
              id: generateId(),
              name: 'End of Life Disposal',
              maneuver_type: 'disposal',
              delta_v_mps: 11,
              thruster_id: monoThruster.id,
              occurrences: 1,
              thruster_efficiency: 1,
            });
          }

          setManeuvers(defaultManeuvers);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Reload thrusters
  const reloadThrusters = useCallback(async () => {
    try {
      const thrusterList = await api.getThrusters();
      setThrusters(thrusterList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reload thrusters');
    }
  }, []);

  // Handle launch option change - update orbit transfer delta-V
  const handleLaunchOptionChange = useCallback(
    (optionId: string) => {
      setSelectedLaunchOption(optionId);
      const option = launchOptions.find((o) => o.id === optionId);
      if (option) {
        // Update orbit transfer maneuver delta-V to match new launch option
        setManeuvers((prev) =>
          prev.map((m) =>
            m.maneuver_type === 'orbit_transfer'
              ? { ...m, delta_v_mps: option.dv_remaining_to_geo_mps }
              : m
          )
        );
      }
    },
    [launchOptions]
  );

  // Compute budget
  const computeBudget = useCallback(async () => {
    if (!selectedLaunchOption || maneuvers.length === 0) {
      setError('Please select a launch option and add at least one maneuver');
      return;
    }

    setComputing(true);
    setError(null);

    try {
      const result = await api.computeBudget({
        dry_mass_kg: dryMass,
        launch_option_id: selectedLaunchOption,
        maneuvers: maneuvers.map(({ name, maneuver_type, delta_v_mps, thruster_id, occurrences, thruster_efficiency }) => ({
          name,
          maneuver_type,
          delta_v_mps,
          thruster_id,
          occurrences,
          thruster_efficiency,
        })),
        hydrazine_tank_capacity_kg: hydrazineTankCapacity,
        oxidizer_tank_capacity_kg: oxidizerTankCapacity,
        xenon_tank_capacity_kg: xenonTankCapacity,
      });
      setResults(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Computation failed');
      setResults(null);
    } finally {
      setComputing(false);
    }
  }, [dryMass, selectedLaunchOption, maneuvers, hydrazineTankCapacity, oxidizerTankCapacity, xenonTankCapacity]);

  // Maneuver management
  const addManeuver = useCallback(() => {
    const defaultThruster = thrusters[0];
    if (!defaultThruster) return;

    setManeuvers((prev) => [
      ...prev,
      {
        id: generateId(),
        name: 'New Maneuver',
        maneuver_type: 'custom' as ManeuverType,
        delta_v_mps: 100,
        thruster_id: defaultThruster.id,
        occurrences: 1,
        thruster_efficiency: 1,
      },
    ]);
  }, [thrusters]);

  const updateManeuver = useCallback(
    (id: string, updates: Partial<ManeuverInput>) => {
      setManeuvers((prev) =>
        prev.map((m) => (m.id === id ? { ...m, ...updates } : m))
      );
    },
    []
  );

  const deleteManeuver = useCallback((id: string) => {
    setManeuvers((prev) => prev.filter((m) => m.id !== id));
  }, []);

  const moveManeuver = useCallback((id: string, direction: 'up' | 'down') => {
    setManeuvers((prev) => {
      const index = prev.findIndex((m) => m.id === id);
      if (index === -1) return prev;

      const newIndex = direction === 'up' ? index - 1 : index + 1;
      if (newIndex < 0 || newIndex >= prev.length) return prev;

      const newManeuvers = [...prev];
      [newManeuvers[index], newManeuvers[newIndex]] = [
        newManeuvers[newIndex],
        newManeuvers[index],
      ];
      return newManeuvers;
    });
  }, []);

  if (loading) {
    return (
      <div className="app">
        <header className="app-header">
          <h1>Satellite Propellant Budget Calculator</h1>
        </header>
        <main className="app-main">
          <div className="loading">Loading...</div>
        </main>
      </div>
    );
  }

  const selectedOption = launchOptions.find((o) => o.id === selectedLaunchOption);

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            <img src="/satellite.svg" alt="" className="header-icon" />
            <h1>Satellite Propellant Budget Calculator</h1>
          </div>
          <p className="header-subtitle">
            Calculate propellant requirements for mission maneuvers using the rocket equation
          </p>
        </div>
      </header>

      <main className="app-main">
        <div className="app-grid">
          <div className="left-column">
            <InputsCard
              dryMass={dryMass}
              setDryMass={setDryMass}
              launchOptions={launchOptions}
              selectedLaunchOption={selectedLaunchOption}
              onLaunchOptionChange={handleLaunchOptionChange}
              hydrazineTankCapacity={hydrazineTankCapacity}
              setHydrazineTankCapacity={setHydrazineTankCapacity}
              oxidizerTankCapacity={oxidizerTankCapacity}
              setOxidizerTankCapacity={setOxidizerTankCapacity}
              xenonTankCapacity={xenonTankCapacity}
              setXenonTankCapacity={setXenonTankCapacity}
            />

            <ThrustersManager
              thrusters={thrusters}
              onThrustersChange={reloadThrusters}
            />
          </div>

          <div className="right-column">
            <ManeuversTable
              maneuvers={maneuvers}
              thrusters={thrusters}
              onAdd={addManeuver}
              onUpdate={updateManeuver}
              onDelete={deleteManeuver}
              onMove={moveManeuver}
            />

            <Card className="compute-card">
              <div className="compute-actions">
                <button
                  className="btn-primary compute-button"
                  onClick={computeBudget}
                  disabled={computing || maneuvers.length === 0}
                >
                  {computing ? 'Computing...' : 'Compute Propellant Budget'}
                </button>
                {selectedOption && (
                  <div className="launch-info">
                    <span className="text-muted">Selected: </span>
                    <span>{selectedOption.name}</span>
                    <span className="text-muted"> • </span>
                    <span className="text-mono">
                      {selectedOption.delivered_mass_kg.toLocaleString()} kg capacity
                    </span>
                  </div>
                )}
              </div>
            </Card>

            {error && (
              <Card className="error-card">
                <div className="error-message">{error}</div>
              </Card>
            )}

            {results && <ResultsCard results={results} />}
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>
          Propellant calculations use the Tsiolkovsky rocket equation with sequential mass depletion.
          Launch vehicle data are editable placeholders for demonstration purposes.
        </p>
      </footer>
    </div>
  );
}

export default App;
