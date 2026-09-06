"""Provider-neutral Stage 7 preview release contracts and fail-safe routing.

The module is intentionally deployment-agnostic. It exposes reversible release
policy, user-facing safety/status projection, privacy-safe observability shaping,
and synthetic drill primitives without authorizing a real preview cohort or any
production state mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Iterable, Mapping

PREVIEW_CONTRACT_VERSION = "stage7.preview-contract.v1"
PREVIEW_CHANNEL = "preview"
PREVIEW_PROFILE = "provider-neutral"

SAFETY_ORIGINAL = "ORIGINAL"
SAFETY_RESTORED = "RESTORED"
SAFETY_REVIEW_REQUIRED = "REVIEW_REQUIRED"
SAFETY_UNCERTAIN = "UNCERTAIN"
SAFETY_FAILED_SAFE = "FAILED_SAFE"

ROUTE_ORIGINAL = "original"
ROUTE_CANDIDATE = "restored_candidate"
ROUTE_REVIEW = "review"

_ALLOWED_ROUTE_REASONS = {
    "preview_activation_not_authorized",
    "kill_switch_engaged",
    "candidate_hard_rejected",
    "candidate_uncertain",
    "candidate_review_required",
    "candidate_eligible",
    "no_candidate_available",
}
_ALLOWED_EVENT_TYPES = {
    "preview_route_decision",
    "preview_status_projection",
    "preview_rollback",
    "preview_kill_switch",
}
_ALLOWED_LATENCY_BUCKETS = {"lt_100ms", "100_500ms", "500ms_2s", "2s_10s", "gte_10s", "not_measured"}


class PreviewReleaseContractError(ValueError):
    """Preview release policy or telemetry violated its bounded contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PreviewReleaseContractError(message)


