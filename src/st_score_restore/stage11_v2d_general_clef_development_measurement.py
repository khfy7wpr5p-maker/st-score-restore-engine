"""Validation for the Stage 11 general-clef successor development replay.

This is deliberately development evidence, not qualification evidence. The same
213-box teacher corpus was used while selecting the deterministic geometry
policy, so the artifact must disclose that selection path and must never
self-authorize holdout access, detector qualification, Stage 11 closure,
production, or Stage 12 entry.
"""
from __future__ import annotations

import math
from typing import Any, Mapping


SCHEMA_VERSION_V1 = "stage11.v2d.general-clef-successor-development-measurement.v1"
SCHEMA_VERSION_V2 = "stage11.v2d.general-clef-successor-development-measurement.v2"
SCHEMA_VERSION = SCHEMA_VERSION_V1
EXPECTED_TEACHER_SHA256 = "68df771d5ace9f0b968452ff532fa2693fa2cd3405477d91fa3a98eccb190d54"
EXPECTED_HISTORICAL_OEMER_SHA256 = "bfb1e99b779453ee272c6679b29ac884a10183d841ca45bdcab6dbc394d10e1a"
EXPECTED_TEACHER_COUNTS = {"treble": 165, "bass": 34, "tab": 12, "soprano": 2}
EXPECTED_POOLED = {
    "teacherBoxCount": 213,
    "candidateCount": 205,
    "tp": 201,
    "fp": 4,
    "fn": 12,
}
EXPECTED_TYPED = {
    "treble": {"teacherBoxes": 165, "candidateCount": 157, "typedTp": 157, "typedFp": 0, "typedFn": 8},
    "bass": {"teacherBoxes": 34, "candidateCount": 36, "typedTp": 32, "typedFp": 4, "typedFn": 2},
    "tab": {"teacherBoxes": 12, "candidateCount": 12, "typedTp": 12, "typedFp": 0, "typedFn": 0},
    "soprano": {"teacherBoxes": 2, "candidateCount": 0, "typedTp": 0, "typedFp": 0, "typedFn": 2},
}
EXPECTED_TARGETS = {
    "pooledPrecisionMinimum": 0.90,
    "pooledRecallMinimum": 0.85,
    "trebleRecallMinimum": 0.90,
    "bassRecallMinimum": 0.85,
    "tabRecallMinimum": 0.80,
}
FORBIDDEN_TRUE_CLAIMS = (
    "qualificationEvidence",
    "detectorQualified",
    "freshIndependentHoldoutAuthorized",
    "freshIndependentHoldoutAccessed",
    "trainingOrFineTuningPerformed",
    "p414Modified",
    "pr211MergeAuthorized",
    "productionPromotionAuthorized",
    "overallStage11PassAuthorized",
    "stage12EntryAuthorized",
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _finite_probability(value: Any, name: str) -> float:
    result = float(value)
    _require(math.isfinite(result) and 0.0 <= result <= 1.0, f"{name} must be in [0,1]")
    return result


def _metric(tp: int, fp: int, fn: int) -> dict[str, float | int]:
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def validate_general_clef_development_measurement(payload: Mapping[str, Any]) -> dict[str, Any]:
    schema_version = payload.get("schemaVersion")
    _require(
        schema_version in {SCHEMA_VERSION_V1, SCHEMA_VERSION_V2},
        "general-clef development schema mismatch",
    )
    _require(payload.get("developmentOnly") is True, "artifact must remain development-only")
    _require(payload.get("qualificationEvidence") is False, "development replay cannot become qualification evidence")

    inputs = payload.get("inputBindings") or {}
    teacher = inputs.get("teacherTruth") or {}
    _require(teacher.get("sha256") == EXPECTED_TEACHER_SHA256, "teacher truth SHA-256 mismatch")
    _require(teacher.get("pageCount") == 18, "teacher page count mismatch")
    _require(teacher.get("clefBoxCount") == 213, "teacher clef-box count mismatch")
    _require(teacher.get("clefTypeCounts") == EXPECTED_TEACHER_COUNTS, "teacher subtype counts mismatch")
    _require(inputs.get("sourceImageIdentityMatchedCount") == 18, "source-image identity must match 18/18 pages")

    historical = inputs.get("historicalOemerDevelopmentArtifact") or {}
    _require(
        historical.get("sha256") == EXPECTED_HISTORICAL_OEMER_SHA256,
        "historical Oemer development artifact SHA-256 mismatch",
    )
    _require(historical.get("coordinateSpace") == "oemer_resized_prediction_pixels", "historical coordinate-space disclosure mismatch")
    _require(historical.get("qualificationEvidence") is False, "historical rejected artifact cannot be qualification evidence")

    selection = payload.get("selectionDisclosure") or {}
    _require(selection.get("developmentTruthUsedForThresholdSelection") is True, "development selection disclosure is mandatory")
    _require(selection.get("independentQualificationClaim") is False, "development replay cannot claim independent qualification")
    _require(selection.get("postSelectionReplayOnSameDevelopmentCorpus") is True, "same-corpus replay disclosure required")
    _require(selection.get("freshHoldoutAccessed") is False, "fresh holdout must remain closed")

    matching = payload.get("matching") or {}
    _require(matching.get("method") == "greedy_one_to_one_descending_iou_type_aware", "matching method mismatch")
    _require(float(matching.get("iouThreshold")) == 0.50, "IoU threshold mismatch")

    pooled = payload.get("pooledMetrics") or {}
    for key, expected in EXPECTED_POOLED.items():
        _require(pooled.get(key) == expected, f"pooled metric mismatch: {key}")
    recomputed = _metric(EXPECTED_POOLED["tp"], EXPECTED_POOLED["fp"], EXPECTED_POOLED["fn"])
    for key in ("precision", "recall", "f1"):
        actual = _finite_probability(pooled.get(key), f"pooled {key}")
        _require(abs(actual - float(recomputed[key])) <= 1e-12, f"pooled {key} mismatch")

    subtype = payload.get("perSubtype") or {}
    _require(set(subtype) == set(EXPECTED_TYPED), "per-subtype set mismatch")
    for clef_type, expected in EXPECTED_TYPED.items():
        record = subtype.get(clef_type) or {}
        for key, value in expected.items():
            _require(record.get(key) == value, f"{clef_type}.{key} mismatch")
        tp, fp, fn = expected["typedTp"], expected["typedFp"], expected["typedFn"]
        derived = _metric(tp, fp, fn)
        _require(abs(_finite_probability(record.get("precision"), f"{clef_type}.precision") - float(derived["precision"])) <= 1e-12, f"{clef_type}.precision mismatch")
        _require(abs(_finite_probability(record.get("recall"), f"{clef_type}.recall") - float(derived["recall"])) <= 1e-12, f"{clef_type}.recall mismatch")

    targets = payload.get("developmentTargets") or {}
    _require(targets == EXPECTED_TARGETS, "development targets mismatch")
    assessment = payload.get("targetAssessment") or {}
    _require(assessment.get("pooledPrecisionPass") is True, "pooled precision target must pass")
    _require(assessment.get("pooledRecallPass") is True, "pooled recall target must pass")
    _require(assessment.get("trebleRecallPass") is True, "treble recall target must pass")
    _require(assessment.get("bassRecallPass") is True, "bass recall target must pass")
    _require(assessment.get("tabRecallPass") is True, "TAB recall target must pass")

    decision = payload.get("decision") or {}
    if schema_version == SCHEMA_VERSION_V1:
        _require(
            assessment.get("sopranoDevelopmentExpectationPass") is False,
            "soprano must remain unresolved at this checkpoint",
        )
        _require(
            assessment.get("generalClefDevelopmentFreezeReady") is False,
            "soprano blocker must keep freeze closed",
        )
        _require(
            decision.get("disposition") == "PARTIAL_PASS_SOPRANO_UNRESOLVED",
            "development disposition mismatch",
        )
        _require(
            decision.get("typedTrebleBassTabDevelopmentTargetsMet") is True,
            "treble/bass/TAB target status mismatch",
        )
        _require(
            decision.get("sopranoTypedSupportEstablished") is False,
            "soprano typed support is not established",
        )
        _require(
            decision.get("nextSafeAction")
            == "RESOLVE_SOPRANO_VIA_FROZEN_P4_14_COEXISTENCE_OR_EXPLICIT_REVIEW_PATH_BEFORE_FREEZE",
            "next safe action mismatch",
        )
    else:
        review = payload.get("reviewPath") or {}
        _require(review.get("mode") == "EXPLICIT_REVIEW_ONLY", "review mode mismatch")
        _require(review.get("autoSubtypeAssignment") is False, "review path must not auto-type soprano")
        _require(review.get("outputClefType") == "unknown", "review path output type mismatch")
        _require(review.get("outputStatus") == "REVIEW_REQUIRED", "review path output status mismatch")
        _require(review.get("outputReason") == "POSSIBLE_C_CLEF", "review path reason mismatch")
        _require(
            review.get("candidateProvenance")
            == "source-only:c-clef-review:five-line-c1-compact",
            "review path provenance mismatch",
        )
        _require(review.get("p414Modified") is False, "P4.14 must remain unchanged")

        thresholds = review.get("thresholds") or {}
        expected_thresholds = {
            "minimumFiveLineTopologySupport": 0.60,
            "minimumPresenceConfidence": 0.79,
            "minimumXOffsetStaffSpaces": 0.50,
            "maximumXOffsetStaffSpaces": 2.00,
            "minimumYOffsetStaffSpaces": 1.50,
            "maximumYOffsetStaffSpaces": 2.50,
            "typedSuppressionIou": 0.20,
        }
        _require(thresholds == expected_thresholds, "review-path thresholds mismatch")

        review_metrics = review.get("developmentMeasurement") or {}
        expected_review_counts = {
            "teacherBoxes": 2,
            "candidateCount": 2,
            "tp": 2,
            "fp": 0,
            "fn": 0,
        }
        for key, expected in expected_review_counts.items():
            _require(review_metrics.get(key) == expected, f"review metric mismatch: {key}")
        _require(
            abs(_finite_probability(review_metrics.get("precision"), "review precision") - 1.0)
            <= 1e-12,
            "review precision mismatch",
        )
        _require(
            abs(_finite_probability(review_metrics.get("recall"), "review recall") - 1.0)
            <= 1e-12,
            "review recall mismatch",
        )
        _require(
            review_metrics.get("sameDevelopmentTruthUsedForThresholdSelection") is True,
            "review threshold-selection disclosure required",
        )

        _require(
            assessment.get("sopranoDevelopmentExpectationPass") is True,
            "soprano review-routing expectation must pass",
        )
        _require(
            assessment.get("sopranoReviewRoutingPass") is True,
            "soprano review routing must pass",
        )
        _require(
            assessment.get("sopranoTypedClassificationPass") is False,
            "soprano typed classification must remain unclaimed",
        )
        _require(
            assessment.get("generalClefDevelopmentFreezeReady") is True,
            "development candidate must be freeze-ready",
        )

        _require(
            decision.get("disposition")
            == "DEVELOPMENT_FREEZE_READY_WITH_SOPRANO_REVIEW_ONLY",
            "development disposition mismatch",
        )
        _require(
            decision.get("typedTrebleBassTabDevelopmentTargetsMet") is True,
            "treble/bass/TAB target status mismatch",
        )
        _require(
            decision.get("sopranoTypedSupportEstablished") is False,
            "soprano typed support must remain false",
        )
        _require(
            decision.get("sopranoReviewRoutingEstablished") is True,
            "soprano review routing must be established",
        )
        _require(
            decision.get("candidateFreezePerformed") is False,
            "candidate freeze is a later approval gate",
        )
        _require(
            decision.get("prequalificationPolicyFreezePerformed") is False,
            "prequalification freeze is a later approval gate",
        )
        _require(
            decision.get("nextSafeAction")
            == "FREEZE_GENERAL_CLEF_CANDIDATE_AND_PREQUALIFICATION_POLICY_BEFORE_ANY_FRESH_HOLDOUT_ACCESS",
            "next safe action mismatch",
        )

    boundary = payload.get("claimBoundary") or {}
    for key in FORBIDDEN_TRUE_CLAIMS:
        _require(boundary.get(key) is False, f"forbidden claim must remain false: {key}")
    if schema_version == SCHEMA_VERSION_V2:
        _require(
            boundary.get("generalClefCandidateFrozen") is False,
            "general-clef candidate is not frozen yet",
        )
        _require(
            boundary.get("prequalificationPolicyFrozen") is False,
            "prequalification policy is not frozen yet",
        )

    result = {
        "status": "pass",
        "disposition": decision["disposition"],
        "teacher_box_count": EXPECTED_POOLED["teacherBoxCount"],
        "tp": EXPECTED_POOLED["tp"],
        "fp": EXPECTED_POOLED["fp"],
        "fn": EXPECTED_POOLED["fn"],
        "detector_qualified": False,
        "holdout_authorized": False,
    }
    if schema_version == SCHEMA_VERSION_V2:
        review_metrics = payload["reviewPath"]["developmentMeasurement"]
        result.update(
            {
                "soprano_review_tp": int(review_metrics["tp"]),
                "soprano_review_fp": int(review_metrics["fp"]),
                "soprano_review_fn": int(review_metrics["fn"]),
                "development_freeze_ready": True,
                "soprano_typed_support_established": False,
                "candidate_frozen": False,
            }
        )
    return result


__all__ = [
    "SCHEMA_VERSION",
    "SCHEMA_VERSION_V1",
    "SCHEMA_VERSION_V2",
    "validate_general_clef_development_measurement",
]
