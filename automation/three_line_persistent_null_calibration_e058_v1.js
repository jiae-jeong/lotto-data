#!/usr/bin/env node
'use strict';

/*
 * E058: persistent but non-predictive three-line portfolio null calibration.
 * Each target portfolio is generated without reading target outcomes.
 * Initial state is a uniform ordered partition of a uniform 18-subset.
 * Each transition retains exactly 3/6 numbers in each corresponding line,
 * then fills the 9 vacancies from outside the prior union18.
 */
const fs = require('node:fs');
const crypto = require('node:crypto');

const SPEC = Object.freeze({
  study_id: 'E058_THREE_LINE_PERSISTENT_PORTFOLIO_NULL_CALIBRATION_v1',
  data_sha256: '7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2',
  cutoff: 1250,
  start_target: 401,
  target_count: 850,
  trajectories: 1000,
  retention_per_line: 3,
  line_size: 6,
  line_count: 3,
  bootstrap_replicates: 4000,
  block_size: 50,
  seed: 20261116058,
  exact_null: {
    max_hits: 1.514256248572755,
    any2: 0.47497624326892623,
    any3: 0.07135490714617204,
    winning_union_coverage: 2.4
  },
  alpha_per_metric: 0.0125,
  any2_positive_block_share_min: 0.65
});

const ALL = Array.from({length:45}, (_,i)=>i+1);
const METRICS = ['max_hits','any2','any3','winning_union_coverage'];

