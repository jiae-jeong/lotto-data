#!/usr/bin/env node
"use strict";
const fs = require("fs");
const crypto = require("crypto");

const FULL_SHA = "7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2";
const PREFIX_SHA = "a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7";
const START = 401, END = 1249, HISTORY_START = 301, WINDOW = 100;
const BOOTSTRAPS = 4000, BLOCK = 50, ALPHA = 0.0125;
const METRICS = ["max_hits", "any2", "any3", "winning_union_coverage"];
const NULL = {max_hits:1.514256248572755, any2:0.47497624326892623, any3:0.07135490714617204, winning_union_coverage:2.4};

function sha(b) { return crypto.createHash("sha256").update(b).digest("hex"); }
function parseDraws(raw) {
  const lines = raw.toString("utf8").split(/\r?\n/).filter(x => x.trim() !== "");
  const rows = lines.slice(1).map(line => line.split(","));
  if (rows.length !== 1250) throw new Error("Expected 1250 non-empty draw rows");
  return rows.map((r, i) => {
    const round = Number(r[0]), nums = r.slice(2, 8).map(Number), bonus = Number(r[8]);
    if (round !== i + 1 || nums.length !== 6 || new Set(nums).size !== 6 ||
        nums.some(n => !Number.isInteger(n) || n < 1 || n > 45) ||
        !Number.isInteger(bonus) || bonus < 1 || bonus > 45 || nums.includes(bonus))
      throw new Error("Invalid canonical draw row " + (i + 1));
    return {round, nums};
  });
}
function prefixBytes(raw, cutoff) {
  const lines = raw.toString("utf8").match(/[^\n]*\n|[^\n]+$/g) || [];
  const selected = [lines[0]];
  let count = 0;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim() === "") { selected.push(lines[i]); continue; }
    if (count >= cutoff) break;
    selected.push(lines[i]); count++;
  }
  if (count !== cutoff) throw new Error("Cannot isolate source prefix");
  return Buffer.from(selected.join(""), "utf8");
}
function choose(n, k) {
  if (k < 0 || k > n) return 0;
  let x = 1;
  for (let i = 1; i <= Math.min(k, n-k); i++) x = x * (n-i+1) / i;
  return x;
}
function exactNull() {
  const den = choose(45, 6);
  let maxSum = 0, p2 = 0, p3 = 0, unionSum = 0;
  for (let a=0; a<=6; a++) for (let b=0; b<=6; b++) for (let c=0; c<=6; c++) {
    const outside = 6-a-b-c;
    if (outside < 0 || outside > 27) continue;
    const ways = choose(6,a)*choose(6,b)*choose(6,c)*choose(27,outside);
    maxSum += Math.max(a,b,c)*ways;
    if (Math.max(a,b,c) >= 2) p2 += ways;
    if (Math.max(a,b,c) >= 3) p3 += ways;
    unionSum += (a+b+c)*ways;
  }
  return {max_hits:maxSum/den, any2:p2/den, any3:p3/den, winning_union_coverage:unionSum/den};
}
function hhi(draws, end) {
  const count = Array(46).fill(0);
  for (let i=end-WINDOW; i<end; i++) for (const n of draws[i].nums) count[n]++;
  return count.slice(1).reduce((s,c)=>s+(c/600)**2,0);
}
function median(a) {
  const x = a.slice().sort((p,q)=>p-q), m = x.length >> 1;
  return x.length % 2 ? x[m] : (x[m-1]+x[m])/2;
}
function buildRegimes(draws, maxTarget) {
  const h = {};
  for (let e=WINDOW; e<=maxTarget-1; e++) h[e] = hhi(draws,e);
  const regimes = {};
  for (let u=HISTORY_START; u<=maxTarget; u++) {
    const rs=Math.max(WINDOW,u-300), re=u-101, refs=[];
    for(let e=rs;e<=re;e++) refs.push(h[e]);
    if(refs.length<100 || h[u-1]===undefined) throw new Error("Missing pre-target HHI");
    regimes[u] = {regime:h[u-1]>=median(refs)?1:0, current:h[u-1], threshold:median(refs), ref_count:refs.length, ref_end:re};
  }
  return {h,regimes};
}
function updateCounts(regime, outcome, exposures, successes) {
  exposures[regime]++;
  for (const n of outcome) successes[regime][n]++;
}
function makeScores(regime, exposures, successes) {
  const scores={};
  for(let n=1;n<=45;n++) scores[n]=(successes[regime][n]+6)/(exposures[regime]+45);
  return scores;
}
function cmpScore(a,b,s) { return s[b]-s[a] || a-b; }
function combinations(arr, k) {
  const out=[], cur=[];
  function rec(start) {
    if(cur.length===k){out.push(cur.slice());return;}
    for(let i=start;i<=arr.length-(k-cur.length);i++){cur.push(arr[i]);rec(i+1);cur.pop();}
  }
  rec(0); return out;
}
function e045Ticket(scores, used) {
  const available=Array.from({length:45},(_,i)=>i+1).filter(n=>!used.has(n)).sort((a,b)=>cmpScore(a,b,scores));
  const pool=available.slice(0,16);
  let best=null;
  for(const ticket of combinations(pool,6)){
    const sorted=ticket.slice().sort((a,b)=>a-b);
    const odd=sorted.filter(n=>n%2).length, low=sorted.filter(n=>n<=22).length;
    const bands=new Set(sorted.map(n=>Math.floor((n-1)/10))).size;
    let consecutive=0;
    for(let i=1;i<6;i++) if(sorted[i]-sorted[i-1]===1) consecutive++;
    const raw=sorted.reduce((s,n)=>s+scores[n],0);
    const value=raw-0.022*Math.abs(odd-3)-0.020*Math.abs(low-3)-0.010*Math.max(0,consecutive-2)+0.004*bands;
    const lexLess=(x,y)=>{for(let q=0;q<6;q++){if(x[q]!==y[q])return x[q]<y[q];}return false;};
    if(!best || value>best.value+1e-15 || (Math.abs(value-best.value)<=1e-15 && lexLess(sorted,best.ticket)))
      best={ticket:sorted,value};
  }
  return best.ticket;
}
function scoreOnlyTicket(scores, used) {
  const available=Array.from({length:45},(_,i)=>i+1).filter(n=>!used.has(n)).sort((a,b)=>cmpScore(a,b,scores));
  return available.slice(0,6);
}
function portfolio(makeTicket, scores) {
  const used=new Set(), lines=[];
  for(let i=0;i<3;i++){const line=makeTicket(scores,used);lines.push(line);for(const n of line)used.add(n);}
  if(lines.length!==3 || used.size!==18) throw new Error("Invalid 3x6 disjoint geometry");
  return lines;
}
function metrics(lines, actual) {
  const hits=lines.map(line=>line.reduce((s,n)=>s+(actual.has(n)?1:0),0));
  const max=Math.max(...hits), union=new Set(lines.flat());
  return {max_hits:max,any2:+(max>=2),any3:+(max>=3),any4:+(max>=4),any5:+(max>=5),any6:+(max>=6),
    winning_union_coverage:[...union].filter(n=>actual.has(n)).length,line_hit_distribution:hits};
}
function rng32(seed) {
  let x=seed>>>0; if(x===0)x=0x9e3779b9;
  return {next(){x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967296;},int(n){return Math.floor(this.next()*n);}};
}
function permute(lines, rng) {
  const labels=Array.from({length:45},(_,i)=>i+1), shuffled=labels.slice();
  for(let i=shuffled.length-1;i>0;i--){const j=rng.int(i+1);[shuffled[i],shuffled[j]]=[shuffled[j],shuffled[i]];}
  const map=new Map(labels.map((n,i)=>[n,shuffled[i]]));
  return lines.map(line=>line.map(n=>map.get(n)));
}
function mean(a){return a.reduce((s,x)=>s+x,0)/a.length;}
function movingBlockCI(values, seed) {
  const sizes=Array(16).fill(50).concat([49]), rng=rng32(seed), reps=[];
  for(let b=0;b<BOOTSTRAPS;b++){
    const sample=[];
    for(const size of sizes){const start=rng.int(values.length-size+1);for(let j=0;j<size;j++)sample.push(values[start+j]);}
    reps.push(mean(sample));
  }
  reps.sort((a,b)=>a-b);
  return [reps[Math.floor((ALPHA/2)*(BOOTSTRAPS-1))],reps[Math.floor((1-ALPHA/2)*(BOOTSTRAPS-1))]];
}
function summarize(rows, arm, seedBase) {
  const out={}, blocks=[];
  for(const m of METRICS){
    const d=rows.map(r=>r[arm][m]-NULL[m]);
    const ci=movingBlockCI(d,seedBase+METRICS.indexOf(m));
    out[m]={observed_mean:mean(rows.map(r=>r[arm][m])),exact_null:NULL[m],delta_mean:mean(d),
      adjusted_moving_block_ci:ci,lower_bound_gt_zero:ci[0]>0};
  }
  for(let start=0;start<rows.length;start+=50){
    const end=Math.min(start+50,rows.length), vals=rows.slice(start,end).map(r=>r[arm].any2-NULL.any2);
    blocks.push({start_target:rows[start].target,end_target:rows[end-1].target,n:end-start,mean_any2_delta:mean(vals),positive:mean(vals)>0});
  }
  const share=blocks.filter(b=>b.positive).length/blocks.length;
  return {metrics:out,blocks,any2_positive_block_share:share,strict_historical_gate:
    METRICS.every(m=>out[m].lower_bound_gt_zero)&&share>=0.65};
}
function run(file) {
  const raw=fs.readFileSync(file), full=sha(raw), prefix=sha(prefixBytes(raw,1249));
  if(full!==FULL_SHA || prefix!==PREFIX_SHA) throw new Error("Source hash mismatch");
  const draws=parseDraws(raw), {regimes}=buildRegimes(draws,END);
  const exposures=[0,0], successes=[Array(46).fill(0),Array(46).fill(0)];
  for(let u=HISTORY_START;u<START;u++) updateCounts(regimes[u].regime,draws[u-1].nums,exposures,successes);
  const rows=[], candidateRecall=Object.fromEntries([10,15,20,25,30].map(k=>[k,[]]));
  const zeroAgg=()=>({count:0,max_hits:0,any2:0,any3:0,any4:0,any5:0,any6:0,winning_union_coverage:0});
  const randomAgg={E079_A:zeroAgg(),E079_B:zeroAgg()};
  for(let t=START;t<=END;t++){
    const g=regimes[t].regime, scores=makeScores(g,exposures,successes);
    const rank=Array.from({length:45},(_,i)=>i+1).sort((a,b)=>cmpScore(a,b,scores));
    const actual=new Set(draws[t-1].nums);
    for(const k of [10,15,20,25,30]) candidateRecall[k].push(rank.slice(0,k).filter(n=>actual.has(n)).length);
    const a=portfolio(e045Ticket,scores), b=portfolio(scoreOnlyTicket,scores);
    const ma=metrics(a,actual), mb=metrics(b,actual);
    const row={target:t,E079_A:ma,E079_B:mb};
    rows.push(row);
    for(const [arm,lines,offset] of [["E079_A",a,0],["E079_B",b,1000000]]){
      const rng=rng32(20261122079+t+offset);
      for(let j=0;j<120;j++){
        const rm=metrics(permute(lines,rng),actual);
        for(const m of ["max_hits","any2","any3","any4","any5","any6","winning_union_coverage"])randomAgg[arm][m]+=rm[m];
        randomAgg[arm].count++;
      }
    }
    updateCounts(g,draws[t-1].nums,exposures,successes);
  }
  const A=summarize(rows,"E079_A",20261122100), B=summarize(rows,"E079_B",20261122200);
  const paired={};
  for(const m of METRICS){const d=rows.map(r=>r.E079_B[m]-r.E079_A[m]);paired[m]={delta_mean:mean(d),adjusted_moving_block_ci:movingBlockCI(d,20261122300+METRICS.indexOf(m))};}
  const randomSummary={};
  for(const arm of ["E079_A","E079_B"]){const x=randomAgg[arm];randomSummary[arm]={portfolios:x.count,...Object.fromEntries(["max_hits","any2","any3","any4","any5","any6","winning_union_coverage"].map(m=>[m,x[m]/x.count]))};}
  const candidateSummary=Object.fromEntries(Object.entries(candidateRecall).map(([k,v])=>[k,{mean_hits:mean(v),recall:mean(v)/6,random_expected_hits:Number(k)*6/45,delta_hits:mean(v)-Number(k)*6/45}]));
  return {study_id:"E079_E045_STRUCTURE_OBJECTIVE_ABLATION_v1",source:{full_sha256:full,prefix_sha256:prefix,rows:draws.length,cutoff:END},targets:rows.length,range:[START,END],
    exact_null:NULL,E079_A:A,E079_B:B,paired_B_minus_A:paired,matched_random:randomSummary,candidate_stage_fixed_summary:candidateSummary,
    leakage:{violations:0,rule:"all score training outcomes and HHI inputs end no later than target-1"},
    caveats:["1244-1249 are contaminated live-history diagnostics","historical results are not clean holdout or prospective confirmation","no model promotion or number release"]};
}
if(require.main===module){
  const result=run(process.argv[2]||"lotto_data.csv");
  const out=process.argv[3]||"E079_RESULTS.json";
  fs.writeFileSync(out,JSON.stringify(result,null,2)+"\n");
  process.stdout.write(JSON.stringify({out,targets:result.targets,E079_A:result.E079_A.metrics,E079_B:result.E079_B.metrics,paired:result.paired_B_minus_A},null,2)+"\n");
}
module.exports={run};