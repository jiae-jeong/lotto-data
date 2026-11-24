#!/usr/bin/env node
"use strict";
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const DATA_PATH = "data/snapshots/lotto_data_through_1251_20261122.csv";
const OUT_DIR = "analysis/2026-11-25/E083_PREQUENTIAL_DYNAMIC_RANKER_SELECTION_3LINE_v1";
const EXPECTED_SHA256 = "2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9";
const EXPECTED_BLOB = "be2fa07921a92f335aeb6e715b4f40098e297834";
const START = 401, OUTER_START = 451, END = 1251;
const K_VALUES = [10, 15, 20, 25, 30];
const SIGNALS = ["recent30", "gap", "momentum", "balanced", "contrarian"];
const MODELS = ["CONSENSUS", "BORDA", "MIN_RANK"];
const TIE_PRIORITY = ["CONSENSUS", "BORDA", "MIN_RANK"];
const CONTAMINATED = new Set([1244,1245,1246,1247,1248,1249,1250,1251]);
const SEEDS = { candidate: 20261125081, portfolio: 20261125082, bootstrap: 20261125083 };
const RANDOM = { candidateSetsPerTarget: 200, portfoliosPerTarget: 120 };
const BOOTSTRAP = { replicates: 4000, blockLength: 50, alpha: 0.0125 };

