import argparse
import ast
import csv
import json
import math
import re
from concurrent.futures import ProcessPoolExecutor
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image


RELATION_WEIGHTS = {
    "low_level_edit_accuracy": 0.35,
    "high_level_score": 0.65,
}
NON_RELATION_WEIGHTS = {
    "low_level_edit_accuracy": 0.45,
    "high_level_score": 0.55,
}

PRESERVE_OPS = {"preserve_data_values", "preserve_unrelated_charts"}
RELATION_TYPES = {"multi_chart_relation", "complex_relation"}
SAFE_REFERENCE_TYPES = {
    "line",
    "multi_line",
    "step_line",
    "area",
    "stacked_area",
    "bar",
    "horizontal_bar",
    "grouped_bar",
    "stacked_bar",
    "stacked_horizontal_bar",
    "proportional_bar",
    "lollipop",
    "dot_plot",
    "waterfall",
}


def read_json(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clamp(value, lo=0.0, hi=1.0):
    if value is None or math.isnan(float(value)):
        return lo
    return max(lo, min(hi, float(value)))


def load_rgb(path, size=None):
    image = Image.open(path).convert("RGB")
    if size is not None and image.size != size:
        image = image.resize(size, Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.float32)


def image_valid(path):
    if not path.exists():
        return False, "missing"
    if path.stat().st_size < 1000:
        return False, "too_small_file"
    try:
        image = Image.open(path).convert("RGB")
    except Exception as exc:
        return False, f"open_error:{exc}"
    if image.width < 400 or image.height < 250:
        return False, f"too_small_canvas:{image.width}x{image.height}"
    arr = np.asarray(image, dtype=np.float32)
    if float(arr.std()) < 1.0:
        return False, "blank_or_constant"
    return True, f"{image.width}x{image.height}"


def mse(a, b, mask=None):
    diff = (a.astype(np.float32) - b.astype(np.float32)) ** 2
    if mask is not None:
        if mask.sum() == 0:
            return 0.0
        diff = diff[mask]
    return float(np.mean(diff))


def mae(a, b, mask=None):
    diff = np.abs(a.astype(np.float32) - b.astype(np.float32))
    if mask is not None:
        if mask.sum() == 0:
            return 0.0
        diff = diff[mask]
    return float(np.mean(diff))


def standard_ssim(a, b):
    if np.array_equal(a, b):
        return 1.0
    from skimage.metrics import structural_similarity

    gray_a = np.dot(a[..., :3], [0.299, 0.587, 0.114]).astype(np.float32)
    gray_b = np.dot(b[..., :3], [0.299, 0.587, 0.114]).astype(np.float32)
    return float(structural_similarity(gray_a, gray_b, data_range=255.0))


def bounded_metric_size(size, max_dimension=512):
    width, height = size
    scale = min(1.0, max_dimension / max(width, height))
    return max(1, int(round(width * scale))), max(1, int(round(height * scale)))


def changed_mask(before, after, threshold=24):
    delta = np.max(np.abs(before.astype(np.float32) - after.astype(np.float32)), axis=2)
    return delta > threshold


def normalized_improvement(noop_error, pred_error):
    if noop_error <= 1e-9:
        return 1.0 if pred_error <= 1e-9 else 0.0
    return clamp((noop_error - pred_error) / noop_error)


def normalized_similarity_improvement(noop_similarity, pred_similarity):
    if noop_similarity >= 1.0 - 1e-9:
        return 1.0 if pred_similarity >= 1.0 - 1e-9 else 0.0
    return clamp((pred_similarity - noop_similarity) / (1.0 - noop_similarity))


def extract_reference_spec(code_path):
    code = safe_read_code(code_path).lstrip("\ufeff")
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "SPEC" for target in node.targets):
            continue
        value = node.value
        if (
            isinstance(value, ast.Call)
            and value.args
            and isinstance(value.args[0], ast.Constant)
            and isinstance(value.args[0].value, str)
        ):
            try:
                return json.loads(value.args[0].value)
            except json.JSONDecodeError:
                return {}
    return {}


def grid_shape(chart_count):
    cols = 2 if chart_count <= 4 else 3
    rows = int(math.ceil(chart_count / cols))
    return rows, cols


def weighted_boundaries(length, weights):
    total = float(sum(weights))
    boundaries = [0]
    running = 0.0
    for weight in weights:
        running += float(weight)
        boundaries.append(int(round(length * running / total)))
    boundaries[-1] = length
    return boundaries


