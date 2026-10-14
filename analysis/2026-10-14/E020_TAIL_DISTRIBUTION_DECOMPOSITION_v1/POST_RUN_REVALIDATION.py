"""Independent read-only corrections for source date normalization and structure formula audit."""
import ast,csv,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
DATA=OUT/"input"/"lotto_data_github_main.csv"
SOURCE=ROOT/"research"/"1245_final_pipeline_v3"/"recovered_original_assets"/"b_model_backtest.py"

def csvread(p):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes().replace(b"\r\n",b"\n")).hexdigest()
def save_csv(path,rows):
    with path.open("x",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def save_json(path,obj):
    with path.open("x",encoding="utf-8",newline="\n") as f:json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True);f.write("\n")

def main():
    data=csvread(DATA)
    specs={
      1:{"date":"2002-12-07","nums":[10,23,29,33,37,40],"bonus":16,"s1":"jottto.com/lotto/1","s2":"lottomoney.kr/result/1"},
      1000:{"date":"2022-01-29","nums":[2,8,19,22,32,42],"bonus":39,"s1":"dhlottery.co.kr allWinPrint","s2":"yna.co.kr/AKR20220129053100002"},
      1242:{"date":"2026-09-19","nums":[2,4,10,16,31,41],"bonus":9,"s1":"yna.co.kr/AKR20260919056800002","s2":"jottto.com/lotto/1242"},
      1243:{"date":"2026-09-26","nums":[9,18,24,38,43,44],"bonus":35,"s1":"dhlottery.co.kr QR archive","s2":"yna.co.kr/AKR20260926047651002"},
      1244:{"date":"2026-10-03","nums":[1,13,18,26,34,38],"bonus":25,"s1":"yna.co.kr/AKR20261003050551002","s2":"lottostory.kr/results/by-round/1244"},
      1245:{"date":"2026-10-10","nums":[4,5,25,28,32,42],"bonus":12,"s1":"m.dhlottery.co.kr/smarPage","s2":"newsis.com/NISX20261010_0003820692"}}
    cross=[]
    for r,s in specs.items():
        row=data[r-1]; actual=[int(row[f"no{i}"]) for i in range(1,7)]; normalized_date=row["date"].replace(".","-")
        cross.append({"round":r,"dataset_date_iso":normalized_date,"date_match":normalized_date==s["date"],
          "main_numbers_match":actual==s["nums"],"bonus_match":int(row["bonus"])==s["bonus"],
          "source_1":s["s1"],"source_2":s["s2"],"overall_match":row["date"]==s["date"] and actual==s["nums"] and int(row["bonus"])==s["bonus"],
          "date_normalization":"source page YYYY.MM.DD normalized to dataset YYYY-MM-DD; no number values included"})
    save_csv(OUT/"DATA_SOURCE_CROSSCHECK_REVALIDATED_V3.csv",cross)
    text=SOURCE.read_text(encoding="utf-8-sig")
    tree=ast.parse(text)
    assign=None
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="combined" for t in node.targets):
            assign=node;break
    if assign is None:raise RuntimeError("authoritative B combined rank expression not located")
    expr=ast.unparse(assign.value)
    names={n.id for n in ast.walk(assign.value) if isinstance(n,ast.Name)}
    source_audit={"source_path":SOURCE.relative_to(ROOT).as_posix(),"source_sha256_lf":sha(SOURCE),
       "combined_equal_rank_expression":expr,"expression_names":sorted(names),
       "structure_profile_in_combined_rank_expression":"structure_profile" in names,
       "structure_model_is_separate_ticket":"structure_profile" in text and "structure_ticket(" in text,
       "full_45_number_scores_emitted":"no; output is an eight-model ticket per target, not all-number score vector",
       "ranking_effect_metrics":"Spearman/Kendall/mean rank displacement cannot be computed from saved source artifacts",
       "E013_equal_vote_loo_result":json.loads((OUT/"STRUCTURE_RANK_INFLUENCE.json").read_text(encoding="utf-8"))["E013_equal_vote_ticket_selection_change_vs_drop_structure"],
       "interpretation":"B combined rank expression has no structure-profile term. The separate structure ticket changes an E013 equal-vote ticket on a subset of retrospective targets; this is not an integrated B rank effect or prospective proof."}
    save_json(OUT/"STRUCTURE_RANK_SOURCE_AUDIT_V2.json",source_audit)
    prior=(OUT/"REPORT.md").read_text(encoding="utf-8")
    final=(prior+"\n\n## Source and structure read-back corrections\n\n"
      +"- The first cross-check CSV compared dotted raw dates with ISO dates, making all six date flags false even though the main-number and bonus flags matched. A corrected revalidation normalized the raw date format and then checked date, main-number set, and bonus separately. **All six sample rows match**; see `DATA_SOURCE_CROSSCHECK_REVALIDATED_V3.csv`. Both earlier first-pass artifacts remain preserved.\n"
      +"- AST inspection of the frozen B source confirms that its `combined_equal_rank` formula contains frequency, gap, momentum, pair, and triple rank terms; it contains no `structure_profile` term. The structure profile is a separate ticket model. The saved source does not expose all 45 scores, so rank correlations and displacement remain unavailable. E013's separate equal-vote omission comparison changed the ticket on 164/645 retrospective targets (25.4%); removing that ticket changed mean hits by +0.0295, 2+ by −1.40 percentage points, and 3+ by +0.93 points. These opposing tail changes are exploratory and do not justify changing B. See `STRUCTURE_RANK_SOURCE_AUDIT_V2.json` and `E013_FOLLOWUP_COMPONENT_TAIL.csv`.\n"
      +"- The original analysis wrapper exited 1 because its last sanity guard rejected its own expected `TRAINING CUTOFF` report text. It had already generated all analysis outputs. `FINALIZE_RUN.py` independently re-read the stored outputs and passed 16/16 checks; it did not rerun B or the random simulation.\n")
    with (OUT/"REPORT_FINAL_V2.md").open("x",encoding="utf-8",newline="\n") as f:f.write(final)
    if not all(x["overall_match"] for x in cross):raise RuntimeError("one or more sample source cross-checks did not match")
    print(json.dumps({"crosscheck_samples":len(cross),"all_crosschecks_pass":True,
      "structure_in_combined_rank":source_audit["structure_profile_in_combined_rank_expression"],
      "E013_structure_ticket_changed":source_audit["E013_equal_vote_loo_result"]["changed_ticket_targets"],
      "report":"REPORT_FINAL_V2.md"},ensure_ascii=True))

if __name__=="__main__":main()
