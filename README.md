# Relation-Aware Multi-Chart Editing with Executable Code

This repository accompanies an anonymous submission on relation-aware multi-chart editing in a chart-to-code setting. Given only a rendered multi-chart dashboard and a natural-language edit instruction, a model must return one complete executable Python program. The original plotting code and source data are not model inputs.

## Benchmark at a glance

- 4,091 frozen research tasks; 4,078 tasks in the redistributable public package
- 37 chart types, 42 domains, and 2--7 subplots per dashboard
- 828 relation-aware tasks with explicit affected nodes, preserved nodes, and activated relation edges
- public 298-task evaluation set covering 233 base-dashboard clusters
- seven model runs with sanitized requests, raw responses, generated programs, renders, and frozen scores

## Repository contents

- `scripts/`: frozen evaluator, bootstrap analysis, request materialization, and restricted Docker runner
- `docs/`: dataset card, metric definition, source-level audit, and upload/release instructions
- `metadata/`: public release manifest, dataset statistics, fixed-test index, and exclusion record
- `results/`: aggregate and per-sample evaluation records, statistical tests, and 300-task sensitivity summaries
- `examples/`: four complete benchmark records with model input, instruction, labels, executable reference, and target render
- `licenses/`: Apache-2.0 code license, CC BY 4.0 benchmark-data license, and third-party notices

## Release assets

The repository's **Releases** page should contain:

1. `relation_aware_multichart_public_v1.zip`: the complete 4,078-task redistributable benchmark.
2. `anonymous_evaluation_artifact_public298_v1.zip`: the complete 298-task evaluation artifact, including all seven model outputs.

The large archives are release assets rather than Git-tracked files. Verify their hashes against `RELEASE_SHA256SUMS.txt` before use.

## Reproduce the reported analysis

The 298-task artifact already contains frozen model outputs and metric records; reproducing the reported statistics does not call any model API.

```bash
python scripts/bootstrap_evaluation_v2_3.py \
  --evaluation-root results/evaluation \
  --output-root reproduced_statistics \
  --iterations 10000 \
  --seed 20260727
```

Build the restricted evaluator image with:

```bash
docker build -f scripts/Dockerfile.evaluator -t relation-chart-evaluator:py38 scripts
```

See `docs/METRIC_PARAMETERS.md` for metric definitions and frozen parameter values. See `docs/DATASET_CARD.md` and `licenses/THIRD_PARTY_NOTICES.md` before redistribution.

## License

Software is licensed under Apache-2.0. Benchmark-authored annotations, manifests, structured edit programs, evaluation labels, and original synthetic renders are licensed under CC BY 4.0. Third-party source data and real-data-derived artifacts retain their upstream terms. The project licenses do not override those terms.

## Citation

The anonymous citation metadata in `CITATION.cff` should be replaced with the final paper record after double-blind review.
