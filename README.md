# Satellite Propellant Budget Calculator

A full-stack application for calculating satellite propellant requirements across mission maneuvers using the Tsiolkovsky rocket equation.

## Features

- **Propellant Budget Calculation**: Uses sequential mass depletion with the rocket equation
- **Multiple Thruster Types**: Support for monopropellant and bipropellant systems
- **Launch Vehicle Presets**: Editable placeholders for Falcon 9, H-IIA/H3, Ariane 6
- **Mission Planning**: Define custom maneuver sequences (orbit transfer, NSSK, EWSK, disposal)
- **Feasibility Analysis**: Check if mission fits launch vehicle capability
- **Biprop Split**: Automatic oxidizer/fuel mass calculation based on mixture ratio

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, uv
- **Frontend**: React 18, TypeScript, Vite
- **Testing**: pytest, ruff, mypy

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Run the server
uv run uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run the dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

### Using Docker Compose (Optional)

```bash
# Start both services
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/launch-options` | List launch vehicle presets |
| GET | `/api/thrusters` | List user thrusters |
| POST | `/api/thrusters` | Create thruster |
| PUT | `/api/thrusters/{id}` | Update thruster |
| DELETE | `/api/thrusters/{id}` | Delete thruster |
| POST | `/api/compute` | Compute propellant budget |

### Example: Compute Propellant Budget

```bash
# First, get thruster IDs
curl http://localhost:8000/api/thrusters

# Then compute (replace thruster_id with actual UUID)
curl -X POST http://localhost:8000/api/compute \
  -H "Content-Type: application/json" \
  -d '{
    "dry_mass_kg": 2000,
    "launch_option_id": "falcon9-gto-3500",
    "maneuvers": [
      {
        "name": "GTO to GEO Transfer",
        "maneuver_type": "orbit_transfer",
        "delta_v_mps": 1800,
        "thruster_id": "YOUR-THRUSTER-UUID-HERE",
        "occurrences": 1
      },
      {
        "name": "NSSK",
        "maneuver_type": "nssk",
        "delta_v_mps": 50,
        "thruster_id": "YOUR-THRUSTER-UUID-HERE",
        "occurrences": 15
      }
    ]
  }'
```

## Development

### Backend

```bash
cd backend

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Type checking
uv run mypy app

# Linting
uv run ruff check app tests
uv run ruff format app tests
```

### Frontend

```bash
cd frontend

# Type checking
npm run build

# Linting
npm run lint
```

## Project Structure

```
sat-prop-budget/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── models.py            # Pydantic models
│   │   ├── data.py              # In-memory data storage
│   │   ├── routers/
│   │   │   ├── health.py
│   │   │   ├── launch_options.py
│   │   │   ├── thrusters.py
│   │   │   └── compute.py
│   │   └── services/
│   │       └── prop_budget.py   # Rocket equation calculations
│   ├── tests/
│   │   ├── test_prop_budget.py  # Unit tests for calculations
│   │   └── test_api.py          # API integration tests
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api.ts               # API client
│   │   ├── types.ts             # TypeScript types
│   │   └── components/
│   │       ├── Card.tsx
│   │       ├── InputsCard.tsx
│   │       ├── ThrustersManager.tsx
│   │       ├── ManeuversTable.tsx
│   │       └── ResultsCard.tsx
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

## Calculation Method

The propellant budget is calculated using:

1. **Rocket Equation**: For each maneuver with ΔV and Isp:
   ```
   m_after = m_before × exp(-ΔV / (g₀ × Isp))
   propellant = m_before - m_after
   ```

2. **Sequential Mass Depletion**: Maneuvers are processed in order, with each maneuver starting from the ending mass of the previous one.

3. **Bisection Solver**: Since total propellant depends on initial mass (which depends on total propellant), we solve iteratively:
   - Find m₀ such that: (m₀ - dry_mass) = Σ propellant_i(m₀)

4. **Bipropellant Split**: For biprop thrusters with mixture ratio MR = Ox/Fuel:
   ```
   fuel = propellant / (1 + MR)
   oxidizer = propellant - fuel
   ```

## Launch Vehicle Data

**Note**: The launch vehicle data are *editable placeholders* for demonstration purposes. They do not represent actual current performance values. Please update with real data for production use.

## License

MIT
