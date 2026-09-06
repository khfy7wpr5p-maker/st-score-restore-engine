"""Stage 9A provider-neutral Music-Symbol Preservation capability.

This module does not perform model training or claim authoritative OMR truth. It
validates provenance-bound semantic preservation evidence, converts uncertainty
into safe routing, and hands bounded evidence to the Stage 9 comparator without
allowing semantic quality claims to override hard safety.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .multi_engine_comparator import compare_restoration_variants

CONTRACT_VERSION = "stage9a.mspm-evidence.v1"
POLICY_ID = "stage9a.semantic-preservation-routing.v1"
TAXONOMY_VERSION = "stage9a.music-symbol-taxonomy.v1"
COMPARATOR_HANDOFF_VERSION = "stage9a.comparator-handoff.v1"

ASSESSMENT_STATES = frozenset({"assessed", "not_assessed", "unavailable"})
COVERAGE_STATES = frozenset({"complete", "partial", "unknown"})
DISPOSITIONS = frozenset({"hard_veto", "review", "observe"})
MATERIALITIES = frozenset({"material", "uncertain", "minor"})

INITIAL_SYMBOL_CLASSES = (
    "staff_line",
    "tab_line",
    "notehead",
    "stem",
    "flag",
    "beam",
    "augmentation_dot",
    "rest",
    "accidental",
    "clef",
    "key_signature",
    "time_signature",
    "barline",
    "repeat",
    "tie",
    "slur",
    "tab_digit",
    "tab_string_position_relationship",
    "guitar_articulation",
)

RISK_CODES = (
    "symbol_missing_after_restoration",
    "symbol_invented_after_restoration",
    "symbol_displaced",
    "symbol_merged_or_split",
    "staff_or_tab_relationship_changed",
    "thin_symbol_at_risk",
    "semantic_comparison_uncertain",
)

MATERIAL_HARM_RISKS = frozenset(
    {
        "symbol_missing_after_restoration",
        "symbol_invented_after_restoration",
        "symbol_displaced",
        "symbol_merged_or_split",
        "staff_or_tab_relationship_changed",
    }
)


class PreservationContractError(ValueError):
    """Raised when preservation evidence violates the Stage 9A contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PreservationContractError(message)


def _text(mapping: Mapping[str, Any], key: str) -> str:
    value = str(mapping.get(key) or "").strip()
    _require(bool(value), f"{key} is required")
    return value


def _component_identity(evidence: Mapping[str, Any]) -> dict[str, str]:
    component = evidence.get("component")
    _require(isinstance(component, Mapping), "component identity is required")
    component_id = _text(component, "id")
    version = _text(component, "version")
    artifact_digest = _text(component, "artifactDigest")
    mode = _text(component, "mode")
    _require(
        mode in {"synthetic", "deterministic", "learned", "omr_auxiliary", "hybrid"},
        "unsupported component mode",
    )
    return {
        "id": component_id,
        "version": version,
        "artifactDigest": artifact_digest,
        "mode": mode,
    }


def _public_finding(finding: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "evidenceId": str(finding.get("evidenceId") or "").strip(),
        "symbolClass": str(finding.get("symbolClass") or "").strip(),
        "riskCode": str(finding.get("riskCode") or "").strip(),
        "disposition": str(finding.get("disposition") or "").strip(),
        "materiality": str(finding.get("materiality") or "").strip(),
        "confidenceLabel": str(finding.get("confidenceLabel") or "").strip() or None,
        "localizationRef": str(finding.get("localizationRef") or "").strip() or None,
    }


