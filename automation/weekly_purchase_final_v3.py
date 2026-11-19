#!/usr/bin/env python3
from __future__ import annotations

import csv, hashlib, importlib.util, json, math, random, statistics, sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'lotto_data.csv'
MODELS = ROOT / 'automation' / 'recovered_models_v2.py'
OUTROOT = ROOT / 'research' / 'weekly_purchase'
POLICY = 'WEEKLY_FIVE_TICKET_PORTFOLIO_V3_DIVERSIFIED_HOLDOUT'
KST = timezone(timedelta(hours=9))
BACKTEST_TARGETS = 200
SELECT_TARGETS = 100
RANDOM_BUNDLES_PER_TARGET = 100


def load_rows():
    rows=[]
    with DATA.open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            rows.append((int(r['round']), tuple(sorted(int(r[f'no{i}']) for i in range(1,7))), int(r['bonus'])))
    rounds=[r[0] for r in rows]
    assert rounds==list(range(1,max(rounds)+1)) and len(rounds)==len(set(rounds))
    return rows


def load_models():
    spec=importlib.util.spec_from_file_location('recovered_v2', MODELS)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def zscore(vals):
    xs=list(vals.values()); mu=statistics.mean(xs); sd=statistics.pstdev(xs) or 1.0
    return {k:(v-mu)/sd for k,v in vals.items()}


def support_scores(hist, model):
    draws=[x[1] for x in hist]
    pred=model.predict(draws)
    votes=Counter(n for ticket in pred.values() for n in ticket)
    f100=Counter(n for d in draws[-100:] for n in d)
    recent=zscore({n:f100[n] for n in range(1,46)})
    gaps={}
    for n in range(1,46):
        g=0
        for d in reversed(draws):
            if n in d: break
            g+=1
        gaps[n]=g
    zgap=zscore(gaps)
    # Model-vote consensus is primary; recent100 and gap only break/support ties.
    score={n:3.0*votes[n] + 0.35*recent[n] + 0.15*zgap[n] for n in range(1,46)}
    return score, pred


def history_structure(hist):
    recent=[x[1] for x in hist[-200:]] if len(hist)>=200 else [x[1] for x in hist]
    return statistics.mean(sum(d) for d in recent)


def structural_penalty(lines, mean_sum):
    p=0.0
    for line in lines:
        s=sorted(line); odd=sum(n%2 for n in s); low=sum(n<=22 for n in s)
        cons=sum(1 for a,b in zip(s,s[1:]) if b==a+1)
        p += ((sum(s)-mean_sum)/22.0)**2 + 0.85*(odd-3)**2 + 0.55*(low-3)**2 + 0.35*max(0,cons-2)**2
    return p


def partition30(numbers, priority, hist):
    ordered=sorted(numbers,key=lambda n:(-priority.get(n,0.0),n))
    lines=[[] for _ in range(5)]
    snake=[0,1,2,3,4,4,3,2,1,0]
    for i,n in enumerate(ordered): lines[snake[i%10]].append(n)
    mean_sum=history_structure(hist)
    best=[sorted(x) for x in lines]; bestp=structural_penalty(best,mean_sum)
    # Outcome-blind local balancing; the selected 30-number union never changes.
    for _ in range(40):
        improvement=None
        for a in range(5):
            for b in range(a+1,5):
                for ia in range(6):
                    for ib in range(6):
                        cand=[x[:] for x in best]
                        cand[a][ia],cand[b][ib]=cand[b][ib],cand[a][ia]
                        cand[a].sort(); cand[b].sort()
                        cp=structural_penalty(cand,mean_sum)
                        if cp < bestp-1e-12 and (improvement is None or cp<improvement[0]): improvement=(cp,cand)
        if improvement is None: break
        bestp,best=improvement
    assert len(set().union(*map(set,best)))==30
    assert all(len(x)==6 for x in best)
    return best,bestp


def model_guided(hist, model):
    score,pred=support_scores(hist,model)
    chosen=sorted(range(1,46),key=lambda n:(-score[n],n))[:30]
    lines,pen=partition30(chosen,score,hist)
    return lines,{'source':'MODEL_GUIDED_30_UNIQUE','model_predictions':{k:list(v) for k,v in pred.items()},'structure_penalty':pen}