def _opaque_ref(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


@dataclass(frozen=True)
class PreviewReleasePolicy:
    """Immutable release gate configuration for one provider-neutral process."""

    activation_authorized: bool = False
    kill_switch_engaged: bool = False
    provider_selected: bool = False
    live_resources_created: bool = False
    production_deployment_authorized: bool = False

    def __post_init__(self) -> None:
        if self.activation_authorized:
            _require(self.provider_selected is False, "provider selection is outside the Stage 7 provider-neutral contract")
            _require(self.live_resources_created is False, "live resources are outside the Stage 7 provider-neutral contract")
            _require(self.production_deployment_authorized is False, "production deployment is outside the Stage 7 provider-neutral contract")

    def public_contract(self) -> dict[str, Any]:
        return {
            "contractVersion": PREVIEW_CONTRACT_VERSION,
            "channel": PREVIEW_CHANNEL,
            "profile": PREVIEW_PROFILE,
            "activationAuthorized": self.activation_authorized,
            "killSwitchEngaged": self.kill_switch_engaged,
            "providerSelected": self.provider_selected,
            "liveResourcesCreated": self.live_resources_created,
            "productionDeploymentAuthorized": self.production_deployment_authorized,
            "rollbackTarget": ROUTE_ORIGINAL,
            "omrCorrectnessClaimed": False,
            "musicalTruthClaimed": False,
            "productionSecurityCertified": False,
        }


def choose_preview_route(
    *,
    policy: PreviewReleasePolicy,
    candidate_available: bool,
    safety_verdict: str | None,
) -> dict[str, str]:
    """Choose a reversible route without allowing soft quality to bypass safety."""

    normalized = (safety_verdict or "").strip().lower()
    if policy.kill_switch_engaged:
        route, reason = ROUTE_ORIGINAL, "kill_switch_engaged"
    elif not policy.activation_authorized:
        route, reason = ROUTE_ORIGINAL, "preview_activation_not_authorized"
    elif not candidate_available:
        route, reason = ROUTE_ORIGINAL, "no_candidate_available"
    elif normalized == "reject":
        route, reason = ROUTE_ORIGINAL, "candidate_hard_rejected"
    elif normalized == "review_required":
        route, reason = ROUTE_REVIEW, "candidate_review_required"
    elif normalized == "pass":
        route, reason = ROUTE_CANDIDATE, "candidate_eligible"
    else:
        route, reason = ROUTE_REVIEW, "candidate_uncertain"
    return {"route": route, "reasonCode": reason}


def _page_status(page: Mapping[str, Any]) -> str:
    source_id = page.get("sourceArtifactId")
    candidate_id = page.get("currentCandidateArtifactId")
    selected_id = page.get("selectedArtifactId")
    review = page.get("reviewDecision") or {}
    safety = page.get("safetyReport") or {}
    verdict = str(safety.get("verdict") or "").lower()
    action = str(review.get("action") or "").lower()

    if selected_id and source_id and selected_id == source_id:
        return SAFETY_ORIGINAL
    if selected_id and candidate_id and selected_id == candidate_id and action == "approve" and verdict != "reject":
        return SAFETY_RESTORED
    if verdict == "reject":
        return SAFETY_FAILED_SAFE
    if verdict == "review_required" or candidate_id:
        return SAFETY_REVIEW_REQUIRED
    return SAFETY_UNCERTAIN


def build_preview_status(
    job_snapshot: Mapping[str, Any],
    *,
    policy: PreviewReleasePolicy | None = None,
) -> dict[str, Any]:
    """Project job state into a bounded, user-facing preview safety contract."""

    policy = policy or PreviewReleasePolicy()
    pages_raw = job_snapshot.get("pages") or []
    pages: Iterable[Mapping[str, Any]] = [item for item in pages_raw if isinstance(item, Mapping)]
    page_states = [_page_status(page) for page in pages]

    if not page_states:
        aggregate = SAFETY_UNCERTAIN
    elif SAFETY_FAILED_SAFE in page_states:
        aggregate = SAFETY_FAILED_SAFE
    elif SAFETY_REVIEW_REQUIRED in page_states or SAFETY_UNCERTAIN in page_states:
        aggregate = SAFETY_REVIEW_REQUIRED
    elif SAFETY_ORIGINAL in page_states and SAFETY_RESTORED not in page_states:
        aggregate = SAFETY_ORIGINAL
    elif SAFETY_RESTORED in page_states:
        aggregate = SAFETY_RESTORED
    else:
        aggregate = SAFETY_UNCERTAIN

    return {
        "contractVersion": PREVIEW_CONTRACT_VERSION,
        "channel": PREVIEW_CHANNEL,
        "profile": PREVIEW_PROFILE,
        "activationAuthorized": policy.activation_authorized,
        "killSwitchEngaged": policy.kill_switch_engaged,
        "safetyStatus": aggregate,
        "pageSafetyStatus": page_states,
        "originalFallbackAvailable": True,
        "provenanceRequired": True,
        "omrCorrectnessClaimed": False,
        "musicalTruthClaimed": False,
        "productionSecurityCertified": False,
        "messageCode": {
            SAFETY_ORIGINAL: "original_selected_or_fallback",
            SAFETY_RESTORED: "restored_output_selected_with_review_boundary",
            SAFETY_REVIEW_REQUIRED: "review_required_before_trusting_restored_output",
            SAFETY_UNCERTAIN: "status_uncertain_use_original_or_review",
            SAFETY_FAILED_SAFE: "restored_candidate_rejected_original_fallback",
        }[aggregate],
    }


def build_privacy_safe_event(
    *,
    event_type: str,
    job_id: str,
    route: str,
    reason_code: str,
    latency_bucket: str = "not_measured",
    failure_class: str | None = None,
) -> dict[str, Any]:
    """Build observability evidence without artifact content, identity, or free text."""

    _require(event_type in _ALLOWED_EVENT_TYPES, "unsupported preview event type")
    _require(route in {ROUTE_ORIGINAL, ROUTE_CANDIDATE, ROUTE_REVIEW}, "unsupported preview route")
    _require(reason_code in _ALLOWED_ROUTE_REASONS, "unsupported preview reason code")
    _require(latency_bucket in _ALLOWED_LATENCY_BUCKETS, "unsupported latency bucket")
    if failure_class is not None:
        _require(failure_class in {"none", "validation", "runtime", "storage", "timeout", "unknown"}, "unsupported failure class")
    return {
        "contractVersion": PREVIEW_CONTRACT_VERSION,
        "eventType": event_type,
        "jobRef": _opaque_ref(job_id),
        "route": route,
        "reasonCode": reason_code,
        "latencyBucket": latency_bucket,
        "failureClass": failure_class or "none",
        "containsArtifactBytes": False,
        "containsRawPrivateMetrics": False,
        "containsSecrets": False,
        "containsFreeText": False,
    }


def run_synthetic_preview_drills() -> dict[str, Any]:
    """Exercise release, rollback, degraded-mode, and fallback semantics synthetically."""

    inactive = PreviewReleasePolicy()
    active_synthetic = PreviewReleasePolicy(activation_authorized=True)
    killed_synthetic = PreviewReleasePolicy(activation_authorized=True, kill_switch_engaged=True)
    scenarios = {
        "activation_gate": choose_preview_route(policy=inactive, candidate_available=True, safety_verdict="pass"),
        "eligible_candidate": choose_preview_route(policy=active_synthetic, candidate_available=True, safety_verdict="pass"),
        "hard_reject": choose_preview_route(policy=active_synthetic, candidate_available=True, safety_verdict="reject"),
        "review_required": choose_preview_route(policy=active_synthetic, candidate_available=True, safety_verdict="review_required"),
        "missing_candidate": choose_preview_route(policy=active_synthetic, candidate_available=False, safety_verdict=None),
        "kill_switch": choose_preview_route(policy=killed_synthetic, candidate_available=True, safety_verdict="pass"),
    }
    expected = {
        "activation_gate": {"route": ROUTE_ORIGINAL, "reasonCode": "preview_activation_not_authorized"},
        "eligible_candidate": {"route": ROUTE_CANDIDATE, "reasonCode": "candidate_eligible"},
        "hard_reject": {"route": ROUTE_ORIGINAL, "reasonCode": "candidate_hard_rejected"},
        "review_required": {"route": ROUTE_REVIEW, "reasonCode": "candidate_review_required"},
        "missing_candidate": {"route": ROUTE_ORIGINAL, "reasonCode": "no_candidate_available"},
        "kill_switch": {"route": ROUTE_ORIGINAL, "reasonCode": "kill_switch_engaged"},
    }
    passed = scenarios == expected
    return {
        "contractVersion": PREVIEW_CONTRACT_VERSION,
        "result": "PASS" if passed else "BLOCKED",
        "syntheticOnly": True,
        "previewReleaseActivated": False,
        "productionDeploymentPerformed": False,
        "scenarios": scenarios,
    }


__all__ = [
    "PREVIEW_CONTRACT_VERSION",
    "PreviewReleaseContractError",
    "PreviewReleasePolicy",
    "build_preview_status",
    "build_privacy_safe_event",
    "choose_preview_route",
    "run_synthetic_preview_drills",
]