function xorshift32(seed) {
  let x = seed >>> 0;
  if (x === 0) x = 0x9e3779b9;
  return function next() {
    x ^= (x << 13);
    x ^= (x >>> 17);
    x ^= (x << 5);
    return (x >>> 0) / 4294967296;
  };
}
function sampleWithoutReplacement(values, k, rng) {
  const a = values.slice();
  for (let i=0; i<k; i++) {
    const j = i + Math.floor(rng() * (a.length-i));
    const t=a[i]; a[i]=a[j]; a[j]=t;
  }
  return a.slice(0,k);
}
function initialPortfolio(rng) {
  const selected = sampleWithoutReplacement(ALL,18,rng);
  return [selected.slice(0,6),selected.slice(6,12),selected.slice(12,18)]
    .map(line=>line.slice().sort((a,b)=>a-b));
}
function transitionPortfolio(previous, rng) {
  const retained = previous.map(line=>sampleWithoutReplacement(line,3,rng));
  const oldUnion = new Set(previous.flat());
  const outside = ALL.filter(n=>!oldUnion.has(n));
  const additions = sampleWithoutReplacement(outside,9,rng);
  return retained.map((line,i)=>line.concat(additions.slice(i*3,i*3+3)).sort((a,b)=>a-b));
}
function assertPortfolio(lines) {
  if (lines.length!==3 || lines.some(x=>x.length!==6 || new Set(x).size!==6)) throw new Error('bad line shape');
  const flat=lines.flat();
  if (flat.some(n=>n<1||n>45) || new Set(flat).size!==18) throw new Error('bad union18 geometry');
}
function assertTransition(previous, next) {
  assertPortfolio(previous); assertPortfolio(next);
  for (let i=0;i<3;i++) {
    const a=new Set(previous[i]);
    const overlap=next[i].filter(n=>a.has(n)).length;
    if (overlap!==3) throw new Error('line retention is not exactly 3/6');
  }
  const a=new Set(previous.flat()), b=new Set(next.flat());
  let overlap=0; for (const n of a) if (b.has(n)) overlap++;
  if (overlap!==9) throw new Error('union retention is not exactly 9/18');
}
function selfTest() {
  for (let seed=1;seed<=100;seed++) {
    const rng=xorshift32(seed);
    let p=initialPortfolio(rng); assertPortfolio(p);
    for (let i=0;i<100;i++) { const q=transitionPortfolio(p,rng); assertTransition(p,q); p=q; }
  }
  return {seeds:100, transitions:10000, geometry_violations:0, line_retention_violations:0, union_retention_violations:0};
}
function portfolioMetrics(lines, actual) {
  const hits=lines.map(line=>line.reduce((s,n)=>s+(actual.has(n)?1:0),0));
  const maximum=Math.max(...hits);
  return [maximum,maximum>=2?1:0,maximum>=3?1:0,lines.flat().reduce((s,n)=>s+(actual.has(n)?1:0),0)];
}
function mean(a) { return a.reduce((s,x)=>s+x,0)/a.length; }
function sampleSd(a) {
  const m=mean(a); return Math.sqrt(a.reduce((s,x)=>s+(x-m)*(x-m),0)/(a.length-1));
}
function movingBlockCI(deltas, trajectoryIndex, metricIndex) {
  const n=deltas.length, b=50, blocks=n/b;
  if (n!==850 || blocks!==17) throw new Error('unexpected target/block geometry');
  const prefix=new Float64Array(n+1);
  for (let i=0;i<n;i++) prefix[i+1]=prefix[i]+deltas[i];
  const starts=n-b+1, blockMeans=new Float64Array(starts);
  for (let s=0;s<starts;s++) blockMeans[s]=(prefix[s+b]-prefix[s])/b;
  const rng=xorshift32((SPEC.seed+1000003*trajectoryIndex+9000+metricIndex)>>>0);
  const boot=new Float64Array(4000);
  for (let r=0;r<4000;r++) {
    let total=0;
    for (let k=0;k<blocks;k++) total+=blockMeans[Math.floor(rng()*starts)];
    boot[r]=total/blocks;
  }
  boot.sort();
  return [boot[24],boot[3974]];
}
function wilson95(successes,n) {
  const z=1.959963984540054, p=successes/n, z2=z*z, den=1+z2/n;
  const center=(p+z2/(2*n))/den;
  const half=z*Math.sqrt(p*(1-p)/n+z2/(4*n*n))/den;
  return [Math.max(0,center-half),Math.min(1,center+half)];
}
function lag1Autocorrelation(values) {
  const m=mean(values);
  let num=0,den=0;
  for (let i=0;i<values.length;i++) den+=(values[i]-m)*(values[i]-m);
  for (let i=1;i<values.length;i++) num+=(values[i]-m)*(values[i-1]-m);
  return den===0?0:num/den;
}
function run(draws) {
  if (draws.length!==SPEC.cutoff) throw new Error('data row count mismatch');
  const targets=draws.slice(SPEC.start_target-1,SPEC.cutoff);
  if (targets.length!==SPEC.target_count) throw new Error('target count mismatch');
  const trajectoryRows=[], trajectoryMeans=METRICS.map(()=>[]);
  const blockShareCounts=Array(18).fill(0);
  let geometryViolations=0, transitionViolations=0;
  let totalPortfolios=0;
  for (let r=0;r<SPEC.trajectories;r++) {
    const rng=xorshift32((SPEC.seed+1000003*r)>>>0);
    let lines=initialPortfolio(rng);
    const deltaArrays=METRICS.map(()=>new Float64Array(SPEC.target_count));
    const rawSums=[0,0,0,0];
    for (let i=0;i<targets.length;i++) {
      assertPortfolio(lines);
      const actual=new Set(targets[i].nums);
      const m=portfolioMetrics(lines,actual);
      for (let j=0;j<4;j++) {
        deltaArrays[j][i]=m[j]-SPEC.exact_null[METRICS[j]];
        rawSums[j]+=m[j];
      }
      totalPortfolios++;
      if (i<targets.length-1) {
        const next=transitionPortfolio(lines,rng);
        try { assertTransition(lines,next); } catch(e) { transitionViolations++; throw e; }
        lines=next;
      }
    }
    const ci=[], blockCounts=[];
    let allPass=true;
    for (let j=0;j<4;j++) {
      const lohi=movingBlockCI(Array.from(deltaArrays[j]),r,j);
      ci.push(lohi);
      if (!(lohi[0]>0)) allPass=false;
    }
    const any2=deltaArrays[1];
    let positive=0;
    for (let k=0;k<17;k++) {
      let s=0; for (let i=k*50;i<(k+1)*50;i++) s+=any2[i];
      if (s>0) positive++;
    }
    blockCounts.push(positive);
    blockShareCounts[positive]++;
    if (positive/17<SPEC.any2_positive_block_share_min) allPass=false;
    const rawMeans=rawSums.map(x=>x/targets.length);
    for (let j=0;j<4;j++) trajectoryMeans[j].push(rawMeans[j]);
    trajectoryRows.push({
      trajectory:r,
      max_hits_mean:rawMeans[0],
      any2_rate:rawMeans[1],
      any3_rate:rawMeans[2],
      winning_union_coverage_mean:rawMeans[3],
      max_hits_ci_lower:ci[0][0], max_hits_ci_upper:ci[0][1],
      any2_ci_lower:ci[1][0], any2_ci_upper:ci[1][1],
      any3_ci_lower:ci[2][0], any3_ci_upper:ci[2][1],
      union_coverage_ci_lower:ci[3][0], union_coverage_ci_upper:ci[3][1],
      any2_positive_50_blocks:positive,
      any2_positive_block_share:positive/17,
      false_pass:allPass?1:0,
      any2_lag1_autocorrelation:lag1Autocorrelation(Array.from(any2))
    });
  }
  const falsePasses=trajectoryRows.reduce((s,x)=>s+x.false_pass,0);
  const empirical={};
  for (let j=0;j<4;j++) {
    const vals=trajectoryMeans[j], observed=mean(vals), exact=SPEC.exact_null[METRICS[j]];
    const se=sampleSd(vals)/Math.sqrt(vals.length);
    empirical[METRICS[j]]={mean:observed,exact_mean:exact,delta:observed-exact,trajectory_level_mc_se:se,z:se===0?null:(observed-exact)/se};
  }
  return {
    study_id:SPEC.study_id,
    data_cutoff:SPEC.cutoff,
    target_range:[SPEC.start_target,SPEC.cutoff],
    target_count:SPEC.target_count,
    simulation:{trajectories:SPEC.trajectories,portfolios:totalPortfolios,retention_per_line:3,line_size:6,union_retention:9,seed:SPEC.seed,bootstrap_replicates:SPEC.bootstrap_replicates,block_size:50,blocks:17,final_remainder:0},
    empirical_null:empirical,
    strict_gate_false_pass:{false_passes,denominator:SPEC.trajectories,rate:falsePasses/SPEC.trajectories,wilson95:wilson95(falsePasses,SPEC.trajectories)},
    block_share_distribution:blockShareCounts,
    mean_any2_lag1_autocorrelation:mean(trajectoryRows.map(x=>x.any2_lag1_autocorrelation)),
    geometry:{geometry_violations:geometryViolations,transition_violations:transitionViolations},
    trajectoryRows
  };
}
function parseDrawCsv(raw) {
  const lines=raw.toString('utf8').replace(/^\uFEFF/,'').trim().split(/\r?\n/);
  const header=lines[0].split(',');
  const idx=Object.fromEntries(header.map((x,i)=>[x,i]));
  const rows=lines.slice(1).map(line=>{
    const c=line.split(',');
    return {round:Number(c[idx.round]),date:c[idx.date],nums:[1,2,3,4,5,6].map(i=>Number(c[idx['no'+i]])).sort((a,b)=>a-b),bonus:Number(c[idx.bonus])};
  });
  return rows;
}
if (require.main===module) {
  const input=process.argv[2]||'lotto_data.csv';
  const outdir=process.argv[3]||'analysis/2026-11-16/E058_PERSISTENT_NULL_v1';
  const raw=fs.readFileSync(input);
  const sha=crypto.createHash('sha256').update(raw).digest('hex');
  if (sha!==SPEC.data_sha256) throw new Error('source data SHA mismatch: '+sha);
  const draws=parseDrawCsv(raw);
  if (draws.length!==1250 || draws.some((d,i)=>d.round!==i+1 || new Set(d.nums).size!==6 || d.nums.some(n=>n<1||n>45) || d.bonus<1||d.bonus>45||d.nums.includes(d.bonus))) throw new Error('canonical data validation failed');
  const tests=selfTest();
  const result=run(draws);
  fs.mkdirSync(outdir,{recursive:true});
  const {trajectoryRows,...summary}=result;
  fs.writeFileSync(outdir+'/INFERENCE.json',JSON.stringify(summary,null,2)+'\n');
  fs.writeFileSync(outdir+'/TRAJECTORY_SUMMARY.csv',
    'trajectory,max_hits_mean,any2_rate,any3_rate,winning_union_coverage_mean,max_hits_ci_lower,any2_ci_lower,any3_ci_lower,union_coverage_ci_lower,any2_positive_50_blocks,any2_positive_block_share,false_pass,any2_lag1_autocorrelation\n'+
    trajectoryRows.map(x=>[x.trajectory,x.max_hits_mean,x.any2_rate,x.any3_rate,x.winning_union_coverage_mean,x.max_hits_ci_lower,x.any2_ci_lower,x.any3_ci_lower,x.union_coverage_ci_lower,x.any2_positive_50_blocks,x.any2_positive_block_share,x.false_pass,x.any2_lag1_autocorrelation].join(',')).join('\n')+'\n');
  fs.writeFileSync(outdir+'/SELF_TEST.json',JSON.stringify(tests,null,2)+'\n');
  fs.writeFileSync(outdir+'/COMPLETION.json',JSON.stringify({status:'COMPLETE',executed:true,study_id:SPEC.study_id},null,2)+'\n');
}
module.exports={SPEC,xorshift32,sampleWithoutReplacement,initialPortfolio,transitionPortfolio,assertPortfolio,assertTransition,selfTest,portfolioMetrics,run,parseDrawCsv};
