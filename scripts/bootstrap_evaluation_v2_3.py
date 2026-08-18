import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


METRICS = [
    "overall_score",
    "code_executability",
    "low_level_edit_accuracy",
    "high_level_score",
    "relation_conditioned_fidelity",
    "relation_scope_accuracy",
    "relation_edge_consistency",
    "visual_structural_similarity",
    "preservation_accuracy",
]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def ci(values):
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return {"mean": None, "ci_low": None, "ci_high": None}
    return {
        "mean": float(np.mean(finite)),
        "ci_low": float(np.percentile(finite, 2.5)),
        "ci_high": float(np.percentile(finite, 97.5)),
    }


def two_sided_bootstrap_pvalue(estimates):
    values = np.asarray(estimates, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return None
    lower = (np.count_nonzero(values <= 0.0) + 1) / (values.size + 1)
    upper = (np.count_nonzero(values >= 0.0) + 1) / (values.size + 1)
    return float(min(1.0, 2.0 * min(lower, upper)))


def add_holm_adjustment(rows):
    by_metric = defaultdict(list)
    for index, row in enumerate(rows):
        if row.get("p_value") is not None:
            by_metric[row["metric"]].append(index)
    for indices in by_metric.values():
        ordered = sorted(indices, key=lambda index: rows[index]["p_value"])
        count = len(ordered)
        running = 0.0
        for rank, index in enumerate(ordered):
            adjusted = min(1.0, (count - rank) * rows[index]["p_value"])
            running = max(running, adjusted)
            rows[index]["p_value_holm"] = running
            rows[index]["significant_holm_05"] = bool(running < 0.05)


def safe_nanmean(values):
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    return float(np.mean(finite)) if finite.size else np.nan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260727)
    args = parser.parse_args()

    models = {}
    for model_dir in sorted(path for path in args.evaluation_root.iterdir() if path.is_dir()):
        metrics_path = model_dir / "metrics_per_sample.json"
        if metrics_path.exists():
            models[model_dir.name] = json.loads(metrics_path.read_text(encoding="utf-8"))
    if not models:
        raise SystemExit(f"No model metrics found under {args.evaluation_root}")

    task_ids = [row["task_id"] for row in next(iter(models.values()))]
    task_index = {task_id: index for index, task_id in enumerate(task_ids)}
    clusters = defaultdict(list)
    first_rows = {row["task_id"]: row for row in next(iter(models.values()))}
    for task_id in task_ids:
        row = first_rows[task_id]
        cluster_key = (row.get("split"), row.get("dashboard_id") or task_id)
        clusters[cluster_key].append(task_index[task_id])
    split_clusters = defaultdict(list)
    for cluster_key in clusters:
        split_clusters[cluster_key[0]].append(cluster_key)

    arrays = {}
    for model, rows in models.items():
        by_task = {row["task_id"]: row for row in rows}
        if set(by_task) != set(task_ids):
            raise ValueError(f"{model} does not contain the same task set")
        arrays[model] = {
            metric: np.asarray(
                [
                    float(by_task[task_id][metric])
                    if isinstance(by_task[task_id].get(metric), (int, float))
                    else np.nan
                    for task_id in task_ids
                ],
                dtype=float,
            )
            for metric in METRICS
        }

    rng = np.random.default_rng(args.seed)
    bootstrap_indices = []
    for _ in range(args.iterations):
        sampled = []
        for cluster_keys in split_clusters.values():
            selected_clusters = rng.choice(
                len(cluster_keys), size=len(cluster_keys), replace=True
            )
            for selected in selected_clusters:
                sampled.extend(clusters[cluster_keys[int(selected)]])
        bootstrap_indices.append(np.asarray(sampled, dtype=int))

    model_rows = []
    model_json = {}
    for model, metric_arrays in arrays.items():
        model_json[model] = {}
        for metric, values in metric_arrays.items():
            estimates = [safe_nanmean(values[index]) for index in bootstrap_indices]
            interval = ci(estimates)
            observed = safe_nanmean(values)
            record = {
                "model": model,
                "metric": metric,
                "observed": observed,
                **interval,
            }
            model_rows.append(record)
            model_json[model][metric] = record

    pair_rows = []
    model_names = sorted(models)
    for left_index, left in enumerate(model_names):
        for right in model_names[left_index + 1 :]:
            for metric in METRICS:
                difference = arrays[left][metric] - arrays[right][metric]
                estimates = [safe_nanmean(difference[index]) for index in bootstrap_indices]
                interval = ci(estimates)
                p_value = two_sided_bootstrap_pvalue(estimates)
                pair_rows.append(
                    {
                        "model_a": left,
                        "model_b": right,
                        "metric": metric,
                        "applicable_subset": (
                            "relation_samples_only"
                            if metric
                            in {
                                "relation_conditioned_fidelity",
                                "relation_scope_accuracy",
                                "relation_edge_consistency",
                            }
                            else "all_samples"
                        ),
                        "observed_a_minus_b": safe_nanmean(difference),
                        "ci_low": interval["ci_low"],
                        "ci_high": interval["ci_high"],
                        "p_value": p_value,
                        "significant_95": bool(
                            interval["ci_low"] > 0 or interval["ci_high"] < 0
                        ),
                    }
                )
    add_holm_adjustment(pair_rows)

    args.output_root.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_root / "model_metric_bootstrap_ci.csv", model_rows)
    write_csv(args.output_root / "paired_model_difference_ci.csv", pair_rows)
    write_json(
        args.output_root / "bootstrap_summary.json",
        {
            "iterations": args.iterations,
            "seed": args.seed,
            "resampling_unit": "dashboard_id_cluster",
            "stratification": ["split"],
            "cluster_count": len(clusters),
            "multiple_comparison_correction": "Holm within each metric family",
            "models": model_json,
            "paired_differences": pair_rows,
        },
    )
    print(
        json.dumps(
            {
                "models": len(models),
                "tasks": len(task_ids),
                "iterations": args.iterations,
                "model_intervals": len(model_rows),
                "paired_intervals": len(pair_rows),
                "output_root": str(args.output_root.resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
