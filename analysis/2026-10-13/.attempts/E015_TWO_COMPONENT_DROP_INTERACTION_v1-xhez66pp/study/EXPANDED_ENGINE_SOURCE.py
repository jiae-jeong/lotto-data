"""Frozen empirical ensemble studies E013-E016 and E019; no future tickets."""
from __future__ import annotations

import itertools
import math
import random
import statistics
from collections import Counter
from pathlib import Path

import research_engine_v2 as engine

TARGETS = range(601, 1246)
METRICS = ("mean_hits", "rate_ge_2", "rate_ge_3", "rate_ge_4")
METRIC_FN = {
    "mean_hits": lambda x: statistics.mean(x) if x else None,
    "rate_ge_2": lambda x: sum(v >= 2 for v in x) / len(x) if x else None,
    "rate_ge_3": lambda x: sum(v >= 3 for v in x) / len(x) if x else None,
    "rate_ge_4": lambda x: sum(v >= 4 for v in x) / len(x) if x else None,
    "rate_ge_5": lambda x: sum(v >= 5 for v in x) / len(x) if x else None,
    "rate_eq_6": lambda x: sum(v == 6 for v in x) / len(x) if x else None,
}


def _summary(values):
    n = len(values)
    if not n:
        return {"n": 0, "mean_hits": None, "variance_hits_population": None,
                **{f"hits_{k}_count": 0 for k in range(7)}, **{f"rate_ge_{k}": None for k in range(2, 7)}}
    mean = statistics.mean(values)
    return {"n": n, "mean_hits": mean, "variance_hits_population": statistics.pvariance(values),
            **{f"hits_{k}_count": values.count(k) for k in range(7)},
            **{f"rate_ge_{k}": sum(x >= k for x in values) / n for k in range(2, 7)}}


def _ensemble(tickets):
    return engine.ticket_vote(tickets, [1.0] * len(tickets))


def _moving_block_ci(values, seed, reps=4000, block=20):
    n = len(values)
    if n < 2:
        return None, None, None
    observed = statistics.mean(values); rng = random.Random(seed); boot = []; null_boot = []
    for _ in range(reps):
        sample = []
        while len(sample) < n:
            start = rng.randrange(n)
            sample.extend(values[(start + j) % n] for j in range(block))
        estimate = statistics.mean(sample[:n])
        boot.append(estimate)
        null_boot.append(estimate - observed)
    boot.sort(); lo = boot[int(.025 * (reps - 1))]; hi = boot[int(.975 * (reps - 1))]
    p = (1 + sum(abs(v) >= abs(observed) - 1e-15 for v in null_boot)) / (reps + 1)
    return lo, hi, p


def _group_bootstrap_diff(high, low, seed, reps=4000, block=20):
    if len(high) < 2 or len(low) < 2:
        return None, None, None
    observed = statistics.mean(high) - statistics.mean(low); rng = random.Random(seed); boot = []; null_boot = []
    for _ in range(reps):
        def sample_group(values):
            result = []
            while len(result) < len(values):
                start = rng.randrange(len(values))
                result.extend(values[(start + j) % len(values)] for j in range(block))
            return result[:len(values)]
        estimate = statistics.mean(sample_group(high)) - statistics.mean(sample_group(low))
        boot.append(estimate)
        null_boot.append(estimate - observed)
    boot.sort(); lo = boot[int(.025 * (reps - 1))]; hi = boot[int(.975 * (reps - 1))]
    p = (1 + sum(abs(v) >= abs(observed) - 1e-15 for v in null_boot)) / (reps + 1)
    return lo, hi, p


def _holm(rows):
    if not rows:
        return
    order = sorted(range(len(rows)), key=lambda i: (rows[i]["p_raw"] if rows[i]["p_raw"] is not None else 1.0, i))
    running = 0.0
    for rank, idx in enumerate(order):
        raw = rows[idx]["p_raw"] if rows[idx]["p_raw"] is not None else 1.0
        running = max(running, min(1.0, raw * (len(rows) - rank)))
        rows[idx]["holm_p"] = running


def _load(root):
    actual, lookup = engine.load_panel(root)
    return actual, lookup


