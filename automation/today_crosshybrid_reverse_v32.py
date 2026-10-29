#!/usr/bin/env python3
from pathlib import Path

# V32 deliberately reuses the exact V31 implementation and changes only the
# predeclared direction of the cross-hybrid: old-feature slow core + multiwindow
# z-blend tail. The strict gate/comparator/bootstrapping remain identical.
p = Path(__file__).resolve().parent / 'today_crosshybrid_v31.py'
s = p.read_text(encoding='utf-8')
s = s.replace("TODAY_CROSSHYBRID_1248_V31.json", "TODAY_CROSSHYBRID_REVERSE_1248_V32.json")
s = s.replace("SEED=202610300930", "SEED=202610300945")
s = s.replace("'bv31'", "'bv32'").replace("'acv31'", "'acv32'").replace("'v12v31'", "'v12v32'").replace("'v18v31'", "'v18v32'")
s = s.replace(
"def rank_cross(mwslow,oldblend):\n core=sorted(range(1,46),key=lambda n:(-mwslow[n],n))[:6];tail=sorted((n for n in range(1,46) if n not in core),key=lambda n:(-oldblend[n],n))[:24];return core+tail",
"def rank_cross(oldslow,mwblend):\n core=sorted(range(1,46),key=lambda n:(-oldslow[n],n))[:6];tail=sorted((n for n in range(1,46) if n not in core),key=lambda n:(-mwblend[n],n))[:24];return core+tail")
s = s.replace(
"os={k:predict_old(v18,X,s['w']) for k,s in old.items()};oz={k:zscore(v) for k,v in os.items()};oldblend={n:sum(oz[k][n] for k in CFG)/len(CFG) for n in range(1,46)};ms={k:predict_mw(v18,X,E,s['w']) for k,s in mw.items()};r=rank_cross(ms['slow'],oldblend);",
"os={k:predict_old(v18,X,s['w']) for k,s in old.items()};ms={k:predict_mw(v18,X,E,s['w']) for k,s in mw.items()};mz={k:zscore(v) for k,v in ms.items()};mwblend={n:sum(mz[k][n] for k in CFG)/len(CFG) for n in range(1,46)};r=rank_cross(os['slow'],mwblend);")
s = s.replace("'mw_core':r[:6],'crosshybrid_top30':r", "'old_core':r[:6],'reverse_crosshybrid_top30':r")
s = s.replace("'V30_CORE_V28_TAIL_CROSSHYBRID_V31'", "'V28_CORE_V30_TAIL_CROSSHYBRID_V32'")
s = s.replace(
"'Top6 core from V30 multiwindow slow learner; ranks7-30 from original V26/V28 old-feature slow/medium/fast z-blend excluding core. Tail template selected only from prior rolling150 outcomes. Strict gate unchanged.'",
"'Top6 core from original V26/V28 old-feature slow learner; ranks7-30 from V30 multiwindow slow/medium/fast z-blend excluding core. Tail template selected only from prior rolling150 outcomes. Strict gate unchanged.'")
exec(compile(s, str(p), 'exec'), globals(), globals())