def hash_diversified(hist):
    raw='|'.join(f"{r}:{','.join(map(str,nums))}:{b}" for r,nums,b in hist[-50:])
    seed=int(hashlib.sha256(raw.encode()).hexdigest()[:16],16)
    rng=random.Random(seed)
    chosen=rng.sample(range(1,46),30)
    priority={n:rng.random() for n in chosen}
    lines,pen=partition30(chosen,priority,hist)
    return lines,{'source':'HASH_DIVERSITY_BASELINE_30_UNIQUE','seed_sha256':hashlib.sha256(raw.encode()).hexdigest(),'structure_penalty':pen}


def metrics(tickets,actual):
    sets=list(map(set,tickets)); hits=[len(s & set(actual)) for s in sets]
    union=set().union(*sets)
    ovs=[len(sets[i]&sets[j]) for i in range(5) for j in range(i+1,5)]
    return {'max_hits':max(hits),'any_2plus':int(max(hits)>=2),'any_3plus':int(max(hits)>=3),'any_4plus':int(max(hits)>=4),'any_5plus':int(max(hits)>=5),'any_6':int(max(hits)>=6),'winning_union_coverage':len(union&set(actual)),'ticket_union_size':len(union),'mean_pair_overlap':statistics.mean(ovs),'max_pair_overlap':max(ovs)}


def random_independent(actual,rng):
    return metrics([sorted(rng.sample(range(1,46),6)) for _ in range(5)],actual)


def random_diversified(actual,rng):
    nums=rng.sample(range(1,46),30); rng.shuffle(nums)
    return metrics([sorted(nums[i*6:(i+1)*6]) for i in range(5)],actual)


def avg(arr,key): return statistics.mean(float(x[key]) for x in arr)

def summarize(arr):
    keys=['max_hits','any_2plus','any_3plus','any_4plus','any_5plus','any_6','winning_union_coverage','ticket_union_size','mean_pair_overlap','max_pair_overlap']
    return {k:avg(arr,k) for k in keys}


def backtest(rows,model):
    start=max(200,len(rows)-BACKTEST_TARGETS)
    rec=[]
    for i in range(start,len(rows)):
        hist=rows[:i]; actual=rows[i][1]; target=rows[i][0]
        mg,_=model_guided(hist,model); hb,_=hash_diversified(hist)
        rng=random.Random(930000+target)
        indep=[]; div=[]
        for _ in range(RANDOM_BUNDLES_PER_TARGET):
            indep.append(random_independent(actual,rng)); div.append(random_diversified(actual,rng))
        rec.append({'target':target,'model':metrics(mg,actual),'hash':metrics(hb,actual),'independent':summarize(indep),'diversified_random':summarize(div)})
    train=rec[:SELECT_TARGETS]; hold=rec[SELECT_TARGETS:]
    keys=['max_hits','any_2plus','any_3plus','winning_union_coverage']
    def policy_summary(part,name): return {k:statistics.mean(float(r[name][k]) for r in part) for k in keys}
    tr_m=policy_summary(train,'model'); tr_h=policy_summary(train,'hash')
    # Predeclared selection order: 2+ first, then 3+, max hits, union coverage.
    chooser=lambda s:(s['any_2plus'],s['any_3plus'],s['max_hits'],s['winning_union_coverage'])
    selected='model' if chooser(tr_m)>chooser(tr_h) else 'hash'
    def full_summary(part,name):
        if name in ('model','hash'):
            return summarize([r[name] for r in part])
        keys2=list(part[0][name]); return {k:statistics.mean(float(r[name][k]) for r in part) for k in keys2}
    hold_sel=full_summary(hold,selected); hold_ind=full_summary(hold,'independent'); hold_div=full_summary(hold,'diversified_random')
    promotion=(hold_sel['winning_union_coverage']>=hold_ind['winning_union_coverage'] and hold_sel['any_2plus']>=hold_ind['any_2plus'])
    # Predeclared fallback: if model selection fails the untouched holdout, use the
    # non-predictive 30-unique diversity baseline instead; this avoids promoting a
    # historically worse predictive rule.
    fallback_used=False
    if not promotion and selected=='model':
        selected='hash'; fallback_used=True
        hold_sel=full_summary(hold,'hash')
        promotion=(hold_sel['winning_union_coverage']>=hold_ind['winning_union_coverage'] and hold_sel['any_2plus']>=hold_ind['any_2plus'])
    return {'targets':len(rec),'selection_targets':len(train),'holdout_targets':len(hold),'random_bundles_per_target':RANDOM_BUNDLES_PER_TARGET,'selection_window':{'model':tr_m,'hash':tr_h},'selected_policy':selected,'fallback_used':fallback_used,'holdout_selected':hold_sel,'holdout_independent_random':hold_ind,'holdout_diversity_matched_random':hold_div,'promotion_gate_pass':promotion}


