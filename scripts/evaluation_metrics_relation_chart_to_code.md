# Relation-aware Multi-chart Chart-to-Code Editing Evaluation

## Task

Input: one multi-chart/dashboard image and a natural-language edit instruction.

Output: executable Python code. The code must render the edited dashboard and save `target_image.png`.

The model does not receive the original chart code. `target_code.py`, `target_image.png`, `edit_program.json`, and `evaluation_label.json` are reference/evaluation artifacts only.

## Overall Score

The recommended overall score is:

```text
Overall =
0.10 * Code Executability
+ 0.25 * Low-level Edit Accuracy
+ 0.20 * Multi-chart Relation Accuracy
+ 0.20 * Visual-Structural Similarity
+ 0.15 * Preservation Accuracy
+ 0.10 * Code Quality
```

Report the six components separately, not only the final score.

## 1. Code Executability

Measures whether the predicted chart code can be used as code.

Subcriteria:

- predicted `target_code.py` exists
- code runs without error within the timeout
- code saves a valid non-empty `target_image.png`
- generated image has reasonable size and non-blank content

The script reports `code_executability` in `[0, 1]`.

## 2. Low-level Edit Accuracy

Measures whether the concrete requested operations are completed.

The evaluator reads `edit_program.json` and scores operations such as:

- `add_dashboard_title`
- `change_axis_label`
- `rename_label`
- `modify_color`
- `delete_category_or_series`
- `add_reference_line`
- `change_chart_type`
- `modify_style`
- `add_event_marker`
- `add_trend_line`
- `filter_time_range`
- `set_y_scale`

The implementation combines:

- static evidence from generated code, such as required labels, titles, colors, and plotting APIs
- edit-region visual agreement between `pred_image` and `target_image`

Preservation-only operations are handled in the preservation component.

## 3. Multi-chart Relation Accuracy

This is the benchmark-specific metric.

It measures whether the model understands which subplots are semantically linked and applies edits with the correct scope.

Subcriteria:

- affected subplot F1: predicted changed subplot set vs. reference changed subplot set
- relation edit similarity: similarity inside the affected subplot regions
- scope precision / unaffected preservation: unrelated subplots should not be changed

This is especially important for `multi_chart_relation` and `complex_relation` samples.

Examples:

- the same visible label must be renamed across all related subplots
- the same category must be recolored across all related subplots
- a reference line must be added only to comparable numeric-y subplots
- maps, pies, sankey, radar, treemap, and distribution-only plots should be preserved unless explicitly targeted

## 4. Visual-Structural Similarity

Measures how close the rendered prediction is to the reference render.

The script combines:

- full-image SSIM
- edit-region improvement over the no-edit input baseline
- ChartEditor-style layout/text component matching proxy when OpenCV/SciPy are available

This avoids relying on pixel MSE alone.

## 5. Preservation Accuracy

Measures whether content not requested by the instruction remains unchanged.

The evaluator compares the prediction against the original input image on regions that the reference answer did not change.

This penalizes over-editing and hallucinated changes in unrelated subplots.

## 6. Code Quality

Measures whether the output is usable, reproducible chart code.

Subcriteria:

- contains executable plotting code
- saves `target_image.png`
- avoids absolute local paths
- avoids network / shell / destructive operations
- is not trivially short or empty
- has basic deterministic behavior

This component has lower weight because the primary objective is correct chart editing.

## Recommended Reporting

For the paper, report:

- `overall_score`
- `code_executability`
- `low_level_edit_accuracy`
- `multi_chart_relation_accuracy`
- `visual_structural_similarity`
- `preservation_accuracy`
- `code_quality`

Also provide breakdowns by:

- real vs. synthetic
- instruction type: `single_step`, `multi_step`, `multi_chart_relation`, `complex_relation`
- chart count: 2 to 7 subplots
- operation type
- chart type

