#!/usr/bin/env node
"use strict";
const fs = require("fs");
const crypto = require("crypto");
const dataPath = "lotto_data.csv";
const scorePath = "analysis/2026-11-17/CANDIDATE_RECALL_SCORECARD.csv";
const outputPath = "analysis/2026-11-17/E065_CANDIDATE_RECALL_UNCERTAINTY_AUDIT_V2_EXACT_MOMENTUM.json";
const raw = fs.readFileSync(dataPath, "utf8");
const dataSha = crypto.createHash("sha256").update(raw, "utf8").digest("hex");
const expectedSha = "7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2";
if (dataSha !== expectedSha) throw new Error("Canonical data SHA-256 mismatch");
const physical = raw.replace(/^\uFEFF/, "").split(/\r?\n/);
const lines = physical.filter(x => x.trim().length > 0);
const draws = lines.slice(1).map(line => {
  const p = line.split(",");
  return { round: Number(p[0]), nums: p.slice(2,8).map(Number), bonus: Number(p[8]) };
});
if (draws.length !== 1250) throw new Error("Expected 1250 rows");
draws.forEach((d,i) => {
  if (d.round !== i+1 || d.nums.length !== 6 || new Set(d.nums).size !== 6 ||
      d.nums.some(n => n < 1 || n > 45) || d.bonus < 1 || d.bonus > 45 || d.nums.includes(d.bonus)) {
    throw new Error("Data integrity failure at round " + (i+1));
  }
});
const K=[10,15,20,25,30], SIGNALS=["recent30","gap","momentum","balanced","contrarian","consensus"];
function zscore(o) {
  const v=Object.values(o), mean=v.reduce((a,b)=>a+b,0)/v.length;
  const sd=Math.sqrt(v.reduce((s,x)=>s+(x-mean)**2,0)/v.length)||1;
  const out={}; for(let n=1;n<=45;n++) out[n]=(o[n]-mean)/sd;
  return out;
}
function features(hist) {
  const f30={},f10={},f20={},gapCounts={};
  for(let n=1;n<=45;n++) f30[n]=f10[n]=f20[n]=gapCounts[n]=0;
  for(const d of hist.slice(-30)) for(const n of d.nums) f30[n]++;
  for(const d of hist.slice(-10)) for(const n of d.nums) f10[n]++;
  for(const d of hist.slice(-30,-10)) for(const n of d.nums) f20[n]++;
  for(let n=1;n<=45;n++) for(let j=hist.length-1;j>=0;j--) { if(hist[j].nums.includes(n)) break; gapCounts[n]++; }
  const recent30=zscore(f30), gap=zscore(gapCounts);
  const momentum=zscore(Object.fromEntries(Array.from({length:45},(_,i)=>[i+1,f10[i+1]/10-f20[i+1]/20])));
  const momentumExact=Object.fromEntries(Array.from({length:45},(_,i)=>[i+1,2*f10[i+1]-f20[i+1]]));
  const balanced={},contrarian={},consensus={};
  for(let n=1;n<=45;n++) {
    balanced[n]=(recent30[n]+gap[n])/2;
    contrarian[n]=(-recent30[n]+gap[n])/2;
    consensus[n]=(recent30[n]+gap[n]+momentum[n]+balanced[n]+contrarian[n])/5;
  }
  return {recent30,gap,momentum,momentumExact,balanced,contrarian,consensus};
}
function rng(seed) { let x=seed>>>0; return () => { x^=x<<13; x^=x>>>17; x^=x<<5; return (x>>>0)/4294967296; }; }
const hitsByKey={}; for(const s of SIGNALS) for(const k of K) hitsByKey[s+"|"+k]=[];
for(let i=200;i<draws.length;i++) {
  const fs=features(draws.slice(0,i)), actual=new Set(draws[i].nums);
  for(const s of SIGNALS) {
    const order=Array.from({length:45},(_,j)=>j+1).sort((a,b)=>s==="momentum" ? (fs.momentumExact[b]-fs.momentumExact[a]||a-b) : (fs[s][b]-fs[s][a]||a-b));
    const rank={}; order.forEach((n,j)=>rank[n]=j+1);
    for(const k of K) hitsByKey[s+"|"+k].push([...actual].filter(n=>rank[n]<=k).length);
  }
}
const scoreLines=fs.readFileSync(scorePath,"utf8").replace(/^\uFEFF/,"").split(/\r?\n/).filter(x=>x.trim());
const score={}; for(const line of scoreLines.slice(1)) { const p=line.split(","); score[p[0]+"|"+p[1]]=Number(p[4]); }
const reps=20000, block=50, blocks=21, family=30, tail=0.05/(2*family), results=[];
let testIndex=0;
for(const s of SIGNALS) for(const k of K) {
  const h=hitsByKey[s+"|"+k], recall=h.map(x=>x/6), delta=h.map(x=>x/6-k/45), blockMeans=[];
  for(let b=0;b<blocks;b++) blockMeans.push(delta.slice(b*block,(b+1)*block).reduce((a,x)=>a+x,0)/block);
  const mean=recall.reduce((a,x)=>a+x,0)/recall.length, point=mean-k/45;
  const r=rng(20261117065+testIndex*100003), boot=new Array(reps);
  for(let b=0;b<reps;b++) { let sum=0; for(let j=0;j<blocks;j++) sum+=blockMeans[Math.floor(r()*blocks)]; boot[b]=sum/blocks; }
  boot.sort((a,b)=>a-b);
  const lo=boot[Math.floor(tail*(reps-1))], hi=boot[Math.ceil((1-tail)*(reps-1))];
  results.push({signal:s,k,targets:h.length,mean_recall:mean,exact_random_recall:k/45,delta_pp:point*100,bonferroni_ci_pp:[lo*100,hi*100],positive_50_target_blocks:blockMeans.filter(x=>x>0).length,total_50_target_blocks:blocks,scorecard_mean_recall:score[s+"|"+k],scorecard_reproduction_error_pp:Math.abs(mean-score[s+"|"+k])*100});
  testIndex++;
}
const mismatch=results.filter(x=>x.scorecard_reproduction_error_pp>1e-8);
const out={study_id:"E065_CANDIDATE_RECALL_UNCERTAINTY_AUDIT_v2_EXACT_MOMENTUM",data_sha256:dataSha,data_cutoff:1250,target_range:[201,1250],targets:1050,physical_blank_lines:physical.filter(x=>!x.trim()).length,signals:SIGNALS,k_values:K,exact_random_expected_recall:Object.fromEntries(K.map(k=>[k,k/45])),bootstrap:{block_length:50,blocks:21,remainder:0,reps_per_test:reps,family_tests:30,family_alpha:0.05,per_test_two_sided_alpha:0.05/30,tail_quantiles:[tail,1-tail],seed_rule:"xorshift32: 20261117065 + test_index*100003"},scorecard_reproduction:{matched_rows:30-mismatch.length,mismatches:mismatch},results,momentum_ranking:{formula:"2*count(last10)-count(previous20)",arithmetic:"exact integer",tie_break:"lower number",normalized_zscore_retained_for_consensus:true},verdict:"EXPLORATORY_ONLY_NO_CANDIDATE_SIGNAL_PASSES; no model promotion"};
fs.writeFileSync(outputPath,JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify({outputPath,targets:1050,tests:30,all_ci_include_zero:results.every(x=>x.bonferroni_ci_pp[0]<=0),mismatches:mismatch}));
