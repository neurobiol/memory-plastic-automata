"""Validate local focused implementation against primary v1.1.0 release tables."""
from pathlib import Path
import pandas as pd, numpy as np, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run_controls import Config, run_original_summary

# v1.1.0 results/primary/tables/summary_by_condition.csv, alpha_async, lesion.
archived={
 ('honeycomb','fixed','markov'):(0.19430558848835017,0.1863131967300427),
 ('honeycomb','plastic','markov'):(0.19349153787913967,0.19971710360449468),
 ('honeycomb','fixed','ql'):(0.3923454051271569,-0.00630938430222856),
 ('honeycomb','plastic','ql'):(0.39318862967307905,-0.002436816010706),
 ('square_vn','fixed','markov'):(0.14307400432360284,0.23127998408200426),
 ('square_vn','plastic','markov'):(0.13897756093684122,0.24180399337180755),
 ('square_vn','fixed','ql'):(0.40130503348928565,0.00132761414425526),
 ('square_vn','plastic','ql'):(0.4004276543298967,-0.00404120903332222),
}
rows=[]
for (g,p,f),(ref_a,ref_c) in archived.items():
    got=[run_original_summary(Config(geometry=g,plasticity=p,formalism=f,seed=s)) for s in range(1,6)]
    ga=np.mean([x[0] for x in got]); gc=np.mean([x[1] for x in got]);
    rows.append({'geometry':g,'plasticity':p,'formalism':f,'activity_archived':ref_a,
                 'activity_local':ga,'activity_diff':ga-ref_a,
                 'repair_corr_archived':ref_c,'repair_corr_local':gc,
                 'repair_corr_diff':gc-ref_c})
df=pd.DataFrame(rows)
out=Path(__file__).resolve().parent/'combined'
out.mkdir(exist_ok=True)
df.to_csv(out/'archived_parity.csv',index=False)
print(df[['geometry','plasticity','formalism','activity_diff','repair_corr_diff']].to_string(index=False))
print('max absolute discrepancy',float(df[['activity_diff','repair_corr_diff']].abs().max().max()))
assert df[['activity_diff','repair_corr_diff']].abs().max().max()<1e-10
