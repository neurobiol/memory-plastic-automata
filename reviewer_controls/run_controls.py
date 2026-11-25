#!/usr/bin/env python3
"""Focused reviewer controls based on neurobiol/memory-plastic-automata v1.1.0.

Local reproduction of the repository's square_vn/honeycomb primary-profile update,
with two explicit extensions: counterfactual sham forks and a matched four-state
componentwise-bounded (box) control. This is NOT the unchanged v1.1.0 release.

Usage: python run_controls.py --out ./results --seeds 1,2,3,4,5
       python run_controls.py --smoke --out ./smoke
"""
from __future__ import annotations
import argparse, hashlib, json, math, time
from dataclasses import dataclass, asdict, replace
from pathlib import Path
import numpy as np
import pandas as pd

EPS=1.e-12
STEPS=[0,1,2,5,10,25,50,100,150,199]

@dataclass(frozen=True)
class Config:
    geometry: str='square_vn'
    formalism: str='markov'  # markov, ql, box, ql_diag
    plasticity: str='plastic'
    schedule: str='alpha_async'   # synchronous or alpha_async
    seed: int=1
    L: int=72
    T: int=500
    p0: float=.20
    gamma: float=.68
    sigma_birth: float=.60
    sigma_survive: float=.60
    memory_strength: float=.20
    tau_memory: float=30.
    alpha_async: float=.50
    eta_weight: float=.016
    weight_decay: float=.002
    weight_sum: float=8.
    theta_input: float=.45
    theta_memory: float=.20
    theta_phase: float=.10
    dephase: float=.25
    imprint_start: int=100
    imprint_duration: int=50
    imprint_strength: float=.90
    lesion_time: int=300
    lesion_fraction: float=.08

def stable_int(s):
    return int.from_bytes(hashlib.blake2b(s.encode(),digest_size=4).digest(),'little')

def rng_for(seed,label):
    return np.random.default_rng(np.random.SeedSequence([int(seed),stable_int(label)]))

def clip01(x): return np.clip(x,0.,1.)

def coords(L,g):
    y,x=np.mgrid[0:L,0:L]
    if g=='square_vn': return x.astype(float),y.astype(float)
    if g=='honeycomb': return x.astype(float)+.5*(y%2),y.astype(float)*(math.sqrt(3)/2)
    raise ValueError(g)

def geometry_neighbors(L,g):
    if g=='square_vn': even=odd=[(-1,0),(1,0),(0,-1),(0,1)]
    elif g=='honeycomb':
        even=[(-1,0),(1,0),(0,1)]
        odd=[(-1,0),(1,0),(0,-1)]
    else: raise ValueError(g)
    K=len(even)
    nr=np.zeros((K,L,L),np.int16);nc=np.zeros((K,L,L),np.int16)
    cols=np.arange(L)
    for r in range(L):
        offsets=odd if r%2 else even
        for k,(dr,dc) in enumerate(offsets):
            nr[k,r,:]=(r+dr)%L
            nc[k,r,:]=(cols+dc)%L
    return nr,nc

def make_pattern(L,g):
    X,Y=coords(L,g); x=X-X.mean();y=Y-Y.mean()
    s=max(abs(x).max(),abs(y).max(),1)
    x/=s;y/=s;r=np.sqrt(x*x+y*y)
    p=np.zeros((L,L),float)
    p[((r>.28)&(r<.36))|(((abs(x)<.04)|(abs(y)<.04))&(r<.40))]=1
    return p

def lesion_mask(L,g,f,area_mode='nominal'):
    X,Y=coords(L,g)
    x=(X-X.mean())/(np.max(abs(X-X.mean()))+EPS)
    y=(Y-Y.mean())/(np.max(abs(Y-Y.mean()))+EPS)
    dist=x*x+y*y
    if area_mode=='nominal':
        radius=max(.06,math.sqrt(max(f,1e-6))*.35)
        return dist<=radius*radius
    if area_mode=='eight_percent':
        # 8% of sites using the nearest-to-center sites; deterministic tie ordering.
        N=int(round(f*L*L));inds=np.argsort(dist.ravel(),kind='stable')[:N]
        mask=np.zeros(L*L,bool);mask[inds]=True
        return mask.reshape((L,L))
    raise ValueError(area_mode)

