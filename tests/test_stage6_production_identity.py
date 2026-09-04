from __future__ import annotations

from datetime import UTC, datetime
import unittest

from st_score_restore.job_api_types import JobApiError
from st_score_restore.production_identity import (
    ProductionIdentityAdapter,
    ProductionIdentityPolicy,
    VerifiedTokenEvidence,
)


NOW = datetime(2026, 9, 4, 20, 30, tzinfo=UTC)


class FakeSignatureBackend:
    def __init__(self, evidence_by_token):
        self.evidence_by_token = evidence_by_token

    def verify(self, token: str) -> VerifiedTokenEvidence:
        try:
            return self.evidence_by_token[token]
        except KeyError as error:
            raise JobApiError("identity_verification_failed", "unknown token", http_status=401) from error


def evidence(
    *,
    subject: str,
    tenant: str,
    roles,
    issuer: str = "https://issuer.example",
    audience="st-score-restore",
    exp: float | None = None,
    nbf: float | None = None,
    jti: str = "token-1",
    signature_validated: bool = True,
    key_id: str = "kid-1",
    algorithm: str = "RS256",
):
    now = NOW.timestamp()
    return VerifiedTokenEvidence(
        claims={
            "iss": issuer,
            "aud": audience,
            "sub": subject,
            "tenant_id": tenant,
            "roles": roles,
            "exp": now + 600 if exp is None else exp,
            "nbf": now - 60 if nbf is None else nbf,
            "jti": jti,
        },
        key_id=key_id,
        algorithm=algorithm,
        signature_validated=signature_validated,
    )


def make_adapter(evidence_by_token, revoked=None):
    revoked = set(revoked or ())
    return ProductionIdentityAdapter(
        ProductionIdentityPolicy(
            trusted_issuers=("https://issuer.example",),
            trusted_audiences=("st-score-restore",),
            clock_skew_seconds=30,
        ),
        FakeSignatureBackend(evidence_by_token),
        lambda issuer, token_id: token_id in revoked,
        clock=lambda: NOW,
    )


class ProductionIdentityTests(unittest.TestCase):
    def test_verified_identity_derives_opaque_principal_and_tenant(self):
        adapter = make_adapter({"client": evidence(subject="person@example.com", tenant="school-a", roles=["client"])})
        identity = adapter.authenticate_bearer_token("client")
        self.assertEqual("client", identity.role)
        self.assertTrue(identity.production)
        self.assertTrue(identity.actor_id.startswith("subject:sha256:"))
        self.assertTrue(identity.tenant_key.startswith("tenant:sha256:"))
        self.assertNotIn("person@example.com", identity.actor_id)
        self.assertNotIn("school-a", identity.tenant_key)

    def test_role_conflict_is_denied(self):
        adapter = make_adapter({"conflict": evidence(subject="u1", tenant="t1", roles=["client", "reviewer"])})
        with self.assertRaises(JobApiError) as raised:
            adapter.authenticate_bearer_token("conflict")
        self.assertEqual("identity_role_conflict", raised.exception.code)
        self.assertEqual(403, raised.exception.http_status)

    def test_expired_revoked_and_unsigned_tokens_fail_closed(self):
        now = NOW.timestamp()
        adapter = make_adapter(
            {
                "expired": evidence(subject="u1", tenant="t1", roles=["client"], exp=now - 100),
                "revoked": evidence(subject="u1", tenant="t1", roles=["client"], jti="revoked-1"),
                "unsigned": evidence(subject="u1", tenant="t1", roles=["client"], signature_validated=False),
            },
            revoked={"revoked-1"},
        )
        expectations = {
            "expired": "identity_token_expired",
            "revoked": "identity_token_revoked",
            "unsigned": "identity_signature_not_validated",
        }
        for token, code in expectations.items():
            with self.subTest(token=token), self.assertRaises(JobApiError) as raised:
                adapter.authenticate_bearer_token(token)
            self.assertEqual(code, raised.exception.code)

    def test_wrong_issuer_audience_and_future_nbf_are_denied(self):
        now = NOW.timestamp()
        adapter = make_adapter(
            {
                "issuer": evidence(subject="u1", tenant="t1", roles=["client"], issuer="https://evil.example"),
                "aud": evidence(subject="u1", tenant="t1", roles=["client"], audience="other-service"),
                "nbf": evidence(subject="u1", tenant="t1", roles=["client"], nbf=now + 120),
            }
        )
        expectations = {
            "issuer": "identity_issuer_not_trusted",
            "aud": "identity_audience_mismatch",
            "nbf": "identity_token_not_yet_valid",
        }
        for token, code in expectations.items():
            with self.subTest(token=token), self.assertRaises(JobApiError) as raised:
                adapter.authenticate_bearer_token(token)
            self.assertEqual(code, raised.exception.code)


if __name__ == "__main__":
    unittest.main()
