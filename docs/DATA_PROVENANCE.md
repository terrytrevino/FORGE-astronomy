# Data Provenance

FORGE is designed around explicit provenance. A result should identify the source observation, target coordinates, processing path, and analysis parameters.

## Surveys and observatories used in development

### 2MASS
Near-infrared J, H, and K_s imaging from the Two Micron All Sky Survey.

Primary reference: Skrutskie et al. (2006), *The Two Micron All Sky Survey*, AJ, 131, 1163.

### WISE
Mid-infrared all-sky imaging from the Wide-field Infrared Survey Explorer.

Primary reference: Wright et al. (2010), *The Wide-field Infrared Survey Explorer: Mission Description and Initial On-orbit Performance*, AJ, 140, 1868.

### DSS2
Digitized photographic sky survey imaging used for optical context and morphology comparisons.

### Gaia
Astrometric and stellar-density context products from ESA's Gaia mission.

### CARMA–NRO Orion Survey
Molecular-line products for Orion A, including 12CO, 13CO, and C18O, combining CARMA interferometric observations with Nobeyama 45 m single-dish data.

Development products include moment maps, excitation-temperature products, column-density products, and PPV cubes.

### JWST
NASA / ESA / CSA James Webb Space Telescope public science products used for presentation context and the WASP-39 b exoplanet demonstration.

### NASA Exoplanet Archive
System parameters and published host-star abundance context used by the FORGE exoplanet demonstration.

## Important interpretation rule

Archive availability depends on sky position. A coordinate can be entered anywhere, but FORGE must first determine which observations actually cover that position before selecting an analysis path.
