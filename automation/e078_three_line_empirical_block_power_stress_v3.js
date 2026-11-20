'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');

const OUT = 'analysis/2026-11-21/E078_THREE_LINE_EMPIRICAL_BLOCK_POWER_STRESS_v2';
const E045 = 'analysis/2026-11-14/gha_43499702588_1/E045_THREE_LINE_DISJOINT_PORTFOLIO_WALKFORWARD_v1';
const E046 = 'analysis/2026-11-14/gha_43526534917_1/E046_THREE_LINE_PROSPECTIVE_POWER_PLANNING_v1';
const DATA = 'lotto_data.csv';
const DELIVERY = 'research/DELIVERY_LOG.md';
const PURCHASE_REGISTRY = 'research/PURCHASE_CONFIRMATION_REGISTRY.json';
const TARGET1251 = 'research/weekly_purchase/1251/RESEARCH_SELECTED_LINES_1251_20261120.json';
const V9_1250 = 'analysis/2026-11-14/FIVE_ROLE_RESEARCH_1250_V9.json';
const EXTERNAL = 'analysis/2026-11-20/EXTERNAL_DATA_CROSSCHECK.json';

const EXPECT = {
  dataSha256: '7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2',
  dataBlob: '66431d711919f179e4cb1349e2f7295c68a8735e',
  e045PredSha256: '63741597dced378876c7ac1d7a15fb5864e03f3a2b765a42e9452591867d3500',
  e045PredBlob: 'e55b8f5997dde36ff55b93b4bb53d20b8ad2ba69',
  e045RandomSha256: '19566decad6fac44651341046d10a6241ba40abc7575771736fd53ef8d035a25',
  e045RandomBlob: 'fa0fe8e2317f22b01dbd3b3aa15f4df68d8680c3',
  e046GridBlob: '201a240028d8b7c6a6254dc33fe789a165fbc358',
  deliveryBlob: '98360d2348a244f321bb900fe8c19237cb910217',
  target1251Blob: '9da6f5760367758896f20f8643c771452e7948cd',
  v9Blob: '2cd56b3688c75cab55a090e5188b108eda9c5fee',
  purchaseRegistryBlob: 'a6eadb56302487267d6cc5373f020361930a63d0'
};

const NULLS = [1.514256248572755, 0.47497624326892623, 0.07135490714617204, 2.4];
const METRICS = ['max_hits', 'any2', 'any3', 'winning_union_coverage'];
const Z = 2.4977054744123737;
const NS = [100, 200, 300, 400, 500, 600, 800, 849, 1000];
const DS = [0.25, 0.5, 0.75, 1.0];
const REPS = 10000;
const BASE_SEED = 20261121078;

