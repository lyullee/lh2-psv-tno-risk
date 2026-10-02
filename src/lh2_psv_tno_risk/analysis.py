"""Small, auditable calculations used when reading the published ledgers."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from importlib.resources import files
from typing import Literal


RouteName = Literal["dense_gas", "buoyant_jet", "uncovered"]


@dataclass(frozen=True)
class RouteDecision:
    """Atmospheric-dispersion route selected from the H2-to-air density ratio."""

    route: RouteName
    density_ratio: float
    explanation: str


def _finite_nonnegative(value: float, name: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")
    return numeric


def classify_dispersion_route(
    density_ratio: float,
    *,
    dense_threshold: float = 1.0,
    jet_threshold: float = 0.6,
) -> RouteDecision:
    """Return the route used by the manuscript's current TNO wrapper.

    A ratio at or above 1.0 selects the SLABX dense-gas route. A ratio at or
    below 0.6 selects the Schefer buoyant-jet route. The interval between the
    thresholds is intentionally returned as ``uncovered`` rather than zero
    risk.
    """

    ratio = _finite_nonnegative(density_ratio, "density_ratio")
    dense = _finite_nonnegative(dense_threshold, "dense_threshold")
    jet = _finite_nonnegative(jet_threshold, "jet_threshold")
    if jet >= dense:
        raise ValueError("jet_threshold must be smaller than dense_threshold")
    if ratio >= dense:
        return RouteDecision("dense_gas", ratio, "density ratio is at or above the dense-gas threshold")
    if ratio <= jet:
        return RouteDecision("buoyant_jet", ratio, "density ratio is at or below the buoyant-jet threshold")
    return RouteDecision("uncovered", ratio, "no dispersion model is connected in this density-ratio interval")


def flash_equivalent_mass(lower_cv_mass_kg: float, vapor_quality: float) -> float:
    """Convert lower-control-volume equilibrium vapor quality to mass.

    This is an equilibrium inventory proxy, not a resolved bubble-separation
    rate or measured vent flow.
    """

    mass = _finite_nonnegative(lower_cv_mass_kg, "lower_cv_mass_kg")
    quality = float(vapor_quality)
    if not math.isfinite(quality) or not 0.0 <= quality <= 1.0:
        raise ValueError("vapor_quality must be between 0 and 1")
    return mass * quality


def conditional_risk_area(area_given_fire_m2: float, ignition_probability: float) -> float:
    """Apply direct-ignition probability to an area conditional on jet fire."""

    area = _finite_nonnegative(area_given_fire_m2, "area_given_fire_m2")
    probability = float(ignition_probability)
    if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise ValueError("ignition_probability must be between 0 and 1")
    return area * probability


def load_published_results() -> dict:
    """Load the compact machine-readable record shipped with the package."""

    resource = files("lh2_psv_tno_risk").joinpath("data/published_results.json")
    return json.loads(resource.read_text(encoding="utf-8"))
