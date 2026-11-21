#!/usr/bin/env node
"use strict";
const fs=require("fs");
const path=require("path");
const input=process.argv[2]||"PREDICTIONS_V2.csv";
const lines=fs.readFileSync(input,"utf8").trim().split(/\r?\n/);
const head=lines[0].split(",");
const rows=lines.slice(1).map(line=>Object.fromEntries(line.split(",").map((v,i)=>[head[i],Number(v)])));
const arms=["A","B"];
const out={rows:rows.length,first_target:rows[0]?.target,last_target:rows.at(-1)?.target,sequence:true,cutoff:true,geometry:true,metric_logic:true,arms:{}};
if(rows.length!==849)throw new Error("row count mismatch");
for(let i=0;i<rows.length;i++){
 const r=rows[i];
 if(r.target!==401+i)out.sequence=false;
 if(r.cutoff!==r.target-1)out.cutoff=false;
 for(const a of arms){
  if(r[a+"_union_size"]!==18 || r[a+"_overlap_12"]!==0 || r[a+"_overlap_13"]!==0 || r[a+"_overlap_23"]!==0)out.geometry=false;
  const max=Math.max(r[a+"_line1_hits"],r[a+"_line2_hits"],r[a+"_line3_hits"]);
  if(r[a+"_max_hits"]!==max || r[a+"_any2"]!==+(max>=2) || r[a+"_any3"]!==+(max>=3) ||
     r[a+"_any4"]!==+(max>=4) || r[a+"_any5"]!==+(max>=5) || r[a+"_any6"]!==+(max>=6))out.metric_logic=false;
 }
}
const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
for(const a of arms){
 const hist=Array(7).fill(0);for(const r of rows)hist[r[a+"_max_hits"]]++;
 const blocks=[];for(let i=0;i<rows.length;i+=50){const b=rows.slice(i,i+50);blocks.push({start:b[0].target,end:b.at(-1).target,n:b.length,any2_rate:mean(b.map(r=>r[a+"_any2"])),any4_count:b.reduce((s,r)=>s+r[a+"_any4"],0),any5_count:b.reduce((s,r)=>s+r[a+"_any5"],0),any6_count:b.reduce((s,r)=>s+r[a+"_any6"],0)});}
 out.arms[a]={means:Object.fromEntries(["max_hits","any2","any3","any4","any5","any6","winning_union_coverage"].map(m=>[m,mean(rows.map(r=>r[a+"_"+(m==="winning_union_coverage"?"winning_union_coverage":m)]))])),max_hit_distribution:hist,any2_positive_block_share:blocks.filter(b=>b.any2_rate>0.47497624326892623).length/blocks.length,blocks};
}
out.pass=out.sequence&&out.cutoff&&out.geometry&&out.metric_logic;
process.stdout.write(JSON.stringify(out,null,2)+"\n");
if(!out.pass)process.exitCode=1;