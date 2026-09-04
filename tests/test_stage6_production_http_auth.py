from __future__ import annotations

from datetime import UTC, datetime
import json
import unittest

from st_score_restore.job_api_types import JobApiConfig, JobApiError
from st_score_restore.production_http_auth import JobAuthorizationContext, ProductionApiV1
from st_score_restore.production_identity import (
    ProductionIdentityAdapter,
    ProductionIdentityPolicy,
    VerifiedTokenEvidence,
)


NOW = datetime(2026, 9, 4, 20, 30, tzinfo=UTC)
CLIENT_KEY = "local-client-key-0123456789abcdef"
REVIEWER_KEY = "local-reviewer-key-0123456789abcdef"


class FakeSignatureBackend:
    def __init__(self, evidence_by_token):
        self.evidence_by_token = evidence_by_token

    def verify(self, token: str) -> VerifiedTokenEvidence:
        try:
            return self.evidence_by_token[token]
        except KeyError as error:
            raise JobApiError("identity_verification_failed", "unknown token", http_status=401) from error


class FakeAuthorizationStore:
    def __init__(self):
        self.contexts: dict[str, JobAuthorizationContext] = {}
        self.fail_reads = False

    def bind_job(self, job_id: str, context: JobAuthorizationContext) -> None:
        current = self.contexts.get(job_id)
        if current is not None and current != context:
            raise JobApiError(
                "authorization_binding_conflict",
                "security binding conflict",
                http_status=403,
            )
        self.contexts[job_id] = context

    def get_job_context(self, job_id: str) -> JobAuthorizationContext | None:
        if self.fail_reads:
            raise RuntimeError("store unavailable")
        return self.contexts.get(job_id)


class FakeService:
    def __init__(self):
        self.created_actor = None
        self.created_actor_by_job: dict[str, str] = {}
        self.idempotency: dict[str, str] = {}

    def create_job(self, pages, *, idempotency_key, actor, restoration_config):
        existing = self.idempotency.get(idempotency_key)
        if existing is not None:
            return {"jobId": existing, "state": "UPLOADED"}, True
        job_id = f"job_{len(self.idempotency) + 1}"
        self.idempotency[idempotency_key] = job_id
        self.created_actor = actor
        self.created_actor_by_job[job_id] = actor
        return {"jobId": job_id, "state": "UPLOADED"}, False

    def get_job(self, job_id: str):
        return {"jobId": job_id, "state": "UPLOADED"}


def evidence(*, subject: str, tenant: str, roles, jti: str):
    now = NOW.timestamp()
    return VerifiedTokenEvidence(
        claims={
            "iss": "https://issuer.example",
            "aud": "st-score-restore",
            "sub": subject,
            "tenant_id": tenant,
            "roles": roles,
            "exp": now + 600,
            "nbf": now - 60,
            "jti": jti,
        },
        key_id="kid-1",
        algorithm="RS256",
        signature_validated=True,
    )


def make_adapter(evidence_by_token):
    return ProductionIdentityAdapter(
        ProductionIdentityPolicy(
            trusted_issuers=("https://issuer.example",),
            trusted_audiences=("st-score-restore",),
            clock_skew_seconds=30,
        ),
        FakeSignatureBackend(evidence_by_token),
        lambda issuer, token_id: False,
        clock=lambda: NOW,
    )


