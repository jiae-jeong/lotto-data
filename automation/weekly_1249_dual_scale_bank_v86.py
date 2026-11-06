#!/usr/bin/env python3
"""V86 exploratory independent rank experiment.
Only candidate bank changes: 3 long-timescale + 3 multiscale consensus core.
All 5-line construction, matched exact-null, inferential gate, random seed
and V54 meta-expert selection are unchanged. Historical data were examined
before this test, so nominal PASS is not independent verification.
"""
from pathlib import Path
p=Path(__file__).resolve().parent/'today_meta_v43_v52_v54.py'
outer=p.read_text(encoding='utf-8')
assert "TODAY_META_V43_V52_1248_V54.json" in outer
outer=outer.replace("TODAY_META_V43_V52_1248_V54.json","TODAY_DUAL_SCALE_BANK_1249_V86.json")
assert "'META_V43_V52_V54'" in outer
outer=outer.replace("'META_V43_V52_V54'","'DUAL_SCALE_BANK_V86'")
needle="exec(compile(s,str(p),'exec'),globals(),globals())"
patch="""old_rank=''' core=sorted(range(1,46),key=lambda n:(-slow[n],n))[:6]
 tail=sorted((n for n in range(1,46) if n not in core),key=lambda n:(-blend[n],n))[:24]
 return core+tail'''
new_rank=''' slow3=sorted(range(1,46),key=lambda n:(-slow[n],n))[:3]
 consensus3=sorted((n for n in range(1,46) if n not in slow3),key=lambda n:(-blend[n],n))[:3]
 core=slow3+consensus3
 tail=sorted((n for n in range(1,46) if n not in core),key=lambda n:(-blend[n],n))[:24]
 return core+tail'''
assert old_rank in s
s=s.replace(old_rank,new_rank)
old_load="assert o[-1]['round']==1247 and [x['round'] for x in o]==list(range(1,1248))"
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
assert needle in outer
outer=outer.replace(needle,patch+needle)
exec(compile(outer,str(p),'exec'),globals(),globals())
