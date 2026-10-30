"""Slow numerical cross-check, directly integrates all three auxiliary charges.

Does not use engine.prepare_auxiliary, its section-flow functions, or its
root/charge-dose formulas. It shares only declared constants/data structures.
Floating-point deterministic event ordering is not a weak-order certificate.
"""
import math
import numpy as np
from scipy.integrate import solve_ivp
from engine import A,K,R,RM,BMAX

def simulate_ode(arrivals,device,end,mode='a22',fixed=None):
    pars=np.array(device.params);cap=np.log(pars[:,0]);lm=pars[:,1];ls=pars[:,2];le=pars[:,3];mult=pars[:,4]
    z=np.array(device.initial_z) if fixed is None else np.log(fixed['g'])
    b=device.initial_b if fixed is None else fixed['b']
    y=np.array([device.initial_q,*device.initial_m,*z,b,0.,0.,0.])
    main=0;aux=list(device.initial_aux);gc=z>=cap-1e-12;bc=b>=BMAX-1e-12
    lg=mode in ('a22','gain_only');lb=mode in ('a22','recovery_only')
    raw=np.zeros(3,dtype=bool);orig=np.zeros(3)
    ext=sorted([(s,'on',j) for j in range(3) for s in arrivals[j]]+[(s+1,'off',j) for j in range(3) for s in arrivals[j]])
    idx=0;t=0.;out=[]
    while t<end-1e-10:
        while idx<len(ext) and ext[idx][0]<=t+1e-10:
            when,kind,j=ext[idx];raw[j]=(kind=='on')
            if kind=='on':orig[j]=when
            idx+=1
        bound=min(end,ext[idx][0] if idx<len(ext) else end)
        if main==0 and not any(aux) and not any(raw) and y[0]<1 and max(y[1:4])<1:
            decay=math.exp(-K*(bound-t))
            y[0]=R+(y[0]-R)*decay;y[1:4]=RM+(y[1:4]-RM)*decay
            t=bound
            continue
        def rhs(now,v):
            q=v[0];m=v[1:4];zz=v[4:7];bb=v[7]
            p=np.where(raw,A*np.exp(-A*(now-orig)),0.)
            drive=float(np.dot(np.exp(zz),p))
            dq=K*(R-q)+drive if main==0 else -A*q if main==1 else -bb*q
            dm=np.array([K*(RM-m[j])+mult[j]*p[j] if aux[j]==0 else -[0,lm[j],ls[j],le[j]][aux[j]]*m[j] for j in range(3)])
            dz=np.array([8*le[j]*m[j] if lg and main==0 and aux[j]==3 and not gc[j] else 0 for j in range(3)])
            db=.5*sum(lm[j]*m[j] for j in range(3) if aux[j]==1) if lb and main!=0 and not bc else 0.
            wm=drive if main==0 else A*q if main==1 else 1.1
            wa=sum(mult[j]*p[j] if aux[j]==0 else [0,lm[j],ls[j],le[j]][aux[j]]*m[j] for j in range(3))
            return [dq,*dm,*dz,db,wm,wa,float(sum(dz))+db]
        specs=[('main',0,1 if main==0 else .25 if main==1 else R,1 if main==0 else -1)]
        specs += [('aux',j+1,[1,.8,.1,RM][aux[j]],1 if aux[j]==0 else -1) for j in range(3)]
        specs += [('gaincap',j+4,cap[j],1) for j in range(3) if lg and not gc[j]]
        if lb and not bc:specs.append(('bcap',7,BMAX,1))
        functions=[]
        for kind,index,target,direction in specs:
            def event(now,v,index=index,target=target):return v[index]-target
            event.terminal=True;event.direction=direction;functions.append(event)
        sol=solve_ivp(rhs,(t,bound),y,method='DOP853',rtol=2e-10,atol=2e-12,max_step=.2,events=functions)
        if not sol.success:raise RuntimeError(sol.message)
        old=t;t=float(sol.t[-1]);y=sol.y[:,-1]
        actual={i for i,a in enumerate(sol.t_events) if len(a)}
        # Continuous states make exact simultaneous switches commute here;
        # include numerically coincident crossings and report only diagnostics.
        if actual:
            actual.update(i for i,(_,j,target,_) in enumerate(specs) if abs(y[j]-target)<2e-9)
        for i in sorted(actual):
            kind,j,target,_=specs[i];y[j]=target
            if kind=='main':
                if main==0:main=1;out.append(t)
                elif main==1:main=2
                else:main=0
            elif kind=='aux':aux[j-1]=(aux[j-1]+1)%4
            elif kind=='gaincap':gc[j-4]=True
            else:bc=True
        if t<=old and not actual:raise RuntimeError('no ODE progress')
    return {'outputs':out,'energy':y[8:11].tolist(),'final_gain':np.exp(y[4:7]).tolist(),'final_b':float(y[7]),
            'final_q':float(y[0]),'final_m':y[1:4].tolist(),'final_main_mode':main,'final_aux_modes':aux}
