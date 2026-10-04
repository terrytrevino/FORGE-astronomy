# FORGE Astronomy

**FORGE = Field Observation, Retrieval, Generation, and Evaluation**

FORGE is a coordinate-driven astronomy platform for discovering archival observations, generating reproducible analysis products, and evaluating evidence across multiple physical regimes.

FORGE began as an Orion molecular-cloud workflow in the NASA Fornax environment and has expanded into a web-accessible, multi-archive research platform with portable storage, persistent targets, morphology analysis, spectroscopy discovery, and multi-wavelength data retrieval.

> **See something interesting → locate it → ask what has observed it → generate evidence.**

## Current status

**FORGE Web v0.5 is under active development.**

The project currently includes:

- a public GitHub repository
- a Streamlit web front end
- persistent target handling
- suggested target generation
- archive discovery
- SDSS + 2MASS multi-band visualization
- MAST discovery / preview development
- ALMA archive discovery
- portable local or S3-compatible storage
- reproducible JSON / CSV analysis outputs

The science engine and front end are intentionally separated so that NASA Fornax is one supported environment rather than the only way to use FORGE.

## What FORGE does

A FORGE study can begin with one sky position:

```text
RA / Dec
   ↓
Saved / suggested target selection
   ↓
Archive discovery
   ↓
Retrieve available observations
   ↓
Generate aligned science products
   ↓
Evaluate morphology / spectra / physical context
   ↓
Save results to local or object storage
   ↓
Export reproducible figures, tables, and provenance
```

## FORGE Web

The current Streamlit interface provides:

### Target handling

- saved / reference target dropdown
- new target RA / Dec entry
- persistent target library
- uploaded candidate CSV support
- known Orion reference targets

### Suggested targets

FORGE can currently generate two kinds of suggestions:

- **Nearby compact stars** — ranked from 2MASS point-source data
- **Morphology regions** — high-gradient structures identified from the local 2MASS K field

Suggested coordinates can be downloaded as CSV files and promoted into the analysis workflow.

### Archive Discovery

FORGE currently queries:

- **MAST**
  - JWST
  - HST
  - HLA
  - HLSP
  - other MAST-hosted observations
- **SDSS spectroscopy**
- **IRSA**
  - 2MASS PSC
  - AllWISE
- **ALMA**

The discovery stage intentionally returns a compact manifest before large files are downloaded.

A major design goal is that **spectroscopy should always be checked when a target is searched**.

### Multi-band analysis

The current web interface retrieves and displays:

- SDSS optical imagery
- 2MASS J
- 2MASS H
- 2MASS Ks

FORGE also includes a morphology-region mode that measures local azimuthal background asymmetry.

## Storage architecture

FORGE is designed so that analysis is not tied to one computer or one cloud.

Current storage backends:

- local application storage
- S3-compatible object storage

The long-term model is:

```text
FORGE Web
   |
   +-- AWS S3
   +-- S3-compatible object storage
   +-- Fornax object storage
   +-- future: Google Cloud Storage
   +-- future: Azure Blob Storage
```

Credentials are not stored in the repository or entered directly into the public interface. Production credentials should be supplied through the hosting platform's secure secret-management system.

Typical stored project structure:

```text
forge/
└── orion/
    └── targets/
        └── target_01/
            ├── sdss.jpg
            ├── 2mass_J.png
            ├── 2mass_H.png
            ├── 2mass_K.png
            ├── analysis.json
            └── archive_manifest.json
```

## Current science modules

- **Catalog / target handling**
- **Persistent target library**
- **Suggested target discovery**
- **Morphology**
- **Radial / azimuthal structure analysis**
- **Contrast**
- **Overlays**
- **Metrics**
- **Molecular-line analysis**
- **Spectral extraction**
- **Archive discovery**
- **Portable storage**
- **Streamlit web interface**
- **Jupyter / Fornax dashboard**

## Demonstration science cases

### Orion A

Three APOGEE-selected Orion targets were used to develop and validate the point-source and local-environment workflow.

| Target | RA (deg) | Dec (deg) | Purpose |
|---|---:|---:|---|
| target_01 | 83.806016 | -5.394502 | Orion candidate / structured environment |
| target_02 | 83.833500 | -5.427083 | Orion comparison |
| target_03 | 83.809458 | -5.406833 | Orion comparison |

The workflow now includes:

- SDSS optical imaging
- 2MASS J / H / Ks
- aperture photometry
- catalog colors
- local background asymmetry
- archive discovery
- candidate generation

### OMC-2/3

A comparison field was used to extend the morphology workflow into molecular-cloud structure and molecular-line analysis.

### M45 / Merope

An independent reflection-nebula validation showed wavelength-dependent asymmetry that persisted under progressively larger stellar masks.

### WASP-39 b

A prestaged exoplanet branch demonstrates host-star abundance context alongside JWST atmospheric detections.

## Data sources used or being integrated

- SDSS
- 2MASS
- WISE / AllWISE
- DSS2
- Gaia
- MAST
- HST
- JWST
- HLA
- HLSP
- ALMA
- CARMA–NRO Orion Survey
- NASA Exoplanet Archive

Planned archive expansion includes NRAO / VLA / VLASS / GBT / VLBA and additional spectroscopy sources.

Large archival science products are **not stored in this repository**. FORGE records provenance and retrieves or references source data from their originating archives.

## Repository structure

Current direction:

```text
FORGE-astronomy/
├── webapp/         # Streamlit front end
├── forge/          # reusable science engine (planned consolidation)
├── examples/       # example workflows and target definitions
├── tests/          # reproducibility / regression tests
├── docs/           # methods, architecture, provenance
├── README.md
└── CITATION.cff
```

The goal is to keep the science engine separate from the user interface so future web, desktop, Jupyter, and packaged-app clients can call the same FORGE Core.

## Running the web app locally

From the repository root:

```bash
pip install -r webapp/requirements.txt
streamlit run webapp/app.py
```

## Streamlit Community Cloud deployment

The current deployment configuration is:

```text
Repository: terrytrevino/FORGE-astronomy
Branch:     main
Main file:  webapp/app.py
```

If the Streamlit deployment is configured as public, users can access the app directly through its `.streamlit.app` URL without using NASA Fornax.

## Reproducibility

FORGE aims to preserve:

- sky coordinates
- target definitions
- candidate-selection provenance
- archive / telescope provenance
- exact input products
- analysis parameters
- CSV / JSON summaries
- figures
- software version information
- storage project paths

The goal is not merely to produce an attractive image or plot, but to make the path from coordinates to evidence auditable.

## Development

**FORGE was developed by D. Terry Trevino and Vivian Hom.**

The project has used ChatGPT (OpenAI) for coding assistance, debugging, workflow design, analysis support, documentation, and presentation drafting. Scientific decisions, interpretation, validation, and authorship remain with the human investigators.

## Public repository

The source repository is currently public:

`terrytrevino/FORGE-astronomy`

FORGE remains under active research and software development. APIs, file layouts, analysis methods, and the web interface may change while the first stable public release is prepared.

## Citation

A formal software citation and DOI will be added with the first tagged public release.

## License

A software license will be selected before the first stable public release.