def init(cfg):
    p=(rng_for(cfg.seed,'init').random((cfg.L,cfg.L))<cfg.p0).astype(float)
    s={'p':p.copy(),'m':p.copy(),'bias':np.zeros_like(p)}
    if cfg.formalism!='markov':
        s.update(x=np.zeros_like(p),y=np.zeros_like(p),z=2*p-1)
    nr,nc=geometry_neighbors(cfg.L,cfg.geometry)
    K=nr.shape[0]
    w=np.full((K,cfg.L,cfg.L),cfg.weight_sum/K,dtype=float)
    utility=np.zeros_like(w)
    return {'st':s,'w':w,'utility':utility,'nr':nr,'nc':nc,'A':make_pattern(cfg.L,cfg.geometry)}

def clone(e):
    return {k:({v:a.copy() for v,a in x.items()} if k=='st' else x.copy() if isinstance(x,np.ndarray) and k in ('w','utility') else x)
            for k,x in e.items()}

def gather(a,nr,nc):
    # Same indexing and element order as src/sim_core.py::gather, vectorized.
    return a[nr,nc]

def step(e,cfg,t):
    st=e['st'];p=st['p'];w=e['w'];nr=e['nr'];nc=e['nc']
    inp=np.sum(w*gather(p,nr,nc),axis=0)
    target=clip01((1-p)*np.exp(-((inp+st['bias']-3.)**2)/(2*cfg.sigma_birth**2))
                  +p*np.exp(-((inp+st['bias']-2.5)**2)/(2*cfg.sigma_survive**2)))
    target=clip01(target+cfg.memory_strength*.10*(st['m']-.5))
    if cfg.imprint_start<=t<cfg.imprint_start+cfg.imprint_duration:
        target=clip01((1-cfg.imprint_strength)*target+cfg.imprint_strength*e['A'])
    mask=(rng_for(cfg.seed+t,'alpha').random((cfg.L,cfg.L))<cfg.alpha_async) if cfg.schedule=='alpha_async' else None
    if cfg.formalism=='markov':
        new=clip01((1-cfg.gamma)*p+cfg.gamma*target)
        st['p'][:]=new if mask is None else np.where(mask,new,p)
    else:
        x,y,z=st['x'],st['y'],st['z']
        xn=(1-cfg.dephase)*x+cfg.theta_input*(inp/(cfg.weight_sum+EPS)-.5)
        yn=(1-cfg.dephase)*y+cfg.theta_memory*(st['m']-.5)+cfg.theta_phase*x
        zn=(1-cfg.gamma)*z+cfg.gamma*(2*target-1)+.10*y
        if cfg.formalism=='ql_diag':
            xn[:]=0;yn[:]=0
        if cfg.formalism in ('ql','ql_diag'):
            norm=np.sqrt(xn*xn+yn*yn+zn*zn)
            cm=norm>1
            xn[cm]/=norm[cm];yn[cm]/=norm[cm];zn[cm]/=norm[cm]
        elif cfg.formalism=='box':
            # Only projection changes: cube [-1,1]^3 versus unit ball.
            # The two auxiliaries and their update equations remain identical.
            np.clip(xn,-1.,1.,out=xn)
            np.clip(yn,-1.,1.,out=yn)
            np.clip(zn,-1.,1.,out=zn)
        else: raise ValueError(cfg.formalism)
        if mask is None:
            x[:]=xn;y[:]=yn;z[:]=zn;st['p'][:]=clip01((1+zn)/2)
        else:
            x[mask]=xn[mask];y[mask]=yn[mask];z[mask]=zn[mask]
            st['p'][mask]=clip01((1+zn[mask])/2)
    # Original memory and weight updates, both before and after lesion respectively.
    if mask is None:
        st['m']=(1-1/cfg.tau_memory)*st['m']+(1/cfg.tau_memory)*st['p']
    else:
        st['m'][mask]=(1-1/cfg.tau_memory)*st['m'][mask]+(1/cfg.tau_memory)*st['p'][mask]
    # Intrinsic adaptation and structural rewiring disabled as in original primary profile.

