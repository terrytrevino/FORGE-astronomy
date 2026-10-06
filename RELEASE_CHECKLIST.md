# FORGE v0.11 Release Candidate Checklist

This checklist is for the first team / selected-friends release of FORGE Web v0.11.

## Release engineering

- [x] Public GitHub repository
- [x] Streamlit Community Cloud deployment
- [x] README updated to v0.11
- [x] Python package metadata in `pyproject.toml`
- [x] Importable `forge_astronomy` package scaffold
- [x] Python application CI workflow
- [x] Python package build workflow
- [x] Smoke tests for package version, required app files, and Python syntax
- [ ] Confirm both GitHub Actions workflows are green
- [ ] Create release tag `v0.11.0` after final validation

## Science validation

- [x] Orion target_01 — real APOGEE DR17 spectrum renders
- [x] θ¹ Orionis C — MAST archive discovery works
- [x] θ¹ Orionis C — six MAST previews rendered in manual validation
- [x] θ¹ Orionis C — MAST spectral candidates discovered and a spectrum rendered
- [x] Gaia + 2MASS nearby-star suggestions populate
- [x] Morphology suggestions populate
- [x] SDSS + 2MASS imaging workflow renders
- [x] ALMA inventory discovery works
- [x] NRAO timeout fails gracefully and keeps the app responsive
- [ ] Final browser smoke test from a signed-out/incognito session

## Release communication

- [ ] Confirm live app URL
- [ ] Confirm GitHub repository URL
- [ ] Share with team and selected friends as **FORGE Web v0.11 public alpha**
- [ ] Ask testers to report target name/coordinates, action taken, expected result, actual result, and screenshot/error text
- [ ] Decide software license before a broader stable public release

## Deferred to the next feature cycle

- unified Gaia ↔ 2MASS ↔ APOGEE ↔ SDSS source identity
- selectable MAST spectra instead of first-parseable selection
- spectral-line explanations and abundance context
- Student Mode / classroom workflow
- archive summary-table cleanup
- deeper radio spectral-product visualization
