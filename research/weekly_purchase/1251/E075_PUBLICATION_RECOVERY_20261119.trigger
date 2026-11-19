E075 publication recovery trigger

Reason: workflow run 44426026061 completed the frozen v3 calculation and output verification but failed while persisting the nested INFERENCE.json metrics. The separate recovery workflow preserves every frozen v3 blob, reruns the same preregistered calculation, verifies all outputs, and persists the queue state with the correct schema. No thresholds, alpha, block length, comparator, seed, model weights, or strict gates are changed.
