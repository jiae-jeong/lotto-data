#!/usr/bin/env python3
import os
from pathlib import Path
p=Path(__file__).resolve().parent/'today_blockrobust_hm_v52.py'
s=p.read_text(encoding='utf-8')
mode=os.environ.get('ROBUST_MODE','maxfirst')
tag=os.environ.get('ROBUST_TAG',mode)
s=s.replace("TODAY_BLOCKROBUST_HM_{tag}_1248_V52.json","TODAY_BLOCKROBUST_HM_{tag}_1248_V53.json")
s=s.replace("'BLOCKROBUST_HM_V52'","'BLOCKROBUST_HM_V53'")
s=s.replace("SEED=202610301052","SEED=202610301117")
needle="""     if mode=='positiveblocks':
      pos=lambda z:sum(x>0 for x in z)/len(z)
      return (min(pos(b2),pos(b3)),pos(b3),pos(b2),min(b3),min(b2),n=='H:rr')
     return (min(b3),min(b2),min(bm),statistics.mean(b3),statistics.mean(b2),n=='H:rr')"""
repl="""     if mode=='positiveblocks':
      pos=lambda z:sum(x>0 for x in z)/len(z)
      return (min(pos(b2),pos(b3)),pos(b3),pos(b2),min(b3),min(b2),n=='H:rr')
     if mode=='maxfirst':
      return (min(bm),statistics.mean(bm),min(b2),min(b3),statistics.mean(b2),n=='H:rr')
     if mode=='any2first':
      return (min(b2),statistics.mean(b2),min(b3),min(bm),statistics.mean(b3),n=='H:rr')
     if mode=='jointmean':
      means=[statistics.mean(bm),statistics.mean(b2),statistics.mean(b3)]
      floors=[min(bm),min(b2),min(b3)]
      return (min(means),sum(means),min(floors),sum(floors),n=='H:rr',n)
     if mode=='downside':
      floors=[min(bm),min(b2),min(b3)]
      pos=lambda z:sum(x>0 for x in z)/len(z)
      return (min(floors),min(pos(bm),pos(b2),pos(b3)),sum(floors),statistics.mean(b2)+statistics.mean(b3),n=='H:rr',n)
     return (min(b3),min(b2),min(bm),statistics.mean(b3),statistics.mean(b2),n=='H:rr')"""
assert needle in s
s=s.replace(needle,repl)
s=s.replace("'selection':'V52 {mode}: 8 predeclared H/M x partition policies; at each 50-target boundary choose using only prior 150 outcomes and prior 50-target block robustness. Gate unchanged.'","'selection':'V53 {mode}: four predeclared selector objectives over the same frozen 8 H/M partition policies; target choice uses only prior 150 outcomes in locked 50-target blocks. Gate unchanged.'")
exec(compile(s,str(p),'exec'),globals(),globals())
