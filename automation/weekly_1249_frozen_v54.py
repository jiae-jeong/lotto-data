#!/usr/bin/env python3
"""Re-run frozen V54 meta-policy for round 1249 using data only through 1248.
Only target/cutoff/output-path strings are changed; policy, random seed, null,
validation thresholds and model selection logic stay byte-for-byte identical.
"""
from pathlib import Path
p=Path(__file__).resolve().parent/'today_meta_v43_v52_v54.py'
outer=p.read_text(encoding='utf-8')
old_output="TODAY_META_V43_V52_1248_V54.json"
assert old_output in outer
outer=outer.replace(old_output,"TODAY_META_V43_V52_1249_FROZEN_V54.json")
needle="exec(compile(s,str(p),'exec'),globals(),globals())"
patch="""old_load=\"assert o[-1]['round']==1247 and [x['round'] for x in o]==list(range(1,1248))\"
assert old_load in s
s=s.replace(old_load,\"assert o[-1]['round']==1248 and [x['round'] for x in o]==list(range(1,1249))\")
old_meta=\"'target_round':1248,'data_cutoff':1247\"
assert old_meta in s
s=s.replace(old_meta,\"'target_round':1249,'data_cutoff':1248\")
assert \"SEED=202610301154\" in s
assert \"alpha=.05/4\" in s
exec(compile(s,str(p),'exec'),globals(),globals())"""
assert needle in outer
pathfix="""old_path="analysis/2026-10-30/TODAY_META_V43_V52_1249_FROZEN_V54.json"
assert old_path in s
s=s.replace(old_path,"analysis/2026-11-06/TODAY_META_V43_V52_1249_FROZEN_V54.json")
"""
patch=patch.replace(needle,pathfix+needle)
outer=outer.replace(needle,patch)
exec(compile(outer,str(p),'exec'),globals(),globals())
