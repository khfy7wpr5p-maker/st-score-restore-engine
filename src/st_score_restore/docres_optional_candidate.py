"""Stage 8 DocRes optional-candidate boundary.

This module does not import or emulate DocRes. It provides a disabled-by-default,
provider/library-neutral adapter boundary so a future separately approved runtime
can produce an auditable candidate without overwriting the immutable source.
Only injected synthetic executors are callable during Stage 8 contract drills.
Every candidate remains unusable until music-safety validation has produced an
explicit verdict; Stage 9 comparator selection is not performed here.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Callable, Mapping

CONTRACT_VERSION = "stage8.docres-optional-candidate.v1"
ENGINE_NAME = "docres"
ENGINE_ROLE = "optional_restoration_candidate"
ADAPTER_PROFILE = "disabled-by-default"

ROUTE_ORIGINAL = "original"
ROUTE_REVIEW = "review"
ROUTE_VALIDATED_HOLD = "validated_candidate_hold"


class DocResCandidateContractError(ValueError):
    """The bounded Stage 8 DocRes candidate contract was violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DocResCandidateContractError(message)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class DocResCandidatePolicy:
    """Fail-closed runtime policy for Stage 8.

    Live execution is deliberately not representable as authorized in Stage 8.
    Future runtime approval must introduce a new, separately reviewed contract.
    """

    dependency_approved: bool = False
    model_artifact_approved: bool = False
    external_package_installation_authorized: bool = False
    network_fetch_authorized: bool = False
    live_runtime_activation_authorized: bool = False
    synthetic_execution_authorized: bool = True

    def __post_init__(self) -> None:
        _require(self.dependency_approved is False, "DocRes dependency approval is outside this Stage 8 contract")
        _require(self.model_artifact_approved is False, "DocRes model approval is outside this Stage 8 contract")
        _require(
            self.external_package_installation_authorized is False,
            "external package installation is outside this Stage 8 contract",
        )
        _require(self.network_fetch_authorized is False, "network fetch is outside this Stage 8 contract")
        _require(
            self.live_runtime_activation_authorized is False,
            "live DocRes activation is outside this Stage 8 contract",
        )

    def public_contract(self) -> dict[str, Any]:
        return {
            "contractVersion": CONTRACT_VERSION,
            "engineName": ENGINE_NAME,
            "engineRole": ENGINE_ROLE,
            "adapterProfile": ADAPTER_PROFILE,
            "dependencyStatus": "UNAPPROVED",
            "modelArtifactStatus": "UNAPPROVED",
            "externalPackageInstallationAuthorized": False,
            "networkFetchAuthorized": False,
            "liveRuntimeActivationAuthorized": False,
            "syntheticExecutionAuthorized": self.synthetic_execution_authorized,
            "sourceArtifactImmutable": True,
            "sourceOverwriteForbidden": True,
            "musicSafetyValidationRequired": True,
            "stage9ComparatorSelectionAuthorized": False,
        }


def request_docres_candidate(
    source_bytes: bytes,
    *,
    policy: DocResCandidatePolicy | None = None,
    synthetic_executor: Callable[[bytes], bytes] | None = None,
    synthetic_only: bool = False,
) -> dict[str, Any]:
    """Request a candidate without permitting a real DocRes runtime.

    Normal calls fail closed to the original. A synthetic executor may be used
    only when ``synthetic_only`` is true, solely to verify provenance and
    downstream safety-handoff semantics in CI.
    """

    _require(isinstance(source_bytes, bytes) and bool(source_bytes), "non-empty immutable source bytes are required")
    policy = policy or DocResCandidatePolicy()
    source_digest = _sha256(source_bytes)

    if not synthetic_only:
        return {
            "contractVersion": CONTRACT_VERSION,
            "status": "runtime_blocked",
            "reasonCode": "docres_runtime_not_approved",
            "engine": ENGINE_NAME,
            "candidateAvailable": False,
            "sourceArtifactId": f"sha256:{source_digest}",
            "sourceReturnedUnmodified": True,
            "fallbackRoute": ROUTE_ORIGINAL,
            "musicSafetyValidationRequired": True,
            "stage9ComparatorSelectionAuthorized": False,
            "syntheticOnly": False,
        }

    _require(policy.synthetic_execution_authorized, "synthetic DocRes execution is not authorized")
    _require(synthetic_executor is not None and callable(synthetic_executor), "synthetic executor is required")
    immutable_input = bytes(source_bytes)
    candidate_bytes = synthetic_executor(immutable_input)
    _require(isinstance(candidate_bytes, bytes) and bool(candidate_bytes), "synthetic executor returned invalid bytes")
    _require(_sha256(source_bytes) == source_digest, "source bytes changed during candidate generation")

    candidate_digest = _sha256(candidate_bytes)
    return {
        "contractVersion": CONTRACT_VERSION,
        "status": "candidate_ready_for_safety_validation",
        "engine": ENGINE_NAME,
        "engineRole": ENGINE_ROLE,
        "adapterProfile": ADAPTER_PROFILE,
        "candidateAvailable": True,
        "sourceArtifactId": f"sha256:{source_digest}",
        "sourceDigest": {"algorithm": "sha256", "value": source_digest},
        "sourceReturnedUnmodified": True,
        "candidate": {
            "artifactId": f"sha256:{candidate_digest}",
            "digest": {"algorithm": "sha256", "value": candidate_digest},
            "byteSize": len(candidate_bytes),
            "role": "restoration_candidate",
            "derivedFrom": f"sha256:{source_digest}",
            "immutable": True,
            "teacherApproved": False,
        },
        "safety": {
            "musicSafetyValidationRequired": True,
            "automaticApproval": False,
            "omrCorrectnessClaimed": False,
            "musicalTruthClaimed": False,
        },
        "stage9ComparatorSelectionAuthorized": False,
        "syntheticOnly": True,
        "_syntheticCandidateBytes": candidate_bytes,
    }


