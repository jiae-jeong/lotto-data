#!/usr/bin/env node
"use strict";
const fs = require("fs");
const crypto = require("crypto");
const path = require("path");
const DATA_PATH = "data/snapshots/lotto_data_through_1251_20261122.csv";
const OUT_DIR = "analysis/2026-11-23/E081_MIN_COMPONENT_RANK_RESCUE_v1";
const EXPECTED_DATA_SHA256 = "2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9";
const EXPECTED_DATA_BLOB_SHA = "be2fa07921a92f335aeb6e715b4f40098e297834";
function runE081(raw, metadata) {
  const K_VALUES = [10,15,20,25,30];
  const SIGNALS = ["recent30","gap","momentum","balanced","contrarian"];
  const TARGET_START = 401, TARGET_END = 1251, BLOCK = 50;
  const BOOTSTRAP_REPS = 4000;
  const SEEDS = {bootstrap:20261123081,candidate_random:20261123082,portfolio_random:20261123083};
  const NULL_REGISTERED = {
    max_hits:1.5142562485727544,
    any2:0.4749762432689262,
    any3:0.07135490714617204,
    any4:0.004180448026165553,
    any5:0.00008655553181928678,
    any6:3.68321411996965e-7,
    winning_union_coverage:2.4
  };
  const lines = raw.replace(/^\uFEFF/,"").split(/\r?\n/).filter(x=>x.trim().length);
  const header = lines[0].split(",");
  const expectedHeader = ["round","date","no1","no2","no3","no4","no5","no6","bonus"];
  if (JSON.stringify(header)!==JSON.stringify(expectedHeader)) throw new Error("CSV header mismatch");
  const rows = lines.slice(1).map(line=>{
    const p=line.split(",");
    if(p.length!==9) throw new Error("CSV field count mismatch");
    return {round:Number(p[0]),date:p[1],nums:p.slice(2,8).map(Number),bonus:Number(p[8])};
  });
  if(rows.length!==1251) throw new Error("Expected 1251 data rows");
  for(let i=0;i<rows.length;i++){
    const r=rows[i];
    if(r.round!==i+1) throw new Error("Round sequence gap/duplicate");
    if(r.nums.length!==6 || new Set(r.nums).size!==6 || !r.nums.every(n=>Number.isInteger(n)&&n>=1&&n<=45)) throw new Error("Invalid main numbers");
    if(!Number.isInteger(r.bonus)||r.bonus<1||r.bonus>45||r.nums.includes(r.bonus)) throw new Error("Invalid bonus");
  }
  function mean(xs){return xs.reduce((a,b)=>a+b,0)/xs.length;}
  function choose(n,k){
    if(k<0||k>n)return 0;
    let v=1; for(let i=1;i<=Math.min(k,n-k);i++)v=v*(n-Math.min(k,n-k)+i)/i;
    return v;
  }
  function zscore(obj){
    const vals=Object.values(obj), m=mean(vals), sd=Math.sqrt(mean(vals.map(x=>(x-m)**2)))||1;
    const out={}; for(const k of Object.keys(obj))out[k]=(obj[k]-m)/sd; return out;
  }
  function features(draws){
    const f30=Array(46).fill(0),f10=Array(46).fill(0),fprev20=Array(46).fill(0);
    for(const d of draws.slice(-30))for(const n of d)f30[n]++;
    for(const d of draws.slice(-10))for(const n of d)f10[n]++;
    for(const d of draws.slice(-30,-10))for(const n of d)fprev20[n]++;
    const gaps={};
    for(let n=1;n<=45;n++){let g=0;for(let i=draws.length-1;i>=0;i--){if(draws[i].includes(n))break;g++;}gaps[n]=g;}
    const recentRaw={},momentumRaw={},momentumExact={};
    for(let n=1;n<=45;n++){recentRaw[n]=f30[n];momentumRaw[n]=f10[n]/10-fprev20[n]/20;momentumExact[n]=2*f10[n]-fprev20[n];}
    const recent30=zscore(recentRaw),gap=zscore(gaps),momentum=zscore(momentumRaw);
    const balanced={},contrarian={},consensus={};
    for(let n=1;n<=45;n++){
      balanced[n]=(recent30[n]+gap[n])/2;
      contrarian[n]=(-recent30[n]+gap[n])/2;
      consensus[n]=(recent30[n]+gap[n]+momentum[n]+balanced[n]+contrarian[n])/5;
    }
    return {recent30,gap,momentum,momentumExact,balanced,contrarian,consensus};
  }
  function makeRank(score, exactScore){
    const order=Array.from({length:45},(_,i)=>i+1).sort((a,b)=>{
      const av=exactScore?exactScore[a]:score[a],bv=exactScore?exactScore[b]:score[b];
      return bv-av||a-b;
    });
    const rank={};order.forEach((n,i)=>rank[n]=i+1);return {order,rank};
  }
  function mulberry32(a){return function(){let t=a+=0x6D2B79F5;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};}
  function shuffle(a,rng){const x=a.slice();for(let i=x.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[x[i],x[j]]=[x[j],x[i]];}return x;}
  function portfolioMetrics(ticketLines,winners){
    const lineHits=ticketLines.map(line=>line.reduce((s,n)=>s+(winners.has(n)?1:0),0));
    const union=new Set(ticketLines.flat());
    let cov=0;for(const n of union)if(winners.has(n))cov++;
    const max=Math.max(...lineHits);
    return {line_hits:lineHits,max_hits:max,any2:max>=2?1:0,any3:max>=3?1:0,any4:max>=4?1:0,any5:max>=5?1:0,any6:max>=6?1:0,winning_union_coverage:cov};
  }
  function exactNull(){
    const den=choose(45,6);let totalP=0;
    const sums={max_hits:0,any2:0,any3:0,any4:0,any5:0,any6:0,winning_union_coverage:0};
    for(let a=0;a<=6;a++)for(let b=0;b<=6;b++)for(let c=0;c<=6;c++){
      const d=6-a-b-c;if(d<0||d>27)continue;
      const p=choose(6,a)*choose(6,b)*choose(6,c)*choose(27,d)/den;
      const mx=Math.max(a,b,c);totalP+=p;
      sums.max_hits+=mx*p;
      sums.any2+=(mx>=2?1:0)*p;sums.any3+=(mx>=3?1:0)*p;sums.any4+=(mx>=4?1:0)*p;
      sums.any5+=(mx>=5?1:0)*p;sums.any6+=(mx>=6?1:0)*p;
      sums.winning_union_coverage+=(a+b+c)*p;
    }
    return {probability_sum:totalP,...sums};
  }
  function quantile(xs,p){const a=xs.slice().sort((x,y)=>x-y);const h=(a.length-1)*p,lo=Math.floor(h),hi=Math.ceil(h);return a[lo]+(a[hi]-a[lo])*(h-lo);}
  function movingBlockCI(series,alpha,seed){
    const n=series.length, core= Math.floor(n/BLOCK)*BLOCK, fullBlocks=core/BLOCK, remainder=n-core;
    if(fullBlocks<1)throw new Error("No full blocks");
    const rng=mulberry32(seed>>>0), reps=[];
    for(let r=0;r<BOOTSTRAP_REPS;r++){
      let sum=0;
      for(let j=0;j<fullBlocks;j++){
        const start=Math.floor(rng()*(core-BLOCK+1));
        for(let k=0;k<BLOCK;k++)sum+=series[start+k];
      }
      if(remainder)sum+=series.slice(core).reduce((a,b)=>a+b,0);
      reps.push(sum/n);
    }
    return [quantile(reps,alpha/2),quantile(reps,1-alpha/2)];
  }
  function csv(rows,cols){const esc=v=>{const s=String(v);return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};return [cols.join(","),...rows.map(r=>cols.map(c=>esc(r[c]??"")).join(","))].join("\n")+"\n";}
  const nullCalc=exactNull();
  for(const k of Object.keys(NULL_REGISTERED))if(Math.abs(nullCalc[k]-NULL_REGISTERED[k])>1e-12)throw new Error("Exact null conformance mismatch: "+k);
  if(Math.abs(nullCalc.probability_sum-1)>1e-12)throw new Error("Exact null probabilities do not sum to one");
  const candidateRows=[],portfolioRows=[],randomCandidateRows=[],randomPortfolioRows=[],missTrace=[];
  const missBestCounts=Object.fromEntries(SIGNALS.map(s=>[s,0]));
  let leakageFailures=0,invalidPortfolio=0,traceMisses=0,traceWinners=0;
  const targets=rows.filter(r=>r.round>=TARGET_START&&r.round<=TARGET_END);
  for(const target of targets){
    const cutoff=target.round-1;
    const hist=rows.slice(0,cutoff).map(r=>r.nums);
    if(hist.length!==cutoff)leakageFailures++;
    const winners=new Set(target.nums),fs=features(hist),cr={};
    for(const signal of SIGNALS)cr[signal]=makeRank(fs[signal],signal==="momentum"?fs.momentumExact:null).rank;
    const minOrder=Array.from({length:45},(_,i)=>i+1).sort((a,b)=>{
      const amin=Math.min(...SIGNALS.map(s=>cr[s][a])),bmin=Math.min(...SIGNALS.map(s=>cr[s][b]));
      if(amin!==bmin)return amin-bmin;
      const asum=SIGNALS.reduce((z,s)=>z+cr[s][a],0),bsum=SIGNALS.reduce((z,s)=>z+cr[s][b],0);
      return asum-bsum||a-b;
    });
    const minRank={};minOrder.forEach((n,i)=>minRank[n]=i+1);
    const bordaOrder=Array.from({length:45},(_,i)=>i+1).sort((a,b)=>{
      const as=SIGNALS.reduce((z,s)=>z+cr[s][a],0),bs=SIGNALS.reduce((z,s)=>z+cr[s][b],0);
      return as-bs||a-b;
    });
    const bordaRank={};bordaOrder.forEach((n,i)=>bordaRank[n]=i+1);
    const consensusRank=makeRank(fs.consensus).rank;
    const orders={MIN_RANK:minOrder,BORDA:bordaOrder,CONSENSUS:Object.keys(consensusRank).map(Number).sort((a,b)=>consensusRank[a]-consensusRank[b])};
    const targetCandidate={target_round:target.round,training_through_round:cutoff};
    for(const model of Object.keys(orders)){
      const order=orders[model];
      for(const k of K_VALUES){
        const h=order.slice(0,k).filter(n=>winners.has(n)).length;
        candidateRows.push({target_round:target.round,model,k,hits:h,recall:h/6});
        targetCandidate[model+"_hits_at_"+k]=h;
      }
    }
    const lines3=[minOrder.slice(0,6),minOrder.slice(6,12),minOrder.slice(12,18)];
    const pairOverlap=[0,1,2].flatMap(i=>[i+1,i+2].filter(j=>j<3).map(j=>lines3[i].filter(n=>lines3[j].includes(n)).length));
    const geometryValid=lines3.every(x=>x.length===6&&new Set(x).size===6)&&new Set(lines3.flat()).size===18&&pairOverlap.every(x=>x===0);
    if(!geometryValid)invalidPortfolio++;
    const pm=portfolioMetrics(lines3,winners);
    const targetRandomCandidate={target_round:target.round};
    const cRng=mulberry32((SEEDS.candidate_random+target.round*1009)>>>0),cSum=Object.fromEntries(K_VALUES.map(k=>[k,0]));
    for(let rep=0;rep<200;rep++){
      const perm=shuffle(Array.from({length:45},(_,i)=>i+1),cRng);
      for(const k of K_VALUES)cSum[k]+=perm.slice(0,k).filter(n=>winners.has(n)).length;
    }
    for(const k of K_VALUES)targetRandomCandidate["random_hits_at_"+k]=cSum[k]/200;
    const pRng=mulberry32((SEEDS.portfolio_random+target.round*1013)>>>0);
    const pSum={max_hits:0,any2:0,any3:0,any4:0,any5:0,any6:0,winning_union_coverage:0};
    for(let rep=0;rep<120;rep++){
      const perm=shuffle(Array.from({length:45},(_,i)=>i+1),pRng);
      const m=portfolioMetrics([perm.slice(0,6),perm.slice(6,12),perm.slice(12,18)],winners);
      for(const k of Object.keys(pSum))pSum[k]+=m[k];
    }
    for(const k of Object.keys(pSum))pSum[k]/=120;
    randomCandidateRows.push(targetRandomCandidate);
    randomPortfolioRows.push({target_round:target.round,...pSum});
    portfolioRows.push({target_round:target.round,training_through_round:cutoff,...pm,line1_hits:pm.line_hits[0],line2_hits:pm.line_hits[1],line3_hits:pm.line_hits[2],pair_overlap_12:pairOverlap[0],pair_overlap_13:pairOverlap[1],pair_overlap_23:pairOverlap[2],union_size:18});
    const winnerNumbers=[...winners].sort((a,b)=>a-b);
    for(let slot=0;slot<winnerNumbers.length;slot++){
      const n=winnerNumbers[slot],best=SIGNALS.slice().sort((a,b)=>cr[a][n]-cr[b][n]||SIGNALS.indexOf(a)-SIGNALS.indexOf(b))[0];
      const selected=minRank[n]<=30;
      traceWinners++;
      if(!selected){traceMisses++;missBestCounts[best]++;}
      missTrace.push({target_round:target.round,winner_slot:slot+1,min_rank:minRank[n],borda_rank:bordaRank[n],consensus_rank:consensusRank[n],recent30_rank:cr.recent30[n],gap_rank:cr.gap[n],momentum_rank:cr.momentum[n],balanced_rank:cr.balanced[n],contrarian_rank:cr.contrarian[n],best_component:best,selected_top30:selected,miss_reason:selected?"IN_TOP30":"ALL_COMPONENT_RANKS_GT30"});
    }
    targetCandidate.minrank_max_hits=pm.max_hits;
    targetCandidate.minrank_any2=pm.any2;
    targetCandidate.minrank_any3=pm.any3;
    targetCandidate.minrank_any4=pm.any4;
    targetCandidate.minrank_any5=pm.any5;
    targetCandidate.minrank_any6=pm.any6;
    targetCandidate.minrank_union_coverage=pm.winning_union_coverage;
    targetCandidate.minrank_line1_hits=pm.line_hits[0];
    targetCandidate.minrank_line2_hits=pm.line_hits[1];
    targetCandidate.minrank_line3_hits=pm.line_hits[2];
    targetCandidate.minrank_overlap_12=pairOverlap[0];
    targetCandidate.minrank_overlap_13=pairOverlap[1];
    targetCandidate.minrank_overlap_23=pairOverlap[2];
    targetCandidate.union_size=18;
    targetCandidate.random_portfolio_max_hits=pSum.max_hits;
    targetCandidate.random_portfolio_any2=pSum.any2;
    targetCandidate.random_portfolio_any3=pSum.any3;
    targetCandidate.random_portfolio_any4=pSum.any4;
    targetCandidate.random_portfolio_any5=pSum.any5;
    targetCandidate.random_portfolio_any6=pSum.any6;
    targetCandidate.random_portfolio_union_coverage=pSum.winning_union_coverage;
    candidateRows.push({target_round:target.round,model:"_TARGET",k:0,hits:0,recall:0});
    targetCandidateRows.push(targetCandidate);
  }
  const n=targets.length;
  if(n!==851||leakageFailures!==0||invalidPortfolio!==0||traceWinners!==n*6)throw new Error("Target/cutoff/geometry completeness failure");
  const targetCandidateRows=[];
  const candidateSummary={};
  for(const model of ["MIN_RANK","BORDA","CONSENSUS"]){
    candidateSummary[model]={};
    for(const k of K_VALUES){
      const xs=candidateRows.filter(r=>r.model===model&&r.k===k);
      const hs=xs.map(r=>r.hits),recall=mean(hs)/6;
      const randomMean=mean(randomCandidateRows.map(r=>r["random_hits_at_"+k]));
      const row={targets:n,mean_hits:mean(hs),candidate_recall:recall,exact_random_expected_hits:6*k/45,exact_random_expected_recall:k/45,matched_random_mean_hits:randomMean,delta_recall_vs_exact_random:recall-k/45};
      if(model==="MIN_RANK"){
        const series=hs.map(h=>h/6-k/45);
        row.bonferroni_adjusted_moving_block_ci=movingBlockCI(series,0.01,SEEDS.bootstrap+k);
      }
      candidateSummary[model][k]=row;
    }
  }
  const exactPortfolioMetrics=["max_hits","any2","any3","any4","any5","any6","winning_union_coverage"];
  const portfolioSummary={};
  for(const model of ["MIN_RANK"]){
    const modelRows=portfolioRows;
    portfolioSummary[model]={};
    for(const metric of exactPortfolioMetrics){
      const observed=mean(modelRows.map(r=>r[metric]));
      const randomMean=mean(randomPortfolioRows.map(r=>r[metric]));
      const row={observed_mean:observed,exact_geometry_null:nullCalc[metric],delta_vs_exact_geometry_null:observed-nullCalc[metric],matched_random_mean:randomMean,delta_vs_matched_random:observed-randomMean};
      if(["max_hits","any2","any3","winning_union_coverage"].includes(metric)){
        const series=modelRows.map(r=>r[metric]-nullCalc[metric]);
        const idx=["max_hits","any2","any3","winning_union_coverage"].indexOf(metric);
        row.bonferroni_adjusted_moving_block_ci=movingBlockCI(series,0.0125,SEEDS.bootstrap+300+idx);
      }
      portfolioSummary[model][metric]=row;
    }
  }
  const baselinePortfolioSummary={};
  for(const model of ["BORDA","CONSENSUS"]){
    const modelRows=portfolioRows.map(r=>r);
    baselinePortfolioSummary[model]="RECOMPUTED_CANDIDATE_STAGE_ONLY; portfolio baseline is available from E080 on targets 401..1250 and is not re-estimated in this E081 runner.";
  }
  const maxDist=Array(7).fill(0),lineDist=Array(7).fill(0),unionDist=Array(7).fill(0);
  for(const r of portfolioRows){maxDist[r.max_hits]++;lineDist[r.line1_hits]++;lineDist[r.line2_hits]++;lineDist[r.line3_hits]++;unionDist[r.winning_union_coverage]++;}
  const fullBlocks=Math.floor(n/BLOCK),remainder=n-fullBlocks*BLOCK,blockStability=[];
  for(let b=0;b<fullBlocks;b++){
    const chunk=portfolioRows.slice(b*BLOCK,(b+1)*BLOCK),rate=mean(chunk.map(r=>r.any2));
    blockStability.push({block_type:"FULL_50",block_index:b+1,start_target:chunk[0].target_round,end_target:chunk[chunk.length-1].target_round,targets:chunk.length,any2_rate:rate,delta_vs_exact_null:rate-nullCalc.any2,positive:rate>nullCalc.any2});
  }
  if(remainder){
    const chunk=portfolioRows.slice(fullBlocks*BLOCK),rate=mean(chunk.map(r=>r.any2));
    blockStability.push({block_type:"FINAL_REMAINDER",block_index:fullBlocks+1,start_target:chunk[0].target_round,end_target:chunk[chunk.length-1].target_round,targets:chunk.length,any2_rate:rate,delta_vs_exact_null:rate-nullCalc.any2,positive:rate>nullCalc.any2});
  }
  const positiveBlocks=blockStability.filter(r=>r.block_type==="FULL_50"&&r.positive).length;
  const blockShare=positiveBlocks/fullBlocks;
  const gateCis=["max_hits","any2","any3","winning_union_coverage"].map(k=>portfolioSummary.MIN_RANK[k].bonferroni_adjusted_moving_block_ci);
  const historicalGatePass=gateCis.every(ci=>ci[0]>0)&&blockShare>=0.65;
  const results={
    study_id:"E081_MIN_COMPONENT_RANK_RESCUE_v1",
    evidence_class:"HISTORICAL_CUTOFF_SAFE_EXPLORATORY_DIAGNOSTIC_NOT_CLEAN_HOLDOUT_NOT_PROSPECTIVE",
    source:{path:metadata.source_path,cutoff:1251,rows:1251,sha256:metadata.source_sha256,git_blob_sha:metadata.source_blob_sha},
    code:{path:metadata.code_path,git_blob_sha:metadata.code_blob_sha},
    targets:{start:TARGET_START,end:TARGET_END,count:n,cutoff_rule:"target t uses only rounds 1..t-1",contaminated_live_history_rounds:[1244,1245,1246,1247,1248,1249,1250,1251],clean_holdout:false,prospective_confirmation:false},
    model:{name:"MIN_RANK",formula:"For each number, rank by the minimum of its five component rank positions; tie-break by the sum of the five ranks ascending, then number ascending.",signals:SIGNALS,parameter_search:false,allocator:"Top-18 MIN_RANK order split into ranks 1-6, 7-12, 13-18; exactly three disjoint lines."},
    candidate_stage:{k_values:K_VALUES,models:candidateSummary,miss_trace:{winner_instances:traceWinners,top30_misses:traceMisses,miss_rate:traceMisses/traceWinners,best_component_for_missed_winners:missBestCounts}},
    portfolio_stage:{exact_geometry_null:nullCalc,metrics:portfolioSummary.MIN_RANK,distributions:{max_hit_0_to_6:maxDist,line_hit_0_to_6:lineDist,union_coverage_0_to_6:unionDist},overlap_geometry:{pairwise_ticket_intersections:[0,0,0],union_size:18},any2_positive_50_target_blocks:{positive:positiveBlocks,total:fullBlocks,share:blockShare},block_stability: blockStability},
    strict_gate:{historical_portfolio_gate_pass:historicalGatePass,all_four_adjusted_ci_lower_bounds_gt_zero:gateCis.every(ci=>ci[0]>0),any2_positive_50_target_block_share_min:0.65,actual_share:blockShare,no_leakage:leakageFailures===0,prospective_confirmation:false,prospective_minimum_count_and_completion_rule:"UNSPECIFIED_IN_POLICY",strict_pass_ready:false},
    execution:{targets_valid:n,leakage_failures:leakageFailures,invalid_portfolios:invalidPortfolio,miss_trace_winners:traceWinners,random_candidate_sets:n*200,random_portfolios:n*120,bootstrap_replicates:BOOTSTRAP_REPS,block_length:BLOCK,full_blocks:fullBlocks,final_remainder_targets:remainder,exact_null_probability_sum:nullCalc.probability_sum,exact_null_matches_registered:true},
    decisions:{candidate_model_promoted:false,allocator_promoted:false,strict_pass_ready:false,purchase_lines_generated:false,candidate_numbers_in_output:false,top30_in_output:false}
  };
  const perTargetCols=["target_round","training_through_round","MIN_RANK_hits_at_10","MIN_RANK_hits_at_15","MIN_RANK_hits_at_20","MIN_RANK_hits_at_25","MIN_RANK_hits_at_30","BORDA_hits_at_10","BORDA_hits_at_15","BORDA_hits_at_20","BORDA_hits_at_25","BORDA_hits_at_30","CONSENSUS_hits_at_10","CONSENSUS_hits_at_15","CONSENSUS_hits_at_20","CONSENSUS_hits_at_25","CONSENSUS_hits_at_30","minrank_max_hits","minrank_any2","minrank_any3","minrank_any4","minrank_any5","minrank_any6","minrank_union_coverage","minrank_line1_hits","minrank_line2_hits","minrank_line3_hits","minrank_overlap_12","minrank_overlap_13","minrank_overlap_23","union_size","random_portfolio_max_hits","random_portfolio_any2","random_portfolio_any3","random_portfolio_any4","random_portfolio_any5","random_portfolio_any6","random_portfolio_union_coverage"];
  const perTargetCsv=csv(targetCandidateRows,perTargetCols);
  const missCsv=csv(missTrace,["target_round","winner_slot","min_rank","borda_rank","consensus_rank","recent30_rank","gap_rank","momentum_rank","balanced_rank","contrarian_rank","best_component","selected_top30","miss_reason"]);
  const blockCsv=csv(blockStability,["block_type","block_index","start_target","end_target","targets","any2_rate","delta_vs_exact_null","positive"]);
  const resultsJson=JSON.stringify(results,null,2)+"\n";
  return {results,resultsJson,perTargetCsv,missCsv,blockCsv};
}
function gitBlobSha1(s){const b=Buffer.from(s,"utf8");return crypto.createHash("sha1").update(Buffer.concat([Buffer.from("blob "+b.length+"\\0"),b])).digest("hex");}
const raw=fs.readFileSync(DATA_PATH,"utf8");
const sha=crypto.createHash("sha256").update(raw,"utf8").digest("hex");
const blob=gitBlobSha1(raw);
if(sha!==EXPECTED_DATA_SHA256||blob!==EXPECTED_DATA_BLOB_SHA)throw new Error("Source hash mismatch");
const out=runE081(raw,{source_path:DATA_PATH,source_sha256:sha,source_blob_sha:blob,code_path:"automation/e081_min_component_rank_rescue_v1.js",code_blob_sha:"FILL_AFTER_COMMIT"});
fs.mkdirSync(OUT_DIR,{recursive:true});
fs.writeFileSync(path.join(OUT_DIR,"RESULTS.json"),out.resultsJson);
fs.writeFileSync(path.join(OUT_DIR,"PER_TARGET_METRICS.csv"),out.perTargetCsv);
fs.writeFileSync(path.join(OUT_DIR,"WINNER_MISS_ATTRIBUTION.csv"),out.missCsv);
fs.writeFileSync(path.join(OUT_DIR,"BLOCK_STABILITY.csv"),out.blockCsv);
console.log(JSON.stringify(out.results.execution));
