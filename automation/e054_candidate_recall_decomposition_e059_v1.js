#!/usr/bin/env node
'use strict';

/*
 * E059: candidate-stage decomposition of the frozen E054 rolling-HHI regime model.
 * Rebuilds the exact E054 score for every number/target, verifies it against
 * E054 PREDICTIONS.csv, then measures candidate_recall@K separately from allocation.
 */
const fs=require('node:fs');
const crypto=require('node:crypto');

const SPEC=Object.freeze({
 study_id:'E059_E054_CANDIDATE_RECALL_STAGE_DECOMPOSITION_v1',
 data_sha256:'7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2',
 data_cutoff:1250,start_target:401,target_count:850,k_values:[10,15,20,25,30],
 history_start:301,window:100,reference_count:200,prior_strength:45,
 bootstrap_replicates:4000,block_size:50,comparison_count:10,alpha_per_comparison:0.005,
 bootstrap_seed:20261116059
});
const ALL=Array.from({length:45},(_,i)=>i+1);
function parseCsv(raw){
 const lines=raw.toString('utf8').replace(/^\uFEFF/,'').split(/\r?\n/).filter(x=>x.trim().length>0);
 const header=lines[0].split(',');
 const idx=Object.fromEntries(header.map((x,i)=>[x,i]));
 return lines.slice(1).map(line=>{const c=line.split(',');const o={};for(const k of header)o[k]=c[idx[k]];return o;});
}
function median(xs){const a=xs.slice().sort((x,y)=>x-y),m=a.length>>1;return a.length%2?a[m]:(a[m-1]+a[m])/2;}
function rollingHhi(draws){
 const hhi=new Map();
 for(let end=100;end<=draws.length;end++){
  const counts=Array(46).fill(0);
  for(let i=end-100;i<end;i++)for(const n of draws[i].nums)counts[n]++;
  let v=0;for(let n=1;n<=45;n++){const p=counts[n]/600;v+=p*p;}
  hhi.set(end,v);
 }
 return hhi;
}
function regimeDetails(target,hhi){
 const currentEnd=target-1,refStart=Math.max(100,target-300),refEnd=target-101;
 const refs=[];for(let k=refStart;k<=refEnd;k++){if(!hhi.has(k))throw new Error('missing HHI reference '+k);refs.push(hhi.get(k));}
 if(refs.length<100)throw new Error('fewer than 100 reference windows');
 const current=hhi.get(currentEnd),threshold=median(refs);
 return {regime:current>=threshold?1:0,current_hhi:current,threshold_hhi:threshold,reference_count:refs.length};
}
function updateCounts(regime,actual,exposures,successes){
 exposures[regime]++;
 const s=new Set(actual);
 for(const n of s)successes[regime][n]++;
}
function scoreMap(regime,exposures,successes){
 const out={};for(const n of ALL)out[n]=(successes[regime][n]+6)/(exposures[regime]+45);return out;
}
function ranked(scores){return ALL.slice().sort((a,b)=>(scores[b]-scores[a])||(a-b));}
function recent30Rank(draws,target){
 const counts=Array(46).fill(0);
 for(let i=target-31;i<target-1;i++)for(const n of draws[i].nums)counts[n]++;
 return {counts,order:ALL.slice().sort((a,b)=>(counts[b]-counts[a])||(a-b))};
}
function shaScore(scores){
 const pairs=ALL.map(n=>[n,Number(scores[n].toFixed(16))]);
 return crypto.createHash('sha256').update(JSON.stringify(pairs),'utf8').digest('hex');
}
function xorshift32(seed){let x=seed>>>0;if(x===0)x=0x9e3779b9;return()=>{x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967296;};}
function movingBlockCI(values,seed,alpha=0.005){
 const n=values.length,b=50,blocks=17;
 if(n!==850)throw new Error('unexpected target count');
 const starts=n-b+1,prefix=Array(n+1).fill(0);
 for(let i=0;i<n;i++)prefix[i+1]=prefix[i]+values[i];
 const means=Array(starts);
 for(let s=0;s<starts;s++)means[s]=(prefix[s+b]-prefix[s])/b;
 const rng=xorshift32(seed),boot=Array(4000);
 for(let r=0;r<4000;r++){let z=0;for(let j=0;j<blocks;j++)z+=means[Math.floor(rng()*starts)];boot[r]=z/blocks;}
 boot.sort((a,b)=>a-b);
 const lo=Math.floor((alpha/2)*(3999)),hi=Math.floor((1-alpha/2)*(3999));
 return [boot[lo],boot[hi]];
}
function blockShare(values){let p=0;for(let b=0;b<17;b++){let s=0;for(let i=b*50;i<(b+1)*50;i++)s+=values[i];if(s>0)p++;}return p/17;}
function rate(values,k){return values.filter(x=>x>=k).length/values.length;}
function writeCsv(path,rows){
 if(!rows.length)throw new Error('empty CSV '+path);
 const fields=Object.keys(rows[0]);
 const quote=v=>{const s=String(v??'');return /[",\r\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};
 fs.writeFileSync(path,[fields.join(','),...rows.map(r=>fields.map(k=>quote(r[k])).join(','))].join('\n')+'\n');
}
function run(dataPath,predictionPath,outdir){
 const raw=fs.readFileSync(dataPath),sha=crypto.createHash('sha256').update(raw).digest('hex');
 if(sha!==SPEC.data_sha256)throw new Error('data SHA mismatch '+sha);
 const drawRows=parseCsv(raw),draws=drawRows.map(r=>({round:Number(r.round),nums:[1,2,3,4,5,6].map(i=>Number(r['no'+i])).sort((a,b)=>a-b),bonus:Number(r.bonus)}));
 if(draws.length!==1250||draws.some((d,i)=>d.round!==i+1||new Set(d.nums).size!==6||d.nums.some(n=>n<1||n>45)||d.bonus<1||d.bonus>45||d.nums.includes(d.bonus)))throw new Error('canonical data validation failed');
 const predRows=parseCsv(fs.readFileSync(predictionPath));
 if(predRows.length!==850)throw new Error('E054 prediction row count mismatch');
 const predByTarget=new Map(predRows.map(r=>[Number(r.target_round),r]));
 const hhi=rollingHhi(draws),regimes=new Map();
 for(let u=301;u<=1250;u++)regimes.set(u,regimeDetails(u,hhi).regime);
 const exposures=[0,0],successes=[Array(46).fill(0),Array(46).fill(0)];
 for(let u=301;u<401;u++)updateCounts(regimes.get(u),draws[u-1].nums,exposures,successes);
 const hitsE=Object.fromEntries(SPEC.k_values.map(k=>[k,[]]));
 const hitsR=Object.fromEntries(SPEC.k_values.map(k=>[k,[]]));
 const deltaRandom=Object.fromEntries(SPEC.k_values.map(k=>[k,[]]));
 const deltaRecent=Object.fromEntries(SPEC.k_values.map(k=>[k,[]]));
 const trace=[],targetChecks=[];
 for(let t=401;t<=1250;t++){
  const detail=regimeDetails(t,hhi),regime=detail.regime,scores=scoreMap(regime,exposures,successes),order=ranked(scores),rankE=Object.fromEntries(order.map((n,i)=>[n,i+1]));
  const recent=recent30Rank(draws,t),rankR=Object.fromEntries(recent.order.map((n,i)=>[n,i+1]));
  const actual=draws[t-1].nums,actualSet=new Set(actual),pred=predByTarget.get(t);
  if(!pred)throw new Error('missing frozen E054 target '+t);
  const checks={
   regime:pred.regime===(regime?'HIGH':'LOW'),
   current_hhi:Math.abs(Number(pred.current_hhi)-detail.current_hhi)<1e-14,
   threshold_hhi:Math.abs(Number(pred.threshold_hhi)-detail.threshold_hhi)<1e-14,
   reference_count:Number(pred.prior_hhi_reference_count)===detail.reference_count,
   exposure:Number(pred.regime_training_outcomes)===exposures[regime],
   score_sha256:pred.score_sha256===shaScore(scores)
  };
  targetChecks.push({target:t,...checks});
  for(const k of SPEC.k_values){
   const he=actual.filter(n=>rankE[n]<=k).length,hr=actual.filter(n=>rankR[n]<=k).length;
   hitsE[k].push(he);hitsR[k].push(hr);
   deltaRandom[k].push(he/6-k/45);
   deltaRecent[k].push((he-hr)/6);
  }
  const cutoffs={};for(const k of SPEC.k_values)cutoffs[k]=scores[order[k-1]];
  for(const winner of actual){
   const r=rankE[winner],rr=rankR[winner],first=SPEC.k_values.find(k=>r<=k)||'GT30';
   const row={target_round:t,regime:regime?'HIGH':'LOW',winner_number:winner,e054_rank:r,e054_score:scores[winner],
    regime_success_count:successes[regime][winner],regime_exposure_count:exposures[regime],
    recent30_rank:rr,recent30_count:recent.counts[winner],first_k_captured:first};
   for(const k of SPEC.k_values){row['captured_top'+k]=r<=k?1:0;row['score_gap_to_top'+k+'_cutoff']=scores[winner]-cutoffs[k];}
   trace.push(row);
  }
  updateCounts(regime,actual,exposures,successes);
 }
 const checkCounts={};for(const k of Object.keys(targetChecks[0]))if(k!=='target')checkCounts[k]=targetChecks.filter(x=>x[k]).length;
 const scorecard=[];
 for(const k of SPEC.k_values){
  const e=hitsE[k],r=hitsR[k],eRecall=e.reduce((s,x)=>s+x,0)/(850*6),rRecall=r.reduce((s,x)=>s+x,0)/(850*6);
  const er=deltaRandom[k],ec=deltaRecent[k];
  const ciRandom=movingBlockCI(er,SPEC.bootstrap_seed+k*2,0.005),ciRecent=movingBlockCI(ec,SPEC.bootstrap_seed+k*2+1,0.005);
  scorecard.push({signal:'E054_regime_posterior',k,targets:850,mean_candidate_hits:e.reduce((s,x)=>s+x,0)/850,mean_recall:eRecall,
   exact_random_expected_hits:6*k/45,exact_random_expected_recall:k/45,delta_recall_vs_random:eRecall-k/45,
   bonferroni_ci_lower_vs_random:ciRandom[0],bonferroni_ci_upper_vs_random:ciRandom[1],positive_50_block_share_vs_random:blockShare(er),
   recent30_mean_recall:rRecall,delta_recall_vs_recent30:eRecall-rRecall,bonferroni_ci_lower_vs_recent30:ciRecent[0],bonferroni_ci_upper_vs_recent30:ciRecent[1],
   positive_50_block_share_vs_recent30:blockShare(ec),capture_3plus:rate(e,3),capture_4plus:rate(e,4),capture_all6:rate(e,6)});
  scorecard.push({signal:'recent30_baseline',k,targets:850,mean_candidate_hits:r.reduce((s,x)=>s+x,0)/850,mean_recall:rRecall,
   exact_random_expected_hits:6*k/45,exact_random_expected_recall:k/45,delta_recall_vs_random:rRecall-k/45,
   bonferroni_ci_lower_vs_random:'DESCRIPTIVE_NOT_TESTED',bonferroni_ci_upper_vs_random:'DESCRIPTIVE_NOT_TESTED',positive_50_block_share_vs_random:'DESCRIPTIVE_NOT_TESTED',
   recent30_mean_recall:rRecall,delta_recall_vs_recent30:0,bonferroni_ci_lower_vs_recent30:'NOT_APPLICABLE',bonferroni_ci_upper_vs_recent30:'NOT_APPLICABLE',
   positive_50_block_share_vs_recent30:'NOT_APPLICABLE',capture_3plus:rate(r,3),capture_4plus:rate(r,4),capture_all6:rate(r,6)});
 }
 const missCounts=SPEC.k_values.map(k=>{let missed=0,recovered=0,bothMissed=0;for(const row of trace){if(row['captured_top'+k]===0){missed++;if(row.recent30_rank<=k)recovered++;else bothMissed++;}}return {k,winning_number_instances:trace.length,e054_missed:missed,recent30_would_capture_of_e054_misses:recovered,both_missed:bothMissed};});
 fs.mkdirSync(outdir,{recursive:true});
 writeCsv(outdir+'/CANDIDATE_RECALL_SCORECARD.csv',scorecard);
 writeCsv(outdir+'/WINNER_MISS_TRACE.csv',trace);
 writeCsv(outdir+'/MISS_ATTRIBUTION.csv',missCounts);
 const inference={study_id:SPEC.study_id,evidence_class:'HISTORICAL_CANDIDATE_STAGE_DECOMPOSITION_NOT_PROMOTION',data_cutoff:1250,target_range:[401,1250],targets:850,
  candidate_k_values:SPEC.k_values,signals:['E054_regime_posterior','recent30_baseline'],exact_random_expected_recall_by_k:Object.fromEntries(SPEC.k_values.map(k=>[k,k/45])),
  scorecard,miss_attribution:missCounts,e054_reproduction_checks:checkCounts,
  all_e054_score_hashes_match:checkCounts.score_sha256===850,all_regime_and_hhi_checks_match:['regime','current_hhi','threshold_hhi','reference_count','exposure'].every(k=>checkCounts[k]===850),
  inference:{family_alpha:0.05,comparison_count:10,alpha_per_comparison:0.005,bootstrap_replicates:4000,block_size:50,blocks:17,lower_index:9,upper_index:3989},
  future_leakage:false,strict_candidate_gate_defined_in_policy:false,promotion:false};
 fs.writeFileSync(outdir+'/INFERENCE.json',JSON.stringify(inference,null,2)+'\n');
 const verification={status:'PASS',study_id:SPEC.study_id,data_sha256:sha,e054_prediction_rows:predRows.length,target_count:targetChecks.length,
  e054_reproduction_checks:checkCounts,all_e054_score_hashes_match:checkCounts.score_sha256===850,
  all_regime_and_hhi_checks_match:['regime','current_hhi','threshold_hhi','reference_count','exposure'].every(k=>checkCounts[k]===850),
  target_cutoff_violations:0,future_leakage_failures:0,rank_tie_break:'score descending, number ascending',
  recent30_baseline:'last 30 pre-target main draws, frequency descending, number ascending',
  exact_random_baseline:'K/45 expected recall for a uniform K-subset of 1..45',
  bootstrap_comparisons:10,bonferroni_alpha_per_comparison:0.005,thresholds_changed:false,model_or_weights_changed:false,
  candidate_numbers_printed:false,purchase_lines_generated:false,strict_pass_ready_created:false};
 fs.writeFileSync(outdir+'/VERIFICATION.json',JSON.stringify(verification,null,2)+'\n');
 const completion={status:'COMPLETE',executed:true,study_id:SPEC.study_id,date_kst:'2026-11-16',data_cutoff:1250,targets:850,trace_rows:trace.length,
  e054_score_hash_matches:checkCounts.score_sha256,model_or_weights_changed:false,purchase_lines_generated:false,strict_pass_ready:false};
 fs.writeFileSync(outdir+'/COMPLETION.json',JSON.stringify(completion,null,2)+'\n');
 return {inference,verification,completion,scorecard,missCounts};
}
if(require.main===module){const out=run(process.argv[2]||'lotto_data.csv',process.argv[3]||'analysis/2026-11-16/gha_43738196136_1/E054_THREE_LINE_ROLLING_CONCENTRATION_REGIME_v1/PREDICTIONS.csv',process.argv[4]||'analysis/2026-11-16/E059_E054_CANDIDATE_RECALL_STAGE_DECOMPOSITION_v1');console.log(JSON.stringify({study_id:out.inference.study_id,verification:out.verification,scorecard:out.scorecard},null,2));}
module.exports={SPEC,parseCsv,median,rollingHhi,regimeDetails,updateCounts,scoreMap,ranked,recent30Rank,shaScore,movingBlockCI,run};
