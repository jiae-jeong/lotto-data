#!/usr/bin/env python3
"""V83 exploratory strict-gate test, prospectively specified for this execution.
Modify only V54 meta-expert selection to a 150-round any2-guarded rule.
Use the same 1248 cutoff, V54 source models and matched exact null; retain
the original strict portfolio gate in its entirety.
Historical results have been inspected in prior experiments, so a nominal
PASS here would still require independent prospective confirmation.
"""
from pathlib import Path
p=Path(__file__).resolve().parent/'today_meta_v43_v52_v54.py'
source=p.read_text(encoding='utf-8')
decision_old="""     d=(2*(mav(meta52,'max_hits')-mav(meta43,'max_hits'))+4*(mav(meta52,'any2')-mav(meta43,'any2'))+3*(mav(meta52,'any3')-mav(meta43,'any3')))/9.0
     meta_locked='V52' if d>-0.03 else 'V43'
     meta43.clear();meta52.clear()"""
decision_new="""     def guarded_any2(q):
      a=list(q);n=len(a)
      p=(sum(float(x['any2']) for x in a)+20*float(NULL['any2']))/(n+20.)
      lower=p-math.sqrt(p*(1.-p)/(n+20.))
      tail3=(mav(a,'any3')-float(NULL['any3'])) if a else 0.
      mx=(mav(a,'max_hits')-float(NULL['max_hits'])) if a else 0.
      return lower+0.15*tail3+0.08*mx
     meta_locked='V52' if guarded_any2(meta52)>=guarded_any2(meta43) else 'V43'"""
assert decision_old in source
source=source.replace(decision_old,decision_new)
assert "meta43=deque(maxlen=50);meta52=deque(maxlen=50)" in source
source=source.replace("meta43=deque(maxlen=50);meta52=deque(maxlen=50)","meta43=deque(maxlen=150);meta52=deque(maxlen=150)")
assert "TODAY_META_V43_V52_1248_V54.json" in source
source=source.replace("TODAY_META_V43_V52_1248_V54.json","TODAY_ANY2_GUARDED_1249_V83.json")
assert "'META_V43_V52_V54'" in source
source=source.replace("'META_V43_V52_V54'","'ANY2_GUARDED_V83'")
needle="exec(compile(s,str(p),'exec'),globals(),globals())"
patch="""old_load="assert o[-1]['round']==1247 and [x['round'] for x in o]==list(range(1,1248))"
assert old_load in s
s=s.replace(old_load,"assert o[-1]['round']==1248 and [x['round'] for x in o]==list(range(1,1249))")
old_meta="'target_round':1248,'data_cutoff':1247"
assert old_meta in s
s=s.replace(old_meta,"'target_round':1249,'data_cutoff':1248")
old_output="analysis/2026-10-30/TODAY_ANY2_GUARDED_1249_V83.json"
assert old_output in s
s=s.replace(old_output,"analysis/2026-11-06/TODAY_ANY2_GUARDED_1249_V83.json")
assert "alpha=.05/4" in s and "SEED=202610301154" in s
"""
assert needle in source
source=source.replace(needle,patch+needle)
exec(compile(source,str(p),'exec'),globals(),globals())
