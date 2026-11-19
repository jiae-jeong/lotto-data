# B-v1 matched actual random baseline — pre-execution plan

Reference: the reproduced B-v1 audit commit; original code/results remain read-only.
Targets:201–250,401–450,601–650,801–850,1001–1050,1101–1150,1151–1200.
No exclusions. All350targets and8Bmodels are compared on exactly the same rounds.

Random seed20261009;PCG64 with independent SeedSequence([seed,target]) streams.
Each target:generate10000 actual uniform six-distinct-number tickets from1..45.
Use iid ordered uniform sextuples,reject duplicates,sort. Each valid unordered
ticket has6! equally likely preimages. Do not sample synthetic hypergeometric
hit counts. Compare actual generated tickets to the fixed historical actual draw.
Store per-target/block/pooled counts,seven-hit PMF,tails2+..6+,mean,variance,
Monte Carlo SE/95%mean intervals andWilsonrate intervals,stream byte SHA.
Total3.5million comparisons;runtime/memory burden modest,mean SEabout0.000419.
Expected6-hit countabout0.43,so precision forjackpot rate is limited.

B350tickets/model remains a350-round historical sample. More random tickets
reduce simulation noise,not B uncertainty. Compare paired historical intervals,
not unrelated recent windows. Source B classifications and formulas remain fixed.

B meanCI:Student-t95%df349(Cornish-Fisher fixed approximation),rate2+:Wilson95%.
Report difference CIs by subtracting the exact theoretical baseline.
Add20000 whole-seven-block bootstrap resamples(seed20261010),50rounds/block,
same weights across8models. Only7blocks:stability/CI are descriptive and limited.
Exploratory tests:exact350fold hypergeometric convolution for mean sum;exact
two-sided probability-ordered Binomial(350,p2plus) for2+;Holm family16tests.
These tests assume fair independent draws and do not undo post-hoc model design.
No statistically verified predictive edge ornewmodelclass promotion is declared.

Distribution diagnostic:chi-squarebins0,1,2,3,4,5+,df5. Never change seed,
sample size,metrics,intervals orsampler based on outcomes. Unresolved earlier
0.7743/0.7571/0.8065 results excluded. No1245outcome read/use and no purchase,
candidate,recommendation ornewfinal-three-line numbers emitted.