def assess_preservation_evidence(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one source-versus-candidate preservation evidence record."""

    _require(isinstance(evidence, Mapping), "preservation evidence must be an object")
    _require(evidence.get("contractVersion") == CONTRACT_VERSION, "unexpected preservation contract version")

    source_id = _text(evidence, "sourceArtifactId")
    candidate_id = _text(evidence, "candidateArtifactId")
    _require(source_id != candidate_id, "candidate must be distinct from immutable source")

    taxonomy_version = _text(evidence, "taxonomyVersion")
    component = _component_identity(evidence)
    state = _text(evidence, "assessmentState")
    coverage = _text(evidence, "coverageState")
    _require(state in ASSESSMENT_STATES, "unsupported assessment state")
    _require(coverage in COVERAGE_STATES, "unsupported coverage state")

    findings_value = evidence.get("findings", [])
    _require(isinstance(findings_value, list), "findings must be an array")
    findings: list[dict[str, Any]] = []
    hard_veto = False
    review_required = False
    reasons: list[str] = []

    if taxonomy_version != TAXONOMY_VERSION:
        review_required = True
        reasons.append("taxonomy_version_not_accepted_by_current_policy")

    if state != "assessed":
        review_required = True
        reasons.append("semantic_evidence_not_assessed" if state == "not_assessed" else "semantic_component_unavailable")

    if coverage != "complete":
        review_required = True
        reasons.append("semantic_coverage_incomplete")

    for raw in findings_value:
        _require(isinstance(raw, Mapping), "each finding must be an object")
        finding = _public_finding(raw)
        _require(bool(finding["evidenceId"]), "finding evidenceId is required")
        _require(bool(finding["symbolClass"]), "finding symbolClass is required")
        _require(bool(finding["riskCode"]), "finding riskCode is required")
        _require(finding["disposition"] in DISPOSITIONS, "unsupported finding disposition")
        _require(finding["materiality"] in MATERIALITIES, "unsupported finding materiality")
        findings.append(finding)

        risk = finding["riskCode"]
        disposition = finding["disposition"]
        materiality = finding["materiality"]

        if risk not in RISK_CODES:
            review_required = True
            reasons.append("extensible_risk_requires_policy_review")

        if disposition == "hard_veto":
            if risk in MATERIAL_HARM_RISKS and materiality == "material":
                hard_veto = True
                reasons.append(risk)
            else:
                review_required = True
                reasons.append("unsupported_hard_veto_request")
        elif disposition == "review":
            review_required = True
            reasons.append(risk if risk in RISK_CODES else "semantic_comparison_uncertain")
        elif materiality == "uncertain":
            review_required = True
            reasons.append("semantic_comparison_uncertain")

    if hard_veto:
        status = "hard_veto"
        review_required = False
        recommended_route = "return_original_or_alternate_safe_path"
        reasons.insert(0, "material_semantic_preservation_harm")
    elif review_required:
        status = "review_required" if state == "assessed" else "not_assessed"
        recommended_route = "return_original_or_review"
    else:
        status = "pass"
        recommended_route = "eligible_for_stage9_comparator"
        reasons.append("no_material_semantic_preservation_harm_found")

    return {
        "contractVersion": CONTRACT_VERSION,
        "policyId": POLICY_ID,
        "taxonomyVersion": taxonomy_version,
        "sourceArtifactId": source_id,
        "candidateArtifactId": candidate_id,
        "component": component,
        "assessmentState": state,
        "coverageState": coverage,
        "status": status,
        "semanticHardVeto": hard_veto,
        "reviewRequired": review_required,
        "automaticApproval": False,
        "automaticFinalSelectionAuthorized": False,
        "omrCorrectnessImplied": False,
        "musicalTruthImplied": False,
        "modelTrainingImplied": False,
        "originalFallbackRequired": True,
        "recommendedRoute": recommended_route,
        "reasonCodes": list(dict.fromkeys(reasons)),
        "findings": findings,
    }


def fail_safe_preservation_assessment(
    source_artifact_id: str,
    candidate_artifact_id: str,
    *,
    code: str = "invalid_or_unavailable_semantic_evidence",
) -> dict[str, Any]:
    _require(bool(str(source_artifact_id).strip()), "source artifact id required")
    _require(bool(str(candidate_artifact_id).strip()), "candidate artifact id required")
    return {
        "contractVersion": CONTRACT_VERSION,
        "policyId": POLICY_ID,
        "taxonomyVersion": TAXONOMY_VERSION,
        "sourceArtifactId": str(source_artifact_id).strip(),
        "candidateArtifactId": str(candidate_artifact_id).strip(),
        "component": {
            "id": "unavailable",
            "version": "unavailable",
            "artifactDigest": "unavailable",
            "mode": "synthetic",
        },
        "assessmentState": "unavailable",
        "coverageState": "unknown",
        "status": "not_assessed",
        "semanticHardVeto": False,
        "reviewRequired": True,
        "automaticApproval": False,
        "automaticFinalSelectionAuthorized": False,
        "omrCorrectnessImplied": False,
        "musicalTruthImplied": False,
        "modelTrainingImplied": False,
        "originalFallbackRequired": True,
        "recommendedRoute": "return_original_or_review",
        "reasonCodes": [code],
        "findings": [],
    }


def safe_assess_preservation_evidence(
    evidence: Mapping[str, Any],
    *,
    expected_source_artifact_id: str | None = None,
    expected_candidate_artifact_id: str | None = None,
) -> dict[str, Any]:
    evidence_mapping = evidence if isinstance(evidence, Mapping) else {}
    source = str(expected_source_artifact_id or evidence_mapping.get("sourceArtifactId") or "").strip()
    candidate = str(expected_candidate_artifact_id or evidence_mapping.get("candidateArtifactId") or "").strip()
    try:
        result = assess_preservation_evidence(evidence_mapping)
        if expected_source_artifact_id is not None:
            _require(result["sourceArtifactId"] == expected_source_artifact_id, "source evidence binding mismatch")
        if expected_candidate_artifact_id is not None:
            _require(result["candidateArtifactId"] == expected_candidate_artifact_id, "candidate evidence binding mismatch")
        return result
    except (PreservationContractError, AttributeError, TypeError):
        return fail_safe_preservation_assessment(source or "unknown-source", candidate or "unknown-candidate")


def apply_preservation_to_variant(
    variant: Mapping[str, Any],
    assessment: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach Stage 9A evidence to a Stage 9 comparator candidate."""

    _require(isinstance(variant, Mapping), "variant must be an object")
    _require(isinstance(assessment, Mapping), "assessment must be an object")
    variant_copy = deepcopy(dict(variant))
    artifact_id = str(variant_copy.get("artifactId") or "").strip()
    derived_from = str(variant_copy.get("derivedFrom") or "").strip()
    _require(bool(artifact_id) and bool(derived_from), "variant provenance required")

    candidate_id = str(assessment.get("candidateArtifactId") or "").strip()
    source_id = str(assessment.get("sourceArtifactId") or "").strip()
    _require(candidate_id == artifact_id, "Stage 9A candidate binding mismatch")
    _require(source_id == derived_from, "Stage 9A source binding mismatch")

    status = str(assessment.get("status") or "").strip()
    semantic_hard_veto = bool(assessment.get("semanticHardVeto"))
    review_required = bool(assessment.get("reviewRequired"))

    variant_copy["stage9aPreservation"] = {
        "handoffVersion": COMPARATOR_HANDOFF_VERSION,
        "status": status,
        "policyId": assessment.get("policyId"),
        "taxonomyVersion": assessment.get("taxonomyVersion"),
        "component": deepcopy(assessment.get("component")),
        "reasonCodes": list(assessment.get("reasonCodes") or []),
        "findings": deepcopy(assessment.get("findings") or []),
        "automaticApproval": False,
        "omrCorrectnessImplied": False,
        "musicalTruthImplied": False,
    }
    variant_copy["semanticHardVeto"] = bool(variant_copy.get("semanticHardVeto")) or semantic_hard_veto

    if review_required and not variant_copy["semanticHardVeto"]:
        previous = str(variant_copy.get("safetyVerdict") or "unknown").strip().lower()
        variant_copy["preStage9aSafetyVerdict"] = previous
        if previous == "pass":
            variant_copy["safetyVerdict"] = "review_required"

    return variant_copy


def _synthetic_evidence(source: str, candidate: str, findings: list[dict[str, Any]], *, coverage: str = "complete") -> dict[str, Any]:
    return {
        "contractVersion": CONTRACT_VERSION,
        "taxonomyVersion": TAXONOMY_VERSION,
        "sourceArtifactId": source,
        "candidateArtifactId": candidate,
        "component": {
            "id": "stage9a.synthetic-evidence-producer",
            "version": "1",
            "artifactDigest": "sha256:synthetic-component",
            "mode": "synthetic",
        },
        "assessmentState": "assessed",
        "coverageState": coverage,
        "findings": findings,
    }


def run_synthetic_mspm_drills() -> dict[str, Any]:
    source = "sha256:stage9a-source"

    def base_variant(candidate: str) -> dict[str, Any]:
        return {
            "artifactId": candidate,
            "engineId": "opencv",
            "engineVersion": "synthetic-1",
            "configDigest": "sha256:stage9a-config",
            "derivedFrom": source,
            "safetyVerdict": "pass",
            "qualityEvidence": {
                "documentQualityDelta": 2,
                "legibilityDelta": 1,
                "contrastDelta": 1,
                "noiseReductionEvidence": 1,
            },
            "structuralRisk": 0,
        }

    missing_candidate = "sha256:missing-accidental"
    missing = assess_preservation_evidence(
        _synthetic_evidence(
            source,
            missing_candidate,
            [{
                "evidenceId": "finding-1",
                "symbolClass": "accidental",
                "riskCode": "symbol_missing_after_restoration",
                "disposition": "hard_veto",
                "materiality": "material",
                "confidenceLabel": "high",
            }],
        )
    )
    missing_cmp = compare_restoration_variants(
        source,
        [apply_preservation_to_variant(base_variant(missing_candidate), missing)],
    )

    uncertain_candidate = "sha256:uncertain-tab"
    uncertain = assess_preservation_evidence(
        _synthetic_evidence(
            source,
            uncertain_candidate,
            [{
                "evidenceId": "finding-2",
                "symbolClass": "tab_digit",
                "riskCode": "semantic_comparison_uncertain",
                "disposition": "review",
                "materiality": "uncertain",
            }],
        )
    )
    uncertain_cmp = compare_restoration_variants(
        source,
        [apply_preservation_to_variant(base_variant(uncertain_candidate), uncertain)],
    )

    safe_candidate = "sha256:safe"
    safe = assess_preservation_evidence(_synthetic_evidence(source, safe_candidate, []))
    safe_cmp = compare_restoration_variants(
        source,
        [apply_preservation_to_variant(base_variant(safe_candidate), safe)],
    )

    mismatch_candidate = "sha256:mismatch"
    mismatch_raw = _synthetic_evidence(source, "sha256:other-candidate", [])
    mismatch = safe_assess_preservation_evidence(
        mismatch_raw,
        expected_source_artifact_id=source,
        expected_candidate_artifact_id=mismatch_candidate,
    )
    mismatch_cmp = compare_restoration_variants(
        source,
        [apply_preservation_to_variant(base_variant(mismatch_candidate), mismatch)],
    )

    passed = all((
        missing["semanticHardVeto"] is True,
        missing_cmp["recommendedArtifactId"] == source,
        uncertain["reviewRequired"] is True,
        uncertain_cmp["outcome"] == "review_required",
        uncertain_cmp["recommendedArtifactId"] == source,
        safe["status"] == "pass",
        safe_cmp["recommendedArtifactId"] == safe_candidate,
        safe_cmp["automaticFinalSelectionAuthorized"] is False,
        mismatch["reviewRequired"] is True,
        mismatch_cmp["recommendedArtifactId"] == source,
    ))

    return {
        "contractVersion": CONTRACT_VERSION,
        "policyId": POLICY_ID,
        "result": "PASS" if passed else "BLOCKED",
        "syntheticOnly": True,
        "realUserDataUsed": False,
        "modelTrainingPerformed": False,
        "modelWeightsLoaded": False,
        "networkFetchPerformed": False,
        "productionInferencePerformed": False,
        "stage10Activated": False,
        "automaticFinalSelectionPerformed": False,
        "scenarios": {
            "material_symbol_loss_hard_veto": {"assessment": missing, "comparator": missing_cmp},
            "uncertain_tab_digit_routes_review": {"assessment": uncertain, "comparator": uncertain_cmp},
            "complete_safe_evidence_reaches_comparator": {"assessment": safe, "comparator": safe_cmp},
            "provenance_mismatch_fails_safe": {"assessment": mismatch, "comparator": mismatch_cmp},
        },
    }


__all__ = [
    "CONTRACT_VERSION",
    "POLICY_ID",
    "TAXONOMY_VERSION",
    "COMPARATOR_HANDOFF_VERSION",
    "INITIAL_SYMBOL_CLASSES",
    "RISK_CODES",
    "PreservationContractError",
    "assess_preservation_evidence",
    "safe_assess_preservation_evidence",
    "apply_preservation_to_variant",
    "run_synthetic_mspm_drills",
]
