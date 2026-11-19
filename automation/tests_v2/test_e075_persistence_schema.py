import unittest
from automation.e075_persist_result_v1 import build_report


class E075PersistenceSchemaTests(unittest.TestCase):
    def test_report_reads_metric_groups_from_inference_metrics_object(self):
        inference = {
            "data_cutoff":1250,"target_range":[401,1250],"targets":850,
            "random_bundles_total_per_version":102000,"block_count":17,
            "metrics":{
                "legacy_vs_exact_null":{m:{"delta_mean":-0.01,"adjusted_moving_block_ci":[-0.02,0.01]} for m in ("max_hits","any2","any3","winning_union_coverage")},
                "corrected_vs_exact_null":{m:{"delta_mean":0.01,"adjusted_moving_block_ci":[-0.01,0.03]} for m in ("max_hits","any2","any3","winning_union_coverage")},
                "corrected_minus_legacy":{m:{"delta_mean":0.02,"moving_block_ci":[-0.01,0.05]} for m in ("max_hits","any2","any3","winning_union_coverage")},
            },
            "legacy_any2_positive_50_target_block_share":0.47,
            "corrected_any2_positive_50_target_block_share":0.53,
            "historical_strict_gate_pass_legacy":False,
            "historical_strict_gate_pass_corrected":False,
            "candidate_pool_comparisons":3150,"candidate_pool_rule_identical":True,
            "first_role_pool_mismatches":0,"downstream_pool_content_differences":12,
            "legacy_order_consecutive_mismatches":7,"targets_with_changed_lines":9,"changed_line_count":14,
        }
        verification={"leakage_failures":0,"training_cutoff_violations":0,"future_predictions":0,
                      "portfolio_geometry_violations":0,"random_geometry_violations":0}
        report=build_report(inference,verification,"7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2",
                            "https://github.com/jiae-jeong/lotto-data/actions/runs/1",1)
        self.assertIn("| max_hits | -0.010000 | 0.010000 | 0.020000 |",report)
        self.assertIn("Legacy any2-positive 50-target block share: 47.00%",report)
        self.assertIn("Corrected any2-positive 50-target block share: 53.00%",report)
        self.assertIn("not new predictive evidence",report.lower())
        self.assertIn("STRICT_PASS_READY: **not created**",report)


if __name__=="__main__":
    unittest.main()
