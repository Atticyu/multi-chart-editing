# Auto-generated reference code for the relation-aware multi-chart chart-to-code benchmark.
# The model-facing task is to generate edited chart code; rendered images are evaluation artifacts only.

import json
import math
import os
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch
import numpy as np
import pandas as pd


DATA_POOL_ROOT = Path(os.environ.get("REAL_DATA_POOL_ROOT", Path(__file__).resolve().parents[3] / "real_data_pool_v3"))


def _to_num(series):
    return pd.to_numeric(series, errors="coerce")


def _to_axis_values(series):
    numeric = _to_num(series)
    if numeric.notna().sum() >= max(3, int(len(series) * 0.2)):
        return numeric
    dates = pd.to_datetime(series, errors="coerce")
    if dates.notna().sum() >= max(3, int(len(series) * 0.2)):
        return dates.dt.year.astype(float)
    return numeric


def _pretty(text):
    text = str(text).replace("_", " ")
    return text[:1].upper() + text[1:]


def _apply_filters(df, filters):
    out = df.copy()
    for flt in filters:
        field = flt.get("field")
        if field not in out.columns:
            continue
        op = flt.get("operator")
        if op == "in":
            values = [str(v) for v in flt.get("values", [])]
            out = out[out[field].astype(str).isin(values)]
        elif op == "range":
            mask = pd.Series(True, index=out.index)
            values = _to_num(out[field])
            if values.notna().sum() < max(3, int(len(out) * 0.2)):
                dates = pd.to_datetime(out[field], errors="coerce")
                if dates.notna().sum() >= max(3, int(len(out) * 0.2)):
                    values = dates.dt.year.astype(float)
            if "min" in flt:
                mask = mask & (values >= float(flt["min"]))
            if "max" in flt:
                mask = mask & (values <= float(flt["max"]))
            out = out[mask]
    return out


def _chart_mentions_target(chart, target):
    target = str(target)
    for flt in chart.get("filters", []):
        if target in [str(v) for v in flt.get("values", [])]:
            return True
    for value in chart.get("encodings", {}).values():
        if value is not None and str(value) == target:
            return True
    return False


def _ops_for_chart(chart, operations):
    selected = []
    for op in operations:
        name = op.get("operation")
        scope = op.get("scope", "")
        target = op.get("target")
        if name in {"preserve_data_values"}:
            selected.append(op)
        elif scope == "chart_id" and op.get("chart_id") == chart.get("chart_id"):
            selected.append(op)
        elif scope == "dataset_only" and op.get("dataset_id") == chart.get("data_source", {}).get("dataset_id"):
            selected.append(op)
        elif scope == "relation_tag" and op.get("relation_tag") in chart.get("relation_tags", []):
            selected.append(op)
        elif scope == "all_charts":
            selected.append(op)
        elif scope == "numeric_y_charts" and chart.get("chart_type") in {
            "line", "multi_line", "step_line", "area", "stacked_area", "bar",
            "horizontal_bar", "grouped_bar", "stacked_bar", "stacked_horizontal_bar",
            "proportional_bar", "lollipop", "dot_plot", "waterfall", "scatter",
            "bubble", "hexbin", "contour_density", "box", "violin", "strip_plot",
            "error_bar", "dual_axis_line_bar",
        }:
            selected.append(op)
        elif scope == "time_series_charts":
            x = chart.get("encodings", {}).get("x")
            x_values = x if isinstance(x, list) else [x]
            if any(
                token in str(value).lower()
                for value in x_values
                for token in ("year", "date", "time")
            ):
                selected.append(op)
        elif scope in {
            "charts_where_field_or_category_appears",
            "charts_where_label_appears",
        }:
            # Category-value applicability is resolved against each chart's
            # loaded data; selecting here lets the plotting function apply the
            # edit only when the target label is actually present.
            selected.append(op)
        elif target and _chart_mentions_target(chart, target):
            selected.append(op)
        elif name == "preserve_unrelated_charts":
            selected.append(op)
    return selected


def _apply_data_ops(df, chart, operations):
    out = df.copy()
    object_cols = [c for c in out.columns if out[c].dtype == object or str(out[c].dtype).startswith("string")]
    for op in _ops_for_chart(chart, operations):
        name = op.get("operation")
        target = op.get("target")
        if name == "delete_category_or_series" and target is not None:
            mask = pd.Series(False, index=out.index)
            for col in object_cols:
                mask = mask | (out[col].astype(str) == str(target))
            out = out[~mask]
        elif name == "rename_label" and target is not None:
            new_label = str(op.get("new_label", target))
            for col in object_cols:
                out[col] = out[col].astype(str).replace(str(target), new_label)
        elif name == "filter_time_range":
            x = _field(chart.get("encodings", {}).get("x"), out)
            if x and x in out.columns:
                values = _to_axis_values(out[x])
                mask = pd.Series(True, index=out.index)
                if "min" in op:
                    mask = mask & (values >= float(op["min"]))
                if "max" in op:
                    mask = mask & (values <= float(op["max"]))
                out = out[mask]
        elif name == "adjust_top_k":
            enc = chart.get("encodings", {})
            cat = _field(enc.get("x") or enc.get("color_by") or enc.get("group_by"), out)
            y = _field(enc.get("y"), out)
            if isinstance(y, list):
                y = _field(y, out)
            if cat and cat in out.columns and y and y in out.columns:
                temp = out[[cat, y]].copy()
                temp[y] = _to_num(temp[y])
                ranked = temp.dropna().groupby(cat)[y].mean().sort_values(ascending=False)
                keep = ranked.head(int(op.get("k", 5))).index.astype(str).tolist()
                out = out[out[cat].astype(str).isin(keep)]
        elif name == "adjust_rolling_window":
            enc = chart.get("encodings", {})
            x = _field(enc.get("x"), out)
            y = _field(enc.get("y"), out)
            if isinstance(y, list):
                y = _field(y, out)
            group = _field(enc.get("color_by") or enc.get("group_by"), out)
            if x and x in out.columns and y and y in out.columns:
                out = out.copy()
                out[x] = _to_axis_values(out[x])
                out[y] = _to_num(out[y])
                out = out.dropna(subset=[x, y]).sort_values(x)
                window = int(op.get("window", 5))
                if group and group in out.columns:
                    out[y] = out.groupby(group, group_keys=False)[y].transform(lambda s: s.rolling(window, min_periods=1).mean())
                else:
                    out[y] = out[y].rolling(window, min_periods=1).mean()
    return out


def _apply_chart_data_transform(df, chart):
    transform = chart.get("data_transform", {}) or {}
    transform_id = transform.get("transform_id", "identity")
    if transform_id == "identity":
        return df

    out = df.copy()
    if transform_id == "top_k_by_measure":
        cat = _field(transform.get("category"), out)
        measure = _field(transform.get("measure"), out)
        if not cat or cat not in out.columns or not measure or measure not in out.columns:
            return out
        temp = out[[cat, measure]].copy()
        temp[measure] = _to_num(temp[measure])
        ranked = temp.dropna().groupby(cat)[measure].mean().sort_values(ascending=False)
        keep = ranked.head(int(transform.get("k", 8))).index.astype(str).tolist()
        return out[out[cat].astype(str).isin(keep)].copy()

    if transform_id == "rolling_mean":
        x = _field(transform.get("x"), out)
        measure = _field(transform.get("measure"), out)
        group = _field(transform.get("group_by"), out)
        if not x or x not in out.columns or not measure or measure not in out.columns:
            return out
        out[x] = _to_axis_values(out[x])
        out[measure] = _to_num(out[measure])
        out = out.dropna(subset=[x, measure]).sort_values(x)
        window = int(transform.get("window", 3))
        if group and group in out.columns:
            out[measure] = out.groupby(group, group_keys=False)[measure].transform(lambda s: s.rolling(window, min_periods=1).mean())
        else:
            out[measure] = out[measure].rolling(window, min_periods=1).mean()
        return out

    if transform_id == "normalize_measure":
        measure = _field(transform.get("measure"), out)
        if not measure or measure not in out.columns:
            return out
        values = _to_num(out[measure])
        method = transform.get("method", "minmax")
        if method == "zscore":
            std = values.std()
            if std and np.isfinite(std) and std > 0:
                out[measure] = (values - values.mean()) / std
        else:
            span = values.max() - values.min()
            if span and np.isfinite(span) and span > 0:
                out[measure] = (values - values.min()) / span
        return out

    return out