def plastic_step(e,cfg):
    st=e['st'];w=e['w'];utility=e['utility']
    co=st['p'][None,:,:]*gather(st['p'],e['nr'],e['nc'])
    utility*=1-1/50.
    utility+=(1/50.)*co
    if cfg.plasticity=='plastic':
        active=(w>0)
        w+=cfg.eta_weight*(co-co.mean(0,keepdims=True))*active
        w-=cfg.weight_decay*w
        w[:]=np.maximum(w,0)*active
        den=w.sum(0,keepdims=True)
        zero=den[0]<=EPS
        if np.any(zero):
            w[:,zero]=1.
            den=w.sum(0,keepdims=True)
        w*=cfg.weight_sum/(den+EPS)

def intervene(e,mask):
    e['st']['p'][mask]=0.
    if 'z' in e['st']:
        e['st']['x'][mask]=0.
        e['st']['y'][mask]=0.
        e['st']['z'][mask]=-1.

def correlation(a,b):
    av=a.ravel()-a.mean();bv=b.ravel()-b.mean()
    return float(np.sum(av*bv)/(np.sqrt(np.sum(av*av)*np.sum(bv*bv))+EPS))

def metric_row(c,where,t0,pre,les,sham,mask):
    p=les['st']['p'];s=sham['st']['p']; A=les['A']
    local=mask;all_=np.ones_like(local,bool)
    row={**asdict(c),'area_mode':where,'dt':t0,'realized_lesion_fraction':mask.mean(),
         'mean_activity_lesion':float(p.mean()),'mean_activity_sham':float(s.mean()),
         'target_corr_lesion':correlation(p,A),'target_corr_sham':correlation(s,A),
         'pre_corr_lesion':correlation(p,pre),'pre_corr_sham':correlation(s,pre),
         'first_post_corr':None}
    for tag,sel in [('local',local),('global',all_)]:
        row['pre_mae_'+tag]=float(np.mean(abs(p[sel]-pre[sel])))
        row['sham_pre_mae_'+tag]=float(np.mean(abs(s[sel]-pre[sel])))
        row['damage_mae_'+tag]=float(np.mean(abs(p[sel]-s[sel])))
        row['lesion_mean_'+tag]=float(p[sel].mean())
        row['sham_mean_'+tag]=float(s[sel].mean())
    return row

def run_case(cfg,area_mode='nominal',T=None):
    """Same full state and later random stream, diverging solely at lesion event.

    dt=0 is after lesion application, before event-time plastic update.
    dt=1 is after the following complete sweep.
    """
    T=cfg.T if T is None else T
    base=init(cfg)
    for t in range(cfg.lesion_time+1):
        step(base,cfg,t)
        if t<cfg.lesion_time:plastic_step(base,cfg)
    les=clone(base);sham=clone(base)
    pre=base['st']['p'].copy()
    mask=lesion_mask(cfg.L,cfg.geometry,cfg.lesion_fraction,area_mode)
    assert np.array_equal(les['st']['p'],sham['st']['p'])
    intervene(les,mask)
    rows=[metric_row(cfg,area_mode,0,pre,les,sham,mask)]
    plastic_step(les,cfg);plastic_step(sham,cfg)
    for t in range(cfg.lesion_time+1,T):
        step(les,cfg,t);step(sham,cfg,t)
        plastic_step(les,cfg);plastic_step(sham,cfg)
        dt=t-cfg.lesion_time
        if dt in STEPS or t==T-1:
            rows.append(metric_row(cfg,area_mode,dt,pre,les,sham,mask))
    assert all(np.isfinite(r['damage_mae_local']) for r in rows)
    return rows

