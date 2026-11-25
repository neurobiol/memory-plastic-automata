import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent
out=root/'figures';out.mkdir(exist_ok=True)
df=pd.read_csv(root/'combined/mean_trajectories.csv')
labels={'markov':'Scalar classical','ql':'Unit-ball hidden state','box':'Equal-dim. box control'}
for geo in ('square_vn','honeycomb'):
 for metric in ('damage_mae_local','damage_mae_global'):
  d=df.query('geometry==@geo and area_mode=="nominal"').groupby(['formalism','dt'],as_index=False)[metric].mean()
  fig,ax=plt.subplots(figsize=(6.8,4.1))
  for f in ('markov','box','ql'):
   y=d[d.formalism==f]
   ax.plot(y.dt,y[metric],marker='o',linewidth=1.8,markersize=3.8,label=labels[f])
  ax.set(xlabel='Sweeps after lesion',ylabel='Mean absolute lesion–sham difference',
         title=('Square von Neumann' if geo=='square_vn' else 'Honeycomb')+'; '+('lesion sites' if metric=='damage_mae_local' else 'whole lattice'))
  ax.grid(alpha=.22)
  ax.legend(fontsize=8,loc='best')
  fig.tight_layout()
  for ext in ('pdf','png'):
   fig.savefig(out/f'{geo}_{metric}.{ext}',dpi=200)
  plt.close(fig)

# Activity–target-correlation tradeoff at the final sweep, aggregated over 2 plasticity conditions and 5 seeds.
base=pd.read_csv(root/'combined/derived_by_case.csv')
for severity in ('nominal','eight_percent'):
 d=base[base.area_mode==severity].groupby(['geometry','formalism'],as_index=False)[['mean_activity_lesion','target_corr_lesion']].mean()
 fig,ax=plt.subplots(figsize=(6.8,4.2))
 for g,marker in [('square_vn','o'),('honeycomb','s')]:
  for f in ('markov','box','ql'):
   q=d[(d.geometry==g)&(d.formalism==f)].iloc[0]
   ax.scatter(q.mean_activity_lesion,q.target_corr_lesion,s=85,marker=marker)
   ax.annotate(('VN' if g=='square_vn' else 'HC')+'/'+{'markov':'Scalar','box':'Box','ql':'Ball'}[f],
    (q.mean_activity_lesion,q.target_corr_lesion),xytext=(4,4),textcoords='offset points',fontsize=8)
 ax.set(xlabel='Final mean activity',ylabel='Final Pearson correlation with imposed pattern A',
        title='Model activity and imposed-pattern retention')
 ax.grid(alpha=.2)
 fig.tight_layout()
 for ext in ('pdf','png'):fig.savefig(out/f'tradeoff_{severity}.{ext}',dpi=200)
 plt.close(fig)
