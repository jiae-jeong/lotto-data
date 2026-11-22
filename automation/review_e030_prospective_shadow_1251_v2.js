#!/usr/bin/env node
"use strict";
const fs = require("fs");
const crypto = require("crypto");

const EXPECTED_FROZEN_SHA256 = "e809288c6f6a2d891fb48e88810369e03ff64cea48333b5fca383d6621b316c6";
const EXPECTED_CANONICAL_SHA256 = "7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2";
const EXPECTED_SNAPSHOT_SHA256 = "2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9";
const EXPECTED_SNAPSHOT_ROWS = 1251;
const TARGET = 1251;
const K_VALUES = [10, 15, 20, 25, 30];

function sha256(bytes) {
  return crypto.createHash("sha256").update(bytes).digest("hex");
}
function parseCsv(path) {
  const raw = fs.readFileSync(path);
  const lines = raw.toString("utf8").split(/\r?\n/).filter(line => line.trim() !== "");
  const rows = lines.slice(1).map(line => line.split(","));
  if (rows.length !== EXPECTED_SNAPSHOT_ROWS) throw new Error("snapshot row count mismatch");
  const draws = rows.map((r, i) => {
    const round = Number(r[0]), date = r[1];
    const main = r.slice(2, 8).map(Number), bonus = Number(r[8]);
    if (round !== i + 1) throw new Error("round sequence mismatch at " + (i + 1));
    if (main.length !== 6 || new Set(main).size !== 6 ||
        main.some(n => !Number.isInteger(n) || n < 1 || n > 45)) throw new Error("invalid main numbers");
    if (!Number.isInteger(bonus) || bonus < 1 || bonus > 45 || main.includes(bonus))
      throw new Error("invalid bonus number");
    return { round, date, main, bonus };
  });
  return { raw, draws };
}
function review(frozen, draws) {
  if (frozen.status !== "FROZEN_PROSPECTIVE_SHADOW_ONLY" ||
      frozen.target_round !== TARGET || frozen.training_through_round !== TARGET - 1)
    throw new Error("unexpected frozen artifact scope");
  const actual = new Set(draws[TARGET - 1].main);
  const signals = frozen.signals.map(signal => {
    const order = signal.score_order;
    if (order.length !== 45 || new Set(order).size !== 45 ||
        order.some(n => !Number.isInteger(n) || n < 1 || n > 45))
      throw new Error("invalid 45-number ranking");
    const winnerRanks = [...actual].map(n => order.indexOf(n) + 1).sort((a,b) => a-b);
    const candidateRecall = {};
    for (const k of K_VALUES)
      candidateRecall[k] = {
        winners_retained: winnerRanks.filter(rank => rank <= k).length,
        winners_total: 6,
        random_expected_hits: k * 6 / 45
      };
    const top6 = order.slice(0, 6);
    const frozenSet = [...signal.numbers].sort((a,b)=>a-b);
    const top6Sorted = [...top6].sort((a,b)=>a-b);
    if (JSON.stringify(frozenSet) !== JSON.stringify(top6Sorted))
      throw new Error("frozen top-six set differs from score order");
    return {
      signal: signal.signal,
      top6_hit_count: top6.filter(n => actual.has(n)).length,
      winner_rank_positions: winnerRanks,
      mean_winner_rank: winnerRanks.reduce((a,b)=>a+b,0)/6,
      candidate_recall_at_k: candidateRecall
    };
  });
  const a=frozen.signals[0].score_order, b=frozen.signals[1].score_order;
  const overlap = {};
  for (const k of [6,10,15,30])
    overlap[k] = a.slice(0,k).filter(n => b.slice(0,k).includes(n)).length;
  return {
    review_id: "E030_PROSPECTIVE_SHADOW_REVIEW_1251_v1",
    evidence_class: "FIRST_RESUMED_PROSPECTIVE_SHADOW_OBSERVATION_SINGLE_TARGET_NOT_CONFIRMATION",
    target_round: TARGET,
    draw_date: draws[TARGET-1].date,
    training_cutoff: TARGET-1,
    candidate_stage_only: true,
    signals,
    top_k_overlap_counts: overlap,
    no_portfolio_or_allocator_evaluation: true,
    no_purchase_readiness_effect: true,
    prospective_horizon_note: "E030 resumed at target 1251 after the historical pre-draw gap at 1247-1250; this is one shadow observation, not a completed confirmation horizon."
  };
}
function main() {
  const [frozenPath, snapshotPath, resumePath] = process.argv.slice(2);
  if (!frozenPath || !snapshotPath || !resumePath)
    throw new Error("usage: node review.js FROZEN_SIGNALS_1251.json lotto_data_through_1251_20261122.csv RESUME_STATUS_1251.json");
  const frozenBytes=fs.readFileSync(frozenPath);
  const frozen=JSON.parse(frozenBytes.toString("utf8"));
  const snapshot=parseCsv(snapshotPath);
  const resume=JSON.parse(fs.readFileSync(resumePath,"utf8"));
  const frozenSha=sha256(frozenBytes), snapshotSha=sha256(snapshot.raw);
  if (frozenSha !== EXPECTED_FROZEN_SHA256 || frozenSha !== resume.prediction_sha256)
    throw new Error("frozen artifact SHA256 mismatch");
  if (snapshotSha !== EXPECTED_SNAPSHOT_SHA256) throw new Error("snapshot SHA256 mismatch");
  if (snapshot.draws.length !== EXPECTED_SNAPSHOT_ROWS) throw new Error("snapshot rows mismatch");
  if (frozen.canonical_data_sha256 !== EXPECTED_CANONICAL_SHA256 ||
      frozen.training_data_cutoff !== 1250 || resume.training_data_sha256 !== EXPECTED_CANONICAL_SHA256)
    throw new Error("pre-draw training source mismatch");
  if (Date.parse(frozen.generated_at_utc) >= Date.parse(snapshot.draws[TARGET-1].date.replaceAll(".","-")))
    throw new Error("freeze timestamp is not before target draw date");
  const result=review(frozen,snapshot.draws);
  result.integrity = {
    frozen_artifact_sha256: frozenSha,
    snapshot_sha256: snapshotSha,
    snapshot_rows: snapshot.draws.length,
    round_sequence_valid: true,
    main_and_bonus_validation: true,
    cutoff_safe_pre_draw_freeze: true,
    official_api_direct_retrieval: false
  };
  process.stdout.write(JSON.stringify(result,null,2)+"\n");
}
main();
