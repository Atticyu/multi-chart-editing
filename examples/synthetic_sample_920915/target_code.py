
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

SPEC = json.loads(r"""{"dashboard_id": "dashboard_aug_0433", "domain": "hospital_operations", "data_origin": "synthetic_relation_augmented_qc", "title": "Hospital Operations Augmented Dashboard", "theme": {"id": "muted_publication", "bg": "#FAFAF7", "ax": "#FFFFFC", "grid": "#DDD6C9", "palette": ["#3B6EA8", "#C06C2E", "#6A994E", "#9D4EDD", "#BC4749", "#2A9D8F"]}, "charts": [{"chart_id": "chart_1", "chart_type": "lollipop", "title": "Hospital Operations view 1: lollipop", "data_key": "data_1", "enc": {"x": "category", "y": "value"}, "relation_tags": ["domain_hospital_operations", "synthetic_relation_augmented_qc", "shared_theme", "shared_visible_labels"]}, {"chart_id": "chart_2", "chart_type": "waterfall", "title": "Hospital Operations view 2: waterfall", "data_key": "data_2", "enc": {"x": "category", "y": "value"}, "relation_tags": ["domain_hospital_operations", "synthetic_relation_augmented_qc", "shared_theme", "shared_visible_labels"]}, {"chart_id": "chart_3", "chart_type": "candlestick", "title": "Hospital Operations view 3: candlestick", "data_key": "data_3", "enc": {}, "relation_tags": ["domain_hospital_operations", "synthetic_relation_augmented_qc", "shared_theme", "shared_visible_labels"]}, {"chart_id": "chart_4", "chart_type": "stacked_bar", "title": "Hospital Operations view 4: stacked bar", "data_key": "data_4", "enc": {"x": "category", "y": "value", "group": "segment"}, "relation_tags": ["domain_hospital_operations", "synthetic_relation_augmented_qc", "shared_theme", "shared_visible_labels"]}, {"chart_id": "chart_5", "chart_type": "dot_plot", "title": "Hospital Operations view 5: dot plot", "data_key": "data_5", "enc": {"x": "category", "y": "value"}, "relation_tags": ["domain_hospital_operations", "synthetic_relation_augmented_qc", "shared_theme", "shared_visible_labels"]}], "quality_constraints": ["No empty subplots", "At least three x values for line/area charts", "Reference lines only on standard numeric-y charts", "Edit targets use visible labels rather than encoding field names", "Most edit instructions affect labels or comparable encodings across multiple subplots"]}""")
DATASETS = json.loads(r"""{"data_1": [{"category": "North", "value": 176.633}, {"category": "Central", "value": 185.879}, {"category": "West", "value": 171.102}, {"category": "East", "value": 244.724}, {"category": "South", "value": 255.146}, {"category": "Metro", "value": 59.153}], "data_2": [{"category": "North", "value": 120.2}, {"category": "Central", "value": 73.524}, {"category": "West", "value": 47.112}, {"category": "East", "value": 169.439}, {"category": "South", "value": 217.848}, {"category": "Metro", "value": 119.422}], "data_3": [{"date": "2014", "open": 151.397, "high": 156.773, "low": 149.052, "close": 154.427}, {"date": "2015", "open": 154.427, "high": 159.498, "low": 146.931, "close": 149.063}, {"date": "2016", "open": 149.063, "high": 152.959, "low": 145.962, "close": 150.1}, {"date": "2017", "open": 150.1, "high": 155.01, "low": 140.072, "close": 144.345}, {"date": "2018", "open": 144.345, "high": 146.613, "low": 133.149, "close": 138.333}, {"date": "2019", "open": 138.333, "high": 150.118, "low": 135.198, "close": 147.087}, {"date": "2020", "open": 147.087, "high": 154.579, "low": 141.008, "close": 148.233}, {"date": "2021", "open": 148.233, "high": 165.269, "low": 145.17, "close": 160.767}, {"date": "2022", "open": 160.767, "high": 163.761, "low": 151.363, "close": 154.152}, {"date": "2023", "open": 154.152, "high": 160.775, "low": 141.353, "close": 144.685}, {"date": "2024", "open": 144.685, "high": 146.4, "low": 130.935, "close": 138.6}, {"date": "2025", "open": 138.6, "high": 142.039, "low": 128.873, "close": 132.753}], "data_4": [{"category": "North", "segment": "baseline", "value": 133.632}, {"category": "North", "segment": "growth", "value": 89.04}, {"category": "North", "segment": "priority", "value": 243.456}, {"category": "Central", "segment": "baseline", "value": 69.555}, {"category": "Central", "segment": "growth", "value": 130.506}, {"category": "Central", "segment": "priority", "value": 216.546}, {"category": "West", "segment": "baseline", "value": 86.28}, {"category": "West", "segment": "growth", "value": 205.234}, {"category": "West", "segment": "priority", "value": 75.143}, {"category": "East", "segment": "baseline", "value": 102.076}, {"category": "East", "segment": "growth", "value": 70.976}, {"category": "East", "segment": "priority", "value": 199.842}, {"category": "South", "segment": "baseline", "value": 56.552}, {"category": "South", "segment": "growth", "value": 113.792}, {"category": "South", "segment": "priority", "value": 162.433}], "data_5": [{"category": "North", "value": 173.988}, {"category": "Central", "value": 94.101}, {"category": "West", "value": 89.599}, {"category": "East", "value": 108.494}, {"category": "South", "value": 226.215}, {"category": "Metro", "value": 119.655}]}""")
OPERATIONS = json.loads(r"""[{"operation": "modify_style", "scope": "all_charts"}, {"operation": "change_axis_label", "axis": "y", "new_label": "Comparable value", "scope": "chart_id", "chart_id": "chart_1"}, {"operation": "change_axis_label", "axis": "y", "new_label": "Comparable value", "scope": "chart_id", "chart_id": "chart_2"}, {"operation": "change_axis_label", "axis": "y", "new_label": "Comparable value", "scope": "chart_id", "chart_id": "chart_4"}, {"operation": "change_axis_label", "axis": "y", "new_label": "Comparable value", "scope": "chart_id", "chart_id": "chart_5"}]""")
OUTPUT_FILE = "target_image.png"