function assert(ok, msg) { if (!ok) throw new Error('ASSERT: ' + msg); }
function sha256(buf) { return crypto.createHash('sha256').update(buf).digest('hex'); }
function blobSha(p) { return execFileSync('git', ['hash-object', p], {encoding:'utf8'}).trim(); }
function readText(p) { return fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, ''); }
function parseCsv(p) {
  const lines = readText(p).split(/\r?\n/).filter(x => x.length > 0);
  const head = lines.shift().split(',');
  return lines.map(line => {
    const vals = line.split(',');
    const o = {};
    head.forEach((k,i) => o[k] = vals[i] === undefined ? '' : vals[i]);
    return o;
  });
}
function nums(s) { return String(s).trim().split(/\s+/).filter(Boolean).map(Number); }
function unique(a) { return new Set(a).size === a.length; }
function mean(a) { return a.reduce((s,x)=>s+x,0)/a.length; }
function sd(a) {
  const m=mean(a);
  return Math.sqrt(a.reduce((s,x)=>s+(x-m)*(x-m),0)/(a.length-1));
}
function corr(a,b) {
  const ma=mean(a), mb=mean(b);
  let num=0, da=0, db=0;
  for(let i=0;i<a.length;i++){ const x=a[i]-ma, y=b[i]-mb; num+=x*y; da+=x*x; db+=y*y; }
  return num/Math.sqrt(da*db);
}
function wilson(k,n,z=1.959963984540054) {
  const p=k/n, z2=z*z, den=1+z2/n;
  const center=(p+z2/(2*n))/den;
  const half=z*Math.sqrt((p*(1-p)/n)+(z2/(4*n*n)))/den;
  return [Math.max(0,center-half),Math.min(1,center+half)];
}
function mulberry32(seed) {
  let a = seed >>> 0;
  return function() {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function parseEventLines(log, start, end) {
  const i=log.indexOf(start);
  assert(i>=0, 'delivery event start not found: '+start);
  const j=end ? log.indexOf(end,i+start.length) : log.length;
  const section=log.slice(i, j>=0?j:log.length);
  const out=[];
  for (const rawLine of section.split(/\r?\n/)) {
    const line=rawLine.trim();
    const m=line.match(/^[1-5]\.\s*(.+)$/);
    if (m) {
      const values=m[1].split(',').map(x=>Number(x.trim()));
      assert(values.length===6 && values.every(n=>Number.isInteger(n)&&n>=1&&n<=45), 'invalid comma-delimited delivery line');
      out.push(values);
    }
  }
  return out.slice(0,5);
}
function evaluateLines(lines, draw) {
  const drawSet=new Set(draw);
  const hits=lines.map(line=>line.filter(n=>drawSet.has(n)).length);
  const union=[...new Set(lines.flat())];
  const covered=union.filter(n=>drawSet.has(n));
  const max=Math.max(...hits);
  return {
    line_hits:hits,
    hit_distribution_0_to_6:Array.from({length:7},(_,k)=>hits.filter(x=>x===k).length),
    max_hits:max,
    any2:max>=2, any3:max>=3, any4:max>=4, any5:max>=5, any6:max>=6,
    union_size:union.length,
    winning_union_numbers:covered.length,
    winning_union_coverage:covered.length,
    winning_numbers_in_union:covered.length,
    bonus_match_count:lines.reduce((s,l)=>s+(l.includes(draw.bonus)?1:0),0)
  };
}
function csvEscape(v) {
  const s=String(v);
  return /[,"\n]/.test(s) ? '"' + s.replace(/"/g,'""') + '"' : s;
}
function writeCsv(p, rows, cols) {
  const body=[cols.join(','), ...rows.map(r=>cols.map(c=>csvEscape(r[c])).join(','))].join('\n')+'\n';
  fs.writeFileSync(p, body);
}
function jsonWrite(p,obj) { fs.writeFileSync(p, JSON.stringify(obj,null,2)+'\n'); }

function main() {
  const dataRaw=fs.readFileSync(DATA);
  const dataSha=sha256(dataRaw);
  const dataBlob=blobSha(DATA);
  assert(dataSha===EXPECT.dataSha256, 'current canonical data SHA mismatch');
  assert(dataBlob===EXPECT.dataBlob, 'current canonical data git blob mismatch');
  const dataRows=parseCsv(DATA);
  assert(dataRows.length===1250, 'canonical data row count must be 1250');
  const dataMap=new Map();
  for(let i=0;i<dataRows.length;i++){
    const r=dataRows[i], round=Number(r.round);
    assert(round===i+1, 'round sequence gap/duplicate at index '+i);
    const mainNums=[r.no1,r.no2,r.no3,r.no4,r.no5,r.no6].map(Number);
    const bonus=Number(r.bonus);
    assert(mainNums.length===6 && unique(mainNums), 'invalid main numbers round '+round);
    assert(mainNums.every(n=>Number.isInteger(n)&&n>=1&&n<=45), 'main number range round '+round);
    assert(Number.isInteger(bonus)&&bonus>=1&&bonus<=45&&!mainNums.includes(bonus), 'bonus invalid/overlap round '+round);
    dataMap.set(round,{main:mainNums,bonus});
  }
  assert(dataMap.has(1249)&&dataMap.has(1250)&&!dataMap.has(1251),'cutoff must end at 1250');

  const predPath=path.join(E045,'PREDICTIONS.csv');
  const predRaw=fs.readFileSync(predPath);
  const predSha=sha256(predRaw), predBlob=blobSha(predPath);
  assert(predSha===EXPECT.e045PredSha256,'E045 prediction content SHA mismatch');
  assert(predBlob===EXPECT.e045PredBlob,'E045 prediction git blob mismatch');
  const pred=parseCsv(predPath);
  assert(pred.length===849,'E045 target count must be 849');
  const series=[];
  const targetSummaries=[];
  for(let i=0;i<pred.length;i++){
    const r=pred[i], target=Number(r.target_round), train=Number(r.training_through_round);
    assert(target===401+i,'E045 target continuity failure at '+i);
    assert(train===target-1,'E045 cutoff violation target '+target);
    const lines=[nums(r.line1),nums(r.line2),nums(r.line3)];
    assert(lines.every(x=>x.length===6&&unique(x)&&x.every(n=>Number.isInteger(n)&&n>=1&&n<=45)),'invalid ticket target '+target);
    const union=[...new Set(lines.flat())];
    assert(union.length===18,'E045 union geometry failure target '+target);
    const actual=nums(r.actual_numbers);
    assert(actual.length===6&&unique(actual)&&actual.every(n=>n>=1&&n<=45),'invalid actual draw target '+target);
    const aset=new Set(actual);
    const lh=lines.map(l=>l.filter(n=>aset.has(n)).length);
    const max=Math.max(...lh);
    const cov=union.filter(n=>aset.has(n)).length;
    assert(lh[0]===Number(r.line1_hits)&&lh[1]===Number(r.line2_hits)&&lh[2]===Number(r.line3_hits),'stored line hit mismatch target '+target);
    assert(max===Number(r.max_hits),'stored max hit mismatch target '+target);
    assert((max>=2?1:0)===Number(r.any2),'stored any2 mismatch target '+target);
    assert((max>=3?1:0)===Number(r.any3),'stored any3 mismatch target '+target);
    assert(cov===Number(r.winning_union_coverage),'stored union coverage mismatch target '+target);
    const vec=[max-NULLS[0],(max>=2?1:0)-NULLS[1],(max>=3?1:0)-NULLS[2],cov-NULLS[3]];
    series.push(vec);
    targetSummaries.push({target_round:target,training_through_round:train,paired_difference:vec});
  }

  const randomPath=path.join(E045,'RANDOM_BASELINE.csv');
  const randomRaw=fs.readFileSync(randomPath);
  const randomSha=sha256(randomRaw), randomBlob=blobSha(randomPath);
  assert(randomSha===EXPECT.e045RandomSha256,'E045 random comparator SHA mismatch');
  assert(randomBlob===EXPECT.e045RandomBlob,'E045 random comparator blob mismatch');
  const randomRows=parseCsv(randomPath);
  assert(randomRows.length===849,'E045 random row count mismatch');
  for(let i=0;i<randomRows.length;i++){
    const r=randomRows[i];
    assert(Number(r.target_round)===401+i,'random target alignment mismatch');
    assert(Number(r.geometry_violations)===0,'random geometry violation');
    assert(Math.abs(Number(r.exact_null_mean_max_hit)-NULLS[0])<1e-12,'exact max null mismatch');
    assert(Math.abs(Number(r.exact_null_p_any2)-NULLS[1])<1e-12,'exact any2 null mismatch');
    assert(Math.abs(Number(r.exact_null_p_any3)-NULLS[2])<1e-12,'exact any3 null mismatch');
    assert(Math.abs(Number(r.exact_null_expected_union_coverage)-NULLS[3])<1e-12,'exact coverage null mismatch');
  }

  const blocks=[];
  for(let start=0;start<800;start+=50){
    const block=series.slice(start,start+50);
    blocks.push({start:401+start,end:450+start,length:50,mean:METRICS.map((_,j)=>mean(block.map(x=>x[j])))});
  }
  const remainder=series.slice(800);
  assert(remainder.length===49,'historical final remainder must be retained as 49 targets');
  blocks.push({start:1201,end:1249,length:49,mean:METRICS.map((_,j)=>mean(remainder.map(x=>x[j])))});
  const sds=METRICS.map((_,j)=>sd(blocks.map(b=>b.mean[j])));
  const e046BlockPath=path.join(E046,'BLOCK_SUMMARIES.csv');
  const e046GridPath=path.join(E046,'DESIGN_GRID.csv');
  const e046BlockBlob=blobSha(e046BlockPath);
  const e046GridBlob=blobSha(e046GridPath);
  assert(e046GridBlob===EXPECT.e046GridBlob,'E046 design grid blob mismatch');
  const e046Blocks=parseCsv(e046BlockPath);
  assert(e046Blocks.length===68,'E046 block summary row count mismatch');
  const expectedE046=[0.10561720038713017,0.06143217076954477,0.042608134434911835,0.16853955687877298];
  for(let j=0;j<4;j++) assert(Math.abs(sds[j]-expectedE046[j])<1e-12,'historical block SD differs from E046 metric '+METRICS[j]);
  for(const b of blocks){
    for(let j=0;j<4;j++){
      const e=e046Blocks.find(x=>Number(x.block_index)===blocks.indexOf(b)+1&&x.metric===METRICS[j]);
      assert(e && Math.abs(Number(e.mean_paired_difference)-b.mean[j])<1e-12,'E046 block source mismatch '+b.start+' '+METRICS[j]);
    }
  }

  const e046Grid=parseCsv(e046GridPath);
  const e046Map=new Map();
  for(const r of e046Grid){
    e046Map.set(Number(r.prospective_target_count)+'|'+Number(r.standardized_effect_size_d),{
      independence:Number(r.joint_power_independence_approx),
      conservative:Number(r.joint_power_conservative_union_lower)
    });
  }

  const correlation={};
  for(let i=0;i<4;i++){
    correlation[METRICS[i]]={};
    for(let j=0;j<4;j++) correlation[METRICS[i]][METRICS[j]]=corr(blocks.map(b=>b.mean[i]),blocks.map(b=>b.mean[j]));
  }

  const results=[];
  const gridRows=[];
  let cell=0;
  for(const n of NS){
    const fullCount=Math.floor(n/50), rem=n%50;
    const blockLengths=Array(fullCount).fill(50);
    if(rem>0) blockLengths.push(rem);
    const varianceFactor=blockLengths.reduce((s,len)=>s+(len/n)*(len/n),0);
    const requiredPositiveBlocks=Math.ceil(0.65*blockLengths.length);
    let partialWindows=[];
    if(rem>0){
      for(let start=0;start+rem<=series.length;start++){
        const w=series.slice(start,start+rem);
        partialWindows.push(METRICS.map((_,j)=>mean(w.map(x=>x[j]))));
      }
      assert(partialWindows.length>0,'no partial remainder windows for '+rem);
    }
    for(const d of DS){
      const rng=mulberry32((BASE_SEED+cell*7919)>>>0); cell++;
      let joint=0, blockPass=0;
      const ciPass=[0,0,0,0];
      for(let rep=0;rep<REPS;rep++){
        const sums=[0,0,0,0];
        let pos=0, bi=0;
        for(let b=0;b<fullCount;b++){
          const v=blocks[Math.floor(rng()*16)].mean;
          for(let j=0;j<4;j++) sums[j]+=50*(v[j]+d*sds[j]);
          if(v[1]+d*sds[1]>0) pos++;
          bi++;
        }
        if(rem>0){
          const v=partialWindows[Math.floor(rng()*partialWindows.length)];
          for(let j=0;j<4;j++) sums[j]+=rem*(v[j]+d*sds[j]);
          if(v[1]+d*sds[1]>0) pos++;
          bi++;
        }
        const lowers=[];
        for(let j=0;j<4;j++){
          const lower=sums[j]/n-Z*sds[j]*Math.sqrt(varianceFactor);
          lowers.push(lower);
          if(lower>0) ciPass[j]++;
        }
        const blockOk=pos>=requiredPositiveBlocks;
        if(blockOk) blockPass++;
        if(blockOk && lowers.every(x=>x>0)) joint++;
      }
      const wci=wilson(joint,REPS);
      const e046=e046Map.get(n+'|'+d)||null;
      const row={
        prospective_targets:n,
        full_50_target_blocks:fullCount,
        final_remainder_targets:rem,
        blocks_including_remainder:blockLengths.length,
        remainder_included:rem>0,
        standardized_effect_d:d,
        simulation_replicates:REPS,
        max_hits_ci_positive_probability:ciPass[0]/REPS,
        any2_ci_positive_probability:ciPass[1]/REPS,
        any3_ci_positive_probability:ciPass[2]/REPS,
        union_coverage_ci_positive_probability:ciPass[3]/REPS,
        any2_positive_block_share_gate_probability:blockPass/REPS,
        joint_strict_gate_probability:joint/REPS,
        joint_strict_gate_wilson95_lower:wci[0],
        joint_strict_gate_wilson95_upper:wci[1],
        e046_independence_approximation:e046?e046.independence:null,
        e046_conservative_union_lower:e046?e046.conservative:null,
        joint_minus_e046_independence:e046?(joint/REPS-e046.independence):null
      };
      results.push(row);
      gridRows.push(row);
    }
  }

  const deliveryLog=readText(DELIVERY);
  const deliveryBlob=blobSha(DELIVERY);
  assert(deliveryBlob===EXPECT.deliveryBlob,'delivery log blob changed');
  const lines1249=parseEventLines(deliveryLog,'## Event 2026-11-06 — target round 1249','## Event 2026-11-13 — target round 1250');
  const lines1250=parseEventLines(deliveryLog,'## Event 2026-11-13 — target round 1250','## Evidence correction — target round 1250');
  assert(lines1249.length===5&&lines1250.length===5,'delivery ledger line extraction mismatch');
  const draw1249=dataMap.get(1249), draw1250=dataMap.get(1250);
  const review1249=evaluateLines(lines1249,draw1249.main);
  review1249.bonus_match_count=lines1249.filter(l=>l.includes(draw1249.bonus)).length;
  const review1250=evaluateLines(lines1250,draw1250.main);
  review1250.bonus_match_count=lines1250.filter(l=>l.includes(draw1250.bonus)).length;
  const registry=JSON.parse(readText(PURCHASE_REGISTRY));
  const target1251=JSON.parse(readText(TARGET1251));
  const v9=JSON.parse(readText(V9_1250));
  const external=JSON.parse(readText(EXTERNAL));
  assert(blobSha(PURCHASE_REGISTRY)===EXPECT.purchaseRegistryBlob,'purchase registry blob mismatch');
  assert(blobSha(TARGET1251)===EXPECT.target1251Blob,'target1251 research-selected source blob mismatch');
  assert(blobSha(V9_1250)===EXPECT.v9Blob,'target1250 V9 source blob mismatch');
  assert(registry.confirmed_purchases.length===0,'purchase registry is not empty; review needs reclassification');
  assert(target1251.target_round===1251&&target1251.target_draw_date==='2026-11-21','target 1251 metadata mismatch');
  assert(target1251.status.strict_portfolio_pass===false&&target1251.status.purchase_confirmation==='NOT_CONFIRMED','target 1251 status mismatch');
  assert(v9.target_round===1250&&v9.data_cutoff===1249&&v9.strict_portfolio_pass===undefined,'target 1250 V9 provenance mismatch');
  assert(external.status==='PASS'&&external.repo_data_cutoff===1250&&external.repo_vs_fallback_numbers_match===true,'external data crosscheck mismatch');
  const review={
    as_of_kst:'2026-11-21T08:03:38+09:00',
    source:{
      delivery_log_blob_sha:deliveryBlob,
      canonical_data_sha256:dataSha,
      canonical_data_blob_sha:dataBlob,
      purchase_confirmation_registry_blob_sha:blobSha(PURCHASE_REGISTRY),
      confirmed_purchase_count:registry.confirmed_purchases.length
    },
    target_1249:{
      provenance:'USER_VISIBLE_INTERMEDIATE_CANDIDATE_RECORDED_IN_DELIVERY_LOG',
      strict_status:'FAIL_NOT_STRICT_PASS',
      purchase_confirmation:'NOT_CONFIRMED',
      source_presealed_artifact:'NOT_FOUND_PER_DELIVERY_LOG_CAVEAT',
      winning_main_numbers:dataMap.get(1249).main,
      bonus:dataMap.get(1249).bonus,
      comparison:review1249
    },
    target_1250:{
      provenance:'PRESERVED_CANDIDATE_LINES_IN_DELIVERY_LOG_BUT_DISPLAY_EVIDENCE_CORRECTED_AS_UNVERIFIED',
      strict_status:'STRICT_PASS_NOT_READY',
      purchase_confirmation:'NOT_CONFIRMED',
      canonical_source_artifact:'analysis/2026-11-14/FIVE_ROLE_RESEARCH_1250_V9.json',
      source_artifact_sha256:sha256(fs.readFileSync(V9_1250)),
      source_artifact_blob_sha:blobSha(V9_1250),
      source_cutoff:1249,
      winning_main_numbers:dataMap.get(1250).main,
      bonus:dataMap.get(1250).bonus,
      comparison:review1250,
      inclusion_rule:'Descriptive saved-candidate diagnostic only; not a verified delivery and not an actual purchase.'
    },
    target_1251:{
      provenance:'RESEARCH_SELECTED_LINES_ARTIFACT_AND_DELIVERY_LOG_EVENT_2026-11-20',
      source_artifact_blob_sha:blobSha(TARGET1251),
      source_cutoff:1250,
      draw_date:'2026-11-21',
      draw_outcome_status:'NOT_YET_PUBLISHED_AS_OF_AUDIT_TIME',
      comparison_status:'DEFERRED_UNTIL_OFFICIAL_DRAW_RESULT',
      purchase_confirmation:'NOT_CONFIRMED',
      strict_status:'STRICT_FAIL',
      line_numbers_reproduced_or_printed:false
    },
    learning_boundary:{
      actual_purchase_learning_eligible_targets:0,
      no_purchase_receipt_or_explicit_confirmation_found:true,
      recommendation_review_is_separate_from_actual_purchase_learning:true,
      no_source_lines_reconstructed:true,
      no_delivery_log_append_needed_in_this_run:true
    }
  };

  const reportLines=[];
  reportLines.push('# E078 — Empirical multivariate block-resampling power stress test');
  reportLines.push('');
  reportLines.push('**Classification: DESIGN-ONLY / HISTORICAL-INPUT STRESS TEST. Not model evidence, not a strict PASS, and not prospective confirmation.**');
  reportLines.push('');
  reportLines.push('## Question and frozen design');
  reportLines.push("Does preserving the empirical joint distribution of the four strict-gate endpoint block means change the prospective confirmation power picture relative to E046's normal-theory independence approximation?");
  reportLines.push('');
  reportLines.push('- Source cutoff: 1249; targets 401–1249 (849), already inspected/live-history material.');
  reportLines.push('- Four endpoints: max-hit, any2, any3, winning-union coverage, each differenced from the exact disjoint-union18 null.');
  reportLines.push('- 16 complete 50-target source blocks plus the final 49-target remainder; the remainder is retained.');
  reportLines.push('- Empirical multivariate block vectors are resampled jointly, preserving observed cross-endpoint dependence. The final prospective remainder is sampled from all contiguous source windows of the same length.');
  reportLines.push('- Hypothetical effect sizes: 0.25/0.50/0.75/1.00 historical block SD per endpoint. No model or gate is changed.');
  reportLines.push('- '+REPS+' Monte Carlo trajectories per grid cell; family alpha 0.05, per-endpoint alpha 0.0125, critical z '+Z+'.');
  reportLines.push('');
  reportLines.push('## Source and integrity');
  reportLines.push('- Canonical current data: 1–1250, SHA256 '+dataSha+', Git blob '+dataBlob+'. Round 1251 is not present.');
  reportLines.push('- E045 prediction source: SHA256 '+predSha+', Git blob '+predBlob+'. 849/849 targets; cutoff violations 0; all three-line union18 geometries and stored hits recomputed.');
  reportLines.push('- E045 exact comparator source: SHA256 '+randomSha+', Git blob '+randomBlob+'. 849/849 targets; geometry violations 0.');
  reportLines.push('- Historical block SDs reproduce E046 exactly: '+sds.map(x=>x.toFixed(9)).join(', ')+'.');
  reportLines.push('- 1244–1249 are contaminated live-history diagnostics, not clean holdout or prospective evidence.');
  reportLines.push('');
  reportLines.push('## Joint gate probability (empirical block resampling)');
  reportLines.push('');
  reportLines.push('| Targets | d | Full blocks + remainder | Joint gate probability | Wilson 95% interval | E046 independence approx. |');
  reportLines.push('|---:|---:|---:|---:|---:|---:|');
  for(const r of results){
    reportLines.push('| '+r.prospective_targets+' | '+r.standardized_effect_d.toFixed(2)+' | '+r.full_50_target_blocks+(r.final_remainder_targets?' + '+r.final_remainder_targets:'')+' | '+(100*r.joint_strict_gate_probability).toFixed(2)+'% | '+(100*r.joint_strict_gate_wilson95_lower).toFixed(2)+'–'+(100*r.joint_strict_gate_wilson95_upper).toFixed(2)+'% | '+(r.e046_independence_approximation===null?'—':(100*r.e046_independence_approximation).toFixed(2)+'%')+' |');
  }
  reportLines.push('');
  reportLines.push('## Interpretation');
  reportLines.push('This is a planning stress test only. The source contains just 16 complete non-overlapping 50-target blocks plus one 49-target remainder, so empirical block resampling has limited support and cannot establish future power or model edge. The E046 independence approximation is not treated as ground truth; the empirical joint estimate retains endpoint correlation but remains conditional on historical block behavior. Neither method replaces the operational moving-block bootstrap on future, pre-registered prospective outcomes.');
  reportLines.push('');
  reportLines.push('The prospective minimum target count and completion rule remain unspecified. This study does not choose or adopt either, does not relax the strict gate, and cannot create STRICT_PASS_READY or purchase lines.');
  reportLines.push('');
  reportLines.push('## Recommendation delivery audit');
  reportLines.push('- Target 1249: the DELIVERY_LOG records an intermediate candidate display, strict FAIL, and no purchase confirmation. Its post-draw line/union metrics are stored in DELIVERY_REVIEW_1249_1250_1251.json; the original log is unchanged.');
  reportLines.push('- Target 1250: preserved lines are evaluated only as an unverified saved-candidate diagnostic because the append-only evidence correction says the user-visible display is not independently verified. Excluded from actual-purchase learning.');
  reportLines.push('- Target 1251: the 2026-11-20 research-selected artifact is pre-draw; outcome comparison is deferred until the official 2026-11-21 result. Purchase is not confirmed.');
  reportLines.push('- Confirmed purchases in the registry: '+registry.confirmed_purchases.length+'. No purchase-learning aggregate is updated.');
  reportLines.push('');
  reportLines.push('## Decision');
  reportLines.push('E078 computation completed as a design-only uncertainty stress test. No predictive model is promoted; no candidate numbers or purchase lines are generated or displayed; no freeze/seal is created.');
  fs.mkdirSync(OUT,{recursive:true});
  jsonWrite(path.join(OUT,'RESULTS.json'),{
    study_id:'E078_THREE_LINE_EMPIRICAL_BLOCK_POWER_STRESS_v1',
    classification:'DESIGN_ONLY_HISTORICAL_INPUT_STRESS_TEST_NOT_MODEL_EVIDENCE',
    source_cutoff:1249,target_range:[401,1249],target_count:849,
    source_sha256:{canonical_data:dataSha,e045_predictions:predSha,e045_random_baseline:randomSha},
    source_git_blob_sha:{canonical_data:dataBlob,e045_predictions:predBlob,e045_random_baseline:randomBlob,e046_design_grid:e046GridBlob,e046_block_summaries:e046BlockBlob},
    exact_null:{max_hits:NULLS[0],any2:NULLS[1],any3:NULLS[2],winning_union_coverage:NULLS[3]},
    block_source:{complete_blocks:16,final_remainder_targets:49,total_blocks:17,sd_by_metric:Object.fromEntries(METRICS.map((m,i)=>[m,sds[i]])),correlation_matrix:correlation,means:blocks},
    simulation:{target_counts:NS,effect_sizes_block_sd:DS,replicates_per_cell:REPS,seed:BASE_SEED,critical_z:Z,alpha_per_metric:0.0125,block_share_min:0.65,final_remainder_retained:true,method:'joint empirical resampling of 50-target block vectors; same-length contiguous-window resampling for final remainder; fixed historical block SD for planning lower bound'},
    results,
    limitations:['Only 16 full historical blocks plus one 49-target remainder are available.','All source targets are historical and previously inspected; not untouched or prospective.','This design approximation is not the operational moving-block bootstrap.','No prospective minimum target count or completion rule is adopted.','No model or purchase policy promotion.']
  });
  writeCsv(path.join(OUT,'SIMULATION_GRID.csv'),gridRows,Object.keys(gridRows[0]));
  writeCsv(path.join(OUT,'BLOCK_SOURCE_SUMMARIES.csv'),blocks.map((b,i)=>({block_index:i+1,target_start:b.start,target_end:b.end,block_length:b.length,max_hits:b.mean[0],any2:b.mean[1],any3:b.mean[2],winning_union_coverage:b.mean[3]})),['block_index','target_start','target_end','block_length','max_hits','any2','any3','winning_union_coverage']);
  jsonWrite(path.join(OUT,'DELIVERY_REVIEW_1249_1250_1251.json'),review);
  jsonWrite(path.join(OUT,'VERIFICATION.json'),{
    study_id:'E078_THREE_LINE_EMPIRICAL_BLOCK_POWER_STRESS_v1',
    status:'PASS_DESIGN_COMPUTATION_ONLY',
    checks:{
      canonical_data_sha_and_blob_match:true,canonical_data_rows:1250,canonical_round_sequence:true,
      e045_prediction_content_and_blob_match:true,e045_targets:849,e045_target_range:[401,1249],
      cutoff_violations:0,invalid_tickets:0,geometry_violations:0,stored_hit_mismatches:0,
      e045_random_source_hashes_match:true,random_geometry_violations:0,exact_null_match:true,
      e046_block_summary_reproduced:true,final_49_target_remainder_retained:true,
      simulation_cells:results.length,replicates_per_cell:REPS,all_results_finite:results.every(r=>Object.values(r).filter(x=>typeof x==='number').every(Number.isFinite)),
      no_target_1250_or_1251_outcome_used:true,no_future_leakage:true,
      contaminated_rounds_1244_to_1249_labelled:true,prospective_rule_not_invented:true,
      no_candidate_or_purchase_lines_generated:true,no_freeze_or_seal_created:true
    },
    historical_live_history_scope:[1244,1245,1246,1247,1248,1249],
    evidence_class:'DESIGN_ONLY_NOT_PROSPECTIVE_CONFIRMATION'
  });
  fs.writeFileSync(path.join(OUT,'REPORT.md'),reportLines.join('\n')+'\n');
  const files=['RESULTS.json','SIMULATION_GRID.csv','BLOCK_SOURCE_SUMMARIES.csv','DELIVERY_REVIEW_1249_1250_1251.json','VERIFICATION.json','REPORT.md'];
  const manifest={study_id:'E078_THREE_LINE_EMPIRICAL_BLOCK_POWER_STRESS_v1',files:{}};
  for(const f of files) manifest.files[f]={sha256:sha256(fs.readFileSync(path.join(OUT,f))),bytes:fs.statSync(path.join(OUT,f)).size};
  jsonWrite(path.join(OUT,'SHA256_MANIFEST.json'),manifest);
  jsonWrite(path.join(OUT,'COMPLETION.json'),{
    study_id:'E078_THREE_LINE_EMPIRICAL_BLOCK_POWER_STRESS_v1',
    status:'COMPLETE_DESIGN_ONLY',
    source_cutoff:1249,target_count:849,simulation_cells:results.length,replicates_per_cell:REPS,
    no_future_leakage:true,strict_pass_ready:false,purchase_lines_generated:false,freeze_or_seal_created:false,
    output_files:files.concat(['SHA256_MANIFEST.json','COMPLETION.json'])
  });
  console.log(JSON.stringify({status:'COMPLETE',out:OUT,cells:results.length,replicates:REPS,blockSd:sds,correlation:correlation,review1249:review1249,review1250:review1250},null,2));
}
main();
