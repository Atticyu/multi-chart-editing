# Source and License Audit, v6

Audit generated: `2026-08-09T16:00:59.310445+00:00`

This is a dataset-level provenance and release-decision record, not legal advice. It replaces
the earlier group-level assumption with direct source, terms, attribution, transformation, and
checksum fields for each of the 25 real-data tables.

## Result

- Audited source tables: 25
- Approved for raw-table redistribution with the recorded conditions: 24
- Excluded from raw-table redistribution pending license confirmation: 1
- Source groups: 8
- Status counts: `{"excluded_unverified_dataset_license": 1, "verified_redistributable_public_domain": 6, "verified_redistributable_with_attribution": 7, "verified_redistributable_with_required_disclaimer": 1, "verified_redistributable_with_upstream_attribution": 8, "verified_upstream_public_domain_with_mirror_provenance": 2}`

## Blocking Item

- `vega_stocks`: The Vega repository code is BSD-3-Clause, but its README states that datasets retain separate licenses. The stocks resource has neither source nor license metadata. Release action: exclude `raw/vega/stocks.csv` and dependent samples unless an authoritative dataset license is obtained.

## Affected Benchmark Artifacts

- Base dashboards: 2
- Full real editing samples: 13
- `test_100_fixed` affected tasks: 1
- `test_20_fixed` affected tasks: 0
- `test_300_fixed` affected tasks: 2

## Interpretation

Publicly downloadable data are not automatically licensed for unrestricted redistribution.
For this release, 24 tables have a documented redistribution route. The remaining Vega stocks
table is publicly accessible but lacks an identified data provider and per-dataset license; the
Vega repository's BSD-3-Clause software license cannot be applied to it by assumption.

OWID was checked per Grapher indicator rather than by homepage. All selected OWID full-indicator
records in the stored snapshots report `nonRedistributable=false`; their upstream citations and
license labels must remain with the release.

## Publication Boundary

The paper may state that 25 public source tables were audited and that 24 are approved for raw
redistribution under their recorded terms. It should not state that all 25 share a single open
license. If the public benchmark excludes the listed stock-derived samples, report the final public
sample count separately from the frozen internal evaluation count.
