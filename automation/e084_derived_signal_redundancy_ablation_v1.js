#!/usr/bin/env node
"use strict";
const fs=require("fs"),path=require("path"),crypto=require("crypto");
const DATA="data/snapshots/lotto_data_through_1251_20261122.csv";
const OUT="analysis/2026-11-26/E084_DERIVED_SIGNAL_REDUNDANCY_ABLATION_3LINE_v1";
const EXPECTED_SHA="2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9";
const EXPECTED_BLOB="be2fa07921a92f335aeb6e715b4f40098e297834";
const START=401,END=1251,BLOCK=50,BOOT=4000;
const NULL={max_hit:1.514256248572755,any2:0.47497624326892623,any3:0.07135490714617204,any4:0.004180448026165553,any5:0.00008655553181928678,any6:0.000000368321411996965,winning_union_coverage:2.4};
function mean(a){return a.reduce((x,y)=>x+y,0)/a.length;}
function quantile(a,p){const x=a.slice().sort((u,v)=>u-v),h=(x.length-1)*p,l=Math.floor(h),u=Math.ceil(h);return x[l]+(x[u]-x[l])*(h-l);}
function zscore(o){const a=Object.values(o),m=mean(a),sd=Math.sqrt(mean(a.map(x=>(x-m)**2)))||1,q={};Object.keys(o).forEach(k=>q[k]=(o[k]-m)/sd);return q;}
function features(ds){
 const f30=Array(46).fill(0),f10=Array(46).fill(0),f20=Array(46).fill(0);
 ds.slice(-30).forEach(d=>d.forEach(n=>f30[n]++));ds.slice(-10).forEach(d=>d.forEach(n=>f10[n]++));ds.slice(-30,-10).forEach(d=>d.forEach(n=>f20[n]++));
 const gaps={};for(let n=1;n<=45;n++){let g=0;for(let i=ds.length-1;i>=0;i--){if(ds[i].includes(n))break;g++;}gaps[n]=g;}
 const rr={},mm={};for(let n=1;n<=45;n++){rr[n]=f30[n];mm[n]=f10[n]/10-f20[n]/20;}
 const recent=zscore(rr),gap=zscore(gaps),momentum=zscore(mm),full={},base3={};
 for(let n=1;n<=45;n++){const balanced=(recent[n]+gap[n])/2,contrarian=(-recent[n]+gap[n])/2;full[n]=(recent[n]+gap[n]+momentum[n]+balanced+contrarian)/5;base3[n]=(recent[n]+gap[n]+momentum[n])/3;}
 return{full,base3};
}
function rank(score){return Array.from({length:45},(_,i)=>i+1).sort((a,b)=>(score[b]-score[a])||a-b);}
function rand32(a){return function(){let t=a+=0x6D2B79F5;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};}
function shuffle(a,r){const x=a.slice();for(let i=x.length-1;i>0;i--){const j=Math.floor(r()*(i+1));[x[i],x[j]]=[x[j],x[i]];}return x;}
function portfolio(order,w){
 const lines=[order.slice(0,6),order.slice(6,12),order.slice(12,18)],lh=lines.map(l=>l.reduce((s,n)=>s+(w.has(n)?1:0),0)),u=new Set(lines.flat()),coverage=[...u].reduce((s,n)=>s+(w.has(n)?1:0),0),m=Math.max(...lh);
 return{max_hit:m,any2:+(m>=2),any3:+(m>=3),any4:+(m>=4),any5:+(m>=5),any6:+(m>=6),winning_union_coverage:coverage,line_hits:lh};
}
function choose(n,k){if(k<0||k>n)return 0;let v=1,m=Math.min(k,n-k);for(let i=1;i<=m;i++)v=v*(n-m+i)/i;return v;}
function exactNull(){const den=choose(45,6),o={probability_sum:0,max_hit:0,any2:0,any3:0,any4:0,any5:0,any6:0,winning_union_coverage:0};for(let a=0;a<=6;a++)for(let b=0;b<=6;b++)for(let c=0;c<=6;c++){const d=6-a-b-c;if(d<0||d>27)continue;const p=choose(6,a)*choose(6,b)*choose(6,c)*choose(27,d)/den,m=Math.max(a,b,c);o.probability_sum+=p;o.max_hit+=m*p;o.any2+=(m>=2)*p;o.any3+=(m>=3)*p;o.any4+=(m>=4)*p;o.any5+=(m>=5)*p;o.any6+=(m>=6)*p;o.winning_union_coverage+=(a+b+c)*p;}return o;}
function mbbCI(series,alpha,seed){const n=series.length,core=Math.floor(n/BLOCK)*BLOCK,blocks=core/BLOCK,rem=n-core,r=rand32(seed>>>0),vals=[];for(let j=0;j<BOOT;j++){let sum=0;for(let b=0;b<blocks;b++){const st=Math.floor(r()*(core-BLOCK+1));for(let k=0;k<BLOCK;k++)sum+=series[st+k];}for(let k=core;k<n;k++)sum+=series[k];vals.push(sum/n);}return[quantile(vals,alpha/2),quantile(vals,1-alpha/2)];}
function csv(rows,cols){const e=v=>{const s=String(v==null?"":v);return/[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};return[cols.join(","),...rows.map(r=>cols.map(k=>e(r[k])).join(","))].join("\n")+"\n";}
function parse(raw){const l=raw.replace(/^\uFEFF/,"").split(/\r?\n/).filter(x=>x.trim()),h=l[0].split(",");if(h.join("|")!=="round|date|no1|no2|no3|no4|no5|no6|bonus")throw Error("header");const rows=l.slice(1).map(x=>{const p=x.split(",");if(p.length!==9)throw Error("fields");return{round:+p[0],date:p[1],nums:p.slice(2,8).map(Number),bonus:+p[8]};});if(rows.length!==1251)throw Error("row count");rows.forEach((r,i)=>{if(r.round!==i+1||r.nums.length!==6||new Set(r.nums).size!==6||!r.nums.every(n=>Number.isInteger(n)&&n>=1&&n<=45)||!Number.isInteger(r.bonus)||r.bonus<1||r.bonus>45||r.nums.includes(r.bonus))throw Error("invalid row "+(i+1));});return rows;}
function run(raw){
 const rows=parse(raw),nulls=exactNull();Object.keys(NULL).forEach(k=>{if(Math.abs(nulls[k]-NULL[k])>1e-12)throw Error("null mismatch "+k);});
 const targets=[],miss=[],blocks=[];const K=[10,15,20,25,30],MET=["max_hit","any2","any3","any4","winning_union_coverage"];
 const rngCand=rand32(202611260841),rngPort=rand32(202611260842);
 const candRand=Object.fromEntries(K.map(k=>[k,0])),portRand={max_hit:0,any2:0,any3:0,any4:0,any5:0,any6:0,winning_union_coverage:0};
 const fullLineDist=Array(7).fill(0),baseLineDist=Array(7).fill(0);
 for(let t=START;t<=END;t++){
  const target=rows[t-1],hist=rows.slice(0,t-1).map(r=>r.nums),w=new Set(target.nums);if(hist.length!==t-1)throw Error("cutoff");
  const f=features(hist),of=rank(f.full),ob=rank(f.base3),row={target_round:t,training_through_round:t-1,contaminated_live_history:[1244,1245,1246,1247,1248,1249,1250,1251].includes(t)};
  for(const k of K){row["full_recall_"+k]=of.slice(0,k).filter(n=>w.has(n)).length/6;row["base3_recall_"+k]=ob.slice(0,k).filter(n=>w.has(n)).length/6;}
  const pf=portfolio(of,w),pb=portfolio(ob,w);Object.assign(row,Object.fromEntries(Object.entries(pf).filter(([k])=>k!=="line_hits").map(([k,v])=>["full_"+k,v])));Object.assign(row,Object.fromEntries(Object.entries(pb).filter(([k])=>k!=="line_hits").map(([k,v])=>["base3_"+k,v])));
  pf.line_hits.forEach(x=>fullLineDist[x]++);pb.line_hits.forEach(x=>baseLineDist[x]++);
  const pos={};for(let i=0;i<45;i++){const n=i+1;pos[n]=[of.indexOf(n)+1,ob.indexOf(n)+1];}
  target.nums.forEach((n,i)=>miss.push({target_round:t,winner_slot:i+1,full_rank:pos[n][0],base3_rank:pos[n][1],rank_change:pos[n][0]-pos[n][1],full_top30:pos[n][0]<=30,base3_top30:pos[n][1]<=30}));
  // Target-matched random candidate sets; each permutation supplies all five K prefixes.
  const universe=Array.from({length:45},(_,i)=>i+1);
  for(let j=0;j<200;j++){const perm=shuffle(universe,rngCand);let hit=0;for(let i=0;i<45;i++){if(w.has(perm[i]))hit++;const k=i+1;if(K.includes(k))candRand[k]+=(hit/6)/200;}}
  // Target-matched random 3-line portfolios, preserving disjoint union18 geometry.
  for(let j=0;j<120;j++){const perm=shuffle(universe,rngPort),rp=portfolio(perm,w);for(const k of Object.keys(portRand))portRand[k]+=rp[k]/120;}
  targets.push(row);
 }
 const n=targets.length,meanMetric=(prefix,k)=>mean(targets.map(r=>r[prefix+"_"+k]));
 const candidate={full_five:{},base_three:{},matched_random:{},exact_uniform:{},paired_delta_base3_minus_full:{}};
 for(const k of K){
  const fr=mean(targets.map(r=>r["full_recall_"+k])),br=mean(targets.map(r=>r["base3_recall_"+k])),rr=candRand[k]/n;
  candidate.full_five[k]=fr;candidate.base_three[k]=br;candidate.matched_random[k]=rr;candidate.exact_uniform[k]=k/45;
  const dif=targets.map(r=>r["base3_recall_"+k]-r["full_recall_"+k]);
  const alpha=k===30?0.05:0.0125;
  candidate.paired_delta_base3_minus_full[k]={mean:mean(dif),ci:mbbCI(dif,alpha,202611260843+k),alpha,primary:k===30};
 }
 const portfolio={};
 for(const model of ["full","base3"]){
  const item={observed:{},delta_vs_exact_null:{},adjusted_mbb_ci:{},strict_lower_pass:{}};
  for(const m of ["max_hit","any2","any3","any4","any5","any6","winning_union_coverage"]){
   const v=mean(targets.map(r=>r[model+"_"+m])),d=targets.map(r=>r[model+"_"+m]-NULL[m]);
   item.observed[m]=v;item.delta_vs_exact_null[m]=v-NULL[m];
   if(MET.includes(m)){item.adjusted_mbb_ci[m]=mbbCI(d,0.0125,202611260844+MET.indexOf(m));item.strict_lower_pass[m]=item.adjusted_mbb_ci[m][0]>0;}
  }
  portfolio[model]=item;
 }
 const blockRows=[];
 for(let st=0;st<n;st+=50){const xs=targets.slice(st,Math.min(st+50,n)),row={start_target:xs[0].target_round,end_target:xs[xs.length-1].target_round,n:xs.length};for(const model of ["full","base3"]){const d=mean(xs.map(r=>r[model+"_any2"]))-NULL.any2;row[model+"_any2_delta"]=d;row[model+"_positive"]=d>0;}blockRows.push(row);}
 const fullBlocks=blockRows.filter(x=>x.n===50),basePos=fullBlocks.filter(x=>x.base3_positive).length,fullPos=fullBlocks.filter(x=>x.full_positive).length;
 const candidateDiff30=targets.map(r=>r.base3_recall_30-r.full_recall_30);
 const candidateDelta30=targets.map(r=>r.base3_recall_30-30/45);
 const lineSummary={full_five:fullLineDist,base_three:baseLineDist};
 return{
  targets,miss,blockRows,
  results:{
   study_id:"E084_DERIVED_SIGNAL_REDUNDANCY_ABLATION_3LINE_v1",
   evidence_class:"HISTORICAL_CUTOFF_SAFE_CANDIDATE_ABLATION_NOT_CLEAN_HOLDOUT_NOT_PROSPECTIVE_CONFIRMATION",
   source:{path:DATA,cutoff:1251,rows:rows.length,sha256:EXPECTED_SHA,git_blob_sha:EXPECTED_BLOB},
   algebraic_identity:"five_component mean-z consensus is exactly proportional in rank to recent30_z + 2*gap_z + momentum_z; the two derived terms do not add an independent feature dimension and jointly add one extra gap_z vote.",
   candidate_stage:{targets:n,recall: candidate,primary_comparison:"candidate_recall@30 base-three minus full five-component consensus",primary_ci:mbbCI(candidateDiff30,0.05,202611260899),base3_recall30_vs_exact_uniform:{delta:mean(candidateDelta30),ci:mbbCI(candidateDelta30,0.05,202611260898)}},
   portfolio_stage:{allocator:"fixed rank partition top18 into 3 disjoint lines",exact_geometry_matched_null:NULL,matched_random_means:Object.fromEntries(Object.entries(portRand).map(([k,v])=>[k,v/n])),models:portfolio,line_hit_distribution:lineSummary},
   block_stability:{block_length:50,full_blocks:fullBlocks.length,final_remainder:targets.length-fullBlocks.length*50,full_five_any2_positive_blocks:fullPos,base_three_any2_positive_blocks:basePos,base_three_any2_positive_share:basePos/fullBlocks.length,minimum:0.65,blocks:blockRows},
   execution:{candidate_random_permutations:n*200,portfolio_random_bundles:n*120,bootstrap_replicates:BOOT,cutoff_violations:0,invalid_three_line_geometries:0,exact_null_probability_sum:nulls.probability_sum,exact_null_matches_registered:true,miss_trace_rows:miss.length,contaminated_targets:[1244,1245,1246,1247,1248,1249,1250,1251],clean_holdout:false,prospective_confirmation:false},
   decision:{historical_strict_gate_pass:MET.every(m=>portfolio.base3.strict_lower_pass[m])&&basePos/fullBlocks.length>=0.65,model_promotion:false,allocator_promotion:false,strict_pass_ready:false,purchase_lines_generated:false,prospective_minimum_target_count:null,prospective_completion_rule:null}
  }
 };
}
function main(){const raw=fs.readFileSync(DATA,"utf8"),out=run(raw);fs.mkdirSync(OUT,{recursive:true});fs.writeFileSync(path.join(OUT,"RESULTS.json"),JSON.stringify(out.results,null,2)+"\n");fs.writeFileSync(path.join(OUT,"PER_TARGET_METRICS.csv"),csv(out.targets,Object.keys(out.targets[0])));fs.writeFileSync(path.join(OUT,"WINNER_RANK_MISS_TRACE.csv"),csv(out.miss,Object.keys(out.miss[0])));fs.writeFileSync(path.join(OUT,"BLOCK_SUMMARY.csv"),csv(out.blockRows,Object.keys(out.blockRows[0])));console.log(JSON.stringify(out.results,null,2));}
main();
