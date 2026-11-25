from pathlib import Path
import pandas as pd, numpy as np, json
root=Path(__file__).resolve().parent
frames=[pd.read_csv(root/d/'metrics_by_time.csv') for d in ['batch_square_fixed','batch_square_plastic','batch_honey_fixed','batch_honey_plastic']]
df=pd.concat(frames,ignore_index=True)
out=root/'combined';out.mkdir(exist_ok=True)
df.to_csv(out/'metrics_by_time.csv',index=False)
final=df.sort_values('dt').groupby(['geometry','plasticity','seed','formalism','area_mode'],as_index=False).tail(1).copy()
final.to_csv(out/'final_by_case.csv',index=False)
base=df[df.dt==0].set_index(['geometry','plasticity','seed','formalism','area_mode'])
final=final.set_index(['geometry','plasticity','seed','formalism','area_mode'])
final['initial_damage_mae_local']=base['damage_mae_local']
final['initial_damage_mae_global']=base['damage_mae_global']
final['local_damage_remaining_ratio']=final['damage_mae_local']/(final['initial_damage_mae_local']+1e-15)
final['local_pre_error_lesion_minus_sham']=final['pre_mae_local']-final['sham_pre_mae_local']
final['global_pre_error_lesion_minus_sham']=final['pre_mae_global']-final['sham_pre_mae_global']
final['target_corr_damaged_minus_sham']=final['target_corr_lesion']-final['target_corr_sham']
final.to_csv(out/'derived_by_case.csv')
print('Final effects by model:')
s=final.groupby(['geometry','plasticity','area_mode','formalism'])[
 ['initial_damage_mae_local','damage_mae_local','damage_mae_global','local_damage_remaining_ratio','pre_mae_local','sham_pre_mae_local','local_pre_error_lesion_minus_sham','target_corr_lesion','target_corr_sham','mean_activity_lesion','mean_activity_sham']].mean()
s.to_csv(out/'summary_by_model.csv')
print(s.to_string(float_format=lambda x:f'{x:.4f}'))
# Pairwise dimensionality matches on the same geometry, seed, plasticity and severity
idx=['geometry','plasticity','seed','area_mode']
a=final.reset_index()
wide=a.pivot(index=idx,columns='formalism',values=['target_corr_lesion','mean_activity_lesion','damage_mae_local','local_damage_remaining_ratio','pre_mae_local','sham_pre_mae_local'])
pair=pd.DataFrame(index=wide.index)
for metric in ['target_corr_lesion','mean_activity_lesion','damage_mae_local','local_damage_remaining_ratio','pre_mae_local']:
  for lhs,rhs in [('ql','markov'),('ql','box'),('box','markov')]:
    pair[f'{metric}__{lhs}_minus_{rhs}']=wide[(metric,lhs)]-wide[(metric,rhs)]
pair.reset_index().to_csv(out/'paired_model_contrasts.csv',index=False)
print('\nContrast mean:')
print(pair.groupby(['geometry','plasticity','area_mode']).mean().to_string(float_format=lambda x:f'{x:.4f}'))
# Post-lesion trajectory and divergence time comparisons
traj=df.groupby(['geometry','plasticity','area_mode','formalism','dt'],as_index=False)[['damage_mae_local','damage_mae_global','pre_mae_local','sham_pre_mae_local','target_corr_lesion','target_corr_sham']].mean()
traj.to_csv(out/'mean_trajectories.csv',index=False)
print('\nCoverage',df.groupby(['geometry','area_mode']).realized_lesion_fraction.first().to_string())
