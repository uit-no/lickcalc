# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- No entries yet.

### Changed
- No entries yet.

### Fixed
- No entries yet.

## [1.2.1] - 2026-07-25

### Added
- No entries yet.

### Changed
- Version bump from 1.2.0 to 1.2.1.
- Updated Dash dependency to 4.4.1 for deployment/runtime consistency.
- Aligned environment dependency constraints with the known-good deployment dependency policy in requirements.txt.

### Fixed
- Reduced dependency drift between deployment and local environment manifests for dash-bootstrap-components and trompy.

## [1.2.0] - 2026-07-25

### Added
- Added a modernized default Plotly visual theme with improved axis/grid styling.

### Changed
- Version bump from 1.1.0 to 1.2.0.
- Moved the Remove long licks control below the microstructural results table.
- Reduced plot heights for a more compact (squatter) graph layout.
- Updated graph colorway to a more attractive and varied palette.
- Updated the Weibull observed series rendering from circle markers to a staircase-style line.
- Set plot backgrounds to match the app background color.

### Fixed
- Fixed horizontal graph alignment behavior when the First n ILIs slider is shown by synchronizing vertical spacing across adjacent graph columns.

## [1.1.0] - 2026-05-29

### Added
- Added support for Coulbourn data files.
- Added Pixi environment files for more reproducible setup.

### Changed
- Version bump from 1.0.4 to 1.1.0.
- Improved handling of Ohrbets offset workflows.

### Fixed
- None.

## [1.0.4] - 2025-11-19

### Changed
- Version bump from 1.0.3 to 1.0.4.
- Started fixes for Ohrbets offset behavior.

## [1.0.3] - 2025-11-18

### Changed
- Version bump from 1.0.2 to 1.0.3.
- Improved LS file parsing.
- Added inter-burst interval (IBI) to the results table.

## [1.0.2] - 2025-11-13

### Changed
- Version bump from 1.0.1 to 1.0.2.
- Minor cleanup and documentation refinements.

## [1.0.1] - 2025-11-13

### Added
- Added batch processing, including auto offset detection and improved batch export.
- Added trial-based analysis options and between-time window analysis.
- Added inter-burst interval export/analysis and LS lab file parsing support.

### Changed
- Version bump from 1.0.0 to 1.0.1.
- Improved batch modal usability and help/README content.

## [1.0.0] - 2025-11-03

### Added
- Introduced project version file and set initial version to 1.0.0.
- Added an About dialog showing the app version.