def apply_music_safety_handoff(
    candidate_envelope: Mapping[str, Any],
    safety_report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Convert a music-safety verdict into a Stage 8 fail-safe handoff.

    A safety PASS only places the candidate in a validated hold for a future
    Stage 9 comparator. It never selects the candidate as final output.
    """

    _require(isinstance(candidate_envelope, Mapping), "candidate envelope must be an object")
    if not candidate_envelope.get("candidateAvailable"):
        return {
            "route": ROUTE_ORIGINAL,
            "reasonCode": "candidate_unavailable",
            "musicSafetyValidated": False,
            "stage9ComparatorEligible": False,
            "stage9ComparatorSelectionAuthorized": False,
            "automaticFinalSelectionAuthorized": False,
        }

    candidate = candidate_envelope.get("candidate") or {}
    _require(candidate.get("role") == "restoration_candidate", "candidate role drifted")
    _require(candidate.get("derivedFrom") == candidate_envelope.get("sourceArtifactId"), "candidate provenance drifted")
    _require(candidate_envelope.get("sourceReturnedUnmodified") is True, "source immutability proof missing")

    verdict = ""
    if isinstance(safety_report, Mapping):
        verdict = str(safety_report.get("verdict") or "").strip().lower()

    if verdict == "pass":
        route, reason, eligible, validated = ROUTE_VALIDATED_HOLD, "music_safety_pass", True, True
    elif verdict == "reject":
        route, reason, eligible, validated = ROUTE_ORIGINAL, "music_safety_reject", False, True
    elif verdict == "review_required":
        route, reason, eligible, validated = ROUTE_REVIEW, "music_safety_review_required", False, True
    else:
        route, reason, eligible, validated = ROUTE_REVIEW, "music_safety_unknown", False, False

    return {
        "route": route,
        "reasonCode": reason,
        "musicSafetyValidated": validated,
        "stage9ComparatorEligible": eligible,
        "stage9ComparatorSelectionAuthorized": False,
        "automaticFinalSelectionAuthorized": False,
        "originalFallbackAvailable": True,
    }


def run_synthetic_docres_candidate_drills() -> dict[str, Any]:
    """Exercise the Stage 8 gate, provenance, and safety handoff synthetically."""

    source = b"stage8-synthetic-source"
    executor_calls = {"count": 0}

    def executor(value: bytes) -> bytes:
        executor_calls["count"] += 1
        return value + b"-candidate"

    live_gate = request_docres_candidate(source, synthetic_executor=executor)
    gate_did_not_execute = executor_calls["count"] == 0
    synthetic = request_docres_candidate(source, synthetic_executor=executor, synthetic_only=True)
    pass_handoff = apply_music_safety_handoff(synthetic, {"verdict": "pass"})
    review_handoff = apply_music_safety_handoff(synthetic, {"verdict": "review_required"})
    reject_handoff = apply_music_safety_handoff(synthetic, {"verdict": "reject"})
    unknown_handoff = apply_music_safety_handoff(synthetic, None)

    passed = all(
        (
            live_gate.get("fallbackRoute") == ROUTE_ORIGINAL,
            live_gate.get("candidateAvailable") is False,
            gate_did_not_execute,
            synthetic.get("status") == "candidate_ready_for_safety_validation",
            synthetic.get("sourceReturnedUnmodified") is True,
            pass_handoff.get("route") == ROUTE_VALIDATED_HOLD,
            pass_handoff.get("stage9ComparatorEligible") is True,
            pass_handoff.get("stage9ComparatorSelectionAuthorized") is False,
            review_handoff.get("route") == ROUTE_REVIEW,
            reject_handoff.get("route") == ROUTE_ORIGINAL,
            unknown_handoff.get("route") == ROUTE_REVIEW,
        )
    )
    return {
        "contractVersion": CONTRACT_VERSION,
        "result": "PASS" if passed else "BLOCKED",
        "syntheticOnly": True,
        "docresRuntimeDependencyApproved": False,
        "liveDocresRuntimeActivated": False,
        "externalPackageInstalled": False,
        "modelArtifactDownloaded": False,
        "networkFetchPerformed": False,
        "stage9ComparatorSelectionPerformed": False,
        "scenarios": {
            "live_runtime_gate": {key: value for key, value in live_gate.items() if not key.startswith("_")},
            "safety_pass": pass_handoff,
            "safety_review": review_handoff,
            "safety_reject": reject_handoff,
            "safety_unknown": unknown_handoff,
        },
    }


__all__ = [
    "CONTRACT_VERSION",
    "DocResCandidateContractError",
    "DocResCandidatePolicy",
    "apply_music_safety_handoff",
    "request_docres_candidate",
    "run_synthetic_docres_candidate_drills",
]
