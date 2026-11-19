#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_fixed_hybrid_allocator_v81.py'
s=p.read_text(encoding='utf-8')
s=s.replace('TODAY_FIXED_HYBRID_ALLOCATOR_1248_V81.json','TODAY_FIXED_HYBRID_ALLOCATOR_1248_V82.json')
s=s.replace('202610302481','202610302582')
s=s.replace("'FIXED_HYBRID_ALLOCATOR_V81'","'FIXED_HYBRID_ALLOCATOR_V82'")
s=s.replace("return [top6[0],top6[1],x2[2],x2[3],x2[4]]","return [top6[0],top6[1],top6[2],x2[3],x2[4]]")
s=s.replace("'selection':'V81 single fixed H:hybrid27 allocator; no policy selection on evaluation outcomes. Template combines two concentration lines and three coverage lines, fixed by outcome-blind maximum-union tie rule. Strict gate unchanged.'","'selection':'V82 complementary single fixed H:hybrid27 allocator; no policy selection on evaluation outcomes. Template combines three concentration lines and two coverage lines, the preregistered complement of V81. Strict gate unchanged.'")
s=s.replace("'geometry':'V81 fixed hybrid27: union27 with three duplicated rank positions; exact matched-label null computed for the identical overlap mask.'","'geometry':'V82 fixed hybrid27 complement: union27 with three duplicated rank positions; exact matched-label null computed for the identical overlap mask.'")
exec(compile(s,str(p),'exec'),globals(),globals())