def _target_color_map(chart, operations):
    cmap = {}
    chart_ops = _ops_for_chart(chart, operations)
    for op in chart_ops:
        if op.get("operation") == "modify_color" and op.get("target") is not None:
            label = str(op["target"])
            for rename in chart_ops:
                if rename.get("operation") == "rename_label" and str(rename.get("target")) == label:
                    label = str(rename.get("new_label", label))
            cmap[label] = op.get("color", "red")
    return cmap


def _style_flags(operations):
    return any(op.get("operation") == "modify_style" for op in operations)


def _palette(labels, color_map):
    base = list(plt.get_cmap("tab20").colors) + list(plt.get_cmap("Set2").colors)
    colors = {}
    for i, label in enumerate(labels):
        label = str(label)
        colors[label] = color_map.get(label, base[i % len(base)])
    return colors


def _stable_top_labels(series, n):
    """Return frequent labels with an explicit deterministic tie break."""
    counts = series.astype(str).value_counts(sort=False)
    ranked = sorted(
        ((str(label), int(count)) for label, count in counts.items()),
        key=lambda item: (-item[1], item[0]),
    )
    return [label for label, _ in ranked[: int(n)]]


def _small(df, n=5000):
    if len(df) <= n:
        return df
    return df.sample(n=n, random_state=7)


def _template(chart):
    return chart.get("visual_template", {}) or {}


def _tget(chart, key, default=None):
    return _template(chart).get(key, default)


def _theme(chart):
    return chart.get("_style_theme", {}) or {}


def _theme_dark(chart):
    return _theme(chart).get("theme_id") == "dark_monitoring"


def _axis_text_color(chart):
    return "#E5E7EB" if _theme_dark(chart) else "#111827"


def _grid_color(chart):
    return "#CBD5E1" if _theme_dark(chart) else "#94A3B8"


def _apply_axis_theme(ax, chart, style_modified=False):
    theme = _theme(chart)
    ax.set_facecolor(theme.get("axes_facecolor", "white"))
    text_color = _axis_text_color(chart)
    spine_policy = theme.get("spine_policy", "standard")
    for side, spine in ax.spines.items():
        spine.set_color("#CBD5E1" if _theme_dark(chart) else "#374151")
        spine.set_linewidth(0.8)
        if spine_policy in {"left_bottom", "minimal"} and side in {"top", "right"}:
            spine.set_visible(False)
        if spine_policy == "minimal" and side in {"top", "right"}:
            spine.set_visible(False)
    ax.tick_params(colors=text_color, labelsize=8)
    ax.xaxis.label.set_color(text_color)
    ax.yaxis.label.set_color(text_color)
    legend = ax.get_legend()
    if legend is not None:
        for text in legend.get_texts():
            text.set_color(text_color)
        legend.get_frame().set_facecolor(theme.get("axes_facecolor", "white"))
        legend.get_frame().set_edgecolor("none")
    grid_axis = _tget(chart, "grid_axis", "both")
    grid_alpha = float(_tget(chart, "grid_alpha", theme.get("grid_alpha", 0.18)))
    if style_modified:
        ax.grid(True, linestyle="--", alpha=max(grid_alpha, 0.30), color=_grid_color(chart))
    else:
        ax.grid(True, axis=grid_axis if grid_axis in {"x", "y", "both"} else "both", linestyle="-", alpha=grid_alpha, color=_grid_color(chart))


def _numeric_columns(df):
    cols = []
    for c in df.columns:
        if _to_num(df[c]).notna().sum() >= max(3, int(len(df) * 0.2)):
            cols.append(c)
    return cols


def _field(preferred, df=None):
    if preferred is None:
        return None
    if isinstance(preferred, (list, tuple)):
        for value in preferred:
            if df is None or value in df.columns:
                return value
        return preferred[0] if preferred else None
    return preferred


def _category_column(df, preferred):
    preferred = _field(preferred, df)
    if preferred and preferred in df.columns:
        return preferred
    for c in df.columns:
        if df[c].dtype == object and df[c].nunique(dropna=True) <= 30:
            return c
    return None


def _measure_column(df, preferred):
    preferred = _field(preferred, df)
    if preferred and preferred in df.columns:
        return preferred
    nums = _numeric_columns(df)
    return nums[0] if nums else None


def _has_visible_magnitude(values):
    arr = pd.to_numeric(pd.Series(np.asarray(values).ravel()), errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    return len(arr) > 0 and float(arr.abs().max()) > 1e-12


def _add_legend(ax, chart, labels_count, preferred="best", mode="auto"):
    if labels_count <= 0:
        return None
    fontsize = int(_tget(chart, "legend_fontsize", 7))
    if mode == "below" or labels_count >= 5 or preferred in {"lower center", "center"}:
        ncol = max(1, min(3, labels_count))
        return ax.legend(
            fontsize=fontsize,
            frameon=False,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.24),
            ncol=ncol,
            borderaxespad=0.0,
            handlelength=1.2,
            columnspacing=0.9,
        )
    if mode == "right" or labels_count >= 4:
        return ax.legend(
            fontsize=fontsize,
            frameon=False,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            borderaxespad=0.0,
        )
    return ax.legend(fontsize=fontsize, frameon=False, loc=preferred)


def _plot_line_like(ax, df, chart, kind, color_map):
    enc = chart.get("encodings", {})
    x = _field(enc.get("x"), df)
    y = _measure_column(df, enc.get("y"))
    color_by = _field(enc.get("color_by") or enc.get("group_by"), df)
    if not x or x not in df.columns or not y:
        raise ValueError(f"Insufficient data for {kind}: missing x/y encoding")
    data = df[[x, y] + ([color_by] if color_by and color_by in df.columns else [])].copy()
    data[x] = _to_axis_values(data[x])
    data[y] = _to_num(data[y])
    data = data.dropna()
    if data.empty:
        raise ValueError(f"Insufficient data for {kind}: no rows after numeric conversion")
    marker = _tget(chart, "marker", "o")
    linestyle = _tget(chart, "linestyle", "-")
    linewidth = float(_tget(chart, "linewidth", 1.8))
    markersize = float(_tget(chart, "markersize", 3))
    drawstyle = _tget(chart, "drawstyle", "default" if kind != "step_line" else "steps-post")
    legend_loc = _tget(chart, "legend_loc", "best")
    area_alpha = float(_tget(chart, "alpha", 0.28 if kind == "area" else 0.72))
    if color_by and color_by in data.columns:
        groups = list(data[color_by].astype(str).dropna().unique())[:10]
        colors = _palette(groups, color_map)
        if kind in {"stacked_area", "area"}:
            pivot = data[data[color_by].astype(str).isin(groups)].pivot_table(index=x, columns=color_by, values=y, aggfunc="mean").sort_index()
            if kind == "stacked_area":
                ax.stackplot(pivot.index, [pivot[c].fillna(0).values for c in pivot.columns], labels=[str(c) for c in pivot.columns], colors=[colors[str(c)] for c in pivot.columns], alpha=area_alpha)
            else:
                for col in pivot.columns:
                    ax.fill_between(pivot.index, pivot[col].values, alpha=area_alpha, color=colors[str(col)])
                    ax.plot(pivot.index, pivot[col].values, label=str(col), color=colors[str(col)], linewidth=linewidth, linestyle=linestyle, marker=marker, markersize=markersize, drawstyle=drawstyle)
        else:
            for label in groups:
                g = data[data[color_by].astype(str) == label].groupby(x, as_index=False)[y].mean().sort_values(x)
                ax.plot(g[x], g[y], marker=marker, markersize=markersize, linewidth=linewidth, linestyle=linestyle, label=str(label), color=colors[str(label)], drawstyle=drawstyle)
        _add_legend(ax, chart, len(groups), preferred=legend_loc, mode="below" if kind in {"line", "multi_line", "step_line", "area", "stacked_area"} else "auto")
    else:
        g = data.groupby(x, as_index=False)[y].mean().sort_values(x)
        if kind == "area":
            ax.fill_between(g[x], g[y], alpha=area_alpha)
        ax.plot(g[x], g[y], marker=marker, markersize=markersize, linewidth=linewidth, linestyle=linestyle, drawstyle=drawstyle)
    ax.set_xlabel(_pretty(x))
    ax.set_ylabel(_pretty(y))