def cell_slices(height, width, chart_count, layout_id="regular_grid"):
    if layout_id == "wide_top" and chart_count >= 3:
        cols = 3
        rows = 1 + int(math.ceil((chart_count - 1) / cols))
        ys = weighted_boundaries(height, [1.18] + [1.0] * (rows - 1))
        xs = weighted_boundaries(width, [1.0] * cols)
        cells = [(slice(ys[0], ys[1]), slice(0, width))]
        for idx in range(chart_count - 1):
            row = 1 + idx // cols
            col = idx % cols
            cells.append((slice(ys[row], ys[row + 1]), slice(xs[col], xs[col + 1])))
        return cells
    if layout_id == "left_focus" and chart_count >= 4:
        rows = int(math.ceil((chart_count - 1) / 2))
        ys = weighted_boundaries(height, [1.0] * rows)
        xs = weighted_boundaries(width, [1.35, 1.0, 1.0])
        cells = [(slice(0, height), slice(xs[0], xs[1]))]
        for idx in range(chart_count - 1):
            row = idx // 2
            col = 1 + idx % 2
            cells.append((slice(ys[row], ys[row + 1]), slice(xs[col], xs[col + 1])))
        return cells
    if layout_id == "top_strip" and chart_count >= 5:
        cols = 3
        top_count = min(3, chart_count)
        lower = chart_count - top_count
        rows = 1 + int(math.ceil(lower / cols))
        ys = weighted_boundaries(height, [0.82] + [1.18] * (rows - 1))
        xs = weighted_boundaries(width, [1.0] * cols)
        cells = [
            (slice(ys[0], ys[1]), slice(xs[idx], xs[idx + 1]))
            for idx in range(top_count)
        ]
        for idx in range(lower):
            row = 1 + idx // cols
            col = idx % cols
            cells.append((slice(ys[row], ys[row + 1]), slice(xs[col], xs[col + 1])))
        return cells
    rows, cols = grid_shape(chart_count)
    cells = []
    for idx in range(chart_count):
        r = idx // cols
        c = idx % cols
        y1 = int(round(height * r / rows))
        y2 = int(round(height * (r + 1) / rows))
        x1 = int(round(width * c / cols))
        x2 = int(round(width * (c + 1) / cols))
        cells.append((slice(y1, y2), slice(x1, x2)))
    return cells


def cell_changed_rates(input_img, other_img, chart_count, layout_id):
    h, w = input_img.shape[:2]
    mask = changed_mask(input_img, other_img)
    rates = []
    for ys, xs in cell_slices(h, w, chart_count, layout_id):
        cell = mask[ys, xs]
        rates.append(float(cell.mean()) if cell.size else 0.0)
    return rates


def affected_cell_f1(
    input_img,
    ref_img,
    pred_img,
    chart_count,
    layout_id,
    chart_ids=None,
    expected_affected_chart_ids=None,
):
    ref_rates = cell_changed_rates(input_img, ref_img, chart_count, layout_id)
    pred_rates = cell_changed_rates(input_img, pred_img, chart_count, layout_id)
    chart_ids = chart_ids or [f"chart_{index + 1}" for index in range(chart_count)]
    if expected_affected_chart_ids is not None:
        expected = set(expected_affected_chart_ids)
        ref_set = {index for index, chart_id in enumerate(chart_ids) if chart_id in expected}
    else:
        ref_set = {i for i, rate in enumerate(ref_rates) if rate >= 0.0025}
    pred_set = {i for i, rate in enumerate(pred_rates) if rate >= 0.0025}
    if not ref_set and not pred_set:
        return 1.0, 1.0, 1.0, 0, 0, 0, [], []
    tp = len(ref_set & pred_set)
    precision = tp / len(pred_set) if pred_set else 0.0
    recall = tp / len(ref_set) if ref_set else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    reference_ids = [chart_ids[index] for index in sorted(ref_set) if index < len(chart_ids)]
    predicted_ids = [chart_ids[index] for index in sorted(pred_set) if index < len(chart_ids)]
    return f1, precision, recall, len(ref_set), len(pred_set), tp, reference_ids, predicted_ids


def chart_target_fidelities(input_img, ref_img, pred_img, chart_count, layout_id, chart_ids):
    fidelities = {}
    h, w = input_img.shape[:2]
    for chart_id, (ys, xs) in zip(
        chart_ids, cell_slices(h, w, chart_count, layout_id)
    ):
        input_cell = input_img[ys, xs]
        ref_cell = ref_img[ys, xs]
        pred_cell = pred_img[ys, xs]
        target_mask = changed_mask(input_cell, ref_cell)
        if target_mask.any():
            noop_error = mse(ref_cell, input_cell, target_mask)
            pred_error = mse(ref_cell, pred_cell, target_mask)
            score = normalized_improvement(noop_error, pred_error)
        else:
            extra_mae = mae(input_cell, pred_cell)
            score = clamp(1.0 - extra_mae / 64.0)
        fidelities[chart_id] = score
    return fidelities


def relation_edge_consistency(edge_labels, node_fidelities):
    if not edge_labels:
        return None, None, None
    edge_scores = []
    action_scores = []
    endpoint_scores = []
    for edge in edge_labels:
        source = edge.get("source")
        target = edge.get("target")
        source_fidelity = clamp(node_fidelities.get(source, 0.0))
        target_fidelity = clamp(node_fidelities.get(target, 0.0))
        endpoint_score = 0.5 * (source_fidelity + target_fidelity)
        edge_score = math.sqrt(source_fidelity * target_fidelity)
        action_score = float(source_fidelity >= 0.5 and target_fidelity >= 0.5)
        endpoint_scores.append(endpoint_score)
        action_scores.append(action_score)
        edge_scores.append(edge_score)
    return (
        float(np.mean(edge_scores)),
        float(np.mean(action_scores)),
        float(np.mean(endpoint_scores)),
    )


