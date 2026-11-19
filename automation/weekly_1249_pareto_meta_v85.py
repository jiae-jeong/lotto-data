#!/usr/bin/env python3
"""V85 exploration: Pareto-guarded meta-policy; freeze rule before run.

Candidate ranking, full V43 and V52 expert models, block boundaries,
exact disjoint-30 matched null, 7000x bootstrap, and all strict pass
thresholds are unchanged from V54. At a boundary, choose V43 only if
its past 150-target mean any2 AND any3 each strictly exceed V52;
otherwise choose V52. No numeric thresholds fitted to outcomes.

CAUTION: prior experiments observed this historical holdout, so even
a nominal historical PASS is NOT untouched confirmation.
"""
from pathlib import Path
p=Path(__file__).resolve().parent/'today_meta_v43_v52_v54.py'
s=p.read_text(encoding='utf-8')
old="""     d=(2*(mav(meta52,'max_hits')-mav(meta43,'max_hits'))+4*(mav(meta52,'any2')-mav(meta43,'any2'))+3*(mav(meta52,'any3')-mav(meta43,'any3')))/9.0
     meta_locked='V52' if d>-0.03 else 'V43'
     meta43.clear();meta52.clear()"""
new="""     dominates=(mav(meta43,'any2')>mav(meta52,'any2') and mav(meta43,'any3')>mav(meta52,'any3'))
     meta_locked='V43' if dominates else 'V52'"""
assert old in s
s=s.replace(old,new)
old_window="meta43=deque(maxlen=50);meta52=deque(maxlen=50)"
assert old_window in s
s=s.replace(old_window,"meta43=deque(maxlen=150);meta52=deque(maxlen=150)")
assert 'TODAY_META_V43_V52_1248_V54.json' in s
s=s.replace('TODAY_META_V43_V52_1248_V54.json','TODAY_PARETO_META_1249_V85.json')
assert "'META_V43_V52_V54'" in s
s=s.replace("'META_V43_V52_V54'","'PARETO_META_V85'")
old_desc="Keep V52 unless its weighted prior-block disadvantage 2*max+4*any2+3*any3 exceeds 0.03; otherwise use V43."
assert old_desc in s
s=s.replace(old_desc,"Choose V43 only when it strictly dominates V52 on BOTH previous150 mean any2 and mean any3; otherwise V52.")
needle="exec(compile(s,str(p),'exec'),globals(),globals())"
assert needle in s
patch="""old_load="assert o[-1]['round']==1247 and [x['round'] for x in o]==list(range(1,1248))"
assert old_load in s
s=s.replace(old_load,"assert o[-1]['round']==1248 and [x['round'] for x in o]==list(range(1,1249))")
old_meta="'target_round':1248,'data_cutoff':1247"
assert old_meta in s
s=s.replace(old_meta,"'target_round':1249,'data_cutoff':1248")
old_path="analysis/2026-10-30/TODAY_PARETO_META_1249_V85.json"
assert old_path in s
s=s.replace(old_path,"analysis/2026-11-06/TODAY_PARETO_META_1249_V85.json")
assert "alpha=.05/4" in s and "SEED=202610301154" in s
"""
s=s.replace(needle,patch+needle)
exec(compile(s,str(p),'exec'),globals(),globals())
