#!/usr/bin/env python3
import os
from pathlib import Path
p=Path(__file__).resolve().parent/'today_overlap_adaptive_v59fix.py'
src=p.read_text(encoding='utf-8')
os.environ['OVERLAP_ADAPT_MODE']='any3guard'
src=src.replace('TODAY_OVERLAP_ADAPTIVE_{m}_1248_V59.json','TODAY_LONGWINDOW_OVERLAP_1248_V70.json')
src=src.replace("'OVERLAP_ADAPTIVE_V59'","'LONGWINDOW_OVERLAP_V70'")
src=src.replace('deque(maxlen=ROLL)', 'deque(maxlen=300)')
src=src.replace('list(hist[n])[-150:]', 'list(hist[n])[-300:]')
src=src.replace("'selection':'V59 {mode}: 12 preregistered H/M overlap policies with geometry-specific exact nulls; selected only at 50-target boundaries from prior <=150 outcomes.'","'selection':'V70: fixed any3guard selector over the preregistered V59 overlap family, locked every 50 targets using only prior <=300 outcomes to reduce block variance; exact null and strict gate unchanged.'")
exec(compile(src,str(p),'exec'),globals(),globals())