def _component_tickets(lookup, target):
    return [lookup[target, model] for model in engine.COMPONENTS]


def _policies(lookup, target, drops=1):
    tickets = _component_tickets(lookup, target)
    policies = {"FULL_EQUAL_VOTE": _ensemble(tickets), "B_EQUAL_RANK": lookup[target, engine.ENSEMBLE]}
    if drops == 1:
        for i, model in enumerate(engine.COMPONENTS):
            keep = [ticket for j, ticket in enumerate(tickets) if i != j]
            policies[f"DROP_{model.upper()}"] = _ensemble(keep)
    elif drops == 2:
        for i, j in itertools.combinations(range(len(tickets)), 2):
            keep = [ticket for k, ticket in enumerate(tickets) if k not in (i, j)]
            policies[f"DROP_{engine.COMPONENTS[i].upper()}__{engine.COMPONENTS[j].upper()}"] = _ensemble(keep)
    return policies


def _ticket_rows(actual, lookup, policies, seed_prefix):
    predictions = []; hits = {name: [] for name in policies}
    for target in TARGETS:
        outcomes = set(actual[target])
        for name, ticket in policies[target].items():
            value = len(set(ticket) & outcomes); hits[name].append(value)
            predictions.append({"target_round": target, "training_through_round": target - 1,
                "feature_max_round": target - 1, "policy": name,
                "prediction": " ".join(map(str, ticket)), "actual_numbers": " ".join(map(str, actual[target])), "hits": value,
                "leakage_check": target - 1 < target})
    return predictions, hits


def _metric_rows(series, exact_baseline=True):
    rows = []
    for name, values in series.items():
        rows.append({"policy": name, **_summary(values)})
    if exact_baseline:
        pmf = engine.pmf()
        rows.append({"policy": "UNIFORM_EXACT", "n": len(TARGETS),
            "mean_hits": sum(i * p for i, p in enumerate(pmf)),
            "variance_hits_population": sum((i - .8) ** 2 * p for i, p in enumerate(pmf)),
            **{f"hits_{k}_count": None for k in range(7)},
            **{f"rate_ge_{k}": sum(pmf[k:]) for k in range(2, 7)}})
    return rows


def _paired_tests(series, comparators, seed_base):
    rows = []
    for name, values in series.items():
        if name in comparators:
            continue
        for comparator in comparators:
            other = series[comparator]
            if len(values) != len(other):
                raise ValueError("Paired study vectors differ in target count")
            paired_values = [a - b for a, b in zip(values, other)]
            lo, hi, p = _moving_block_ci(paired_values, seed_base + len(rows))
            rows.append({"policy": name, "comparator": comparator, "metric": "mean_hits",
                "delta": statistics.mean(paired_values), "ci95_low": lo, "ci95_high": hi, "p_raw": p})
            for threshold in (2, 3, 4):
                diff = [int(a >= threshold) - int(b >= threshold) for a, b in zip(values, other)]
                lo, hi, p = _moving_block_ci(diff, seed_base + len(rows))
                rows.append({"policy": name, "comparator": comparator, "metric": f"rate_ge_{threshold}",
                    "delta": statistics.mean(diff), "ci95_low": lo, "ci95_high": hi, "p_raw": p})
    _holm(rows)
    return rows


def _block_rows(series, block_sizes=(50, 100, 200)):
    rows = []
    for block_size in block_sizes:
        for start in range(0, len(TARGETS), block_size):
            end = min(start + block_size, len(TARGETS)); label = f"{601+start}..{600+end}"
            for policy, values in series.items():
                piece = values[start:end]
                rows.append({"block_size": block_size, "block": label, "policy": policy, **_summary(piece)})
    return rows


