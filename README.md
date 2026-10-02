# lh2-psv-tno-risk

Research record and lightweight post-processing tools for the manuscript
**“Conditional Risk Analysis Linking Self Pressurization and Pressure Relief
Venting in a Liquid Hydrogen Storage Tank.”**

The repository links four calculation stages:

1. heat ingress and self-pressurization of a horizontal LH2 tank;
2. binary PSV opening, closing, and time-dependent vent release;
3. depressurization flash state and vent-outlet thermal state; and
4. TNO-aligned jet-fire and atmospheric-dispersion routing indicators.

The public package contains the reported results, plotting scripts, figures,
and small audit functions. It does not redistribute facility drawings,
proprietary equipment records, or the complete internal TNO calculation
system. The values are therefore a citable research record and a transparent
post-processing reference, not a design-certified PSV sizing tool.

## Install

The published package is available from [PyPI](https://pypi.org/project/lh2-psv-tno-risk/).

```bash
pip install lh2-psv-tno-risk
```

## Use

```python
from lh2_psv_tno_risk import (
    classify_dispersion_route,
    conditional_risk_area,
    flash_equivalent_mass,
    load_published_results,
)

print(classify_dispersion_route(1.019))
print(flash_equivalent_mass(2141.3, 0.01288))
print(conditional_risk_area(2.320, 0.053))
print(load_published_results()["headline"])
```

The command-line summary is available as:

```bash
lh2-psv-tno-risk
```

## Reproduce the figures

The `paper/data` directory stores the machine-readable result ledgers used by
the manuscript. Install the figure dependencies and run:

```bash
pip install -e ".[figures,test]"
python scripts/plot_parameter_comparisons.py
python scripts/summarize_lh2_phase_dynamics.py
pytest
```

The scripts regenerate the five manuscript figures from the saved result
ledgers. Re-running the upstream tank and internal TNO solvers requires the
qualified source models used by the study and is outside this public archive.

## Scope of the reported risk metric

The conditional risk-area proxy integrates location-dependent fatality
probability over a horizontal plane after multiplying by a selected
direct-ignition probability. It excludes annual initiating-event frequency,
weather frequency, and occupancy. It must not be interpreted as annual
individual risk.

## Citation

Use `CITATION.cff`. The archived software record is available at
[https://doi.org/10.5281/zenodo.23105207](https://doi.org/10.5281/zenodo.23105207).

## Acknowledgement

This work was supported by the Ministry of Climate, Energy and Environment
(MCEE) and the Korea Institute of Energy Technology Evaluation and Planning
(KETEP) under project No. RS-2025-02311196.

## License

MIT for the code and original metadata in this repository. Third-party models
and source publications retain their own terms.
