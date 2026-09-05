#!/usr/bin/env python3
"""Validate the Stage 6 S6-04 secrets/KMS/IAM implementation authorization."""

from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage6_s6_04_authorization import load_and_validate

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    record = load_and_validate(
        ROOT / "evidence/stage6/governance/stage6-s6-04-secrets-kms-iam-authorization.v1.json"
    )
    print(
        json.dumps(
            {
                "schemaVersion": record["schema_version"],
                "authorizationId": record["authorization_id"],
                "decision": record["decision"],
                "entryMainSha": record["entry_checkpoint"]["main_sha"],
                "providerSelectionFinalized": record["explicitly_not_authorized"]["provider_selection_finalization"],
                "liveResourceCreationAuthorized": record["safety_assertions"]["live_resource_creation_authorized"],
                "productionDeploymentAuthorized": record["safety_assertions"]["production_deployment_authorized"],
                "nextSafeBoundary": record["next_safe_boundary"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
