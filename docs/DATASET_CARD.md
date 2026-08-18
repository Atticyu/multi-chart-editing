# Dataset Card

## Task

Each model-facing sample contains `input_image.png` and `instruction.txt`. The required response is a complete Python program that writes `target_image.png`. The model is not given the original plotting code, source table, edit plan, target image, masks, or relation labels.

## Public release

The frozen internal benchmark contains 4,091 accepted tasks. The redistributable public package contains 4,078 tasks after excluding 13 tasks derived from one table whose dataset-specific redistribution permission could not be verified.

| Property | Public value |
|---|---:|
| Tasks | 4,078 |
| Base dashboards | 788 |
| Real-data-derived tasks | 352 |
| Synthetic tasks | 3,726 |
| Relation-aware tasks | 828 |
| Chart types | 37 |
| Domains | 42 |
| Subplots per task | 2--7 |

The public release manifest is `metadata/global_release_manifest.jsonl`. Exact counts and build exclusions are in `metadata/dataset_statistics.json` and `metadata/PUBLIC_RELEASE_EXCLUSIONS_V6.json`.

## Primary evaluation set

The primary test contains 298 redistributable tasks from 233 base-dashboard clusters: 58 real-data-derived and 240 synthetic tasks. It was obtained by removing two nonredistributable records from a preselected 300-task stress test; no model was rerun. The fixed-test index is `metadata/test_298_sample_index.csv`.

## Relations and edit scope

Relation-aware records identify affected subplot nodes, preserved nodes, and instruction-activated edges. Edges can encode shared labels, variables, semantic groups, data fields, or coordinated visual policies. Relation annotations are evaluator-side labels and are not exposed as model input.

## Quality control

Reference programs are rendered in a frozen environment. Automated checks reject failed renders, empty panels, exact input-target no-ops, unchanged affected panels, severe text overlap, invalid legend placement, implausible canvas geometry, and disagreement between saved code and target render. Targeted human inspection was used to discover recurring failure modes and improve rules; it was not a randomized human-rating study.

## Known boundaries

- Explicit relation labels occur only in synthetic tasks.
- Real-data-derived dashboards use public tables but are programmatically composed rather than naturally collected dashboard images.
- The task intentionally combines visual reconstruction, scope inference, and editing because source code and data are hidden.
- The deterministic metrics pass no-op, oracle, and controlled-perturbation checks but are not calibrated to human semantic ratings.
- Instruction language still contains repeated normalized patterns; the release does not claim template-held-out generalization.

## Provenance and licensing

The real-data source audit is in `docs/source_license_audit_v6.json` and `docs/THIRD_PARTY_SOURCE_DETAILS.md`. Follow dataset-level upstream terms and attribution requirements before redistributing derived real-data artifacts.