def _plot_bar_like(ax, df, chart, kind, color_map):
    enc = chart.get("encodings", {})
    y = _measure_column(df, enc.get("y"))
    x = _category_column(df, enc.get("x") or enc.get("color_by") or enc.get("group_by"))
    color_pref = _field(enc.get("color_by"), df)
    group_pref = _field(enc.get("group_by"), df)
    group = color_pref if color_pref != x else group_pref
    if not x or not y:
        raise ValueError(f"Insufficient data for {kind}: missing category or measure")
    data = df[[x, y] + ([group] if group and group in df.columns and group != x else [])].copy()
    data[y] = _to_num(data[y])
    data = data.dropna(subset=[x, y])
    if data.empty:
        raise ValueError(f"Insufficient data for {kind}: no valid category/measure rows")
    if not _has_visible_magnitude(data[y]):
        raise ValueError(f"Insufficient visible data for {kind}: all plotted values are zero")
    sort_policy = _tget(chart, "sort", "descending")
    width = float(_tget(chart, "width", 0.78))
    edgecolor = _tget(chart, "edgecolor", "white")
    linewidth = float(_tget(chart, "linewidth", 0.5))
    rotation = float(_tget(chart, "rotation", 35))
    if kind in {"grouped_bar", "stacked_bar", "stacked_horizontal_bar", "proportional_bar"} and group and group in data.columns:
        pivot = data.pivot_table(index=x, columns=group, values=y, aggfunc="mean")
        if sort_policy == "ascending":
            order = pivot.mean(axis=1).sort_values(ascending=True).head(8).index
        elif sort_policy == "original":
            order = pivot.index[:8]
        else:
            order = pivot.mean(axis=1).sort_values(ascending=False).head(8).index
        pivot = pivot.loc[order]
        pivot_values = pivot.fillna(0)
        if not _has_visible_magnitude(pivot_values.values):
            raise ValueError(f"Insufficient visible data for {kind}: grouped values are all zero")
        if kind == "proportional_bar":
            denom = pivot_values.sum(axis=1).replace(0, np.nan)
            if denom.notna().sum() == 0:
                raise ValueError(f"Insufficient visible data for {kind}: all composition totals are zero")
            pivot = pivot_values.div(denom, axis=0).fillna(0) * 100
            pivot.plot(kind="bar", stacked=True, ax=ax, width=width, edgecolor=edgecolor, linewidth=linewidth)
            ax.set_ylabel("Share (%)")
        elif kind == "stacked_horizontal_bar":
            pivot.plot(kind="barh", stacked=True, ax=ax, width=width, edgecolor=edgecolor, linewidth=linewidth)
            ax.set_xlabel(_pretty(y))
        elif kind == "stacked_bar":
            pivot.plot(kind="bar", stacked=True, ax=ax, width=width, edgecolor=edgecolor, linewidth=linewidth)
        else:
            pivot.plot(kind="bar", ax=ax, width=width, edgecolor=edgecolor, linewidth=linewidth)
        if kind != "stacked_horizontal_bar":
            ax.tick_params(axis="x", labelrotation=rotation)
        _add_legend(ax, chart, len(pivot.columns), preferred="best", mode="right")
    else:
        agg = data.groupby(x, as_index=False)[y].mean()
        if sort_policy == "ascending":
            agg = agg.sort_values(y, ascending=True)
        elif sort_policy == "original":
            agg = agg
        else:
            agg = agg.sort_values(y, ascending=False)
        agg = agg.head(12)
        labels = [str(v) for v in agg[x]]
        colors = _palette(labels, color_map)
        color_values = [colors[label] for label in labels]
        if kind == "waterfall":
            values = agg[y].values
            starts = np.r_[0, np.cumsum(values)[:-1]]
            wf_colors = ["#4C78A8" if value >= 0 else "#E45756" for value in values]
            ax.bar(labels, values, bottom=starts, color=wf_colors, width=width, edgecolor=edgecolor, linewidth=linewidth)
            ax.plot(np.arange(len(labels)), np.cumsum(values), color="#374151", linewidth=1.0, marker="o", markersize=2)
            ax.axhline(0, color="#374151", linewidth=0.8)
            ax.set_ylabel(_pretty(y))
            ax.tick_params(axis="x", labelrotation=rotation)
        elif kind in {"lollipop", "dot_plot"}:
            ypos = np.arange(len(labels))[::-1]
            values = agg[y].values[::-1]
            labels_rev = labels[::-1]
            stem_lw = float(_tget(chart, "stem_linewidth", 1.2))
            size = float(_tget(chart, "size", 42))
            if stem_lw > 0:
                ax.hlines(ypos, 0, values, color="#94A3B8", linewidth=stem_lw)
            ax.scatter(values, ypos, s=size, color=[colors[label] for label in labels_rev], edgecolor=edgecolor if edgecolor != "none" else "white", linewidth=linewidth)
            ax.set_yticks(ypos)
            ax.set_yticklabels(labels_rev)
            ax.set_xlabel(_pretty(y))
        elif kind == "horizontal_bar":
            ax.barh(labels[::-1], agg[y].values[::-1], color=color_values[::-1], edgecolor=edgecolor, linewidth=linewidth)
            ax.set_xlabel(_pretty(y))
        else:
            ax.bar(labels, agg[y], color=color_values, width=width, edgecolor=edgecolor, linewidth=linewidth)
            ax.set_ylabel(_pretty(y))
            ax.tick_params(axis="x", labelrotation=rotation)
    ax.set_xlabel(_pretty(x))


def _plot_scatter_like(ax, df, chart, kind, color_map):
    enc = chart.get("encodings", {})
    nums = _numeric_columns(df)
    x_pref = _field(enc.get("x"), df)
    y_pref = _field(enc.get("y"), df)
    x = x_pref if x_pref in df.columns else (nums[0] if nums else None)
    y = y_pref if y_pref in df.columns else (nums[1] if len(nums) > 1 else None)
    if x == y:
        alternate = next((column for column in nums if column != x), None)
        if alternate:
            y = alternate
        else:
            df = df.copy()
            df["_observation_index"] = np.arange(len(df))
            x = "_observation_index"
    color_by = _field(enc.get("color_by") or enc.get("group_by"), df)
    if color_by in {x, y}:
        color_by = None
    if not x or not y:
        raise ValueError(f"Insufficient data for {kind}: missing numeric x/y")
    data = _small(df[[x, y] + ([color_by] if color_by and color_by in df.columns else [])].copy(), 1200)
    data[x] = _to_num(data[x])
    data[y] = _to_num(data[y])
    data = data.dropna(subset=[x, y])
    point_size = float(_tget(chart, "size", 65 if kind == "bubble" else 28))
    alpha = float(_tget(chart, "alpha", 0.72))
    marker = _tget(chart, "marker", "o")
    edgecolor = _tget(chart, "edgecolor", "white")
    linewidth = float(_tget(chart, "linewidth", 0.4))
    if kind in {"hexbin", "contour_density"}:
        alpha = float(_tget(chart, "alpha", 0.78))
        cmap = _tget(chart, "cmap", "viridis")
        gridsize = int(_tget(chart, "gridsize", 28))
        if kind == "hexbin":
            hb = ax.hexbin(data[x], data[y], gridsize=gridsize, cmap=cmap, mincnt=int(_tget(chart, "mincnt", 1)), alpha=alpha)
            plt.colorbar(hb, ax=ax, fraction=0.046, pad=0.04)
        else:
            hist, xedges, yedges = np.histogram2d(data[x], data[y], bins=gridsize)
            if hist.max() <= 0:
                ax.scatter(data[x], data[y], s=point_size, alpha=alpha, marker=marker, edgecolor=edgecolor, linewidth=linewidth)
            else:
                xx = (xedges[:-1] + xedges[1:]) / 2
                yy = (yedges[:-1] + yedges[1:]) / 2
                levels = int(_tget(chart, "levels", 6))
                cf = ax.contourf(xx, yy, hist.T, levels=levels, cmap=cmap, alpha=alpha)
                ax.contour(xx, yy, hist.T, levels=levels, colors="#374151", linewidths=0.4, alpha=0.45)
                plt.colorbar(cf, ax=ax, fraction=0.046, pad=0.04)
    elif color_by and color_by in data.columns:
        labels = list(data[color_by].astype(str).dropna().unique())[:10]
        colors = _palette(labels, color_map)
        for label in labels:
            g = data[data[color_by].astype(str) == label]
            size = point_size * (1.7 if kind == "bubble" else 1.0)
            ax.scatter(g[x], g[y], s=size, alpha=alpha, marker=marker, label=str(label), color=colors[str(label)], edgecolor=edgecolor, linewidth=linewidth)
        _add_legend(ax, chart, len(labels), preferred="best", mode="right")
    else:
        ax.scatter(data[x], data[y], s=point_size * (1.7 if kind == "bubble" else 1.0), alpha=alpha, marker=marker, edgecolor=edgecolor, linewidth=linewidth)
    add_trend = _tget(chart, "trend", False) or any(op.get("operation") == "add_trend_line" for op in chart.get("_active_ops", []))
    if add_trend and len(data) >= 8:
        xs = data[x].astype(float)
        ys = data[y].astype(float)
        if xs.nunique() > 1:
            coef = np.polyfit(xs, ys, 1)
            xx = np.linspace(xs.min(), xs.max(), 80)
            ax.plot(xx, coef[0] * xx + coef[1], color="#374151", linewidth=1.2, linestyle="--", alpha=0.75)
    ax.set_xlabel(_pretty(x))
    ax.set_ylabel(_pretty(y))


