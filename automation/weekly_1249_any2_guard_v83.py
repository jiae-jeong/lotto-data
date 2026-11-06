#!/usr/bin/env python3
"""V83 preregistered one-axis research: trailing 150-target any2 lower-bound
expert selector. Only the meta expert selection changes from V54.
Inherited V54 ranking, V43/V52 expert construction, exact label-matched null,
Bonferroni bootstrap and strict pass gate are unchanged.
This is exploratory on previously inspected historical data and MUST NOT be
declared independently confirmed even if the nominal strict gate is passed.
"""
from pathlib import Path
p=Path(__file__).resolve().parent/'weekly_1249_frozen_v54.py'
outer=p.read_text(encoding='utf-8')
old="""outer=p.read_text(encoding='utf-8')
old_output="""
new="""outer=p.read_text(encoding='utf-8')
# V54 source text is loaded into `outer` by the frozen replay wrapper.
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
assert decision_old in outer
outer=outer.replace(decision_old,decision_new)
old_window="meta43=deque(maxlen=50);meta52=deque(maxlen=50)"
new_window="meta43=deque(maxlen=150);meta52=deque(maxlen=150)"
assert old_window in outer
outer=outer.replace(old_window,new_window)
old_output="""
assert old in outer
outer=outer.replace(old,new)
old2="assert old_output in outer"
# Use a different version output path so the V54 replay evidence is never modified.
assert old2 in outer
outer=outer.replace('"TODAY_META_V43_V52_1249_FROZEN_V54.json"', '"TODAY_ANY2_GUARDED_1249_V83.json"')
outer=outer.replace('"analysis/2026-11-06/TODAY_META_V43_V52_1249_FROZEN_V54.json"','"analysis/2026-11-06/TODAY_ANY2_GUARDED_1249_V83.json"')
exec(compile(outer,str(p),'exec'),globals(),globals())