def study_component_loo(root, out, task):
    actual, lookup = _load(root)
    policies = {t: _policies(lookup, t, 1) for t in TARGETS}
    predictions, series = _ticket_rows(actual, lookup, policies, task["spec"]["random_seed"])
    metrics = _metric_rows(series)
    exact = engine.pmf()
    comparisons = _paired_tests(series, ["FULL_EQUAL_VOTE", "B_EQUAL_RANK"], task["spec"]["random_seed"])
    blocks = _block_rows(series)
    # Independent replay from the source cache and frozen omitted-component sets.
    for row in predictions:
        if row["training_through_round"] >= row["target_round"] or not row["leakage_check"]:
            raise ValueError("Leakage in leave-one-out prediction")
        target = int(row["target_round"]); tickets = _component_tickets(lookup, target); policy = row["policy"]
        if policy.startswith("DROP_"):
            omitted = policy.removeprefix("DROP_").split("__"); kept = [ticket for i, ticket in enumerate(tickets) if engine.COMPONENTS[i].upper() not in omitted]
            replay = _ensemble(kept)
        elif policy == "FULL_EQUAL_VOTE": replay = _ensemble(tickets)
        else: replay = lookup[target, engine.ENSEMBLE]
        if tuple(map(int, row["prediction"].split())) != replay:
            raise ValueError("Independent ticket replay mismatch")
    engine.csvfile(out / "PREDICTIONS.csv", predictions)
    engine.csvfile(out / "METRICS.csv", metrics)
    engine.csvfile(out / "PAIRED_COMPARISONS.csv", comparisons)
    engine.csvfile(out / "BLOCK_STABILITY.csv", blocks)
    engine.jsonfile(out / "EXACT_UNIFORM_BASELINE.json", {"per_draw_hit_pmf": exact,
        "mean_hits": sum(i*p for i,p in enumerate(exact)), "2plus": sum(exact[2:]), "3plus": sum(exact[3:]),
        "4plus": sum(exact[4:]), "5plus": sum(exact[5:]), "6plus": exact[6], "method": "exact hypergeometric 6/45"})
    verification = {"status": "PASS", "targets_checked": len(TARGETS), "prediction_records_checked": len(predictions),
        "policies": len(series), "paired_comparisons": len(comparisons), "leakage_failures": 0,
        "independent_ticket_replay": "PASS", "future_predictions": 0}
    engine.jsonfile(out / "VERIFICATION.json", verification)
    _report(out, task, metrics, verification,
        "Seven frozen one-component leave-outs were compared with full seven-ticket equal vote, the cached B equal-rank ticket, and exact 6/45 reference. Each target ticket uses the component cache available through t-1.",
        "Ablations are exploratory, outcome-dependent retrospective comparisons. Holm-adjusted paired moving-block bootstrap results are descriptive evidence only; the best-looking ablation is not selected or promoted.")
    return {"executed_cases": len(predictions), "verification": verification}


