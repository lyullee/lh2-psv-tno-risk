import pytest

from lh2_psv_tno_risk import (
    classify_dispersion_route,
    conditional_risk_area,
    flash_equivalent_mass,
    load_published_results,
)


def test_route_boundaries_and_uncovered_interval():
    assert classify_dispersion_route(1.019).route == "dense_gas"
    assert classify_dispersion_route(0.448).route == "buoyant_jet"
    assert classify_dispersion_route(0.765).route == "uncovered"


def test_conditional_risk_matches_reported_rounding():
    assert conditional_risk_area(0.260, 0.008) == pytest.approx(0.00208)
    assert conditional_risk_area(2.320, 0.053) == pytest.approx(0.12296)


def test_flash_mass_and_record_load():
    assert flash_equivalent_mass(2141.3, 0.01288) == pytest.approx(27.579944)
    assert load_published_results()["headline"]["tank_volume_m3"] == 56.3343


@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_vapor_quality_is_bounded(value):
    with pytest.raises(ValueError):
        flash_equivalent_mass(10.0, value)
