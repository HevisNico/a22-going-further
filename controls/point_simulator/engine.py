"""Event-driven numerical A22 assay for one full three-input cell.

Physical laws are unchanged for mode='a22'. Auxiliary event times are solved
independently because their dynamics do not depend on the main mode. Main
READY flow is analytic except the small ERROR/raw-current overlap, handled
by adaptive scalar ODE integration. Protected flow integrates the actual
mark-driven b(t), including its cap. All doses use physical endpoints.

This is a floating-point research simulator, NOT an interval certificate or
a verifier of every weak ordering. Near-coincident events are logged.
"""
import math
from dataclasses import dataclass
import numpy as np
from scipy.optimize import brentq
from scipy.integrate import solve_ivp, quad

A=math.log(4); K=.5; R=.1; RM=.025; BMAX=1.1
NOMINAL=np.array([4, math.log(1.25)/.02, math.log(8)/1.06, A/.15,
                  (1-RM)/(A/(A-K)*(math.exp(-K*.02)-math.exp(-A*.02)))])

def h(u, kappa=K):
    if kappa == A:
        return A*u*math.exp(-A*u)
    return A/(A-kappa)*(math.exp(-kappa*u)-math.exp(-A*u))

@dataclass
class Device:
    params: list  # three rows C,LM,LS,LE,M
    initial_q: float
    initial_m: list
    initial_z: list
    initial_b: float
    initial_aux: list
    # Exploratory families only: the certified family uses these defaults.
    # The main trigger varies; its reset remains 1 and its emitted pulse is canonical.
    main_threshold: float = 1.
    kappa: float = K
    # Per port: READY->MARK, MARK->SILENT, SILENT->ERROR. Rest stays RM.
    auxiliary_thresholds: list | None = None

def thresholds(device):
    values = np.array(device.auxiliary_thresholds if device.auxiliary_thresholds is not None
                      else [[1., .8, .1]]*3, dtype=float)
    if (values.shape != (3, 3) or not np.all(np.isfinite(values))
            or not np.all(values[:, 0] > values[:, 1])
            or not np.all(values[:, 1] > values[:, 2]) or not np.all(values[:, 2] > RM)):
        raise ValueError('auxiliary thresholds must be ordered above rest')
    if not (math.isfinite(device.kappa) and 0 < device.kappa < A
            and math.isfinite(device.main_threshold) and device.main_threshold > .25):
        raise ValueError('invalid leak or main threshold')
    return values

def prepare_auxiliary(arrivals, device):
    events=[]
    levels=thresholds(device); kappa=device.kappa
    for j in range(3):
        firing, mark_end, error_start = levels[j]
        cap,lm,ls,le,mult=device.params[j]
        mode=device.initial_aux[j]
        if mode not in (0,3): raise ValueError('unsupported initial auxiliary mode')
        finish=0.
        initial_m=device.initial_m[j]
        if mode==3:
            finish=math.log(initial_m/RM)/le
            events.append((finish,'aux',j,0,RM))
        previous=None
        for arrival in arrivals[j]:
            if arrival < 0: raise ValueError('input cannot precede initialization')
            if previous is not None and arrival-previous <= 1: raise ValueError('raw pulses overlap on a port')
            if previous is not None and arrival < finish-1e-10:
                raise ValueError('auxiliary unfinished at next input; local separation obligation failed')
            # Original initialization permits a residual ERROR overlapping the
            # source pulse at t=0. That raw pulse is admitted by the auxiliary
            # only after the residual phase ends; no physical reset is added.
            ready_start=max(arrival,finish) if previous is None and mode==3 else arrival
            mstart=RM+(initial_m-RM)*math.exp(-kappa*arrival) if previous is None and mode==0 else RM
            attenuation=math.exp(-A*(ready_start-arrival))
            delay=brentq(lambda u:RM+(mstart-RM)*math.exp(-kappa*u)+mult*attenuation*h(u,kappa)-firing,
                         0,min(.1,arrival+1-ready_start),xtol=1e-14)
            mark=ready_start+delay
            silent=mark+math.log(firing/mark_end)/lm
            error=silent+math.log(mark_end/error_start)/ls
            finish=error+math.log(error_start/RM)/le
            events.extend([(arrival,'on',j,0,0),(arrival+1,'off',j,0,0),
                           (mark,'aux',j,1,firing),(silent,'aux',j,2,mark_end),
                           (error,'aux',j,3,error_start),(finish,'aux',j,0,RM)])
            previous=arrival
    return sorted(events,key=lambda e:(e[0],e[1],e[2]))

