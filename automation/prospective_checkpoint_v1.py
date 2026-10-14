"""Promotion and checkpoint statuses under the pre-1246 amendment."""
from __future__ import annotations


def checkpoint_status(target_count: int, promotion_pass: bool,
                      futility_registered: bool = False,
                      futility_met: bool = False) -> str:
    """Return a status without treating a low-powered interim miss as rejection."""
    if target_count < 200:
        return "PROSPECTIVE_PENDING"
    if promotion_pass:
        return "PROSPECTIVE_VALIDATED_EDGE"
    if futility_registered and futility_met:
        return "REJECTED"
    return "PROSPECTIVE_INSUFFICIENT_EVIDENCE"


def promotion_gates(any3_differences: list[float], max_hit_differences: list[float],
                    any4_differences: list[float], shadow_differences: list[float], any3_e_value: float,
                    max_hit_e_value: float, alpha_any3: float = 0.02,
                    alpha_max: float = 0.02, shadow_e_value: float = 0.0,
                    alpha_shadow: float = 0.01) -> dict:
    """Evaluate the fixed 200-target portfolio gates; does not tune thresholds."""
    if not (len(any3_differences) == len(max_hit_differences) == len(any4_differences) == len(shadow_differences) == 200):
        return {"pass": False, "reason": "incomplete_200_target_actual_purchase_series"}
    gates = {
        "any3_e_process": any3_e_value >= 1.0 / alpha_any3,
        "max_hit_e_process": max_hit_e_value >= 1.0 / alpha_max,
        "shadow_single_ticket_e_process": shadow_e_value >= 1.0 / alpha_shadow,
        "positive_shadow_mean": sum(shadow_differences) / 200.0 > 0,
        "positive_any3_mean": sum(any3_differences) / 200.0 > 0,
        "positive_max_hit_mean": sum(max_hit_differences) / 200.0 > 0,
        "any4plus_no_harm": sum(any4_differences) / 200.0 >= 0,
    }
    block_checks=[]
    for block in range(4):
        start=block*50;end=start+50
        any3=sum(any3_differences[start:end])/50.0
        max_hit=sum(max_hit_differences[start:end])/50.0
        block_checks.append({"block":block+1,"any3plus_mean_difference":any3,
            "max_hit_mean_difference":max_hit,"positive_both":any3>0 and max_hit>0,
            "within_registered_floor":any3>=-0.02 and max_hit>=-0.10})
    gates["block_stability"]=(sum(x["positive_both"] for x in block_checks)>=3
        and all(x["within_registered_floor"] for x in block_checks))
    return {"pass": all(gates.values()), "gates": gates, "blocks": block_checks}
