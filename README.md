# FORGE Astronomy

**FORGE = Field Observation, Retrieval, Generation, and Evaluation**

FORGE is a coordinate-driven astronomy platform for discovering archival observations, retrieving multi-wavelength data, generating reproducible analysis products, and evaluating astronomical evidence across imaging, spectroscopy, morphology, historical archives, and radio datasets.

FORGE began as an Orion molecular-cloud workflow in the NASA Fornax environment and has evolved into a public web-accessible research platform.

> **See something interesting → locate it → ask what has observed it → generate evidence.**

## Current status

**FORGE Web v0.11 — public alpha**

Live application:

**https://forge-astronomy-rpjevm5zy6an8falnxcyvx.streamlit.app/**

Repository:

**terrytrevino/FORGE-astronomy**

The current public alpha supports:

- coordinate-driven target selection
- saved and reference targets
- Gaia and 2MASS nearby-star suggestions
- morphology-region suggestions
- SDSS optical and 2MASS J/H/Ks visualization
- MAST multi-mission archive discovery
- MAST preview imagery
- real MAST 1-D spectrum discovery and plotting
- SDSS spectroscopy
- real APOGEE DR17 spectrum retrieval and plotting
- IRSA / 2MASS / AllWISE discovery
- ALMA archive discovery
- NRAO radio-archive discovery with fail-fast timeout handling
- radio spectral-line triage
- DSS / historical sky-survey discovery
- Harvard DASCH exposure discovery
- local and S3-compatible project storage
- downloadable CSV / JSON analysis products
- reproducible archive and analysis provenance

FORGE remains an active research and software-development project. v0.11 is being treated as a functional checkpoint before the next feature cycle.

## Core workflow

A FORGE investigation can begin with a single coordinate:

```text
RA / Dec
   ↓
Target identity / saved target
   ↓
Archive discovery
   ↓
Suggested nearby stars and morphology regions
   ↓
Retrieve available imaging / spectra
   ↓
Analyze point source or local morphology
   ↓
Compare wavelength regimes
   ↓
Save figures, metadata, CSV / JSON, and provenance
```

The design principle is simple:

**one coordinate → many archives → reproducible evidence.**

## FORGE Web

### Target handling

The current Streamlit interface supports:

- manual target name + RA / Dec entry
- saved / reference target dropdown
- persistent target library
- uploaded candidate CSV files
- known Orion validation targets

Known Orion references include:

| Target | APOGEE ID | RA (deg) | Dec (deg) |
|---|---|---:|---:|
| target_01 | 2M05351344-0523402 | 83.806016 | -5.394502 |
| target_02 | 2M05352004-0525375 | 83.833500 | -5.427083 |
| target_03 | 2M05351427-0524246 | 83.809458 | -5.406833 |

### Suggested targets

FORGE currently produces two complementary suggestion classes.

**Nearby compact stars**
- 2MASS point-source candidates
- Gaia DR3 candidates

**Morphology regions**
- high-gradient structures identified from the local 2MASS K field
- useful for cloud edges, rims, pillars, diffuse structure, and non-point-source analysis

This intentionally separates **point-source science** from **morphology-region science**.

## Archive discovery

FORGE can currently query or inspect:

### MAST
- HST
- JWST
- IUE
- HLA
- HLSP
- other MAST-hosted holdings

FORGE can:
- summarize mission holdings near a target
- preview selected MAST image products
- search candidate MAST FITS spectral products
- parse and plot compatible 1-D wavelength / flux spectra
- export plotted spectra as CSV

### SDSS
- optical image retrieval
- spectroscopic target search
- 1-D spectral plotting when a match exists

### APOGEE DR17
FORGE can retrieve and plot real APOGEE H-band spectra for matched science targets.

**Validated example:** Orion `target_01` successfully retrieves and renders its real APOGEE DR17 spectrum.

### IRSA
- 2MASS PSC
- AllWISE

### ALMA
- public science-dataset discovery
- observation metadata around the target field

### NRAO / radio
The current radio layer supports:
- NRAO archive discovery paths for facilities such as VLA, VLBA, and GBT
- timeout protection so unavailable archive services do not freeze the app
- preliminary spectral-line triage using channel count, product type, spectral resolution, and related metadata