class ProductionApiAuthorizationTests(unittest.TestCase):
    def setUp(self):
        tokens = {
            "client-a": evidence(subject="client-a", tenant="school-a", roles=["client"], jti="c-a"),
            "client-b": evidence(subject="client-b", tenant="school-a", roles=["client"], jti="c-b"),
            "reviewer-a": evidence(subject="reviewer-a", tenant="school-a", roles=["reviewer"], jti="r-a"),
            "reviewer-b": evidence(subject="reviewer-b", tenant="school-b", roles=["reviewer"], jti="r-b"),
        }
        self.store = FakeAuthorizationStore()
        self.service = FakeService()
        self.api = ProductionApiV1(
            self.service,
            JobApiConfig(client_api_key=CLIENT_KEY, reviewer_api_key=REVIEWER_KEY),
            make_adapter(tokens),
            self.store,
        )

    def create_job(self, token="client-a", idempotency_key="prod-0001"):
        return self.api.handle(
            "POST",
            "/api/v1/restoration-jobs",
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "image/png",
                "X-Filename": "page.png",
                "Idempotency-Key": idempotency_key,
            },
            b"synthetic-image-bytes",
        )

    def test_create_binds_opaque_owner_and_same_tenant_reviewer_can_read(self):
        created = self.create_job()
        self.assertEqual(202, created.status)
        context = self.store.contexts["job_1"]
        self.assertTrue(context.owner_key.startswith("subject:sha256:"))
        self.assertTrue(context.tenant_key.startswith("tenant:sha256:"))
        self.assertEqual(context.owner_key, self.service.created_actor)

        reviewer = self.api.handle(
            "GET",
            "/api/v1/restoration-jobs/job_1",
            {"Authorization": "Bearer reviewer-a"},
        )
        self.assertEqual(200, reviewer.status)

    def test_client_ownership_and_tenant_isolation_fail_closed(self):
        self.assertEqual(202, self.create_job().status)
        other_client = self.api.handle(
            "GET",
            "/api/v1/restoration-jobs/job_1",
            {"Authorization": "Bearer client-b"},
        )
        self.assertEqual(403, other_client.status)
        self.assertEqual("job_ownership_forbidden", json.loads(other_client.body)["error"]["code"])

        other_tenant = self.api.handle(
            "GET",
            "/api/v1/restoration-jobs/job_1",
            {"Authorization": "Bearer reviewer-b"},
        )
        self.assertEqual(403, other_tenant.status)
        self.assertEqual("tenant_access_forbidden", json.loads(other_tenant.body)["error"]["code"])

    def test_static_key_and_caller_actor_headers_are_rejected(self):
        static_key = self.api.handle(
            "GET",
            "/api/v1/restoration-jobs/job_1",
            {"Authorization": "Bearer client-a", "X-Api-Key": CLIENT_KEY},
        )
        self.assertEqual(401, static_key.status)
        self.assertEqual("production_static_credential_forbidden", json.loads(static_key.body)["error"]["code"])

        actor = self.api.handle(
            "GET",
            "/api/v1/restoration-jobs/job_1",
            {"Authorization": "Bearer client-a", "X-Actor-Id": "attacker-controlled"},
        )
        self.assertEqual(400, actor.status)
        self.assertEqual("caller_supplied_identity_forbidden", json.loads(actor.body)["error"]["code"])

    def test_missing_or_unavailable_authorization_state_is_denied(self):
        missing = self.api.handle(
            "GET",
            "/api/v1/restoration-jobs/job_404",
            {"Authorization": "Bearer client-a"},
        )
        self.assertEqual(403, missing.status)
        self.assertEqual("job_security_context_missing", json.loads(missing.body)["error"]["code"])

        self.store.fail_reads = True
        unavailable = self.api.handle(
            "GET",
            "/api/v1/restoration-jobs/job_1",
            {"Authorization": "Bearer client-a"},
        )
        self.assertEqual(503, unavailable.status)
        self.assertEqual("authorization_store_unavailable", json.loads(unavailable.body)["error"]["code"])

    def test_same_external_idempotency_key_is_scoped_to_authenticated_principal(self):
        first = self.create_job("client-a")
        second = self.create_job("client-b")
        self.assertEqual(202, first.status)
        self.assertEqual(202, second.status)
        self.assertEqual("job_1", json.loads(first.body)["jobId"])
        self.assertEqual("job_2", json.loads(second.body)["jobId"])
        self.assertNotEqual(self.store.contexts["job_1"], self.store.contexts["job_2"])
        self.assertEqual(2, len(self.service.idempotency))

    def test_same_principal_idempotent_replay_keeps_same_job_and_binding(self):
        first = self.create_job("client-a")
        replay = self.create_job("client-a")
        self.assertEqual(202, first.status)
        self.assertEqual(200, replay.status)
        self.assertEqual("job_1", json.loads(replay.body)["jobId"])
        self.assertEqual(1, len(self.service.idempotency))
        self.assertEqual(
            self.store.contexts["job_1"].owner_key,
            self.service.created_actor_by_job["job_1"],
        )

    def test_external_idempotency_validation_is_preserved_before_scoping(self):
        invalid = self.create_job("client-a", idempotency_key="short")
        self.assertEqual(400, invalid.status)
        self.assertEqual("invalid_idempotency_key", json.loads(invalid.body)["error"]["code"])
        self.assertEqual({}, self.service.idempotency)

    def test_health_remains_non_identity_liveness_probe(self):
        response = self.api.handle("GET", "/health", {})
        self.assertEqual(200, response.status)


if __name__ == "__main__":
    unittest.main()
