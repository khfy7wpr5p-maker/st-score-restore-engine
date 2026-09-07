"""Stage 10 provider-neutral ST Restore Selector foundation.

The selector plans explicitly approved engines and converts a trusted Stage 9
recommendation plus provenance-bound Stage 9A preservation evidence into a
controlled, non-production source-variant decision. It never bypasses safety,
never overrides hard vetoes, and always retains the immutable original.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

CONTRACT_VERSION = "stage10.st-restore-selector.v1"
POLICY_ID = "stage10.original-aware-fail-closed-selector.v1"
STAGE9_CONTRACT_VERSION = "stage9.multi-engine-comparator.v1"
STAGE9A_CONTRACT_VERSION = "stage9a.mspm-evidence.v1"

DECISION_ORIGINAL = "original_selected"
DECISION_VARIANT = "restoration_variant_selected_for_controlled_use"
DECISION_REVIEW = "original_selected_review_required"


class SelectorContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SelectorContractError(message)


def _text(value: Any) -> str:
    return str(value or "").strip()


def plan_engine_invocations(
    source_artifact_id: str,
    engine_capabilities: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return a deterministic provider-neutral invocation recommendation."""

    source = _text(source_artifact_id)
    _require(bool(source), "source artifact id required")
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw in engine_capabilities:
        _require(isinstance(raw, Mapping), "engine capability must be an object")
        engine_id = _text(raw.get("engineId"))
        approval = _text(raw.get("approvalState")).lower()
        availability = _text(raw.get("availabilityState")).lower()
        enabled = raw.get("enabled") is True
        _require(bool(engine_id), "engineId required")
        _require(engine_id not in seen, "duplicate engineId")
        _require(approval in {"approved", "unapproved"}, "unsupported approvalState")
        _require(availability in {"available", "unavailable"}, "unsupported availabilityState")
        seen.add(engine_id)

        if approval != "approved":
            action, reasons = "skip", ["engine_unapproved"]
        elif availability != "available":
            action, reasons = "skip", ["engine_unavailable"]
        elif not enabled:
            action, reasons = "skip", ["engine_disabled"]
        else:
            action, reasons = "invoke", ["explicitly_approved", "available", "enabled"]

        entries.append(
            {
                "engineId": engine_id,
                "action": action,
                "reasonCodes": reasons,
                "providerPreferenceApplied": False,
            }
        )

    entries.sort(key=lambda item: item["engineId"])
    return {
        "contractVersion": CONTRACT_VERSION,
        "policyId": POLICY_ID,
        "sourceArtifactId": source,
        "originalIncluded": True,
        "originalArtifactId": source,
        "invocationPlan": entries,
        "invokeCount": sum(1 for item in entries if item["action"] == "invoke"),
        "providerSpecificPreferenceApplied": False,
        "networkFetchAuthorized": False,
        "modelArtifactDownloadAuthorized": False,
        "liveSelectorActivationAuthorized": False,
        "productionDeploymentAuthorized": False,
    }


def _fail_safe_selection(source: str, *reasons: str) -> dict[str, Any]:
    return {
        "contractVersion": CONTRACT_VERSION,
        "policyId": POLICY_ID,
        "decisionMode": "controlled_non_production",
        "decision": DECISION_REVIEW,
        "selectedArtifactId": source,
        "selectedRole": "immutable_source",
        "originalArtifactId": source,
        "originalSelectable": True,
        "reviewRequired": True,
        "reasonCodes": list(dict.fromkeys(reasons or ("invalid_or_unavailable_selector_evidence",))),
        "liveSelectorActivationAuthorized": False,
        "automaticFinalSelectionAuthorized": False,
        "teacherApprovalImplied": False,
        "omrCorrectnessImplied": False,
        "musicalTruthImplied": False,
        "productionDeploymentAuthorized": False,
    }