The triage labels products as candidates such as **LIKELY SPECTRAL**, **POSSIBLE**, or **CONTINUUM / UNCLEAR**. These labels indicate product capability, not a confirmed molecular or atomic line detection.

### Historical astronomy
Current historical discovery includes:
- DSS / DSS2
- Harvard DASCH exposure discovery

These provide a path toward long-baseline historical comparisons and plate-based studies.

## Spectroscopy

Spectroscopy is now a first-class FORGE workflow rather than a demonstration-only feature.

Current capabilities:

- SDSS optical spectrum retrieval
- APOGEE DR17 H-band spectrum retrieval
- MAST spectral-product discovery
- generic parsing of common FITS wavelength / flux structures
- real spectrum plotting
- optional common optical line markers
- downloadable wavelength / flux CSV files

### Current validation cases

**Orion target_01**
- real APOGEE DR17 spectrum successfully retrieved
- wavelength and flux parsed and plotted correctly

**θ¹ Orionis C / Orion Nebula field**
- SDSS: no spectroscopic match
- APOGEE DR17: no target match
- MAST: rich archive coverage
- MAST previews: successfully rendered
- MAST spectroscopy: 10 candidate spectral products discovered and a real spectrum successfully plotted
- ALMA: large public observation inventory in the field

This field is now a primary validation case for future emission-line and source-versus-nebula spectroscopy workflows.

## Multi-band imaging

The web interface currently retrieves and displays:

- SDSS optical
- 2MASS J
- 2MASS H
- 2MASS Ks

The Orion tests demonstrate why multi-wavelength comparison matters: optical imagery can become difficult to interpret in bright nebulosity while the near-infrared 2MASS bands may reveal substantially clearer local structure.

## Morphology and local environment

FORGE includes:

- point-source analysis
- aperture / background measurements
- radial and azimuthal structure analysis
- local-background asymmetry
- contrast and overlay products
- morphology candidate generation

A key Orion result was that `target_01` lies in a substantially more asymmetric and structured local infrared background than the comparison targets, reinforcing the need to distinguish stellar measurements from environmental structure.

## Storage architecture

FORGE is designed so the science workflow is not tied to one computer or cloud provider.

Current storage backends:

- local application storage
- S3-compatible object storage

Conceptual model:

```text
FORGE Web
   |
   +-- Local project storage
   +-- AWS S3
   +-- S3-compatible object storage
   +-- Fornax-compatible object storage
   +-- future: Google Cloud Storage
   +-- future: Azure Blob Storage
```

Credentials are not stored in the repository. Production credentials should be supplied through the hosting platform's secret-management system.

Typical project structure:

```text
forge/
└── project/
    └── targets/
        └── target_name/
            ├── imagery
            ├── spectra
            ├── analysis.json
            └── archive_manifest.json
```

## Current science modules

- target / catalog handling
- persistent target library
- nearby-star suggestions
- morphology-region suggestions
- archive discovery
- SDSS imaging
- 2MASS J / H / Ks imaging
- point-source analysis
- morphology analysis
- radial / azimuthal structure analysis
- contrast and overlays
- SDSS spectroscopy
- APOGEE spectroscopy
- MAST spectroscopy
- radio spectral-product triage
- historical-survey discovery
- portable storage
- Streamlit web interface
- Jupyter / NASA Fornax workflow

## Release engineering

FORGE v0.11 now includes two GitHub Actions release gates:

- **Python application** — installs the web-app dependencies on Python 3.11 and 3.12, compiles the Python sources, installs the local package, and runs the smoke-test suite.
- **Python package** — builds a source distribution and wheel, validates the distributions, installs the wheel, verifies the package version, and uploads the build artifacts.

Python package metadata lives in `pyproject.toml`. The initial importable package API is `forge_astronomy`, version `0.11.0`. During the public alpha the Streamlit application remains under `webapp/`; reusable science-engine code will progressively migrate behind the package API.

See `RELEASE_CHECKLIST.md` for the team-release gate.

## Development milestones

### Completed in the current public alpha

**Milestone 1 — Core science workflow**
- coordinate-driven analysis
- multi-band Orion validation
- photometry and local-environment analysis
- reusable Fornax / Python workflow

