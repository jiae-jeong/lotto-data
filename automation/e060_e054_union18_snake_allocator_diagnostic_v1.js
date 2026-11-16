#!/usr/bin/env node
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

function parseCsv(raw) {
  const lines = raw.replace(/^\uFEFF/, "").trimEnd().split(/\r?\n/);
  const headers = lines.shift().split(",");
  return lines.filter(line => line.trim()).map(line => {
    const cells = line.split(",");
    if (cells.length !== headers.length) throw new Error("CSV column count mismatch");
    return Object.fromEntries(headers.map((h, i) => [h, cells[i]]));
  });
}
function numbers(value) {
  return value.trim().split(/\s+/).map(Number).sort((a,b)=>a-b);
}
function xorshift32(seed) {
  let x = seed >>> 0;
  if (x === 0) x = 0x9e3779b9;
  return () => {
    x ^= x << 13; x ^= x >>> 17; x ^= x << 5;
    return (x >>> 0) / 4294967296;
  };
}
function randomPortfolio(rng) {
  const a = Array.from({length:45}, (_,i)=>i+1);
  for (let i=a.length-1;i>0;i--) {
    const j=Math.floor(rng()*(i+1));
    [a[i],a[j]]=[a[j],a[i]];
  }
  return [a.slice(0,6),a.slice(6,12),a.slice(12,18)].map(x=>x.sort((a,b)=>a-b));
}
function metrics(lines, actual) {
  const union = new Set(lines.flat());
  if (lines.length!==3 || lines.some(x=>x.length!==6 || new Set(x).size!==6) || union.size!==18)
    throw new Error("Invalid three-line disjoint union18 geometry");
  const hits = lines.map(line=>line.filter(n=>actual.has(n)).length);
  const maxHits = Math.max(...hits);
  return {max_hits:maxHits, any2:Number(maxHits>=2), any3:Number(maxHits>=3), winning_union_coverage:[...union].filter(n=>actual.has(n)).length};
}
function snakePartition(lines) {
  const union=[...new Set(lines.flat())].sort((a,b)=>a-b);
  if(union.length!==18) throw new Error("Candidate union is not 18");
  const ix=[[0,5,6,11,12,17],[1,4,7,10,13,16],[2,3,8,9,14,15]];
  return ix.map(row=>row.map(i=>union[i]).sort((a,b)=>a-b));
}
function movingBlockCi(values, seed, replicates=4000, blockSize=50) {
  const rng=xorshift32(seed);
  const sizes=Array(Math.floor(values.length/blockSize)).fill(blockSize);
  const remainder=values.length%blockSize;
  if(remainder) sizes.push(remainder);
  const means=[];
  for(let r=0;r<replicates;r++) {
    let sum=0, count=0;
    for(const size of sizes) {
      const start=Math.floor(rng()*(values.length-size+1));
      for(let i=start;i<start+size;i++){sum+=values[i];count++;}
    }
    if(count!==values.length) throw new Error("Bootstrap sample length mismatch");
    means.push(sum/count);
  }
  means.sort((a,b)=>a-b);
  const alpha=0.0125;
  return [means[Math.floor((alpha/2)*(replicates-1))],means[Math.floor((1-alpha/2)*(replicates-1))]];
}
function csvEscape(v) {
  const s=String(v);
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g,'""') + '"' : s;
}
function writeCsv(file, rows, fields) {
  const out=[fields.join(",")];
  for(const row of rows) out.push(fields.map(k=>csvEscape(row[k] ?? "")).join(","));
  fs.writeFileSync(file, out.join("\n")+"\n", "utf8");
}
function writeJson(file, obj) { fs.writeFileSync(file, JSON.stringify(obj,null,2)+"\n","utf8"); }
function sha256(file) { return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex"); }

function run(root, outdir) {
  const dataPath=path.join(root,"lotto_data.csv");
  const predPath=path.join(root,"analysis/2026-11-16/gha_43738196136_1/E054_THREE_LINE_ROLLING_CONCENTRATION_REGIME_v1/PREDICTIONS.csv");
  const dataRaw=fs.readFileSync(dataPath);
  const dataSha=crypto.createHash("sha256").update(dataRaw).digest("hex");
  const data=parseCsv(dataRaw.toString("utf8"));
  const pred=parseCsv(fs.readFileSync(predPath,"utf8"));
  if(data.length!==1250 || pred.length!==850) throw new Error("Unexpected source row count");
  const byRound=new Map(data.map(r=>[Number(r.round),r]));
  const exact={max_hits:1.514256248572755,any2:0.47497624326892623,any3:0.07135490714617204,winning_union_coverage:2.4};
  const observed={E054:[],NUMERIC_SNAKE:[]}, randomRows=[], predictionRows=[];
  let geometryViolations=0, randomGeometryViolations=0, cutoffViolations=0, unionMismatch=0;
  const randomCount=120;
  for(let i=0;i<pred.length;i++) {
    const p=pred[i], t=Number(p.target_round), training=Number(p.training_through_round);
    if(t!==401+i || training!==t-1) {cutoffViolations++;throw new Error("Target/training cutoff mismatch at "+t);}
    const source=byRound.get(t);
    if(!source) throw new Error("Missing source target "+t);
    const lines=[numbers(p.line1),numbers(p.line2),numbers(p.line3)];
    const union=[...new Set(lines.flat())];
    if(union.length!==18) {geometryViolations++;throw new Error("E054 geometry invalid at "+t);}
    const snake=snakePartition(lines);
    if([...new Set(snake.flat())].sort((a,b)=>a-b).join(",")!==union.slice().sort((a,b)=>a-b).join(",")) {unionMismatch++;throw new Error("Snake changed candidate union at "+t);}
    const actualData=Array.from({length:6},(_,k)=>Number(source["no"+(k+1)]));
    const actualPred=numbers(p.actual_numbers);
    if(actualData.slice().sort((a,b)=>a-b).join(" ")!==actualPred.join(" ")) throw new Error("E054 target outcomes differ from canonical data at "+t);
    const actual=new Set(actualData);
    const e=metrics(lines,actual), s=metrics(snake,actual);
    observed.E054.push(e); observed.NUMERIC_SNAKE.push(s);
    const seed=(20261116060 + t*1009)>>>0, rng=xorshift32(seed);
    const sums={max_hits:0,any2:0,any3:0,winning_union_coverage:0};
    for(let r=0;r<randomCount;r++) {
      const rp=randomPortfolio(rng), rm=metrics(rp,actual);
      if(new Set(rp.flat()).size!==18) randomGeometryViolations++;
      for(const k of Object.keys(sums)) sums[k]+=rm[k];
    }
    const means={};
    for(const k of Object.keys(sums)) means[k]=sums[k]/randomCount;
    randomRows.push({target_round:t,random_bundles:randomCount,...means});
    predictionRows.push({
      target_round:t,training_through_round:training,
      e054_line1:lines[0].join(" "),e054_line2:lines[1].join(" "),e054_line3:lines[2].join(" "),
      snake_line1:snake[0].join(" "),snake_line2:snake[1].join(" "),snake_line3:snake[2].join(" "),
      actual_numbers:actualData.slice().sort((a,b)=>a-b).join(" "),
      e054_max_hits:e.max_hits,e054_any2:e.any2,e054_any3:e.any3,e054_union_coverage:e.winning_union_coverage,
      snake_max_hits:s.max_hits,snake_any2:s.any2,snake_any3:s.any3,snake_union_coverage:s.winning_union_coverage
    });
  }
  const keys=Object.keys(exact), inference={}, blockRows=[];
  for(let ai=0;ai<2;ai++) {
    const name=ai===0?"E054":"NUMERIC_SNAKE", rows=observed[name], metricsOut={};
    for(let mi=0;mi<keys.length;mi++) {
      const k=keys[mi], values=rows.map(x=>x[k]-exact[k]);
      const ci=movingBlockCi(values,(20261116060 + ai*1000003 + mi*9001)>>>0);
      const blocks=[];
      for(let start=0;start<values.length;start+=50) blocks.push(values.slice(start,start+50));
      const positive=blocks.filter(b=>b.reduce((a,b)=>a+b,0)/b.length>0).length;
      const blockShare=positive/blocks.length;
      blocks.forEach((b,bi)=>blockRows.push({allocator:name,metric:k,block_index:bi+1,target_start:401+bi*50,target_end:401+bi*50+b.length-1,mean_delta:b.reduce((a,b)=>a+b,0)/b.length,positive:Number(b.reduce((a,b)=>a+b,0)/b.length>0)}));
      metricsOut[k]={observed_mean:rows.reduce((a,x)=>a+x[k],0)/rows.length,exact_null_mean:exact[k],delta_mean:values.reduce((a,b)=>a+b,0)/values.length,adjusted_moving_block_ci:ci,lower_bound_strictly_gt_zero:ci[0]>0,positive_50_target_blocks:positive,block_count:blocks.length,positive_block_share:blockShare,block_share_gate_pass:blockShare>=0.65};
    }
    const historicalGatePass=keys.every(k=>metricsOut[k].lower_bound_strictly_gt_zero) && metricsOut.any2.block_share_gate_pass;
    inference[name]={metrics:metricsOut,historical_strict_gate_diagnostic:historicalGatePass,strict_pass_ready:false,promotion:false};
  }
  const randomMean={};
  for(const k of keys) randomMean[k]=randomRows.reduce((a,r)=>a+r[k],0)/randomRows.length;
  const randomCheck={};
  for(const k of keys) randomCheck[k]={empirical_random_mean:randomMean[k],exact_null_mean:exact[k],delta:randomMean[k]-exact[k]};
  const unionCoverageEqual=predictionRows.every(r=>r.e054_union_coverage===r.snake_union_coverage);
  if(!unionCoverageEqual) throw new Error("Union coverage differs despite frozen candidate set");
  fs.mkdirSync(outdir,{recursive:true});
  writeCsv(path.join(outdir,"PREDICTIONS.csv"),predictionRows,Object.keys(predictionRows[0]));
  writeCsv(path.join(outdir,"RANDOM_BASELINE.csv"),randomRows,Object.keys(randomRows[0]));
  writeCsv(path.join(outdir,"BLOCK_STABILITY.csv"),blockRows,Object.keys(blockRows[0]));
  writeJson(path.join(outdir,"INFERENCE.json"),{
    study_id:"E060_E054_UNION18_SNAKE_ALLOCATOR_DIAGNOSTIC_v1",
    evidence_class:"HISTORICAL_ALLOCATOR_ONLY_SENSITIVITY_DIAGNOSTIC_NOT_INDEPENDENT_PREDICTIVE_EVIDENCE",
    data_cutoff:1250,target_range:[401,1250],targets:850,
    source_data_sha256:dataSha,
    candidate_union:"Frozen per-target E054 union18; unchanged across both allocations",
    alternative_allocator:"Sort the frozen 18-number union ascending, then assign indices [0,5,6,11,12,17], [1,4,7,10,13,16], [2,3,8,9,14,15] to three lines.",
    exact_null:exact,random_baseline:{bundles_per_target:randomCount,total_bundles:850*randomCount,means:randomCheck},
    allocators:inference,
    paired_partition_diagnostic:{
      union_coverage_identical_for_all_targets:unionCoverageEqual,
      mean_max_hits_delta_snake_minus_E054:predictionRows.reduce((a,r)=>a+r.snake_max_hits-r.e054_max_hits,0)/850,
      mean_any2_delta_snake_minus_E054:predictionRows.reduce((a,r)=>a+r.snake_any2-r.e054_any2,0)/850,
      mean_any3_delta_snake_minus_E054:predictionRows.reduce((a,r)=>a+r.snake_any3-r.e054_any3,0)/850
    },
    thresholds_changed:false,alpha_changed:false,block_length_changed:false,comparator_changed:false,
    parameter_search:false,variants_evaluated:1,purchase_lines_generated:false,strict_pass_ready:false,freeze_or_seal_created:false
  });
  writeJson(path.join(outdir,"VERIFICATION.json"),{
    status:"PASS",study_id:"E060_E054_UNION18_SNAKE_ALLOCATOR_DIAGNOSTIC_v1",
    data_rows:1250,data_cutoff:1250,data_sha256:dataSha,target_count:850,target_sequence_valid:true,
    e054_training_cutoff_violations:cutoffViolations,leakage_failures:0,future_predictions:0,
    e054_geometry_violations:geometryViolations,snake_geometry_violations:0,random_geometry_violations:randomGeometryViolations,
    candidate_union_mismatches:unionMismatch,union_coverage_identical:unionCoverageEqual,
    random_bundles_per_target:randomCount,random_bundles_total:850*randomCount,random_baseline_executed:true,
    bootstrap_replicates_per_metric:4000,block_length_targets:50,blocks:17,
    no_parameter_search:true,strict_thresholds_changed:false,alpha_changed:false,block_length_changed:false,comparator_changed:false,
    candidate_union_comes_from_frozen_E054_predictions:true,target_outcomes_read_only_after_portfolio_construction:true,
    strict_pass_ready_created:false,purchase_lines_generated:false,freeze_or_seal_created:false
  });
  writeJson(path.join(outdir,"COMPLETION.json"),{
    status:"COMPLETE",executed:true,study_id:"E060_E054_UNION18_SNAKE_ALLOCATOR_DIAGNOSTIC_v1",
    data_cutoff:1250,targets:850,random_bundles:102000,bootstrap_replicates_per_metric:4000,
    historical_allocator_diagnostic_only:true,strict_pass_ready:false,purchase_lines_generated:false,freeze_or_seal_created:false
  });
  const report=[
    "# E060 - E054 frozen-union18 allocator partition diagnostic",
    "",
    "Status: COMPLETE; historical allocator-only sensitivity diagnostic, not an independent predictive model and not purchase evidence.",
    "",
    "- Cutoff 1250; targets 401-1250 (850).",
    "- Candidate union18 is frozen from E054 predictions and is identical for both partitions.",
    "- Compared the original E054 three-line partition with one fixed numeric-order snake partition; no model, candidate, weight, or parameter search.",
    "- Random baseline: 120 exact-geometry disjoint-union18 portfolios per target (102,000 total).",
    "- Inference: four unchanged strict metrics, 4,000 moving-block bootstrap replicates, 50-target blocks, 17 blocks.",
    "",
    "## Results",
    "",
    ...["E054","NUMERIC_SNAKE"].flatMap(name=>[
      "### "+name,
      "",
      "| Metric | Observed | Exact null | Delta | Adjusted CI | Positive blocks |",
      "|---|---:|---:|---:|---:|---:|",
      ...keys.map(k=>{const m=inference[name].metrics[k];return "| "+k+" | "+m.observed_mean.toFixed(6)+" | "+m.exact_null_mean.toFixed(6)+" | "+m.delta_mean.toFixed(6)+" | ["+m.adjusted_moving_block_ci[0].toFixed(6)+", "+m.adjusted_moving_block_ci[1].toFixed(6)+"] | "+m.positive_50_target_blocks+"/17 |";}),
      "",
      "Historical gate diagnostic: "+(inference[name].historical_strict_gate_diagnostic?"PASS":"FAIL")+" (not eligible for readiness or promotion).",
      ""
    ]),
    "Union coverage is identical by construction because the 18-number candidate set is unchanged.",
    "",
    "No candidate numbers are promoted. No STRICT_PASS_READY, purchase lines, freeze, or seal are generated.",
    "",
    "The historical targets are already inspected/live-history material, not prospective confirmation."
  ].join("\n");
  fs.writeFileSync(path.join(outdir,"REPORT.md"),report+"\n","utf8");
  const files=["PREDICTIONS.csv","RANDOM_BASELINE.csv","BLOCK_STABILITY.csv","INFERENCE.json","VERIFICATION.json","COMPLETION.json","REPORT.md"];
  const manifestRows=files.map(name=>({path:name,sha256:sha256(path.join(outdir,name)),bytes:fs.statSync(path.join(outdir,name)).size}));
  writeCsv(path.join(outdir,"SHA256_MANIFEST.csv"),manifestRows,["path","sha256","bytes"]);
  return {targets:850,random_bundles:102000,metrics:inference,random_mean:randomCheck,manifest_entries:manifestRows.length,manifest_status:"PASS"};
}

if(require.main===module) {
  const root=process.argv[2]||process.cwd();
  const outdir=process.argv[3]||path.join(root,"analysis/2026-11-16/E060_E054_UNION18_SNAKE_ALLOCATOR_DIAGNOSTIC_v1");
  process.stdout.write(JSON.stringify(run(root,outdir),null,2)+"\n");
}
module.exports={run};
