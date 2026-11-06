#!/usr/bin/env python3
"""V86 exploratory dual-timescale candidate bank (pre-registered).
Independent change from V85: V54 untouched expert policy and strict gate,
but core6 = 3 long-horizon slow ranks + 3 consensus multiscale ranks.
Remaining 24 candidates chosen from consensus multiscale ranks. This
evaluates ranking improvement independently of allocator choice.
Historical dataset is previously inspected and not untouched holdout.
"""
from pathlib import Path
p=Path(__file__).resolve().parent/'today_meta_v43_v52_v54.py'
s=p.read_text(encoding='utf-8')
old=""" core=sorted(range(1,46),key=lambda n:(-slow[n],n))[:6]
 tail=sorted((n for n in range(1,46) if n not in core),key=lambda n:(-blend[n],n))[:24]
 return core+tail"""
new=""" slow3=sorted(range(1,46),key=lambda n:(-slow[n],n))[:3]
 consensus3=sorted((n for n in range(1,46) if n not in slow3),key=lambda n:(-blend[n],n))[:3]
 core=slow3+consensus3
 tail=sorted((n for n in range(1,46) if n not in core),key=lambda n:(-blend[n],n))[:24]
 return core+tail"""
assert old in s
s=s.replace(old,new)
assert 'TODAY_META_V43_V52_1248_V54.json' in s
s=s.replace('TODAY_META_V43_V52_1248_V54.json','TODAY_DUAL_SCALE_BANK_1249_V86.json')
assert "'META_V43_V52_V54'" in s
s=s.replace("'META_V43_V52_V54'","'DUAL_SCALE_BANK_V86'")
needle="exec(compile(s,str(p),'exec'),globals(),globals())"
assert needle in s
patch="""old_load="assert o[-1]['round']==1247 and [x['round'] for x in o]==list(range(1,1248))"
assert old_load in s
s=s.replace(old_load,"assert o[-1]['round']==1248 and [x['round'] for x in o]==list(range(1,1249))")
old_meta="'target_round':1248,'data_cutoff':1247"
assert old_meta in s
s=s.replace(old_meta,"'target_round':1249,'data_cutoff':1248")
old_path="analysis/2026-10-30/TODAY_DUAL_SCALE_BANK_1249_V86.json"
assert old_path in s
s=s.replace(old_path,"analysis/2026-11-06/TODAY_DUAL_SCALE_BANK_1249_V86.json")
assert "alpha=.05/4" in s and "SEED=202610301154" in s
"""
s=s.replace(needle,patch+needle)
exec(compile(s,str(p),'exec'),globals(),globals())