def _plot_distribution(ax, df, chart, kind):
    enc = chart.get("encodings", {})
    y = _measure_column(df, enc.get("y") or enc.get("x"))
    group = _category_column(df, enc.get("color_by") or enc.get("group_by"))
    if not y:
        raise ValueError(f"Insufficient data for {kind}: missing numeric measure")
    data = df.copy()
    data[y] = _to_num(data[y])
    data = data.dropna(subset=[y])
    if data.empty:
        raise ValueError(f"Insufficient data for {kind}: no valid numeric values")
    bins = int(_tget(chart, "bins", 22))
    alpha = float(_tget(chart, "alpha", 0.78))
    edgecolor = _tget(chart, "edgecolor", "white")
    rotation = float(_tget(chart, "rotation", 35))
    if kind == "histogram":
        ax.hist(data[y], bins=bins, alpha=alpha, color="#4C78A8", edgecolor=edgecolor)
    elif kind == "density":
        data[y].plot(kind="density", ax=ax, color="#4C78A8", linewidth=2.0, alpha=min(1.0, alpha + 0.15))
    elif kind == "ecdf":
        linewidth = float(_tget(chart, "linewidth", 1.8))
        marker = _tget(chart, "marker", None)
        markersize = float(_tget(chart, "markersize", 2.0))
        if group and group in data.columns:
            top = _stable_top_labels(data[group], 6)
            colors = _palette(top, {})
            for label in top:
                values = np.sort(data[data[group].astype(str) == label][y].dropna().values)
                if len(values):
                    p = np.arange(1, len(values) + 1) / len(values)
                    ax.plot(values, p, label=str(label), linewidth=linewidth, marker=marker, markersize=markersize, alpha=alpha, color=colors[str(label)], drawstyle="steps-post")
            _add_legend(ax, chart, len(top), preferred="best", mode="below")
        else:
            values = np.sort(data[y].dropna().values)
            p = np.arange(1, len(values) + 1) / len(values)
            ax.plot(values, p, linewidth=linewidth, marker=marker, markersize=markersize, alpha=alpha, drawstyle="steps-post")
        ax.set_ylabel("Cumulative share")
    elif kind == "strip_plot":
        if group and group in data.columns:
            top = _stable_top_labels(data[group], 8)
            colors = _palette(top, {})
            rng = np.random.default_rng(7)
            jitter = float(_tget(chart, "jitter", 0.18))
            size = float(_tget(chart, "size", 24))
            for idx, label in enumerate(top):
                values = data[data[group].astype(str) == label][y].dropna().values
                xpos = idx + rng.uniform(-jitter, jitter, size=len(values))
                ax.scatter(xpos, values, s=size, alpha=alpha, color=colors[str(label)], edgecolor=edgecolor if edgecolor != "none" else "white", linewidth=0.25)
            ax.set_xticks(range(len(top)))
            ax.set_xticklabels(top, rotation=rotation, ha="right")
            ax.set_ylabel(_pretty(y))
        else:
            rng = np.random.default_rng(7)
            xpos = rng.uniform(-0.2, 0.2, size=len(data))
            ax.scatter(xpos, data[y], s=float(_tget(chart, "size", 24)), alpha=alpha, edgecolor=edgecolor if edgecolor != "none" else "white", linewidth=0.25)
            ax.set_xticks([0])
            ax.set_xticklabels([_pretty(y)])
            ax.set_ylabel(_pretty(y))
    elif kind in {"box", "violin"} and group and group in data.columns:
        top = _stable_top_labels(data[group], 8)
        series = [data[data[group].astype(str) == label][y].dropna().values for label in top]
        if kind == "box":
            ax.boxplot(series, labels=top, patch_artist=True, notch=bool(_tget(chart, "notch", False)), showmeans=bool(_tget(chart, "showmeans", False)))
            ax.tick_params(axis="x", labelrotation=rotation)
        else:
            ax.violinplot(series, showmeans=bool(_tget(chart, "showmeans", True)), showextrema=True)
            ax.set_xticks(range(1, len(top) + 1))
            ax.set_xticklabels(top, rotation=rotation, ha="right")
    else:
        ax.hist(data[y], bins=bins, alpha=alpha, edgecolor=edgecolor)
    if _tget(chart, "show_mean", False):
        ax.axvline(float(data[y].mean()), color="#374151", linestyle="--", linewidth=1.1)
    ax.set_xlabel(_pretty(y))


def _plot_heatmap(ax, df, chart, kind):
    nums = _numeric_columns(df)
    if len(nums) < 2:
        raise ValueError(f"Insufficient numeric data for {kind}: fewer than two numeric columns")
    corr = df[nums[:8]].apply(_to_num).corr()
    im = ax.imshow(corr.values, cmap=_tget(chart, "cmap", "viridis"), aspect="auto", vmin=-1, vmax=1)
    if _tget(chart, "show_values", False) and len(corr.columns) <= 6:
        for row in range(len(corr.index)):
            for col in range(len(corr.columns)):
                ax.text(col, row, f"{corr.values[row, col]:.1f}", ha="center", va="center", fontsize=6, color="white")
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.index)))
    ax.set_xticklabels([_pretty(c) for c in corr.columns], rotation=float(_tget(chart, "label_rotation", 45)), ha="right", fontsize=7)
    ax.set_yticklabels([_pretty(c) for c in corr.index], fontsize=7)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)


def _plot_pie(ax, df, chart, kind, color_map):
    enc = chart.get("encodings", {})
    y = _measure_column(df, enc.get("y"))
    cat = _category_column(df, enc.get("color_by") or enc.get("x") or enc.get("group_by"))
    if not cat or not y:
        raise ValueError(f"Insufficient data for {kind}: missing category or measure")
    data = df[[cat, y]].copy()
    data[y] = _to_num(data[y])
    agg = data.dropna().groupby(cat)[y].mean().sort_values(ascending=False).head(8)
    if agg.empty:
        raise ValueError(f"Insufficient data for {kind}: no grouped values")
    if (agg <= 0).any():
        agg = agg.abs()
    agg = agg[agg > 0]
    if agg.empty or not np.isfinite(agg.values).all() or float(agg.sum()) <= 0:
        raise ValueError(f"Insufficient data for {kind}: no positive finite shares")
    labels = [str(v) for v in agg.index]
    colors = _palette(labels, color_map)
    label_mode = _tget(chart, "label_mode", "direct")
    wedge_width = _tget(chart, "wedge_width", None)
    if kind == "donut" and wedge_width is None:
        wedge_width = 0.42
    wedgeprops = {"linewidth": 0.6, "edgecolor": "white"}
    if wedge_width is not None:
        wedgeprops["width"] = float(wedge_width)
    wedges, _ = ax.pie(
        agg.values,
        labels=labels if label_mode == "direct" else None,
        colors=[colors[l] for l in labels],
        startangle=float(_tget(chart, "startangle", 90)),
        wedgeprops=wedgeprops,
        textprops={"fontsize": 7},
    )
    if label_mode == "legend":
        ax.legend(wedges, labels, frameon=False, fontsize=int(_tget(chart, "legend_fontsize", 7)), loc="center left", bbox_to_anchor=(1.0, 0.5))
    elif kind == "donut" and wedge_width is None:
        centre = plt.Circle((0, 0), 0.58, fc="white")
        ax.add_artist(centre)
    ax.axis("equal")