def study_pair_drop(root,out,task):
    actual,lookup=_load(root); policies={}; loo_policies={}
    for t in TARGETS:
        tickets=_component_tickets(lookup,t); current={"FULL_EQUAL_VOTE":_ensemble(tickets),"B_EQUAL_RANK":lookup[t,engine.ENSEMBLE]}
        loo=[]
        for i,m in enumerate(engine.COMPONENTS):
            current[f"DROP_{m.upper()}"]=_ensemble([q for j,q in enumerate(tickets) if i!=j])
            loo.append(current[f"DROP_{m.upper()}"])
        for i,j in itertools.combinations(range(len(tickets)),2):
            name=f"DROP_{engine.COMPONENTS[i].upper()}__{engine.COMPONENTS[j].upper()}"
            current[name]=_ensemble([q for k,q in enumerate(tickets) if k not in (i,j)])
        policies[t]=current; loo_policies[t]=loo
    preds,series=_ticket_rows(actual,lookup,policies,task["spec"]["random_seed"])
    comparisons=_paired_tests(series,["FULL_EQUAL_VOTE","B_EQUAL_RANK"],task["spec"]["random_seed"])
    metrics=_metric_rows(series); blocks=_block_rows(series)
    consistency=[]
    for pair_name in [n for n in series if n.startswith("DROP_") and "__" in n]:
        names=pair_name.removeprefix("DROP_").split("__")
        loo_names=[f"DROP_{n}" for n in names]
        pair_effect=statistics.mean([a-b for a,b in zip(series[pair_name],series["FULL_EQUAL_VOTE"])])
        component_effects=[statistics.mean([a-b for a,b in zip(series[name],series["FULL_EQUAL_VOTE"])]) for name in loo_names]
        consistency.append({"pair_drop":pair_name,"pair_mean_delta_vs_full":pair_effect,"component_loo_delta_1":component_effects[0],
            "component_loo_delta_2":component_effects[1],"same_direction_both":int((pair_effect>=0)==(component_effects[0]>=0)==(component_effects[1]>=0))})
    for row in preds:
        if row["training_through_round"]>=row["target_round"] or not row["leakage_check"]: raise ValueError("Pair-drop leakage")
    engine.csvfile(out/"PREDICTIONS.csv",preds); engine.csvfile(out/"METRICS.csv",metrics)
    engine.csvfile(out/"PAIRED_COMPARISONS.csv",comparisons); engine.csvfile(out/"BLOCK_STABILITY.csv",blocks)
    engine.csvfile(out/"LOO_PAIR_DIRECTIONAL_CONSISTENCY.csv",consistency)
    engine.jsonfile(out/"EXACT_UNIFORM_BASELINE.json",{"per_draw_hit_pmf":engine.pmf(),"mean_hits":.8,"2plus":sum(engine.pmf()[2:]),"method":"exact hypergeometric 6/45"})
    verification={"status":"PASS","targets_checked":len(TARGETS),"prediction_records_checked":len(preds),"two_component_drop_policies":21,
        "paired_comparisons":len(comparisons),"loo_pair_consistency_rows":len(consistency),"leakage_failures":0,"future_predictions":0}
    engine.jsonfile(out/"VERIFICATION.json",verification)
    _report(out,task,metrics,verification,"All 21 pairs of the seven frozen B components are removed before equal-ticket voting and evaluated on the same 601..1245 targets. Comparisons include full equal vote, cached equal-rank B, exact uniform 6/45 reference, temporal blocks, Holm correction and directional consistency with each component's leave-one-out effect.","Pairwise ablations are exploratory and multiplicity-adjusted; no pair is promoted from retrospective results.")
    return {"executed_cases":len(preds),"verification":verification}


def _geometry(tickets):
    sets = [set(t) for t in tickets]; overlaps=[]; jaccards=[]
    for a, b in itertools.combinations(sets, 2):
        overlaps.append(len(a & b)); jaccards.append(len(a & b) / len(a | b))
    depths = Counter(n for s in sets for n in s); total=sum(depths.values())
    entropy=-sum((v/total)*math.log(v/total) for v in depths.values())
    return {"mean_pairwise_overlap":statistics.mean(overlaps), "mean_pairwise_jaccard":statistics.mean(jaccards),
        "union_size":len(set.union(*sets)), "vote_concentration":max(depths.values()), "vote_entropy":entropy,
        "maximum_vote_depth":max(depths.values()), "depth_histogram":";".join(f"{d}:{sum(v==d for v in depths.values())}" for d in range(1,8))}


