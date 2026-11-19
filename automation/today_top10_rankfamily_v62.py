#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_top6_rankfamily_v61.py'
s=p.read_text(encoding='utf-8')
s=s.replace('TODAY_TOP6_RANKFAMILY_1248_V61.json','TODAY_TOP10_RANKFAMILY_1248_V62.json')
s=s.replace('202610301761','202610301862')
s=s.replace('TOP6_RANKFAMILY_V61','TOP10_RANKFAMILY_V62')
s=s.replace('top6x2','top10x2')
s=s.replace('top6_template','top10_template')
s=s.replace('for r in range(6):g[r%5].append(r);g[(r+2)%5].append(r)','for r in range(10):g[r%5].append(r);g[(r+2)%5].append(r)')
s=s.replace('u=6','u=10')
s=s.replace('exact_null_top6x2','exact_null_top10x2')
s=s.replace('V61:', 'V62:')
s=s.replace('V61 finite', 'V62 finite')
s=s.replace('union24','union20')
exec(compile(s,str(p),'exec'),globals(),globals())