def _df(key):
    return pd.DataFrame(DATASETS[key])

def _pretty(text):
    return str(text).replace("_", " ").title()

def _ops(chart):
    out = []
    for op in OPERATIONS:
        if op.get("scope") == "all_charts":
            out.append(op)
        elif op.get("scope") == "chart_id" and op.get("chart_id") == chart["chart_id"]:
            out.append(op)
        elif op.get("scope") == "safe_numeric_y_charts" and chart.get("chart_type") in {"line","multi_line","step_line","area","stacked_area","bar","horizontal_bar","grouped_bar","stacked_bar","stacked_horizontal_bar","proportional_bar","lollipop","dot_plot","waterfall"}:
            out.append(op)
        elif op.get("scope") == "charts_where_label_appears":
            out.append(op)
    return out

def _apply_data_ops(df, chart):
    out = df.copy()
    for op in OPERATIONS:
        if op.get("operation") == "rename_label":
            target, new = str(op.get("target")), str(op.get("new_label"))
            for col in out.columns:
                if out[col].dtype == object:
                    out[col] = out[col].astype(str).replace(target, new)
        if op.get("operation") == "delete_category_or_series":
            target = str(op.get("target"))
            for col in out.columns:
                if out[col].dtype == object and target in set(out[col].astype(str)):
                    out = out[out[col].astype(str) != target]
    return out

def _color_map(chart):
    cmap = {}
    for op in OPERATIONS:
        if op.get("operation") == "modify_color":
            label = str(op.get("target"))
            for rename in OPERATIONS:
                if rename.get("operation") == "rename_label" and str(rename.get("target")) == label:
                    label = str(rename.get("new_label", label))
            cmap[label] = op.get("color", "#DC2626")
    return cmap

def _palette(labels, chart):
    base = chart.get("theme", {}).get("palette") or SPEC["theme"]["palette"]
    cmap = _color_map(chart)
    return {str(label): cmap.get(str(label), base[i % len(base)]) for i, label in enumerate(labels)}

