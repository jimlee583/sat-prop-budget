import type {
  ComputeRequest,
  ComputeResponse,
  HealthResponse,
  LaunchOption,
  Thruster,
  ThrusterCreate,
} from './types';

const API_BASE = '/api';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

/** Health check */
export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`);
  return handleResponse<HealthResponse>(response);
}

/** Get all launch options */
export async function getLaunchOptions(): Promise<LaunchOption[]> {
  const response = await fetch(`${API_BASE}/launch-options`);
  return handleResponse<LaunchOption[]>(response);
}

/** Get all thrusters */
export async function getThrusters(): Promise<Thruster[]> {
  const response = await fetch(`${API_BASE}/thrusters`);
  return handleResponse<Thruster[]>(response);
}

/** Create a new thruster */
export async function createThruster(data: ThrusterCreate): Promise<Thruster> {
  const response = await fetch(`${API_BASE}/thrusters`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<Thruster>(response);
}

/** Update a thruster */
export async function updateThruster(
  id: string,
  data: Partial<ThrusterCreate>
): Promise<Thruster> {
  const response = await fetch(`${API_BASE}/thrusters/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<Thruster>(response);
}

/** Delete a thruster */
export async function deleteThruster(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/thrusters/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok && response.status !== 204) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
}

/** Compute propellant budget */
export async function computeBudget(data: ComputeRequest): Promise<ComputeResponse> {
  const response = await fetch(`${API_BASE}/compute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<ComputeResponse>(response);
}
