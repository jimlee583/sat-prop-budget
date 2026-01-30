"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.data import init_default_thrusters
from app.main import app


@pytest.fixture
def client():
    """Create test client with initialized data."""
    init_default_thrusters()
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestLaunchOptionsEndpoint:
    """Tests for launch options endpoints."""

    def test_list_launch_options(self, client):
        """Test listing all launch options."""
        response = client.get("/api/launch-options")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # At least Falcon 9, H-IIA/H3, Ariane 6

        # Verify structure
        option = data[0]
        assert "id" in option
        assert "name" in option
        assert "vehicle" in option
        assert "delivered_mass_kg" in option
        assert "dv_remaining_to_geo_mps" in option


class TestThrustersEndpoint:
    """Tests for thruster management endpoints."""

    def test_list_thrusters(self, client):
        """Test listing all thrusters."""
        response = client.get("/api/thrusters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have default thrusters
        assert len(data) >= 2

    def test_create_mono_thruster(self, client):
        """Test creating a mono-propellant thruster."""
        thruster_data = {
            "name": "Test Mono Thruster",
            "thruster_type": "chemical_mono",
            "isp_s": 230.0,
        }
        response = client.post("/api/thrusters", json=thruster_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Mono Thruster"
        assert data["isp_s"] == 230.0
        assert data["thruster_type"] == "chemical_mono"
        assert "id" in data

    def test_create_biprop_thruster(self, client):
        """Test creating a bi-propellant thruster."""
        thruster_data = {
            "name": "Test Biprop Thruster",
            "thruster_type": "chemical_biprop",
            "isp_s": 315.0,
            "mixture_ratio_ox_to_fuel": 1.6,
        }
        response = client.post("/api/thrusters", json=thruster_data)
        assert response.status_code == 201
        data = response.json()
        assert data["thruster_type"] == "chemical_biprop"
        assert data["mixture_ratio_ox_to_fuel"] == 1.6

    def test_create_biprop_without_mr_fails(self, client):
        """Creating biprop without mixture ratio should fail."""
        thruster_data = {
            "name": "Bad Biprop",
            "thruster_type": "chemical_biprop",
            "isp_s": 315.0,
        }
        response = client.post("/api/thrusters", json=thruster_data)
        assert response.status_code == 422

    def test_update_thruster(self, client):
        """Test updating a thruster."""
        # First create a thruster
        create_response = client.post(
            "/api/thrusters",
            json={"name": "To Update", "thruster_type": "chemical_mono", "isp_s": 200.0},
        )
        thruster_id = create_response.json()["id"]

        # Update it
        update_response = client.put(
            f"/api/thrusters/{thruster_id}",
            json={"name": "Updated Name", "isp_s": 225.0},
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "Updated Name"
        assert data["isp_s"] == 225.0

    def test_delete_thruster(self, client):
        """Test deleting a thruster."""
        # Create a thruster
        create_response = client.post(
            "/api/thrusters",
            json={"name": "To Delete", "thruster_type": "chemical_mono", "isp_s": 200.0},
        )
        thruster_id = create_response.json()["id"]

        # Delete it
        delete_response = client.delete(f"/api/thrusters/{thruster_id}")
        assert delete_response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/thrusters/{thruster_id}")
        assert get_response.status_code == 404


class TestComputeEndpoint:
    """Tests for propellant budget computation endpoint."""

    def test_compute_basic(self, client):
        """Test basic computation."""
        # Get a thruster ID
        thrusters = client.get("/api/thrusters").json()
        mono_thruster = next(t for t in thrusters if t["thruster_type"] == "chemical_mono")

        request_data = {
            "dry_mass_kg": 1000.0,
            "launch_option_id": "falcon9-gto-3500",
            "maneuvers": [
                {
                    "name": "orbit_transfer",
                    "maneuver_type": "orbit_transfer",
                    "delta_v_mps": 1800.0,
                    "thruster_id": mono_thruster["id"],
                    "occurrences": 1,
                }
            ],
        }

        response = client.post("/api/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert data["dry_mass_kg"] == 1000.0
        assert data["total_delta_v_mps"] == 1800.0
        assert data["total_propellant_kg"] > 0
        assert "feasible" in data
        assert "mass_margin_kg" in data
        assert len(data["maneuvers"]) == 1

    def test_compute_with_biprop(self, client):
        """Test computation with bipropellant thruster."""
        thrusters = client.get("/api/thrusters").json()
        biprop_thruster = next(t for t in thrusters if t["thruster_type"] == "chemical_biprop")

        request_data = {
            "dry_mass_kg": 1500.0,
            "launch_option_id": "falcon9-gto-5500",
            "maneuvers": [
                {
                    "name": "transfer",
                    "maneuver_type": "orbit_transfer",
                    "delta_v_mps": 1500.0,
                    "thruster_id": biprop_thruster["id"],
                    "occurrences": 1,
                }
            ],
        }

        response = client.post("/api/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should have biprop split
        maneuver = data["maneuvers"][0]
        assert maneuver["ox_kg"] is not None
        assert maneuver["fuel_kg"] is not None
        assert pytest.approx(maneuver["ox_kg"] + maneuver["fuel_kg"], rel=1e-6) == maneuver[
            "propellant_kg"
        ]

    def test_compute_infeasible(self, client):
        """Test computation that exceeds launch capability."""
        thrusters = client.get("/api/thrusters").json()
        mono_thruster = next(t for t in thrusters if t["thruster_type"] == "chemical_mono")

        # Use very heavy satellite that won't fit
        request_data = {
            "dry_mass_kg": 5000.0,
            "launch_option_id": "falcon9-gto-3500",  # Only 3500 kg capability
            "maneuvers": [
                {
                    "name": "transfer",
                    "maneuver_type": "orbit_transfer",
                    "delta_v_mps": 1800.0,
                    "thruster_id": mono_thruster["id"],
                    "occurrences": 1,
                }
            ],
        }

        response = client.post("/api/compute", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert data["feasible"] is False
        assert data["mass_margin_kg"] < 0

    def test_compute_invalid_thruster(self, client):
        """Test computation with invalid thruster ID."""
        request_data = {
            "dry_mass_kg": 1000.0,
            "launch_option_id": "falcon9-gto-3500",
            "maneuvers": [
                {
                    "name": "test",
                    "delta_v_mps": 100.0,
                    "thruster_id": "00000000-0000-0000-0000-000000000000",
                    "occurrences": 1,
                }
            ],
        }

        response = client.post("/api/compute", json=request_data)
        assert response.status_code == 404

    def test_compute_invalid_launch_option(self, client):
        """Test computation with invalid launch option."""
        thrusters = client.get("/api/thrusters").json()
        thruster = thrusters[0]

        request_data = {
            "dry_mass_kg": 1000.0,
            "launch_option_id": "nonexistent-option",
            "maneuvers": [
                {
                    "name": "test",
                    "delta_v_mps": 100.0,
                    "thruster_id": thruster["id"],
                    "occurrences": 1,
                }
            ],
        }

        response = client.post("/api/compute", json=request_data)
        assert response.status_code == 404
