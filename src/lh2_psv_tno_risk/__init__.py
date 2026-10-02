"""Public post-processing API for the LH2-PSV-TNO research record."""

from .analysis import (
    RouteDecision,
    classify_dispersion_route,
    conditional_risk_area,
    flash_equivalent_mass,
    load_published_results,
)

__all__ = [
    "RouteDecision",
    "classify_dispersion_route",
    "conditional_risk_area",
    "flash_equivalent_mass",
    "load_published_results",
]

__version__ = "0.1.2"
