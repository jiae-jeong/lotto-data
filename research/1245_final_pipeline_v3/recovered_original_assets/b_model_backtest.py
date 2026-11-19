#!/usr/bin/env python3
"""Leakage-safe rolling-origin backtest for fixed lotto signal models.

Reads work/lotto-data/lotto_data.csv without modifying it. Writes reproducible
predictions, aggregate metrics, and a report to outputs/.
"""
from __future__ import annotations

import csv
import itertools
import json
import math
import random
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "work" / "lotto-data" / "lotto_data.csv"
OUT = ROOT / "outputs"
ANCHORS = [200, 400, 600, 800, 1000, 1100, 1150, 1200]
HORIZONS = [10, 25, 50, "to_end"]
N_NUMBERS, DRAW_SIZE = 45, 6
RECENT_WINDOW = 50
STRUCTURE_BANK_SEED = 20261006
STRUCTURE_BANK_SIZE = 10000
MODEL_NAMES = ["long_frequency", "current_gap", "frequency_plus_gap", "recent_momentum",
               "structure_profile", "pair_association", "triple_association", "combined_equal_rank"]
RANGE_BUCKETS = [(1, 10), (11, 20), (21, 30), (31, 40), (41, 45)]


def read_data() -> list[dict]:
    with INPUT.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    draws = []
    for r in rows:
        nums = tuple(sorted(int(r[f"no{i}"]) for i in range(1, 7)))
        draws.append({"round": int(r["round"]), "date": r["date"], "nums": nums})
    draws.sort(key=lambda d: d["round"])
    return draws


def bucket_counts(nums: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sum(lo <= x <= hi for x in nums) for lo, hi in RANGE_BUCKETS)


def structure_profile(nums: tuple[int, ...], previous: tuple[int, ...] | None) -> tuple:
    gaps = [b - a for a, b in zip(nums, nums[1:])]
    return (sum(x % 2 for x in nums), sum(x <= 22 for x in nums), bucket_counts(nums),
            sum(nums) // 10, sum(g == 1 for g in gaps),
            sum(x in set(previous or ()) for x in nums))


def make_structure_bank() -> list[tuple[int, ...]]:
    rng = random.Random(STRUCTURE_BANK_SEED)
    bank: set[tuple[int, ...]] = set()
    while len(bank) < STRUCTURE_BANK_SIZE:
        bank.add(tuple(sorted(rng.sample(range(1, 46), 6))))
    return sorted(bank)