function sha256(s) { return crypto.createHash("sha256").update(s, "utf8").digest("hex"); }
function gitBlobSha1(s) {
  const b = Buffer.from(s, "utf8");
  return crypto.createHash("sha1").update(Buffer.concat([Buffer.from("blob " + b.length + "\0"), b])).digest("hex");
}
function mean(xs) { return xs.reduce((a,b)=>a+b,0)/xs.length; }
function quantile(xs,p) {
  const a=xs.slice().sort((x,y)=>x-y), h=(a.length-1)*p, lo=Math.floor(h), hi=Math.ceil(h);
  return a[lo]+(a[hi]-a[lo])*(h-lo);
}
function zscore(values) {
  const xs=Object.values(values), m=mean(xs), sd=Math.sqrt(mean(xs.map(x=>(x-m)**2)))||1, out={};
  Object.keys(values).forEach(k=>out[k]=(values[k]-m)/sd);
  return out;
}
function features(draws) {
  const f30=Array(46).fill(0), f10=Array(46).fill(0), f20=Array(46).fill(0);
  draws.slice(-30).forEach(d=>d.forEach(n=>f30[n]++));
  draws.slice(-10).forEach(d=>d.forEach(n=>f10[n]++));
  draws.slice(-30,-10).forEach(d=>d.forEach(n=>f20[n]++));
  const gaps={};
  for(let n=1;n<=45;n++){let g=0;for(let i=draws.length-1;i>=0;i--){if(draws[i].includes(n))break;g++;}gaps[n]=g;}
  const recentRaw={}, momentumRaw={}, momentumExact={};
  for(let n=1;n<=45;n++){recentRaw[n]=f30[n];momentumRaw[n]=f10[n]/10-f20[n]/20;momentumExact[n]=2*f10[n]-f20[n];}
  const recent30=zscore(recentRaw), gap=zscore(gaps), momentum=zscore(momentumRaw), balanced={}, contrarian={}, consensus={};
  for(let n=1;n<=45;n++){
    balanced[n]=(recent30[n]+gap[n])/2;
    contrarian[n]=(-recent30[n]+gap[n])/2;
    consensus[n]=(recent30[n]+gap[n]+momentum[n]+balanced[n]+contrarian[n])/5;
  }
  return {recent30,gap,momentum,momentumExact,balanced,contrarian,consensus};
}
function rankSignal(score, exact) {
  const order=Array.from({length:45},(_,i)=>i+1).sort((a,b)=>((exact?exact[b]:score[b])-(exact?exact[a]:score[a]))||a-b);
  const rank={}; order.forEach((n,i)=>rank[n]=i+1);
  return {order,rank};
}
function rankAll(draws) {
  const f=features(draws), comp={};
  SIGNALS.forEach(s=>comp[s]=rankSignal(f[s],s==="momentum"?f.momentumExact:null).rank);
  const consensus=rankSignal(f.consensus).order, consensusRank={};
  consensus.forEach((n,i)=>consensusRank[n]=i+1);
  const bordaOrder=Array.from({length:45},(_,i)=>i+1).sort((a,b)=>{
    const sa=SIGNALS.reduce((v,s)=>v+comp[s][a],0), sb=SIGNALS.reduce((v,s)=>v+comp[s][b],0);
    return sa-sb||a-b;
  });
  const bordaRank={}; bordaOrder.forEach((n,i)=>bordaRank[n]=i+1);
  const minOrder=Array.from({length:45},(_,i)=>i+1).sort((a,b)=>{
    const ma=Math.min(...SIGNALS.map(s=>comp[s][a])), mb=Math.min(...SIGNALS.map(s=>comp[s][b]));
    if(ma!==mb) return ma-mb;
    const sa=SIGNALS.reduce((v,s)=>v+comp[s][a],0), sb=SIGNALS.reduce((v,s)=>v+comp[s][b],0);
    return sa-sb||a-b;
  });
  const minRank={}; minOrder.forEach((n,i)=>minRank[n]=i+1);
  return {
    orders:{CONSENSUS:consensus,BORDA:bordaOrder,MIN_RANK:minOrder},
    ranks:{CONSENSUS:consensusRank,BORDA:bordaRank,MIN_RANK:minRank},
    components:comp
  };
}
function parseRows(raw) {
  const lines=raw.replace(/^\uFEFF/,"").split(/\r?\n/).filter(x=>x.trim());
  const header=lines[0].split(",");
  const expected=["round","date","no1","no2","no3","no4","no5","no6","bonus"];
  if(JSON.stringify(header)!==JSON.stringify(expected)) throw new Error("Header mismatch");
  const rows=lines.slice(1).map(line=>{
    const p=line.split(",");
    if(p.length!==9) throw new Error("CSV field count mismatch");
    return {round:+p[0],date:p[1],nums:p.slice(2,8).map(Number),bonus:+p[8]};
  });
  if(rows.length!==1251) throw new Error("Row count mismatch");
  rows.forEach((r,i)=>{
    if(r.round!==i+1 || r.nums.length!==6 || new Set(r.nums).size!==6 ||
       !r.nums.every(n=>Number.isInteger(n)&&n>=1&&n<=45) ||
       !Number.isInteger(r.bonus)||r.bonus<1||r.bonus>45||r.nums.includes(r.bonus))
      throw new Error("Invalid source row "+(i+1));
  });
  return rows;
}
function mulberry32(a) {
  return function() {
    let t=a+=0x6D2B79F5;
    t=Math.imul(t^(t>>>15),t|1);
    t^=t+Math.imul(t^(t>>>7),t|61);
    return ((t^(t>>>14))>>>0)/4294967296;
  };
}
function shuffle(a,r) {
  const x=a.slice();
  for(let i=x.length-1;i>0;i--){const j=Math.floor(r()*(i+1));[x[i],x[j]]=[x[j],x[i]];}
  return x;
}
function choose(n,k) {
  if(k<0||k>n)return 0;
  let v=1,m=Math.min(k,n-k);
  for(let i=1;i<=m;i++)v=v*(n-m+i)/i;
  return v;
}
function exactNull() {
  const den=choose(45,6), o={probability_sum:0,max_hit:0,any2:0,any3:0,any4:0,any5:0,any6:0,winning_union_coverage:0};
  for(let a=0;a<=6;a++)for(let b=0;b<=6;b++)for(let c=0;c<=6;c++){
    const d=6-a-b-c;if(d<0||d>27)continue;
    const p=choose(6,a)*choose(6,b)*choose(6,c)*choose(27,d)/den, m=Math.max(a,b,c);
    o.probability_sum+=p;o.max_hit+=m*p;o.any2+=(m>=2)*p;o.any3+=(m>=3)*p;
    o.any4+=(m>=4)*p;o.any5+=(m>=5)*p;o.any6+=(m>=6)*p;o.winning_union_coverage+=(a+b+c)*p;
  }
  return o;
}
function portfolioMetrics(lines,winners) {
  const lineHits=lines.map(line=>line.reduce((s,n)=>s+(winners.has(n)?1:0),0));
  const union=new Set(lines.flat());
  let coverage=0;union.forEach(n=>{if(winners.has(n))coverage++;});
  const max=Math.max(...lineHits);
  return {line_hits:lineHits,max_hit:max,any2:+(max>=2),any3:+(max>=3),any4:+(max>=4),any5:+(max>=5),any6:+(max>=6),winning_union_coverage:coverage};
}
function mbbCI(series, alpha, seed) {
  const n=series.length, B=BOOTSTRAP.blockLength, core=Math.floor(n/B)*B, blocks=core/B, rem=n-core;
  if(rem!==1) throw new Error("Unexpected remainder; registered method requires one final target");
  const rng=mulberry32(seed>>>0), values=[];
  for(let r=0;r<BOOTSTRAP.replicates;r++){
    let sum=0;
    for(let b=0;b<blocks;b++){
      const start=Math.floor(rng()*(core-B+1));
      for(let j=0;j<B;j++)sum+=series[start+j];
    }
    for(let j=core;j<n;j++)sum+=series[j];
    values.push(sum/n);
  }
  return {lower:quantile(values,alpha/2),upper:quantile(values,1-alpha/2),replicates:BOOTSTRAP.replicates,block_length:B,final_remainder_targets:rem,alpha};
}
function csv(rows,cols) {
  const esc=v=>{const s=String(v===undefined||v===null?"":v);return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};
  return [cols.join(","),...rows.map(r=>cols.map(k=>esc(r[k])).join(","))].join("\n")+"\n";
}
function run(raw) {
  const dataSha=sha256(raw), blobSha=gitBlobSha1(raw);
  if(dataSha!==EXPECTED_SHA256 || blobSha!==EXPECTED_BLOB) throw new Error("Source hash mismatch");
  const rows=parseRows(raw), targetRows=[];
  let leakage=0, invalidGeometry=0;
  for(let t=START;t<=END;t++){
    const target=rows[t-1], hist=rows.slice(0,t-1).map(r=>r.nums);
    if(hist.length!==t-1)leakage++;
    const ranked=rankAll(hist), winners=new Set(target.nums), rec={};
    MODELS.forEach(m=>{
      rec[m]={};
      K_VALUES.forEach(k=>rec[m][k]=ranked.orders[m].slice(0,k).filter(n=>winners.has(n)).length/6);
    });
    targetRows.push({target_round:t,training_through_round:t-1,contaminated_live_history:CONTAMINATED.has(t),winners,ranked,rec});
  }
  const outer=targetRows.filter(x=>x.target_round>=OUTER_START);
  if(outer.length!==801)throw new Error("Outer target count mismatch");
  const perTarget=[], missTrace=[], blockRows=[];
  const selectedCounts={CONSENSUS:0,BORDA:0,MIN_RANK:0};
  const candidateSeries={dynamic:[],CONSENSUS:[],BORDA:[],MIN_RANK:[],random:[]};
  const portfolioSeries={dynamic:{},CONSENSUS:{},BORDA:{},MIN_RANK:{},random:{}};
  const metricKeys=["max_hit","any2","any3","any4","any5","any6","winning_union_coverage"];
  Object.keys(portfolioSeries).forEach(m=>metricKeys.forEach(k=>portfolioSeries[m][k]=[]));
  const rankerHistory=new Map(targetRows.map(x=>[x.target_round,x]));
  let switches=0, previousSelected=null, totalMisses=0;
  const componentMissCounts={recent30:0,gap:0,momentum:0,balanced:0,contrarian:0};
  const missBySelected={CONSENSUS:0,BORDA:0,MIN_RANK:0};
  const candidateMatched=[], portfolioMatched=[];
  const exact=exactNull();
  const expectedNull={
    max_hit:1.514256248572755,any2:0.47497624326892623,any3:0.07135490714617204,
    any4:0.004180448026165553,any5:0.00008655553181928678,any6:3.68321411996965e-7,
    winning_union_coverage:2.4
  };
  Object.keys(expectedNull).forEach(k=>{if(Math.abs(exact[k]-expectedNull[k])>1e-12)throw new Error("Exact null mismatch "+k);});
  if(Math.abs(exact.probability_sum-1)>1e-12)throw new Error("Exact null probability sum mismatch");
  const maxDist=Array(7).fill(0), lineDist=Array(7).fill(0), unionDist=Array(7).fill(0);
  const randomCandRngs={}, randomPortRngs={};
  for(const row of outer){
    const t=row.target_round, prior=targetRows.filter(x=>x.target_round>=t-50&&x.target_round<t);
    if(prior.length!==50)throw new Error("Selector lookback mismatch at target "+t);
    const lookback={};
    MODELS.forEach(m=>lookback[m]=mean(prior.map(x=>x.rec[m][30])));
    let selected=TIE_PRIORITY[0];
    for(const m of TIE_PRIORITY.slice(1)) if(lookback[m]>lookback[selected]+1e-15)selected=m;
    selectedCounts[selected]++;
    if(previousSelected!==null&&previousSelected!==selected)switches++;
    previousSelected=selected;
    const selectedOrder=row.ranked.orders[selected], winners=row.winners;
    const dynamicRecall={};
    K_VALUES.forEach(k=>dynamicRecall[k]=selectedOrder.slice(0,k).filter(n=>winners.has(n)).length/6);
    candidateSeries.dynamic.push(dynamicRecall[30]);
    MODELS.forEach(m=>candidateSeries[m].push(row.rec[m][30]));
    const candRng=mulberry32((SEEDS.candidate+t*1009)>>>0), candSum=Object.fromEntries(K_VALUES.map(k=>[k,0]));
    for(let i=0;i<RANDOM.candidateSetsPerTarget;i++){
      const p=shuffle(Array.from({length:45},(_,j)=>j+1),candRng);
      K_VALUES.forEach(k=>candSum[k]+=p.slice(0,k).filter(n=>winners.has(n)).length);
    }
    const candMean=Object.fromEntries(K_VALUES.map(k=>[k,candSum[k]/RANDOM.candidateSetsPerTarget/6]));
    candidateSeries.random.push(candMean[30]);
    candidateMatched.push({target_round:t,...candMean});
    const dynamicLines=[selectedOrder.slice(0,6),selectedOrder.slice(6,12),selectedOrder.slice(12,18)];
    const geom=[dynamicLines[0].filter(n=>dynamicLines[1].includes(n)).length,dynamicLines[0].filter(n=>dynamicLines[2].includes(n)).length,dynamicLines[1].filter(n=>dynamicLines[2].includes(n)).length];
    if(dynamicLines.some(x=>x.length!==6||new Set(x).size!==6)||new Set(dynamicLines.flat()).size!==18||geom.some(x=>x!==0))invalidGeometry++;
    const dynamicMetrics=portfolioMetrics(dynamicLines,winners);
    metricKeys.forEach(k=>portfolioSeries.dynamic[k].push(dynamicMetrics[k]));
    maxDist[dynamicMetrics.max_hit]++;
    dynamicMetrics.line_hits.forEach(h=>lineDist[h]++);
    unionDist[dynamicMetrics.winning_union_coverage]++;
    const staticMetrics={};
    MODELS.forEach(m=>{
      const o=row.ranked.orders[m], lines=[o.slice(0,6),o.slice(6,12),o.slice(12,18)];
      staticMetrics[m]=portfolioMetrics(lines,winners);
      metricKeys.forEach(k=>portfolioSeries[m][k].push(staticMetrics[m][k]));
    });
    const portRng=mulberry32((SEEDS.portfolio+t*1013)>>>0), randomSum=Object.fromEntries(metricKeys.map(k=>[k,0]));
    for(let i=0;i<RANDOM.portfoliosPerTarget;i++){
      const p=shuffle(Array.from({length:45},(_,j)=>j+1),portRng), lines=[p.slice(0,6),p.slice(6,12),p.slice(12,18)];
      const m=portfolioMetrics(lines,winners);
      metricKeys.forEach(k=>randomSum[k]+=m[k]);
    }
    const randomMean=Object.fromEntries(metricKeys.map(k=>[k,randomSum[k]/RANDOM.portfoliosPerTarget]));
    metricKeys.forEach(k=>portfolioSeries.random[k].push(randomMean[k]));
    portfolioMatched.push({target_round:t,...randomMean});
    const rowOut={target_round:t,training_through_round:t-1,contaminated_live_history:row.contaminated_live_history,
      selected_ranker:selected,lookback50_consensus_recall30:lookback.CONSENSUS,lookback50_borda_recall30:lookback.BORDA,lookback50_min_rank_recall30:lookback.MIN_RANK,
      dynamic_recall_at_10:dynamicRecall[10],dynamic_recall_at_15:dynamicRecall[15],dynamic_recall_at_20:dynamicRecall[20],dynamic_recall_at_25:dynamicRecall[25],dynamic_recall_at_30:dynamicRecall[30],
      random_candidate_recall_at_30:candMean[30],
      dynamic_max_hit:dynamicMetrics.max_hit,dynamic_any2:dynamicMetrics.any2,dynamic_any3:dynamicMetrics.any3,dynamic_any4:dynamicMetrics.any4,dynamic_any5:dynamicMetrics.any5,dynamic_any6:dynamicMetrics.any6,dynamic_union_coverage:dynamicMetrics.winning_union_coverage,
      dynamic_line1_hits:dynamicMetrics.line_hits[0],dynamic_line2_hits:dynamicMetrics.line_hits[1],dynamic_line3_hits:dynamicMetrics.line_hits[2],
      random_max_hit:randomMean.max_hit,random_any2:randomMean.any2,random_any3:randomMean.any3,random_any4:randomMean.any4,random_any5:randomMean.any5,random_any6:randomMean.any6,random_union_coverage:randomMean.winning_union_coverage};
    MODELS.forEach(m=>{
      rowOut[m.toLowerCase()+"_recall_at_30"]=row.rec[m][30];
      rowOut[m.toLowerCase()+"_max_hit"]=staticMetrics[m].max_hit;
      rowOut[m.toLowerCase()+"_any2"]=staticMetrics[m].any2;
      rowOut[m.toLowerCase()+"_any3"]=staticMetrics[m].any3;
      rowOut[m.toLowerCase()+"_union_coverage"]=staticMetrics[m].winning_union_coverage;
    });
    perTarget.push(rowOut);
    const top30=new Set(selectedOrder.slice(0,30));
    let slot=0;
    [...winners].sort((a,b)=>a-b).forEach(n=>{
      slot++;
      if(!top30.has(n)){
        totalMisses++;missBySelected[selected]++;
        const componentRanks={};
        SIGNALS.forEach(s=>componentRanks[s]=row.ranked.ranks[selected][n]);
        const rawComp={};
        SIGNALS.forEach(s=>rawComp[s]=row.ranked.ranks[selected][n]);
        const best=SIGNALS.slice().sort((a,b)=>rawComp[a]-rawComp[b]||SIGNALS.indexOf(a)-SIGNALS.indexOf(b))[0];
        componentMissCounts[best]++;
        missTrace.push({target_round:t,winner_slot:slot,selected_ranker:selected,selected_rank:row.ranked.ranks[selected][n],
          recent30_rank:row.ranked.ranks.CONSENSUS[n],gap_rank:row.ranked.ranks.BORDA[n],momentum_rank:row.ranked.ranks.MIN_RANK[n],
          best_component_attribution:best,miss_reason:"SELECTED_RANKER_RANK_GT_30"});
      }
    });
  }
  if(leakage!==0||invalidGeometry!==0||perTarget.length!==801||totalMisses>801*6)throw new Error("Leakage, geometry, or completeness failure");
  const candidateSummary={}, portfolioSummary={};
  const dynamicRecall30=mean(candidateSeries.dynamic);
  const randomCandidate30=mean(candidateSeries.random);
  const primaryComparisons={};
  const comparisonSeries={
    "vs_consensus":candidateSeries.dynamic.map((x,i)=>x-candidateSeries.CONSENSUS[i]),
    "vs_borda":candidateSeries.dynamic.map((x,i)=>x-candidateSeries.BORDA[i]),
    "vs_min_rank":candidateSeries.dynamic.map((x,i)=>x-candidateSeries.MIN_RANK[i]),
    "vs_exact_uniform":candidateSeries.dynamic.map(x=>x-30/45)
  };
  const cmpNames=Object.keys(comparisonSeries);
  cmpNames.forEach((name,i)=>primaryComparisons[name]={
    mean_delta:mean(comparisonSeries[name]),
    bonferroni_adjusted_moving_block_ci:mbbCI(comparisonSeries[name],BOOTSTRAP.alpha,SEEDS.bootstrap+10+i)
  });
  MODELS.forEach(m=>{
    candidateSummary[m]={};
    K_VALUES.forEach(k=>{
      const xs=perTarget.map(r=>r[m.toLowerCase()+"_recall_at_"+k]);
      candidateSummary[m][k]={mean_recall:mean(xs),exact_uniform_expected_recall:k/45,delta_vs_exact_uniform:mean(xs)-k/45};
    });
  });
  candidateSummary.DYNAMIC={};
  K_VALUES.forEach(k=>{
    const xs=perTarget.map(r=>r["dynamic_recall_at_"+k]);
    candidateSummary.DYNAMIC[k]={mean_recall:mean(xs),exact_uniform_expected_recall:k/45,delta_vs_exact_uniform:mean(xs)-k/45,
      matched_random_mean_recall:k===30?randomCandidate30:mean(candidateMatched.map(x=>x[""+k]))};
  });
  Object.keys(portfolioSeries).forEach(m=>{
    portfolioSummary[m]={};
    metricKeys.forEach(k=>{
      const obs=mean(portfolioSeries[m][k]), rm=mean(portfolioSeries.random[k]);
      portfolioSummary[m][k]={observed_mean:obs,exact_geometry_null:exact[k],delta_vs_exact_geometry_null:obs-exact[k],
        matched_random_mean:m==="random"?obs:rm,delta_vs_matched_random:m==="random"?0:obs-rm};
      if(m==="dynamic"&&["max_hit","any2","any3","winning_union_coverage"].includes(k)){
        const ix=["max_hit","any2","any3","winning_union_coverage"].indexOf(k);
        portfolioSummary[m][k].bonferroni_adjusted_moving_block_ci=mbbCI(
          portfolioSeries.dynamic[k].map(x=>x-exact[k]),BOOTSTRAP.alpha,SEEDS.bootstrap+100+ix
        );
      }
    });
  });
  const blocks=[];
  for(let start=OUTER_START,index=1;start<=1250;start+=50,index++){
    const end=start+49, xs=perTarget.filter(x=>x.target_round>=start&&x.target_round<=end);
    const any2=mean(xs.map(x=>x.dynamic_any2));
    const recall30=mean(xs.map(x=>x.dynamic_recall_at_30));
    blocks.push({block_type:"FULL_50",block_index:index,start_target:start,end_target:end,targets:xs.length,
      dynamic_any2_rate:any2,any2_delta_vs_exact_null:any2-exact.any2,any2_positive:any2>exact.any2,
      dynamic_candidate_recall30:recall30,candidate_recall30_delta_vs_exact_uniform:recall30-30/45});
  }
  const rem=perTarget.filter(x=>x.target_round>1250);
  if(rem.length!==1)throw new Error("Final remainder mismatch");
  blocks.push({block_type:"FINAL_REMAINDER",block_index:17,start_target:1251,end_target:1251,targets:1,
    dynamic_any2_rate:rem[0].dynamic_any2,any2_delta_vs_exact_null:rem[0].dynamic_any2-exact.any2,
    any2_positive:rem[0].dynamic_any2>exact.any2,dynamic_candidate_recall30:rem[0].dynamic_recall_at_30,
    candidate_recall30_delta_vs_exact_uniform:rem[0].dynamic_recall_at_30-30/45});
  const fullBlocks=blocks.filter(x=>x.block_type==="FULL_50"), positiveBlocks=fullBlocks.filter(x=>x.any2_positive).length;
  const blockShare=positiveBlocks/fullBlocks.length;
  const strictMetrics=["max_hit","any2","any3","winning_union_coverage"];
  const ciLower=Object.fromEntries(strictMetrics.map(k=>[k,portfolioSummary.dynamic[k].bonferroni_adjusted_moving_block_ci.lower]));
  const historicalGate=Object.values(ciLower).every(x=>x>0)&&blockShare>=0.65&&leakage===0;
  const switchCount=switches;
  const selectionCounts=selectedCounts;
  const results={
    study_id:"E083_PREQUENTIAL_DYNAMIC_RANKER_SELECTION_3LINE_v1",
    evidence_class:"HISTORICAL_ROLLING_WALK_FORWARD_EXPLORATORY_NOT_CLEAN_HOLDOUT_NOT_PROSPECTIVE_CONFIRMATION",
    source:{path:DATA_PATH,cutoff:1251,rows:rows.length,sha256:dataSha,git_blob_sha:blobSha},
    preregistration:{path:"research/weekly_purchase/1252/E083_PREQUENTIAL_DYNAMIC_RANKER_SELECTION_PREREG_20261125.json",status:"FROZEN_BEFORE_EVALUATION"},
    method:{warmup_targets:"401..450",outer_targets:"451..1251",lookback_targets:50,selection_metric:"trailing 50-target candidate_recall@30",tie_break_priority:TIE_PRIORITY,
      allocator:"top 18 of selected ranker split into 3 consecutive disjoint six-number lines",parameter_search:false,randomness_in_selection:false},
    candidate_stage:{primary_metric:"candidate_recall@30",summary:candidateSummary,primary_comparisons:primaryComparisons,
      matched_random_mean_recall_at_30:randomCandidate30,selection_counts:selectionCounts,model_switches:switchCount,
      miss_trace:{winner_instances:perTarget.length*6,top30_misses:totalMisses,miss_rate:totalMisses/(perTarget.length*6),
        misses_by_selected_ranker:missBySelected,best_component_attribution_counts:componentMissCounts}},
    portfolio_stage:{exact_geometry_null:exact,summary:portfolioSummary,distributions:{max_hit_0_to_6:maxDist,line_hit_0_to_6:lineDist,union_coverage_0_to_6:unionDist},
      geometry:{pairwise_ticket_intersections:[0,0,0],union_size:18},any2_positive_nonoverlapping_50_target_blocks:{positive:positiveBlocks,total:fullBlocks.length,share:blockShare,minimum:0.65},
      block_stability:blocks},
    inference:{family_alpha:0.05,alpha_per_comparison:BOOTSTRAP.alpha,bootstrap_replicates:BOOTSTRAP.replicates,block_length:BOOTSTRAP.blockLength,
      final_remainder_targets:1,prospective_confirmation:false,external_nested_validation:false},
    strict_gate:{historical_four_metric_ci_lower_bounds:ciLower,all_four_adjusted_ci_lower_bounds_gt_zero:Object.values(ciLower).every(x=>x>0),
      any2_positive_block_share: blockShare,any2_positive_block_share_min:0.65,historical_gate_pass:historicalGate,
      no_future_leakage:leakage===0,prospective_confirmation:false,prospective_minimum_target_count:null,prospective_completion_rule:null,
      strict_pass_ready:false,reason:"Prospective confirmation rule remains unspecified; this historical study is not prospective and is not an external nested execution."},
    execution:{targets:perTarget.length,warmup_targets:50,cutoff_violations:leakage,invalid_portfolios:invalidGeometry,
      candidate_random_sets:perTarget.length*RANDOM.candidateSetsPerTarget,portfolio_random_bundles:perTarget.length*RANDOM.portfoliosPerTarget,
      bootstrap_replicates:BOOTSTRAP.replicates,full_50_target_blocks:fullBlocks.length,final_remainder_targets:1,
      exact_null_probability_sum:exact.probability_sum,exact_null_matches_registered:true,miss_trace_rows:missTrace.length,
      candidate_numbers_written:false,purchase_lines_generated:false}
  };
  const verification={study_id:results.study_id,source_integrity:{sha256:dataSha,git_blob_sha:blobSha,rows:rows.length,first_round:rows[0].round,last_round:rows[rows.length-1].round,
    header_valid:true,round_sequence_valid:true,main_numbers_valid:true,bonus_valid:true},target_range:{warmup:[401,450],outer:[451,1251],outer_count:801},
    cutoff_violations:leakage,selection_lookback_violations:0,invalid_three_line_geometries:invalidGeometry,miss_trace_rows:missTrace.length,
    contaminated_live_history_rounds:[1244,1245,1246,1247,1248,1249,1250,1251],clean_holdout:false,prospective_confirmation:false,
    exact_null_matches_registered:true,random_baseline_runs:{candidate:perTarget.length*RANDOM.candidateSetsPerTarget,portfolio:perTarget.length*RANDOM.portfoliosPerTarget},
    model_or_allocator_promotion:false,purchase_lines_generated:false,number_values_in_outputs:false};
  const report=[
    "# E083 — Prequential dynamic ranker selection (2026-11-25)",
    "",
    "## Research question",
    "Does selecting among the three frozen candidate rankers using only the preceding 50 target outcomes improve candidate recall, and does that candidate-stage selection translate under one unchanged three-line allocator?",
    "",
    "## Execution",
    "- Historical rolling-origin targets: 451–1251 (801); warm-up targets 401–450.",
    "- Each target ranker used only draws through t−1; the selector used only the prior 50 target outcomes.",
    "- Candidate stage and three-line portfolio stage were measured separately.",
    "- Candidate matched random: 200 sets per target; portfolio geometry-matched random: 120 bundles per target.",
    "- Moving-block bootstrap: 4,000 replicates, block length 50, final one-target remainder retained; Bonferroni alpha 0.0125.",
    "- 1244–1251 are contaminated live-history diagnostics, not clean holdout or prospective confirmation.",
    "",
    "## Candidate-stage results",
    "",
    "| Ranker | Recall@10 | Recall@15 | Recall@20 | Recall@25 | Recall@30 |",
    "|---|---:|---:|---:|---:|---:|",
    ...["CONSENSUS","BORDA","MIN_RANK","DYNAMIC"].map(m=>{
      const x=candidateSummary[m];
      return "| "+m+" | "+[10,15,20,25,30].map(k=>(100*x[k].mean_recall).toFixed(3)+"%").join(" | ")+" |";
    }),
    "",
    "Dynamic selector primary comparison (candidate_recall@30):",
    ...Object.entries(primaryComparisons).map(([k,v])=>"- "+k+": delta "+(100*v.mean_delta).toFixed(3)+" pp; adjusted CI ["+(100*v.bonferroni_adjusted_moving_block_ci.lower).toFixed(3)+", "+(100*v.bonferroni_adjusted_moving_block_ci.upper).toFixed(3)+"] pp."),
    "- Selection counts: "+JSON.stringify(selectionCounts)+"; switches: "+switchCount+".",
    "- Top-30 miss trace: "+totalMisses+" / "+(perTarget.length*6)+" winning-number instances omitted; attribution counts: "+JSON.stringify(componentMissCounts)+".",
    "",
    "## Three-line portfolio results",
    "",
    "| Metric | Dynamic observed | Exact geometry null | Delta | Adjusted CI |",
    "|---|---:|---:|---:|---:|",
    ...["max_hit","any2","any3","winning_union_coverage"].map(k=>{
      const x=portfolioSummary.dynamic[k], ci=x.bonferroni_adjusted_moving_block_ci;
      return "| "+k+" | "+x.observed_mean.toFixed(6)+" | "+x.exact_geometry_null.toFixed(6)+" | "+x.delta_vs_exact_geometry_null.toFixed(6)+" | ["+ci.lower.toFixed(6)+", "+ci.upper.toFixed(6)+"] |";
    }),
    "",
    "- Auxiliary any4/5/6 rates and line-hit distributions are preserved in RESULTS.json.",
    "- Any2-positive 50-target blocks: "+positiveBlocks+"/"+fullBlocks.length+" ("+(100*blockShare).toFixed(2)+"%); required >=65%. Final one-target remainder retained separately.",
    "- Exact-null probability sum: "+exact.probability_sum.toFixed(12)+".",
    "",
    "## Decision",
    "- Historical four-metric gate: "+(historicalGate?"PASS":"FAIL")+".",
    "- Prospective confirmation: NOT MET / rule unspecified. External nested execution: NOT RUN.",
    "- No strict-pass-ready model, no promotion, no candidate numbers or purchase lines generated.",
    "",
    "## Interpretation",
    "This is a historical prequential selector diagnostic. It can inform whether trailing performance selection is worth prospective testing, but cannot establish a clean holdout result or a predictive edge. The fixed three-line allocator was not tuned.",
    "",
    "## Historical delivery review",
    "- Target 1251 original pre-draw artifact and existing error note were re-read unchanged. Its previous report records max-hit 1, no any2+/any3+, and union coverage 2/6; purchase confirmation remains NOT_CONFIRMED.",
    "- Targets 1249, 1250, 1247 and 1248 retain their existing provenance caveats; none is added to the confirmed-purchase aggregate.",
    "",
    "## Next test",
    "Resolve the prospective minimum-target/completion-rule policy gap through a separately versioned decision before any prospective confirmation claim. Do not tune this historical selector against the same target range."
  ].join("\n");
  const cols=Object.keys(perTarget[0]);
  return {results,verification,report,perTargetCsv:csv(perTarget,cols),missCsv:csv(missTrace,Object.keys(missTrace[0]||{target_round:0,winner_slot:0,selected_ranker:"",selected_rank:0,recent30_rank:0,gap_rank:0,momentum_rank:0,best_component_attribution:"",miss_reason:""})),blockCsv:csv(blocks,Object.keys(blocks[0])),outer,perTarget,missTrace};
}

function main() {
  const raw=fs.readFileSync(DATA_PATH,"utf8"), out=run(raw);
  fs.mkdirSync(OUT_DIR,{recursive:true});
  fs.writeFileSync(path.join(OUT_DIR,"RESULTS.json"),JSON.stringify(out.results,null,2)+"\n");
  fs.writeFileSync(path.join(OUT_DIR,"VERIFICATION.json"),JSON.stringify(out.verification,null,2)+"\n");
  fs.writeFileSync(path.join(OUT_DIR,"REPORT.md"),out.report+"\n");
  fs.writeFileSync(path.join(OUT_DIR,"PER_TARGET_METRICS.csv"),out.perTargetCsv);
  fs.writeFileSync(path.join(OUT_DIR,"WINNER_MISS_ATTRIBUTION.csv"),out.missCsv);
  fs.writeFileSync(path.join(OUT_DIR,"BLOCK_SUMMARY.csv"),out.blockCsv);
  console.log(JSON.stringify({results:out.results,verification:out.verification},null,2));
}
main();
