"""Provider-neutral production identity and authorization primitives for Stage 6.

This module deliberately does not select or activate an identity provider. A
provider-specific cryptographic signature verifier must be injected at runtime.
The adapter then validates the signed evidence and derives privacy-safe opaque
principal identifiers used by the API and audit boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import math
from typing import Any, Callable, Mapping, Protocol

from .job_api_types import JobApiError


@dataclass(frozen=True)
class VerifiedTokenEvidence:
    """Claims returned only after cryptographic signature verification."""

    claims: Mapping[str, Any]
    key_id: str
    algorithm: str
    signature_validated: bool


class SignatureVerificationBackend(Protocol):
    """Provider-specific boundary that verifies token signatures and keys."""

    def verify(self, token: str) -> VerifiedTokenEvidence:
        ...


class RevocationChecker(Protocol):
    """Returns True only when the verified token identifier is revoked."""

    def __call__(self, issuer: str, token_id: str) -> bool:
        ...


@dataclass(frozen=True)
class ProductionIdentityPolicy:
    trusted_issuers: tuple[str, ...]
    trusted_audiences: tuple[str, ...]
    role_claim: str = "roles"
    tenant_claim: str = "tenant_id"
    allowed_user_roles: tuple[str, ...] = ("client", "reviewer")
    clock_skew_seconds: int = 60

    def __post_init__(self) -> None:
        if not self.trusted_issuers or any(not value.strip() for value in self.trusted_issuers):
            raise JobApiError(
                "invalid_identity_policy",
                "Production identity requires at least one non-empty trusted issuer.",
                http_status=500,
            )
        if not self.trusted_audiences or any(not value.strip() for value in self.trusted_audiences):
            raise JobApiError(
                "invalid_identity_policy",
                "Production identity requires at least one non-empty trusted audience.",
                http_status=500,
            )
        if len(set(self.allowed_user_roles)) != len(self.allowed_user_roles) or not self.allowed_user_roles:
            raise JobApiError(
                "invalid_identity_policy",
                "Production identity roles must be non-empty and unique.",
                http_status=500,
            )
        if not 0 <= int(self.clock_skew_seconds) <= 300:
            raise JobApiError(
                "invalid_identity_policy",
                "clock_skew_seconds must be between 0 and 300.",
                http_status=500,
            )
        if not self.role_claim.strip() or not self.tenant_claim.strip():
            raise JobApiError(
                "invalid_identity_policy",
                "Identity claim names must be non-empty.",
                http_status=500,
            )


@dataclass(frozen=True)
class AuthenticatedIdentity:
    role: str
    actor_id: str
    subject_key: str | None
    tenant_key: str | None
    production: bool

    @classmethod
    def development(cls, role: str, actor_id: str) -> "AuthenticatedIdentity":
        return cls(
            role=role,
            actor_id=actor_id,
            subject_key=None,
            tenant_key=None,
            production=False,
        )


class ProductionIdentityAdapter:
    """Fail-closed verifier for provider-neutral signed identity evidence."""

    def __init__(
        self,
        policy: ProductionIdentityPolicy,
        signature_backend: SignatureVerificationBackend,
        revocation_checker: RevocationChecker,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if signature_backend is None or revocation_checker is None:
            raise JobApiError(
                "invalid_identity_configuration",
                "Production identity requires signature verification and revocation checking.",
                http_status=500,
            )
        self.policy = policy
        self.signature_backend = signature_backend
        self.revocation_checker = revocation_checker
        self._clock = clock or (lambda: datetime.now(UTC))

    def authenticate_bearer_token(self, token: str) -> AuthenticatedIdentity:
        if not isinstance(token, str) or not token or len(token) > 16_384 or any(character.isspace() for character in token):
            raise JobApiError(
                "invalid_bearer_token",
                "The production bearer token is malformed.",
                http_status=401,
            )
        try:
            evidence = self.signature_backend.verify(token)
        except JobApiError:
            raise
        except Exception as error:
            raise JobApiError(
                "identity_verification_failed",
                "Signed identity verification failed.",
                http_status=401,
            ) from error
        if not isinstance(evidence, VerifiedTokenEvidence):
            raise JobApiError(
                "invalid_verified_identity_evidence",
                "The signature verifier returned an invalid evidence contract.",
                http_status=500,
            )
        if evidence.signature_validated is not True:
            raise JobApiError(
                "identity_signature_not_validated",
                "Production identity requires a validated cryptographic signature.",
                http_status=401,
            )
        if not isinstance(evidence.key_id, str) or not evidence.key_id.strip():
            raise JobApiError(
                "identity_key_id_missing",
                "Production identity requires a verified key identifier.",
                http_status=401,
            )
        algorithm = str(evidence.algorithm or "").strip()
        if not algorithm or algorithm.lower() == "none":
            raise JobApiError(
                "identity_algorithm_forbidden",
                "Unsigned identity algorithms are forbidden.",
                http_status=401,
            )
        if not isinstance(evidence.claims, Mapping):
            raise JobApiError(
                "invalid_identity_claims",
                "Verified identity claims must be an object.",
                http_status=401,
            )
        claims = evidence.claims
        issuer = self._required_text(claims, "iss")
        if issuer not in self.policy.trusted_issuers:
            raise JobApiError(
                "identity_issuer_not_trusted",
                "The identity issuer is not trusted.",
                http_status=401,
            )
        audiences = self._audiences(claims.get("aud"))
        if not set(audiences).intersection(self.policy.trusted_audiences):
            raise JobApiError(
                "identity_audience_mismatch",
                "The identity token is not intended for this service.",
                http_status=401,
            )

        now = self._now_timestamp()
        skew = float(self.policy.clock_skew_seconds)
        expires_at = self._required_numeric_date(claims, "exp")
        not_before = self._required_numeric_date(claims, "nbf")
        if expires_at <= now - skew:
            raise JobApiError(
                "identity_token_expired",
                "The identity token has expired.",
                http_status=401,
            )
        if not_before > now + skew:
            raise JobApiError(
                "identity_token_not_yet_valid",
                "The identity token is not yet valid.",
                http_status=401,
            )

        subject = self._required_text(claims, "sub")
        tenant = self._required_text(claims, self.policy.tenant_claim)
        token_id = self._required_text(claims, "jti")
        try:
            revoked = self.revocation_checker(issuer, token_id)
        except Exception as error:
            raise JobApiError(
                "identity_revocation_check_unavailable",
                "Identity revocation status could not be verified.",
                http_status=503,
            ) from error
        if revoked is not False:
            raise JobApiError(
                "identity_token_revoked",
                "The identity token has been revoked.",
                http_status=401,
            )

        roles = self._role_values(claims.get(self.policy.role_claim))
        permitted = sorted(set(roles).intersection(self.policy.allowed_user_roles))
        if not permitted:
            raise JobApiError(
                "identity_role_not_permitted",
                "The authenticated identity has no permitted application role.",
                http_status=403,
            )
        if len(permitted) != 1:
            raise JobApiError(
                "identity_role_conflict",
                "Conflicting production application roles are denied.",
                http_status=403,
            )

        subject_key = self._opaque_key("subject", issuer, subject)
        tenant_key = self._opaque_key("tenant", issuer, tenant)
        return AuthenticatedIdentity(
            role=permitted[0],
            actor_id=subject_key,
            subject_key=subject_key,
            tenant_key=tenant_key,
            production=True,
        )

    def _now_timestamp(self) -> float:
        value = self._clock()
        if not isinstance(value, datetime):
            raise JobApiError(
                "invalid_identity_clock",
                "Identity clock must return a datetime.",
                http_status=500,
            )
        normalized = value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
        return normalized.timestamp()

    @staticmethod
    def _required_text(claims: Mapping[str, Any], name: str) -> str:
        value = claims.get(name)
        if not isinstance(value, str) or not value.strip() or len(value) > 1024:
            raise JobApiError(
                "identity_required_claim_missing",
                "A required identity claim is missing or invalid.",
                http_status=401,
                details={"claim": name},
            )
        return value

    @staticmethod
    def _required_numeric_date(claims: Mapping[str, Any], name: str) -> float:
        value = claims.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise JobApiError(
                "identity_required_claim_missing",
                "A required identity time claim is missing or invalid.",
                http_status=401,
                details={"claim": name},
            )
        numeric = float(value)
        if not math.isfinite(numeric):
            raise JobApiError(
                "identity_required_claim_missing",
                "A required identity time claim is missing or invalid.",
                http_status=401,
                details={"claim": name},
            )
        return numeric

    @staticmethod
    def _audiences(value: Any) -> tuple[str, ...]:
        if isinstance(value, str) and value.strip():
            return (value,)
        if isinstance(value, (list, tuple)) and value and all(isinstance(item, str) and item.strip() for item in value):
            return tuple(value)
        raise JobApiError(
            "identity_audience_mismatch",
            "The identity audience claim is missing or invalid.",
            http_status=401,
        )

    @staticmethod
    def _role_values(value: Any) -> tuple[str, ...]:
        if isinstance(value, str) and value.strip():
            return (value,)
        if isinstance(value, (list, tuple)) and value and all(isinstance(item, str) and item.strip() for item in value):
            return tuple(value)
        return ()

    @staticmethod
    def _opaque_key(kind: str, issuer: str, value: str) -> str:
        digest = hashlib.sha256(f"{issuer}\x00{value}".encode("utf-8")).hexdigest()
        return f"{kind}:sha256:{digest}"
