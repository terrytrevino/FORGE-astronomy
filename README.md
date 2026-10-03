# FORGE Astronomy

**FORGE = Field Observation, Retrieval, Generation, and Evaluation**

FORGE is a coordinate-driven astronomy workflow for discovering archival observations, generating reproducible analysis products, and evaluating evidence across multiple physical regimes.

FORGE began as an Orion molecular-cloud study in the NASA Fornax environment and has since expanded to support multi-wavelength morphology, molecular-line spectroscopy, external validation, and exoplanet atmosphere demonstrations.

## What FORGE does

A FORGE study can begin with a sky position:

```text
RA / Dec
   ↓
Archive coverage check
   ↓
Retrieve available observations
   ↓
Generate aligned science products
   ↓
Evaluate morphology / spectra / physical context
   ↓
Export reproducible figures, tables, and provenance
```

The central idea is simple:

> **See something interesting → locate it → ask what has observed it → generate evidence.**

## Current science modules

- **Catalog / target handling** — coordinate-driven target definitions
- **Morphology** — radial and azimuthal structure analysis
- **Contrast** — directional and spatial contrast products
- **Overlays** — morphology overlays tied to astronomical images
- **Metrics** — reusable structural metrics
- **Molecular analysis** — WCS cutouts, moments, tracer summaries, and line ratios
- **Spectra** — low-memory PPV spectral extraction
- **Exoplanets** — host-star abundance and atmospheric-species comparison
- **Dashboard** — interactive Jupyter/Fornax control surface

## Demonstration science cases

### Orion A
Three candidate fields plus an OMC-2/3 comparison field were used to develop and validate the molecular-cloud workflow with 2MASS imaging and CARMA–NRO molecular-line products.

### M45 / Merope
An independent reflection-nebula validation showed wavelength-dependent asymmetry that persisted under progressively larger stellar masks.

### WASP-39 b
A prestaged exoplanet branch demonstrates host-star abundance context alongside JWST atmospheric detections.

## Data sources currently used

FORGE has worked with public archival products from:

- 2MASS
- WISE
- DSS2
- Gaia
- CARMA–NRO Orion Survey
- NASA / ESA / CSA JWST products
- NASA Exoplanet Archive

Large archival data products are **not stored in this repository**. FORGE records provenance and retrieves or references source data from the originating archives.

## Example target table

| Target | RA (deg) | Dec (deg) | Purpose |
|---|---:|---:|---|
| target_01 | 83.806016 | -5.394502 | Orion candidate |
| target_02 | 83.833500 | -5.427083 | Orion comparison |
| target_03 | 83.809458 | -5.406833 | Orion comparison |
| omc23_field_01 | 83.854167 | -5.172778 | OMC-2/3 context field |
| m45_merope_01 | 56.588750 | 23.941110 | External morphology validation |

## Repository direction

The intended structure is:

```text
FORGE-astronomy/
├── forge/          # reusable science engine
├── app/            # dashboard / future front ends
├── examples/       # example target definitions and workflows
├── tests/          # reproducibility and regression tests
├── docs/           # architecture, data provenance, methods
├── README.md
└── pyproject.toml
```

The science engine is deliberately separated from the front end so that Jupyter/Fornax is one client rather than the only client. Future web, desktop, and packaged-app interfaces can call the same FORGE Core.

## Reproducibility

FORGE aims to preserve:

- sky coordinates and target definitions
- archive / telescope provenance
- exact input products
- analysis parameters
- generated CSV / JSON summaries
- figures
- software version information

The goal is not merely to produce an attractive image or plot, but to make the path from coordinates to evidence auditable.

## Development

**FORGE was developed by D. Terry Trevino and Vivian Hom.**

The project has used ChatGPT (OpenAI) for coding assistance, debugging, workflow design, analysis support, documentation, and presentation drafting. Scientific decisions, interpretation, validation, and authorship remain with the human investigators.

## Current status

FORGE is under active research and software development. APIs, file layouts, and methods may change while the first public release is stabilized.

## Citation

A formal software citation and DOI will be added with the first tagged public release.

## License

A software license will be selected before the first stable public release.
