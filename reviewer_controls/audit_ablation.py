"""Numerical sensitivity audit of analytically identical scalar and diagonal-QL maps."""
from pathlib import Path
from dataclasses import replace
import numpy as np,pandas as pd
from run_controls import Config,init,step,plastic_step,intervene,lesion_mask
rows=[]
for geo in ('square_vn','honeycomb'):
 for plastic in ('fixed','plastic'):
  for seed in (1,2):
   for memory in (0.,.3):
    c=Config(geometry=geo,plasticity=plastic,seed=seed,L=52,T=280,imprint_start=90,imprint_duration=40,lesion_time=180,memory_strength=memory)
    d=replace(c,formalism='ql_diag')
    a,b=init(c),init(d)
    maxp=maxw=0.;first_nontrivial=None; t0diff=None
    for t in range(c.T):
      step(a,c,t);step(b,d,t)
      if t==c.lesion_time:
       mask=lesion_mask(c.L,c.geometry,c.lesion_fraction);intervene(a,mask);intervene(b,mask)
      plastic_step(a,c);plastic_step(b,d)
      diff=np.max(abs(a['st']['p']-b['st']['p']))
      if t==0:t0diff=float(diff)
      if diff>1e-6 and first_nontrivial is None:first_nontrivial=t
      maxp=max(maxp,float(diff)); maxw=max(maxw,float(np.max(abs(a['w']-b['w']))))
    rows.append({'geometry':geo,'plasticity':plastic,'seed':seed,'memory_strength':memory,'first_sweep_diff_gt_1e-6':first_nontrivial,
                 'first_step_max_diff':t0diff,'end_activity_scalar':float(a['st']['p'].mean()),'end_activity_diag':float(b['st']['p'].mean()),
                 'end_activity_delta':float(b['st']['p'].mean()-a['st']['p'].mean()),
                 'end_field_mae':float(np.mean(abs(a['st']['p']-b['st']['p']))),'max_step_site_diff':maxp,'max_weight_diff':maxw})
df=pd.DataFrame(rows)
root=Path(__file__).resolve().parent/'combined'
df.to_csv(root/'ablation_precision_audit.csv',index=False)
print('Number of pairs',len(df)); print('max first-step difference',df.first_step_max_diff.max())
print('First sweep diff > 1e-6 range',df['first_sweep_diff_gt_1e-6'].min(),df['first_sweep_diff_gt_1e-6'].max())
print('End field MAE median',df.end_field_mae.median(),'mean',df.end_field_mae.mean())
print('Activity difference mean absolute',df.end_activity_delta.abs().mean(),'max',df.end_activity_delta.abs().max())
print(df.groupby('geometry')[['end_field_mae','end_activity_delta','max_step_site_diff']].agg(['mean','max']).to_string())
