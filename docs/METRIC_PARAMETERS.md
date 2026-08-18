# Evaluation Metrics and Frozen Parameters

Execution is a gate: a failed program receives zero on all primary metrics. Successful renders are compared with the input image `I` and reference target `T`, using the input as a no-op baseline.

## Components

- **Low-level edit score (`L`)**: mean operation-level improvement on counterfactual supports. Each support is obtained by rendering a target that omits one requested operation while retaining the others.
- **Preservation (`P`)**: combines the proportion of visibly changed preserved pixels with preserved-region mean absolute error.
- **Scope fidelity**: geometric mean of edit fidelity on affected endpoint-operation pairs and preservation on the remaining pairs.
- **Edge consistency (`C_e`)**: geometric mean of endpoint fidelities for each activated relation edge.
- **Relation-conditioned fidelity (`R`)**: combines scope fidelity and mean edge consistency.
- **Structural fidelity (`S`)**: combines no-op-normalized changed-region error improvement and normalized SSIM, with an aspect-ratio penalty.
- **High-level score (`H`)**: geometric mean of task fidelity and preservation.
- **Overall**: execution-gated mixture of low- and high-level scores, with separate weights for ordinary and relation-aware tasks.

## Parameterized definitions

```text
M_o = {j : max_c |T[j,c] - T_without_o[j,c]| > tau}
P   = alpha_P (1 - r_tau) + (1 - alpha_P) (1 - MAE_P / kappa)
R   = alpha_R S_scope + (1 - alpha_R) mean_e C_e
S   = q_aspect [alpha_S V_edit + (1 - alpha_S) V_ssim]
q_aspect = exp(-lambda_a |log(a_prediction / a_reference)|)
Q   = S                                      ordinary task
Q   = alpha_Q R + (1 - alpha_Q) S           relation-aware task
H   = sqrt(Q P)
Overall = alpha_ord L + (1-alpha_ord) H      ordinary task
Overall = alpha_rel L + (1-alpha_rel) H      relation-aware task
```

All bounded components are clipped to `[0, 1]` where applicable.

## Frozen values

| Parameter | Value | Role |
|---|---:|---|
| `tau` | 24 | visible-change threshold in 8-bit RGB units |
| `kappa` | 64 | preserved-region MAE scale in 8-bit RGB units |
| `lambda_a` | 4 | aspect-ratio drift penalty |
| `alpha_P` | 0.70 | changed-pixel coverage weight in preservation |
| `alpha_R` | 0.60 | explicit scope weight in relation fidelity |
| `alpha_S` | 0.60 | changed-region improvement weight in structural fidelity |
| `alpha_Q` | 0.50 | relation/structure balance for relation-aware tasks |
| `alpha_rel` | 0.35 | low-level weight in relation-aware Overall |
| `alpha_ord` | 0.45 | low-level weight in ordinary Overall |
| `epsilon` | 1e-9 | numerical stabilizer |

The thresholds separate visible edits from small rasterization differences and bound preserved-region intensity error. The mixture weights emphasize affected-area coverage, explicit scope, no-op-normalized edit fidelity, and high-level task completion while retaining complementary evidence. These are evaluator design parameters rather than values calibrated against human semantic ratings. Controlled fixtures verify the expected directions for no-op, oracle, input-target blends, missing relation endpoints, preserved-panel corruption, layout displacement, and background tinting.