def _final_type(chart):
    ctype = chart["chart_type"]
    for op in _ops(chart):
        if op.get("operation") == "change_chart_type":
            ctype = op.get("new_chart_type", ctype)
    return ctype

def _label_ops(ax, chart, x=None, y=None):
    if x:
        ax.set_xlabel(_pretty(x))
    if y:
        ax.set_ylabel(_pretty(y))
    for op in _ops(chart):
        if op.get("operation") == "change_axis_label":
            if op.get("axis") == "x": ax.set_xlabel(op.get("new_label", ""))
            if op.get("axis") == "y": ax.set_ylabel(op.get("new_label", ""))

def _maybe_ref(ax, chart, data, y):
    if not y or y not in data.columns:
        return
    for op in _ops(chart):
        if op.get("operation") == "add_reference_line":
            vals = pd.to_numeric(data[y], errors="coerce").dropna()
            if len(vals):
                value = vals.mean() if op.get("y") == "mean" else float(op.get("y"))
                lo, hi = float(vals.min()), float(vals.max())
                span = max(hi - lo, 1e-9)
                if lo - 0.2 * span <= value <= hi + 0.2 * span:
                    ax.axhline(value, color=op.get("color", "purple"), linestyle="--", linewidth=1.4)
                    ax.text(0.98, 0.94, op.get("label", "Reference mean"), transform=ax.transAxes, ha="right", va="top", fontsize=7, color=op.get("color", "purple"))

def plot_time(ax, data, chart, ctype):
    x, y, group = chart["enc"]["x"], chart["enc"]["y"], chart["enc"].get("group")
    data = data.copy()
    data[x] = pd.to_numeric(data[x], errors="coerce")
    data[y] = pd.to_numeric(data[y], errors="coerce")
    colors = _palette(sorted(data[group].astype(str).unique()) if group else ["series"], chart)
    if group:
        labels = sorted(data[group].astype(str).unique())[:6]
        pivot = data[data[group].astype(str).isin(labels)].pivot_table(index=x, columns=group, values=y, aggfunc="mean").sort_index().fillna(0)
        if ctype == "stacked_area":
            ax.stackplot(pivot.index.values, [pivot[c].values for c in pivot.columns], labels=[str(c) for c in pivot.columns], colors=[colors[str(c)] for c in pivot.columns], alpha=0.72)
        else:
            for label in labels:
                g = data[data[group].astype(str) == str(label)].sort_values(x)
                if ctype == "step_line":
                    ax.step(g[x], g[y], where="mid", label=str(label), color=colors[str(label)], linewidth=1.7)
                elif ctype == "area":
                    ax.fill_between(g[x].values, g[y].values, alpha=0.22, color=colors[str(label)])
                    ax.plot(g[x], g[y], label=str(label), color=colors[str(label)], linewidth=1.7)
                else:
                    ax.plot(g[x], g[y], marker="o", markersize=3, label=str(label), color=colors[str(label)], linewidth=1.7)
        if len(labels) <= 6:
            ax.legend(frameon=False, fontsize=7, loc="best")
    else:
        g = data.groupby(x, as_index=False)[y].mean().sort_values(x)
        if ctype == "area":
            ax.fill_between(g[x].values, g[y].values, alpha=0.3)
        ax.plot(g[x], g[y], marker="o", linewidth=1.8)
    _label_ops(ax, chart, x, y)
    _maybe_ref(ax, chart, data, y)

