"""Tests for propellant budget calculation service."""

import math

import pytest

from app.services.prop_budget import (
    G0,
    ManeuverSpec,
    check_feasibility,
    compute_biprop_split,
    compute_mass_ratio,
    compute_propellant_for_maneuver,
    solve_propellant_budget,
)


class TestComputeMassRatio:
    """Tests for compute_mass_ratio function."""

    def test_zero_delta_v_returns_one(self):
        """Zero delta-V should result in mass ratio of 1."""
        assert compute_mass_ratio(0.0, 300.0) == 1.0

    def test_known_values(self):
        """Test with known values from rocket equation."""
        # dV = g0 * Isp * ln(MR) => MR = exp(dV / (g0 * Isp))
        isp = 300.0
        delta_v = G0 * isp * math.log(2.0)  # Should give MR = 2
        result = compute_mass_ratio(delta_v, isp)
        assert pytest.approx(result, rel=1e-6) == 2.0

    def test_negative_isp_raises(self):
        """Negative Isp should raise ValueError."""
        with pytest.raises(ValueError, match="Isp must be positive"):
            compute_mass_ratio(100.0, -300.0)

    def test_negative_delta_v_raises(self):
        """Negative delta-V should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            compute_mass_ratio(-100.0, 300.0)


class TestComputePropellantForManeuver:
    """Tests for compute_propellant_for_maneuver function."""

    def test_single_maneuver_sanity_check(self):
        """Test single maneuver propellant calculation - sanity check."""
        # A satellite with 1000 kg before maneuver
        # Isp = 300 s, delta-V = 500 m/s
        m_before = 1000.0
        delta_v = 500.0
        isp = 300.0

        prop_kg, m_after = compute_propellant_for_maneuver(m_before, delta_v, isp)

        # Verify using rocket equation directly
        expected_m_after = m_before / math.exp(delta_v / (G0 * isp))
        expected_prop = m_before - expected_m_after

        assert pytest.approx(prop_kg, rel=1e-6) == expected_prop
        assert pytest.approx(m_after, rel=1e-6) == expected_m_after

        # Mass conservation check
        assert pytest.approx(m_before, rel=1e-6) == m_after + prop_kg

    def test_zero_delta_v(self):
        """Zero delta-V should consume no propellant."""
        m_before = 1000.0
        prop_kg, m_after = compute_propellant_for_maneuver(m_before, 0.0, 300.0)

        assert prop_kg == 0.0
        assert m_after == m_before

    def test_high_delta_v_high_isp(self):
        """Test with high delta-V and high Isp (like electric propulsion)."""
        m_before = 2000.0
        delta_v = 2000.0
        isp = 1500.0  # Ion thruster

        prop_kg, m_after = compute_propellant_for_maneuver(m_before, delta_v, isp)

        # Should use relatively little propellant due to high Isp
        assert prop_kg < 300.0  # Much less than low-Isp would require
        assert m_after > 0
        assert pytest.approx(m_before, rel=1e-6) == m_after + prop_kg


class TestComputeBipropSplit:
    """Tests for bipropellant split calculation."""

    def test_biprop_split_mr_1(self):
        """MR = 1.0 should give 50/50 split."""
        fuel, ox = compute_biprop_split(100.0, 1.0)
        assert pytest.approx(fuel, rel=1e-6) == 50.0
        assert pytest.approx(ox, rel=1e-6) == 50.0

    def test_biprop_split_mr_0_8(self):
        """Test typical hydrazine/NTO mixture ratio of 0.8."""
        # MR = Ox/Fuel = 0.8
        # fuel = prop / (1 + 0.8) = prop / 1.8
        # ox = prop - fuel
        prop = 180.0
        mr = 0.8
        fuel, ox = compute_biprop_split(prop, mr)

        expected_fuel = 180.0 / 1.8  # 100
        expected_ox = 180.0 - expected_fuel  # 80

        assert pytest.approx(fuel, rel=1e-6) == expected_fuel
        assert pytest.approx(ox, rel=1e-6) == expected_ox
        assert pytest.approx(fuel + ox, rel=1e-6) == prop

    def test_biprop_split_mr_2(self):
        """MR = 2.0: twice as much oxidizer as fuel."""
        prop = 300.0
        mr = 2.0
        fuel, ox = compute_biprop_split(prop, mr)

        expected_fuel = 300.0 / 3.0  # 100
        expected_ox = 300.0 - expected_fuel  # 200

        assert pytest.approx(fuel, rel=1e-6) == expected_fuel
        assert pytest.approx(ox, rel=1e-6) == expected_ox

    def test_biprop_split_invalid_mr(self):
        """Zero or negative MR should raise."""
        with pytest.raises(ValueError, match="Mixture ratio must be positive"):
            compute_biprop_split(100.0, 0.0)
        with pytest.raises(ValueError, match="Mixture ratio must be positive"):
            compute_biprop_split(100.0, -0.5)


class TestSolvePropellantBudget:
    """Tests for solve_propellant_budget function."""

    def test_single_maneuver_mono(self):
        """Test single maneuver with mono propellant."""
        dry_mass = 1000.0
        maneuvers = [
            ManeuverSpec(
                name="orbit_transfer",
                delta_v_mps=500.0,
                isp_s=220.0,
                occurrences=1,
                is_biprop=False,
            )
        ]

        result = solve_propellant_budget(dry_mass, maneuvers)

        assert result.converged
        assert result.dry_mass_kg == dry_mass
        assert result.total_delta_v_mps == 500.0
        assert result.total_propellant_kg > 0

        # Verify mass conservation
        assert pytest.approx(result.initial_mass_kg, rel=1e-4) == (
            dry_mass + result.total_propellant_kg
        )

        # Verify final mass equals dry mass
        final_mass = result.initial_mass_kg - result.total_propellant_kg
        assert pytest.approx(final_mass, rel=1e-4) == dry_mass

    def test_multi_maneuver_changing_isp(self):
        """Test multiple maneuvers with different Isp values."""
        dry_mass = 1500.0
        maneuvers = [
            ManeuverSpec(
                name="transfer",
                delta_v_mps=1500.0,
                isp_s=320.0,  # Biprop LAE
                occurrences=1,
                is_biprop=True,
                mixture_ratio_ox_to_fuel=0.8,
            ),
            ManeuverSpec(
                name="nssk",
                delta_v_mps=50.0,
                isp_s=220.0,  # Mono REA
                occurrences=15,  # 15 years
                is_biprop=False,
            ),
            ManeuverSpec(
                name="ewsk",
                delta_v_mps=2.0,
                isp_s=220.0,
                occurrences=15,
                is_biprop=False,
            ),
            ManeuverSpec(
                name="disposal",
                delta_v_mps=10.0,
                isp_s=220.0,
                occurrences=1,
                is_biprop=False,
            ),
        ]

        result = solve_propellant_budget(dry_mass, maneuvers)

        assert result.converged
        assert len(result.maneuver_results) == 4

        # Total delta-V check
        expected_dv = 1500.0 + 50.0 * 15 + 2.0 * 15 + 10.0
        assert pytest.approx(result.total_delta_v_mps, rel=1e-6) == expected_dv

        # Verify sequential mass depletion
        prev_m_after = result.initial_mass_kg
        for mr in result.maneuver_results:
            assert pytest.approx(mr.m_before_kg, rel=1e-4) == prev_m_after
            prev_m_after = mr.m_after_kg

        # Final mass should be dry mass
        assert pytest.approx(result.maneuver_results[-1].m_after_kg, rel=1e-2) == dry_mass

        # First maneuver should have biprop split
        assert result.maneuver_results[0].ox_kg is not None
        assert result.maneuver_results[0].fuel_kg is not None
        assert pytest.approx(
            result.maneuver_results[0].ox_kg + result.maneuver_results[0].fuel_kg, rel=1e-6
        ) == result.maneuver_results[0].propellant_kg

        # Other maneuvers should not have biprop split
        for mr in result.maneuver_results[1:]:
            assert mr.ox_kg is None
            assert mr.fuel_kg is None

    def test_zero_delta_v_maneuver(self):
        """Test with zero delta-V maneuver."""
        dry_mass = 1000.0
        maneuvers = [
            ManeuverSpec(
                name="null_maneuver",
                delta_v_mps=0.0,
                isp_s=300.0,
                occurrences=1,
            )
        ]

        result = solve_propellant_budget(dry_mass, maneuvers)

        assert result.converged
        assert result.total_propellant_kg == 0.0
        assert result.initial_mass_kg == dry_mass

    def test_invalid_dry_mass_raises(self):
        """Zero or negative dry mass should raise."""
        with pytest.raises(ValueError, match="Dry mass must be positive"):
            solve_propellant_budget(0.0, [ManeuverSpec("test", 100.0, 300.0)])

    def test_empty_maneuvers_raises(self):
        """Empty maneuver list should raise."""
        with pytest.raises(ValueError, match="At least one maneuver"):
            solve_propellant_budget(1000.0, [])

    def test_large_delta_v_converges(self):
        """Test that solver converges for large delta-V requirements."""
        dry_mass = 500.0
        maneuvers = [
            ManeuverSpec(
                name="huge_transfer",
                delta_v_mps=5000.0,
                isp_s=320.0,
                occurrences=1,
            )
        ]

        result = solve_propellant_budget(dry_mass, maneuvers)

        assert result.converged
        # For such large delta-V, propellant >> dry mass
        assert result.total_propellant_kg > dry_mass * 3


class TestCheckFeasibility:
    """Tests for feasibility checking."""

    def test_feasible_with_margin(self):
        """Test feasible case with positive margin."""
        initial_mass = 3000.0
        capability = 3500.0

        feasible, margin = check_feasibility(initial_mass, capability)

        assert feasible is True
        assert margin == 500.0

    def test_infeasible_negative_margin(self):
        """Test infeasible case with negative margin."""
        initial_mass = 4000.0
        capability = 3500.0

        feasible, margin = check_feasibility(initial_mass, capability)

        assert feasible is False
        assert margin == -500.0

    def test_exactly_at_limit(self):
        """Test case where mass exactly equals capability."""
        initial_mass = 3500.0
        capability = 3500.0

        feasible, margin = check_feasibility(initial_mass, capability)

        assert feasible is True
        assert margin == 0.0


class TestIntegrationScenarios:
    """Integration tests for realistic mission scenarios."""

    def test_typical_geo_mission(self):
        """Test a typical GEO satellite mission profile."""
        # Typical GEO comms satellite scenario
        dry_mass = 2000.0  # 2 ton dry mass

        maneuvers = [
            # GTO to GEO transfer using LAE
            ManeuverSpec(
                name="orbit_transfer",
                delta_v_mps=1800.0,
                isp_s=320.0,
                occurrences=1,
                is_biprop=True,
                mixture_ratio_ox_to_fuel=0.8,
            ),
            # 15 years of NSSK
            ManeuverSpec(
                name="nssk",
                delta_v_mps=50.0,
                isp_s=220.0,
                occurrences=15,
                is_biprop=False,
            ),
            # 15 years of EWSK
            ManeuverSpec(
                name="ewsk",
                delta_v_mps=2.0,
                isp_s=220.0,
                occurrences=15,
                is_biprop=False,
            ),
            # End of life disposal
            ManeuverSpec(
                name="disposal",
                delta_v_mps=11.0,
                isp_s=220.0,
                occurrences=1,
                is_biprop=False,
            ),
        ]

        result = solve_propellant_budget(dry_mass, maneuvers)

        assert result.converged

        # Verify reasonable propellant mass
        # For ~2600 m/s total dV with these Isps, expect significant propellant
        assert 1500.0 < result.total_propellant_kg < 4000.0

        # Verify biprop split on transfer maneuver
        transfer = result.maneuver_results[0]
        assert transfer.ox_kg is not None
        assert transfer.fuel_kg is not None

        # Check feasibility against Falcon 9 GTO
        feasible, margin = check_feasibility(result.initial_mass_kg, 3500.0)
        # This should be close to the limit
        print(f"Initial mass: {result.initial_mass_kg:.1f} kg")
        print(f"Propellant: {result.total_propellant_kg:.1f} kg")
        print(f"Margin: {margin:.1f} kg")
