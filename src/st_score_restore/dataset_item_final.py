"""Synthetic lineage, review, and assertion validation for dataset items."""

from __future__ import annotations

from typing import Any

from .dataset_contract_common import _code_array, _date, _enum, _fields, _int, _match, _obj
from .dataset_contract_constants import CODE, DATASET_ACTOR_ID, DATASET_REVIEW_STATES, DatasetManifestError, EVIDENCE_ID, SEMVER, SHA


def finalize_item(value: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    where = ctx["where"]
    synthetic = value["syntheticGeneration"]
    if ctx["source"] == "synthetic":
        synthetic = _obj(synthetic, f"{where}.syntheticGeneration")
        _fields(synthetic, {"generator", "generatorVersion", "generatorCommit", "generatedOn", "derivationAuthorizationReference", "seed", "parameters"}, f"{where}.syntheticGeneration")
        _match(synthetic["generator"], CODE, f"{where}.syntheticGeneration.generator")
        _match(synthetic["generatorVersion"], SEMVER, f"{where}.syntheticGeneration.generatorVersion")
        _match(synthetic["generatorCommit"], SHA, f"{where}.syntheticGeneration.generatorCommit")
        generated_on = _date(synthetic["generatedOn"], f"{where}.syntheticGeneration.generatedOn")
        derivation_reference = _match(synthetic["derivationAuthorizationReference"], EVIDENCE_ID, f"{where}.syntheticGeneration.derivationAuthorizationReference")
        _int(synthetic["seed"], f"{where}.syntheticGeneration.seed")
        _obj(synthetic["parameters"], f"{where}.syntheticGeneration.parameters")
        if ctx["parent"] is None:
            raise DatasetManifestError(f"{where} synthetic item requires a non-synthetic parent")
    else:
        generated_on = derivation_reference = None
        if synthetic is not None or ctx["parent"] is not None:
            raise DatasetManifestError(f"{where} parent/generation metadata is only for synthetic sources")

    review = _obj(value["review"], f"{where}.review")
    _fields(review, {"status", "reviewedBy", "reviewedOn", "evidenceReference", "noteCodes"}, f"{where}.review")
    status = _enum(review["status"], DATASET_REVIEW_STATES, f"{where}.review.status")
    reviewer = _match(review["reviewedBy"], DATASET_ACTOR_ID, f"{where}.review.reviewedBy", null=True)
    reviewed_on = _date(review["reviewedOn"], f"{where}.review.reviewedOn", null=True)
    evidence = _match(review["evidenceReference"], EVIDENCE_ID, f"{where}.review.evidenceReference", null=True)
    _code_array(review["noteCodes"], f"{where}.review.noteCodes")
    completed = status in {"approved", "rejected", "revoked"}
    if completed != (reviewer is not None and reviewed_on is not None and evidence is not None):
        raise DatasetManifestError(f"{where}.review actor/date/evidence do not match status")
    if not completed and any(v is not None for v in (reviewer, reviewed_on, evidence)):
        raise DatasetManifestError(f"{where}.review incomplete status cannot claim evidence")
    granted = {p for p, permission in ctx["permissions"].items() if permission["status"] == "granted"}
    if granted and status != "approved":
        raise DatasetManifestError(f"{where} active permission requires approved dataset review")
    if ctx["artifact"] == "external_available" and status != "approved":
        raise DatasetManifestError(f"{where} external artifact requires approved dataset review")
    if ctx["artifact"] == "revoked" and status != "revoked":
        raise DatasetManifestError(f"{where} revoked artifact requires revoked dataset review")

    assertions = _obj(value["assertions"], f"{where}.assertions")
    names = {"teacherApprovalImpliedDatasetPermission", "teacherApprovalImpliedTrainingPermission", "originalBytesInGit", "stage1TrainingExecutionAuthorized"}
    _fields(assertions, names, f"{where}.assertions")
    if any(assertions[name] is not False for name in names):
        raise DatasetManifestError(f"{where}.assertions must remain false")
    ctx.update({"raw": value, "review": status, "reviewOn": reviewed_on, "generatedOn": generated_on, "derivationReference": derivation_reference})
    return ctx