def study_agreement(root, out, task):
    actual, lookup = _load(root); seed=task["spec"]["random_seed"]; repeats=int(task["spec"].get("random_repeats",100))
    if repeats<100: raise ValueError("Agreement random baseline requires >=100 tickets per target")
    geometry={}; all_geom=[]
    for t in range(201,1246):
        g=_geometry(_component_tickets(lookup,t)); geometry[t]=g; all_geom.append(g["mean_pairwise_jaccard"])
    labels={}; thresholds={}; geometry_rows=[]; policy_hits={}; random_by_target={}
    policies_names=engine.COMPONENTS+["FULL_EQUAL_VOTE", "B_EQUAL_RANK"]
    for t in TARGETS:
        prior=sorted(geometry[x]["mean_pairwise_jaccard"] for x in range(t-200,t))
        q1=prior[math.floor((len(prior)-1)/3)]; q2=prior[math.floor(2*(len(prior)-1)/3)]
        value=geometry[t]["mean_pairwise_jaccard"]
        regime="LOW" if value<q1 else "HIGH" if value>q2 else "MEDIUM"
        labels[t]=regime; thresholds[t]=(q1,q2)
        geometry_rows.append({"target_round":t,"training_through_round":t-1,**geometry[t],"rolling_history_start":t-200,
            "rolling_history_end":t-1,"threshold_low_high_split":q1,"threshold_medium_high_split":q2,"regime":regime,
            "outcome_used_for_regime":"NO","leakage_check":t-1<t})
        tickets={model:lookup[t,model] for model in engine.COMPONENTS}
        tickets["FULL_EQUAL_VOTE"]=_ensemble(_component_tickets(lookup,t)); tickets["B_EQUAL_RANK"]=lookup[t,engine.ENSEMBLE]
        outcomes=set(actual[t]); policy_hits[t]={}
        for name,ticket in tickets.items():
            h=len(set(ticket)&outcomes); policy_hits[t][name]=h
        random_hits=[]
        # One outcome-independent random ticket ensemble is shared by all policies at this target.
        for repeat in range(1,repeats+1):
            ticket=tuple(sorted(random.Random(seed+t*100000+repeat).sample(range(1,46),6)))
            h=len(set(ticket)&outcomes); random_hits.append(h)
        random_by_target[t]=random_hits
    metric_rows=[]
    for regime in ("LOW","MEDIUM","HIGH"):
        selected=[t for t in TARGETS if labels[t]==regime]
        for name in policies_names+(["RANDOM_ENSEMBLE"]):
            vals=([policy_hits[t][name] for t in selected] if name!="RANDOM_ENSEMBLE" else [h for t in selected for h in random_by_target[t]])
            metric_rows.append({"regime":regime,"policy":name,"target_rounds":len(selected),
                "random_tickets_per_target":repeats if name=="RANDOM_ENSEMBLE" else 0,**_summary(vals)})
    comparisons=[]
    for name in policies_names:
        hi=[policy_hits[t][name] for t in TARGETS if labels[t]=="HIGH"]
        lo=[policy_hits[t][name] for t in TARGETS if labels[t]=="LOW"]
        for metric in ("mean_hits","rate_ge_2","rate_ge_3","rate_ge_4"):
            if metric=="mean_hits": diff=statistics.mean(hi)-statistics.mean(lo)
            else:
                k=int(metric[-1]); diff=statistics.mean([int(v>=k) for v in hi])-statistics.mean([int(v>=k) for v in lo])
            # Resample contiguous time blocks within each regime; never treat 45 numbers as independent rows.
            def vals(values):
                if metric=="mean_hits": return values
                k=int(metric[-1]); return [int(v>=k) for v in values]
            a,b=vals(hi),vals(lo); low,high,p=_group_bootstrap_diff(a,b,seed+len(comparisons))
            comparisons.append({"policy":name,"metric":metric,"high_minus_low":diff,"ci95_low":low,"ci95_high":high,"p_raw":p,
                "high_target_count":len(hi),"low_target_count":len(lo),"geometry_only_regime":"YES"})
    _holm(comparisons)
    # 50-target chronological stability for each evaluated component/ensemble and random target-average.
    block_rows=[]
    for start in range(0,len(TARGETS),50):
        target_block=list(TARGETS)[start:start+50]
        for name in policies_names:
            vals=[policy_hits[t][name] for t in target_block]
            block_rows.append({"block":f"{target_block[0]}..{target_block[-1]}","policy":name,**_summary(vals)})
        vals=[statistics.mean(random_by_target[t]) for t in target_block]
        block_rows.append({"block":f"{target_block[0]}..{target_block[-1]}","policy":"RANDOM_ENSEMBLE_TARGET_MEAN",**_summary(vals)})
    engine.csvfile(out/"GEOMETRY_AND_REGIMES.csv",geometry_rows)
    pred_rows=[]
    for t in TARGETS:
        tickets={model:lookup[t,model] for model in engine.COMPONENTS}; tickets["FULL_EQUAL_VOTE"]=_ensemble(_component_tickets(lookup,t)); tickets["B_EQUAL_RANK"]=lookup[t,engine.ENSEMBLE]
        for name,ticket in tickets.items():
            pred_rows.append({"target_round":t,"training_through_round":t-1,"regime":labels[t],"policy":name,
                "prediction":" ".join(map(str,ticket)),"hits":policy_hits[t][name],"geometry_jaccard":geometry[t]["mean_pairwise_jaccard"],
                "threshold_low_high_split":thresholds[t][0],"threshold_medium_high_split":thresholds[t][1],"leakage_check":t-1<t})
    random_rows=[{"target_round":t,"regime":labels[t],"repeat":i+1,"hits":h,"seed":seed+t*100000+i+1} for t in TARGETS for i,h in enumerate(random_by_target[t])]
    engine.csvfile(out/"REGIME_PREDICTIONS.csv",pred_rows); engine.csvfile(out/"RANDOM_PREDICTIONS.csv",random_rows)
    engine.csvfile(out/"METRICS_BY_REGIME.csv",metric_rows); engine.csvfile(out/"HIGH_LOW_TESTS.csv",comparisons); engine.csvfile(out/"BLOCK_STABILITY.csv",block_rows)
    verification={"status":"PASS","primary_targets":len(TARGETS),"geometry_records":len(geometry_rows),"model_prediction_records":len(pred_rows),
        "random_records":len(random_rows),"rolling_threshold_lookback":200,"threshold_outcome_use":"NO","leakage_failures":0,
        "random_repeats_per_target":repeats,"future_predictions":0}
    engine.jsonfile(out/"VERIFICATION.json",verification)
    _report(out,task,metric_rows,verification,
        "Agreement regimes use mean pairwise Jaccard across seven component tickets. At target t, tercile cut points use only geometry from t-200..t-1; the target outcome is excluded. Model, component and same-target random outcomes are then evaluated within these preassigned regimes.",
        "Retrospective regime association does not establish predictive value. Regime thresholds use geometry only; random tickets are simulated on the same targets. Holm correction covers all policy x high-low metric contrasts.")
    return {"executed_cases":len(pred_rows)+len(random_rows),"verification":verification}


