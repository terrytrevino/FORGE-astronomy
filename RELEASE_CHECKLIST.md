# FORGE v0.12 Release Candidate Checklist

This checklist is for the professor / team public-alpha evaluation build of FORGE Web v0.12.

## Release engineering

- [x] Public GitHub repository
- [x] Streamlit Community Cloud deployment
- [x] README updated to v0.12
- [x] Python package metadata set to `0.12.0`
- [x] Importable `forge_astronomy` package scaffold
- [x] Python application CI workflow
- [x] Python package build workflow
- [x] Smoke tests updated for v0.12
- [ ] Confirm both GitHub Actions workflows are green
- [ ] Create release tag `v0.12.0` after final validation

## Science validation

- [x] Orion target_01 — real APOGEE DR17 spectrum renders
- [x] θ¹ Orionis C — MAST archive discovery works
- [x] θ¹ Orionis C — MAST previews rendered in manual validation
- [x] θ¹ Orionis C — MAST spectral candidates discovered and a spectrum rendered
- [x] Gaia + 2MASS nearby-star suggestions populate
- [x] Morphology suggestions populate
- [x] SDSS + 2MASS imaging workflow renders
- [x] ALMA inventory discovery works
- [x] ASKAP/CASDA live radio discovery is integrated
- [x] NRAO timeout fails gracefully and keeps the app responsive
- [x] Signed-out/incognito app smoke test completed

## Guided workflow / Field Brief validation

- [x] Start Here workflow guides target → archives → spectroscopy → analysis → Field Brief
- [x] Completed target milestones persist across new browser sessions where saved evidence is available
- [x] FORGE Field Brief renders for target_01
- [x] Field Brief includes archive inventory, Discovery Lens, evidence status, provenance, and open questions
- [x] Markdown Field Brief download works
- [x] Shareable Field Brief permalink renders independently
- [x] Share link regenerates when new evidence, including spectroscopy, is attached
- [ ] Re-test target_01 shared permalink after the latest share-link regeneration fix

## Public-facing communication

- [x] Live app URL confirmed
- [x] GitHub repository URL confirmed
- [x] GitHub README explains FORGE as an investigation engine rather than only an archive aggregator
- [x] README documents Field Brief v0.12
- [ ] Update Wix homepage copy from “Coming Next” to “Available now in FORGE v0.12”
- [ ] Confirm Wix homepage hero explains the core distinction: catalogs identify objects; FORGE investigates the evidence around them
- [ ] Final Wix mobile/link check
- [ ] Share with team / professors as **FORGE Web v0.12 public alpha**
- [ ] Ask testers to report target name/coordinates, action taken, expected result, actual result, and screenshot/error text
- [ ] Decide software license before a broader stable public release

## Next feature cycle

- richer PDF / visual Field Briefs
- unified Gaia ↔ 2MASS ↔ APOGEE ↔ SDSS source identity
- selectable spectra instead of first-parseable selection
- deeper spectral-line explanations and abundance context
- guided / Student Mode refinements
- archive summary-table cleanup
- deeper radio spectral-product visualization