def simulate(arrivals, device, end, mode='a22', fixed=None, checkpoints=()):
    if mode not in ('a22','fixed','gain_only','recovery_only'):
        raise ValueError('invalid mode')
    learn_g=mode in ('a22','gain_only'); learn_b=mode in ('a22','recovery_only')
    kappa=device.kappa; trigger=device.main_threshold
    events=prepare_auxiliary(arrivals,device)
    events.extend((float(t),'checkpoint',-1,0,0) for t in checkpoints if 0<=t<=end)
    events.append((end,'end',-1,0,0))
    events.sort(key=lambda e:(e[0],e[1],e[2]))
    cap=np.log(np.array(device.params)[:,0]); lm=np.array(device.params)[:,1]
    ls=np.array(device.params)[:,2]; le=np.array(device.params)[:,3]; mult=np.array(device.params)[:,4]
    q=device.initial_q
    z=np.array(device.initial_z,dtype=float) if fixed is None else np.log(np.array(fixed['g'],dtype=float))
    b=device.initial_b if fixed is None else float(fixed['b'])
    if np.any(z>cap+1e-12) or b<=0 or b>BMAX+1e-12: raise ValueError('initial physical bound violated')
    main=0; aux=list(device.initial_aux); aux_origin=np.zeros(3)
    aux_value=np.array(device.initial_m,dtype=float)
    raw=np.zeros(3,dtype=bool); raw_origin=np.zeros(3)
    t=0.; idx=0; fire_start=None
    energy=np.zeros(3)  # main, auxiliary, actual actuation
    outputs=[]; snapshots={}; near=0; nonlinear=0; steps=0; main_events=[]
    activity={'gain_dose':[0.,0.,0.],'recovery_dose':0.,'partial_mark_segments':0,
              'protected_mark_segments':0,'ready_error_segments':0}
    def snapshot(now):
        charges=[]
        for j in range(3):
            if aux[j]:
                charges.append(aux_value[j]*math.exp(-[0,lm[j],ls[j],le[j]][aux[j]]*(now-aux_origin[j])))
            else:
                val=RM+(aux_value[j]-RM)*math.exp(-kappa*(now-aux_origin[j]))
                if raw[j]:
                    start=max(raw_origin[j],aux_origin[j])
                    val+=mult[j]*math.exp(-A*(start-raw_origin[j]))*h(max(0,now-start),kappa)
                charges.append(val)
        return {'energy':energy.tolist(),'gain':np.exp(z).tolist(),'b':b,'main_mode':main,'q':q,
                'aux_modes':list(aux),'aux_charge':charges,'raw_active':raw.tolist(),
                'outgoing_active':main==1}
    while t < end-1e-11:
        while idx<len(events) and events[idx][0]<=t+2e-11:
            time,kind,j,phase,value=events[idx]
            if kind=='on': raw[j]=True;raw_origin[j]=time
            elif kind=='off': raw[j]=False
            elif kind=='aux': aux[j]=phase;aux_origin[j]=time;aux_value[j]=value
            elif kind=='checkpoint':
                snapshots[str(time)]=snapshot(time)
            idx+=1
        boundary=min(end,events[idx][0] if idx<len(events) else end)
        dt=boundary-t
        if dt<=0: raise RuntimeError('event scheduler did not advance')
        steps+=1
        if steps>100000: raise RuntimeError('event budget exceeded')
        pulses=np.where(raw,A*np.exp(-A*(t-raw_origin)),0.)
        mnow=np.array([aux_value[j]*math.exp(-([0,lm[j],ls[j],le[j]][aux[j]])*(t-aux_origin[j]))
                      if aux[j] else RM for j in range(3)])
        errors=np.array([learn_g and main==0 and aux[j]==3 and z[j]<cap[j]-1e-13 for j in range(3)])
        marks=np.array([learn_b and main!=0 and aux[j]==1 for j in range(3)])
        z0=z.copy(); b0=b; q0=q
        eg=np.where(errors,8*mnow,0.)
        mb=np.where(marks,.5*mnow,0.)
        def zend(u): return np.minimum(cap,z0+eg*(-np.expm1(-le*u)))
        def braw(u): return b0+float(np.sum(mb*(-np.expm1(-lm*u))))
        def bend(u): return min(BMAX,braw(u))
        def bunc_integral(u): return b0*u+float(np.sum(mb*(u+np.expm1(-lm*u)/lm)))
        contact=None
        if b0<BMAX and braw(dt)>BMAX:
            contact=brentq(lambda u:braw(u)-BMAX,0,dt,xtol=1e-13)
        def bint(u):
            if b0>=BMAX:return BMAX*u
            if contact is not None and u>contact:return bunc_integral(contact)+BMAX*(u-contact)
            return bunc_integral(u)
        event=None; numerical_flow=None
        if main==0:
            variable=bool(np.any(errors & raw))
            if variable:
                nonlinear+=1
                def rhs(u,v):return [kappa*(R-v[0])+float(np.dot(np.exp(zend(u)),pulses))*math.exp(-A*u)]
                def threshold(u,v):return v[0]-trigger
                threshold.terminal=True;threshold.direction=1
                numerical_flow=solve_ivp(rhs,(0,dt),[q0],events=threshold,dense_output=True,
                                         method='DOP853',rtol=1e-11,atol=1e-13)
                if not numerical_flow.success:raise RuntimeError(numerical_flow.message)
                if len(numerical_flow.t_events[0]):dt=float(numerical_flow.t_events[0][0]);event='fire'
                q=float(numerical_flow.y[0,-1])
            else:
                J=float(np.dot(np.exp(z0),pulses)); bb=J/(A-kappa); aa=q0-R+bb
                def ready(u):return R+aa*math.exp(-kappa*u)-bb*math.exp(-A*u)
                probe=dt
                if aa>0 and J>0:
                    ratio=A*bb/(kappa*aa)
                    if ratio>0:probe=min(dt,max(0,math.log(ratio)/(A-kappa)))
                if probe>0 and ready(probe)>=trigger:
                    dt=brentq(lambda u:ready(u)-trigger,0,probe,xtol=1e-13);event='fire'
                q=ready(dt)
        elif main==1:
            remaining=fire_start+1-t
            if remaining<=dt+1e-12:dt=max(0,remaining);event='fast_end'
            q=q0*math.exp(-A*dt)
        else:
            target=math.log(q0/R)
            if bint(dt)>=target:
                dt=brentq(lambda u:bint(u)-target,0,dt,xtol=1e-13);event='reopen'
            q=q0*math.exp(-bint(dt))
        z=zend(dt);b=bend(dt)
        activity['gain_dose']=(np.array(activity['gain_dose'])+z-z0).tolist()
        activity['recovery_dose']+=b-b0
        if dt>0:
            activity['ready_error_segments']+=int(np.any(errors))
            activity['protected_mark_segments']+=int(np.any(marks))
            activity['partial_mark_segments']+=int(np.any(marks & ((t-aux_origin)>1e-9)))
        if main==0:
            if numerical_flow is not None:
                main_work=quad(lambda u:float(np.dot(np.exp(zend(u)),pulses))*math.exp(-A*u),0,dt,epsabs=1e-11)[0]
            else:main_work=float(np.dot(np.exp(z0),pulses))*(-math.expm1(-A*dt))/A
        elif main==1:main_work=q0-q
        else:main_work=1.1*dt
        aux_work=0.
        for j in range(3):
            if aux[j]==0:aux_work+=mult[j]*pulses[j]*(-math.expm1(-A*dt))/A
            else:aux_work+=mnow[j]*(-math.expm1(-[0,lm[j],ls[j],le[j]][aux[j]]*dt))
        energy+=np.array([main_work,aux_work,float(np.sum(z-z0))+b-b0])
        t+=dt
        if event:
            main_events.append({'time':t,'event':event,'b':b})
            if abs(t-boundary)<2e-9:near+=1
            if event=='fire':
                outputs.append(t);main=1;q=1.;fire_start=t
            elif event=='fast_end':main=2;q=.25
            else:main=0;q=R
        if dt<=1e-14 and event is None:raise RuntimeError('zero step')
    # End checkpoints, if present, have not been consumed by the main loop.
    for time,kind,_,_,_ in events[idx:]:
        if kind=='checkpoint' and abs(time-end)<1e-8:
            snapshots[str(time)]=snapshot(time)
    return {'main_events':main_events,'outputs':outputs,'energy':energy.tolist(),'snapshots':snapshots,
            'final_gain':np.exp(z).tolist(),'final_b':b,'near_main_external_coincidences':near,
            'nonlinear_ready_segments':nonlinear,'segments':steps,'activity':activity,
            'final_state':snapshot(t)}