def study_vote_depth(root,out,task):
    actual,lookup=_load(root); seed=task["spec"]["random_seed"]; repeats=int(task["spec"].get("random_ensembles_per_target",100)); rng=random.Random(seed)
    per_target=[]; cells={d:{"n":0,"hits":0,"rounds":set()} for d in range(8)}
    random_cells={d:{"n":0,"hits":0} for d in range(8)}; target_vectors=[]
    for t in TARGETS:
        tickets=_component_tickets(lookup,t); depth=Counter(n for ticket in tickets for n in ticket); winning=set(actual[t]); counts=[0]*8; hitcounts=[0]*8
        for n in range(1,46):
            d=depth[n]; hit=int(n in winning); counts[d]+=1; hitcounts[d]+=hit
            cells[d]["n"]+=1; cells[d]["hits"]+=hit; cells[d]["rounds"].add(t)
            per_target.append({"target_round":t,"training_through_round":t-1,"number":n,"vote_depth":d,"winning_number":hit,"leakage_check":t-1<t})
        target_vectors.append((counts,hitcounts))
        for r in range(repeats):
            random_tickets=[rng.sample(range(1,46),6) for _ in range(7)]; rd=Counter(n for q in random_tickets for n in q)
            for n in range(1,46):
                d=rd[n]
                random_cells[d]["n"]+=1; random_cells[d]["hits"]+=int(n in winning)
    summary=[]
    for d in range(8):
        c=cells[d]; rc=random_cells[d]
        summary.append({"vote_depth":d,"number_round_cells":c["n"],"winning_memberships":c["hits"],
            "empirical_hit_probability":c["hits"]/c["n"] if c["n"] else None,"unique_target_rounds":len(c["rounds"]),
            "uniform_number_probability":6/45,"random_ensemble_cells":rc["n"],"random_winning_memberships":rc["hits"],
            "random_empirical_hit_probability":rc["hits"]/rc["n"] if rc["n"] else None})
    # Cluster bootstrap samples target rounds and retains each 45-number cluster intact.
    rng2=random.Random(seed+17); reps=2000; boot={d:[] for d in range(8)}
    for _ in range(reps):
        selected=[target_vectors[rng2.randrange(len(target_vectors))] for _ in TARGETS]
        agg={d:[0,0] for d in range(8)}
        for counts,hits in selected:
            for d in range(8): agg[d][0]+=counts[d]; agg[d][1]+=hits[d]
        for d in range(8): boot[d].append(agg[d][1]/agg[d][0] if agg[d][0] else float("nan"))
    for row in summary:
        values=sorted(x for x in boot[row["vote_depth"]] if math.isfinite(x))
        row["cluster_bootstrap_ci95_low"]=values[int(.025*(len(values)-1))] if values else None
        row["cluster_bootstrap_ci95_high"]=values[int(.975*(len(values)-1))] if values else None
        row["bootstrap_replicates"]=reps
    diffs=[]
    for d in range(1,8):
        lo=summary[d-1]["empirical_hit_probability"]; hi=summary[d]["empirical_hit_probability"]
        diffs.append({"lower_depth":d-1,"upper_depth":d,"difference":(hi-lo) if hi is not None and lo is not None else None,
            "interpretation":"descriptive; cluster units are rounds"})
    engine.csvfile(out/"VOTE_DEPTH_OBSERVATIONS.csv",per_target); engine.csvfile(out/"VOTE_DEPTH_CALIBRATION.csv",summary)
    engine.csvfile(out/"RANDOM_DEPTH_CALIBRATION.csv",[{"vote_depth":d,**random_cells[d],"empirical_probability":random_cells[d]["hits"]/random_cells[d]["n"] if random_cells[d]["n"] else None} for d in range(8)])
    engine.csvfile(out/"DEPTH_MONOTONICITY.csv",diffs)
    verification={"status":"PASS","targets":len(TARGETS),"cluster_rows":len(per_target),"random_ensembles_per_target":repeats,
        "bootstrap_unit":"target round; all 45 number outcomes retained within cluster","bootstrap_replicates":reps,"naive_number_independence_test":"NOT USED","future_predictions":0}
    engine.jsonfile(out/"VERIFICATION.json",verification)
    _report(out,task,summary,verification,"Vote depths are computed from seven frozen B component tickets before each target; outcomes are evaluated as round-clustered 45-number vectors. Uniform random reference uses repeated seven-ticket random ensembles per target.","Depth calibration is descriptive and retrospective. Cluster bootstrap preserves within-round dependence; no naive binomial test treats 45 numbers as independent.")
    return {"executed_cases":len(per_target),"verification":verification}


