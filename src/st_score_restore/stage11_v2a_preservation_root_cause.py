"""Stage 11-only root-cause analysis for frozen V2a preservation review.

This module deliberately does not replace the shared music safety validator.  It provides a
narrow analysis layer for the already-frozen V2a candidate so the conservative PR #209
signals can be separated into: (a) execution-profile determinism, (b) near-edge raster
changes, (c) robust component displacement, and (d) genuinely unresolved preservation
risk.  It cannot train, tune, select, promote, expose a route, access held-out data, or
authorize Stage 12.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping

import cv2
import numpy as np

EXPECTED_PACKAGE_SHA256 = "7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234"
EXPECTED_PACKAGE_SIZE_BYTES = 7_817_857
EXPECTED_WIKIMEDIA_SOURCE_SHA256 = "36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb"
EXPECTED_BEETHOVEN_SOURCE_SHA256 = "c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c"
PR208_WIKIMEDIA_SHADOW_SHA256 = "0f914fd2508efb7af84de633d8010e66668a32a47ba647aa0aae2e744e7065e3"
PR209_WIKIMEDIA_SHADOW_SHA256 = "6ecdd820edb5de0bbcf5a560f32015e70f3f44e5d400af58d2de63f01a4711f1"
CONTRACT_ID = "stage11.v2a.preservation-root-cause.nonheldout.v1"
EVIDENCE_TYPE = "stage11_v2a_preservation_root_cause_execution"
EVIDENCE_SCHEMA_VERSION = "stage11.v2a.preservation-root-cause-execution.v1"
CURRENT_TRUTH_TYPE = "stage11_v2a_preservation_root_cause_current_truth"
CURRENT_TRUTH_SCHEMA_VERSION = "1.0.0"


class Stage11V2aPreservationRootCauseError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aPreservationRootCauseError(message)


@dataclass(frozen=True)
class PreservationRedesignConfig:
    """Stage 11-only analysis thresholds; not the shared production validator config."""

    pixel_tolerance_radius: int = 2
    distant_invention_review_fraction: float = 0.01
    distant_invention_reject_fraction: float = 0.04
    tolerant_loss_review_fraction: float = 0.002
    tolerant_loss_reject_fraction: float = 0.02
    component_match_min_area_ratio: float = 0.35
    component_match_gate_fraction: float = 0.008
    component_match_gate_min_pixels: float = 4.0
    component_recall_review_fraction: float = 0.90
    component_recall_reject_fraction: float = 0.80
    component_shift_p95_review_pixels: float = 3.0

    def __post_init__(self) -> None:
        _require(0 <= self.pixel_tolerance_radius <= 8, "invalid pixel tolerance radius")
        for name in (
            "distant_invention_review_fraction", "distant_invention_reject_fraction",
            "tolerant_loss_review_fraction", "tolerant_loss_reject_fraction",
            "component_match_min_area_ratio", "component_match_gate_fraction",
            "component_recall_review_fraction", "component_recall_reject_fraction",
        ):
            value = float(getattr(self, name))
            _require(0.0 <= value <= 1.0, f"invalid {name}")
        _require(self.distant_invention_review_fraction < self.distant_invention_reject_fraction, "invalid invention thresholds")
        _require(self.tolerant_loss_review_fraction < self.tolerant_loss_reject_fraction, "invalid loss thresholds")
        _require(self.component_recall_reject_fraction < self.component_recall_review_fraction, "invalid component recall thresholds")
        _require(self.component_match_gate_min_pixels > 0, "invalid component gate")
        _require(self.component_shift_p95_review_pixels > 0, "invalid component shift threshold")


def preservation_root_cause_contract() -> dict[str, Any]:
    return {
        "contractId": CONTRACT_ID,
        "candidate": {
            "packageSha256": EXPECTED_PACKAGE_SHA256,
            "packageSizeBytes": EXPECTED_PACKAGE_SIZE_BYTES,
            "frozen": True,
        },
        "scope": {
            "nonheldoutOnly": True,
            "stage11AnalysisOnly": True,
            "sharedMusicSafetyValidatorModified": False,
            "httpApiModified": False,
            "normalJobServiceModified": False,
            "semanticPerClassIdentityClaimed": False,
            "threadProfileCanAffectCpuOutputBytes": True,
        },
        "analysis": {
            "nearEdgeRasterTolerance": "euclidean-distance-transform",
            "componentShiftStatistic": "distance-gated-nearest-centroid-distribution",
            "singleMaxShiftIsRejectVeto": False,
            "unreliable72DpiSystemCountIsSemanticVeto": False,
            "semanticIdentityRequiredForAutomaticPass": True,
        },
        "authorization": {
            "rootCauseAnalysisAuthorized": True,
            "trainingAuthorized": False,
            "tuningAuthorized": False,
            "productionInferenceAuthorized": False,
            "productionPromotionAuthorized": False,
            "realUserRolloutAuthorized": False,
            "finalProductionModelSelectionAuthorized": False,
            "stage12EntryAuthorized": False,
        },
    }


def _mask(value: Any, label: str) -> np.ndarray:
    result = np.asarray(value, dtype=bool)
    _require(result.ndim == 2 and result.size > 0, f"{label} mask must be a non-empty 2-D array")
    return result


def distance_tolerant_ink_metrics(source_mask: Any, candidate_mask: Any, *, radius: int = 2) -> dict[str, Any]:
    """Measure loss/invention only when no corresponding ink exists within ``radius`` pixels."""

    source = _mask(source_mask, "source")
    candidate = _mask(candidate_mask, "candidate")
    _require(source.shape == candidate.shape, "source/candidate masks must have identical shape")
    _require(0 <= int(radius) <= 8, "radius outside bounded Stage 11 analysis range")

    source_count = int(source.sum())
    candidate_count = int(candidate.sum())
    source_distance = cv2.distanceTransform((~source).astype(np.uint8), cv2.DIST_L2, 5)
    candidate_distance = cv2.distanceTransform((~candidate).astype(np.uint8), cv2.DIST_L2, 5)
    tolerant_loss = source & (candidate_distance > float(radius))
    distant_invention = candidate & (source_distance > float(radius))
    raw_invention = candidate & ~source
    raw_loss = source & ~candidate
    raw_invention_count = int(raw_invention.sum())
    raw_loss_count = int(raw_loss.sum())
    tolerant_loss_count = int(tolerant_loss.sum())
    distant_invention_count = int(distant_invention.sum())

    within_radius_invention = max(0, raw_invention_count - distant_invention_count)
    return {
        "radiusPixels": int(radius),
        "sourceDarkPixels": source_count,
        "candidateDarkPixels": candidate_count,
        "rawLostDarkPixels": raw_loss_count,
        "rawInventedDarkPixels": raw_invention_count,
        "tolerantLostDarkPixels": tolerant_loss_count,
        "distantInventedDarkPixels": distant_invention_count,
        "tolerantLossFraction": round(tolerant_loss_count / max(1, source_count), 8),
        "distantInventionFraction": round(distant_invention_count / max(1, source_count), 8),
        "rawInventionWithinRadiusFraction": round(within_radius_invention / max(1, raw_invention_count), 8),
    }


def _components(mask: np.ndarray, *, min_area: int = 2, max_area: int = 2500) -> list[dict[str, float]]:
    count, _, stats, centroids = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    items: list[dict[str, float]] = []
    for index in range(1, count):
        area = int(stats[index, cv2.CC_STAT_AREA])
        if min_area <= area <= max_area:
            items.append({"area": float(area), "cx": float(centroids[index, 0]), "cy": float(centroids[index, 1])})
    return items


def robust_component_shift_metrics(
    source_mask: Any,
    candidate_mask: Any,
    *,
    min_area_ratio: float = 0.35,
    gate_fraction: float = 0.008,
    gate_min_pixels: float = 4.0,
) -> dict[str, Any]:
    """Summarize nearest plausible centroid shifts; a single max outlier is never a veto."""

    source = _mask(source_mask, "source")
    candidate = _mask(candidate_mask, "candidate")
    _require(source.shape == candidate.shape, "source/candidate masks must have identical shape")
    source_items = _components(source)
    candidate_items = _components(candidate)
    diagonal = math.hypot(*source.shape)
    gate = max(float(gate_min_pixels), diagonal * float(gate_fraction))
    shifts: list[float] = []
    for item in source_items:
        best = None
        for other in candidate_items:
            area_ratio = min(item["area"], other["area"]) / max(item["area"], other["area"])
            if area_ratio < min_area_ratio:
                continue
            distance = math.hypot(item["cx"] - other["cx"], item["cy"] - other["cy"])
            if distance <= gate and (best is None or distance < best):
                best = distance
        if best is not None:
            shifts.append(best)
    matched = len(shifts)
    recall = matched / max(1, len(source_items))
    array = np.asarray(shifts, dtype=np.float64)
    percentile = lambda p: float(np.percentile(array, p)) if array.size else 0.0
    return {
        "sourceComponentCount": len(source_items),
        "candidateComponentCount": len(candidate_items),
        "matchedSourceComponentCount": matched,
        "matchRecall": round(recall, 8),
        "gatePixels": round(gate, 6),
        "medianShiftPixels": round(percentile(50), 6),
        "p95ShiftPixels": round(percentile(95), 6),
        "p99ShiftPixels": round(percentile(99), 6),
        "maxShiftPixels": round(float(array.max()) if array.size else 0.0, 6),
        "singleMaximumUsedAsRejectVeto": False,
    }


def geometry_reliability_from_legacy_review(review: Mapping[str, Any]) -> dict[str, Any]:
    geometry = review.get("geometry") or {}
    staff = geometry.get("staff") or {}
    tab = geometry.get("tab") or {}
    unknown = geometry.get("unknownSystems") or {}
    recognized_source = int(staff.get("sourceSystemCount", 0)) + int(tab.get("sourceSystemCount", 0))
    recognized_candidate = int(staff.get("candidateSystemCount", 0)) + int(tab.get("candidateSystemCount", 0))
    preserved = bool(staff.get("systemCountPreserved", False)) and bool(tab.get("systemCountPreserved", False))
    reliable = (
        recognized_source > 0
        and recognized_candidate > 0
        and preserved
        and int(unknown.get("source", 0)) == 0
        and int(unknown.get("candidate", 0)) == 0
    )
    return {
        "reliableForVeto": reliable,
        "recognizedSourceSystems": recognized_source,
        "recognizedCandidateSystems": recognized_candidate,
        "legacySystemCountsPreserved": preserved,
        "unreliableGeometryIsSemanticRejectVeto": False,
    }


def classify_stage11_redesign(
    tolerant_ink: Mapping[str, Any],
    components: Mapping[str, Any],
    geometry: Mapping[str, Any],
    *,
    semantic_identity_established: bool = False,
    config: PreservationRedesignConfig | None = None,
) -> dict[str, Any]:
    """Fail closed while preventing known false-veto mechanisms from deciding by themselves."""

    resolved = config or PreservationRedesignConfig()
    reject: list[str] = []
    review: list[str] = []
    loss = float(tolerant_ink.get("tolerantLossFraction", 1.0))
    invention = float(tolerant_ink.get("distantInventionFraction", 1.0))
    component_recall = float(components.get("matchRecall", 0.0))
    p95 = float(components.get("p95ShiftPixels", float("inf")))

    if loss >= resolved.tolerant_loss_reject_fraction:
        reject.append("distance_tolerant_symbol_loss_severe")
    elif loss >= resolved.tolerant_loss_review_fraction:
        review.append("distance_tolerant_symbol_loss_detected")
    if invention >= resolved.distant_invention_reject_fraction:
        reject.append("distant_dark_invention_severe")
    elif invention >= resolved.distant_invention_review_fraction:
        review.append("distant_dark_invention_detected")
    if component_recall < resolved.component_recall_reject_fraction:
        reject.append("robust_component_recall_severe")
    elif component_recall < resolved.component_recall_review_fraction:
        review.append("robust_component_recall_reduced")
    if p95 >= resolved.component_shift_p95_review_pixels:
        review.append("component_shift_distribution_detected")
    if not bool(geometry.get("reliableForVeto", False)):
        review.append("geometry_detector_unreliable_for_semantic_veto")
    if not semantic_identity_established:
        review.append("semantic_identity_not_established")

    reject = sorted(set(reject))
    review = sorted(set(review) - set(reject))
    verdict = "reject" if reject else "review_required" if review else "pass"
    return {
        "verdict": verdict,
        "automaticApproval": False,
        "rejectReasons": reject,
        "reviewRequiredReasons": review,
        "semanticIdentityEstablished": bool(semantic_identity_established),
        "sharedMusicSafetyValidatorModified": False,
        "configuration": asdict(resolved),
    }


def validate_root_cause_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == EVIDENCE_TYPE, "root-cause evidence type mismatch")
    _require(payload.get("schemaVersion") == EVIDENCE_SCHEMA_VERSION, "root-cause evidence schema mismatch")
    _require(payload.get("status") == "completed", "root-cause evidence must be completed")
    _require(payload.get("contractId") == CONTRACT_ID, "root-cause contract mismatch")
    _require(payload.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "package SHA mismatch")
    _require(int(payload.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "package size mismatch")
    sources = payload.get("sources") or {}
    _require((sources.get("wikimedia") or {}).get("sha256") == EXPECTED_WIKIMEDIA_SOURCE_SHA256, "Wikimedia source SHA mismatch")
    _require((sources.get("beethoven") or {}).get("sha256") == EXPECTED_BEETHOVEN_SOURCE_SHA256, "Beethoven source SHA mismatch")

    determinism = payload.get("determinism") or {}
    _require(determinism.get("rootCauseFinding") == "cpu_intraop_thread_profile_changes_decoded_output_pixels", "determinism root-cause finding mismatch")
    _require(determinism.get("scopeClaim") == "sufficient_for_wikimedia_pr208_pr209_drift_not_claimed_for_all_five_pages", "determinism scope must remain bounded")
    profiles = determinism.get("threadProfiles") or []
    by_threads = {int(item.get("intraopThreads", -1)): item for item in profiles if isinstance(item, Mapping)}
    _require((by_threads.get(5) or {}).get("shadowSha256") == PR208_WIKIMEDIA_SHADOW_SHA256, "thread=5 must reproduce PR #208 hash")
    _require((by_threads.get(4) or {}).get("shadowSha256") == PR209_WIKIMEDIA_SHADOW_SHA256, "thread=4 must reproduce PR #209 hash")
    _require((by_threads.get(8) or {}).get("shadowSha256") == PR209_WIKIMEDIA_SHADOW_SHA256, "thread=8 must reproduce PR #209 hash")
    repeat = determinism.get("repeatabilityAtThreads5") or {}
    _require(repeat.get("run1Sha256") == repeat.get("run2Sha256") == PR208_WIKIMEDIA_SHADOW_SHA256, "thread=5 repeat hashes must be byte-identical")
    _require(float(repeat.get("decodedMaxAbsDiff", 1.0)) == 0.0, "thread=5 repeat decoded pixels must be identical")
    cross_profile = determinism.get("crossProfileDifference") or {}
    _require(int(cross_profile.get("changedPixelCount", 0)) == 1, "cross-profile changed-pixel count mismatch")
    _require(int(cross_profile.get("decodedMaxAbsDiff", 0)) == 1, "cross-profile max pixel difference mismatch")

    redesign = payload.get("validatorRedesign") or {}
    _require(redesign.get("sharedMusicSafetyValidatorModified") is False, "shared validator must remain untouched")
    wikimedia = redesign.get("wikimedia") or {}
    _require(int(wikimedia.get("legacyRawInventedDarkPixels", 0)) == 29_866, "Wikimedia legacy invention count mismatch")
    _require(abs(float(wikimedia.get("rawInventionWithin1pxFraction", 0.0)) - 0.8093) <= 0.0002, "Wikimedia 1px fraction mismatch")
    _require(abs(float(wikimedia.get("rawInventionWithin2pxFraction", 0.0)) - 0.9174) <= 0.0002, "Wikimedia 2px fraction mismatch")
    _require(int(wikimedia.get("tolerantLostDarkPixels2px", -1)) == 5, "Wikimedia tolerant loss mismatch")
    _require(int(wikimedia.get("distantInventedDarkPixels2px", -1)) == 2_467, "Wikimedia distant invention mismatch")
    component = wikimedia.get("componentShiftDistribution") or {}
    _require(float(component.get("p95Pixels", 99.0)) < 1.6, "Wikimedia p95 component shift unexpectedly high")
    _require(float(component.get("p99Pixels", 99.0)) < 4.5, "Wikimedia p99 component shift unexpectedly high")
    _require(float(component.get("maxPixels", 0.0)) > 8.0, "Wikimedia max outlier evidence missing")
    _require(component.get("singleMaximumUsedAsRejectVeto") is False, "single maximum may not be reject veto")
    _require(wikimedia.get("redesignedVerdict") == "review_required", "Wikimedia redesigned verdict mismatch")

    aggregate = payload.get("aggregate") or {}
    _require(int(aggregate.get("pageCount", 0)) == 5, "aggregate page count mismatch")
    _require(aggregate.get("verdictCounts") == {"pass": 0, "reject": 4, "review_required": 1}, "aggregate redesigned verdict counts mismatch")
    _require(aggregate.get("preservationDisposition") == "blocked", "preservation must remain blocked")

    safety = payload.get("safety") or {}
    for key in ("heldOutAccessed", "optimizerCreated", "backpropagationExecuted", "weightsMutated", "trainingPerformed", "tuningPerformed", "realUserDataUsed"):
        _require(safety.get(key) is False, f"root-cause safety flag must be false: {key}")
    authorization = payload.get("authorization") or {}
    _require(authorization.get("rootCauseAnalysisAuthorized") is True, "root-cause authorization missing")
    for key in ("trainingAuthorized", "tuningAuthorized", "productionInferenceAuthorized", "productionPromotionAuthorized", "realUserRolloutAuthorized", "finalProductionModelSelectionAuthorized", "stage12EntryAuthorized"):
        _require(authorization.get(key) is False, f"authorization must remain false: {key}")
    _require(payload.get("contract") == preservation_root_cause_contract(), "root-cause contract snapshot mismatch")
    return {
        "status": "pass",
        "determinismRootCausePartiallyResolved": True,
        "wikimediaFalseVetoMechanismsDiagnosed": True,
        "preservationDisposition": "blocked",
        "productionPromotionAuthorized": False,
        "stage12EntryAuthorized": False,
    }


def validate_root_cause_current_truth(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == CURRENT_TRUTH_TYPE, "current truth type mismatch")
    _require(payload.get("schemaVersion") == CURRENT_TRUTH_SCHEMA_VERSION, "current truth schema mismatch")
    _require(payload.get("state") == "ROOT_CAUSE_DIAGNOSED_VALIDATOR_REDESIGN_BLOCKED", "current truth state mismatch")
    _require(payload.get("baseMainSha") == "7966102edc40aa6ab3ba5216342ae34bc237acdb", "current truth base SHA mismatch")
    _require(payload.get("implementationBranch") == "stage11-v2a-preservation-root-cause-closure", "current truth branch mismatch")
    _require(payload.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "current truth package SHA mismatch")
    determinism = payload.get("determinism") or {}
    _require(determinism.get("wikimediaPr208Pr209ThreadProfileRootCauseEstablished") is True, "thread-profile root cause must be established for Wikimedia")
    _require(determinism.get("allFiveHistoricalDriftsFullyExplained") is False, "all historical drift must not be over-claimed")
    redesign = payload.get("validatorRedesign") or {}
    _require(redesign.get("sharedValidatorChanged") is False, "shared validator boundary must remain unchanged")
    _require(redesign.get("redesignedVerdictCounts") == {"pass": 0, "reject": 4, "review_required": 1}, "current truth verdict counts mismatch")
    _require(redesign.get("productionPromotionStillBlocked") is True, "promotion must remain blocked")
    authorization = payload.get("authorization") or {}
    for key in ("productionInferenceAuthorized", "productionPromotionAuthorized", "realUserRolloutAuthorized", "finalProductionModelSelectionAuthorized", "stage12EntryAuthorized"):
        _require(authorization.get(key) is False, f"current truth authorization must remain false: {key}")
    return {
        "status": "pass",
        "state": "ROOT_CAUSE_DIAGNOSED_VALIDATOR_REDESIGN_BLOCKED",
        "productionPromotionAuthorized": False,
        "stage12EntryAuthorized": False,
    }


__all__ = [
    "CONTRACT_ID",
    "PreservationRedesignConfig",
    "Stage11V2aPreservationRootCauseError",
    "classify_stage11_redesign",
    "distance_tolerant_ink_metrics",
    "geometry_reliability_from_legacy_review",
    "preservation_root_cause_contract",
    "robust_component_shift_metrics",
    "validate_root_cause_current_truth",
    "validate_root_cause_evidence",
]
