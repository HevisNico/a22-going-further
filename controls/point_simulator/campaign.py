"""Predeclared full-network falsification campaign, NOT a box proof.
All devices and outcomes are saved. Training variability is not a future failure.
"""
import argparse
import gzip
import hashlib
import json
import math
import time
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import numpy as np
from engine import Device,NOMINAL,simulate

ROOT=Path(__file__).resolve().parent
TOL=1e-7
GAPS=[20.,20.,20.,23.,41.,20.,31.,20.,47.,20.,20.]

def plan():
    kinds=[('homogeneous_corner',32),('independent_uniform',64),('independent_corner',64),
           ('layer_corner',16),('lane_corner',16),('port_role_corner',16),('bottleneck',16)]
    cases=[]
    for group,(kind,count) in enumerate(kinds):
        for index in range(count):
            cases.append({'name':f'{kind}_{index:03d}','kind':kind,'index':index,
                          'seed':100000+1000*group+index,'epsilon':.1,
                          'initial_policy':['random','endpoint_ready','endpoint_error','endpoint_mixed'][index%4]})
    return cases

def make_devices(case):
    rng=np.random.default_rng(case['seed']);kind=case['kind'];idx=case['index']
    choose=lambda shape:rng.choice([.9,1.1],size=shape)
    if kind=='independent_uniform':f=rng.uniform(.9,1.1,(18,12,3,5))
    elif kind=='independent_corner':f=choose((18,12,3,5))
    elif kind=='homogeneous_corner':
        signs=np.array([1.1 if (idx>>k)&1 else .9 for k in range(5)])
        f=np.broadcast_to(signs,(18,12,3,5)).copy()
    elif kind=='layer_corner':f=np.broadcast_to(choose((18,1,1,5)),(18,12,3,5)).copy()
    elif kind=='lane_corner':f=np.broadcast_to(choose((1,12,1,5)),(18,12,3,5)).copy()
    elif kind=='port_role_corner':f=np.broadcast_to(choose((1,1,3,5)),(18,12,3,5)).copy()
    elif kind=='bottleneck':
        f=np.ones((18,12,3,5));split=[3,6,9,12][idx%4]
        low=np.array([.9,.9,.9,.9,.9]);high=np.array([1.1,1.1,1.1,1.1,1.1])
        first,second=(low,high) if idx<8 else (high,low)
        f[:split]=first;f[split:]=second
        if idx%8>=4:f[split:,:,1,:]=first
    else:raise ValueError(kind)
    devices=[];policy=case['initial_policy']
    for n in range(18):
        row=[]
        for j in range(12):
            if policy=='random':
                aux=rng.choice([0,3],3).tolist();q=.1+rng.uniform(-1e-5,1e-5)
                m=[.025+rng.uniform(0 if h==3 else -1e-5,1e-5) for h in aux]
                z=np.log([.3,1.2,.3])+rng.uniform(-1e-5,1e-5,3);b=.08+rng.uniform(-1e-5,1e-5)
            else:
                aux=([0]*3 if policy=='endpoint_ready' else [3]*3 if policy=='endpoint_error'
                     else [3*((n+j+p+idx)%2) for p in range(3)])
                q=.1+float(rng.choice([-1e-5,1e-5]));b=.08+float(rng.choice([-1e-5,1e-5]))
                m=[.025+float(rng.choice([0,1e-5] if h==3 else [-1e-5,1e-5])) for h in aux]
                z=np.log([.3,1.2,.3])+rng.choice([-1e-5,1e-5],3)
            row.append(Device((NOMINAL*f[n,j]).tolist(),q,m,z.tolist(),b,aux))
        devices.append(row)
    return devices

def protocol(gaps=None,first=230.):
    training=[8.*k for k in range(28)];future=[float(first)]
    for gap in GAPS if gaps is None else gaps:
        if gap<20:raise ValueError('future spacing below 20')
        future.append(future[-1]+gap)
    return training,future,future[-1]+60

