"""Recreate Figure 3 independently, using the manuscript's rounded results.
Requires numpy and matplotlib. No input PDF or external data files needed.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Section 5.3 and Table 4 of the manuscript.
categories = ['Activity', 'Entropy', 'Target corr.']
square_vn = [0.258, 0.509, -0.296]
honeycomb = [0.221, 0.442, -0.261]
counts = [428, 4]
maximum_gain = 0.0043

# Styling and panel positions measured from the original vector PDF.
plt.rcdefaults()
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                     'axes.labelsize': 12, 'axes.titlesize': 15,
                     'axes.titleweight': 'bold', 'axes.titlepad': 8,
                     'axes.edgecolor': '#c4c4c4', 'axes.linewidth': 0.9,
                     'grid.color': '#d3d3d3', 'grid.linewidth': 0.6,
                     'grid.alpha': 0.55, 'legend.fontsize': 10,
                     'pdf.fonttype': 42})
teal, gold, salmon = '#74cbbe', '#f0c34e', '#ee8e7e'
W, H = 748.186279, 270.309113  # points
fig = plt.figure(figsize=(W/72, H/72), facecolor='white')
def panel(left):
    return fig.add_axes([left/W, (H-235.246613)/H,
                         309.405407/W, 208.656006/H])
a, b = panel(54.106251), panel(431.580841)

x = np.arange(3)
a.bar(x-0.17, square_vn, 0.34, color=teal, label='Square VN')
a.bar(x+0.17, honeycomb, 0.34, color=gold, label='Honeycomb')
a.set_xticks(x, categories, fontsize=11)
a.set_yticks(np.arange(-3, 6)/10)
a.set_ylim(-0.33625, 0.54925)
a.set_ylabel('Full QL minus diagonal ablation')
a.set_title('Transverse-state contribution')
a.legend(loc='upper right', frameon=False)
a.axhline(0, color='black', lw=0.9)

b.bar([0, 1], counts, width=0.8, color=[salmon, teal])
b.set_xticks([0, 1], ['No later\nimprovement', 'Any later\nimprovement'])
b.set_yticks(np.arange(0, 451, 50))
b.set_ylim(0, 450)
b.set_ylabel('Lesion trajectories')
b.set_title('Pre lesion state')
b.text(0.995, 0.0736, f'maximum gain = {maximum_gain:.4f}',
       transform=b.transAxes, ha='right', va='baseline',
       color='#d39c00', fontsize=11, fontweight='bold')
for ax in (a, b):
    ax.set_axisbelow(False)
    ax.grid(axis='y')

out = Path(__file__).resolve().parent
fig.savefig(out / 'fig3_recreated.pdf')
fig.savefig(out / 'fig3_recreated.png', dpi=300)
plt.close(fig)
print('Created fig3_recreated.pdf and fig3_recreated.png')