def _plot_dual_or_error(ax, df, chart, kind, color_map):
    enc = chart.get("encodings", {})
    x = _field(enc.get("x"), df)
    y = _measure_column(df, enc.get("y"))
    if not x or x not in df.columns or not y:
        _plot_bar_like(ax, df, chart, "bar", color_map)
        return
    data = df[[x, y]].copy()
    data[y] = _to_num(data[y])
    if data[x].dtype == object:
        data[x] = _to_axis_values(data[x])
        if data[x].notna().sum() >= max(3, int(len(data) * 0.2)):
            agg = data.dropna().groupby(x)[y].agg(["mean", "std"]).sort_index().tail(20)
        else:
            agg = data.dropna().groupby(x)[y].agg(["mean", "std"]).sort_values("mean", ascending=False).head(10)
    else:
        data[x] = _to_num(data[x])
        agg = data.dropna().groupby(x)[y].agg(["mean", "std"]).sort_index().tail(20)
    if kind == "error_bar":
        ax.bar([str(i) for i in agg.index], agg["mean"], yerr=agg["std"].fillna(0), color="#4C78A8", alpha=float(_tget(chart, "bar_alpha", 0.8)), capsize=4)
        ax.tick_params(axis="x", labelrotation=35)
    else:
        ax.bar(agg.index, agg["mean"], color="#A0CBE8", alpha=float(_tget(chart, "bar_alpha", 0.65)))
        ax2 = ax.twinx()
        ax2.plot(agg.index, agg["mean"].rolling(3, min_periods=1).mean(), color="#F58518", marker=_tget(chart, "line_marker", "o"), linewidth=float(_tget(chart, "line_width", 2.0)))
        ax2.set_ylabel("Rolling mean")
    ax.set_ylabel(_pretty(y))


def _top_category_values(df, cat, measure, limit=10):
    data = df[[cat, measure]].copy()
    data[measure] = _to_num(data[measure])
    grouped = data.dropna(subset=[cat, measure]).groupby(cat)[measure].mean().sort_values(ascending=False)
    grouped = grouped[np.isfinite(grouped.values)]
    grouped = grouped[grouped.abs() > 1e-12]
    return grouped.head(limit)


def _plot_radar(ax, df, chart, color_map):
    enc = chart.get("encodings", {})
    nums = []
    preferred = enc.get("y")
    if isinstance(preferred, list):
        nums = [c for c in preferred if c in df.columns and c in _numeric_columns(df)]
    if len(nums) < 3:
        nums = [c for c in _numeric_columns(df) if c not in {enc.get("x")}][:5]
    cat = _category_column(df, enc.get("color_by") or enc.get("x") or enc.get("group_by"))
    data = df.copy()
    measure = _measure_column(data, enc.get("y"))
    if len(nums) < 3 and cat and measure and cat in data.columns and measure in data.columns:
        temp = data[[cat, measure]].copy()
        temp[measure] = _to_num(temp[measure])
        grouped_metrics = temp.dropna(subset=[cat, measure]).groupby(cat)[measure].agg(["mean", "std", "count"]).fillna(0)
        grouped_metrics = grouped_metrics[grouped_metrics["count"] > 0].sort_values("mean", ascending=False).head(3)
        if not grouped_metrics.empty:
            nums = ["mean", "std", "count"]
            values = grouped_metrics[nums]
            values.index = values.index.astype(str)
        else:
            values = pd.DataFrame()
    else:
        nums = nums[:5]
        values = pd.DataFrame()
    if len(nums) < 3:
        raise ValueError("Insufficient data for radar: fewer than three numeric measures")
    for col in nums:
        if col in data.columns:
            data[col] = _to_num(data[col])
    if values.empty:
        labels = ["Overall"]
        rows = [data[nums].mean(numeric_only=True)]
        if cat and cat in data.columns:
            top = _stable_top_labels(data[cat], 3)
            grouped = data[data[cat].astype(str).isin(top)].groupby(cat)[nums].mean(numeric_only=True)
            labels = [str(v) for v in grouped.index]
            rows = [grouped.loc[v] for v in grouped.index]
        values = pd.DataFrame(rows, index=labels, columns=nums)
    values = values.replace([np.inf, -np.inf], np.nan).dropna(how="all")
    if values.empty:
        raise ValueError("Insufficient data for radar: empty normalized table")
    mins = values.min(axis=0)
    spans = (values.max(axis=0) - mins).replace(0, 1.0)
    norm = (values - mins) / spans
    angles = np.linspace(0, 2 * np.pi, len(nums), endpoint=False)
    closed_angles = np.r_[angles, angles[0]]
    colors = _palette(norm.index.tolist(), color_map)
    alpha = float(_tget(chart, "alpha", 0.20))
    linewidth = float(_tget(chart, "linewidth", 1.8))
    marker = _tget(chart, "marker", "o")
    for label, row in norm.iterrows():
        yvals = np.r_[row.fillna(0).values.astype(float), float(row.fillna(0).values[0])]
        xcoords = np.cos(closed_angles) * yvals
        ycoords = np.sin(closed_angles) * yvals
        ax.plot(xcoords, ycoords, label=str(label), color=colors[str(label)], linewidth=linewidth, marker=marker, markersize=float(_tget(chart, "markersize", 3)))
        ax.fill(xcoords, ycoords, color=colors[str(label)], alpha=alpha)
    for angle, label in zip(angles, nums):
        ax.plot([0, np.cos(angle)], [0, np.sin(angle)], color="#94A3B8", linewidth=0.6, alpha=0.5)
        ax.text(1.12 * np.cos(angle), 1.12 * np.sin(angle), _pretty(label), ha="center", va="center", fontsize=7)
    for radius in [0.25, 0.5, 0.75, 1.0]:
        ax.add_patch(plt.Circle((0, 0), radius, fill=False, color="#CBD5E1", linewidth=0.5, alpha=0.45))
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.25, 1.25)
    ax.set_aspect("equal")
    ax.set_axis_off()
    _add_legend(ax, chart, len(norm.index), preferred=_tget(chart, "legend_loc", "lower center"), mode="below")


def _plot_treemap(ax, df, chart, color_map):
    enc = chart.get("encodings", {})
    cat = _category_column(df, enc.get("x") or enc.get("color_by") or enc.get("group_by"))
    measure = _measure_column(df, enc.get("y"))
    if not cat or not measure:
        raise ValueError("Insufficient data for treemap: missing category or measure")
    values = _top_category_values(df, cat, measure, limit=10).abs()
    if values.empty:
        raise ValueError("Insufficient data for treemap: no positive category values")
    labels = [str(v) for v in values.index]
    colors = _palette(labels, color_map)
    total = float(values.sum())
    x0 = y0 = 0.0
    width = height = 1.0
    horizontal = True
    alpha = float(_tget(chart, "alpha", 0.86))
    lw = float(_tget(chart, "linewidth", 0.8))
    for label, value in values.items():
        frac = float(value) / total if total > 0 else 0
        if horizontal:
            w = width * frac
            rect = Rectangle((x0, y0), w, height, facecolor=colors[label], edgecolor="white", linewidth=lw, alpha=alpha, label="treemap_tile")
            ax.add_patch(rect)
            cx, cy = x0 + w / 2, y0 + height / 2
            x0 += w
            width -= w
        else:
            h = height * frac
            rect = Rectangle((x0, y0), width, h, facecolor=colors[label], edgecolor="white", linewidth=lw, alpha=alpha, label="treemap_tile")
            ax.add_patch(rect)
            cx, cy = x0 + width / 2, y0 + h / 2
            y0 += h
            height -= h
        total -= float(value)
        horizontal = not horizontal
        ax.text(cx, cy, label[:18], ha="center", va="center", fontsize=7, color="#111827")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()


def _plot_funnel(ax, df, chart, color_map):
    enc = chart.get("encodings", {})
    cat = _category_column(df, enc.get("x") or enc.get("color_by") or enc.get("group_by"))
    measure = _measure_column(df, enc.get("y"))
    if not cat or not measure:
        raise ValueError("Insufficient data for funnel: missing category or measure")
    values = _top_category_values(df, cat, measure, limit=7).abs().sort_values(ascending=False)
    if values.empty:
        raise ValueError("Insufficient data for funnel: no stage values")
    labels = [str(v) for v in values.index]
    colors = _palette(labels, color_map)
    maxv = float(values.max())
    alpha = float(_tget(chart, "alpha", 0.82))
    for idx, (label, value) in enumerate(values.items()):
        top_width = float(value) / maxv
        next_width = float(values.iloc[idx + 1]) / maxv if idx + 1 < len(values) else top_width * 0.72
        y_top = len(values) - idx
        y_bottom = len(values) - idx - 0.82
        poly = Polygon(
            [(-top_width / 2, y_top), (top_width / 2, y_top), (next_width / 2, y_bottom), (-next_width / 2, y_bottom)],
            closed=True,
            facecolor=colors[str(label)],
            edgecolor="white",
            linewidth=float(_tget(chart, "linewidth", 0.8)),
            alpha=alpha,
        )
        ax.add_patch(poly)
        ax.text(0, (y_top + y_bottom) / 2, f"{label[:16]}  {value:.1f}", ha="center", va="center", fontsize=7)
    ax.set_xlim(-0.62, 0.62)
    ax.set_ylim(0, len(values) + 0.2)
    ax.set_axis_off()


