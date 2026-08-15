"""Generate the five empirical manuscript figures from frozen audit evidence.

The artwork is deliberately evidence-first: white paper, thin rules, small
type, restrained colour and direct quantitative encodings.  It is not an
infographic layer and does not add claims beyond the source tables.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

ROOT = Path(__file__).resolve().parent
PKG = ROOT.parent
DATA = ROOT / "figure_source_data"
VECTOR = ROOT / "vector"
PREVIEW = ROOT / "qa_preview"
FIG_W = 183 / 25.4

C = {
    "ink": "#20262B", "blue": "#355F83", "teal": "#317B73",
    "red": "#B24E49", "amber": "#A77B25", "mid": "#7C8993",
    "light": "#D7E0E6", "faint": "#EEF2F4", "white": "#FFFFFF",
}
mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "Liberation Serif", "DejaVu Serif"],
    "font.size": 9.0, "axes.titlesize": 10.0, "axes.titleweight": "bold",
    "axes.labelsize": 8.8, "xtick.labelsize": 8.0, "ytick.labelsize": 8.0,
    "svg.hashsalt": "poca-result-figures-v1",
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": .7,
    "axes.edgecolor": C["ink"], "xtick.color": C["ink"], "ytick.color": C["ink"],
    "text.color": C["ink"], "legend.frameon": False, "svg.fonttype": "none",
    "pdf.fonttype": 42, "figure.facecolor": "white", "savefig.facecolor": "white",
})


def rows(path: Path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def save(fig, stem: str):
    VECTOR.mkdir(exist_ok=True); PREVIEW.mkdir(exist_ok=True)
    kw = dict(bbox_inches="tight", pad_inches=.025)
    svg_meta = {"Date": "2026-01-01T00:00:00", "Creator": "Python/Matplotlib reproducible figure generator"}
    pdf_meta = {"CreationDate": None, "ModDate": None,
                "Creator": "Python/Matplotlib reproducible figure generator",
                "Producer": "Matplotlib"}
    fig.savefig(VECTOR / f"{stem}.svg", metadata=svg_meta, **kw)
    fig.savefig(VECTOR / f"{stem}.pdf", metadata=pdf_meta, **kw)
    fig.savefig(VECTOR / f"{stem}.tiff", dpi=600, **kw)
    fig.savefig(PREVIEW / f"{stem}.png", dpi=300, **kw)
    plt.close(fig)


def panel(ax, letter, heading, subtitle=None):
    ax.text(-.08, 1.045, letter, transform=ax.transAxes, fontsize=11,
            fontweight="bold", va="bottom", clip_on=False)
    ax.text(0, 1.045, heading, transform=ax.transAxes, fontsize=9.8,
            fontweight="bold", va="bottom", clip_on=False)
    if subtitle:
        ax.text(0, .995, subtitle, transform=ax.transAxes, fontsize=7.2,
                color=C["mid"], va="bottom", clip_on=False)


def axis_clean(ax, left=False, bottom=False):
    for n, sp in ax.spines.items():
        sp.set_visible((n == "left" and left) or (n == "bottom" and bottom))
    ax.tick_params(length=2.4 if (left or bottom) else 0, width=.65, pad=2)


def arrow(ax, xy0, xy1, color=C["ink"], lw=.8):
    ax.add_patch(FancyArrowPatch(xy0, xy1, arrowstyle="-|>", mutation_scale=6,
                                 lw=lw, color=color, shrinkA=0, shrinkB=0))


def derive_effective(local):
    out, blocked = [], False
    for value in local:
        if blocked:
            out.append("BLOCKED")
        else:
            out.append(value)
            if value != "PASS": blocked = True
    return out


STATUS_COLORS = {"PASS": C["teal"], "FAIL": C["red"], "INDETERMINATE": C["amber"],
                 "NOT_TESTED": C["mid"], "BLOCKED": C["blue"]}
STATUS_GLYPHS = {"PASS": "P", "FAIL": "F", "INDETERMINATE": "I",
                 "NOT_TESTED": "NT", "BLOCKED": "B"}
STATUS_CODES = {"PASS": 0, "FAIL": 1, "INDETERMINATE": 2,
                "NOT_TESTED": 3, "BLOCKED": 4}


def status_heatmap(ax, matrix, names, layers):
    """Render categorical audit outcomes as a compact data matrix."""
    palette = [C["teal"], C["red"], C["amber"], "#E5E8EA", C["blue"]]
    ax.set_xlim(-.5, len(layers) - .5)
    ax.set_ylim(len(names) - .5, -.5)
    ax.set_aspect("auto")
    for y, row in enumerate(matrix):
        for x, value in enumerate(row):
            ax.add_patch(Rectangle((x - .5, y - .5), 1, 1,
                                   facecolor=palette[STATUS_CODES[value]],
                                   edgecolor="none", zorder=0))
            text_color = C["white"] if value in ("PASS", "FAIL", "BLOCKED") else C["ink"]
            ax.text(x, y, STATUS_GLYPHS[value], ha="center", va="center", fontsize=8.0,
                    color=text_color, fontweight="bold")
    ax.set_xticks(range(len(layers)), layers)
    ax.set_yticks(range(len(names)), names)
    ax.tick_params(length=0, pad=3)
    for spine in ax.spines.values():
        spine.set_visible(True); spine.set_color(C["light"]); spine.set_linewidth(.7)


def status_matrix(ax, matrix, names, layers, changed=()):
    changed = set(changed)
    ax.set_xlim(-.55, 4.55); ax.set_ylim(4.55, -.55)
    for x in range(5): ax.axvline(x, color=C["light"], lw=.55, zorder=0)
    for y in range(5): ax.axhline(y, color=C["light"], lw=.55, zorder=0)
    for y, row in enumerate(matrix):
        for x, value in enumerate(row):
            color = STATUS_COLORS[value]
            filled = value in ("PASS", "FAIL", "INDETERMINATE")
            marker = "o" if value in ("PASS", "NOT_TESTED") else "X" if value == "FAIL" else "D" if value == "INDETERMINATE" else "s"
            ax.scatter(x, y, s=84 if value != "FAIL" else 96, marker=marker,
                       facecolor=color if filled else C["white"], edgecolor=color,
                       lw=1.0, zorder=2)
            ax.text(x, y, STATUS_GLYPHS[value], ha="center", va="center", fontsize=5.5,
                    fontweight="bold", color=C["white"] if filled else color, zorder=3)
            if (y, x) in changed:
                ax.add_patch(Rectangle((x-.29, y-.29), .58, .58, fill=False,
                                       edgecolor=C["red"], lw=.8, ls=(0, (2, 2))))
    ax.set_xticks(range(5), layers); ax.set_yticks(range(5), names)
    axis_clean(ax)


def fig2():
    faults = rows(PKG / "validation" / "fault_injection_results_20260720.csv")[1:]
    clean = json.loads((PKG / "extension" / "results" / "clean_control_summary.json").read_text())
    ext = json.loads((PKG / "extension" / "results" / "lshade_positive_external_20260721.json").read_text())
    fig = plt.figure(figsize=(FIG_W, 4.35))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, .85], left=.16, right=.98, top=.86, bottom=.18, wspace=.46)
    a, b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    panel(a, "a", "Expected detection gate")
    labels = ["source name", "result column", "candidate overwrite", "auxiliary calls", "reduction FE", "iteration stop", "observer RNG", "operator label"]
    gates = ["identity", "budget", "path", "observer", "replay"]; gm = {g: i for i, g in enumerate(gates)}
    arr = np.zeros((len(faults), len(gates)))
    for y, rec in enumerate(faults): arr[y, gm[rec["expected_gate"]]] = 1
    a.set_xlim(-.5, len(gates) - .5); a.set_ylim(len(labels) - .5, -.5); a.set_aspect("auto")
    for yy in range(len(labels)):
        for xx in range(len(gates)):
            a.add_patch(Rectangle((xx - .5, yy - .5), 1, 1,
                                  facecolor=C["red"] if arr[yy, xx] else "#F2F3F4",
                                  edgecolor="none", zorder=0))
    a.set_xticks(range(5), [x.upper() for x in gates]); a.set_yticks(range(8), labels)
    a.tick_params(length=0, pad=3)
    for spine in a.spines.values(): spine.set_visible(True); spine.set_color(C["light"])
    a.set_xlabel("gate receiving the injected defect")
    panel(b, "b", "Records passing the stated contract")
    categories = ["injected defects", "clean records", "external records"]
    observed = [len(faults), clean["records"] - clean["false_positives"], ext["pass_count"]]
    totals = [len(faults), clean["records"], ext["record_count"]]
    y = np.arange(3)
    b.barh(y, totals, color="#E8ECEE", height=.52, edgecolor="none")
    b.barh(y, observed, color=[C["red"], C["teal"], C["teal"]], height=.52)
    for yy, obs, total in zip(y, observed, totals):
        b.text(total + max(totals) * .025, yy, f"{obs}/{total}", va="center", fontsize=8.0)
    b.set_yticks(y, categories); b.set_xlabel("records"); b.set_xlim(0, max(totals) * 1.18)
    axis_clean(b, left=True, bottom=True)
    save(fig, "figure1_validation_coverage")


def fig3():
    data = rows(DATA / "figure3_case_status.csv"); layers = ["L1", "L2", "L3", "L4", "L5"]
    local = [[r[x] for x in layers] for r in data]; effective = [derive_effective(x) for x in local]
    names = ["Historical EPLO", "Recovered EPLO", "Later FSDC", "QSMODE", "IDE-EDA"]
    fig = plt.figure(figsize=(FIG_W, 4.35))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1], left=.16, right=.985, top=.86, bottom=.24, wspace=.52)
    a, b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    panel(a, "a", "Local audit status")
    status_heatmap(a, local, names, layers)
    panel(b, "b", "Effective claim status")
    status_heatmap(b, effective, names, layers)
    specs = [("P", "pass", C["teal"], "o", True), ("F", "fail", C["red"], "X", True),
             ("I", "indeterminate", C["amber"], "D", True), ("NT", "not tested", C["mid"], "o", False), ("B", "blocked", C["blue"], "s", False)]
    handles = [Line2D([0], [0], marker=m, linestyle="", markersize=5, markerfacecolor=col if fill else C["white"], markeredgecolor=col, label=f"{g}  {lab}") for g, lab, col, m, fill in specs]
    fig.legend(handles=handles, loc="lower center", ncol=5, bbox_to_anchor=(.58, .05), fontsize=6.4, columnspacing=.9, handletextpad=.2)
    save(fig, "figure2_case_admissibility")


def fig4():
    occ = rows(DATA / "figure4_eplo_occupancy.csv")
    fig = plt.figure(figsize=(FIG_W, 3.55))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, .95], left=.12, right=.985, top=.86, bottom=.20, wspace=.52)
    a, b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    panel(a, "a", "Observed candidate occupancy")
    vals = {r["state"]: float(r["percent"]) for r in occ}
    labels = ["diagnosis / reconstruction", "transient scouting", "transport", "contraction"]
    values = [vals["Diagnosis/reconstruction"], vals["Transient scouting"], vals["Transport"], vals["Contraction"]]
    y = np.arange(4)
    a.barh(y, values, color=[C["teal"], C["amber"], "#C8CED2", "#C8CED2"], height=.55)
    for yy, v in zip(y, values): a.text(max(v + 1.2, 1.2), yy, f"{v:.1f}%", va="center", fontsize=8.0)
    a.set_yticks(y, labels); a.set_xlim(0, 108); a.set_xlabel("assignments (%)"); axis_clean(a, left=True, bottom=True)
    panel(b, "b", "Declared versus evaluated path")
    # Short stage labels keep the table readable at journal column width; the
    # full semantics are stated in the caption and source data.
    columns = ["stats", "state", "candidate", "objective", "selection"]
    declared = ["statistics", "diagnosis", "state\ncandidate", "objective", "selection"]
    realized = ["statistics", "candidate", "rand/1/\nbin", "objective", "selection"]
    b.set_xlim(-.5, 4.5); b.set_ylim(1.5, -.5); b.set_aspect("auto")
    for yy in range(2):
        for xx in range(5):
            b.add_patch(Rectangle((xx - .5, yy - .5), 1, 1,
                                  facecolor="#F4F5F6", edgecolor="none", zorder=0))
    for x in range(6): b.axvline(x - .5, color=C["light"], lw=.7)
    for yline in range(3): b.axhline(yline - .5, color=C["light"], lw=.7)
    for x, (d, r) in enumerate(zip(declared, realized)):
        b.text(x, 0, d, ha="center", va="center", fontsize=7.6, linespacing=.95)
        b.text(x, 1, r, ha="center", va="center", fontsize=7.6, linespacing=.95,
               color=C["red"] if x == 2 else C["ink"], fontweight="bold" if x == 2 else "normal")
    b.set_xticks(range(5), columns); b.set_yticks([0, 1], ["declared", "evaluated"]); b.tick_params(length=0, pad=4)
    for spine in b.spines.values(): spine.set_visible(True); spine.set_color(C["light"])
    save(fig, "figure3_eplo_execution_path")


def fig5():
    ranks = rows(DATA / "figure5_average_ranks.csv"); comps = rows(ROOT / "EPLO_full_15_comparisons.csv")
    names = ["EPLO candidate" if "EPLO candidate" in r["algorithm"] else r["algorithm"] for r in ranks]
    values = np.array([float(r["average_rank"]) for r in ranks]); y = np.arange(len(values)); eplo = next(i for i, n in enumerate(names) if "EPLO candidate" in n)
    strong = {"L-SHADE", "jSO", "SHADE"}
    fig = plt.figure(figsize=(FIG_W, 5.25))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.62, .95], height_ratios=[1, 1], left=.145, right=.985, top=.91, bottom=.10, hspace=.48, wspace=.42)
    a, b, c = fig.add_subplot(gs[:, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 1])
    panel(a, "a", "Average rank across 24 function–dimension tasks", "lower is better; recovered EPLO is highlighted")
    for i, (n, v) in enumerate(zip(names, values)):
        col = C["red"] if i == eplo else C["teal"] if n in strong else C["mid"]
        a.hlines(i, 0, v, color=C["light"], lw=1.0); a.scatter(v, i, s=48 if i == eplo else 28, marker="D" if i == eplo else "o", color=col, edgecolor=C["white"], lw=.5); a.text(v+.16, i, f"{v:.3f}", va="center", fontsize=7.2, color=col, fontweight="bold" if i == eplo else "normal")
    a.set_yticks(y, names); a.set_ylim(len(y)-.45, -.55); a.set_xlim(0, 16.8); a.set_xlabel("average rank"); axis_clean(a, left=True, bottom=True)
    a.text(values[eplo]+1.1, eplo-.48, "7 / 16", fontsize=8.8, color=C["red"], fontweight="bold")
    focus = [r for r in comps if r["comparator"] in ("L-SHADE", "jSO", "SHADE", "EPLO-Random-State", "EPLO-Time-Scheduled-State")]; fn = [r["comparator"].replace("EPLO-", "") for r in focus]; yy = np.arange(len(focus))
    cl = np.array([float(r["cl_probability"]) for r in focus]); hp = np.array([float(r["holm_p"]) for r in focus])
    panel(b, "b", "Pairwise effect direction", "P(EPLO better)"); b.axvline(.5, color=C["mid"], ls=(0, (2, 2)), lw=.8)
    for i, (v, r) in enumerate(zip(cl, focus)):
        col = C["red"] if r["comparator"] in strong else C["blue"]; b.hlines(i, .5, v, color=col, lw=1.1); b.scatter(v, i, s=30, color=col, edgecolor=C["white"], lw=.5)
    b.set_yticks(yy, fn); b.set_ylim(len(yy)-.45, -.55); b.set_xlim(0, 1); b.set_xlabel("probability"); axis_clean(b, left=True, bottom=True)
    panel(c, "c", "Multiplicity-adjusted evidence", "Holm-adjusted p; dashed line = 0.05"); c.axvline(.05, color=C["red"], ls=(0, (2, 2)), lw=.8)
    for i, v in enumerate(hp): c.hlines(i, .05, max(v, 1e-6), color=C["blue"], lw=1.0); c.scatter(max(v, 1e-6), i, s=30, facecolor=C["white"], edgecolor=C["blue"], lw=1.0)
    c.set_xscale("log"); c.set_xlim(1e-3, 1.2); c.set_ylim(len(yy)-.45, -.55); c.set_yticks(yy, fn); c.set_xlabel("Holm-adjusted p"); axis_clean(c, left=True, bottom=True)
    save(fig, "figure4_recovered_eplo_gate")


def fig6():
    data = rows(DATA / "figure6_instrumentation_cost.csv")[:3]; labels = ["off", "accepted only", "full candidate"]
    runtime = [float(r["runtime_ratio"]) for r in data]; sizes = [float(r["trace_bytes"]) for r in data]; colors = [C["mid"], C["blue"], C["red"]]
    fig = plt.figure(figsize=(FIG_W, 3.25))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1], left=.09, right=.985, top=.88, bottom=.18, wspace=.42)
    a, b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    panel(a, "a", "Runtime overhead")
    a.bar(range(3), runtime, color=colors, width=.62, edgecolor="none")
    a.axhline(1, color=C["mid"], ls=(0, (2, 2)), lw=.7)
    a.set_xticks(range(3), labels); a.set_ylabel("median ratio"); a.set_ylim(.96, 1.62); axis_clean(a, left=True, bottom=True)
    for i, v in enumerate(runtime): a.text(i, v + .035, f"{v:.3f}×", ha="center", fontsize=8.0)
    panel(b, "b", "Serialized trace footprint")
    b.bar(range(3), sizes, color=colors, width=.62, edgecolor="none")
    b.set_yscale("log"); b.set_xticks(range(3), labels); b.set_ylabel("median bytes"); axis_clean(b, left=True, bottom=True)
    for i, v in enumerate(sizes): b.text(i, v * 1.35, f"{int(v):,}", ha="center", fontsize=8.0)
    save(fig, "figure5_instrumentation_cost")


if __name__ == "__main__":
    fig2(); fig3(); fig4(); fig5(); fig6()
    print(f"Vector masters: {VECTOR}")
    print(f"QA previews: {PREVIEW}")