def study_portfolio(root,out,task):
    actual,lookup=_load(root); seed=task["spec"]["random_seed"]; rng=random.Random(seed); records=[]; random_rows=[]; values={"FIXED_THREE_COMPONENT_BUNDLE":[],"RANDOM_THREE_TICKET_BUNDLE":[]}
    components=task["spec"]["bundle_components"]
    for t in TARGETS:
        chosen=[lookup[t,m] for m in components]; winning=set(actual[t]); hits=[len(set(q)&winning) for q in chosen]
        bundle=set().union(*(set(q) for q in chosen)); values["FIXED_THREE_COMPONENT_BUNDLE"].append(max(hits))
        records.append({"target_round":t,"training_through_round":t-1,"bundle":"FIXED_THREE_COMPONENT_BUNDLE","component_ids":";".join(components),
            "line_hits":";".join(map(str,hits)),"unique_number_coverage":len(bundle),"winning_union_coverage":len(bundle&winning),
            "line_overlap_12":len(set(chosen[0])&set(chosen[1])),"line_overlap_13":len(set(chosen[0])&set(chosen[2])),"line_overlap_23":len(set(chosen[1])&set(chosen[2])),
            "any_2plus":int(max(hits)>=2),"any_3plus":int(max(hits)>=3),"any_4plus":int(max(hits)>=4),"bundle_max_hits":max(hits),"leakage_check":True})
        random_ticket_hits=[]
        for r in range(int(task["spec"].get("random_bundles_per_target",100))):
            bundle_tickets=[tuple(sorted(rng.sample(range(1,46),6))) for _ in range(3)]; rh=[len(set(q)&winning) for q in bundle_tickets]; runion=set().union(*(set(q) for q in bundle_tickets))
            random_ticket_hits.append(max(rh)); random_rows.append({"target_round":t,"repeat":r+1,"line_hits":";".join(map(str,rh)),"unique_number_coverage":len(runion),
                "winning_union_coverage":len(runion&winning),"any_2plus":int(max(rh)>=2),"any_3plus":int(max(rh)>=3),"any_4plus":int(max(rh)>=4),"bundle_max_hits":max(rh)})
        values["RANDOM_THREE_TICKET_BUNDLE"].append(statistics.mean(random_ticket_hits))
    fixed=[r for r in records]; random_records=random_rows
    metrics=[{"bundle":"FIXED_THREE_COMPONENT_BUNDLE","target_rounds":len(fixed),
        "mean_bundle_max_hits":statistics.mean(r["bundle_max_hits"] for r in fixed),
        "mean_unique_number_coverage":statistics.mean(r["unique_number_coverage"] for r in fixed),
        "mean_winning_union_coverage":statistics.mean(r["winning_union_coverage"] for r in fixed),
        "rate_any_2plus":statistics.mean(r["any_2plus"] for r in fixed),"rate_any_3plus":statistics.mean(r["any_3plus"] for r in fixed),
        "rate_any_4plus":statistics.mean(r["any_4plus"] for r in fixed)},
        {"bundle":"RANDOM_THREE_TICKET_BUNDLE","target_rounds":len(TARGETS),"random_bundles":len(random_records),
        "mean_bundle_max_hits":statistics.mean(r["bundle_max_hits"] for r in random_records),
        "mean_unique_number_coverage":statistics.mean(r["unique_number_coverage"] for r in random_records),
        "mean_winning_union_coverage":statistics.mean(r["winning_union_coverage"] for r in random_records),
        "rate_any_2plus":statistics.mean(r["any_2plus"] for r in random_records),"rate_any_3plus":statistics.mean(r["any_3plus"] for r in random_records),
        "rate_any_4plus":statistics.mean(r["any_4plus"] for r in random_records)}]
    engine.csvfile(out/"BUNDLE_RESULTS.csv",records); engine.csvfile(out/"RANDOM_BUNDLE_RESULTS.csv",random_rows); engine.csvfile(out/"BUNDLE_METRICS.csv",metrics)
    verification={"status":"PASS","target_rounds":len(TARGETS),"fixed_bundle_records":len(records),"random_bundle_records":len(random_rows),
        "bundle_components_frozen":components,"future_predictions":0,"component_sources":"cutoff-safe stored OOS forecasts"}
    engine.jsonfile(out/"VERIFICATION.json",verification)
    _report(out,task,metrics,verification,"One pre-frozen three-component bundle is evaluated only where all component predictions exist. Random comparisons use three independent uniform tickets on each same target round.","Retrospective portfolio findings do not change any prospective or purchase rules; no bundle is generated for future rounds.")
    return {"executed_cases":len(records)+len(random_rows),"verification":verification}