def feature_structure_bank(bank: list[tuple[int, ...]]) -> list[tuple]:
    rows = []
    for ticket in bank:
        gaps = [b - a for a, b in zip(ticket, ticket[1:])]
        fixed = (sum(x % 2 for x in ticket), sum(x <= 22 for x in ticket), bucket_counts(ticket),
                 sum(ticket) // 10, sum(g == 1 for g in gaps))
        mask = sum(1 << (x - 1) for x in ticket)
        rows.append((ticket, fixed, mask))
    return rows


def rank_scores(values: list[float]) -> list[int]:
    order = sorted(range(45), key=lambda i: (-values[i], i + 1))
    result = [0] * 45
    for rank, i in enumerate(order):
        result[i] = 45 - rank
    return result


def top_six(scores: list[float]) -> tuple[int, ...]:
    return tuple(sorted(i + 1 for i in sorted(range(45), key=lambda i: (-scores[i], i + 1))[:6]))


def pair_z(a: int, b: int, n: int, freq: list[int], pair_counts: Counter) -> float:
    expected = (DRAW_SIZE - 1) / DRAW_SIZE * N_NUMBERS / (N_NUMBERS - 1) * freq[a] * freq[b] / n
    observed = pair_counts[(a + 1, b + 1)]
    return (observed - expected) / math.sqrt(max(expected, 1e-12))


def triple_z(a: int, b: int, c: int, n: int, freq: list[int], triple_counts: Counter) -> float:
    factor = ((DRAW_SIZE - 1) * (DRAW_SIZE - 2) / (DRAW_SIZE ** 2)
              * (N_NUMBERS ** 2) / ((N_NUMBERS - 1) * (N_NUMBERS - 2)))
    expected = factor * freq[a] * freq[b] * freq[c] / (n ** 2)
    observed = triple_counts[(a + 1, b + 1, c + 1)]
    return (observed - expected) / math.sqrt(max(expected, 1e-12))


def pair_ticket(n: int, freq: list[int], pc: Counter) -> tuple[int, ...]:
    pairs = list(itertools.combinations(range(45), 2))
    best = max(pairs, key=lambda p: (pair_z(*p, n, freq, pc), -p[0], -p[1]))
    selected = list(best)
    while len(selected) < 6:
        candidates = [i for i in range(45) if i not in selected]
        nxt = max(candidates, key=lambda i: (sum(pair_z(min(i, j), max(i, j), n, freq, pc)
                                                  for j in selected), -i))
        selected.append(nxt)
    return tuple(sorted(i + 1 for i in selected))


def triple_ticket(n: int, freq: list[int], tc: Counter) -> tuple[int, ...]:
    triples = list(itertools.combinations(range(45), 3))
    best = max(triples, key=lambda t: (triple_z(*t, n, freq, tc), -t[0], -t[1], -t[2]))
    selected = list(best)
    while len(selected) < 6:
        candidates = [i for i in range(45) if i not in selected]
        nxt = max(candidates, key=lambda i: (sum(triple_z(*sorted((i, a, b)), n, freq, tc)
                                                  for a, b in itertools.combinations(selected, 2)), -i))
        selected.append(nxt)
    return tuple(sorted(i + 1 for i in selected))


def structure_ticket(bank: list[tuple], n: int, profile_counts: list[Counter],
                     previous: tuple[int, ...]) -> tuple[int, ...]:
    # Independent Laplace-smoothed marginal likelihoods; fixed category counts:
    # odd=7, low=7, band vector=210 weak compositions, sum decades=24, overlap=7.
    ks = (7, 7, 210, 24, 6, 7)
    category_sets = [set(row[1][j] for row in bank) for j in range(5)]
    log_probs = [{key: math.log((profile_counts[j][key] + 1) / (n + ks[j]))
                  for key in category_sets[j]} for j in range(5)]
    log_overlap = [math.log((profile_counts[5][k] + 1) / (n + ks[5])) for k in range(7)]
    prev_mask = sum(1 << (x - 1) for x in previous)
    best_ticket, best_score = None, -float("inf")
    for ticket, fixed, mask in bank:
        score = sum(log_probs[j][fixed[j]] for j in range(5)) + log_overlap[(mask & prev_mask).bit_count()]
        if score > best_score:
            best_ticket, best_score = ticket, score
    return best_ticket


def predictions_for_round(draws: list[dict], train_n: int, freq: list[int], last_seen: list[int],
                          pc: Counter, tc: Counter, profile_counts: list[Counter],
                          bank: list[tuple]) -> dict[str, tuple[int, ...]]:
    n = train_n
    current_round = draws[train_n - 1]["round"]
    previous = draws[train_n - 1]["nums"]
    gaps = [current_round - last_seen[i] if last_seen[i] else current_round for i in range(45)]
    freq_ranks = rank_scores([float(x) for x in freq])
    gap_ranks = rank_scores([float(x) for x in gaps])
    recent = draws[max(0, train_n - RECENT_WINDOW):train_n]
    earlier = draws[max(0, train_n - 2 * RECENT_WINDOW):max(0, train_n - RECENT_WINDOW)]
    recent_counts = [0] * 45
    earlier_counts = [0] * 45
    for d in recent:
        for num in d["nums"]:
            recent_counts[num - 1] += 1
    for d in earlier:
        for num in d["nums"]:
            earlier_counts[num - 1] += 1
    recent_rates = [recent_counts[i] / max(1, len(recent)) - earlier_counts[i] / max(1, len(earlier))
                    for i in range(45)]
    momentum_ranks = rank_scores(recent_rates)

    pair_node = [sum(pair_z(min(i, j), max(i, j), n, freq, pc)
                     for j in range(45) if j != i) for i in range(45)]
    triple_node = [0.0] * 45
    for a, b, c in itertools.combinations(range(45), 3):
        z = triple_z(a, b, c, n, freq, tc)
        triple_node[a] += z
        triple_node[b] += z
        triple_node[c] += z
    pair_ranks, triple_ranks = rank_scores(pair_node), rank_scores(triple_node)
    combined = [(freq_ranks[i] + gap_ranks[i] + momentum_ranks[i]
                 + (pair_ranks[i] + triple_ranks[i]) / 2) / 4 for i in range(45)]

    return {
        "long_frequency": top_six([float(x) for x in freq]),
        "current_gap": top_six([float(x) for x in gaps]),
        "frequency_plus_gap": top_six([(freq_ranks[i] + gap_ranks[i]) / 2 for i in range(45)]),
        "recent_momentum": top_six(recent_rates),
        "structure_profile": structure_ticket(bank, n, profile_counts, previous),
        "pair_association": pair_ticket(n, freq, pc),
        "triple_association": triple_ticket(n, freq, tc),
        "combined_equal_rank": top_six(combined),
    }


def baseline() -> tuple[list[float], float, float]:
    den = math.comb(45, 6)
    probs = [math.comb(6, k) * math.comb(39, 6-k) / den for k in range(7)]
    mean = sum(k * probs[k] for k in range(7))
    var = sum((k - mean) ** 2 * probs[k] for k in range(7))
    return probs, mean, var


def aggregate(records: list[dict], base_probs: list[float], base_mean: float, base_var: float) -> dict:
    hits = [int(r["hits"]) for r in records]
    n = len(hits)
    hist = Counter(hits)
    result = {"n": n, "mean_hits": statistics.mean(hits) if n else 0,
              "variance_hits_population": statistics.pvariance(hits) if n else 0,
              "rate_ge_2": sum(x >= 2 for x in hits) / n if n else 0,
              "rate_ge_3": sum(x >= 3 for x in hits) / n if n else 0,
              "rate_ge_4": sum(x >= 4 for x in hits) / n if n else 0,
              "rate_ge_5": sum(x >= 5 for x in hits) / n if n else 0,
              "structure_conditions_mean_of_6": statistics.mean(int(r["structure_conditions_matched"]) for r in records) if n else 0,
              "structure_full_match_rate": sum(bool(r["structure_full_match"]) for r in records) / n if n else 0}
    for k in range(7):
        result[f"hits_{k}_count"] = hist[k]
        result[f"hits_{k}_rate"] = hist[k] / n if n else 0
        result[f"baseline_hits_{k}_rate"] = base_probs[k]
    result.update({"baseline_mean_hits": base_mean, "baseline_variance_hits": base_var,
                   "baseline_rate_ge_2": sum(base_probs[2:]),
                   "baseline_rate_ge_3": sum(base_probs[3:]),
                   "baseline_rate_ge_4": sum(base_probs[4:]),
                   "baseline_rate_ge_5": sum(base_probs[5:])})
    return result


def main() -> None:
    draws = read_data()
    if len(draws) != 1244 or [d["round"] for d in draws] != list(range(1, 1245)):
        raise SystemExit("Input no longer matches validated rounds 1..1244; inspect before backtesting.")
    bank = feature_structure_bank(make_structure_bank())
    freq = [0] * 45
    last_seen = [0] * 45
    pc: Counter = Counter()
    tc: Counter = Counter()
    profile_counts = [Counter() for _ in range(6)]
    for d in draws[:200]:
        nums = d["nums"]
        for x in nums:
            freq[x - 1] += 1
            last_seen[x - 1] = d["round"]
        pc.update(itertools.combinations(nums, 2))
        tc.update(itertools.combinations(nums, 3))
        prof = structure_profile(nums, None)
        for i, value in enumerate(prof[:5]):
            profile_counts[i][value] += 1
    for idx in range(1, 200):
        prof = structure_profile(draws[idx]["nums"], draws[idx - 1]["nums"])
        profile_counts[5][prof[5]] += 1

    # Origin cutoff must be no later than the round immediately before each prediction.
    cached: dict[int, dict[str, tuple[int, ...]]] = {}
    for train_n in range(200, len(draws)):
        target_round = train_n + 1
        cached[target_round] = predictions_for_round(draws, train_n, freq, last_seen, pc, tc,
                                                      profile_counts, bank)
        if train_n < len(draws):
            d = draws[train_n]
            for x in d["nums"]:
                freq[x - 1] += 1
                last_seen[x - 1] = d["round"]
            pc.update(itertools.combinations(d["nums"], 2))
            tc.update(itertools.combinations(d["nums"], 3))
            prof = structure_profile(d["nums"], draws[train_n - 1]["nums"])
            for i, value in enumerate(prof):
                profile_counts[i][value] += 1

    prediction_rows: list[dict] = []
    for anchor in ANCHORS:
        for horizon in HORIZONS:
            length = min(horizon, 1244 - anchor) if isinstance(horizon, int) else 1244 - anchor
            if length <= 0:
                continue
            label = (f"{horizon}" if length == horizon else f"{horizon}_cap{length}") if isinstance(horizon, int) else f"to_end_{length}"
            for target in range(anchor + 1, anchor + length + 1):
                train_n = target - 1
                actual = set(draws[target - 1]["nums"])
                previous = set(draws[target - 2]["nums"])
                actual_prof = structure_profile(tuple(sorted(actual)), tuple(sorted(previous)))
                for model in MODEL_NAMES:
                    pred = cached[target][model]
                    pred_set = set(pred)
                    pred_prof = structure_profile(pred, tuple(sorted(previous)))
                    components = [pred_prof[i] == actual_prof[i] for i in range(6)]
                    prediction_rows.append({
                        "anchor_after_round": anchor, "horizon": label, "horizon_length": length,
                        "target_round": target, "training_through_round": train_n,
                        "model": model, "predicted_numbers": " ".join(map(str, pred)),
                        "actual_numbers": " ".join(map(str, sorted(actual))), "hits": len(pred_set & actual),
                        "odd_match": int(components[0]), "low_1_22_match": int(components[1]),
                        "band_vector_match": int(components[2]), "sum_decade_match": int(components[3]),
                        "consecutive_pair_count_match": int(components[4]),
                        "previous_draw_overlap_match": int(components[5]),
                        "structure_conditions_matched": sum(components),
                        "structure_full_match": int(all(components)),
                    })

    base_probs, base_mean, base_var = baseline()
    aggregate_rows: list[dict] = []
    groups: dict[tuple, list[dict]] = {}
    for r in prediction_rows:
        groups.setdefault((r["anchor_after_round"], r["horizon"], r["model"]), []).append(r)
    for (anchor, horizon, model), records in sorted(groups.items()):
        m = aggregate(records, base_probs, base_mean, base_var)
        aggregate_rows.append({"anchor_after_round": anchor, "horizon": horizon, "model": model, **m,
                               "delta_mean_vs_random": m["mean_hits"] - base_mean,
                               "delta_ge2_pp_vs_random": (m["rate_ge_2"] - m["baseline_rate_ge_2"]) * 100})

    trend_rows = [r for r in aggregate_rows if r["horizon"] == "50"
                  and r["anchor_after_round"] in [a for a in ANCHORS if 1244-a >= 50]]
    with (OUT / "b_model_50_round_trends.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["anchor_after_round", "tested_rounds", "model", "n", "mean_hits",
                  "delta_mean_vs_random", "rate_ge_2", "delta_ge2_pp_vs_random",
                  "rate_ge_3", "rate_ge_4", "rate_ge_5", "variance_hits_population",
                  "structure_conditions_mean_of_6", "structure_full_match_rate"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in sorted(trend_rows, key=lambda x: (x["anchor_after_round"], x["model"])):
            w.writerow({k: (f"{r['anchor_after_round'] + 1}-{r['anchor_after_round'] + 50}"
                            if k == "tested_rounds" else r[k]) for k in fields})

    # Consistency screen on the disjoint 50-round windows available at 200..1100.
    anchor50 = [a for a in ANCHORS if 1244 - a >= 50]
    classification_rows = []
    for model in MODEL_NAMES:
        rows = [r for r in aggregate_rows if r["model"] == model and r["horizon"] == "50"]
        deltas = [float(r["delta_mean_vs_random"]) for r in rows]
        positives = sum(x > 0 for x in deltas)
        pooled = [r for r in prediction_rows if r["model"] == model and r["horizon"] == "50"
                  and r["anchor_after_round"] in anchor50]
        pooled_metric = aggregate(pooled, base_probs, base_mean, base_var)
        mean_delta = pooled_metric["mean_hits"] - base_mean
        ge2_delta_pp = (pooled_metric["rate_ge_2"] - pooled_metric["baseline_rate_ge_2"]) * 100
        negatives = sum(x < 0 for x in deltas)
        if len(anchor50) >= 6 and positives >= 6 and mean_delta >= 0.05 and ge2_delta_pp >= 2:
            classification = "KEEP"
            reason = f"50회 구간 {positives}/{len(anchor50)}개에서 평균 적중이 기준선 초과; pooled 평균차 {mean_delta:+.3f}, 2+ 적중률 차 {ge2_delta_pp:+.2f}pp (기술적 기준만 충족)."
        elif len(anchor50) >= 6 and negatives >= 6 and mean_delta <= -0.08 and ge2_delta_pp <= -2:
            classification = "REDUCE"
            reason = f"50회 구간 {negatives}/{len(anchor50)}개에서 평균 적중이 기준선 미달; pooled 평균차 {mean_delta:+.3f}, 2+ 적중률 차 {ge2_delta_pp:+.2f}pp."
        elif abs(mean_delta) < 0.03 and abs(ge2_delta_pp) < 1.5 and positives in (3, 4):
            classification = "HOLD"
            reason = f"기준선 근처: pooled 평균차 {mean_delta:+.3f}, 2+ 적중률 차 {ge2_delta_pp:+.2f}pp; 50회 구간 {positives}/{len(anchor50)}개 우세."
        else:
            classification = "ADDITIONAL VALIDATION"
            reason = f"결과가 기준점에 따라 일관되지 않거나 유지/축소 기준을 충족하지 않음; 50회 구간 {positives}/{len(anchor50)}개 우세, pooled 평균차 {mean_delta:+.3f}, 2+ 적중률 차 {ge2_delta_pp:+.2f}pp."
        classification_rows.append({"model": model, "classification": classification,
                                    "50_round_blocks_positive": positives, "50_round_blocks_total": len(anchor50),
                                    "pooled_mean_hit_delta": mean_delta, "pooled_ge2_rate_delta_pp": ge2_delta_pp,
                                    "pooled_n": pooled_metric["n"],
                                    "pooled_mean_hits": pooled_metric["mean_hits"],
                                    "pooled_variance_hits": pooled_metric["variance_hits_population"],
                                    "pooled_rate_ge_2": pooled_metric["rate_ge_2"],
                                    "pooled_rate_ge_3": pooled_metric["rate_ge_3"],
                                    "pooled_rate_ge_4": pooled_metric["rate_ge_4"],
                                    "pooled_rate_ge_5": pooled_metric["rate_ge_5"],
                                    "structure_conditions_mean_of_6": pooled_metric["structure_conditions_mean_of_6"],
                                    "structure_full_match_rate": pooled_metric["structure_full_match_rate"],
                                    **{f"hits_{k}_count": pooled_metric[f"hits_{k}_count"] for k in range(7)},
                                    "reason": reason})

    OUT.mkdir(parents=True, exist_ok=True)
    pred_fields = list(prediction_rows[0]) if prediction_rows else []
    with (OUT / "b_model_predictions.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=pred_fields)
        w.writeheader(); w.writerows(prediction_rows)
    agg_fields = list(aggregate_rows[0]) if aggregate_rows else []
    with (OUT / "b_model_holdout_metrics.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=agg_fields)
        w.writeheader(); w.writerows(aggregate_rows)
    with (OUT / "b_model_classification.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(classification_rows[0]))
        w.writeheader(); w.writerows(classification_rows)

    # Report the exact theoretical lottery baseline and fixed design choices.
    total_tests = len(prediction_rows)
    report = [
        "# B 모델 롤링 워크포워드 백테스트",
        "",
        f"- 데이터: 회차 1~1244, {len(draws)}회. 원본 `{INPUT}`은 읽기 전용으로 사용했습니다.",
        f"- 총 평가 레코드: {total_tests} (같은 목표 회차가 여러 중첩 holdout에 반복 기록되며, 독립 표본 수로 보면 안 됩니다).",
        "- 누수 방지: 예측 대상이 t회면 학습은 오직 1~t-1회까지입니다. 기준점 뒤 각 회차마다 직전까지의 데이터로 점수를 갱신하는 expanding walk-forward 방식입니다.",
        "- 기준점: 200, 400, 600, 800, 1000, 1100, 1150, 1200회차 이후. 각 기준점마다 10/25/50회 및 해당 기준점 이후 마지막 회차까지의 holdout을 계산했습니다. 남은 회차보다 긴 horizon은 가능한 길이까지만 사용합니다.",
        "- 10/25/50회 holdout은 중첩되고, `to_end` 구간도 서로 겹칩니다. 안정성 분류는 기준점 200~1100 이후의 50회 블록(7개, 서로 겹치지 않음)을 중심으로 했습니다.",
        "",
        "## 고정 모델 정의",
        "| 모델 | 고정 점수/선정 규칙 |",
        "|---|---|",
        "| 1 장기 출현빈도 | 학습구간 본번호 출현 횟수 내림차순 상위 6개; 동률이면 작은 번호 먼저 |",
        "| 2 미출현 간격 | cutoff 회차-마지막 출현 회차 내림차순 상위 6개; 동률 작은 번호 먼저 |",
        "| 3 빈도+간격 | 1과 2의 45개 번호 내 순위점수(1위=45, 45위=1)를 각 0.5 가중 평균, 상위 6개 |",
        "| 4 최근 빈도 변화 | 직전 50회 출현률 - 그 직전 50회 출현률; 큰 순 상위 6개. 학습구간 100회 미만이면 이용 가능한 각 창 길이로 나눔 |",
        f"| 5 구조 프로필 | 홀수개수, 1~22 개수, 5개 구간 분포벡터, 합계 10단위 구간, 연속쌍 개수, 직전 회차 중복의 학습분포에 독립 Laplace(+1) 스무딩 로그확률을 합산. 고정 균등 후보은행 {STRUCTURE_BANK_SIZE:,}개 중 최대점수 조합 선택; 고정 seed={STRUCTURE_BANK_SEED}, 동점은 사전식 |",
        "| 6 번호쌍 | pair 잔차 z=(관측-기대)/√기대. 기대=5/6×45/44×fᵢfⱼ/n. 최고 z pair로 시작 후 이미 고른 수와의 z 합이 큰 번호를 순차 추가 |",
        "| 7 triple | triple 잔차 z=(관측-기대)/√기대. 기대=fᵢfⱼfₖ/n²×(5×4/6²)×45²/(44×43). 최고 z triple로 시작 후 기존 선택 2개와 형성하는 z 합이 큰 번호를 순차 추가 |",
        "| 8 결합 동일가중 | 번호별 장기빈도 순위, 미출현간격 순위, 최근모멘텀 순위, 관계축( pair 잔차 순위와 triple 잔차 순위의 평균 )을 각각 1/4 가중. 상위 6개. 구조 프로필은 set-level이라 결합 축에서 제외 |",
        "- 순위축은 동률을 작은 번호 우선으로 해결합니다. pair/triple 계산은 본번호만 사용합니다.",
        "- 구조 적중은 예측 조합의 홀수 수, 저/고 수, 5구간 벡터, 합계 10단위, 연속쌍 수, 직전 회차 중복 수가 실제 회차와 각각 같은지 계산했습니다. 전체 6조건 일치 여부도 기록했습니다.",
        "",
        "## 균등 무작위 6/45 기준선 (정확 계산)",
        "- 각 추첨 조합은 C(45,6)=8,145,060가지가 동일 확률이라고 두었습니다. 적중 k개의 확률은 C(6,k)×C(39,6-k)/C(45,6)입니다.",
        "- 적중 분포: " + ", ".join((f"{k}개={base_probs[k]*100:.8f}%" if k == 6
                                      else f"{k}개={base_probs[k]*100:.4f}%") for k in range(7)) + ".",
        f"- 회차당 평균 적중 {base_mean:.6f}, 적중수 분산 {base_var:.6f}; 2+ 적중 {sum(base_probs[2:])*100:.4f}%, 3+ {sum(base_probs[3:])*100:.4f}%, 4+ {sum(base_probs[4:])*100:.4f}%, 5+ {sum(base_probs[5:])*100:.4f}%.",
        "- 이는 이론적 균등무작위 기대값이며, 모델별 실제 홀드아웃 결과와 비교하는 기준입니다.",
        "",
        "## 분류 기준 (사전 고정된 기술적 스크리닝; 유의성 검정 아님)",
        "- 50회 블록에서 6/7 이상 평균 적중 우세, pooled 평균 적중 +0.05 이상, 2+ 적중률 +2pp 이상이면 KEEP.",
        "- 6/7 이상 평균 적중 열세, pooled 평균 적중 -0.08 이하, 2+ 적중률 -2pp 이하이면 REDUCE.",
        "- pooled 평균 차 절댓값 <0.03, 2+ 차 절댓값 <1.5pp이고 블록 우세가 3/7 또는 4/7이면 HOLD. 그 외에는 ADDITIONAL VALIDATION.",
        "- 이 규칙은 보수적인 운영 분류일 뿐 p-value, 신뢰구간, 통계적 유의성 또는 당첨 예측력을 의미하지 않습니다. 여러 모델/겹치는 창 비교에 대한 다중검정 보정은 하지 않았습니다.",
        "",
        "## 비중첩 50회 블록 종합 (기준점 200~1150; 총 350회 예측)",
        "| 모델 | 분류 | 0/1/2/3/4/5/6개 적중 횟수 | 평균 | 분산 | 2+ | 3+ | 4+ | 5+ | 기준선 대비 평균 | 기준선 대비 2+ | 평균 구조조건 일치/6 | 전체 구조 일치 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in classification_rows:
        report.append("| {model} | {classification} | {hist} | {mean:.3f} | {var:.3f} | {ge2:.2%} | {ge3:.2%} | {ge4:.2%} | {ge5:.2%} | {dmean:+.3f} | {dge2:+.2f}pp | {sm:.3f} | {sf:.2%} |".format(
            model=row["model"], classification=row["classification"],
            hist="/".join(str(row[f"hits_{k}_count"]) for k in range(7)),
            mean=row["pooled_mean_hits"], var=row["pooled_variance_hits"],
            ge2=row["pooled_rate_ge_2"], ge3=row["pooled_rate_ge_3"],
            ge4=row["pooled_rate_ge_4"], ge5=row["pooled_rate_ge_5"],
            dmean=row["pooled_mean_hit_delta"], dge2=row["pooled_ge2_rate_delta_pp"],
            sm=row["structure_conditions_mean_of_6"], sf=row["structure_full_match_rate"]))
    report += [
        "",
        "## 50회 블록별 시간 변화",
        "각 셀은 평균 적중(무작위 평균 0.800 대비 차이) / 2+ 적중률(무작위 17.53% 대비 차이)입니다.",
        "| 모델 | 201~250 | 401~450 | 601~650 | 801~850 | 1001~1050 | 1101~1150 | 1151~1200 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model in MODEL_NAMES:
        cells = []
        for anchor in anchor50:
            r = next(x for x in trend_rows if x["model"] == model and x["anchor_after_round"] == anchor)
            cells.append(f"{r['mean_hits']:.3f} ({r['delta_mean_vs_random']:+.3f}) / {r['rate_ge_2']:.1%} ({r['delta_ge2_pp_vs_random']:+.2f}pp)")
        report.append("| " + model + " | " + " | ".join(cells) + " |")
    report += [
        "- 블록별 상세값은 `b_model_50_round_trends.csv`; 모든 10/25/50/남은구간 결과는 `b_model_holdout_metrics.csv`에 있습니다.",
        "",
        "## 파일 구성",
        "- `b_model_predictions.csv`: 모든 기준점·기간·모델·목표 회차별 예측, 학습 cutoff, 본번호, 적중 및 6개 구조조건 결과.",
        "- `b_model_holdout_metrics.csv`: 각 기준점×기간×모델의 0~6 적중 분포, 2+/3+/4+/5+ 비율, 평균·분산, 구조조건 일치와 정확 무작위 기준선.",
        "- `b_model_classification.csv`: 50회 비중첩 블록 일관성, 수치 차이, KEEP/REDUCE/HOLD/ADDITIONAL VALIDATION 분류 및 이유.",
        "- `b_model_50_round_trends.csv`: 7개 비중첩 50회 블록에서의 시간별 평균 적중 및 2+ 적중률 변화.",
        "- 재현: PowerShell에서 `./outputs/run_b_model_backtest.ps1`.",
        "- 추천번호는 생성하지 않았습니다. 통계적 유의성 검정은 계산하지 않았습니다.",
    ]
    for row in classification_rows:
        report.append(f"- **{row['model']} — {row['classification']}**: {row['reason']}")
    (OUT / "b_model_backtest_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Rows={len(draws)}; prediction_records={total_tests}; anchors={ANCHORS}")
    print(f"Random baseline mean={base_mean:.6f}; variance={base_var:.6f}; p_ge2={sum(base_probs[2:]):.6f}")
    for row in classification_rows:
        print(f"{row['model']}: {row['classification']}; blocks+={row['50_round_blocks_positive']}/{row['50_round_blocks_total']}; delta_mean={row['pooled_mean_hit_delta']:+.3f}; delta_ge2_pp={row['pooled_ge2_rate_delta_pp']:+.2f}")
    print(f"Outputs: {OUT}")


if __name__ == "__main__":
    main()