def validate(lines):
    flat=[n for x in lines for n in x]
    return len(lines)==5 and all(len(x)==6 and x==sorted(x) and len(set(x))==6 and all(isinstance(n,int) and 1<=n<=45 for n in x) for x in lines) and len(set(flat))==30


def protocol_gate(run_dir):
    a=json.loads((run_dir/'PROTOCOL_AUDIT.json').read_text(encoding='utf-8-sig')); v=json.loads((run_dir/'VERIFICATION.json').read_text(encoding='utf-8-sig'))
    assert a.get('protocol_status')=='FULL_COMPLETE' and v.get('protocol_status')=='FULL_COMPLETE'
    assert all(a.get('protocol_checks',{}).values()) and int(v.get('data_cutoff',-1))==1246 and int(v.get('successor_leakage_failures',1))==0
    return a,v


def main():
    date=sys.argv[1] if len(sys.argv)>1 else datetime.now(KST).date().isoformat()
    run_dir=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else max((ROOT/'analysis'/date).glob('MASTER_FULL_V5_*'),key=lambda p:p.stat().st_mtime)
    audit,ver=protocol_gate(run_dir); rows=load_rows(); model=load_models(); cutoff=rows[-1][0]; target=cutoff+1
    bt=backtest(rows,model)
    if not bt['promotion_gate_pass']: raise SystemExit('V3 promotion gate failed; do not output final numbers')
    if bt['selected_policy']=='model': lines,source=model_guided(rows,model)
    else: lines,source=hash_diversified(rows)
    assert validate(lines); pass1='PASS'; assert validate(lines); pass2='PASS'
    text='\n'.join(' '.join(map(str,x)) for x in lines); parsed=[[int(n) for n in r.split()] for r in text.splitlines()]; assert parsed==lines and validate(parsed)
    payload={'target_round':target,'created_kst':datetime.now(KST).isoformat(),'data_cutoff':cutoff,'data_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),'policy_version':POLICY,'classification':'PRIMARY_WEEKLY_PURCHASE_POLICY_PROTOCOL_FULL_V3','protocol_status':'FULL_COMPLETE','protocol_checks':audit['protocol_checks'],'protocol_run_dir':str(run_dir.relative_to(ROOT)),'selected_policy':bt['selected_policy'],'selection_source':source,'final_lines':lines,'portfolio':{'unique_number_coverage':30,'pairwise_overlaps':[0]*10,'mean_pair_overlap':0.0,'max_pair_overlap':0,'duplicate_numbers_across_lines':0},'walkforward_holdout':bt,'integrity':{'validator_1':pass1,'validator_2':pass2,'final_text_parse':'PASS','line_count':5,'numbers_per_line':6,'range_1_45':'PASS','within_line_unique':'PASS','duplicate_ticket':'PASS','cross_line_unique_30':'PASS'},'interpretation':'If the model-guided policy does not survive the untouched holdout against independent random bundles, the predeclared fallback is the 30-unique diversity baseline. Any advantage from that fallback is portfolio diversification, not evidence that particular numbers are more likely to be drawn.','freeze_payload_sha256':None}
    canon=json.dumps({k:v for k,v in payload.items() if k!='freeze_payload_sha256'},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode(); payload['freeze_payload_sha256']=hashlib.sha256(canon).hexdigest()
    outdir=OUTROOT/str(target); outdir.mkdir(parents=True,exist_ok=True); out=outdir/f"FINAL_FIVE_LINES_{target}_{date.replace('-','')}_PROTOCOL_FULL_V3.json"
    if out.exists(): raise SystemExit(f'write-once violation: {out}')
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    stored=json.loads(out.read_text(encoding='utf-8')); assert stored['final_lines']==lines and validate(stored['final_lines'])
    print(json.dumps({'status':'PASS','protocol_status':'FULL_COMPLETE','target':target,'cutoff':cutoff,'policy':POLICY,'selected_policy':bt['selected_policy'],'fallback_used':bt['fallback_used'],'promotion_gate_pass':bt['promotion_gate_pass'],'final_lines':lines,'portfolio_unique_coverage':30,'portfolio_max_overlap':0,'validator_1':'PASS','validator_2':'PASS','final_text_parse':'PASS','stored_vs_display':'PASS','holdout_selected':bt['holdout_selected'],'holdout_independent_random':bt['holdout_independent_random'],'holdout_diversity_matched_random':bt['holdout_diversity_matched_random'],'output':str(out)},ensure_ascii=False))

if __name__=='__main__': main()
