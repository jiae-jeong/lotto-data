#!/usr/bin/env node
"use strict";

const fs = require("fs");
const pathLib = require("path");
const crypto = require("crypto");

const DATA_PATH = "lotto_data.csv";
const OUT_DIR = "analysis/2026-11-23/E080_BORDA_RANK_AGGREGATION_v1";
const TARGET_START = 401;
const TARGET_END = 1250;
const K_VALUES = [10, 15, 20, 25, 30];
const SIGNALS = ["recent30", "gap", "momentum", "balanced", "contrarian"];
const RANDOM_CANDIDATE_REPS = 200;
const RANDOM_PORTFOLIO_REPS = 120;
const BOOTSTRAP_REPS = 4000;
const BLOCK_LENGTH = 50;
const SEEDS = {
  bootstrap: 20261123080,
  candidate_random: 20261123081,
  portfolio_random: 20261123082
};
const NULL = {
  max_hits: 1.5142562485727544,
  any2: 0.4749762432689262,
  any3: 0.07135490714617204,
  any4: 0.004180448026165553,
  any5: 0.00008655553181928678,
  any6: 3.68321411996965e-7,
  winning_union_coverage: 2.4
};

function sha256(s) {
  return crypto.createHash("sha256").update(s, "utf8").digest("hex");
}
function gitBlobSha1(s) {
  const b = Buffer.from(s, "utf8");
  return crypto.createHash("sha1").update(Buffer.concat([Buffer.from("blob " + b.length + "\0"), b])).digest("hex");
}
function mulberry32(a) {
  return function() {
    let t = a += 0x6D2B79F5;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function shuffle(values, rng) {
  const a = values.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
function mean(xs) {
  return xs.reduce((a, b) => a + b, 0) / xs.length;
}
function quantile(xs, p) {
  const a = xs.slice().sort((x, y) => x - y);
  const h = (a.length - 1) * p;
  const lo = Math.floor(h), hi = Math.ceil(h);
  return a[lo] + (a[hi] - a[lo]) * (h - lo);
}
function zscore(values) {
  const xs = Object.values(values);
  const m = mean(xs);
  const sd = Math.sqrt(mean(xs.map(x => (x - m) ** 2))) || 1;
  const out = {};
  for (const k of Object.keys(values)) out[k] = (values[k] - m) / sd;
  return out;
}
function features(draws) {
  const f30 = Array(46).fill(0), f10 = Array(46).fill(0), fprev20 = Array(46).fill(0);
  for (const d of draws.slice(-30)) for (const n of d) f30[n]++;
  for (const d of draws.slice(-10)) for (const n of d) f10[n]++;
  for (const d of draws.slice(-30, -10)) for (const n of d) fprev20[n]++;
  const gaps = {};
  for (let n = 1; n <= 45; n++) {
    let g = 0;
    for (let i = draws.length - 1; i >= 0; i--) {
      if (draws[i].includes(n)) break;
      g++;
    }
    gaps[n] = g;
  }
  const recentRaw = {}, momentumRaw = {}, momentumExact = {};
  for (let n = 1; n <= 45; n++) {
    recentRaw[n] = f30[n];
    momentumRaw[n] = f10[n] / 10 - fprev20[n] / 20;
    momentumExact[n] = 2 * f10[n] - fprev20[n];
  }
  const recent30 = zscore(recentRaw);
  const gap = zscore(gaps);
  const momentum = zscore(momentumRaw);
  const balanced = {}, contrarian = {}, consensus = {};
  for (let n = 1; n <= 45; n++) {
    balanced[n] = (recent30[n] + gap[n]) / 2;
    contrarian[n] = (-recent30[n] + gap[n]) / 2;
    consensus[n] = (recent30[n] + gap[n] + momentum[n] + balanced[n] + contrarian[n]) / 5;
  }
  return {recent30, gap, momentum, momentumExact, balanced, contrarian, consensus};
}
function rankMap(score, exactScore) {
  const order = Array.from({length:45}, (_,i)=>i+1).sort((a,b) => {
    const av = exactScore ? exactScore[a] : score[a];
    const bv = exactScore ? exactScore[b] : score[b];
    return bv - av || a - b;
  });
  const ranks = {};
  order.forEach((n,i)=>{ranks[n]=i+1;});
  return {order, ranks};
}
function portfolioMetrics(lines, winners) {
  const lineHits = lines.map(line => line.reduce((s,n)=>s+(winners.has(n)?1:0),0));
  const union = new Set(lines.flat());
  let unionCoverage = 0;
  for (const n of union) if (winners.has(n)) unionCoverage++;
  const maxHit = Math.max(...lineHits);
  return {
    line_hits: lineHits,
    max_hits: maxHit,
    any2: maxHit >= 2 ? 1 : 0,
    any3: maxHit >= 3 ? 1 : 0,
    any4: maxHit >= 4 ? 1 : 0,
    any5: maxHit >= 5 ? 1 : 0,
    any6: maxHit >= 6 ? 1 : 0,
    winning_union_coverage: unionCoverage
  };
}
function bootstrapCI(series, alpha, seed) {
  const n = series.length;
  if (n % BLOCK_LENGTH !== 0) throw new Error("Target count must be divisible by block length in this preregistration.");
  const blocks = n / BLOCK_LENGTH;
  const rng = mulberry32(seed >>> 0);
  const reps = [];
  for (let b = 0; b < BOOTSTRAP_REPS; b++) {
    let sum = 0;
    for (let j = 0; j < blocks; j++) {
      const start = Math.floor(rng() * (n - BLOCK_LENGTH + 1));
      for (let k = 0; k < BLOCK_LENGTH; k++) sum += series[start + k];
    }
    reps.push(sum / n);
  }
  return [quantile(reps, alpha / 2), quantile(reps, 1 - alpha / 2)];
}
function summarizePortfolio(rows, metric) {
  const xs = rows.map(r => r[metric]);
  return mean(xs);
}
function csvEscape(v) {
  const s = String(v);
  return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}
function toCsv(rows, columns) {
  return [columns.join(","), ...rows.map(r => columns.map(c => csvEscape(r[c])).join(","))].join("\n") + "\n";
}
function ensure(condition, message) {
  if (!condition) throw new Error(message);
}

function main() {
  const raw = fs.readFileSync(DATA_PATH, "utf8");
  const dataSha = sha256(raw);
  const dataBlobSha = gitBlobSha1(raw);
  const lines = raw.replace(/^\uFEFF/, "").split(/\r?\n/).filter(x => x.trim().length > 0);
  const header = lines[0].split(",");
  const expectedHeader = ["round","date","no1","no2","no3","no4","no5","no6","bonus"];
  ensure(JSON.stringify(header) === JSON.stringify(expectedHeader), "Unexpected canonical CSV header.");
  const rows = lines.slice(1).map(line => {
    const p = line.split(",");
    ensure(p.length === 9, "Invalid CSV field count.");
    return {
      round: Number(p[0]),
      date: p[1],
      nums: p.slice(2,8).map(Number),
      bonus: Number(p[8])
    };
  });
  ensure(rows.length === 1250, "Canonical row count mismatch.");
  for (let i=0;i<rows.length;i++) {
    const r=rows[i];
    ensure(r.round === i+1, "Round sequence gap or duplicate at row " + (i+1));
    ensure(r.nums.length===6 && new Set(r.nums).size===6, "Invalid main numbers at round " + r.round);
    ensure(r.nums.every(n=>Number.isInteger(n)&&n>=1&&n<=45), "Out-of-range main number at round " + r.round);
    ensure(Number.isInteger(r.bonus)&&r.bonus>=1&&r.bonus<=45&&!r.nums.includes(r.bonus), "Invalid bonus at round " + r.round);
  }
  ensure(dataSha === "7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2", "Canonical data SHA-256 mismatch.");
  ensure(dataBlobSha === "66431d711919f179e4cb1349e2f7295c68a8735e", "Canonical Git blob SHA mismatch.");

  const candidateRows = [];
  const portfolioRows = [];
  const randomCandidateRows = [];
  const randomPortfolioRows = [];
  const missRows = [];
  const componentHitRows = [];
  const targetRows = rows.filter(r=>r.round>=TARGET_START&&r.round<=TARGET_END);

  for (const target of targetRows) {
    const hist = rows.slice(0, target.round-1).map(r=>r.nums);
    const winners = new Set(target.nums);
    const fscores = features(hist);
    const componentRanks = {};
    for (const signal of SIGNALS) {
      componentRanks[signal] = rankMap(fscores[signal], signal==="momentum" ? fscores.momentumExact : null).ranks;
    }
    const bordaScore = {};
    for (let n=1;n<=45;n++) bordaScore[n] = SIGNALS.reduce((s,signal)=>s+componentRanks[signal][n],0);
    const bordaOrder = Array.from({length:45},(_,i)=>i+1).sort((a,b)=>bordaScore[a]-bordaScore[b]||a-b);
    const consensusOrder = rankMap(fscores.consensus).order;
    const bordaRank = {}, consensusRank = {};
    bordaOrder.forEach((n,i)=>{bordaRank[n]=i+1;});
    consensusOrder.forEach((n,i)=>{consensusRank[n]=i+1;});
    const candidateHits = {};
    for (const model of ["BORDA","CONSENSUS"]) {
      const order = model==="BORDA" ? bordaOrder : consensusOrder;
      for (const k of K_VALUES) {
        const h = order.slice(0,k).filter(n=>winners.has(n)).length;
        candidateRows.push({target_round:target.round,model,k,hits:h,recall:h/6});
        candidateHits[model+"_"+k]=h;
      }
    }
    for (const n of target.nums) {
      missRows.push({
        target_round:target.round,
        winner:n,
        borda_rank:bordaRank[n],
        consensus_rank:consensusRank[n],
        recent30_rank:componentRanks.recent30[n],
        gap_rank:componentRanks.gap[n],
        momentum_rank:componentRanks.momentum[n],
        balanced_rank:componentRanks.balanced[n],
        contrarian_rank:componentRanks.contrarian[n],
        borda_rank_band:bordaRank[n]<=10?"1-10":bordaRank[n]<=15?"11-15":bordaRank[n]<=20?"16-20":bordaRank[n]<=25?"21-25":bordaRank[n]<=30?"26-30":"31-45"
      });
    }
    const bordaLines = [bordaOrder.slice(0,6),bordaOrder.slice(6,12),bordaOrder.slice(12,18)];
    const consensusLines = [consensusOrder.slice(0,6),consensusOrder.slice(6,12),consensusOrder.slice(12,18)];
    ensure(bordaLines.flat().length===18 && new Set(bordaLines.flat()).size===18, "Borda line geometry invalid.");
    ensure(consensusLines.flat().length===18 && new Set(consensusLines.flat()).size===18, "Consensus line geometry invalid.");
    const bMetrics = portfolioMetrics(bordaLines,winners);
    const cMetrics = portfolioMetrics(consensusLines,winners);
    portfolioRows.push({
      target_round:target.round,
      borda_max_hits:bMetrics.max_hits,
      borda_any2:bMetrics.any2,
      borda_any3:bMetrics.any3,
      borda_any4:bMetrics.any4,
      borda_any5:bMetrics.any5,
      borda_any6:bMetrics.any6,
      borda_union_coverage:bMetrics.winning_union_coverage,
      borda_line1_hits:bMetrics.line_hits[0],
      borda_line2_hits:bMetrics.line_hits[1],
      borda_line3_hits:bMetrics.line_hits[2],
      consensus_max_hits:cMetrics.max_hits,
      consensus_any2:cMetrics.any2,
      consensus_any3:cMetrics.any3,
      consensus_any4:cMetrics.any4,
      consensus_any5:cMetrics.any5,
      consensus_any6:cMetrics.any6,
      consensus_union_coverage:cMetrics.winning_union_coverage
    });

    const cRng = mulberry32((SEEDS.candidate_random + target.round * 1009) >>> 0);
    const cSums = Object.fromEntries(K_VALUES.map(k=>[k,0]));
    for (let rep=0;rep<RANDOM_CANDIDATE_REPS;rep++) {
      const perm = shuffle(Array.from({length:45},(_,i)=>i+1),cRng);
      for (const k of K_VALUES) cSums[k] += perm.slice(0,k).filter(n=>winners.has(n)).length;
    }
    for (const k of K_VALUES) randomCandidateRows.push({target_round:target.round,k,mean_hits:cSums[k]/RANDOM_CANDIDATE_REPS});

    const pRng = mulberry32((SEEDS.portfolio_random + target.round * 1013) >>> 0);
    const pSums = {max_hits:0,any2:0,any3:0,any4:0,any5:0,any6:0,winning_union_coverage:0};
    for (let rep=0;rep<RANDOM_PORTFOLIO_REPS;rep++) {
      const perm=shuffle(Array.from({length:45},(_,i)=>i+1),pRng);
      const lines3=[perm.slice(0,6),perm.slice(6,12),perm.slice(12,18)];
      const m=portfolioMetrics(lines3,winners);
      for (const k of Object.keys(pSums)) pSums[k]+=m[k];
    }
    for (const k of Object.keys(pSums)) pSums[k]/=RANDOM_PORTFOLIO_REPS;
    randomPortfolioRows.push({target_round:target.round,...pSums});
  }

  const n=targetRows.length;
  ensure(n===850 && n%BLOCK_LENGTH===0, "Unexpected target count/block remainder.");
  const candidateSummary = {};
  const candidateComparisons = [];
  for (const model of ["BORDA","CONSENSUS"]) {
    candidateSummary[model]={};
    for (const k of K_VALUES) {
      const xs=candidateRows.filter(r=>r.model===model&&r.k===k);
      const hits=xs.map(r=>r.hits);
      const randomMean=mean(randomCandidateRows.filter(r=>r.k===k).map(r=>r.mean_hits));
      const exactHits=6*k/45;
      const exactRecall=k/45;
      const deltaSeries=hits.map(h=>h/6-exactRecall);
      const alpha=0.005;
      const ci=bootstrapCI(deltaSeries,alpha,SEEDS.bootstrap+(model==="BORDA"?0:100)+k);
      candidateSummary[model][k]={
        targets:n,
        mean_hits:mean(hits),
        candidate_recall:mean(hits)/6,
        exact_random_expected_hits:exactHits,
        exact_random_expected_recall:exactRecall,
        delta_recall_vs_exact_random:mean(deltaSeries),
        matched_random_mean_hits:randomMean,
        adjusted_ci_vs_exact_random:ci
      };
    }
  }
  for (const k of K_VALUES) {
    const b=candidateRows.filter(r=>r.model==="BORDA"&&r.k===k).map(r=>r.hits);
    const c=candidateRows.filter(r=>r.model==="CONSENSUS"&&r.k===k).map(r=>r.hits);
    const diff=b.map((h,i)=>(h-c[i])/6);
    candidateComparisons.push({k,delta_recall_borda_minus_consensus:mean(diff),inference:"DESCRIPTIVE_ONLY_NOT_A_SEPARATE_TEST"});
  }

  const metricMap={
    max_hits:"max_hits",
    any2:"any2",
    any3:"any3",
    winning_union_coverage:"winning_union_coverage"
  };
  const portfolioSummary={BORDA:{},CONSENSUS:{}};
  const strictIntervals={};
  for (const model of ["BORDA","CONSENSUS"]) {
    for (const [metric,key] of Object.entries(metricMap)) {
      const observed=portfolioRows.map(r=>r[metric==="winning_union_coverage"?(model==="BORDA"?"borda_union_coverage":"consensus_union_coverage"):(model==="BORDA"?"borda_"+key:"consensus_"+key)]);
      const nullValue=NULL[metric];
      const delta=observed.map(x=>x-nullValue);
      const summary={
        observed_mean:mean(observed),
        exact_geometry_matched_null:nullValue,
        delta_mean:mean(delta)
      };
      if(model==="BORDA") {
        const ci=bootstrapCI(delta,0.0125,SEEDS.bootstrap+300+Object.keys(metricMap).indexOf(metric));
        summary.adjusted_moving_block_ci=ci;
        strictIntervals[metric]=ci;
      }
      portfolioSummary[model][metric]=summary;
    }
  }
  const blockRows=[];
  for (const model of ["BORDA","CONSENSUS"]) {
    for (let start=0;start<n;start+=BLOCK_LENGTH) {
      const subset=portfolioRows.slice(start,start+BLOCK_LENGTH);
      const row={model,block_index:start/BLOCK_LENGTH+1,target_start:subset[0].target_round,target_end:subset[subset.length-1].target_round,n:subset.length};
      for (const [metric,key] of Object.entries(metricMap)) {
        const prefix=model==="BORDA"?"borda_":"consensus_";
        const col=metric==="winning_union_coverage"?prefix+"union_coverage":prefix+key;
        row["delta_"+metric]=mean(subset.map(r=>r[col]))-NULL[metric];
      }
      row.any2_positive=row.delta_any2>0;
      blockRows.push(row);
    }
  }
  const bordaBlocks=blockRows.filter(r=>r.model==="BORDA");
  const any2PositiveBlocks=bordaBlocks.filter(r=>r.any2_positive).length;
  const any2PositiveShare=any2PositiveBlocks/bordaBlocks.length;

  const maxHitDist=Array(7).fill(0), lineHitDist=Array(7).fill(0), unionDist=Array(7).fill(0);
  for (const r of portfolioRows) {
    maxHitDist[r.borda_max_hits]++;
    lineHitDist[r.borda_line1_hits]++; lineHitDist[r.borda_line2_hits]++; lineHitDist[r.borda_line3_hits]++;
    unionDist[r.borda_union_coverage]++;
  }
  const randomPortfolioMean={};
  for (const key of Object.keys(NULL)) randomPortfolioMean[key]=mean(randomPortfolioRows.map(r=>r[key]));
  const ciAllPositive=Object.values(strictIntervals).every(ci=>ci[0]>0);
  const strictHistoricalGatePass=ciAllPositive&&any2PositiveShare>=0.65;
  const verification={
    study_id:"E080_BORDA_RANK_AGGREGATION_v1",
    data_path:DATA_PATH,
    data_rows:rows.length,
    round_sequence_valid:true,
    main_number_validation:"PASS",
    bonus_validation:"PASS",
    data_sha256:dataSha,
    data_git_blob_sha:dataBlobSha,
    code_path:__filename,
    code_sha256:sha256(fs.readFileSync(__filename,"utf8")),
    target_range:[TARGET_START,TARGET_END],
    target_count:n,
    cutoff_rule:"Each target t uses only draws <= t-1.",
    cutoff_violations:0,
    contaminated_rounds:[1244,1245,1246,1247,1248,1249],
    clean_holdout:false,
    prospective_confirmation:false,
    candidate_random_sets:RANDOM_CANDIDATE_REPS*n,
    portfolio_random_bundles:RANDOM_PORTFOLIO_REPS*n,
    matched_random_geometry_preserved:true,
    line_geometry:"Three disjoint six-number lines, union18, fixed top18 rank partition",
    geometry_violations:0,
    bootstrap_replicates:BOOTSTRAP_REPS,
    block_length:BLOCK_LENGTH,
    block_count:n/BLOCK_LENGTH,
    final_remainder_targets:0,
    candidate_family_comparisons:10,
    candidate_alpha_per_comparison:0.005,
    portfolio_family_alpha:0.05,
    portfolio_alpha_per_metric:0.0125,
    no_future_leakage:true,
    strict_historical_gate_pass:strictHistoricalGatePass,
    strict_pass_ready:false,
    no_candidate_or_purchase_lines_released:true
  };
  const results={
    study_id:"E080_BORDA_RANK_AGGREGATION_v1",
    evidence_class:"HISTORICAL_CUTOFF_SAFE_CANDIDATE_AND_FIXED_ALLOCATOR_DIAGNOSTIC_NOT_CLEAN_HOLDOUT_NOT_PROSPECTIVE",
    source:{path:DATA_PATH,cutoff:1250,rows:rows.length,sha256:dataSha,git_blob_sha:dataBlobSha},
    hypothesis:{
      candidate_model:"Equal-weight Borda rank aggregation of recent30, gap, momentum, balanced, contrarian component rankings.",
      ranking_rule:"For each number, sum its five component rank positions; lower sum ranks first; lower number breaks ties.",
      stable_baseline:"Existing candidate_recall_v1.py consensus score, unchanged.",
      allocator:"Top 18 candidates partitioned by rank into lines 1-6, 7-12, 13-18; exactly three disjoint lines."
    },
    candidate_recall:{k_values:K_VALUES,models:candidateSummary,borda_minus_consensus:candidateComparisons},
    exact_geometry_matched_null:NULL,
    portfolio:{
      means:portfolioSummary,
      max_hit_distribution_0_to_6:maxHitDist,
      all_line_hit_distribution_0_to_6:lineHitDist,
      union_coverage_distribution_0_to_6:unionDist,
      matched_random_means:randomPortfolioMean,
      any2_positive_50_target_blocks:any2PositiveBlocks,
      total_50_target_blocks:bordaBlocks.length,
      any2_positive_block_share:any2PositiveShare,
      strict_adjusted_ci_borda:strictIntervals,
      strict_historical_gate_pass:strictHistoricalGatePass,
      prospective_confirmation:false,
      strict_pass_ready:false
    },
    decision:{
      candidate_model_promotion:false,
      allocator_promotion:false,
      strict_pass_ready:false,
      prospective_confirmation:false,
      purchase_lines_generated:false
    }
  };

  fs.mkdirSync(OUT_DIR,{recursive:true});
  fs.writeFileSync(pathLib.join(OUT_DIR,"RESULTS.json"),JSON.stringify(results,null,2)+"\n");
  fs.writeFileSync(pathLib.join(OUT_DIR,"VERIFICATION.json"),JSON.stringify(verification,null,2)+"\n");
  fs.writeFileSync(pathLib.join(OUT_DIR,"CANDIDATE_RECALL.csv"),toCsv(candidateRows,["target_round","model","k","hits","recall"]));
  fs.writeFileSync(pathLib.join(OUT_DIR,"PORTFOLIO_PREDICTIONS.csv"),toCsv(portfolioRows,Object.keys(portfolioRows[0])));
  fs.writeFileSync(pathLib.join(OUT_DIR,"CANDIDATE_RANDOM_BASELINE.csv"),toCsv(randomCandidateRows,Object.keys(randomCandidateRows[0])));
  fs.writeFileSync(pathLib.join(OUT_DIR,"PORTFOLIO_RANDOM_BASELINE.csv"),toCsv(randomPortfolioRows,Object.keys(randomPortfolioRows[0])));
  fs.writeFileSync(pathLib.join(OUT_DIR,"BLOCK_STABILITY.csv"),toCsv(blockRows,Object.keys(blockRows[0])));
  fs.writeFileSync(pathLib.join(OUT_DIR,"WINNER_MISS_TRACE.csv"),toCsv(missRows,Object.keys(missRows[0])));
  const manifest={};
  for (const name of fs.readdirSync(OUT_DIR).filter(x=>x.endsWith(".csv")||x.endsWith(".json"))) {
    const content=fs.readFileSync(pathLib.join(OUT_DIR,name),"utf8");
    manifest[name]={sha256:sha256(content),bytes:Buffer.byteLength(content,"utf8")};
  }
  fs.writeFileSync(pathLib.join(OUT_DIR,"SHA256_MANIFEST.json"),JSON.stringify(manifest,null,2)+"\n");
  console.log(JSON.stringify({results,verification},null,2));
}
main();
