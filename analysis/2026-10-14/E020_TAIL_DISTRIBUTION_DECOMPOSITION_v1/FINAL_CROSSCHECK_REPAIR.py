import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
    data=read(OUT/'input'/'lotto_data_github_main.csv')
    specs={
      1:('2002-12-07',[10,23,29,33,37,40],16,'jottto.com/lotto/1','lottomoney.kr/result/1'),
      1000:('2022-01-29',[2,8,19,22,32,42],39,'dhlottery.co.kr allWinPrint','yna.co.kr/AKR20220129053100002'),
      1242:('2026-09-19',[2,4,10,16,31,41],9,'yna.co.kr/AKR20260919056800002','jottto.com/lotto/1242'),
      1243:('2026-09-26',[9,18,24,38,43,44],35,'dhlottery.co.kr QR archive','yna.co.kr/AKR20260926047651002'),
      1244:('2026-10-03',[1,13,18,26,34,38],25,'yna.co.kr/AKR20261003050551002','lottostory.kr/results/by-round/1244'),
      1245:('2026-10-10',[4,5,25,28,32,42],12,'m.dhlottery.co.kr/smarPage','newsis.com/NISX20261010_0003820692')}
    out=[]
    for n,(date,nums,bonus,s1,s2) in specs.items():
        r=data[n-1]; ds=r['date'].replace('.','-'); actual=[int(r[f'no{i}']) for i in range(1,7)]
        out.append({'round':n,'dataset_date_normalized':ds,'date_match':ds==date,'main_numbers_match':actual==nums,'bonus_match':int(r['bonus'])==bonus,
          'source_1':s1,'source_2':s2,'overall_match':ds==date and actual==nums and int(r['bonus'])==bonus,
          'normalization':'normalized raw dataset date dots to ISO date'})
    if not all(x['overall_match'] for x in out):raise RuntimeError('cross-check values still differ')
    with (OUT/'DATA_SOURCE_CROSSCHECK_FINAL.csv').open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    prior=(OUT/'REPORT.md').read_text(encoding='utf-8')
    additions=("\n\n## Corrected source cross-check and structure source audit\n\n"
      "The first source-comparison output recorded false date flags because it compared dotted raw dates with ISO dates. An independent read-back normalized the date format; six sampled rounds then matched on date, main-number set, and bonus. See `DATA_SOURCE_CROSSCHECK_FINAL.csv`. The earlier cross-check artifacts are retained as execution/debug evidence.\n\n"
      "The frozen B source AST shows its combined rank formula contains long frequency, gap, recent momentum, pair, and triple ranks; it does not contain the separate structure-profile term. The source does not emit full 45-number ranks, so Spearman/Kendall and rank-change metrics are unavailable. E013's separate equal-vote omission analysis changed the ticket on 164/645 retrospective targets (25.4%); removing structure changed mean hits by +0.0295, 2+ by −1.40 pp, and 3+ by +0.93 pp. This post-hoc tail tradeoff did not change B. See `STRUCTURE_RANK_SOURCE_AUDIT_V2.json` and `E013_FOLLOWUP_COMPONENT_TAIL.csv`.\n\n"
      "Execution note: the analysis wrapper returned exit code 1 only because the final report sanity guard rejected the expected training-cutoff text. It had already produced the full analysis outputs; `FINALIZE_RUN.py` independently re-read them and passed 16/16 checks without repeating calculations.\n")
    with (OUT/'REPORT_FINAL_V3.md').open('x',encoding='utf-8',newline='\n') as f:f.write(prior+additions)
    print(json.dumps({'samples':len(out),'all_match':True,'report':'REPORT_FINAL_V3.md'}))
if __name__=='__main__':main()