**Milestone 2 — Public web app**
- Streamlit deployment
- public access without a Fornax account
- dark high-contrast interface
- persistent/reference target workflow

**Milestone 3 — Multi-archive discovery**
- MAST
- SDSS
- IRSA
- ALMA
- radio discovery paths
- historical survey discovery

**Milestone 4 — Candidate generation**
- 2MASS compact-star suggestions
- Gaia DR3 suggestions
- morphology-region suggestions

**Milestone 5 — Real spectroscopy**
- SDSS spectrum plotting
- APOGEE DR17 real-target validation
- MAST real-spectrum validation

**Milestone 6 — Radio spectral triage**
- archive-query framework
- spectral-capability scoring
- responsive timeout behavior

**Milestone 7 — Portable storage**
- local
- S3-compatible
- saved manifests and analysis outputs

## Next milestone cycle

The next development cycle is expected to focus on:

1. **Spectrum selection and explanation**
   - choose among multiple archive spectra
   - instrument / wavelength-range summaries
   - atomic and molecular line identification
   - educational explanations
   - abundance context where scientifically supported

2. **Unified source identity**
   - coordinate cross-matching across Gaia, 2MASS, APOGEE, SDSS, and related catalogs
   - match separation / confidence
   - one FORGE source card per astronomical object

3. **Student Mode**
   - guided workflow
   - simplified controls
   - instructional prompts
   - exportable classroom results

4. **Archive-result cleanup**
   - readable summary tables first
   - raw JSON / technical metadata retained under Advanced details

5. **Radio spectral products**
   - move from metadata triage toward actual spectral-cube / spectral-product visualization where archive services permit

## Demonstration science cases

### Orion A
Three APOGEE-selected Orion targets were used to develop and validate the core point-source and local-environment workflow.

### θ¹ Orionis C / M42
Used to validate a dense multi-archive field, MAST image previews, MAST spectroscopy, ALMA discovery, and future emission-line analysis.

### OMC-2/3
Used to extend the morphology workflow into molecular-cloud structure and molecular-line science.

### M45 / Merope
An independent reflection-nebula case used to test wavelength-dependent morphology.

### WASP-39 b
An exoplanet-oriented branch exploring stellar abundance context and atmospheric observations.

## Repository architecture

Current direction:

```text
FORGE-astronomy/
├── webapp/         # public Streamlit front end
├── forge/          # reusable science engine (planned consolidation)
├── examples/       # target definitions / demonstration workflows
├── tests/          # reproducibility and regression testing
├── docs/           # methods, architecture, provenance
├── README.md
└── CITATION.cff
```

The long-term architecture separates the science engine from the user interface so future web, Jupyter, desktop, API, and mobile clients can use the same FORGE Core.

## Running locally

From the repository root:

```bash
pip install -r webapp/requirements.txt
streamlit run webapp/app.py
```

## Deployment

Current Streamlit Community Cloud configuration:

```text
Repository: terrytrevino/FORGE-astronomy
Branch:     main
Main file:  webapp/app.py
```

Live public alpha:

**https://forge-astronomy-rpjevm5zy6an8falnxcyvx.streamlit.app/**

## Reproducibility

FORGE aims to preserve:

- sky coordinates
- target identity
- candidate-selection provenance
- archive / telescope provenance
- exact retrieved products
- analysis parameters
- CSV / JSON summaries
- spectrum wavelength / flux exports
- figures
- software version information
- storage project paths

The goal is not merely to produce an attractive image or plot, but to make the path from coordinates to evidence auditable.

## Contributors

**FORGE was co-developed by D. Terry Trevino and Vivian Hom.**

- **D. Terry Trevino** — co-developer; project architecture, astronomy workflow, systems integration, analysis design, scientific interpretation
- **Vivian Hom** — co-developer; astronomy workflow development, testing, analysis, validation, scientific interpretation

The project has used ChatGPT (OpenAI) for coding assistance, debugging, workflow design, analysis support, documentation, and presentation drafting. Scientific decisions, interpretation, validation, and authorship remain with the human investigators.

## Citation

See `CITATION.cff` for the current software citation metadata.

A DOI may be added with a future tagged release / archival deposit.

## License

A software license will be selected before the first stable public release.

---

**Checkpoint:** FORGE Web v0.11 public alpha — October 2026.