def plot_bar(ax, data, chart, ctype):
    x, y, group = chart["enc"]["x"], chart["enc"]["y"], chart["enc"].get("group")
    data = data.copy()
    data[y] = pd.to_numeric(data[y], errors="coerce")
    if ctype in {"grouped_bar", "stacked_bar", "stacked_horizontal_bar", "proportional_bar"} and group:
        pivot = data.pivot_table(index=x, columns=group, values=y, aggfunc="mean").fillna(0)
        colors = _palette([str(c) for c in pivot.columns], chart)
        if ctype == "grouped_bar":
            pivot.plot(kind="bar", ax=ax, color=[colors[str(c)] for c in pivot.columns], width=0.78)
        elif ctype == "stacked_horizontal_bar":
            pivot.plot(kind="barh", stacked=True, ax=ax, color=[colors[str(c)] for c in pivot.columns])
        else:
            if ctype == "proportional_bar":
                pivot = pivot.div(pivot.sum(axis=1).replace(0, np.nan), axis=0).fillna(0) * 100
            pivot.plot(kind="bar", stacked=True, ax=ax, color=[colors[str(c)] for c in pivot.columns], width=0.78)
        ax.legend(frameon=False, fontsize=7, loc="best")
    else:
        vals = data.groupby(x)[y].mean().sort_values(ascending=False).head(8)
        colors = _palette([str(i) for i in vals.index], chart)
        if ctype == "horizontal_bar":
            ax.barh([str(i) for i in vals.index], vals.values, color=[colors[str(i)] for i in vals.index])
        elif ctype in {"lollipop", "dot_plot"}:
            ypos = np.arange(len(vals))[::-1]
            ax.hlines(ypos, 0, vals.values, color="#94A3B8", linewidth=1.2)
            ax.scatter(vals.values, ypos, color=[colors[str(i)] for i in vals.index], s=50)
            ax.set_yticks(ypos); ax.set_yticklabels([str(i) for i in vals.index])
        elif ctype == "waterfall":
            starts = np.r_[0, np.cumsum(vals.values[:-1])]
            ax.bar([str(i) for i in vals.index], vals.values, bottom=starts, color=[colors[str(i)] for i in vals.index])
            ax.tick_params(axis="x", labelrotation=35)
        else:
            ax.bar([str(i) for i in vals.index], vals.values, color=[colors[str(i)] for i in vals.index])
            ax.tick_params(axis="x", labelrotation=35)
    _label_ops(ax, chart, x, y)
    _maybe_ref(ax, chart, data, y)

def plot_scatter(ax, data, chart, ctype):
    x, y, group = chart["enc"]["x"], chart["enc"]["y"], chart["enc"].get("group")
    data = data.copy()
    data[x] = pd.to_numeric(data[x], errors="coerce")
    data[y] = pd.to_numeric(data[y], errors="coerce")
    data = data.dropna(subset=[x,y])
    if ctype == "hexbin":
        hb = ax.hexbin(data[x], data[y], gridsize=24, cmap="viridis", mincnt=1)
        plt.colorbar(hb, ax=ax, fraction=0.046, pad=0.04)
    elif ctype == "contour_density":
        hist, xe, ye = np.histogram2d(data[x], data[y], bins=25)
        xx = (xe[:-1] + xe[1:]) / 2; yy = (ye[:-1] + ye[1:]) / 2
        cf = ax.contourf(xx, yy, hist.T, levels=6, cmap="viridis", alpha=0.75)
        plt.colorbar(cf, ax=ax, fraction=0.046, pad=0.04)
    elif group:
        labels = sorted(data[group].astype(str).unique())[:6]
        colors = _palette(labels, chart)
        for label in labels:
            g = data[data[group].astype(str)==label]
            size = pd.to_numeric(g.get(chart["enc"].get("size", y), 40), errors="coerce")
            size = 40 if ctype == "scatter" else 25 + 80 * (size - size.min()) / max(float(size.max() - size.min()), 1e-9)
            ax.scatter(g[x], g[y], s=size, alpha=0.72, label=label, color=colors[label], edgecolor="white", linewidth=0.35)
        ax.legend(frameon=False, fontsize=7, loc="best")
    else:
        ax.scatter(data[x], data[y], s=42, alpha=0.72, edgecolor="white", linewidth=0.35)
    _label_ops(ax, chart, x, y)