def select_source_variant(
    source_artifact_id: str,
    comparator_result: Mapping[str, Any],
    stage9a_evidence_by_artifact_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Convert trusted Stage 9 + Stage 9A evidence into a bounded decision."""

    source = _text(source_artifact_id)
    _require(bool(source), "source artifact id required")
    if not isinstance(comparator_result, Mapping):
        return _fail_safe_selection(source, "comparator_result_missing_or_invalid")

    if comparator_result.get("contractVersion") != STAGE9_CONTRACT_VERSION:
        return _fail_safe_selection(source, "unexpected_stage9_contract_version")
    if comparator_result.get("recommendationOnly") is not True:
        return _fail_safe_selection(source, "stage9_recommendation_only_invariant_missing")
    if comparator_result.get("automaticFinalSelectionAuthorized") is not False:
        return _fail_safe_selection(source, "stage9_scope_expansion_detected")
    if comparator_result.get("originalSelectable") is not True:
        return _fail_safe_selection(source, "original_selectability_invariant_missing")
    if _text(comparator_result.get("originalArtifactId")) != source:
        return _fail_safe_selection(source, "stage9_source_binding_mismatch")

    outcome = _text(comparator_result.get("outcome"))
    recommended = _text(comparator_result.get("recommendedArtifactId"))
    role = _text(comparator_result.get("recommendedRole"))

    if outcome in {"original_preferred", "original_retained_no_acceptable_derivative"}:
        if recommended != source or role != "immutable_source":
            return _fail_safe_selection(source, "original_recommendation_binding_mismatch")
        result = _fail_safe_selection(source, "stage9_original_recommendation")
        result["decision"] = DECISION_ORIGINAL
        result["reviewRequired"] = False
        return result

    if outcome == "review_required":
        return _fail_safe_selection(source, "stage9_review_required", "original_retained_pending_review")

    if outcome != "restoration_variant_preferred":
        return _fail_safe_selection(source, "unknown_stage9_outcome")

    variants = comparator_result.get("variants")
    if not isinstance(variants, list):
        return _fail_safe_selection(source, "stage9_variants_missing")
    matches = [item for item in variants if isinstance(item, Mapping) and _text(item.get("artifactId")) == recommended]
    if len(matches) != 1:
        return _fail_safe_selection(source, "recommended_variant_identity_not_unique")

    variant = matches[0]
    if _text(variant.get("derivedFrom")) != source:
        return _fail_safe_selection(source, "recommended_variant_source_mismatch")
    if variant.get("eligible") is not True:
        return _fail_safe_selection(source, "recommended_variant_not_eligible")
    if variant.get("hardVeto") is not False:
        return _fail_safe_selection(source, "hard_veto_cannot_be_overridden")
    if variant.get("reviewRequired") is not False:
        return _fail_safe_selection(source, "review_required_variant_cannot_be_selected")
    if _text(variant.get("safetyVerdict")).lower() != "pass":
        return _fail_safe_selection(source, "music_safety_pass_required")

    evidence_map = stage9a_evidence_by_artifact_id
    if not isinstance(evidence_map, Mapping):
        return _fail_safe_selection(source, "stage9a_preservation_evidence_missing")
    preservation = evidence_map.get(recommended)
    if not isinstance(preservation, Mapping):
        return _fail_safe_selection(source, "stage9a_preservation_evidence_missing")
    if preservation.get("contractVersion") != STAGE9A_CONTRACT_VERSION:
        return _fail_safe_selection(source, "unexpected_stage9a_contract_version")
    if _text(preservation.get("sourceArtifactId")) != source:
        return _fail_safe_selection(source, "stage9a_source_binding_mismatch")
    if _text(preservation.get("candidateArtifactId")) != recommended:
        return _fail_safe_selection(source, "stage9a_candidate_binding_mismatch")
    if _text(preservation.get("status")) != "pass":
        return _fail_safe_selection(source, "stage9a_preservation_pass_required")
    if _text(preservation.get("coverageState")) != "complete":
        return _fail_safe_selection(source, "stage9a_complete_coverage_required")
    if preservation.get("semanticHardVeto") is not False:
        return _fail_safe_selection(source, "stage9a_hard_veto_cannot_be_overridden")
    if preservation.get("reviewRequired") is not False:
        return _fail_safe_selection(source, "stage9a_review_required_cannot_be_selected")
    if preservation.get("automaticApproval") is not False:
        return _fail_safe_selection(source, "stage9a_automatic_approval_scope_expansion")

    return {
        "contractVersion": CONTRACT_VERSION,
        "policyId": POLICY_ID,
        "decisionMode": "controlled_non_production",
        "decision": DECISION_VARIANT,
        "selectedArtifactId": recommended,
        "selectedRole": "restoration_variant",
        "selectedEngineId": _text(variant.get("engineId")),
        "originalArtifactId": source,
        "originalSelectable": True,
        "reviewRequired": False,
        "reasonCodes": [
            "stage9_variant_preferred",
            "music_safety_pass",
            "stage9a_preservation_pass",
            "provenance_bound_controlled_selection",
        ],
        "selectedVariant": deepcopy(dict(variant)),
        "preservationEvidence": deepcopy(dict(preservation)),
        "liveSelectorActivationAuthorized": False,
        "automaticFinalSelectionAuthorized": False,
        "teacherApprovalImplied": False,
        "omrCorrectnessImplied": False,
        "musicalTruthImplied": False,
        "productionDeploymentAuthorized": False,
    }


def safe_select_source_variant(
    source_artifact_id: str,
    comparator_result: Mapping[str, Any],
    stage9a_evidence_by_artifact_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    source = _text(source_artifact_id) or "unknown-source"
    try:
        return select_source_variant(source, comparator_result, stage9a_evidence_by_artifact_id)
    except (SelectorContractError, AttributeError, TypeError):
        return _fail_safe_selection(source, "selector_contract_error")


def _synthetic_preservation(source: str, candidate: str) -> dict[str, Any]:
    return {
        "contractVersion": STAGE9A_CONTRACT_VERSION,
        "sourceArtifactId": source,
        "candidateArtifactId": candidate,
        "assessmentState": "assessed",
        "coverageState": "complete",
        "status": "pass",
        "semanticHardVeto": False,
        "reviewRequired": False,
        "automaticApproval": False,
    }


def run_synthetic_selector_drills() -> dict[str, Any]:
    source = "sha256:stage10-source"
    plan = plan_engine_invocations(
        source,
        [
            {"engineId": "opencv", "approvalState": "approved", "availabilityState": "available", "enabled": True},
            {"engineId": "docres", "approvalState": "unapproved", "availabilityState": "unavailable", "enabled": False},
            {"engineId": "st-image-ai", "approvalState": "unapproved", "availabilityState": "unavailable", "enabled": False},
        ],
    )

    safe_variant = {
        "artifactId": "sha256:stage10-safe",
        "role": "restoration_variant",
        "engineId": "opencv",
        "engineVersion": "synthetic-1",
        "configDigest": "sha256:stage10-config",
        "derivedFrom": source,
        "safetyVerdict": "pass",
        "hardVeto": False,
        "reviewRequired": False,
        "eligible": True,
    }
    comparator_safe = {
        "contractVersion": STAGE9_CONTRACT_VERSION,
        "outcome": "restoration_variant_preferred",
        "recommendedArtifactId": safe_variant["artifactId"],
        "recommendedRole": "restoration_variant",
        "recommendationOnly": True,
        "automaticFinalSelectionAuthorized": False,
        "originalSelectable": True,
        "originalArtifactId": source,
        "variants": [safe_variant],
    }
    evidence = {safe_variant["artifactId"]: _synthetic_preservation(source, safe_variant["artifactId"])}
    selected = select_source_variant(source, comparator_safe, evidence)
    missing_semantic = select_source_variant(source, comparator_safe, {})
    review = select_source_variant(
        source,
        {
            **comparator_safe,
            "outcome": "review_required",
            "recommendedArtifactId": source,
            "recommendedRole": "immutable_source",
        },
        evidence,
    )
    original = select_source_variant(
        source,
        {
            **comparator_safe,
            "outcome": "original_preferred",
            "recommendedArtifactId": source,
            "recommendedRole": "immutable_source",
        },
        evidence,
    )

    plan_by_engine = {item["engineId"]: item for item in plan["invocationPlan"]}
    passed = all(
        (
            plan["originalIncluded"] is True,
            plan_by_engine["opencv"]["action"] == "invoke",
            plan_by_engine["docres"]["action"] == "skip",
            plan_by_engine["st-image-ai"]["action"] == "skip",
            selected["decision"] == DECISION_VARIANT,
            selected["selectedArtifactId"] == safe_variant["artifactId"],
            selected["automaticFinalSelectionAuthorized"] is False,
            missing_semantic["decision"] == DECISION_REVIEW,
            missing_semantic["selectedArtifactId"] == source,
            review["decision"] == DECISION_REVIEW,
            review["selectedArtifactId"] == source,
            original["decision"] == DECISION_ORIGINAL,
            original["selectedArtifactId"] == source,
        )
    )
    return {
        "contractVersion": CONTRACT_VERSION,
        "result": "PASS" if passed else "BLOCKED",
        "syntheticOnly": True,
        "providerSpecificRuntimeUsed": False,
        "docresLiveRuntimeUsed": False,
        "stImageAiRuntimeUsed": False,
        "modelTrainingPerformed": False,
        "liveSelectorActivated": False,
        "productionDeploymentPerformed": False,
        "scenarios": {
            "engine_plan": plan,
            "safe_controlled_variant_selection": selected,
            "missing_stage9a_fails_safe": missing_semantic,
            "review_routes_original": review,
            "original_recommendation": original,
        },
    }


__all__ = [
    "CONTRACT_VERSION",
    "POLICY_ID",
    "SelectorContractError",
    "plan_engine_invocations",
    "select_source_variant",
    "safe_select_source_variant",
    "run_synthetic_selector_drills",
]
