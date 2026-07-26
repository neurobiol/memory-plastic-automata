#!/usr/bin/env python3
"""
Generate white-background paper figures equivalent in layout/orientation to the
three figures used in the IEEE manuscript.

Outputs:
  figures/primary_geometry_effects.pdf
  figures/mechanism_recovery.pdf
  figures/primary_heatmap.pdf
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

OUT = Path('figures')
OUT.mkdir(parents=True, exist_ok=True)

# Verified numerical summaries used throughout the paper.
GEOMETRIES = [
    'Square VN',
    'Honeycomb',
    'Square Moore',
    'Hex cells',
    'Honeycomb NNN',
    'Ext. Moore r2',
    'Ext. hex r2',
]

PRIMARY = {
    'Late activity': np.array([0.209, 0.142, -0.003, -0.003, -0.004, 0.056, -0.004]),
    'Binary entropy': np.array([0.396, 0.268, 0.004, 0.047, 0.058, 0.127, -0.023]),
    'Late target correlation': np.array([-0.183, -0.138, -0.005, 0.002, 0.007, -0.017, 0.000]),
}

ABLATION_GEOMS = ['Square VN', 'Honeycomb']
ABLATION = {
    'Activity': np.array([0.258, 0.221]),
    'Entropy': np.array([0.509, 0.442]),
    'Target corr.': np.array([-0.296, -0.261]),
}

# White-background palette.
WHITE = '#FFFFFF'
BLACK = '#000000'
TEAL = '#74CBBE'
MUSTARD = '#F0C34E'
SALMON = '#EE8E7E'
GRID = '#D3D3D3'
BORDER = '#C4C4C4'
HEATMAP = 'coolwarm'


def style_axes(ax):
    ax.set_facecolor(WHITE)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(0.9)
    ax.tick_params(colors=BLACK, labelsize=10)
    ax.xaxis.label.set_color(BLACK)
    ax.yaxis.label.set_color(BLACK)
    ax.title.set_color(BLACK)
    ax.grid(axis='x' if False else 'y', color=GRID, linewidth=0.6, alpha=0.55)


def save(fig, name):
    fig.patch.set_facecolor(WHITE)
    fig.savefig(OUT / name, bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)


# 1. Primary geometry effects: three horizontal panels.
def primary_geometry_effects():
    fig, axes = plt.subplots(1, 3, figsize=(10.8, 4.65), sharey=True)
    fig.patch.set_facecolor(WHITE)
    fig.suptitle('Primary lesion profile: paired QL minus classical differences',
                 fontsize=16, fontweight='bold', y=0.98, color=BLACK)

    colors = [TEAL, MUSTARD, SALMON]
    xlims = [(-0.015, 0.22), (-0.04, 0.42), (-0.20, 0.02)]

    for ax, (title, values), color, xlim in zip(axes, PRIMARY.items(), colors, xlims):
        style_axes(ax)
        y = np.arange(len(GEOMETRIES))
        ax.barh(y, values, color=color, edgecolor='none')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=10)
        ax.set_xlim(*xlim)
        ax.axvline(0, color=BLACK, linewidth=0.9)
        ax.invert_yaxis()
        ax.grid(axis='x', color=GRID, linewidth=0.6, alpha=0.55)
        ax.grid(axis='y', visible=False)
        ax.set_yticks(y)
        ax.set_yticklabels(GEOMETRIES, fontsize=10)

    axes[0].set_yticklabels(GEOMETRIES, fontsize=10)
    axes[1].tick_params(labelleft=False)
    axes[2].tick_params(labelleft=False)
    fig.supxlabel('Mean paired difference', fontsize=13, y=0.05, color=BLACK)
    fig.subplots_adjust(left=0.12, right=0.98, top=0.82, bottom=0.18, wspace=0.10)
    save(fig, 'primary_geometry_effects.pdf')


# 2. Mechanism and recovery: two-panel figure.
def mechanism_recovery():
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.2))
    fig.patch.set_facecolor(WHITE)

    # Left panel: grouped bars.
    ax = axes[0]
    style_axes(ax)
    cats = list(ABLATION.keys())
    x = np.arange(len(cats))
    w = 0.34
    ax.bar(x - w/2, [ABLATION[c][0] for c in cats], width=w, color=TEAL, label='Square VN', edgecolor='none')
    ax.bar(x + w/2, [ABLATION[c][1] for c in cats], width=w, color=MUSTARD, label='Honeycomb', edgecolor='none')
    ax.axhline(0, color=BLACK, linewidth=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=11)
    ax.set_ylabel('Full QL minus diagonal ablation', fontsize=12)
    ax.set_title('Transverse-state contribution', fontsize=15, fontweight='bold', pad=8)
    ax.grid(axis='y', color=GRID, linewidth=0.6, alpha=0.55)
    ax.grid(axis='x', visible=False)
    leg = ax.legend(frameon=False, fontsize=10, loc='upper right')
    for t in leg.get_texts():
        t.set_color(BLACK)

    # Right panel: audit counts.
    ax2 = axes[1]
    style_axes(ax2)
    labels = ['No later\nimprovement', 'Any later\nimprovement']
    counts = [428, 4]
    ax2.bar(labels, counts, color=[SALMON, TEAL], edgecolor='none')
    ax2.set_ylabel('Lesion trajectories', fontsize=12)
    ax2.set_title('Exact pre-lesion-state audit', fontsize=15, fontweight='bold', pad=8)
    ax2.grid(axis='y', color=GRID, linewidth=0.6, alpha=0.55)
    ax2.grid(axis='x', visible=False)
    ax2.set_ylim(0, 450)
    ax2.text(1, 28, 'maximum gain = 0.0043', ha='center', va='bottom', fontsize=11,
             color='#D39C00', fontweight='bold')

    fig.subplots_adjust(left=0.08, right=0.98, top=0.86, bottom=0.17, wspace=0.22)
    save(fig, 'mechanism_recovery.pdf')


# 3. Heatmap.
def primary_heatmap():
    matrix = np.vstack([
        PRIMARY['Late activity'],
        PRIMARY['Binary entropy'],
        PRIMARY['Late target correlation'],
    ]).T

    fig, ax = plt.subplots(figsize=(10.2, 4.9))
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)
    vmax = np.max(np.abs(matrix))
    im = ax.imshow(matrix, aspect='auto', cmap=HEATMAP, vmin=-vmax, vmax=vmax)

    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(['Activity', 'Entropy', 'Target correlation'], fontsize=12)
    ax.set_yticks(np.arange(len(GEOMETRIES)))
    ax.set_yticklabels(GEOMETRIES, fontsize=11)
    ax.set_title('Primary lesion paired differences by geometry', fontsize=16, fontweight='bold', pad=10)

    for spine in ax.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(0.8)

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            val = matrix[i, j]
            txt_color = 'white' if abs(val) >= 0.20 else 'black'
            ax.text(j, i, f'{val:+.3f}', ha='center', va='center', fontsize=11,
                    color=txt_color, fontweight='bold')

    cbar = fig.colorbar(im, ax=ax, fraction=0.030, pad=0.03)
    cbar.ax.tick_params(labelsize=10, colors=BLACK)
    cbar.outline.set_edgecolor(BORDER)

    fig.subplots_adjust(left=0.16, right=0.95, top=0.86, bottom=0.14)
    save(fig, 'primary_heatmap.pdf')


if __name__ == '__main__':
    primary_geometry_effects()
    mechanism_recovery()
    primary_heatmap()
    print(f'Wrote figures to: {OUT.resolve()}')