def plot_distribution(ax, data, chart, ctype):
    y, group = chart["enc"]["y"], chart["enc"].get("group")
    data = data.copy(); data[y] = pd.to_numeric(data[y], errors="coerce"); data = data.dropna(subset=[y])
    if ctype == "histogram":
        ax.hist(data[y], bins=20, color=SPEC["theme"]["palette"][0], alpha=0.75)
    elif ctype == "density":
        vals = np.sort(data[y].values)
        ax.hist(vals, bins=26, density=True, alpha=0.28, color=SPEC["theme"]["palette"][0])
        ax.plot(vals, np.linspace(0, 1 / max(np.std(vals), 1e-9), len(vals)), color=SPEC["theme"]["palette"][1])
    elif ctype == "ecdf":
        vals = np.sort(data[y].values); ax.step(vals, np.arange(1, len(vals)+1)/len(vals), where="post")
    elif ctype == "strip_plot":
        labels = sorted(data[group].astype(str).unique())[:6]
        colors = _palette(labels, chart)
        seed_text = f"{SPEC.get('dashboard_id', '')}:{chart.get('chart_id', '')}"
        rng = np.random.default_rng(sum((j + 1) * ord(ch) for j, ch in enumerate(seed_text)) % (2**32))
        for i,label in enumerate(labels):
            vals = data[data[group].astype(str)==label][y]
            ax.scatter(rng.normal(i,0.05,len(vals)), vals, s=20, alpha=0.55, color=colors[label])
        ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=30, ha="right")
    elif ctype == "box":
        labels = sorted(data[group].astype(str).unique())[:6]
        ax.boxplot([data[data[group].astype(str)==label][y] for label in labels], labels=labels)
        ax.tick_params(axis="x", labelrotation=30)
    elif ctype == "violin":
        labels = sorted(data[group].astype(str).unique())[:6]
        ax.violinplot([data[data[group].astype(str)==label][y] for label in labels], showmeans=True)
        ax.set_xticks(range(1,len(labels)+1)); ax.set_xticklabels(labels, rotation=30, ha="right")
    _label_ops(ax, chart, None, y)

def plot_heat(ax, data, chart, ctype):
    if ctype == "correlation_heatmap":
        nums = data.select_dtypes(include=[np.number]).iloc[:, :6]
        mat = nums.corr().fillna(0).values
        labels = list(nums.columns)
    else:
        rows = sorted(data[chart["enc"]["row"]].astype(str).unique())[:8]
        cols = sorted(data[chart["enc"]["col"]].astype(str).unique())[:8]
        pivot = data.pivot_table(index=chart["enc"]["row"], columns=chart["enc"]["col"], values=chart["enc"]["y"], aggfunc="mean").reindex(index=rows, columns=cols).fillna(0)
        mat = pivot.values; labels = cols
        ax.set_yticks(range(len(rows))); ax.set_yticklabels(rows)
    im = ax.imshow(mat, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=35, ha="right")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

def plot_part_whole(ax, data, chart, ctype):
    cat, y = chart["enc"]["x"], chart["enc"]["y"]
    vals = data.groupby(cat)[y].mean().sort_values(ascending=False).head(7)
    colors = _palette([str(i) for i in vals.index], chart)
    if ctype in {"pie","donut"}:
        wedges, _ = ax.pie(vals.values, colors=[colors[str(i)] for i in vals.index], startangle=90, wedgeprops={"width":0.45} if ctype=="donut" else None)
        ax.legend(wedges, [str(i) for i in vals.index], frameon=False, fontsize=7, loc="center left", bbox_to_anchor=(1.0,0.5))
    elif ctype == "treemap":
        total = float(vals.sum()); x0=y0=0; w=h=1; horiz=True
        for label, value in vals.items():
            frac = float(value)/total
            if horiz:
                ww = w*frac; rect=(x0,y0,ww,h); cx=x0+ww/2; cy=y0+h/2; x0 += ww; w -= ww
            else:
                hh = h*frac; rect=(x0,y0,w,hh); cx=x0+w/2; cy=y0+hh/2; y0 += hh; h -= hh
            ax.add_patch(Rectangle((rect[0],rect[1]),rect[2],rect[3],facecolor=colors[str(label)],edgecolor="white",alpha=0.85))
            ax.text(cx, cy, str(label)[:14], ha="center", va="center", fontsize=7)
            horiz = not horiz
        ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
    elif ctype == "funnel":
        maxv = vals.max()
        for i,(label,value) in enumerate(vals.items()):
            width = value/maxv
            ax.barh(i, width, left=(1-width)/2, color=colors[str(label)], height=0.72)
            ax.text(0.5, i, str(label), ha="center", va="center", fontsize=7)
        ax.invert_yaxis(); ax.set_xlim(0,1); ax.set_axis_off()

