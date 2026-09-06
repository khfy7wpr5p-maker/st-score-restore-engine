"""Stage 9 provider-neutral multi-engine comparator foundation.

The comparator consumes only provenance-bound restoration evidence after safety
validation. It never overrides a hard deterministic/semantic veto, never turns a
review-required variant into an automatic winner, and always retains the immutable
original as a first-class baseline. The result is a recommendation, not teacher
approval or production activation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

CONTRACT_VERSION = "stage9.multi-engine-comparator.v1"
POLICY_ID = "stage9.lexicographic-quality-evidence.v1"

OUTCOME_ORIGINAL_PREFERRED = "original_preferred"
OUTCOME_VARIANT_PREFERRED = "restoration_variant_preferred"
OUTCOME_REVIEW_REQUIRED = "review_required"
OUTCOME_ORIGINAL_RETAINED = "original_retained_no_acceptable_derivative"


class ComparatorContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ComparatorContractError(message)


def _decimal(value: Any) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ComparatorContractError("quality evidence must be finite numeric values") from exc
    _require(result.is_finite(), "quality evidence must be finite numeric values")
    return result


@dataclass(frozen=True)
class ComparatorPolicy:
    policy_id: str = POLICY_ID
    quality_dimensions: tuple[str, ...] = (
        "documentQualityDelta",
        "legibilityDelta",
        "contrastDelta",
        "noiseReductionEvidence",
    )

    def __post_init__(self) -> None:
        _require(self.policy_id == POLICY_ID, "unreviewed comparator policy")
        _require(bool(self.quality_dimensions), "at least one quality dimension is required")


def _source_entry(source_artifact_id: str) -> dict[str, Any]:
    return {
        "artifactId": source_artifact_id,
        "role": "immutable_source",
        "engineId": "original",
        "eligible": True,
        "hardVeto": False,
        "reviewRequired": False,
        "reasonCodes": ["immutable_original_baseline"],
    }


def _normalize_variant(
    source_artifact_id: str,
    variant: Mapping[str, Any],
    policy: ComparatorPolicy,
) -> dict[str, Any]:
    _require(isinstance(variant, Mapping), "variant evidence must be an object")
    artifact_id = str(variant.get("artifactId") or "").strip()
    engine_id = str(variant.get("engineId") or "").strip()
    engine_version = str(variant.get("engineVersion") or "").strip()
    config_digest = str(variant.get("configDigest") or "").strip()
    derived_from = str(variant.get("derivedFrom") or "").strip()
    verdict = str(variant.get("safetyVerdict") or "").strip().lower()
    hard_veto = bool(variant.get("hardVeto"))
    semantic_hard_veto = bool(variant.get("semanticHardVeto"))
    provenance_complete = all((artifact_id, engine_id, engine_version, config_digest, derived_from))
    reasons: list[str] = []

    if not provenance_complete:
        reasons.append("provenance_incomplete")
    if derived_from != source_artifact_id:
        reasons.append("source_provenance_mismatch")
    if hard_veto:
        reasons.append("hard_deterministic_veto")
    if semantic_hard_veto:
        reasons.append("hard_semantic_veto")
    if verdict == "reject":
        reasons.append("music_safety_reject")
    elif verdict == "review_required":
        reasons.append("music_safety_review_required")
    elif verdict == "pass":
        reasons.append("music_safety_pass")
    else:
        reasons.append("music_safety_unknown")

    eligible = (
        provenance_complete
        and derived_from == source_artifact_id
        and verdict == "pass"
        and not hard_veto
        and not semantic_hard_veto
    )
    review_required = (
        verdict == "review_required"
        or verdict not in {"pass", "reject"}
        or not provenance_complete
        or derived_from != source_artifact_id
    ) and not (hard_veto or semantic_hard_veto or verdict == "reject")

    quality = variant.get("qualityEvidence")
    quality_values: tuple[Decimal, ...] | None = None
    positive_evidence = False
    if eligible and isinstance(quality, Mapping):
        values = tuple(_decimal(quality.get(name, 0)) for name in policy.quality_dimensions)
        structural_risk = _decimal(variant.get("structuralRisk", 0))
        quality_values = values + (-structural_risk,)
        positive_evidence = any(value > 0 for value in values)
        if positive_evidence:
            reasons.append("positive_quality_evidence")
        else:
            reasons.append("no_positive_quality_evidence")
    elif eligible:
        reasons.append("quality_evidence_missing")

    return {
        "artifactId": artifact_id,
        "role": "restoration_variant",
        "engineId": engine_id,
        "engineVersion": engine_version,
        "configDigest": config_digest,
        "derivedFrom": derived_from,
        "safetyVerdict": verdict or "unknown",
        "hardVeto": hard_veto or semantic_hard_veto or verdict == "reject",
        "reviewRequired": review_required,
        "eligible": eligible,
        "qualityVector": tuple(str(value) for value in quality_values) if quality_values is not None else None,
        "positiveQualityEvidence": positive_evidence,
        "reasonCodes": reasons,
        "_rank": quality_values,
    }


def compare_restoration_variants(
    source_artifact_id: str,
    variants: Iterable[Mapping[str, Any]],
    *,
    policy: ComparatorPolicy | None = None,
) -> dict[str, Any]:
    """Return an explainable, deterministic Stage 9 recommendation."""

    _require(isinstance(source_artifact_id, str) and bool(source_artifact_id.strip()), "source artifact id required")
    policy = policy or ComparatorPolicy()
    normalized = [_normalize_variant(source_artifact_id, item, policy) for item in variants]
    normalized.sort(key=lambda item: (item["engineId"], item["engineVersion"], item["artifactId"]))

    hard_rejected = [item for item in normalized if item["hardVeto"]]
    review_pool = [item for item in normalized if item["reviewRequired"]]
    eligible = [item for item in normalized if item["eligible"] and item["positiveQualityEvidence"] and item["_rank"] is not None]

    recommendation = _source_entry(source_artifact_id)
    outcome = OUTCOME_ORIGINAL_PREFERRED
    reason_codes = ["immutable_original_baseline", "no_derivative_proven_better"]

    if eligible:
        ranked = sorted(eligible, key=lambda item: (item["_rank"], item["artifactId"]), reverse=True)
        best = ranked[0]
        same_rank = [item for item in ranked if item["_rank"] == best["_rank"]]
        if len(same_rank) > 1:
            outcome = OUTCOME_REVIEW_REQUIRED
            reason_codes = ["quality_evidence_tie", "original_retained_pending_review"]
        else:
            outcome = OUTCOME_VARIANT_PREFERRED
            recommendation = {key: value for key, value in best.items() if not key.startswith("_")}
            reason_codes = ["safety_pass", "positive_quality_evidence", "deterministic_lexicographic_preference"]
    elif review_pool:
        outcome = OUTCOME_REVIEW_REQUIRED
        reason_codes = ["uncertain_or_review_required_evidence", "original_retained_pending_review"]
    elif normalized and len(hard_rejected) == len(normalized):
        outcome = OUTCOME_ORIGINAL_RETAINED
        reason_codes = ["no_acceptable_derivative", "original_retained"]

    public_variants = [{key: value for key, value in item.items() if not key.startswith("_")} for item in normalized]
    return {
        "contractVersion": CONTRACT_VERSION,
        "policyId": policy.policy_id,
        "outcome": outcome,
        "recommendedArtifactId": recommendation["artifactId"],
        "recommendedRole": recommendation["role"],
        "recommendationOnly": True,
        "automaticFinalSelectionAuthorized": False,
        "teacherApprovalImplied": False,
        "omrCorrectnessImplied": False,
        "musicalTruthImplied": False,
        "originalSelectable": True,
        "originalArtifactId": source_artifact_id,
        "reasonCodes": reason_codes,
        "eligibleDerivativeCount": sum(1 for item in normalized if item["eligible"]),
        "hardRejectedDerivativeCount": len(hard_rejected),
        "reviewDerivativeCount": len(review_pool),
        "variants": public_variants,
    }


def run_synthetic_comparator_drills() -> dict[str, Any]:
    source = "sha256:stage9-synthetic-source"
    safe = {
        "artifactId": "sha256:safe",
        "engineId": "opencv",
        "engineVersion": "synthetic-1",
        "configDigest": "sha256:config-safe",
        "derivedFrom": source,
        "safetyVerdict": "pass",
        "qualityEvidence": {"documentQualityDelta": 2, "legibilityDelta": 1},
        "structuralRisk": 0.1,
    }
    rejected_but_pretty = {
        "artifactId": "sha256:rejected",
        "engineId": "docres",
        "engineVersion": "synthetic-1",
        "configDigest": "sha256:config-rejected",
        "derivedFrom": source,
        "safetyVerdict": "reject",
        "qualityEvidence": {"documentQualityDelta": 999, "legibilityDelta": 999},
        "structuralRisk": 0,
    }
    no_gain = {
        "artifactId": "sha256:no-gain",
        "engineId": "opencv",
        "engineVersion": "synthetic-2",
        "configDigest": "sha256:config-no-gain",
        "derivedFrom": source,
        "safetyVerdict": "pass",
        "qualityEvidence": {"documentQualityDelta": 0, "legibilityDelta": 0},
        "structuralRisk": 0,
    }
    winner = compare_restoration_variants(source, [rejected_but_pretty, safe])
    original = compare_restoration_variants(source, [no_gain])
    unknown = compare_restoration_variants(source, [{**safe, "artifactId": "sha256:unknown", "safetyVerdict": "unknown"}])
    passed = all(
        (
            winner["recommendedArtifactId"] == "sha256:safe",
            winner["hardRejectedDerivativeCount"] == 1,
            winner["automaticFinalSelectionAuthorized"] is False,
            original["recommendedArtifactId"] == source,
            original["outcome"] == OUTCOME_ORIGINAL_PREFERRED,
            unknown["outcome"] == OUTCOME_REVIEW_REQUIRED,
            unknown["recommendedArtifactId"] == source,
        )
    )
    return {
        "contractVersion": CONTRACT_VERSION,
        "result": "PASS" if passed else "BLOCKED",
        "syntheticOnly": True,
        "providerSpecificRuntimeUsed": False,
        "docresLiveRuntimeUsed": False,
        "modelTrainingPerformed": False,
        "stage9aActivated": False,
        "stage10Activated": False,
        "automaticFinalSelectionPerformed": False,
        "scenarios": {"safe_beats_rejected": winner, "original_no_gain": original, "unknown_routes_review": unknown},
    }


__all__ = [
    "CONTRACT_VERSION",
    "POLICY_ID",
    "ComparatorContractError",
    "ComparatorPolicy",
    "compare_restoration_variants",
    "run_synthetic_comparator_drills",
]
