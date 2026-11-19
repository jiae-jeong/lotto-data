#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_twostage_overlap_v69.py'
src=p.read_text(encoding='utf-8')
needle="assert oldscore in s;s=s.replace(oldscore,newscore)\ns=s.replace(\"'union_size':30};break\",\"'union_size':len(set().union(*map(set,L)))};break\")"
repl="assert oldscore in s;s=s.replace(oldscore,newscore)\ns=s.replace(\"float(NULL[k])\",\"float(NULLS[n][k])\")\ns=s.replace(\"'union_size':30};break\",\"'union_size':len(set().union(*map(set,L)))};break\")"
assert needle in src
src=src.replace(needle,repl)
exec(compile(src,str(p),'exec'),globals(),globals())
