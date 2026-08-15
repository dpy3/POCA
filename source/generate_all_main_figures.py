"""Generate the five empirical submission-grade figures from frozen audit evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Polygon

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"]
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["pdf.fonttype"] = 42

from paper_figure_style import PALETTE as C, export_figure, panel_label, panel_rule, rounded_card

ROOT = Path(__file__).resolve().parent
PKG = ROOT.parent
DATA = ROOT / "figure_source_data"
FIG_W = 183 / 25.4


def rows(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def minimal_axis(ax, left=False, bottom=False):
    for name, spine in ax.spines.items():
        spine.set_visible((name == "left" and left) or (name == "bottom" and bottom))
    ax.tick_params(length=2.6 if (left or bottom) else 0, width=0.7, color=C["ink"])


def stage_lanes(ax, centers, colors, ymin, ymax, alpha=0.52):
    """Mark ordered stages without dashboard-like background blocks."""
    for x, color in zip(centers, colors):
        ax.axvline(x, color=color, alpha=min(alpha, 0.38), lw=0.75,
                   zorder=-4)


def figure1():
    fig = plt.figure(figsize=(FIG_W, 4.28))
    gs = fig.add_gridspec(1, 2, width_ratios=[0.68, 1.62],
                          left=0.055, right=0.975, top=0.90, bottom=0.11,
                          wspace=0.20)
    a = fig.add_subplot(gs[0, 0]); b = fig.add_subplot(gs[0, 1])
    for ax, label in zip((a, b), "ab"): panel_label(ax, label)

    a.set_axis_off(); a.set_xlim(0, 1); a.set_ylim(0, 1)
    a.set_title("Hash-linked evidence object", loc="left")
    panel_rule(a)
    a.text(0.21, 0.945, "VERSIONED INPUT", ha="center", va="bottom", fontsize=5.5,
           color=C["pass"], fontweight="bold")
    chain = [("S", "Source"), ("C", "Configuration"), ("E", "Evaluator"),
             ("B", "Budget"), ("R", "Result")]
    ys = np.linspace(0.82, 0.32, 5)
    a.plot([0.24, 0.24], [ys[-1], ys[0]], color=C["pass"], lw=1.1, zorder=0)
    for y, (code, label) in zip(ys, chain):
        a.scatter(0.24, y, s=145, facecolor="white", edgecolor=C["pass"],
                  linewidth=1.2, zorder=2)
        a.text(0.24, y, code, ha="center", va="center", fontsize=7.0, fontweight="bold")
        a.text(0.42, y, label, va="center", fontsize=7.2)
    a.add_patch(FancyArrowPatch((0.24, 0.275), (0.24, 0.19), arrowstyle="-|>",
                                mutation_scale=8, lw=0.9, color=C["line"]))
    a.text(0.24, 0.12, "VERSIONED\nRECORD", ha="center", va="center",
           fontsize=6.5, fontweight="bold", color=C["ink"], linespacing=1.05)
    a.text(0.46, 0.12, "local status\neffective claim", va="center", fontsize=6.3,
           color=C["muted"], linespacing=1.2)

    b.set_axis_off(); b.set_xlim(0, 1); b.set_ylim(0, 1)
    b.set_title("Claim depth advances only after prerequisite passage", loc="left", pad=5)
    panel_rule(b)
    levels = [("L0", "Run"), ("L1", "Algorithm identity"), ("L2", "Budget identity"),
              ("L3", "Evaluated path"), ("L4", "Control identity"),
              ("L5", "Incremental value")]
    xs = np.linspace(0.06, 0.91, 6)
    ys2 = np.linspace(0.46, 0.83, 6)
    b.text(0.02, 0.91, "EVIDENCE FLOW", fontsize=5.6, color=C["pass"],
           fontweight="bold", va="top")
    for i in range(5):
        b.plot([xs[i], xs[i + 1]], [ys2[i], ys2[i]], color=C["pass"], lw=1.15)
        b.plot([xs[i + 1], xs[i + 1]], [ys2[i], ys2[i + 1]], color=C["pass"], lw=1.15)
    for i, (x, y, (code, label)) in enumerate(zip(xs, ys2, levels)):
        col = C["pass"]
        b.scatter(x, y, s=150, facecolor="white", edgecolor=col, linewidth=1.25, zorder=3)
        b.text(x, y, code, ha="center", va="center", fontsize=6.8, fontweight="bold", color=col)
        label_x = x - 0.025 if i == 5 else x + 0.035
        label_ha = "right" if i == 5 else "left"
        b.text(label_x, y + 0.050, label, fontsize=6.6, ha=label_ha, va="bottom",
               color=C["ink"])
    b.annotate("observer + replay validity", xy=(xs[2] + 0.04, ys2[2] + 0.012),
               xytext=(xs[2] - 0.03, ys2[2] + 0.15), fontsize=6.4,
               color=C["observer"], fontweight="bold",
               arrowprops=dict(arrowstyle="-[", mutation_scale=14, lw=0.9,
                               color=C["observer"]))
    b.plot([0.0, 1.0], [0.34, 0.34], color=C["line"], lw=0.65)
    b.text(0.00, 0.22, "EVERY TRANSITION", fontsize=6.0, fontweight="bold", color=C["muted"])
    b.add_patch(FancyArrowPatch((0.22, 0.21), (0.36, 0.21), arrowstyle="-|>",
                                mutation_scale=8, lw=0.9, color=C["line"]))
    b.scatter(0.41, 0.21, s=125, marker="D", facecolor="white", edgecolor=C["indet"], lw=1.1)
    b.text(0.41, 0.21, "?", ha="center", va="center", fontsize=6.3,
           fontweight="bold", color=C["indet"])
    b.add_patch(FancyArrowPatch((0.46, 0.21), (0.61, 0.21), arrowstyle="-|>",
                                mutation_scale=8, lw=0.9, color=C["pass"]))
    b.text(0.535, 0.27, "PASS", ha="center", fontsize=5.8, fontweight="bold", color=C["pass"])
    b.text(0.63, 0.21, "advance to higher claim", va="center", fontsize=6.6)
    b.add_patch(FancyArrowPatch((0.41, 0.17), (0.41, 0.055), arrowstyle="-|>",
                                mutation_scale=8, lw=0.9, color=C["fail"]))
    b.text(0.43, 0.095, "NONPASS", fontsize=5.8, fontweight="bold", color=C["fail"])
    b.text(0.53, 0.075, "stop effective claim; preserve local evidence",
           va="center", fontsize=6.3)
    b.text(0.99, 0.985, "Decision contract, not observed outcomes",
           transform=b.transAxes, ha="right", va="top", fontsize=5.7, color=C["muted"])
    export_figure(fig, ROOT, "figure1_audit_framework"); plt.close(fig)


def figure2():
    faults = rows(PKG / "validation" / "fault_injection_results_20260720.csv")
    clean = json.loads((PKG / "extension" / "results" / "clean_control_summary.json").read_text())
    ext = json.loads((PKG / "extension" / "results" / "lshade_positive_external_20260721.json").read_text())
    fig = plt.figure(figsize=(FIG_W, 6.10))
    gs = fig.add_gridspec(3, 2, height_ratios=[0.30, 1.36, 0.76],
                          left=0.13, right=0.975, top=0.94, bottom=0.10,
                          hspace=0.36, wspace=0.44)
    a = fig.add_subplot(gs[0, :]); b = fig.add_subplot(gs[1, :])
    c = fig.add_subplot(gs[2, 0]); d = fig.add_subplot(gs[2, 1])
    for ax, label in zip((a, b, c, d), "abcd"): panel_label(ax, label)

    a.set_axis_off(); a.set_xlim(0, 1); a.set_ylim(0, 1)
    a.set_title("Bounded validation summary", loc="left")
    panel_rule(a)
    metrics = [("8/8", "preregistered defects", "detected", C["fail"]),
               ("0/45", "clean records", "observed alarms", C["pass"]),
               ("9/9", "external records", "exact audits", C["observer"])]
    for i, (value, unit, outcome, color) in enumerate(metrics):
        x = 0.045 + i * 0.335
        rounded_card(a, (x - 0.018, 0.08), 0.285, 0.72,
                     C["paper"], edge=C["grid"], radius=0.018, lw=0.7)
        a.text(x, 0.38, value, color=color, fontsize=15, fontweight="bold", va="center")
        a.text(x + 0.105, 0.43, unit, fontsize=6.6, va="center")
        a.text(x + 0.105, 0.24, outcome, fontsize=6.3, color=C["muted"], va="center")
        if i < 2: a.plot([x + 0.29, x + 0.29], [0.12, 0.64], color=C["grid"], lw=0.8)

    fault_rows = faults[1:]
    fault_labels = ["Source name", "Result column", "Candidate overwrite", "Auxiliary calls",
                    "Reduction FE", "Iteration stop", "Observer RNG", "Operator label"]
    gate_labels = ["Identity", "Budget", "Path", "Observer", "Replay"]
    gate_map = {name.lower(): i for i, name in enumerate(gate_labels)}
    b.set_title("Injected defects stop at the prespecified prerequisite", loc="left")
    panel_rule(b)
    b.set_xlim(-0.55, 4.55); b.set_ylim(7.65, -0.65)
    stage_lanes(b, range(5), [C["pass_mid"], C["indet"], C["fail"],
                              C["observer"], C["not_tested"]], 0, 1, alpha=0.25)
    for x in range(5): b.axvline(x, color=C["grid"], lw=0.75, zorder=0)
    for y in range(8):
        b.axhline(y, color=C["grid"], lw=0.65, zorder=0)
    for y, record in enumerate(fault_rows):
        x = gate_map[record["expected_gate"].lower()]
        b.scatter(x, y, s=76, marker="x", color=C["fail"], linewidth=1.65, zorder=3)
    b.set_xticks(range(5), [""] * 5); b.set_yticks(range(8), fault_labels)
    for x, label in enumerate(gate_labels):
        b.text(x, -0.43, label.upper(), ha="center", va="bottom", fontsize=5.1,
               fontweight="bold", color=C["muted"])
    minimal_axis(b, bottom=True)
    b.text(0.995, 0.02, "Blank = untargeted gate, not missing observation",
           transform=b.transAxes, ha="right", va="bottom", fontsize=5.8, color=C["muted"])

    modes = ["off", "accepted_only", "full_candidate"]
    vals = [clean["runtime_ratio_by_mode"][m] for m in modes]
    c.set_title("Clean records: instrumentation time", loc="left")
    panel_rule(c)
    c.axhline(1, color=C["line"], ls=(0, (3, 2)), lw=0.85)
    c.vlines(range(3), 1, vals, color=C["pass"], lw=1.25)
    c.scatter(range(3), vals, s=40, facecolor="white", edgecolor=C["pass"], lw=1.25)
    c.set_xticks(range(3), ["Off", "Accepted\nonly", "Full\ncandidate"])
    c.set_ylabel("Median runtime ratio"); c.set_ylim(0.94, max(vals) + 0.13)
    for i, value in enumerate(vals): c.text(i, value + 0.03, f"{value:.3f}", ha="center", fontsize=6.2)
    minimal_axis(c, left=True, bottom=True)

    checks = list(ext["records"][0]["checks"].keys())
    check_labels = [x.replace("_", " ") for x in checks]
    d.set_axis_off(); d.set_xlim(0, 1); d.set_ylim(0, 1)
    d.set_title("External L-SHADE: 9/9 exact checks", loc="left", pad=5)
    panel_rule(d)
    xx = [0.08, 0.40, 0.72]; yy = [0.70, 0.43, 0.16]
    for index, label in enumerate(check_labels):
        x, y = xx[index % 3], yy[index // 3]
        d.scatter(x, y, s=62, facecolor="white", edgecolor=C["observer"], lw=1.2)
        d.text(x + 0.045, y + 0.025, "9/9", va="center", fontsize=6.7,
               fontweight="bold", color=C["observer"])
        d.text(x + 0.045, y - 0.045, label, va="center", fontsize=5.9, color=C["ink"])
    export_figure(fig, ROOT, "figure2_controlled_validation"); plt.close(fig)


def derive_effective(local):
    out, blocked = [], False
    for value in local:
        if blocked:
            out.append("BLOCKED")
        else:
            out.append(value)
            if value != "PASS": blocked = True
    return out


def status_matrix(ax, matrix, names, layers):
    colors = {"PASS": C["pass"], "FAIL": C["fail"], "INDETERMINATE": C["indet"],
              "NOT_TESTED": C["not_tested"], "BLOCKED": C["blocked"]}
    glyphs = {"PASS": "P", "FAIL": "F", "INDETERMINATE": "I",
              "NOT_TESTED": "NT", "BLOCKED": "B"}
    markers = {"PASS": "o", "FAIL": "X", "INDETERMINATE": "D",
               "NOT_TESTED": "o", "BLOCKED": "s"}
    ax.set_xlim(-0.55, 4.55); ax.set_ylim(4.55, -0.55)
    stage_lanes(ax, range(5), [C["pass_mid"], C["pass_mid"], C["indet"],
                               C["observer"], C["blocked"]], 0, 1, alpha=0.16)
    for x in range(5): ax.axvline(x, color=C["grid"], lw=0.55, zorder=0)
    for y in range(5): ax.axhline(y, color=C["grid"], lw=0.55, zorder=0)
    for y, row in enumerate(matrix):
        for x, value in enumerate(row):
            open_symbol = value in ("NOT_TESTED", "BLOCKED")
            ax.scatter(x, y, s=104 if value != "FAIL" else 116,
                       marker=markers[value],
                       facecolor="white" if open_symbol else colors[value],
                       edgecolor=colors[value], lw=1.05, zorder=2)
            ax.text(x, y, glyphs[value], ha="center", va="center", fontsize=5.0,
                    fontweight="bold", color=colors[value] if open_symbol else "white", zorder=3)
    ax.set_xticks(range(5), layers); ax.set_yticks(range(5), names)
    minimal_axis(ax)


def figure3():
    data = rows(DATA / "figure3_case_status.csv"); layers = ["L1", "L2", "L3", "L4", "L5"]
    local = [[r[x] for x in layers] for r in data]; effective = [derive_effective(x) for x in local]
    short = ["Historical EPLO", "Recovered EPLO", "Later FSDC", "QSMODE", "IDE-EDA"]
    names = short
    highest = [0, 2, 4, 1, 1]
    fig = plt.figure(figsize=(FIG_W, 5.45))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.28, 0.94], height_ratios=[1, 1],
                          left=0.145, right=0.975, top=0.92, bottom=0.14,
                          hspace=0.38, wspace=0.43)
    a = fig.add_subplot(gs[:, 0]); b = fig.add_subplot(gs[0, 1]); c = fig.add_subplot(gs[1, 1])
    for ax, label in zip((a, b, c), "abc"): panel_label(ax, label)
    a.set_title("Highest admissible layer for each evidence object", loc="left")
    panel_rule(a)
    terminals = ["provenance stop", "path stop", "value stop", "budget stop", "budget stop"]
    for y, (x, terminal) in enumerate(zip(highest, terminals)):
        a.plot([0, x], [y, y], color=C["pass_light"], lw=6.0, solid_capstyle="round")
        a.scatter(x, y, s=52, color=C["pass"], edgecolor="white", lw=0.6, zorder=3)
        a.text(x + 0.12, y, terminal, va="center", fontsize=6.0, color=C["muted"])
    a.set_yticks(range(5), names); a.set_xticks(range(6), ["L0", "L1", "L2", "L3", "L4", "L5"])
    a.set_xlim(-0.35, 5.55); a.set_ylim(4.6, -0.6)
    a.set_xlabel("Admissible depth (not a performance rank)")
    for x in range(6): a.axvline(x, color=C["grid"], lw=0.65, zorder=0)
    minimal_axis(a, bottom=True)

    b.set_title("Observed locally", loc="left")
    panel_rule(b)
    c.set_title("After prerequisite ordering", loc="left")
    panel_rule(c)
    status_matrix(b, local, short, layers); status_matrix(c, effective, short, layers)
    legend_specs = [("P", "Pass", C["pass"], True, "o"), ("F", "Fail", C["fail"], True, "X"),
                    ("I", "Indeterminate", C["indet"], True, "D"),
                    ("NT", "Not tested", C["not_tested"], False, "o"),
                    ("B", "Blocked", C["blocked"], False, "s")]
    handles = [Line2D([0], [0], marker=marker, linestyle="", markersize=5.5,
                      markerfacecolor=col if filled else "white", markeredgecolor=col,
                      label=f"{glyph} {label}") for glyph, label, col, filled, marker in legend_specs]
    fig.legend(handles=handles, loc="lower center", ncol=5, bbox_to_anchor=(0.62, 0.018),
               columnspacing=0.95, handletextpad=0.3)
    export_figure(fig, ROOT, "figure3_case_admissibility"); plt.close(fig)


def path_lane(ax, y, items, color, accent_index=None):
    xs = np.linspace(0.11, 0.94, len(items))
    ax.plot([xs[0], xs[-1]], [y, y], color=color, lw=1.25, zorder=0)
    for i, (x, text) in enumerate(zip(xs, items)):
        marker = "D" if i == accent_index else "o"
        edge = C["fail"] if i == accent_index else color
        ax.scatter(x, y, s=70 if marker == "o" else 86, marker=marker,
                   facecolor="white", edgecolor=edge, linewidth=1.25, zorder=3)
        ax.text(x, y - 0.072, text, ha="center", va="top", fontsize=6.2,
                fontweight="bold" if i == accent_index else "normal", linespacing=1.05)
    return xs


def figure4():
    occ = rows(DATA / "figure4_eplo_occupancy.csv")
    fig = plt.figure(figsize=(FIG_W, 5.05))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.52, 0.72], width_ratios=[1.55, 1.0],
                          left=0.16, right=0.975, top=0.92, bottom=0.12,
                          hspace=0.34, wspace=0.48)
    a = fig.add_subplot(gs[0, :]); b = fig.add_subplot(gs[1, 0]); c = fig.add_subplot(gs[1, 1])
    for ax, label in zip((a, b, c), "abc"): panel_label(ax, label)
    a.set_axis_off(); a.set_xlim(0, 1); a.set_ylim(0, 1)
    a.set_title("The state candidate is replaced before objective evaluation", loc="left")
    panel_rule(a)
    a.plot([0.06, 0.98], [0.52, 0.52], color=C["grid"], lw=0.7)
    a.axvline(0.457, ymin=0.10, ymax=0.84, color=C["fail"], lw=0.8, ls=(0, (2, 2)), alpha=0.85)
    a.text(0.01, 0.79, "DECLARED", fontsize=6.2, fontweight="bold", color=C["pass"])
    declared = ["Field\nstatistics", "State\ndiagnosis", "State\ncandidate", "Evaluate", "Select"]
    dx = path_lane(a, 0.70, declared, C["pass"])
    a.text(0.01, 0.31, "EXECUTED", fontsize=6.2, fontweight="bold", color=C["ink"])
    executed = ["Field\nstatistics", "State\ncandidate", "Global\nrand/1/bin", "Evaluate", "Select"]
    ex = path_lane(a, 0.24, executed, C["ink"], accent_index=2)
    a.plot([dx[2], ex[2]], [0.66, 0.29], color=C["fail"], lw=1.1, ls=(0, (3, 2)))
    a.annotate("OVERWRITE", xy=(ex[2], 0.30), xytext=(ex[2] + 0.14, 0.49),
               fontsize=6.5, fontweight="bold", color=C["fail"], ha="center",
               arrowprops=dict(arrowstyle="-|>", color=C["fail"], lw=0.9))

    values = [float(r["percent"]) for r in occ]; labels = [r["state"] for r in occ]
    yy = np.arange(4)
    b.set_title("Observed assignment occupancy", loc="left")
    panel_rule(b)
    b.hlines(yy, 0, values, color=C["line"], lw=1.0)
    face = [C["pass"], C["indet"], "white", "white"]
    edge = [C["pass"], C["indet"], C["not_tested"], C["not_tested"]]
    b.scatter(values, yy, s=[46, 34, 30, 30], facecolor=face, edgecolor=edge, lw=1.0)
    b.set_yticks(yy, labels); b.set_xlim(0, 108); b.set_ylim(3.45, -0.45)
    b.set_xlabel("Assignments (%)")
    for y, value in zip(yy, values): b.text(value + 1.8, y, f"{value:.1f}%", va="center", fontsize=6.1)
    minimal_axis(b, left=True, bottom=True)

    c.set_axis_off(); c.set_xlim(0, 1); c.set_ylim(0, 1)
    c.set_title("Interpretation boundary", loc="left")
    panel_rule(c)
    c.plot([0.03, 0.03], [0.10, 0.88], color=C["pass"], lw=2.0)
    c.text(0.11, 0.78, "SUPPORTED", fontsize=6.1, fontweight="bold", color=C["pass"])
    c.text(0.11, 0.58, "The computed state candidate\nis overwritten.", fontsize=7.0, linespacing=1.18)
    c.text(0.11, 0.31, "NOT SUPPORTED", fontsize=6.1, fontweight="bold", color=C["fail"])
    c.text(0.11, 0.11, "Four-state controller value\nor optimizer superiority.", fontsize=7.0, linespacing=1.18)
    export_figure(fig, ROOT, "figure4_eplo_execution_path"); plt.close(fig)


def figure5():
    ranks = rows(DATA / "figure5_average_ranks.csv")
    comps = rows(ROOT / "EPLO_full_15_comparisons.csv")
    fig = plt.figure(figsize=(FIG_W, 5.95))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.62, 0.90], height_ratios=[1, 1],
                          left=0.155, right=0.975, top=0.93, bottom=0.105,
                          hspace=0.40, wspace=0.48)
    a = fig.add_subplot(gs[:, 0]); b = fig.add_subplot(gs[0, 1]); c = fig.add_subplot(gs[1, 1])
    for ax, label in zip((a, b, c), "abc"): panel_label(ax, label)
    names = ["EPLO candidate" if "EPLO candidate" in r["algorithm"] else r["algorithm"] for r in ranks]
    values = np.array([float(r["average_rank"]) for r in ranks])
    y = np.arange(len(values)); eplo_i = next(i for i, name in enumerate(names) if "EPLO candidate" in name)
    strong = {"L-SHADE", "jSO", "SHADE"}
    a.set_title("Recovered EPLO ranks 7th; three adaptive-DE baselines lead", loc="left")
    panel_rule(a)
    for yi, (name, value) in enumerate(zip(names, values)):
        is_eplo = yi == eplo_i
        color = C["pass"] if name in strong else C["fail"] if is_eplo else C["not_tested"]
        a.hlines(yi, 0, value, color=C["grid"], lw=1.15)
        a.scatter(value, yi, s=50 if is_eplo else 30, marker="D" if is_eplo else "o",
                  color=color, edgecolor="white", lw=0.55, zorder=3)
        a.text(value + 0.18, yi, f"{value:.3f}", va="center", fontsize=5.8,
               fontweight="bold" if is_eplo else "normal",
               color=C["fail"] if is_eplo else C["muted"])
    a.set_yticks(y, names); a.set_ylim(len(y) - 0.45, -0.55); a.set_xlim(0, 16.8)
    a.set_xlabel("Average rank across 24 function-dimension tasks (lower is better)")
    a.text(values[eplo_i] + 0.75, eplo_i - 0.62, "7th / 16", color=C["fail"],
           fontsize=7.4, fontweight="bold")
    a.text(0.98, 0.995, "Recovered rerun only; historical rank 1.58 withdrawn",
           transform=a.transAxes, ha="right", va="top", fontsize=5.5, color=C["muted"])
    a.text(0.99, 0.815, "adaptive-DE leaders", transform=a.transAxes,
           ha="right", fontsize=5.7, color=C["pass"])
    minimal_axis(a, left=True, bottom=True)

    focus = [x for x in comps if x["comparator"] in
             ("L-SHADE", "jSO", "SHADE", "EPLO-Random-State", "EPLO-Time-Scheduled-State")]
    focus_names = [x["comparator"].replace("EPLO-", "") for x in focus]
    yy = np.arange(len(focus)); cl = np.array([float(x["cl_probability"]) for x in focus])
    b.set_title("Pairwise effect direction", loc="left")
    panel_rule(b)
    b.axvline(0.5, color=C["line"], ls=(0, (3, 2)), lw=0.85)
    b.scatter(cl, yy, s=38,
              color=[C["fail"] if x["comparator"] in strong else C["pass"] for x in focus],
              edgecolor="white", lw=0.45)
    b.set_yticks(yy, focus_names); b.set_ylim(len(yy) - 0.45, -0.55); b.set_xlim(0, 1)
    b.set_xlabel("P(EPLO better)")
    b.text(0.01, 1.02, "comparator favored", transform=b.transAxes, fontsize=5.7, color=C["fail"])
    b.text(0.99, 1.02, "EPLO favored", transform=b.transAxes, fontsize=5.7, color=C["pass"], ha="right")
    minimal_axis(b, left=True, bottom=True)

    hp = np.array([float(x["holm_p"]) for x in focus])
    c.set_title("Prespecified gate is not passed", loc="left")
    panel_rule(c)
    c.axvline(0.05, color=C["fail"], ls=(0, (3, 2)), lw=0.9)
    c.scatter(np.clip(hp, 1e-6, 1), yy, s=38, facecolor="white", edgecolor=C["pass"], lw=1.15)
    c.set_xscale("log"); c.set_xlim(1e-3, 1.2); c.set_ylim(len(yy) - 0.45, -0.55)
    c.set_yticks(yy, focus_names); c.set_xlabel("Holm-adjusted p")
    c.text(0.05, 1.02, "0.05", transform=c.get_xaxis_transform(), ha="center",
           fontsize=5.7, color=C["fail"])
    minimal_axis(c, left=True, bottom=True)
    export_figure(fig, ROOT, "figure5_recovered_eplo_gate"); plt.close(fig)


def figure6():
    data = rows(DATA / "figure6_instrumentation_cost.csv"); clean = data[:3]
    fig = plt.figure(figsize=(FIG_W, 5.10))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.02, 1.08], height_ratios=[1, 1],
                          left=0.095, right=0.97, top=0.92, bottom=0.12,
                          hspace=0.42, wspace=0.46)
    a = fig.add_subplot(gs[0, 0]); b = fig.add_subplot(gs[1, 0]); c = fig.add_subplot(gs[:, 1])
    for ax, label in zip((a, b, c), "abc"): panel_label(ax, label)
    labels = ["Off", "Accepted only", "Full candidate"]
    runtime = [float(x["runtime_ratio"]) for x in clean]
    sizes = [float(x["trace_bytes"]) for x in clean]
    colors = [C["not_tested"], C["pass"], C["fail"]]

    a.set_title("Runtime cost", loc="left")
    panel_rule(a)
    a.axhline(1, color=C["line"], ls=(0, (3, 2)), lw=0.85)
    a.vlines(range(3), 1, runtime, color=colors, lw=1.25)
    a.scatter(range(3), runtime, s=42, facecolor="white", edgecolor=colors, lw=1.25)
    a.set_xticks(range(3), labels); a.set_ylabel("Median runtime ratio")
    a.set_ylim(0.94, max(runtime) + 0.14)
    for i, value in enumerate(runtime): a.text(i, value + 0.03, f"{value:.3f}", ha="center", fontsize=6.1)
    minimal_axis(a, left=True, bottom=True)

    b.set_title("Serialized trace size", loc="left")
    panel_rule(b)
    b.vlines(range(3), 1, sizes, color=colors, lw=1.25)
    b.scatter(range(3), sizes, s=42, facecolor="white", edgecolor=colors, lw=1.25)
    b.set_yscale("log"); b.set_xticks(range(3), labels)
    b.set_ylabel("Median bytes (log scale)")
    for i, value in enumerate(sizes): b.text(i, value * 1.35, f"{int(value):,}", ha="center", fontsize=6.1)
    minimal_axis(b, left=True, bottom=True)

    c.set_axis_off(); c.set_xlim(0, 1); c.set_ylim(0, 1)
    c.set_title("Staged provenance deployment", loc="left")
    panel_rule(c)
    c.text(0.99, 0.965, "Recommendation, not an optimized policy",
           ha="right", va="top", fontsize=5.8, color=C["muted"])
    stages = [("01", "Hashes + smoke seed", "low-cost entry"),
              ("02", "Full candidate trace", "identity localization"),
              ("03", "Prerequisites pass?", "decision gate"),
              ("04", "Accepted events + hashes", "full campaign")]
    ys = np.array([0.82, 0.60, 0.37, 0.14]); x = 0.28
    c.plot([x, x], [ys[2], ys[0]], color=C["line"], lw=1.15)
    c.add_patch(FancyArrowPatch((x, ys[2] - 0.045), (x, ys[3] + 0.045),
                                arrowstyle="-|>", mutation_scale=8, lw=1.0, color=C["pass"]))
    for i, (y, (num, title, sub)) in enumerate(zip(ys, stages)):
        color = C["indet"] if i == 2 else C["pass"]
        marker = "D" if i == 2 else "o"
        c.scatter(x, y, s=190, marker=marker, facecolor="white", edgecolor=color, lw=1.35, zorder=3)
        c.text(x, y, num, ha="center", va="center", fontsize=6.2, fontweight="bold", color=color)
        c.text(0.42, y + 0.025, title, va="bottom", fontsize=7.1, fontweight="bold")
        c.text(0.42, y - 0.025, sub, va="top", fontsize=6.1, color=C["muted"])
    c.text(x + 0.035, (ys[2] + ys[3]) / 2, "PASS", fontsize=5.7,
           fontweight="bold", color=C["pass"], va="center")
    c.add_patch(FancyArrowPatch((x - 0.045, ys[2]), (0.025, ys[2]), arrowstyle="-|>",
                                mutation_scale=8, lw=0.9, color=C["fail"]))
    c.text(0.02, ys[2] + 0.070, "NONPASS", fontsize=5.7, fontweight="bold", color=C["fail"])
    c.text(0.02, ys[2] - 0.060, "STOP / freeze", fontsize=5.8, color=C["fail"])
    export_figure(fig, ROOT, "figure6_deployment_cost"); plt.close(fig)


if __name__ == "__main__":
    # Keep the historical entry point stable while routing regeneration to the
    # redesigned top-journal composition.
    from generate_top_journal_figures import fig2, fig3, fig4, fig5, fig6
    fig2(); fig3(); fig4(); fig5(); fig6()
    print("Generated redesigned top-journal figure set.")
