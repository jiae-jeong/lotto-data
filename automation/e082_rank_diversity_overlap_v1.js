#!/usr/bin/env node
"use strict";
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const DATA_PATH = "data/snapshots/lotto_data_through_1251_20261122.csv";
const OUT_DIR = "analysis/2026-11-24/E082_RANK_DIVERSITY_OVERLAP_AUDIT_v1";
const EXPECTED_SHA256 = "2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9";
const EXPECTED_BLOB = "be2fa07921a92f335aeb6e715b4f40098e297834";
const START = 401, END = 1251;
const K_VALUES = [10, 15, 20, 25, 30];
const SIGNALS = ["recent30", "gap", "momentum", "balanced", "contrarian"];
const MODELS = ["CONSENSUS", "BORDA", "MIN_RANK"];
const CONTAMINATED = new Set([1244,1245,1246,1247,1248,1249,1250,1251]);

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
function spearman(rankA,rankB) {
  let d2=0;
  for(let n=1;n<=45;n++) d2+=(rankA[n]-rankB[n])**2;
  return 1-(6*d2)/(45*(45*45-1));
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
function analyze(raw) {
  const dataSha=sha256(raw), blobSha=gitBlobSha1(raw);
  if(dataSha!==EXPECTED_SHA256 || blobSha!==EXPECTED_BLOB) throw new Error("Source hash mismatch");
  const rows=parseRows(raw), perTarget=[], fullRank=[];
  const pairKeys=["CONSENSUS__BORDA","CONSENSUS__MIN_RANK","BORDA__MIN_RANK"];
  for(let t=START;t<=END;t++){
    const target=rows[t-1], hist=rows.slice(0,t-1).map(r=>r.nums);
    if(hist.length!==t-1) throw new Error("Cutoff mismatch at target "+t);
    const f=features(hist), comp={};
    SIGNALS.forEach(s=>comp[s]=rankSignal(f[s],s==="momentum"?f.momentumExact:null).rank);
    const consensus=rankSignal(f.consensus).order;
    const consensusRank={}; consensus.forEach((n,i)=>consensusRank[n]=i+1);
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
    const orders={CONSENSUS:consensus,BORDA:bordaOrder,MIN_RANK:minOrder};
    const ranks={CONSENSUS:consensusRank,BORDA:bordaRank,MIN_RANK:minRank};
    const winners=new Set(target.nums), row={target_round:t,training_through_round:t-1,contaminated_live_history:CONTAMINATED.has(t)};
    MODELS.forEach(m=>{
      K_VALUES.forEach(k=>{row[m.toLowerCase()+"_recall_at_"+k]=orders[m].slice(0,k).filter(n=>winners.has(n)).length/6;});
    });
    pairKeys.forEach(pair=>{
      const [a,b]=pair.split("__");
      row[pair+"_spearman"]=spearman(ranks[a],ranks[b]);
      K_VALUES.forEach(k=>{
        const setA=new Set(orders[a].slice(0,k)), setB=new Set(orders[b].slice(0,k));
        let inter=0; setA.forEach(n=>{if(setB.has(n))inter++;});
        let onlyA=0,onlyB=0;
        winners.forEach(n=>{if(setA.has(n)&&!setB.has(n))onlyA++;if(setB.has(n)&&!setA.has(n))onlyB++;});
        row[pair+"_K"+k+"_intersection"]=inter;
        row[pair+"_K"+k+"_jaccard"]=inter/(2*k-inter);
        row[pair+"_K"+k+"_onlyA_winner_hits"]=onlyA;
        row[pair+"_K"+k+"_onlyB_winner_hits"]=onlyB;
        row[pair+"_K"+k+"_net_unique_winner_rescue_A_minus_B"]=onlyA-onlyB;
      });
    });
    perTarget.push(row);
    fullRank.push({target_round:t,ranks});
  }
  const pairSummary={};
  pairKeys.forEach(pair=>{
    const [a,b]=pair.split("__"), rho=perTarget.map(r=>r[pair+"_spearman"]);
    pairSummary[pair]={
      mean_spearman:mean(rho),median_spearman:quantile(rho,.5),p10_spearman:quantile(rho,.1),p90_spearman:quantile(rho,.9),
      top_k:{}
    };
    K_VALUES.forEach(k=>{
      const ints=perTarget.map(r=>r[pair+"_K"+k+"_intersection"]);
      const jac=perTarget.map(r=>r[pair+"_K"+k+"_jaccard"]);
      const onlyA=perTarget.map(r=>r[pair+"_K"+k+"_onlyA_winner_hits"]);
      const onlyB=perTarget.map(r=>r[pair+"_K"+k+"_onlyB_winner_hits"]);
      const ra=perTarget.map(r=>r[a.toLowerCase()+"_recall_at_"+k]);
      const rb=perTarget.map(r=>r[b.toLowerCase()+"_recall_at_"+k]);
      pairSummary[pair].top_k[k]={
        mean_intersection:mean(ints),independent_uniform_expected_intersection:k*k/45,
        mean_jaccard:mean(jac),mean_unique_winner_hits_A_only:mean(onlyA),mean_unique_winner_hits_B_only:mean(onlyB),
        total_unique_winner_hits_A_only:onlyA.reduce((x,y)=>x+y,0),total_unique_winner_hits_B_only:onlyB.reduce((x,y)=>x+y,0),
        mean_recall_A:mean(ra),mean_recall_B:mean(rb),mean_recall_difference_A_minus_B:mean(ra.map((x,i)=>x-rb[i]))
      };
    });
  });
  const modelRecall={};
  MODELS.forEach(m=>{
    modelRecall[m]={};
    K_VALUES.forEach(k=>{
      const xs=perTarget.map(r=>r[m.toLowerCase()+"_recall_at_"+k]);
      modelRecall[m][k]={mean_recall:mean(xs),exact_uniform_expected_recall:k/45,delta_vs_exact_uniform:mean(xs)-k/45};
    });
  });
  const blockRows=[];
  for(let start=START,block=1;start<=1250;start+=50,block++){
    const end=Math.min(start+49,1250), xs=perTarget.filter(r=>r.target_round>=start&&r.target_round<=end);
    pairKeys.forEach(pair=>{
      const [a,b]=pair.split("__");
      const r={block_type:"FULL_50",block_index:block,start_target:start,end_target:end,targets:xs.length,pair,mean_spearman:mean(xs.map(x=>x[pair+"_spearman"]))};
      K_VALUES.forEach(k=>{
        r["K"+k+"_mean_intersection"]=mean(xs.map(x=>x[pair+"_K"+k+"_intersection"]));
        r["K"+k+"_mean_jaccard"]=mean(xs.map(x=>x[pair+"_K"+k+"_jaccard"]));
        r["K"+k+"_net_unique_winner_rescue_A_minus_B"]=mean(xs.map(x=>x[pair+"_K"+k+"_net_unique_winner_rescue_A_minus_B"]));
        r["K"+k+"_mean_recall_A_minus_B"]=mean(xs.map(x=>x[a.toLowerCase()+"_recall_at_"+k]-x[b.toLowerCase()+"_recall_at_"+k]));
      });
      blockRows.push(r);
    });
  }
  const remainder=perTarget.filter(r=>r.target_round>1250);
  if(remainder.length){
    pairKeys.forEach(pair=>{
      const [a,b]=pair.split("__");
      const r={block_type:"FINAL_REMAINDER",block_index:18,start_target:1251,end_target:1251,targets:remainder.length,pair,mean_spearman:mean(remainder.map(x=>x[pair+"_spearman"]))};
      K_VALUES.forEach(k=>{
        r["K"+k+"_mean_intersection"]=mean(remainder.map(x=>x[pair+"_K"+k+"_intersection"]));
        r["K"+k+"_mean_jaccard"]=mean(remainder.map(x=>x[pair+"_K"+k+"_jaccard"]));
        r["K"+k+"_net_unique_winner_rescue_A_minus_B"]=mean(remainder.map(x=>x[pair+"_K"+k+"_net_unique_winner_rescue_A_minus_B"]));
        r["K"+k+"_mean_recall_A_minus_B"]=mean(remainder.map(x=>x[a.toLowerCase()+"_recall_at_"+k]-x[b.toLowerCase()+"_recall_at_"+k]));
      });
      blockRows.push(r);
    });
  }
  const verification={
    study_id:"E082_RANK_DIVERSITY_OVERLAP_AUDIT_v1",source_path:DATA_PATH,rows:rows.length,first_round:rows[0].round,last_round:rows[rows.length-1].round,
    source_sha256:dataSha,source_git_blob_sha:blobSha,header_valid:true,round_sequence_valid:true,main_number_validation:"PASS",bonus_validation:"PASS",
    target_range:[START,END],target_count:perTarget.length,cutoff_violations:0,contaminated_live_history_rounds:[1244,1245,1246,1247,1248,1249,1250,1251],
    clean_holdout:false,prospective_confirmation:false,models:MODELS,rankings_per_target:3,full_rankings_computed:perTarget.length*3,
    pairwise_rank_correlations:perTarget.length*3,top_k_values:K_VALUES,full_50_target_blocks:17,final_remainder_targets:remainder.length,
    candidate_numbers_written_to_output:false,allocator_changed:false,purchase_lines_generated:false
  };
  const results={
    study_id:"E082_RANK_DIVERSITY_OVERLAP_AUDIT_v1",evidence_class:"HISTORICAL_CUTOFF_SAFE_RANK_DEPENDENCE_DIAGNOSTIC_NOT_CLEAN_HOLDOUT_NOT_PROSPECTIVE",
    source:{path:DATA_PATH,cutoff:1251,rows:1251,sha256:dataSha,git_blob_sha:blobSha},
    question:"Do Borda and MIN_RANK add distinct candidate-order information beyond mean-z consensus?",
    models:{CONSENSUS:"mean of five component z-scores",BORDA:"sum of five component rank positions",MIN_RANK:"minimum component rank, then sum-rank tie-break"},
    candidate_recall_vs_exact_uniform:modelRecall,pairwise_rank_dependence_and_top_k_overlap:pairSummary,
    block_stability:{full_blocks:17,block_length:50,final_remainder_targets:remainder.length,block_summary: {
      pairs:pairKeys.map(pair=>{
        const xs=blockRows.filter(r=>r.pair===pair&&r.block_type==="FULL_50");
        return {pair,spearman_block_min:Math.min(...xs.map(r=>r.mean_spearman)),spearman_block_max:Math.max(...xs.map(r=>r.mean_spearman)),
          top_k:Object.fromEntries(K_VALUES.map(k=>[""+k,{
            mean_intersection_min:Math.min(...xs.map(r=>r["K"+k+"_mean_intersection"])),
            mean_intersection_max:Math.max(...xs.map(r=>r["K"+k+"_mean_intersection"])),
            net_unique_winner_rescue_positive_blocks:xs.filter(r=>r["K"+k+"_net_unique_winner_rescue_A_minus_B"]>0).length,
            net_unique_winner_rescue_negative_blocks:xs.filter(r=>r["K"+k+"_net_unique_winner_rescue_A_minus_B"]<0).length
          }]))};
      })
    }},
    decision:{inferential_claims:false,model_promotion:false,allocator_promotion:false,strict_gate_changed:false,prospective_confirmation:false,purchase_lines_generated:false}
  };
  return {results,verification,perTarget,blockRows};
}
function csv(rows,cols){
  const esc=v=>{const s=String(v===undefined||v===null?"":v);return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};
  return [cols.join(","),...rows.map(r=>cols.map(k=>esc(r[k])).join(","))].join("\n")+"\n";
}
function main(){
  const raw=fs.readFileSync(DATA_PATH,"utf8"),out=analyze(raw);
  fs.mkdirSync(OUT_DIR,{recursive:true});
  fs.writeFileSync(path.join(OUT_DIR,"RESULTS.json"),JSON.stringify(out.results,null,2)+"\n");
  fs.writeFileSync(path.join(OUT_DIR,"VERIFICATION.json"),JSON.stringify(out.verification,null,2)+"\n");
  fs.writeFileSync(path.join(OUT_DIR,"PER_TARGET_METRICS.csv"),csv(out.perTarget,Object.keys(out.perTarget[0])));
  fs.writeFileSync(path.join(OUT_DIR,"BLOCK_SUMMARY.csv"),csv(out.blockRows,Object.keys(out.blockRows[0])));
  console.log(JSON.stringify({results:out.results,verification:out.verification},null,2));
}
main();