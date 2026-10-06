# FORGE v0.13 Feature Specification — Sky Context / Finder Charts

## Purpose

Add a target-centered visual context layer that answers:

> **Where is this target, and what is around it?**

Sky Context should appear early in the investigation, after a target is chosen or resolved and before deeper archive interpretation.

## Product role

FORGE should not attempt to replace Aladin.

- **Aladin:** visual sky navigation and field context
- **FORGE:** investigation logic, archive discovery, evidence comparison, quality evaluation, synthesis, provenance, and Field Brief generation

## Minimum viable implementation

- center on the active FORGE target
- clearly mark the target position
- display target name
- display RA / Dec
- adjustable field of view
- angular scale
- north/east orientation
- standard survey background
- optional **Open in Aladin** handoff
- clean placement near the top of the FORGE workflow
- support export/inclusion in future Field Brief layouts

## Follow-on overlays

Candidate overlays include:

- Gaia DR3
- 2MASS
- SIMBAD
- FORGE nearby-star candidates
- FORGE morphology regions
- archive footprints where available
  - HST
  - JWST
  - MAST products
  - ALMA
  - other archives when reliable footprint metadata are available

## User flow

```text
Choose / resolve target
        ↓
Sky Context / Finder Chart
        ↓
Search All Archives
        ↓
Spectroscopy / imaging / historical / radio-mm evidence
        ↓
Acquire + Analyze
        ↓
FORGE Field Brief
```

The finder chart provides spatial orientation before archive and science interpretation.

## Field Brief integration

Future richer Field Briefs should include a **Sky Context** block near the beginning of the report:

- target marker
- field of view
- scale
- orientation
- optional nearby-source overlays
- optional archive footprints

This provides the visual bridge between target identity and the observational evidence inventory.

## Scientific value

Sky Context helps users:

- confirm that they are investigating the intended field
- understand local source density and morphology
- visually relate compact sources to extended structures
- distinguish target context from catalog identity
- identify nearby objects or structures worth promoting into a new FORGE investigation
- understand the geometry of archive coverage where footprints are available

## Design constraints

- preserve the dark, high-contrast FORGE visual system
- remain readable for color-vision deficiencies
- avoid clutter from too many overlays
- overlays should be optional and individually controllable
- target marker must remain visually dominant
- do not imply that an overlaid catalog association is physically related without supporting evidence
- preserve archive/catalog provenance for every displayed layer

## Release target

Candidate first major feature for **FORGE v0.13**.
