#!/usr/bin/env node
"use strict";
const fs=require("fs"),crypto=require("crypto"),path=require("path");
const DATA_PATH="data/snapshots/lotto_data_through_1251_20261122.csv";
const OUT_DIR="analysis/2026-11-23/E081_MIN_COMPONENT_RANK_RESCUE_v1";
const EXPECTED_SHA256="2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9";
const EXPECTED_BLOB="be2fa07921a92f335aeb6e715b4f40098e297834";
function runE081(raw,meta){
 const K=[10,15,20,25,30],S=["recent30","gap","momentum","balanced","contrarian"],START=401,END=1251,B=50,R=4000;
 const SEED={boot:20261123081,cand:20261123082,port:20261123083};
 const NULL={max_hits:1.5142562485727544,any2:0.4749762432689262,any3:0.07135490714617204,any4:0.004180448026165553,any5:0.00008655553181928678,any6:3.68321411996965e-7,winning_union_coverage:2.4};
 const lines=raw.replace(/^\uFEFF/,"").split(/\r?\n/).filter(x=>x.trim());
 const hdr=lines[0].split(",");
 if(JSON.stringify(hdr)!==JSON.stringify(["round","date","no1","no2","no3","no4","no5","no6","bonus"]))throw new Error("Header mismatch");
 const rows=lines.slice(1).map(x=>{const p=x.split(",");if(p.length!==9)throw new Error("Field count");return{round:+p[0],date:p[1],nums:p.slice(2,8).map(Number),bonus:+p[8]};});
 if(rows.length!==1251)throw new Error("Rows mismatch");
 rows.forEach((r,i)=>{if(r.round!==i+1||r.nums.length!==6||new Set(r.nums).size!==6||!r.nums.every(n=>Number.isInteger(n)&&n>=1&&n<=45)||!Number.isInteger(r.bonus)||r.bonus<1||r.bonus>45||r.nums.includes(r.bonus))throw new Error("Invalid row "+(i+1));});
 const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
 function choose(n,k){if(k<0||k>n)return 0;let v=1,m=Math.min(k,n-k);for(let i=1;i<=m;i++)v=v*(n-m+i)/i;return v;}
 function z(o){const a=Object.values(o),m=mean(a),sd=Math.sqrt(mean(a.map(x=>(x-m)*(x-m))))||1,q={};Object.keys(o).forEach(k=>q[k]=(o[k]-m)/sd);return q;}
 function feats(ds){
  const f30=Array(46).fill(0),f10=Array(46).fill(0),f20=Array(46).fill(0);
  ds.slice(-30).forEach(d=>d.forEach(n=>f30[n]++));ds.slice(-10).forEach(d=>d.forEach(n=>f10[n]++));ds.slice(-30,-10).forEach(d=>d.forEach(n=>f20[n]++));
  const gaps={};for(let n=1;n<=45;n++){let g=0;for(let i=ds.length-1;i>=0;i--){if(ds[i].includes(n))break;g++;}gaps[n]=g;}
  const rr={},mm={},me={};for(let n=1;n<=45;n++){rr[n]=f30[n];mm[n]=f10[n]/10-f20[n]/20;me[n]=2*f10[n]-f20[n];}
  const recent30=z(rr),gap=z(gaps),momentum=z(mm),balanced={},contrarian={},consensus={};
  for(let n=1;n<=45;n++){balanced[n]=(recent30[n]+gap[n])/2;contrarian[n]=(-recent30[n]+gap[n])/2;consensus[n]=(recent30[n]+gap[n]+momentum[n]+balanced[n]+contrarian[n])/5;}
  return{recent30,gap,momentum,momentumExact:me,balanced,contrarian,consensus};
 }
 function ranked(score,exact){const order=Array.from({length:45},(_,i)=>i+1).sort((a,b)=>((exact?exact[b]:score[b])-(exact?exact[a]:score[a]))||a-b),rank={};order.forEach((n,i)=>rank[n]=i+1);return{order,rank};}
 function rand32(a){return function(){let t=a+=0x6D2B79F5;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};}
 function shuffle(a,r){const x=a.slice();for(let i=x.length-1;i>0;i--){const j=Math.floor(r()*(i+1));[x[i],x[j]]=[x[j],x[i]];}return x;}
 function pm(ls,w){const lh=ls.map(l=>l.reduce((a,n)=>a+(w.has(n)?1:0),0)),u=new Set(ls.flat());let c=0;u.forEach(n=>{if(w.has(n))c++;});const m=Math.max(...lh);return{line_hits:lh,max_hits:m,any2:+(m>=2),any3:+(m>=3),any4:+(m>=4),any5:+(m>=5),any6:+(m>=6),winning_union_coverage:c};}
 function exactNull(){const d0=choose(45,6),o={probability_sum:0,max_hits:0,any2:0,any3:0,any4:0,any5:0,any6:0,winning_union_coverage:0};for(let a=0;a<=6;a++)for(let b=0;b<=6;b++)for(let c=0;c<=6;c++){const d=6-a-b-c;if(d<0||d>27)continue;const p=choose(6,a)*choose(6,b)*choose(6,c)*choose(27,d)/d0,m=Math.max(a,b,c);o.probability_sum+=p;o.max_hits+=m*p;o.any2+=(m>=2)*p;o.any3+=(m>=3)*p;o.any4+=(m>=4)*p;o.any5+=(m>=5)*p;o.any6+=(m>=6)*p;o.winning_union_coverage+=(a+b+c)*p;}return o;}
 function quant(a,p){const x=a.slice().sort((u,v)=>u-v),h=(x.length-1)*p,l=Math.floor(h),u=Math.ceil(h);return x[l]+(x[u]-x[l])*(h-l);}
 function ciMBB(series,alpha,seed){const n=series.length,core=Math.floor(n/B)*B,nb=core/B,rem=n-core,r=rand32(seed>>>0),out=[];for(let j=0;j<R;j++){let sum=0;for(let b=0;b<nb;b++){const st=Math.floor(r()*(core-B+1));for(let k=0;k<B;k++)sum+=series[st+k];}for(let k=core;k<n;k++)sum+=series[k];out.push(sum/n);}return[quant(out,alpha/2),quant(out,1-alpha/2)];}
 const nullCalc=exactNull();Object.keys(NULL).forEach(k=>{if(Math.abs(nullCalc[k]-NULL[k])>1e-12)throw new Error("Exact null mismatch "+k);});if(Math.abs(nullCalc.probability_sum-1)>1e-12)throw new Error("Null sum");
 const targets=rows.filter(r=>r.round>=START&&r.round<=END),models=["MIN_RANK","BORDA","CONSENSUS"],cand={MIN_RANK:[],BORDA:[],CONSENSUS:[]},port={MIN_RANK:[],BORDA:[],CONSENSUS:[]};
 const randomCand=[],randomPort=[],trace=[],perTarget=[],missBest={recent30:0,gap:0,momentum:0,balanced:0,contrarian:0};
 let leakage=0,badGeometry=0;
 for(const t of targets){
  const cutoff=t.round-1,ds=rows.slice(0,cutoff).map(r=>r.nums),w=new Set(t.nums);if(ds.length!==cutoff)leakage++;
  const f=feats(ds),cr={};S.forEach(s=>cr[s]=ranked(f[s],s==="momentum"?f.momentumExact:null).rank);
  const minOrder=Array.from({length:45},(_,i)=>i+1).sort((a,b)=>{const am=Math.min(...S.map(s=>cr[s][a])),bm=Math.min(...S.map(s=>cr[s][b]));if(am!==bm)return am-bm;const as=S.reduce((q,s)=>q+cr[s][a],0),bs=S.reduce((q,s)=>q+cr[s][b],0);return as-bs||a-b;});
  const minRank={};minOrder.forEach((n,i)=>minRank[n]=i+1);
  const bordaOrder=Array.from({length:45},(_,i)=>i+1).sort((a,b)=>S.reduce((q,s)=>q+cr[s][a],0)-S.reduce((q,s)=>q+cr[s][b],0)||a-b);
  const consensus=ranked(f.consensus).rank,consOrder=Object.keys(consensus).map(Number).sort((a,b)=>consensus[a]-consensus[b]);
  const orderMap={MIN_RANK:minOrder,BORDA:bordaOrder,CONSENSUS:consOrder};
  const row={target_round:t.round,training_through_round:cutoff};
  models.forEach(m=>{
   const o=orderMap[m];
   K.forEach(k=>{const h=o.slice(0,k).filter(n=>w.has(n)).length;cand[m].push({target_round:t.round,k,hits:h});row[m+"_hits_at_"+k]=h;});
   const ls=[o.slice(0,6),o.slice(6,12),o.slice(12,18)],ov=[ls[0].filter(n=>ls[1].includes(n)).length,ls[0].filter(n=>ls[2].includes(n)).length,ls[1].filter(n=>ls[2].includes(n)).length];
   if(ls.some(x=>x.length!==6||new Set(x).size!==6)||new Set(ls.flat()).size!==18||ov.some(x=>x!==0))badGeometry++;
   const mtr=pm(ls,w);port[m].push({target_round:t.round,...mtr,line1_hits:mtr.line_hits[0],line2_hits:mtr.line_hits[1],line3_hits:mtr.line_hits[2],pair_overlap_12:ov[0],pair_overlap_13:ov[1],pair_overlap_23:ov[2],union_size:18});
   Object.keys(mtr).filter(k=>k!=="line_hits").forEach(k=>row[m.toLowerCase()+"_"+k]=mtr[k]);
  });
  const rc=rand32((SEED.cand+t.round*1009)>>>0),cSum=Object.fromEntries(K.map(k=>[k,0]));
  for(let i=0;i<200;i++){const p=shuffle(Array.from({length:45},(_,j)=>j+1),rc);K.forEach(k=>cSum[k]+=p.slice(0,k).filter(n=>w.has(n)).length);}
  const rp=rand32((SEED.port+t.round*1013)>>>0),pSum={max_hits:0,any2:0,any3:0,any4:0,any5:0,any6:0,winning_union_coverage:0};
  for(let i=0;i<120;i++){const p=shuffle(Array.from({length:45},(_,j)=>j+1),rp),mtr=pm([p.slice(0,6),p.slice(6,12),p.slice(12,18)],w);Object.keys(pSum).forEach(k=>pSum[k]+=mtr[k]);}
  Object.keys(pSum).forEach(k=>pSum[k]/=120);
  randomCand.push({target_round:t.round,...Object.fromEntries(K.map(k=>["k"+k,cSum[k]/200]))});randomPort.push({target_round:t.round,...pSum});
  K.forEach(k=>row["random_candidate_hits_at_"+k]=cSum[k]/200);
  Object.keys(pSum).forEach(k=>row["random_portfolio_"+k]=pSum[k]);
  perTarget.push(row);
  [...w].sort((a,b)=>a-b).forEach((num,i)=>{
   const best=S.slice().sort((a,b)=>cr[a][num]-cr[b][num]||S.indexOf(a)-S.indexOf(b))[0],sel=minRank[num]<=30;
   if(!sel)missBest[best]++;
   trace.push({target_round:t.round,winner_slot:i+1,min_rank:minRank[num],borda_rank:bordaOrder.indexOf(num)+1,consensus_rank:consensus[num],recent30_rank:cr.recent30[num],gap_rank:cr.gap[num],momentum_rank:cr.momentum[num],balanced_rank:cr.balanced[num],contrarian_rank:cr.contrarian[num],best_component:best,selected_top30:sel,miss_reason:sel?"IN_TOP30":"ALL_COMPONENT_RANKS_GT30"});
  });
 }
 const n=targets.length;if(n!==851||leakage!==0||badGeometry!==0||trace.length!==n*6)throw new Error("Completeness, leakage, trace or geometry failure");
 const candidateSummary={},portfolioSummary={};
 models.forEach(m=>{
  candidateSummary[m]={};K.forEach(k=>{
   const hs=cand[m].filter(x=>x.k===k).map(x=>x.hits),rec=mean(hs)/6,rm=mean(randomCand.map(x=>x["k"+k]));
   const q={targets:n,mean_hits:mean(hs),candidate_recall:rec,exact_random_expected_hits:6*k/45,exact_random_expected_recall:k/45,matched_random_mean_hits:rm,delta_recall_vs_exact_random:rec-k/45};
   if(m==="MIN_RANK")q.bonferroni_adjusted_moving_block_ci=ciMBB(hs.map(h=>h/6-k/45),0.01,SEED.boot+k);
   candidateSummary[m][k]=q;
  });
  portfolioSummary[m]={};["max_hits","any2","any3","any4","any5","any6","winning_union_coverage"].forEach(metric=>{
   const obs=mean(port[m].map(x=>x[metric])),rm=mean(randomPort.map(x=>x[metric])),q={observed_mean:obs,exact_geometry_null:nullCalc[metric],delta_vs_exact_geometry_null:obs-nullCalc[metric],matched_random_mean:rm,delta_vs_matched_random:obs-rm};
   if(m==="MIN_RANK"&&["max_hits","any2","any3","winning_union_coverage"].includes(metric)){const ix=["max_hits","any2","any3","winning_union_coverage"].indexOf(metric);q.bonferroni_adjusted_moving_block_ci=ciMBB(port[m].map(x=>x[metric]-nullCalc[metric]),0.0125,SEED.boot+300+ix);}
   portfolioSummary[m][metric]=q;
  });
 });
 const maxDist=Array(7).fill(0),lineDist=Array(7).fill(0),unionDist=Array(7).fill(0);
 port.MIN_RANK.forEach(x=>{maxDist[x.max_hits]++;lineDist[x.line1_hits]++;lineDist[x.line2_hits]++;lineDist[x.line3_hits]++;unionDist[x.winning_union_coverage]++;});
 const full=Math.floor(n/B),rem=n-full*B,blocks=[];
 for(let b=0;b<full;b++){const a=port.MIN_RANK.slice(b*B,(b+1)*B),r=mean(a.map(x=>x.any2));blocks.push({block_type:"FULL_50",block_index:b+1,start_target:a[0].target_round,end_target:a[a.length-1].target_round,targets:a.length,any2_rate:r,delta_vs_exact_null:r-nullCalc.any2,positive:r>nullCalc.any2});}
 if(rem){const a=port.MIN_RANK.slice(full*B),r=mean(a.map(x=>x.any2));blocks.push({block_type:"FINAL_REMAINDER",block_index:full+1,start_target:a[0].target_round,end_target:a[a.length-1].target_round,targets:a.length,any2_rate:r,delta_vs_exact_null:r-nullCalc.any2,positive:r>nullCalc.any2});}
 const pos=blocks.filter(x=>x.block_type==="FULL_50"&&x.positive).length,share=pos/full;
 const strictCis=["max_hits","any2","any3","winning_union_coverage"].map(k=>portfolioSummary.MIN_RANK[k].bonferroni_adjusted_moving_block_ci);
 const results={
  study_id:"E081_MIN_COMPONENT_RANK_RESCUE_v1",
  evidence_class:"HISTORICAL_CUTOFF_SAFE_EXPLORATORY_DIAGNOSTIC_NOT_CLEAN_HOLDOUT_NOT_PROSPECTIVE",
  source:{path:meta.source_path,cutoff:1251,rows:1251,sha256:meta.source_sha256,git_blob_sha:meta.source_blob_sha},
  code:{path:meta.code_path,git_blob_sha:meta.code_blob_sha},
  target_range:{start:START,end:END,count:n,cutoff_rule:"target t uses rounds 1..t-1",contaminated_live_history_rounds:[1244,1245,1246,1247,1248,1249,1250,1251],clean_holdout:false,prospective_confirmation:false},
  model:{name:"MIN_RANK",formula:"Ascending minimum of five component rank positions; tie-break by ascending sum of component ranks, then ascending number.",signals:S,parameter_search:false,allocator:"Top 18 split into three disjoint six-number lines."},
  candidate_stage:{k_values:K,models:candidateSummary,miss_trace:{winner_instances:trace.length,top30_misses:trace.filter(x=>!x.selected_top30).length,miss_rate:trace.filter(x=>!x.selected_top30).length/trace.length,best_component_for_missed_winners:missBest}},
  portfolio_stage:{exact_geometry_null:nullCalc,models:portfolioSummary,distributions:{max_hit_0_to_6:maxDist,line_hit_0_to_6:lineDist,union_coverage_0_to_6:unionDist},overlap_geometry:{pairwise_ticket_intersections:[0,0,0],union_size:18},any2_positive_50_target_blocks:{positive:pos,total:full,share},block_stability:blocks},
  strict_gate:{historical_portfolio_gate_pass:strictCis.every(x=>x[0]>0)&&share>=0.65,all_four_adjusted_ci_lower_bounds_gt_zero:strictCis.every(x=>x[0]>0),any2_positive_50_target_block_share_min:0.65,actual_share:share,no_leakage:leakage===0,prospective_confirmation:false,prospective_minimum_count_and_completion_rule:"UNSPECIFIED_IN_POLICY",strict_pass_ready:false},
  execution:{targets_valid:n,leakage_failures:leakage,invalid_portfolios:badGeometry,miss_trace_winners:trace.length,random_candidate_sets:n*200,random_portfolios:n*120,bootstrap_replicates:R,block_length:B,full_blocks:full,final_remainder_targets:rem,exact_null_probability_sum:nullCalc.probability_sum,exact_null_matches_registered:true}
 };
 function csv(a,cols){const esc=v=>{const s=String(v===undefined||v===null?"":v);return/[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};return[cols.join(","),...a.map(x=>cols.map(k=>esc(x[k])).join(","))].join("\n")+"\n";}
 const perCols=Object.keys(perTarget[0]);
 return{results,resultsJson:JSON.stringify(results,null,2)+"\n",perTargetCsv:csv(perTarget,perCols),missCsv:csv(trace,["target_round","winner_slot","min_rank","borda_rank","consensus_rank","recent30_rank","gap_rank","momentum_rank","balanced_rank","contrarian_rank","best_component","selected_top30","miss_reason"]),blockCsv:csv(blocks,["block_type","block_index","start_target","end_target","targets","any2_rate","delta_vs_exact_null","positive"])};
}
function blobSha(s){const b=Buffer.from(s,"utf8");return crypto.createHash("sha1").update(Buffer.concat([Buffer.from("blob "+b.length+"\0"),b])).digest("hex");}
const raw=fs.readFileSync(DATA_PATH,"utf8");
const sha=crypto.createHash("sha256").update(raw,"utf8").digest("hex"),blob=blobSha(raw);
if(sha!==EXPECTED_SHA256||blob!==EXPECTED_BLOB)throw new Error("Data SHA mismatch");
const out=runE081(raw,{source_path:DATA_PATH,source_sha256:sha,source_blob_sha:blob,code_path:"automation/e081_min_component_rank_rescue_v2.js",code_blob_sha:"VERIFY_AFTER_COMMIT"});
fs.mkdirSync(OUT_DIR,{recursive:true});
fs.writeFileSync(path.join(OUT_DIR,"RESULTS.json"),out.resultsJson);
fs.writeFileSync(path.join(OUT_DIR,"PER_TARGET_METRICS.csv"),out.perTargetCsv);
fs.writeFileSync(path.join(OUT_DIR,"WINNER_MISS_ATTRIBUTION.csv"),out.missCsv);
fs.writeFileSync(path.join(OUT_DIR,"BLOCK_STABILITY.csv"),out.blockCsv);
console.log(JSON.stringify(out.results.execution));
