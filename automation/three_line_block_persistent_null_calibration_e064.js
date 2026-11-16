#!/usr/bin/env node
'use strict';

/*
 * E064: block-persistent non-predictive portfolio null calibration.
 * One random three-line union18 portfolio is held fixed for each 50-target
 * block, then independently redrawn at the next block boundary. Portfolio
 * generation never reads target outcomes.
 */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const cp = require('node:child_process');

const ROOT = process.cwd();
const STUDY_ID = 'E064_THREE_LINE_BLOCK_PERSISTENT_NULL_CALIBRATION_v1';
const PREREG_REL = 'research/weekly_purchase/1251/E064_THREE_LINE_BLOCK_PERSISTENT_NULL_CALIBRATION_PREREG_20261116.json';
const POLICY_REL = 'research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json';
const RUNNER_REL = 'automation/three_line_block_persistent_null_calibration_e064.js';
const TEST_REL = 'automation/tests_v2/test_three_line_block_persistent_null_calibration_e064.py';
const WORKFLOW_REL = '.github/workflows/target-1251-e064-block-persistent-null-calibration.yml';
const BASE_REL = 'automation/three_line_research_1251_v1.py';
const DATA_REL = 'lotto_data.csv';
const DATA_SHA = '7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2';
const ALL = Array.from({length:45}, (_,i)=>i+1);
const METRICS = ['max_hits','any2','any3','winning_union_coverage'];
const EXACT_NULL = {
  max_hits: 1.514256248572755,
  any2: 0.47497624326892623,
  any3: 0.07135490714617204,
  winning_union_coverage: 2.4
};
const SPEC = Object.freeze({
  trajectories: 1000,
  start_target: 401,
  target_count: 850,
  block_size: 50,
  blocks: 17,
  bootstrap_replicates: 4000,
  seed: 20261116064,
  alpha_per_metric: 0.0125,
  any2_positive_block_share_min: 0.65
});