def is_ready(s,active=True):
    return (s['main_mode']==0 and not any(s['aux_modes']) and not any(s['raw_active'])
            and not s['outgoing_active'] and (not active or abs(s['q']-.1)<=1e-9)
            and (not active or max(abs(x-.025) for x in s['aux_charge'])<=1e-9))

def metrics(records,future,end):
    expected={(n,j) for n in range(1,19) for j in range(12) if min(j,12-j)<=n}
    masks=[[] for _ in future];failures=[];notrest=[];local_notready=[];latent=[];training=[]
    actual_intervals=[];future_gain_changes=[];all_coast=[];max_delay=0.
    for c in records:
        cell=(c['layer'],c['lane']);r=c['result'];out=r['outputs'];active=cell in expected
        training.append({'cell':list(cell),'count':sum(t<230.-1e-9 for t in out)})
        state=r['snapshots']['230.0']
        if not is_ready(state,active):notrest.append({'cell':list(cell),'state':state})
        counts=[];lats=[];fires=[]
        for k,src in enumerate(future):
            upper=future[k+1] if k+1<len(future) else end
            hits=[x for x in out if src-1e-9<=x<upper-1e-9]
            counts.append(len(hits))
            if hits:masks[k].append(list(cell))
            if len(hits)==1:
                lats.append(hits[0]-src);fires.append(hits[0]);max_delay=max(max_delay,hits[0]-src)
        span=max(lats)-min(lats) if len(lats)>1 else None
        if active and span is not None:latent.append({'cell':list(cell),'span':span})
        errors=[(fires[k+1]-fires[k])-(future[k+1]-future[k]) for k in range(len(future)-1)] if len(fires)==len(future) else []
        actual_intervals.extend(abs(e) for e in errors)
        if counts!=[int(active)]*len(future) or (active and (span is None or span>TOL)):
            failures.append({'cell':list(cell),'expected_active':active,'counts':counts,
                             'latency_span':span,'latencies':lats,'interval_errors':errors})
        for item in c['local_arrival_checks']:
            snap=r['snapshots'][str(item['time'])]
            if not is_ready(snap,active):local_notready.append({'cell':list(cell),'wave':item['wave'],'time':item['time'],'state':snap})
        if active and state['main_mode']==2 and not any(state['aux_modes']) and not any(state['raw_active']):
            first=min((t for port in c['inputs'] for t in port if t>=230.),default=None)
            ready=230.+math.log(state['q']/.1)/state['b']
            if first is not None:all_coast.append({'cell':list(cell),'ready_time':ready,'first_input':first,'margin':first-ready})
        changes=[abs(a-b) for a,b in zip(state['gain'],r['final_gain'])]
        if max(changes)>TOL or abs(r['final_b']-state['b'])>TOL:
            future_gain_changes.append({'cell':list(cell),'gain_differences':changes,'b_difference':r['final_b']-state['b']})
    expected_list=[list(x) for x in sorted(expected)]
    return {'expected_mask':expected_list,'observed_masks':masks,'observed_mask_counts':[len(m) for m in masks],
            'mask_matches_all_waves':all(sorted(m)==expected_list for m in masks),
            'future_failures':failures,'future_behavior_observed':not failures,
            'not_globally_ready_at_230':notrest,'not_ready_before_local_wave':local_notready,
            'training_counts':training,'training_total':sum(x['count'] for x in training),
            'max_latency_span':max((x['span'] for x in latent),default=0.),
            'max_interval_error':max(actual_intervals,default=0.),'max_observed_latency':max_delay,
            'coasting_cells':all_coast,'future_state_changes':future_gain_changes,
            'warning':'Finite numerical observations. Global source windows are a diagnostic; anomalies require causal replay.'}