def affected_region_similarity(input_img, ref_img, pred_img, chart_count, layout_id):
    ref_rates = cell_changed_rates(input_img, ref_img, chart_count, layout_id)
    h, w = input_img.shape[:2]
    scores = []
    for idx, (ys, xs) in enumerate(cell_slices(h, w, chart_count, layout_id)):
        if idx >= len(ref_rates) or ref_rates[idx] < 0.0025:
            continue
        ref_cell = ref_img[ys, xs]
        pred_cell = pred_img[ys, xs]
        input_cell = input_img[ys, xs]
        mask = changed_mask(input_cell, ref_cell)
        noop = mse(ref_cell, input_cell, mask)
        pred = mse(ref_cell, pred_cell, mask)
        scores.append(normalized_improvement(noop, pred))
    return float(np.mean(scores)) if scores else 1.0


def safe_read_code(path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def literal_in_code(code, text):
    if not text:
        return 0.0
    norm_code = code.lower()
    norm_text = str(text).lower()
    if norm_text in norm_code:
        return 1.0
    relaxed = re.sub(r"[^a-z0-9]+", "", norm_text)
    relaxed_code = re.sub(r"[^a-z0-9]+", "", norm_code)
    return 1.0 if relaxed and relaxed in relaxed_code else 0.0


def code_quality_score(code, image_valid_score):
    if not code.strip():
        return 0.0
    score = 0.0
    checks = 0
    checks += 1
    score += 1.0 if len(code) >= 300 else 0.0
    checks += 1
    score += 1.0 if ("target_image.png" in code or "target.png" in code) else 0.0
    checks += 1
    score += 1.0 if re.search(r"\b(matplotlib|plt\.|plotly|seaborn|pandas|numpy)\b", code, re.I) else 0.0
    checks += 1
    score += 1.0 if not re.search(r"[A-Za-z]:\\\\|/Users/|/home/|file://", code) else 0.0
    checks += 1
    score += 1.0 if not re.search(r"\b(requests|urllib|socket|subprocess|os\.system|shutil\.rmtree)\b", code) else 0.0
    checks += 1
    try:
        ast.parse(code)
        score += 1.0
    except SyntaxError:
        score += 0.0
    static_score = score / checks
    return clamp(0.75 * static_score + 0.25 * image_valid_score)


def code_evidence_for_operation(op, code):
    name = op.get("operation", "")
    if name == "add_dashboard_title":
        return literal_in_code(code, op.get("text") or op.get("title", ""))
    if name == "change_axis_label":
        return literal_in_code(code, op.get("new_label", ""))
    if name == "rename_label":
        return literal_in_code(code, op.get("new_label", ""))
    if name == "modify_color":
        color = op.get("color", "")
        target = op.get("target", "")
        color_hit = literal_in_code(code, color) or literal_in_code(code, "red" if str(color).upper() == "#DC2626" else color)
        target_hit = literal_in_code(code, target)
        return clamp(0.65 * color_hit + 0.35 * target_hit)
    if name == "add_reference_line":
        return 1.0 if ("axhline" in code or "reference mean" in code.lower() or literal_in_code(code, op.get("label", ""))) else 0.0
    if name == "change_chart_type":
        new_type = str(op.get("new_chart_type") or op.get("chart_type") or op.get("to", "")).lower()
        if new_type == "bar":
            return 1.0 if re.search(r"\.bar\(|barh\(|kind=['\"]bar", code) else 0.0
        return literal_in_code(code, new_type)
    if name == "delete_category_or_series":
        target = str(op.get("target", ""))
        # Deletions are hard to verify statically because code may define source data before filtering.
        return 0.5 if target and target.lower() not in code.lower() else 0.0
    if name == "modify_style":
        hits = sum(1 for token in ["grid", "title", "spine", "linestyle", "color"] if token in code.lower())
        return clamp(hits / 3.0)
    if name == "add_event_marker":
        return 1.0 if ("axvline" in code or "annotate" in code.lower() or "event" in code.lower()) else 0.0
    if name == "add_trend_line":
        return 1.0 if ("polyfit" in code or "trend" in code.lower() or "linregress" in code) else 0.0
    if name == "filter_time_range":
        return 1.0 if ("year" in code.lower() and any(str(v) in code for v in op.values())) else 0.0
    if name == "set_y_scale":
        return 1.0 if ("set_yscale" in code or "yscale" in code.lower()) else 0.0
    if name == "adjust_top_k":
        return 1.0 if ("head(" in code or "nlargest" in code or "top" in code.lower()) else 0.0
    if name == "adjust_rolling_window":
        return 1.0 if ("rolling" in code.lower() or "window" in code.lower()) else 0.0
    return 0.5 if name and name.lower() in code.lower() else 0.0


def operation_counterfactual_scores(ref_dir, input_img, ref_img, pred_img, metric_size, fallback_score):
    manifest = read_json(ref_dir / "operation_counterfactuals" / "manifest.json", default={})
    output = {}
    for row in manifest.get("operations", []):
        index = int(row.get("operation_index", 0)) - 1
        image_name = row.get("counterfactual_image")
        image_path = ref_dir / "operation_counterfactuals" / str(image_name)
        if index < 0 or not row.get("valid_visual_effect") or not image_path.exists():
            continue
        without_img = load_rgb(image_path, size=metric_size)
        operation_mask = changed_mask(without_img, ref_img)
        if not operation_mask.any():
            continue
        noop_error = mse(ref_img, input_img, operation_mask)
        pred_error = mse(ref_img, pred_img, operation_mask)
        output[index] = {
            "visual_score": normalized_improvement(noop_error, pred_error),
            "source": "operation_counterfactual",
            "changed_pixel_rate": float(operation_mask.mean()),
            "counterfactual_noop_mse": noop_error,
            "prediction_mse": pred_error,
        }
    return output


def relation_scope_fidelity(
    ref_dir,
    input_img,
    ref_img,
    pred_img,
    metric_size,
    chart_count,
    layout_id,
    chart_ids,
    evaluation_label,
    node_fidelities,
):
    manifest = read_json(ref_dir / "operation_counterfactuals" / "manifest.json", default={})
    manifest_by_index = {
        int(row.get("operation_index", 0)): row
        for row in manifest.get("operations", [])
    }
    cells = cell_slices(ref_img.shape[0], ref_img.shape[1], chart_count, layout_id)
    chart_to_cell = {chart_id: cell for chart_id, cell in zip(chart_ids, cells)}
    expected_scores = []
    preserved_scores = []
    labeled_endpoints = 0
    visibly_scorable_endpoints = 0

    for operation_label in evaluation_label.get("operation_labels", []):
        expected = set(operation_label.get("expected_affected_charts", []))
        if not expected:
            continue
        labeled_endpoints += len(expected)
        manifest_row = manifest_by_index.get(int(operation_label.get("operation_index", 0)))
        image_name = manifest_row.get("counterfactual_image") if manifest_row else None
        image_path = ref_dir / "operation_counterfactuals" / str(image_name)
        if not manifest_row or not manifest_row.get("valid_visual_effect") or not image_path.exists():
            expected_scores.extend(clamp(node_fidelities.get(chart_id, 0.0)) for chart_id in expected)
            visibly_scorable_endpoints += len(expected)
            continue

        without_img = load_rgb(image_path, size=metric_size)
        for chart_id in expected:
            cell = chart_to_cell.get(chart_id)
            if cell is None:
                continue
            ys, xs = cell
            reference_cell = ref_img[ys, xs]
            without_cell = without_img[ys, xs]
            prediction_cell = pred_img[ys, xs]
            mask = changed_mask(without_cell, reference_cell)
            if mask.any():
                noop_error = mse(reference_cell, input_img[ys, xs], mask)
                prediction_error = mse(reference_cell, prediction_cell, mask)
                expected_scores.append(normalized_improvement(noop_error, prediction_error))
                visibly_scorable_endpoints += 1
            else:
                # The semantic label is retained as a coverage diagnostic, but
                # a visually absent endpoint cannot identify model behavior.
                expected_scores.append(clamp(node_fidelities.get(chart_id, 0.0)))

        for chart_id in set(chart_ids) - expected:
            cell = chart_to_cell.get(chart_id)
            if cell is None:
                continue
            ys, xs = cell
            reference_cell = ref_img[ys, xs]
            prediction_cell = pred_img[ys, xs]
            preserved_scores.append(clamp(1.0 - mae(reference_cell, prediction_cell) / 64.0))

    expected_fidelity = float(np.mean(expected_scores)) if expected_scores else 1.0
    nonaffected_preservation = float(np.mean(preserved_scores)) if preserved_scores else 1.0
    scope_fidelity = math.sqrt(clamp(expected_fidelity) * clamp(nonaffected_preservation))
    return {
        "relation_scope_accuracy": scope_fidelity,
        "relation_expected_edit_fidelity": expected_fidelity,
        "relation_nonaffected_preservation": nonaffected_preservation,
        "relation_label_visual_coverage": (
            visibly_scorable_endpoints / labeled_endpoints if labeled_endpoints else 1.0
        ),
        "relation_labeled_endpoint_count": labeled_endpoints,
    }


def low_level_score(ops, code, edit_visual_score, preservation_score, counterfactual_scores=None):
    counterfactual_scores = counterfactual_scores or {}
    edit_scores = []
    preserve_scores = []
    per_op = []
    counterfactual_used = 0
    for index, op in enumerate(ops):
        name = op.get("operation", "")
        evidence = None
        if name in PRESERVE_OPS:
            score = preservation_score
            preserve_scores.append(score)
            visual_source = "preservation_region"
            visual_details = {}
        else:
            visual_details = counterfactual_scores.get(index, {})
            score = visual_details.get("visual_score", edit_visual_score)
            visual_source = visual_details.get("source", "global_edit_fallback")
            counterfactual_used += int(visual_source == "operation_counterfactual")
            evidence = code_evidence_for_operation(op, code)
            edit_scores.append(score)
        per_op.append(
            {
                "operation_index": index + 1,
                "operation": name,
                "score": score,
                "visual_source": visual_source,
                "code_evidence_diagnostic_only": evidence,
                **{key: value for key, value in visual_details.items() if key not in {"visual_score", "source"}},
            }
        )
    return {
        "low_level_edit_accuracy": float(np.mean(edit_scores)) if edit_scores else edit_visual_score,
        "preserve_operation_accuracy": float(np.mean(preserve_scores)) if preserve_scores else preservation_score,
        "operation_scores": per_op,
        "counterfactual_operation_count": counterfactual_used,
        "scorable_edit_operation_count": len(edit_scores),
        "counterfactual_coverage": counterfactual_used / len(edit_scores) if edit_scores else 1.0,
    }


def try_charteditor_structural(input_img, ref_img, pred_img, edit_mask):
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import evaluate_multichart_outputs_charteditor_style as ce

        input_u8 = input_img.astype(np.uint8)
        ref_u8 = ref_img.astype(np.uint8)
        pred_u8 = pred_img.astype(np.uint8)
        full = ce.metric_pair(input_u8, ref_u8, pred_u8)
        edit = ce.metric_pair(input_u8, ref_u8, pred_u8, roi_mask=edit_mask)
        return {
            "charteditor_full_rarm": full["rarm"],
            "charteditor_edit_rarm": edit["rarm"],
            "charteditor_full_layout": full["layout"]["score"],
            "charteditor_full_text": full["text"]["score"],
            "charteditor_edit_layout": edit["layout"]["score"],
            "charteditor_edit_text": edit["text"]["score"],
        }
    except Exception:
        return {
            "charteditor_full_rarm": None,
            "charteditor_edit_rarm": None,
            "charteditor_full_layout": None,
            "charteditor_full_text": None,
            "charteditor_edit_layout": None,
            "charteditor_edit_text": None,
        }


def evaluate_one(
    reference_root,
    prediction_root,
    task,
    render_status_by_task=None,
    include_charteditor_proxy=False,
):
    tid = task["task_id"]
    ref_dir = reference_root / "samples" / tid
    pred_dir = prediction_root / tid
    code_path = pred_dir / "target_code.py"
    pred_image_path = pred_dir / "target_image.png"
    if not pred_image_path.exists():
        alt = pred_dir / "target.png"
        if alt.exists():
            pred_image_path = alt

    edit_program = read_json(ref_dir / "edit_program.json", default={"operations": []})
    evaluation_label = read_json(ref_dir / "evaluation_label.json", default={})
    ops = edit_program.get("operations", [])
    code = safe_read_code(code_path)
    image_ok, image_status = image_valid(pred_image_path)
    render_info = (render_status_by_task or {}).get(tid, {})
    render_status = render_info.get("status")
    render_returncode = render_info.get("returncode")
    if render_status_by_task is None or tid not in render_status_by_task:
        render_ok = image_ok
    else:
        render_ok = render_status == "ok"
    code_exists = code_path.exists()
    code_executability = 1.0 if code_exists and image_ok and render_ok else 0.0
    image_valid_score = 1.0 if image_ok else 0.0
    code_quality = code_quality_score(code, image_valid_score)

    base = {
        **task,
        "code_exists": int(code_exists),
        "pred_image_exists": int(pred_image_path.exists()),
        "pred_image_status": image_status,
        "render_status": render_status,
        "render_returncode": render_returncode,
        "code_executability": code_executability,
        "code_quality": code_quality,
        "explicit_relation_label_available": int(
            bool(evaluation_label.get("relation_label_version"))
        ),
    }
    if code_executability < 1.0:
        base.update(
            {
                "low_level_edit_accuracy": 0.0,
                "relation_conditioned_fidelity": (
                    0.0 if task.get("instruction_type") in RELATION_TYPES else None
                ),
                "relation_scope_f1": (
                    0.0 if task.get("instruction_type") in RELATION_TYPES else None
                ),
                "relation_scope_accuracy": (
                    0.0 if task.get("instruction_type") in RELATION_TYPES else None
                ),
                "multi_chart_relation_accuracy": (
                    0.0 if task.get("instruction_type") in RELATION_TYPES else None
                ),
                "relation_edge_consistency": (
                    0.0 if task.get("instruction_type") in RELATION_TYPES else None
                ),
                "relation_edge_action_accuracy": (
                    0.0 if task.get("instruction_type") in RELATION_TYPES else None
                ),
                "relation_edge_endpoint_accuracy": (
                    0.0 if task.get("instruction_type") in RELATION_TYPES else None
                ),
                "visual_structural_similarity": 0.0,
                "preservation_accuracy": 0.0,
                "high_level_score": 0.0,
                "overall_score": 0.0,
                "relation_metric_applicable": int(task.get("instruction_type") in RELATION_TYPES),
                "operation_scores_json": json.dumps([], ensure_ascii=False),
            }
        )
        return base

    ref_image = Image.open(ref_dir / "target_image.png").convert("RGB")
    size = ref_image.size
    metric_size = bounded_metric_size(size)
    pred_native = Image.open(pred_image_path).convert("RGB")
    ref_aspect = size[0] / max(size[1], 1)
    pred_aspect = pred_native.width / max(pred_native.height, 1)
    canvas_aspect_score = clamp(math.exp(-4.0 * abs(math.log(max(pred_aspect, 1e-9) / ref_aspect))))
    input_img = load_rgb(ref_dir / "input_image.png", size=metric_size)
    ref_img = load_rgb(ref_dir / "target_image.png", size=metric_size)
    pred_img = load_rgb(pred_image_path, size=metric_size)

    edit_mask = changed_mask(input_img, ref_img)
    preserve_mask = ~edit_mask
    full_ssim = standard_ssim(ref_img, pred_img)
    noop_full_ssim = standard_ssim(ref_img, input_img)
    full_ssim_improvement = normalized_similarity_improvement(noop_full_ssim, full_ssim)
    noop_edit_mse = mse(ref_img, input_img, edit_mask)
    pred_edit_mse = mse(ref_img, pred_img, edit_mask)
    edit_visual_score = normalized_improvement(noop_edit_mse, pred_edit_mse)
    # The target render is the preservation reference. Small anti-aliasing or
    # layout differences below the edit-mask threshold must not penalize a
    # perfect oracle that exactly matches the target image.
    preserve_mae = mae(ref_img, pred_img, preserve_mask)
    preserve_delta = np.max(np.abs(ref_img - pred_img), axis=2)
    preserve_changed_rate = float((preserve_delta[preserve_mask] > 24).mean()) if preserve_mask.any() else 0.0
    preservation_accuracy = clamp(
        0.70 * (1.0 - preserve_changed_rate) + 0.30 * (1.0 - preserve_mae / 64.0)
    )
    full_mse = mse(ref_img, pred_img)
    full_mae = mae(ref_img, pred_img)

    chart_count = int(task.get("chart_count", 1))
    reference_spec = extract_reference_spec(ref_dir / "target_code.py")
    layout_id = (reference_spec.get("layout_template") or {}).get("layout_id", "regular_grid")
    chart_ids = [
        chart.get("chart_id", f"chart_{index + 1}")
        for index, chart in enumerate(reference_spec.get("charts", []))
    ] or [f"chart_{index + 1}" for index in range(chart_count)]
    relation_applicable = task.get("instruction_type") in RELATION_TYPES
    explicit_affected = (
        evaluation_label.get("expected_affected_charts_union")
        if relation_applicable and evaluation_label.get("relation_label_version")
        else None
    )
    (
        affected_f1,
        affected_precision,
        affected_recall,
        ref_cells,
        pred_cells,
        matched_cells,
        reference_affected_ids,
        predicted_affected_ids,
    ) = affected_cell_f1(
        input_img,
        ref_img,
        pred_img,
        chart_count,
        layout_id,
        chart_ids=chart_ids,
        expected_affected_chart_ids=explicit_affected,
    )
    affected_similarity = affected_region_similarity(
        input_img, ref_img, pred_img, chart_count, layout_id
    )
    edge_labels = (
        evaluation_label.get("expected_relation_edges_union", [])
        if relation_applicable
        else []
    )
    node_fidelities = chart_target_fidelities(
        input_img,
        ref_img,
        pred_img,
        chart_count,
        layout_id,
        chart_ids,
    )
    (
        relation_edge_score,
        relation_edge_action,
        relation_edge_endpoint,
    ) = relation_edge_consistency(
        edge_labels,
        node_fidelities,
    )
    relation_scope = (
        relation_scope_fidelity(
            ref_dir,
            input_img,
            ref_img,
            pred_img,
            metric_size,
            chart_count,
            layout_id,
            chart_ids,
            evaluation_label,
            node_fidelities,
        )
        if relation_applicable
        else None
    )
    relation_conditioned_fidelity = (
        clamp(0.60 * relation_scope["relation_scope_accuracy"] + 0.40 * relation_edge_score)
        if relation_applicable and relation_edge_score is not None
        else relation_scope["relation_scope_accuracy"]
        if relation_applicable
        else None
    )

    structural = (
        try_charteditor_structural(input_img, ref_img, pred_img, edit_mask)
        if include_charteditor_proxy
        else {
            "charteditor_full_rarm": None,
            "charteditor_edit_rarm": None,
            "charteditor_full_layout": None,
            "charteditor_full_text": None,
            "charteditor_edit_layout": None,
            "charteditor_edit_text": None,
        }
    )
    visual_structural = clamp(
        canvas_aspect_score
        * (0.60 * edit_visual_score + 0.40 * full_ssim_improvement)
    )

    per_operation_visual = operation_counterfactual_scores(
        ref_dir, input_img, ref_img, pred_img, metric_size, edit_visual_score
    )
    low = low_level_score(
        ops,
        code,
        edit_visual_score,
        preservation_accuracy,
        counterfactual_scores=per_operation_visual,
    )
    low_level = low["low_level_edit_accuracy"]
    preservation_final = preservation_accuracy

    weights = RELATION_WEIGHTS if relation_applicable else NON_RELATION_WEIGHTS
    high_level_weight = weights["high_level_score"]
    task_fidelity = (
        0.50 * (relation_conditioned_fidelity or 0.0) + 0.50 * visual_structural
        if relation_applicable
        else visual_structural
    )
    high_level_score = math.sqrt(clamp(task_fidelity) * clamp(preservation_final))
    overall = (
        weights["low_level_edit_accuracy"] * low_level
        + high_level_weight * high_level_score
    )
    overall *= code_executability

    base.update(
        {
            "overall_score": overall,
            "low_level_edit_accuracy": low_level,
            "high_level_score": high_level_score,
            "relation_conditioned_fidelity": relation_conditioned_fidelity,
            "multi_chart_relation_accuracy": relation_conditioned_fidelity,
            "relation_scope_f1": affected_f1 if relation_applicable else None,
            "relation_scope_accuracy": (
                relation_scope["relation_scope_accuracy"] if relation_scope else None
            ),
            "relation_expected_edit_fidelity": (
                relation_scope["relation_expected_edit_fidelity"] if relation_scope else None
            ),
            "relation_nonaffected_preservation": (
                relation_scope["relation_nonaffected_preservation"] if relation_scope else None
            ),
            "relation_label_visual_coverage": (
                relation_scope["relation_label_visual_coverage"] if relation_scope else None
            ),
            "relation_labeled_endpoint_count": (
                relation_scope["relation_labeled_endpoint_count"] if relation_scope else None
            ),
            "visual_structural_similarity": visual_structural,
            "preservation_accuracy": preservation_final,
            "full_ssim": full_ssim,
            "noop_full_ssim": noop_full_ssim,
            "full_ssim_improvement": full_ssim_improvement,
            "full_mse": full_mse,
            "full_mae": full_mae,
            "edit_visual_score": edit_visual_score,
            "noop_edit_mse": noop_edit_mse,
            "pred_edit_mse": pred_edit_mse,
            "preserve_mae": preserve_mae,
            "preserve_changed_pixel_rate": preserve_changed_rate,
            "affected_chart_f1": affected_f1,
            "affected_chart_precision": affected_precision,
            "affected_chart_recall": affected_recall,
            "reference_affected_cells": ref_cells,
            "predicted_affected_cells": pred_cells,
            "matched_affected_cells": matched_cells,
            "affected_region_similarity": affected_similarity,
            "reference_affected_chart_ids_json": json.dumps(
                reference_affected_ids, ensure_ascii=False
            ),
            "predicted_affected_chart_ids_json": json.dumps(
                predicted_affected_ids, ensure_ascii=False
            ),
            "relation_edge_consistency": relation_edge_score,
            "relation_edge_action_accuracy": relation_edge_action,
            "relation_edge_endpoint_accuracy": relation_edge_endpoint,
            "relation_edge_check_count": len(edge_labels),
            "relation_node_fidelities_json": json.dumps(
                node_fidelities, ensure_ascii=False, sort_keys=True
            ),
            "explicit_relation_label_available": int(
                bool(evaluation_label.get("relation_label_version"))
            ),
            "relation_metric_applicable": int(relation_applicable),
            "layout_id": layout_id,
            "canvas_aspect_score": canvas_aspect_score,
            "metric_width": metric_size[0],
            "metric_height": metric_size[1],
            "target_changed_pixel_rate": float(edit_mask.mean()),
            "operation_count": len(ops),
            "counterfactual_operation_count": low["counterfactual_operation_count"],
            "scorable_edit_operation_count": low["scorable_edit_operation_count"],
            "counterfactual_coverage": low["counterfactual_coverage"],
            "operation_scores_json": json.dumps(low["operation_scores"], ensure_ascii=False),
            **structural,
        }
    )
    return base


def summarize(rows):
    numeric_keys = [
        "overall_score",
        "code_executability",
        "low_level_edit_accuracy",
        "high_level_score",
        "multi_chart_relation_accuracy",
        "relation_conditioned_fidelity",
        "relation_scope_f1",
        "relation_scope_accuracy",
        "relation_expected_edit_fidelity",
        "relation_nonaffected_preservation",
        "relation_label_visual_coverage",
        "relation_edge_consistency",
        "relation_edge_action_accuracy",
        "relation_edge_endpoint_accuracy",
        "visual_structural_similarity",
        "preservation_accuracy",
        "code_quality",
        "full_ssim",
        "edit_visual_score",
        "affected_chart_f1",
    ]
    summary = {
        "sample_count": len(rows),
        "scoring_version": "v3.1_operation_counterfactual_explicit_relation_execution_gated",
        "relation_sample_weights": RELATION_WEIGHTS,
        "non_relation_sample_weights": NON_RELATION_WEIGHTS,
        "code_quality_role": "diagnostic_only_not_in_overall_score",
        "valid_predictions": sum(1 for row in rows if row.get("code_executability") == 1.0),
        "relation_sample_count": sum(
            1 for row in rows if row.get("instruction_type") in RELATION_TYPES
        ),
        "explicit_relation_label_count": sum(
            1
            for row in rows
            if row.get("instruction_type") in RELATION_TYPES
            and row.get("explicit_relation_label_available") == 1
        ),
    }
    for key in numeric_keys:
        vals = [row.get(key) for row in rows if isinstance(row.get(key), (int, float))]
        summary[f"mean_{key}"] = float(np.mean(vals)) if vals else None
        summary[f"median_{key}"] = float(np.median(vals)) if vals else None

    def group_by(key):
        def mean_numeric(selected, metric):
            values = [
                row.get(metric)
                for row in selected
                if isinstance(row.get(metric), (int, float))
            ]
            return float(np.mean(values)) if values else None

        out = {}
        for value in sorted({str(row.get(key, "")) for row in rows}):
            selected = [row for row in rows if str(row.get(key, "")) == value]
            out[value] = {
                "count": len(selected),
                "mean_overall_score": mean_numeric(selected, "overall_score"),
                "mean_code_executability": mean_numeric(selected, "code_executability"),
                "mean_low_level_edit_accuracy": mean_numeric(selected, "low_level_edit_accuracy"),
                "mean_high_level_score": mean_numeric(selected, "high_level_score"),
                "mean_multi_chart_relation_accuracy": mean_numeric(
                    selected, "multi_chart_relation_accuracy"
                ),
                "mean_relation_conditioned_fidelity": mean_numeric(
                    selected, "relation_conditioned_fidelity"
                ),
                "mean_relation_scope_f1": mean_numeric(selected, "relation_scope_f1"),
                "mean_relation_scope_accuracy": mean_numeric(selected, "relation_scope_accuracy"),
                "mean_relation_edge_consistency": mean_numeric(
                    selected, "relation_edge_consistency"
                ),
                "mean_preservation_accuracy": mean_numeric(selected, "preservation_accuracy"),
            }
        return out

    summary["by_split"] = group_by("split")
    summary["by_instruction_type"] = group_by("instruction_type")
    summary["by_chart_count"] = group_by("chart_count")
    summary["by_propagation_scope"] = group_by("propagation_scope")
    summary["operation_distribution"] = dict(
        Counter(op for row in rows for op in str(row.get("operations", "")).split(";") if op)
    )
    return summary


def write_csv(path, rows):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row.keys()})
    preferred = [
        "task_id",
        "global_sample_id",
        "split",
        "instruction_type",
        "chart_count",
        "operations",
        "overall_score",
        "code_executability",
        "low_level_edit_accuracy",
        "high_level_score",
        "multi_chart_relation_accuracy",
        "relation_conditioned_fidelity",
        "relation_scope_f1",
        "relation_edge_consistency",
        "visual_structural_similarity",
        "preservation_accuracy",
        "code_quality",
    ]
    fieldnames = preferred + [key for key in fieldnames if key not in preferred]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def evaluate_job(job):
    reference_root, prediction_root, task, render_status_by_task, include_proxy = job
    return evaluate_one(
        reference_root,
        prediction_root,
        task,
        render_status_by_task,
        include_charteditor_proxy=include_proxy,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--prediction-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--task-ids-file",
        type=Path,
        help="Optional newline-delimited task IDs to evaluate in reference task order.",
    )
    parser.add_argument(
        "--include-charteditor-proxy",
        action="store_true",
        help="Compute the slower OCR-free ChartEditor-style diagnostic proxy.",
    )
    args = parser.parse_args()

    tasks = read_json(args.reference_root / "tasks.json", default=[])
    if args.task_ids_file:
        selected_ids = {
            line.strip()
            for line in args.task_ids_file.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        }
        tasks = [task for task in tasks if task.get("task_id") in selected_ids]
        found_ids = {task.get("task_id") for task in tasks}
        missing_ids = sorted(selected_ids - found_ids)
        if missing_ids:
            raise SystemExit(
                f"{len(missing_ids)} selected task IDs are missing from the reference: "
                + ", ".join(missing_ids[:10])
            )
    if args.limit is not None:
        tasks = tasks[: args.limit]
    args.output_root.mkdir(parents=True, exist_ok=True)
    render_log = read_json(args.prediction_root / "render_log.json", default=[])
    render_status_by_task = {row.get("task_id"): row for row in render_log if isinstance(row, dict)}
    jobs = [
        (
            args.reference_root,
            args.prediction_root,
            task,
            render_status_by_task,
            args.include_charteditor_proxy,
        )
        for task in tasks
    ]
    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            rows = list(executor.map(evaluate_job, jobs, chunksize=1))
    else:
        rows = [evaluate_job(job) for job in jobs]
    summary = summarize(rows)
    summary.update(
        {
            "reference_root": str(args.reference_root.resolve()),
            "prediction_root": str(args.prediction_root.resolve()),
            "output_root": str(args.output_root.resolve()),
            "charteditor_proxy_included": bool(args.include_charteditor_proxy),
            "workers": int(args.workers),
        }
    )

    write_csv(args.output_root / "metrics_per_sample.csv", rows)
    write_json(args.output_root / "metrics_per_sample.json", rows)
    write_json(args.output_root / "metrics_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