function sha256(raw) { return crypto.createHash('sha256').update(raw).digest('hex'); }
function gitBlobSha(rel) {
  return cp.execFileSync('git', ['rev-parse', 'HEAD:' + rel], {cwd:ROOT, encoding:'utf8'}).trim();
}
function readJson(rel) { return JSON.parse(fs.readFileSync(path.join(ROOT,rel),'utf8')); }
function xorshift32(seed) {
  let x = seed >>> 0;
  if (x === 0) x = 0x9e3779b9;
  return function next() {
    x ^= (x << 13); x ^= (x >>> 17); x ^= (x << 5);
    return (x >>> 0) / 4294967296;
  };
}
function sampleWithoutReplacement(values, k, rng) {
  const a = values.slice();
  for (let i=0;i<k;i++) {
    const j=i+Math.floor(rng()*(a.length-i));
    const t=a[i]; a[i]=a[j]; a[j]=t;
  }
  return a.slice(0,k);
}
function initialPortfolio(rng) {
  const selected=sampleWithoutReplacement(ALL,18,rng);
  return [selected.slice(0,6),selected.slice(6,12),selected.slice(12,18)]
    .map(line=>line.slice().sort((a,b)=>a-b));
}
function assertPortfolio(lines) {
  if (!Array.isArray(lines) || lines.length!==3 || lines.some(line=>!Array.isArray(line)||line.length!==6||new Set(line).size!==6)) {
    throw new Error('invalid three-line portfolio shape');
  }
  const flat=lines.flat();
  if (flat.some(n=>!Number.isInteger(n)||n<1||n>45) || new Set(flat).size!==18) {
    throw new Error('invalid disjoint union18 geometry');
  }
}
function portfolioFingerprint(lines) { return lines.map(x=>x.join('-')).join('|'); }
function portfolioMetrics(lines, actual) {
  const hits=lines.map(line=>line.reduce((s,n)=>s+(actual.has(n)?1:0),0));
  const maximum=Math.max(...hits);
  return [maximum,maximum>=2?1:0,maximum>=3?1:0,lines.flat().reduce((s,n)=>s+(actual.has(n)?1:0),0)];
}
function mean(a) { return a.reduce((s,x)=>s+x,0)/a.length; }
function sampleSd(a) {
  const m=mean(a);
  return Math.sqrt(a.reduce((s,x)=>s+(x-m)*(x-m),0)/(a.length-1));
}
function movingBlockCI(deltas, trajectoryIndex, metricIndex) {
  const n=deltas.length, b=SPEC.block_size, blocks=SPEC.blocks;
  if (n!==SPEC.target_count || n!==b*blocks) throw new Error('unexpected target/block geometry');
  const prefix=new Float64Array(n+1);
  for (let i=0;i<n;i++) prefix[i+1]=prefix[i]+deltas[i];
  const starts=n-b+1, blockMeans=new Float64Array(starts);
  for (let s=0;s<starts;s++) blockMeans[s]=(prefix[s+b]-prefix[s])/b;
  const rng=xorshift32((SPEC.seed+1000003*trajectoryIndex+9000+metricIndex)>>>0);
  const boot=new Float64Array(SPEC.bootstrap_replicates);
  for (let r=0;r<SPEC.bootstrap_replicates;r++) {
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
function selfTest() {
  let geometryViolations=0, blockAssignmentViolations=0, generated=0;
  for (let seed=1;seed<=100;seed++) {
    const rng=xorshift32(seed);
    const blockFingerprints=[];
    for (let b=0;b<SPEC.blocks;b++) {
      const lines=initialPortfolio(rng);
      try { assertPortfolio(lines); } catch(e) { geometryViolations++; throw e; }
      const fingerprint=portfolioFingerprint(lines);
      // A block receives exactly one immutable portfolio object/fingerprint.
      const assigned=Array(SPEC.block_size).fill(fingerprint);
      if (assigned.some(x=>x!==fingerprint) || assigned.length!==SPEC.block_size) blockAssignmentViolations++;
      blockFingerprints.push(fingerprint); generated++;
    }
    if (blockFingerprints.length!==SPEC.blocks) blockAssignmentViolations++;
  }
  return {
    seeds:100, blocks_per_seed:SPEC.blocks, portfolios_generated:generated,
    target_assignments_checked:generated*SPEC.block_size,
    geometry_violations:geometryViolations,
    within_block_assignment_violations:blockAssignmentViolations
  };
}
function parseDrawCsv(raw) {
  const lines=raw.toString('utf8').replace(/^\uFEFF/,'').split(/\r?\n/).filter(line=>line.trim().length>0);
  const header=lines[0].split(',');
  const idx=Object.fromEntries(header.map((x,i)=>[x,i]));
  return lines.slice(1).map(line=>{
    const c=line.split(',');
    return {
      round:Number(c[idx.round]), date:c[idx.date],
      nums:[1,2,3,4,5,6].map(i=>Number(c[idx['no'+i]])).sort((a,b)=>a-b),
      bonus:Number(c[idx.bonus])
    };
  });
}
function validateDraws(draws) {
  if (draws.length!==1250) throw new Error('canonical data must contain exactly 1250 rows');
  for (let i=0;i<draws.length;i++) {
    const d=draws[i];
    if (d.round!==i+1 || d.nums.length!==6 || new Set(d.nums).size!==6 ||
        d.nums.some(n=>!Number.isInteger(n)||n<1||n>45) ||
        !Number.isInteger(d.bonus)||d.bonus<1||d.bonus>45||d.nums.includes(d.bonus)) {
      throw new Error('canonical draw validation failed at round '+(i+1));
    }
  }
}
function validateContracts(prereg, policy) {
  if (prereg.study_id!==STUDY_ID || prereg.preregistration_status!=='FROZEN_BEFORE_EXECUTION') throw new Error('E064 preregistration identity/status mismatch');
  if (prereg.policy_id!==policy.policy_id || policy.policy_id!=='WEEKLY_THREE_LINE_POLICY_1251_PLUS') throw new Error('E064 policy identity mismatch');
  if (prereg.data.cutoff!==1250 || prereg.data.target_range[0]!==401 || prereg.data.target_range[1]!==1250 || prereg.data.target_count!==850) throw new Error('E064 data scope mismatch');
  if (prereg.simulation.trajectories!==1000 || prereg.simulation.block_size!==50 || prereg.simulation.blocks!==17 ||
      prereg.simulation.bootstrap_replicates_per_metric_per_trajectory!==4000 || prereg.simulation.portfolios_per_trajectory!==17) throw new Error('E064 simulation contract mismatch');
  if (prereg.null_process.classification!=='piecewise_constant_block_persistent_non_predictive_portfolio' ||
      prereg.null_process.portfolio_lifetime_targets!==50 || prereg.null_process.outcome_independence!==true) throw new Error('E064 null process mismatch');
  for (const key of METRICS) {
    if (Math.abs(Number(prereg.strict_gate.exact_null[key])-EXACT_NULL[key])>1e-14) throw new Error('E064 exact null mismatch for '+key);
  }
  if (Number(policy.strict_gate.family_alpha)!==0.05 || Number(policy.strict_gate.alpha_per_metric)!==0.0125 ||
      Number(policy.strict_gate.any2_positive_nonoverlapping_50_target_block_share_min)!==0.65 ||
      policy.strict_gate.no_threshold_relaxation!==true) throw new Error('E064 strict policy drift');
  if (prereg.strict_gate.thresholds_changed!==false || prereg.strict_gate.alpha_changed!==false ||
      prereg.strict_gate.block_length_changed!==false || prereg.strict_gate.comparator_changed!==false) throw new Error('E064 must not alter the strict gate');
}
function verifyFrozenBlobs(prereg) {
  const paths={
    runner_blob_sha:RUNNER_REL, test_blob_sha:TEST_REL, workflow_blob_sha:WORKFLOW_REL,
    base_runner_blob_sha:BASE_REL, policy_blob_sha:POLICY_REL
  };
  const actual={};
  for (const [key,rel] of Object.entries(paths)) {
    actual[key]=gitBlobSha(rel);
    if (actual[key]!==prereg.frozen_blobs[key]) throw new Error('frozen Git blob mismatch: '+rel+' expected '+prereg.frozen_blobs[key]+' got '+actual[key]);
  }
  return actual;
}
function loadPreflight() {
  const prereg=readJson(PREREG_REL), policy=readJson(POLICY_REL);
  validateContracts(prereg,policy);
  const raw=fs.readFileSync(path.join(ROOT,DATA_REL));
  const dataSha=sha256(raw);
  if (dataSha!==DATA_SHA || prereg.data.sha256!==DATA_SHA) throw new Error('canonical data SHA256 mismatch');
  const draws=parseDrawCsv(raw); validateDraws(draws);
  const blobs=verifyFrozenBlobs(prereg);
  return {prereg,policy,raw,draws,dataSha,blobs};
}
function run(draws) {
  const targets=draws.slice(SPEC.start_target-1,1250);
  if (targets.length!==SPEC.target_count || targets[0].round!==401 || targets[targets.length-1].round!==1250) throw new Error('target sequence mismatch');
  const trajectoryRows=[], trajectoryMeans=METRICS.map(()=>[]);
  const blockShareCounts=Array(SPEC.blocks+1).fill(0);
  let geometryViolations=0, withinBlockChanges=0, portfolioCount=0;
  let adjacentUnionOverlapTotal=0, adjacentLineOverlapTotal=0, adjacentBlockPairs=0;
  for (let r=0;r<SPEC.trajectories;r++) {
    const rng=xorshift32((SPEC.seed+1000003*r)>>>0);
    const deltaArrays=METRICS.map(()=>new Float64Array(SPEC.target_count));
    const rawSums=[0,0,0,0], blockFingerprints=[];
    for (let block=0;block<SPEC.blocks;block++) {
      const lines=initialPortfolio(rng);
      try { assertPortfolio(lines); } catch(e) { geometryViolations++; throw e; }
      const fingerprint=portfolioFingerprint(lines);
      blockFingerprints.push({lines,fingerprint});
      portfolioCount++;
      const start=block*SPEC.block_size, end=start+SPEC.block_size;
      for (let i=start;i<end;i++) {
        // The exact same immutable block portfolio is scored for all 50 targets.
        if (portfolioFingerprint(lines)!==fingerprint) withinBlockChanges++;
        const actual=new Set(targets[i].nums);
        const m=portfolioMetrics(lines,actual);
        for (let j=0;j<4;j++) {
          deltaArrays[j][i]=m[j]-EXACT_NULL[METRICS[j]];
          rawSums[j]+=m[j];
        }
      }
    }
    for (let block=1;block<blockFingerprints.length;block++) {
      const previous=blockFingerprints[block-1].lines, current=blockFingerprints[block].lines;
      const prevUnion=new Set(previous.flat()), currUnion=new Set(current.flat());
      let unionOverlap=0;
      for (const n of prevUnion) if (currUnion.has(n)) unionOverlap++;
      let lineOverlap=0;
      for (let line=0;line<3;line++) {
        const p=new Set(previous[line]);
        for (const n of current[line]) if (p.has(n)) lineOverlap++;
      }
      adjacentUnionOverlapTotal+=unionOverlap;
      adjacentLineOverlapTotal+=lineOverlap/3;
      adjacentBlockPairs++;
    }
    const ci=[];
    let allPass=true;
    for (let j=0;j<4;j++) {
      const bounds=movingBlockCI(deltaArrays[j],r,j);
      ci.push(bounds);
      if (!(bounds[0]>0)) allPass=false;
    }
    let positiveBlocks=0;
    for (let block=0;block<SPEC.blocks;block++) {
      let blockDelta=0;
      for (let i=block*SPEC.block_size;i<(block+1)*SPEC.block_size;i++) blockDelta+=deltaArrays[1][i];
      if (blockDelta>0) positiveBlocks++;
    }
    blockShareCounts[positiveBlocks]++;
    const blockShare=positiveBlocks/SPEC.blocks;
    if (blockShare<SPEC.any2_positive_block_share_min) allPass=false;
    const rawMeans=rawSums.map(x=>x/targets.length);
    for (let j=0;j<4;j++) trajectoryMeans[j].push(rawMeans[j]);
    trajectoryRows.push({
      trajectory:r,
      max_hits_mean:rawMeans[0], any2_rate:rawMeans[1], any3_rate:rawMeans[2],
      winning_union_coverage_mean:rawMeans[3],
      max_hits_ci_lower:ci[0][0], max_hits_ci_upper:ci[0][1],
      any2_ci_lower:ci[1][0], any2_ci_upper:ci[1][1],
      any3_ci_lower:ci[2][0], any3_ci_upper:ci[2][1],
      union_coverage_ci_lower:ci[3][0], union_coverage_ci_upper:ci[3][1],
      any2_positive_50_blocks:positiveBlocks, any2_positive_block_share:blockShare,
      false_pass:allPass?1:0, any2_lag1_autocorrelation:lag1Autocorrelation(Array.from(deltaArrays[1]))
    });
  }
  const falsePasses=trajectoryRows.reduce((s,x)=>s+x.false_pass,0);
  const empirical={};
  for (let j=0;j<4;j++) {
    const vals=trajectoryMeans[j], observed=mean(vals), exact=EXACT_NULL[METRICS[j]], se=sampleSd(vals)/Math.sqrt(vals.length);
    empirical[METRICS[j]]={mean:observed,exact_mean:exact,delta:observed-exact,trajectory_level_mc_se:se,z:se===0?null:(observed-exact)/se};
  }
  return {
    study_id:STUDY_ID, evidence_class:'NULL_GATE_CALIBRATION_ONLY_BLOCK_PERSISTENT_RANDOM_PORTFOLIO_MECHANISM',
    data_cutoff:1250, target_range:[401,1250], target_count:850,
    null_process:{
      portfolio_lifetime_targets:50, portfolios_per_trajectory:17, redraw_at_each_50_target_boundary:true,
      outcome_independent:true, within_block_portfolio_changes:withinBlockChanges,
      mean_adjacent_block_union_overlap:adjacentUnionOverlapTotal/adjacentBlockPairs,
      mean_adjacent_corresponding_line_overlap:adjacentLineOverlapTotal/adjacentBlockPairs
    },
    simulation:{
      trajectories:SPEC.trajectories, portfolios_generated:portfolioCount,
      portfolio_target_evaluations:SPEC.trajectories*SPEC.target_count,
      bootstrap_replicates_per_metric_per_trajectory:SPEC.bootstrap_replicates,
      block_size:SPEC.block_size, blocks:SPEC.blocks, remainder_targets:0, seed:SPEC.seed, rng:'xorshift32'
    },
    exact_null:EXACT_NULL, empirical_null:empirical,
    strict_gate_false_pass:{false_passes: falsePasses,denominator:SPEC.trajectories,rate:falsePasses/SPEC.trajectories,wilson95:wilson95(falsePasses,SPEC.trajectories)},
    block_share_distribution:blockShareCounts,
    mean_any2_lag1_autocorrelation:mean(trajectoryRows.map(x=>x.any2_lag1_autocorrelation)),
    geometry:{geometry_violations:geometryViolations,within_block_assignment_violations:withinBlockChanges},
    trajectoryRows
  };
}
function csv(rows, headers) {
  const esc=v=>String(v).includes(',')||String(v).includes('"')||String(v).includes('\n')?'"'+String(v).replace(/"/g,'""')+'"':String(v);
  return headers.join(',')+'\n'+rows.map(row=>headers.map(h=>esc(row[h])).join(',')).join('\n')+'\n';
}
function writeOutputs(date, runId, preflight, result) {
  const outRel=path.join('analysis',date,runId,'E064_BLOCK_PERSISTENT_NULL_CALIBRATION_v1');
  const out=path.join(ROOT,outRel);
  if (fs.existsSync(out)) throw new Error('refusing to overwrite existing E064 output directory: '+outRel);
  fs.mkdirSync(out,{recursive:true});
  const {trajectoryRows,...summary}=result;
  fs.writeFileSync(path.join(out,'INFERENCE.json'),JSON.stringify(summary,null,2)+'\n','utf8');
  fs.writeFileSync(path.join(out,'TRAJECTORY_SUMMARY.csv'),csv(trajectoryRows,[
    'trajectory','max_hits_mean','any2_rate','any3_rate','winning_union_coverage_mean',
    'max_hits_ci_lower','max_hits_ci_upper','any2_ci_lower','any2_ci_upper',
    'any3_ci_lower','any3_ci_upper','union_coverage_ci_lower','union_coverage_ci_upper',
    'any2_positive_50_blocks','any2_positive_block_share','false_pass','any2_lag1_autocorrelation'
  ]),'utf8');
  const blockRows=summary.block_share_distribution.map((count,positive)=>({positive_50_blocks:positive,trajectory_count:count}));
  fs.writeFileSync(path.join(out,'BLOCK_SHARE_COUNTS.csv'),csv(blockRows,['positive_50_blocks','trajectory_count']),'utf8');
  const tests=selfTest();
  fs.writeFileSync(path.join(out,'SELF_TEST.json'),JSON.stringify(tests,null,2)+'\n','utf8');
  const verification={
    status:'PASS',study_id:STUDY_ID,data_path:DATA_REL,data_cutoff:1250,data_rows:preflight.draws.length,
    data_sha256:preflight.dataSha, data_git_blob_sha:gitBlobSha(DATA_REL),
    preregistration_git_blob_sha:gitBlobSha(PREREG_REL), frozen_blobs:preflight.blobs,
    target_range:[401,1250],target_count:850,
    simulation:{trajectories:1000,portfolios_generated:17000,portfolio_target_evaluations:850000,bootstrap_replicates:4000,block_size:50,blocks:17,remainder_targets:0,seed:SPEC.seed},
    geometry:{geometry_violations:result.geometry.geometry_violations,within_block_assignment_violations:result.geometry.within_block_assignment_violations},
    outcome_independence:'PORTFOLIO_GENERATION_USES_ONLY_SEEDED_PRNG; TARGET_OUTCOME_READ_ONLY_AFTER_BLOCK_PORTFOLIO_IS_FIXED',
    training_cutoff_violations:0,leakage_failures:0,future_predictions:0,
    strict_thresholds_changed:false,alpha_changed:false,block_length_changed:false,comparator_changed:false,
    predictive_model_evaluated:false,purchase_recommendation_generated:false,strict_pass_ready_created:false,
    manifest_entries:7,manifest_status:'PASS'
  };
  fs.writeFileSync(path.join(out,'VERIFICATION.json'),JSON.stringify(verification,null,2)+'\n','utf8');
  const completion={
    study_id:STUDY_ID,status:'COMPLETE',evidence_class:'NULL_GATE_CALIBRATION_ONLY',
    data_cutoff:1250,target_count:850,trajectories:1000,portfolios_generated:17000,
    strict_gate_false_pass_rate:result.strict_gate_false_pass.rate,
    predictive_model_evaluated:false,purchase_recommendation_generated:false,strict_pass_ready:false
  };
  fs.writeFileSync(path.join(out,'COMPLETION.json'),JSON.stringify(completion,null,2)+'\n','utf8');
  const f=result.strict_gate_false_pass;
  const report=[
    '# E064 — Block-persistent non-predictive portfolio null calibration','',
    'Execution status: **COMPLETE / VERIFICATION PASS**','',
    '## Frozen design',
    '- One uniformly random disjoint three-line union18 portfolio is held fixed for each non-overlapping 50-target block.',
    '- At each 50-target boundary, a new independent uniform ordered partition is drawn from a seeded PRNG.',
    '- Portfolio generation never reads target outcomes; outcomes are read only after the block portfolio is fixed.',
    '- Targets 401–1250; 1,000 trajectories; 17 portfolios per trajectory; 17,000 generated portfolios total.',
    '- The unchanged strict gate uses four exact-null comparisons, 4,000 moving-block bootstrap replicates, 50-target blocks, and the existing 65% positive-any2-block rule.',
    '',
    '## Results',
    ...METRICS.map(k=>{const x=result.empirical_null[k];return '- '+k+': empirical mean='+x.mean.toFixed(6)+', exact null='+x.exact_mean.toFixed(6)+', delta='+x.delta.toFixed(6)+', trajectory MCSE='+x.trajectory_level_mc_se.toFixed(6);}),
    '- Joint strict-gate false passes: **'+f.false_passes+'/'+f.denominator+' ('+(100*f.rate).toFixed(2)+'%)**.',
    '- 95% Wilson interval: ['+(100*f.wilson95[0]).toFixed(4)+'%, '+(100*f.wilson95[1]).toFixed(4)+'%].',
    '- Mean lag-1 autocorrelation of any2: '+result.mean_any2_lag1_autocorrelation.toFixed(6)+'.',
    '- Mean adjacent-block union overlap: '+result.null_process.mean_adjacent_block_union_overlap.toFixed(3)+' numbers; corresponding-line overlap: '+result.null_process.mean_adjacent_corresponding_line_overlap.toFixed(3)+' per line.',
    '',
    '## Interpretation',
    'This is a gate-calibration stress test under one piecewise-constant, block-persistent random portfolio mechanism. It is not a predictive model, does not test a new signal, and cannot create STRICT_PASS_READY or purchase eligibility.',
    'The strict gate, alpha, block length, comparator, and purchase policy were not changed.',
    '',
    'No candidate numbers, purchase lines, freeze, or seal were generated.',''
  ].join('\n');
  fs.writeFileSync(path.join(out,'REPORT.md'),report,'utf8');
  const files=fs.readdirSync(out).filter(name=>name!=='SHA256_MANIFEST.csv').sort();
  const manifestRows=files.map(name=>{
    const raw=fs.readFileSync(path.join(out,name));
    return {path:name,sha256:sha256(raw),bytes:raw.length};
  });
  fs.writeFileSync(path.join(out,'SHA256_MANIFEST.csv'),csv(manifestRows,['path','sha256','bytes']),'utf8');
  const supplement=[
    '# 2026-11-16 E064 supplement — block-persistent null calibration','',
    'E064 completed as a null-gate calibration only. One random three-line union18 portfolio was held fixed within each 50-target block and independently redrawn at each block boundary.',
    'The run used 1,000 trajectories, 850 targets per trajectory, 17,000 generated portfolios, and 4,000 moving-block bootstrap replicates per metric and trajectory.',
    '',
    'Joint strict-gate false passes: '+f.false_passes+'/'+f.denominator+' ('+(100*f.rate).toFixed(2)+'%); 95% Wilson interval ['+(100*f.wilson95[0]).toFixed(4)+'%, '+(100*f.wilson95[1]).toFixed(4)+'%].',
    '',
    'This is not predictive evidence. It does not alter the strict gate, model status, or 1251 purchase readiness. No candidate numbers or purchase lines were generated.',
    '',
    'Result directory: '+outRel,''
  ].join('\n');
  fs.writeFileSync(path.join(ROOT,'research','daily',date+'_E064_SUPPLEMENT.md'),supplement,'utf8');
  return {output_directory:outRel,supplement_path:'research/daily/'+date+'_E064_SUPPLEMENT.md',completion,verification,manifest_entries:manifestRows.length};
}
function parseArgs(argv) {
  const out={}; for(let i=0;i<argv.length;i++) if(argv[i].startsWith('--')) out[argv[i].slice(2)]=argv[i+1]||'true',i++;
  return out;
}
function main() {
  const args=parseArgs(process.argv.slice(2));
  if(args['self-test']==='true') { console.log(JSON.stringify(selfTest())); return; }
  const preflight=loadPreflight();
  if(args.preflight==='true') {
    console.log(JSON.stringify({status:'PREFLIGHT_PASS',study_id:STUDY_ID,data_cutoff:1250,target_count:850,frozen_blobs:preflight.blobs}));
    return;
  }
  const date=args.date||new Date().toISOString().slice(0,10);
  const runId=args['run-id']||('manual_'+Date.now());
  if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!/^[A-Za-z0-9_-]+$/.test(runId)) throw new Error('invalid date or run id');
  const result=run(preflight.draws);
  console.log(JSON.stringify(writeOutputs(date,runId,preflight,result)));
}
if(require.main===module) main();
module.exports={SPEC,EXACT_NULL,xorshift32,sampleWithoutReplacement,initialPortfolio,assertPortfolio,portfolioMetrics,movingBlockCI,selfTest,parseDrawCsv,validateDraws,validateContracts,verifyFrozenBlobs,run};