def run_network(case,devices=None,backend='fast',gaps=None,first=230.,checkpoints=True,
                mode='a22',fixed=None):
    devices=make_devices(case) if devices is None else devices
    training,future,end=protocol(gaps,first);previous=[training+future]+[[] for _ in range(11)]
    records=[];start=time.perf_counter()
    if backend=='ode':
        from ode_reference import simulate_ode
    for n in range(1,19):
        current=[]
        for j in range(12):
            inputs=[previous[(j-1)%12],previous[j],previous[(j+1)%12]]
            local=[]
            for k,src in enumerate(future):
                upper=future[k+1] if k+1<len(future) else end
                times=[t for port in inputs for t in port if src<=t<upper]
                if times:local.append({'wave':k,'time':float(min(times))})
            dates=sorted(set([230.,*future,*[x['time'] for x in local]]))
            allocation=fixed[n-1][j] if isinstance(fixed,list) else fixed
            result=(simulate(inputs,devices[n-1][j],end,checkpoints=dates,mode=mode,fixed=allocation) if backend=='fast'
                    else simulate_ode(inputs,devices[n-1][j],end,mode=mode,fixed=allocation))
            current.append(result['outputs'])
            records.append({'layer':n,'lane':j,'device':devices[n-1][j].__dict__,
                            'inputs':inputs,'local_arrival_checks':local,'result':result})
        previous=current
    r={'case':case,'backend':backend,'training':training,'future':future,'end':end,'records':records,
       'elapsed_seconds':time.perf_counter()-start,'scope':'finite numerical falsification search, not a uniform guarantee'}
    if backend=='fast':r['metrics']=metrics(records,future,end)
    return r

def save_gzip(path,obj):
    raw=json.dumps(obj,separators=(',',':'),allow_nan=False).encode()
    Path(path).write_bytes(gzip.compress(raw,compresslevel=6,mtime=0))

def work(case):
    try:
        r=run_network(case);m=r['metrics'];name=case['name']
        path=ROOT/'results/devices'/(name+'.json.gz');save_gzip(path,r)
        return {'name':name,'case':case,'status':'SIMULATED','file':str(path.relative_to(ROOT)),
                'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'elapsed_seconds':r['elapsed_seconds'],
                'future_failing_cells':len(m['future_failures']),'mask_matches':m['mask_matches_all_waves'],
                'mask_counts':m['observed_mask_counts'],'not_globally_ready':len(m['not_globally_ready_at_230']),
                'not_ready_before_local_wave':len(m['not_ready_before_local_wave']),
                'training_total':m['training_total'],'max_latency_span':m['max_latency_span'],
                'max_interval_error':m['max_interval_error'],'max_latency':m['max_observed_latency']}
    except Exception as e:
        # A failed computation is not silently counted as a successful device.
        out={'name':case['name'],'case':case,'status':'SIMULATION_ERROR','error':repr(e)}
        (ROOT/'results/devices'/(case['name']+'_error.json')).write_text(json.dumps(out,indent=2)+'\n')
        return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=4)
    p.add_argument('--limit',type=int);p.add_argument('--resume',action='store_true');args=p.parse_args()
    cases=plan();(ROOT/'results/devices').mkdir(parents=True,exist_ok=True)
    declared={'cases':cases,'source_training':[8*k for k in range(28)],'first_future':230,
              'future_gaps':GAPS,'numerical_tolerance':TOL,'purpose':'seek counterexamples before further certification'}
    (ROOT/'results/plan.json').write_text(json.dumps(declared,indent=2)+'\n')
    if args.limit:cases=cases[:args.limit]
    logfile=ROOT/'results/progress.jsonl';previous=[]
    if args.resume and logfile.exists():previous=[json.loads(s) for s in logfile.read_text().splitlines() if s.strip()]
    done={x['name'] for x in previous};cases=[c for c in cases if c['name'] not in done]
    with logfile.open('a' if args.resume else 'w') as log,ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(work,c) for c in cases]
        for job in as_completed(futures):
            row=job.result();previous.append(row);log.write(json.dumps(row)+'\n');log.flush()
            print(json.dumps(row),flush=True)
    (ROOT/'results/summary.json').write_text(json.dumps(sorted(previous,key=lambda x:x['name']),indent=2)+'\n')

if __name__=='__main__':main()
