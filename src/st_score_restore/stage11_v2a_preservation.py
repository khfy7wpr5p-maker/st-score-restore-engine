"""Stage 11 V2a conservative symbol-preservation fine-tuning policy.

V2a is a development-only continuation of the V2 Residual U-Net. It is allowed to use
train/development data and the V2 development result for tuning. Frozen held-out data
remains forbidden until the V2a development gate passes.
"""
from __future__ import annotations

from typing import Any, Mapping

from .stage11_v2_symbol_preservation import LossWeights, development_gate

V2A_POLICY_ID = "stage11.v2a.symbol-preservation.finetune.v1"
V2A_LOSS_WEIGHTS = LossWeights(
    pixel_l1=0.34,
    edge_l1=0.14,
    symbol_region_l1=0.30,
    ink_recall_penalty=0.22,
)
V2A_MAX_EPOCHS = 8
V2A_LEARNING_RATE = 5e-5
V2A_MIN_PIXEL_IMPROVEMENT_PERCENT = 45.0
V2A_MIN_EDGE_IMPROVEMENT_PERCENT = 5.0
V2A_TARGET_INK_RECALL_DELTA = -0.05
V2A_IDEAL_INK_RECALL_DELTA = -0.02

# Imported from the completed V2 development evidence. These values are reference-only;
# they are not used as training labels and they do not authorize held-out evaluation.
V2_DEVELOPMENT_REFERENCE = {
    "inkRecallDelta": -0.05993542307987809,
    "pixelL1ImprovementPercent": 57.808715708373306,
    "edgeL1ImprovementPercent": 13.596753265825802,
    "falseInkRateDelta": -0.09770500852027908,
    "status": "review_required",
}


def v2a_candidate_gate(metrics: Mapping[str, Any]) -> dict[str, Any]:
    """Apply the V2 preservation gate plus conservative cleanup-retention floors."""
    base = development_gate(metrics)
    pixel = float(metrics["pixelL1ImprovementPercent"])
    edge = float(metrics["edgeL1ImprovementPercent"])
    reasons = list(base["reasonCodes"])
    if pixel < V2A_MIN_PIXEL_IMPROVEMENT_PERCENT:
        reasons.append("pixel_restoration_below_v2a_cleanup_floor")
    if edge < V2A_MIN_EDGE_IMPROVEMENT_PERCENT:
        reasons.append("edge_restoration_below_v2a_cleanup_floor")
    passed = not reasons
    return {
        **base,
        "status": "pass" if passed else "review_required",
        "developmentGatePassed": passed,
        "eligibleForFrozenHeldOutEvaluation": passed,
        "reasonCodes": reasons,
        "v2aPixelImprovementFloor": V2A_MIN_PIXEL_IMPROVEMENT_PERCENT,
        "v2aEdgeImprovementFloor": V2A_MIN_EDGE_IMPROVEMENT_PERCENT,
    }


def v2a_candidate_rank(metrics: Mapping[str, Any]) -> tuple[float, float, float, float]:
    """Rank dev-only checkpoints: pass first, then preservation, then cleanup quality."""
    gate = v2a_candidate_gate(metrics)
    return (
        1.0 if gate["developmentGatePassed"] else 0.0,
        float(metrics["inkRecallDelta"]),
        float(metrics["pixelL1ImprovementPercent"]),
        float(metrics["edgeL1ImprovementPercent"]),
    )
