"""Extra schema/premise and fixed-bracket consistency checks; standard library.

No A22 training engine, point simulator, or integer interval code is imported.
"""
from decimal import Decimal as D, localcontext, ROUND_CEILING
from fractions import Fraction as F
from certificate_parameters import resolve_epsilon

def graph():
    prev=[True]+[False]*11;active=set();inactive=set();inputs={}
    for n in range(1,19):
        cur=[]
        for j in range(12):
            ports={p for p in range(3) if prev[(j+p-1)%12]}
            (active if ports else inactive).add((n,j));cur.append(bool(ports));inputs[n,j]=ports
        prev=cur
    return active,inactive,inputs

def interval(pair):
    assert isinstance(pair,list) and len(pair)==2
    a,b=map(F,pair);assert a<=b
    return a,b

def validate_inputs(data,certificate,eps):
    # Every declaration (terminal campaign, certificate, its campaign, explicit argument) must agree.
    assert resolve_epsilon(data,str(eps),certificate)==F(str(eps)), 'epsilon binding'
    active,inactive,inputs=graph()
    assert len(data['cells'])==216, 'terminal cell count'
    expected={(n,j) for n in range(1,19) for j in range(12)}
    keys=[(c['layer'],c['lane']) for c in data['cells']]
    assert len(set(keys))==216 and set(keys)==expected, 'terminal cell uniqueness/completeness'
    rows=[(r['layer'],r['lane']) for r in certificate['cells']]
    assert len(rows)==len(set(rows)) and set(rows)==active, 'certificate row uniqueness/completeness'
    inactive_keys=[(c['layer'],c['lane']) for c in certificate['inactive_cells']]
    assert len(inactive_keys)==len(set(inactive_keys)) and set(inactive_keys)==inactive, 'inactive mask consistency'
    for c in data['cells']:
        key=c['layer'],c['lane']
        assert c['main_phase']==0 and c['aux_phases']==[0]*3 and c['pending']==[] and c['raw_inputs']==[None]*3, ('terminal mode/current premise',key)
        assert c['E']==[50,100], ('resource domain premise',key)
        assert len(c['g'])==len(c['m'])==3
        for g in c['g']:
            low,high=interval(g)
            assert 0<low<=4*(1+F(str(eps))), ('positive/nonempty physical gain premise',key)
        low,high=interval(c['b']);assert 0<low<=F('1.1'), ('positive physical recovery floor',key)
        for p,m in enumerate(c['m']):
            low,high=interval(m);assert 0<=low<=F('.025')<=high<1, ('auxiliary rest interval premise',key,p)
            if p in inputs[key]:assert low==high==F('.025'), ('active auxiliary exact rest',key,p)
        low,high=interval(c['q'])
        if key in active:
            assert low==high==F('.1') and c['pulses']>0, ('active main exact rest',key)
        else:
            assert 0<=low<=F('.1')<=high<1 and c['pulses']==0, ('silent main interval premise',key)
    return dict(active=active,inactive=inactive,inputs=inputs)

def coarse_upper(value):
    # The checked claim is deliberately rounded outward to 40 decimal places.
    # This is a declared reporting bound, not an acceptance tolerance.
    with localcontext() as ctx:
        ctx.prec=130
        return D(value).quantize(D('1e-40'),rounding=ROUND_CEILING)

def validate_aggregates(certificate,active,masked,influential,masked_ports):
    ga,gi,ins=graph();expected_ports=sum(len(x) for x in ins.values())
    assert active==len(ga)==certificate['active_cells']==certificate['active'], 'active count consistency'
    assert certificate['inactive_count']==len(gi), 'inactive count consistency'
    assert masked==certificate['masked_count']==len(masked_ports), 'masked count consistency'
    assert influential==certificate['influential_active_ports'], 'influential count consistency'
    assert masked+influential==expected_ports==certificate['all_active_ports'], 'active port partition count'
    reported=[(r['layer'],r['lane'],r['port']) for r in certificate['masked_ports']]
    assert len(reported)==len(set(reported)) and set(reported)==set(masked_ports), 'masked port set consistency'
    return dict(active_cells=active,inactive_cells=len(gi),masked_ports=masked,influential_ports=influential,all_active_ports=expected_ports)

def validate_return(certificate,quiet,B,bound):
    bound=D(bound);assert 0<bound<=D(20), 'return contract must fit the fixed source gap 20'
    assert quiet<bound, ('global return contract',str(quiet),str(bound))
    idle=(B(20)-B(quiet)).l
    assert idle>D(0) and idle>=D(20)-bound, 'strict positive global idle margin'
    claimed=coarse_upper(certificate['global_quiescent_by'])
    assert quiet<=claimed, ('reported global return bound inconsistent',str(quiet),str(claimed))
    assert F(certificate['global_idle_margin_before_20'])==F(20)-F(certificate['global_quiescent_by']), 'reported idle/return consistency'
    return dict(requested_return_bound=str(bound),global_quiescent_upper=str(quiet),
                global_idle_margin_lower=str(idle),checked_integer_global_return_coarse_upper=str(claimed),
                reporting_rounding_grid='1e-40, ceiling')

def row_return_claim(row,computed):
    claimed=coarse_upper(row['quiescent_by'])
    assert computed<=claimed, ('reported per-cell return bound inconsistent',row['layer'],row['lane'],str(computed),str(claimed))