def _plot_sankey(ax, df, chart, color_map):
    enc = chart.get("encodings", {})
    source = _category_column(df, enc.get("x"))
    target = _category_column(df, enc.get("group_by") or enc.get("color_by"))
    if target == source:
        target = next((c for c in df.columns if c != source and (df[c].dtype == object or str(df[c].dtype).startswith("string"))), None)
    measure = _measure_column(df, enc.get("y"))
    if not source or not target or not measure:
        raise ValueError("Insufficient data for sankey: missing source, target, or measure")
    data = df[[source, target, measure]].copy()
    data[measure] = _to_num(data[measure]).abs()
    flows = data.dropna().groupby([source, target])[measure].sum().sort_values(ascending=False).head(14)
    if flows.empty or float(flows.sum()) <= 0:
        raise ValueError("Insufficient data for sankey: empty flows")
    src_labels = [str(v) for v in pd.Index([idx[0] for idx in flows.index]).unique()][:6]
    tgt_labels = [str(v) for v in pd.Index([idx[1] for idx in flows.index]).unique()][:6]
    colors = _palette(src_labels + tgt_labels, color_map)
    src_y = {label: 1 - (i + 0.5) / max(1, len(src_labels)) for i, label in enumerate(src_labels)}
    tgt_y = {label: 1 - (i + 0.5) / max(1, len(tgt_labels)) for i, label in enumerate(tgt_labels)}
    max_flow = float(flows.max())
    for (src, tgt), value in flows.items():
        src = str(src); tgt = str(tgt)
        if src not in src_y or tgt not in tgt_y:
            continue
        lw = max(1.0, float(_tget(chart, "linewidth", 2.0)) * float(value) / max_flow * 5.0)
        arrow = FancyArrowPatch((0.18, src_y[src]), (0.82, tgt_y[tgt]), connectionstyle="arc3,rad=0.18", arrowstyle="-", linewidth=lw, color=colors[src], alpha=float(_tget(chart, "alpha", 0.45)))
        ax.add_patch(arrow)
    for label, ypos in src_y.items():
        ax.text(0.05, ypos, label[:16], ha="left", va="center", fontsize=7)
        ax.scatter([0.16], [ypos], s=35, color=colors[label], zorder=3)
    for label, ypos in tgt_y.items():
        ax.text(0.95, ypos, label[:16], ha="right", va="center", fontsize=7)
        ax.scatter([0.84], [ypos], s=35, color=colors[label], zorder=3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()


def _plot_candlestick(ax, df, chart, color_map):
    enc = chart.get("encodings", {})
    x = _field(enc.get("x"), df)
    y = _measure_column(df, enc.get("y"))
    group = _field(enc.get("color_by") or enc.get("group_by"), df)
    if not x or x not in df.columns or not y:
        raise ValueError("Insufficient data for candlestick: missing time or measure")
    cols = [x, y] + ([group] if group and group in df.columns else [])
    data = df[cols].copy()
    data[x] = _to_axis_values(data[x])
    data[y] = _to_num(data[y])
    data = data.dropna(subset=[x, y])
    if group and group in data.columns and data[group].nunique() > 1:
        chosen = _stable_top_labels(data[group], 1)[0]
        data = data[data[group].astype(str) == chosen]
    agg = data.groupby(x)[y].mean().sort_index().tail(24)
    if len(agg) < 4:
        fallback = data[y].dropna().tail(24).reset_index(drop=True)
        if len(fallback) < 4:
            raise ValueError("Insufficient data for candlestick: fewer than four time points")
        agg = pd.Series(fallback.values, index=np.arange(len(fallback)))
    closes = agg.values.astype(float)
    opens = np.r_[closes[0], closes[:-1]]
    spread = np.maximum(np.abs(closes - opens) * 0.35, np.nanstd(closes) * 0.08 + 1e-6)
    highs = np.maximum(opens, closes) + spread
    lows = np.minimum(opens, closes) - spread
    xpos = np.arange(len(agg))
    width = float(_tget(chart, "width", 0.58))
    alpha = float(_tget(chart, "alpha", 0.86))
    for i, (opn, high, low, close) in enumerate(zip(opens, highs, lows, closes)):
        color = "#2CA02C" if close >= opn else "#D62728"
        ax.vlines(i, low, high, color=color, linewidth=float(_tget(chart, "linewidth", 0.8)), alpha=alpha)
        bottom = min(opn, close)
        height = max(abs(close - opn), np.nanstd(closes) * 0.015 + 1e-6)
        ax.add_patch(Rectangle((i - width / 2, bottom), width, height, facecolor=color, edgecolor="#374151", linewidth=0.4, alpha=alpha))
    ax.set_xticks(xpos[::max(1, len(xpos)//8)])
    ax.set_xticklabels([str(v) for v in agg.index[::max(1, len(xpos)//8)]], rotation=float(_tget(chart, "rotation", 35)), ha="right")
    ax.set_xlabel(_pretty(x))
    ax.set_ylabel(_pretty(y))


def _plot_choropleth_map(ax, df, chart, color_map):
    enc = chart.get("encodings", {})
    region = _category_column(df, enc.get("x") or enc.get("color_by") or enc.get("group_by"))
    measure = _measure_column(df, enc.get("y"))
    if not region or not measure:
        raise ValueError("Insufficient data for choropleth_map: missing region or measure")
    values = _top_category_values(df, region, measure, limit=12)
    if values.empty:
        raise ValueError("Insufficient data for choropleth_map: no regional values")
    vals = values.values.astype(float)
    cmap = plt.get_cmap(_tget(chart, "cmap", "YlGnBu"))
    norm = plt.Normalize(vmin=float(np.nanmin(vals)), vmax=float(np.nanmax(vals)) if float(np.nanmax(vals)) != float(np.nanmin(vals)) else float(np.nanmin(vals)) + 1)
    cols = int(np.ceil(np.sqrt(len(values))))
    rows = int(np.ceil(len(values) / cols))
    for idx, (label, value) in enumerate(values.items()):
        row = idx // cols
        col = idx % cols
        rect = Rectangle((col, rows - row - 1), 0.94, 0.86, facecolor=cmap(norm(float(value))), edgecolor="white", linewidth=float(_tget(chart, "linewidth", 0.9)), alpha=float(_tget(chart, "alpha", 0.9)), label="choropleth_tile")
        ax.add_patch(rect)
        ax.text(col + 0.47, rows - row - 0.57, str(label)[:14], ha="center", va="center", fontsize=6.5, color="#111827")
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_aspect("equal")
    ax.set_axis_off()


def _plot_gantt(ax, df, chart, color_map):
    enc = chart.get("encodings", {})
    task = _category_column(df, enc.get("group_by") or enc.get("color_by") or enc.get("x"))
    time_col = _field(enc.get("x"), df)
    measure = _measure_column(df, enc.get("y"))
    if not task:
        raise ValueError("Insufficient data for gantt: missing task/entity column")
    data = df.copy()
    labels = _stable_top_labels(data[task], 8)
    colors = _palette(labels, color_map)
    bars = []
    if time_col and time_col in data.columns:
        data[time_col] = _to_axis_values(data[time_col])
        for label in labels:
            vals = data[data[task].astype(str) == label][time_col].dropna()
            if len(vals):
                start = float(vals.min())
                end = float(vals.max())
                if end <= start:
                    end = start + 1.0
                bars.append((label, start, end - start))
    if not bars and measure and measure in data.columns:
        vals = data.groupby(task)[measure].mean().sort_values(ascending=False).head(8)
        for idx, (label, value) in enumerate(vals.items()):
            bars.append((str(label), float(idx), max(0.5, abs(float(value)) / max(1.0, abs(float(vals.max()))) * 4.0)))
    if not bars:
        raise ValueError("Insufficient data for gantt: no valid task spans")
    for idx, (label, start, duration) in enumerate(bars):
        ax.barh(idx, duration, left=start, color=colors.get(str(label), "#4C78A8"), alpha=float(_tget(chart, "alpha", 0.74)), edgecolor="white", linewidth=float(_tget(chart, "linewidth", 0.8)))
    ax.set_yticks(range(len(bars)))
    ax.set_yticklabels([label for label, _, _ in bars], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel(_pretty(time_col or measure or "duration"))


def _plot_chart(ax, df, chart, operations):
    chart_ops = _ops_for_chart(chart, operations)
    chart = dict(chart)
    chart["_active_ops"] = chart_ops
    ctype = chart.get("chart_type", "bar")
    for op in chart_ops:
        if op.get("operation") == "change_chart_type":
            ctype = op.get("to_type", ctype)
    color_map = _target_color_map(chart, operations)
    df = _apply_data_ops(df, chart, operations)
    df = _apply_chart_data_transform(df, chart)

    if ctype in {"line", "multi_line", "step_line", "area", "stacked_area"}:
        _plot_line_like(ax, df, chart, ctype, color_map)
    elif ctype in {"bar", "horizontal_bar", "grouped_bar", "stacked_bar", "stacked_horizontal_bar", "proportional_bar", "lollipop", "dot_plot", "waterfall"}:
        _plot_bar_like(ax, df, chart, ctype, color_map)
    elif ctype in {"scatter", "bubble", "hexbin", "contour_density"}:
        _plot_scatter_like(ax, df, chart, ctype, color_map)
    elif ctype in {"histogram", "density", "ecdf", "strip_plot", "box", "violin"}:
        _plot_distribution(ax, df, chart, ctype)
    elif ctype in {"heatmap", "correlation_heatmap"}:
        _plot_heatmap(ax, df, chart, ctype)
    elif ctype in {"pie", "donut"}:
        _plot_pie(ax, df, chart, ctype, color_map)
    elif ctype in {"dual_axis_line_bar", "error_bar"}:
        _plot_dual_or_error(ax, df, chart, ctype, color_map)
    elif ctype == "radar":
        _plot_radar(ax, df, chart, color_map)
    elif ctype == "treemap":
        _plot_treemap(ax, df, chart, color_map)
    elif ctype == "sankey":
        _plot_sankey(ax, df, chart, color_map)
    elif ctype == "candlestick":
        _plot_candlestick(ax, df, chart, color_map)
    elif ctype == "choropleth_map":
        _plot_choropleth_map(ax, df, chart, color_map)
    elif ctype == "funnel":
        _plot_funnel(ax, df, chart, color_map)
    elif ctype == "gantt":
        _plot_gantt(ax, df, chart, color_map)
    else:
        _plot_bar_like(ax, df, chart, "bar", color_map)

    title_color = "#93C5FD" if _theme_dark(chart) else ("#123A6F" if _style_flags(chart_ops) else "#111827")
    ax.set_title(chart.get("title", chart.get("chart_id", "")), fontsize=int(_tget(chart, "title_size", _theme(chart).get("title_size", 10))), color=title_color, pad=8)
    _apply_axis_theme(ax, chart, style_modified=_style_flags(chart_ops))

    enc = chart.get("encodings", {})
    y = _field(enc.get("y"), df)
    transform = chart.get("data_transform", {}) or {}
    op_log_scale = any(op.get("operation") == "set_y_scale" and op.get("scale") == "log" for op in chart_ops)
    if (transform.get("transform_id") == "log_y_scale" or op_log_scale) and y and y in df.columns:
        yy = _to_num(df[y]).dropna()
        if len(yy) and (yy > 0).all():
            ax.set_yscale("log")
    if transform.get("transform_id") == "normalize_measure" and y and y in df.columns:
        method = transform.get("method", "minmax")
        current = ax.get_ylabel()
        suffix = "normalized" if method == "minmax" else "z-score"
        if current:
            ax.set_ylabel(f"{current} ({suffix})")
    for op in chart_ops:
        if op.get("operation") == "change_axis_label":
            if op.get("axis") == "x":
                ax.set_xlabel(op.get("new_label", ""))
            elif op.get("axis") == "y":
                ax.set_ylabel(op.get("new_label", ""))
        if op.get("operation") == "add_reference_line" and y and y in df.columns:
            yy = _to_num(df[y]).dropna()
            if len(yy):
                value = float(yy.mean()) if op.get("y") == "mean" else float(op.get("y"))
                ax.axhline(value, color=op.get("color", "purple"), linestyle="--", linewidth=1.6)
                ax.text(0.98, 0.94, op.get("label", "Reference"), transform=ax.transAxes, ha="right", va="top", fontsize=7, color=op.get("color", "purple"))
        if op.get("operation") == "add_event_marker":
            try:
                ax.axvline(float(op.get("x")), color=op.get("color", "red"), linestyle=":", linewidth=1.6)
                ax.text(float(op.get("x")), 0.98, op.get("label", "event"), transform=ax.get_xaxis_transform(), rotation=90, ha="right", va="top", fontsize=7, color=op.get("color", "red"))
            except Exception:
                pass


def _make_axes(spec, n):
    layout = spec.get("layout_template", {}) or {}
    layout_id = layout.get("layout_id", "regular_grid")
    scale = float(layout.get("figure_scale", 1.0))
    wspace = float(layout.get("wspace", 0.30))
    hspace = float(layout.get("hspace", 0.36))

    if layout_id == "wide_top" and n >= 3:
        cols = 3
        rows = 1 + int(math.ceil((n - 1) / cols))
        fig = plt.figure(figsize=(6.4 * cols * scale, (4.2 + 3.8 * (rows - 1)) * scale))
        gs = fig.add_gridspec(rows, cols, height_ratios=[1.18] + [1.0] * (rows - 1), wspace=wspace, hspace=hspace)
        axes = [fig.add_subplot(gs[0, :])]
        for idx in range(n - 1):
            axes.append(fig.add_subplot(gs[1 + idx // cols, idx % cols]))
        return fig, axes

    if layout_id == "left_focus" and n >= 4:
        rows = int(math.ceil((n - 1) / 2))
        fig = plt.figure(figsize=(18.5 * scale, max(8.5, 4.3 * rows) * scale))
        gs = fig.add_gridspec(rows, 3, width_ratios=[1.35, 1.0, 1.0], wspace=wspace, hspace=hspace)
        axes = [fig.add_subplot(gs[:, 0])]
        for idx in range(n - 1):
            axes.append(fig.add_subplot(gs[idx // 2, 1 + idx % 2]))
        return fig, axes

    if layout_id == "top_strip" and n >= 5:
        cols = 3
        lower = n - min(3, n)
        rows = 1 + int(math.ceil(lower / cols))
        fig = plt.figure(figsize=(6.4 * cols * scale, (3.2 + 4.0 * (rows - 1)) * scale))
        gs = fig.add_gridspec(rows, cols, height_ratios=[0.82] + [1.18] * (rows - 1), wspace=wspace, hspace=hspace)
        axes = []
        top_count = min(3, n)
        for idx in range(top_count):
            axes.append(fig.add_subplot(gs[0, idx]))
        for idx in range(n - top_count):
            axes.append(fig.add_subplot(gs[1 + idx // cols, idx % cols]))
        return fig, axes

    cols = 2 if n <= 4 else 3
    rows = int(math.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(6.0 * cols * scale, 3.9 * rows * scale), squeeze=False)
    axes_flat = list(axes.flatten())
    for ax in axes_flat[n:]:
        ax.axis("off")
    return fig, axes_flat[:n]


def render_dashboard(spec, operations, output_name):
    n = int(spec.get("chart_count", len(spec.get("charts", []))))
    fig, axes_flat = _make_axes(spec, n)
    theme = spec.get("style_theme", {}) or {}

    for ax, chart in zip(axes_flat, spec.get("charts", [])):
        data_file = DATA_POOL_ROOT / chart["data_source"]["processed_file"]
        df = pd.read_csv(data_file)
        df = _apply_filters(df, chart.get("filters", []))
        chart = dict(chart)
        chart["_style_theme"] = theme
        _plot_chart(ax, df, chart, operations)

    title = None
    for op in operations:
        if op.get("operation") == "add_dashboard_title":
            title = op.get("text")
    if title:
        fig.suptitle(title, fontsize=16, fontweight="bold", y=0.995)

    fig.patch.set_facecolor(theme.get("background", "white"))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        plt.tight_layout(rect=(0, 0, 1, 0.96 if title else 1), pad=2.2, h_pad=3.0, w_pad=2.2)
    out_path = Path(__file__).resolve().parent / output_name
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


SPEC = json.loads(r'''{
  "dashboard_id": "dashboard_0030",
  "benchmark_version": "real-v2-blueprint",
  "domain": "owid",
  "data_origin": "real",
  "chart_count": 2,
  "design_goal": "Generate a relation-aware multi-chart dashboard from expanded real tabular data.",
  "style_theme": {
    "theme_id": "presentation_clean",
    "font_family": "DejaVu Sans",
    "background": "white",
    "axes_facecolor": "white",
    "grid": "light y only",
    "grid_alpha": 0.174,
    "spine_policy": "minimal",
    "palette": "presentation accents",
    "legend_policy": "outside if crowded",
    "title_size": 10,
    "theme_sampling": {
      "enabled": true,
      "seed": 20354789,
      "note": "Real-v2 split uses theme sampling and bounded visual parameter jitter."
    }
  },
  "layout_template": {
    "layout_id": "regular_grid",
    "description": "balanced subplot grid",
    "min_charts": 2,
    "max_charts": 7,
    "wspace": 0.49,
    "hspace": 0.653,
    "figure_scale": 0.97,
    "selection_policy": "deterministic layout sampling constrained by chart count"
  },
  "charts": [
    {
      "chart_id": "chart_1",
      "chart_type": "funnel",
      "title": "Owid real-v2 view 1",
      "data_source": {
        "dataset_id": "owid_share_electricity_renewables",
        "processed_file": "processed/owid/owid_share_electricity_renewables.csv"
      },
      "encodings": {
        "x": "entity",
        "y": "renewables",
        "color_by": "entity",
        "size_by": null,
        "group_by": null
      },
      "filters": [
        {
          "field": "entity",
          "operator": "in",
          "values": [
            "Guinea",
            "Saint Pierre and Miquelon",
            "Bahamas",
            "Japan"
          ]
        },
        {
          "field": "year",
          "operator": "range",
          "min": 1988,
          "max": 2023
        }
      ],
      "relation_tags": [
        "country_or_region_relation",
        "shared_entity",
        "shared_measure",
        "shared_time_axis",
        "source_owid",
        "theme_owid"
      ],
      "role_hint": "real-v2 owid subplot 1",
      "llm_generation_notes": [
        "Use the referenced processed CSV file.",
        "Use matplotlib, seaborn, or pandas plotting APIs.",
        "Keep labels readable and avoid overlapping legends.",
        "Do not invent values outside the referenced data."
      ],
      "visual_template": {
        "cluster_id": "gantt_timeline_report",
        "alpha": 0.775,
        "linewidth": 1.173,
        "label_rotation": 8,
        "grid_alpha": 0.139,
        "title_size": 9,
        "legend_fontsize": 6,
        "continuous_sampling": {
          "enabled": true,
          "seed": 20347003,
          "note": "Cluster identity is discrete; numeric rendering parameters are deterministically jittered within bounded ranges."
        },
        "family": "process_family",
        "selection_policy": "deterministic mixed cluster assignment plus bounded continuous parameter sampling"
      },
      "data_transform": {
        "transform_id": "top_k_by_measure",
        "category": "entity",
        "measure": "renewables",
        "k": 8,
        "description": "Keep the highest categories by mean measure value.",
        "selection_policy": "deterministic data-transform sampling constrained by chart type and encodings",
        "seed": 20453787
      }
    },
    {
      "chart_id": "chart_2",
      "chart_type": "gantt",
      "title": "Owid real-v2 view 2",
      "data_source": {
        "dataset_id": "owid_annual_co2_emissions",
        "processed_file": "processed/owid/owid_annual_co2_emissions.csv"
      },
      "encodings": {
        "x": "year",
        "y": "annual_co2_emissions",
        "color_by": "entity",
        "size_by": null,
        "group_by": "entity"
      },
      "filters": [
        {
          "field": "entity",
          "operator": "in",
          "values": [
            "Switzerland",
            "United States",
            "India",
            "Cote d'Ivoire"
          ]
        },
        {
          "field": "year",
          "operator": "range",
          "min": 1831,
          "max": 2019
        }
      ],
      "relation_tags": [
        "country_or_region_relation",
        "shared_entity",
        "shared_measure",
        "shared_time_axis",
        "source_owid",
        "theme_owid"
      ],
      "role_hint": "real-v2 owid subplot 2",
      "llm_generation_notes": [
        "Use the referenced processed CSV file.",
        "Use matplotlib, seaborn, or pandas plotting APIs.",
        "Keep labels readable and avoid overlapping legends.",
        "Do not invent values outside the referenced data."
      ],
      "visual_template": {
        "cluster_id": "funnel_centered_stages",
        "alpha": 0.79,
        "linewidth": 0.68,
        "label_rotation": 8,
        "grid_alpha": 0.24,
        "title_size": 11,
        "legend_fontsize": 6,
        "continuous_sampling": {
          "enabled": true,
          "seed": 20345954,
          "note": "Cluster identity is discrete; numeric rendering parameters are deterministically jittered within bounded ranges."
        },
        "family": "process_family",
        "selection_policy": "deterministic mixed cluster assignment plus bounded continuous parameter sampling"
      },
      "data_transform": {
        "transform_id": "rolling_mean",
        "x": "year",
        "measure": "annual_co2_emissions",
        "group_by": "entity",
        "window": 3,
        "description": "Smooth the numeric measure over the ordered x axis.",
        "selection_policy": "deterministic data-transform sampling constrained by chart type and encodings",
        "seed": 20398619
      }
    }
  ],
  "relation_graph": {
    "nodes": [
      {
        "chart_id": "chart_1",
        "chart_type": "funnel",
        "dataset_id": "owid_share_electricity_renewables",
        "relation_tags": [
          "country_or_region_relation",
          "shared_entity",
          "shared_measure",
          "shared_time_axis",
          "source_owid",
          "theme_owid"
        ]
      },
      {
        "chart_id": "chart_2",
        "chart_type": "gantt",
        "dataset_id": "owid_annual_co2_emissions",
        "relation_tags": [
          "country_or_region_relation",
          "shared_entity",
          "shared_measure",
          "shared_time_axis",
          "source_owid",
          "theme_owid"
        ]
      }
    ],
    "edges": [
      {
        "source": "chart_1",
        "target": "chart_2",
        "relations": [
          "country_or_region_relation",
          "shared_entity",
          "shared_measure",
          "shared_time_axis",
          "source_owid",
          "theme_owid"
        ]
      }
    ]
  },
  "candidate_edit_operations": [
    "modify_color",
    "delete_category",
    "rename_label",
    "add_reference_line",
    "add_event_marker",
    "modify_style",
    "add_dashboard_title",
    "change_axis_label",
    "filter_time_range",
    "reorder_categories"
  ],
  "visual_template_policy": {
    "name": "real-v2 hybrid visual configuration generator",
    "cluster_count_by_family": {
      "line_family": 3,
      "step_line_family": 3,
      "area_family": 3,
      "bar_family": 3,
      "ranking_family": 3,
      "composition_family": 3,
      "scatter_family": 3,
      "density2d_family": 3,
      "distribution_family": 3,
      "empirical_distribution_family": 3,
      "box_violin_family": 3,
      "heatmap_family": 3,
      "pie_family": 3,
      "combo_family": 3,
      "radar_family": 3,
      "hierarchy_family": 3,
      "flow_family": 3,
      "finance_family": 3,
      "map_family": 3,
      "process_family": 3
    },
    "continuous_parameter_sampling": true,
    "layout_sampling": true,
    "dashboard_theme_sampling": true,
    "data_transform_sampling": true
  },
  "instruction_complexity_plan": {
    "single_step_ratio": 0.4,
    "multi_step_ratio": 0.6,
    "max_steps": 6
  },
  "data_quality_constraints": [
    "Use only rows from referenced processed CSV files.",
    "Avoid charts with fewer than 3 visible data points.",
    "Avoid all-zero visible marks.",
    "Preserve relation and source semantics in edits."
  ]
}''')

OPERATIONS = json.loads(r'''[
  {
    "operation": "modify_color",
    "target": "Guinea",
    "color": "red",
    "scope": "relation_tag",
    "relation_tag": "country_or_region_relation"
  },
  {
    "operation": "rename_label",
    "target": "Guinea",
    "new_label": "Guinea (updated)",
    "scope": "relation_tag",
    "relation_tag": "country_or_region_relation"
  },
  {
    "operation": "add_event_marker",
    "x": 1925,
    "label": "Event 1925",
    "color": "red",
    "scope": "time_series_charts"
  }
]''')

if __name__ == "__main__":
    render_dashboard(SPEC, OPERATIONS, "target_image.png")