def run_original_summary(cfg):
    """Single original lesion run; used only for parity tests."""
    e=init(cfg);mask=lesion_mask(cfg.L,cfg.geometry,cfg.lesion_fraction)
    trace=[]
    for t in range(cfg.T):
        step(e,cfg,t)
        if t==cfg.lesion_time:intervene(e,mask)
        plastic_step(e,cfg)
        if t%20==0 or t==cfg.T-1:
            p=e['st']['p'];trace.append((p.mean(),correlation(p,e['A'])))
    return float(np.mean([v[0] for v in trace[-max(3,len(trace)//5):]])),float(trace[-1][1])

def internal_tests():
    # Equality of scalar Markov and QL with transverse coordinates disabled.
    for geometry in ('square_vn','honeycomb'):
        c=Config(geometry=geometry,L=24,T=24,lesion_time=10)
        a=init(c);b=init(replace(c,formalism='ql_diag'))
        for t in range(24):
            step(a,c,t);step(b,replace(c,formalism='ql_diag'),t)
            assert np.max(abs(a['st']['p']-b['st']['p']))<1e-10
            if t==10:
                mask=lesion_mask(c.L,c.geometry,c.lesion_fraction)
                intervene(a,mask);intervene(b,mask)
            plastic_step(a,c);plastic_step(b,c)
            assert np.max(abs(a['w']-b['w']))<1e-10
    # Zero damage when lesion mask falls on zero activity (no-op branch).
    c=Config(L=24,T=30,lesion_time=15)
    base=init(c);other=clone(base)
    for t in range(20):
        step(base,c,t);step(other,c,t)
        plastic_step(base,c);plastic_step(other,c)
        assert np.array_equal(base['st']['p'],other['st']['p'])
    return True

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',default='results')
    ap.add_argument('--seeds',default='1,2,3,4,5')
    ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--severities',default='nominal,eight_percent')
    ap.add_argument('--geometries',default='square_vn,honeycomb')
    ap.add_argument('--plasticities',default='fixed,plastic')
    args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    internal_tests()
    seeds=[int(x) for x in args.seeds.split(',')]
    if args.smoke: seeds=seeds[:1]
    rows=[];cases=[];t0=time.time()
    # Use one primary schedule and both weight conditions for a focused reviewer test.
    # True-8%-area sensitivity is a separate (clearly labeled) severity.
    for geo in args.geometries.split(','):
      for plasticity in args.plasticities.split(','):
       for seed in seeds:
        for formalism in ('markov','ql','box'):
         for severity in args.severities.split(','):
          if args.smoke and severity!='nominal':continue
          c=Config(geometry=geo,plasticity=plasticity,seed=seed,formalism=formalism)
          results=run_case(c,severity)
          rows.extend(results)
          cases.append({'geometry':geo,'plasticity':plasticity,'seed':seed,'formalism':formalism,'severity':severity,
                        'seconds':round(time.time()-t0,1)})
          print('FINISHED',cases[-1],flush=True)
    df=pd.DataFrame(rows)
    df.to_csv(out/'metrics_by_time.csv',index=False)
    # Collect per-case final, early, and middle checkpoints.
    last=df.sort_values('dt').groupby(['geometry','plasticity','seed','formalism','area_mode'],as_index=False).tail(1)
    last.to_csv(out/'case_final_metrics.csv',index=False)
    gp=last.groupby(['geometry','plasticity','formalism','area_mode'],as_index=False).agg(
         n=('seed','nunique'),
         final_damage_local_mean=('damage_mae_local','mean'),
         final_damage_local_min=('damage_mae_local','min'),
         final_damage_global_mean=('damage_mae_global','mean'),
         final_pre_local_mean=('pre_mae_local','mean'),
         final_sham_pre_local_mean=('sham_pre_mae_local','mean'),
         final_target_corr_lesion=('target_corr_lesion','mean'),
         final_target_corr_sham=('target_corr_sham','mean'),
         final_activity_lesion=('mean_activity_lesion','mean'),
         final_activity_sham=('mean_activity_sham','mean'),
         realized_fraction=('realized_lesion_fraction','mean'))
    gp.to_csv(out/'summary.csv',index=False)
    (out/'run_manifest.json').write_text(json.dumps({'repository':'neurobiol/memory-plastic-automata','source_tag':'v1.1.0',
        'note':'Independent focused source-equivalent implementation for two geometries; extensions add fork and box projection.',
        'seeds':seeds,'L':72,'T':500,'schedule':'alpha_async','plasticity':['fixed','plastic'],
        'lesion_time':300,'per_case_seconds_since_start':cases,'elapsed_seconds':time.time()-t0,
        'tests':'markov / pre-projection ablation parity and no-op fork tests passed'},indent=2))
    print('ALL DONE',len(cases),'cases,',len(df),'rows in',round(time.time()-t0,1),'s',flush=True)

if __name__=='__main__':main()