def plot_advanced(ax, data, chart, ctype):
    if ctype == "radar":
        labels = chart["enc"]["metrics"]; group = chart["enc"]["group"]
        groups = sorted(data[group].astype(str).unique())[:4]
        angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
        angles += angles[:1]
        colors = _palette(groups, chart)
        for gname in groups:
            vals = data[data[group].astype(str)==gname][labels].mean().values
            vals = (vals - vals.min()) / max(float(vals.max()-vals.min()), 1e-9)
            vals = vals.tolist() + [float(vals[0])]
            ax.plot(angles, vals, color=colors[gname], label=gname, marker="o", linewidth=1.4)
            ax.fill(angles, vals, alpha=0.10, color=colors[gname])
        ax.set_xticks(angles[:-1]); ax.set_xticklabels([_pretty(x) for x in labels], fontsize=8)
        ax.set_ylim(0, 1.05)
        ax.legend(frameon=False, fontsize=7, loc="lower center", bbox_to_anchor=(0.5, -0.22), ncol=2)
    elif ctype == "sankey":
        sources = sorted(data["source"].unique()); targets = sorted(data["target"].unique())
        sy = np.linspace(0.15,0.85,len(sources)); ty = np.linspace(0.15,0.85,len(targets))
        colors = _palette(sources+targets, chart)
        for s,y in zip(sources,sy): ax.text(0.05,y,s,ha="left",va="center",fontsize=8); ax.scatter([0.22],[y],s=120,color=colors[s])
        for t,y in zip(targets,ty): ax.text(0.95,y,t,ha="right",va="center",fontsize=8); ax.scatter([0.78],[y],s=120,color=colors[t])
        for _,r in data.iterrows():
            y1=sy[sources.index(r["source"])]; y2=ty[targets.index(r["target"])]
            ax.plot([0.24,0.76],[y1,y2],linewidth=max(1,float(r["value"])/20),alpha=0.35,color=colors[r["source"]])
        ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_axis_off()
    elif ctype == "candlestick":
        x = np.arange(len(data)); up = data["close"] >= data["open"]
        for i,row in data.iterrows():
            color = "#16A34A" if row["close"] >= row["open"] else "#DC2626"
            ax.vlines(i, row["low"], row["high"], color=color, linewidth=1)
            ax.add_patch(Rectangle((i-0.28, min(row["open"],row["close"])),0.56,abs(row["close"]-row["open"])+1e-6,facecolor=color,alpha=0.75))
        ax.set_xticks(x[::max(1,len(x)//6)]); ax.set_xticklabels(data["date"].iloc[::max(1,len(x)//6)], rotation=30)
        _label_ops(ax, chart, "date", "price")
    elif ctype == "choropleth_map":
        cat,y = chart["enc"]["x"],chart["enc"]["y"]
        vals = data.groupby(cat)[y].mean().sort_values(ascending=False).head(9)
        norm = plt.Normalize(vals.min(), vals.max()); cmap=plt.get_cmap("viridis")
        for i,(label,value) in enumerate(vals.items()):
            r,c=divmod(i,3); color=cmap(norm(value))
            ax.add_patch(Rectangle((c,r),0.95,0.85,facecolor=color,edgecolor="white"))
            ax.text(c+0.48,r+0.42,str(label)[:12],ha="center",va="center",fontsize=7)
        ax.set_xlim(0,3); ax.set_ylim(0,3); ax.invert_yaxis(); ax.set_axis_off()
        plt.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap), ax=ax, fraction=0.046, pad=0.04)
    elif ctype == "gantt":
        tasks = list(data["task"]); colors = _palette(tasks, chart)
        ax.barh(tasks, data["duration"], left=data["start"], color=[colors[t] for t in tasks], alpha=0.8)
        _label_ops(ax, chart, "start", "task")

def plot_error_dual(ax, data, chart, ctype):
    if ctype == "error_bar":
        x,y = chart["enc"]["x"],chart["enc"]["y"]
        g = data.groupby(x)[y].agg(["mean","std"]).sort_index()
        ax.errorbar(g.index, g["mean"], yerr=g["std"].fillna(0), fmt="o-", capsize=4, color=SPEC["theme"]["palette"][0])
        _label_ops(ax, chart, x, y); _maybe_ref(ax, chart, data, y)
    else:
        x,y = chart["enc"]["x"],chart["enc"]["y"]
        g = data.groupby(x)[y].mean().sort_index()
        ax.bar(g.index, g.values, color=SPEC["theme"]["palette"][0], alpha=0.42)
        ax2 = ax.twinx(); ax2.plot(g.index, g.rolling(3,min_periods=1).mean().values, color=SPEC["theme"]["palette"][1], marker="o")
        _label_ops(ax, chart, x, y); ax2.set_ylabel("Rolling mean")

def draw_chart(ax, chart):
    ctype = _final_type(chart)
    data = _apply_data_ops(_df(chart["data_key"]), chart)
    chart["theme"] = SPEC["theme"]
    if ctype in {"line","multi_line","step_line","area","stacked_area"}: plot_time(ax,data,chart,ctype)
    elif ctype in {"bar","horizontal_bar","grouped_bar","stacked_bar","stacked_horizontal_bar","proportional_bar","lollipop","dot_plot","waterfall"}: plot_bar(ax,data,chart,ctype)
    elif ctype in {"scatter","bubble","hexbin","contour_density"}: plot_scatter(ax,data,chart,ctype)
    elif ctype in {"histogram","density","ecdf","strip_plot","box","violin"}: plot_distribution(ax,data,chart,ctype)
    elif ctype in {"heatmap","correlation_heatmap"}: plot_heat(ax,data,chart,ctype)
    elif ctype in {"pie","donut","treemap","funnel"}: plot_part_whole(ax,data,chart,ctype)
    elif ctype in {"radar","sankey","candlestick","choropleth_map","gantt"}: plot_advanced(ax,data,chart,ctype)
    elif ctype in {"dual_axis_line_bar","error_bar"}: plot_error_dual(ax,data,chart,ctype)
    else: plot_bar(ax,data,chart,"bar")
    title_color = "#123A6F" if any(op.get("operation")=="modify_style" for op in _ops(chart)) else "#111827"
    ax.set_title(chart.get("title",""), color=title_color, fontsize=10, pad=8)
    if any(op.get("operation")=="modify_style" for op in _ops(chart)):
        ax.grid(True, linestyle="--", alpha=0.35, color=SPEC["theme"]["grid"])
    else:
        ax.grid(True, alpha=0.22, color=SPEC["theme"]["grid"])
    for spine in ax.spines.values(): spine.set_alpha(0.55)

def render():
    charts = SPEC["charts"]
    n = len(charts)
    cols = 2 if n <= 4 else 3
    rows = math.ceil(n/cols)
    fig = plt.figure(figsize=(cols*5.0, rows*3.6), facecolor=SPEC["theme"]["bg"])
    axes = []
    for i,chart in enumerate(charts, start=1):
        chart["_subplot_spec"] = (rows, cols, i)
        preview_type = _final_type(chart)
        ax = fig.add_subplot(rows, cols, i, polar=(preview_type == "radar"))
        ax.set_facecolor(SPEC["theme"]["ax"])
        draw_chart(ax, chart)
        axes.append(ax)
    for i in range(n+1, rows*cols+1):
        ax = fig.add_subplot(rows, cols, i); ax.axis("off")
    for op in OPERATIONS:
        if op.get("operation") == "add_dashboard_title":
            fig.suptitle(op.get("title", SPEC.get("title","")), fontsize=14, y=0.995)
    fig.tight_layout(rect=[0,0,1,0.96])
    fig.savefig(OUTPUT_FILE, dpi=140)
    plt.close(fig)

if __name__ == "__main__":
    render()