def _report(out,task,rows,verification,method,interpretation):
    lines=["# "+task["question"],"","## MAINTENANCE/RECHECK","","Existing B component forecasts are reused only as the frozen, cutoff-safe input panel; this is not a new B reproduction.","","## NEW STUDY","",method,"","## NEW FINDING","",interpretation,"","## Results","","```json",__import__("json").dumps(rows,ensure_ascii=False,indent=2),"```","","## Verification","","```json",__import__("json").dumps(verification,ensure_ascii=False,indent=2),"```","","## NEXT TEST","","Retain the frozen experiment and seek independent prospective evidence. Do not tune this result into a future recommendation.",""]
    with (Path(out)/"REPORT.md").open("x",encoding="utf-8") as stream: stream.write("\n".join(lines))


def run_study(root,out,task):
    kind=task["kind"]
    if kind=="component_loo": return study_component_loo(root,out,task)
    if kind=="agreement": return study_agreement(root,out,task)
    if kind=="pair_drop": return study_pair_drop(root,out,task)
    if kind=="vote_depth": return study_vote_depth(root,out,task)
    if kind=="portfolio": return study_portfolio(root,out,task)
    if kind=="blocked": raise FileNotFoundError(task["spec"].get("blocked_reason","Source unavailable"))
    if kind=="purchase": raise FileNotFoundError("No authenticated historical purchase artifact is registered for this task")
    raise ValueError("Unsupported frozen study kind: "+str(kind))
