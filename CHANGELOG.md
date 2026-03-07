# Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2026-03-07
### Added
- Project information and GitHub links for related projects in `README.md` and script output.
- Project standardization to English (variables, functions, comments, CLI).
- Main script renamed from `GeradorBackbone.py` to `backbone-network-topology-generator.py`.
- Output filenames changed to English:
  - `conexoes.csv` -> `connections.csv`
  - `elementos.csv` -> `elements.csv`
  - `localidades.csv` -> `locations.csv`
- Updated CSV headers for improved clarity.
- Coordinate jitter (±0.0005) to prevent element overlapping in geographic maps.
- Increased decimal precision (2 decimal places) for seconds in DMS coordinate format.

### Fixed
- Site ID collisions by increasing city name normalization from 3 to 10 characters.
- SWAC (Metro) self-loops in cities with only one switch.
- Corrected connection statistics in the summary report.

## [A1.05] - 2026-03-06
### Added
- Proportional regional distribution for INNER-CORE and REFLECTOR layers.
- Integrated IXP (PTT) locations as mandatory hubs.

## [A1.00] - 2024-01-15
- Initial release with basic 5-layer hierarchical generation.
