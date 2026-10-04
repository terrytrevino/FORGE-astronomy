# FORGE Web App v0.1

A lightweight Streamlit front end for the existing FORGE Orion workflow.

## Features

- Enter RA/Dec
- Choose Point source or Morphology region
- Acquire SDSS optical imagery
- Acquire 2MASS J/H/K imagery
- Display all four bands together
- Upload `wcs_candidates.csv`
- Run a simple local-background sector asymmetry test

## Run locally

```bash
pip install -r webapp/requirements.txt
streamlit run webapp/app.py
```

## Deploy on Streamlit Community Cloud

Use:
- Repository: `terrytrevino/FORGE-astronomy`
- Branch: `main`
- Main file path: `webapp/app.py`

## Next version

v0.2 can wire in:
- 2MASS catalog colors
- aperture photometry
- radial/azimuthal morphology
- point-source candidate ranking
- persistent target library
- downloadable analysis reports
