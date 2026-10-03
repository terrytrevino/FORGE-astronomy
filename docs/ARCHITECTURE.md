# FORGE Architecture

FORGE separates the reusable science engine from the user interface.

## Intended layout

```text
FORGE-astronomy/
├── forge/
│   ├── catalog.py
│   ├── acquisition.py
│   ├── morphology.py
│   ├── contrast.py
│   ├── overlay.py
│   ├── metrics.py
│   ├── molecular.py
│   ├── spectra.py
│   ├── fitting.py
│   ├── exoplanets.py
│   ├── reporting.py
│   └── provenance.py
├── app/
│   └── dashboard.py
├── examples/
├── tests/
└── docs/
```

## Design principle

A target is defined primarily by sky position plus optional identifiers. Analysis modules should consume target records and data products without depending on a particular front end.

This allows:

- Jupyter / NASA Fornax operation
- future web interfaces
- desktop or packaged applications
- scripted batch processing
- reproducible science runs

## Coordinate-first workflow

1. Define RA / Dec.
2. Check archive coverage.
3. Retrieve or locate available observations.
4. Align products through WCS where appropriate.
5. Run analysis modules compatible with the available data.
6. Save figures, tables, parameters, and provenance.
7. Evaluate the evidence and explicitly record limitations.

## Current implementation status

Implemented in the research codebase:

- catalog handling
- radial / azimuthal morphology
- contrast mapping
- morphology overlays
- structural metrics
- molecular WCS cutouts
- molecular summary products and line ratios
- low-memory PPV spectral extraction
- exoplanet host-star / atmosphere demonstration

Still being consolidated for the public package:

- generalized acquisition
- generalized spectral fitting
- reporting
- tests
- packaging
- dashboard separation from legacy scripts

## Data policy

Large survey products and cubes should remain in their authoritative archives and are not committed to Git. FORGE should preserve source identifiers, retrieval information, checksums where practical, and processing metadata.
