"""Shared ASOC-style publication system and exact-size vector export helpers."""

from pathlib import Path

import matplotlib as mpl
from matplotlib import font_manager

FONT = "Arial"
# Keep the Nature-style Arial-first stack while remaining portable on systems
# where Arial is not installed.  Matplotlib will use the first available face.
font_manager.findfont(FONT, fallback_to_default=True)

PALETTE = {
    # V11 editorial palette: navy structure, teal verification, coral failure,
    # amber conditionality. Saturation is reserved for inferential events.
    "ink": "#17324D", "muted": "#5F7180", "line": "#93A5B2",
    "grid": "#DCE4E8", "paper": "#FFFFFF",
    "pass": "#1E6F8F", "pass_mid": "#80AFC2", "pass_light": "#EEF6F8",
    "observer": "#2A7F7F", "observer_light": "#EEF8F7",
    "fail": "#C84F4B", "fail_light": "#FFF2F0",
    "indet": "#D19A32", "indet_light": "#FFF8E8",
    "blocked": "#596774", "blocked_light": "#F1F4F6",
    "not_tested": "#B5BDC3", "not_tested_light": "#FAFBFC",
    "accent": "#1E6F8F", "accent_light": "#EEF6F8",
}

mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": [FONT, "Helvetica", "Liberation Sans", "DejaVu Sans"],
    "font.size": 7.6, "axes.titlesize": 8.8, "axes.titleweight": "bold",
    "axes.titlepad": 7, "axes.labelsize": 7.5,
    "xtick.labelsize": 6.8, "ytick.labelsize": 6.8, "legend.fontsize": 6.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.7, "legend.frameon": False,
    "axes.edgecolor": "#20262E", "xtick.color": "#20262E",
    "ytick.color": "#20262E", "text.color": "#20262E",
    "svg.fonttype": "none", "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.facecolor": "white", "figure.facecolor": "white",
    "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})


def panel_label(ax, label, x=-0.06, y=1.055):
    # Nature-style panel labels are quiet anchors, not decorative badges.
    ax.text(x, y, label, transform=ax.transAxes, fontsize=8.6,
            fontweight="bold", va="bottom", ha="left", color=PALETTE["ink"])


def panel_rule(ax, y=1.015, color=None, lw=1.0):
    """A restrained header rule that creates visual hierarchy without boxing panels."""
    ax.plot([0, 1], [y, y], transform=ax.transAxes, clip_on=False,
            color=color or PALETTE["grid"], lw=lw)


def rounded_card(ax, xy, width, height, face, edge=None, radius=0.018, lw=0.8):
    from matplotlib.patches import FancyBboxPatch
    patch = FancyBboxPatch(xy, width, height,
                           boxstyle=f"round,pad=0.012,rounding_size={radius}",
                           transform=ax.transAxes, facecolor=face,
                           edgecolor=edge or face, linewidth=lw)
    ax.add_patch(patch)
    return patch


def export_figure(fig, out_dir, stem):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(pad=1.0)
    common = dict(bbox_inches="tight", pad_inches=0.03)
    fig.savefig(out / f"{stem}.svg", **common)
    fig.savefig(out / f"{stem}.pdf", **common)
    fig.savefig(out / f"{stem}.tiff", dpi=600, **common)
    fig.savefig(out / f"{stem}_preview.png", dpi=300, **common)
