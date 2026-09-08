# ADR 0028 — Stage 11 V2a Staging Request/Response Adapter

Status: Accepted for Stage 11 staging validation only  
Date: 2026-09-08

## Context

The frozen V2a TorchScript candidate has passed development, held-out, Stage 9A, package custody, deterministic packaging, and synthetic consumer-adapter integration. The consumer adapter proved arbitrary-size grayscale array handling, but no request/response transport boundary existed for an application service.

The repository already has a non-production `/api/v1` job/review interface. This Stage 11 work must not silently register a new public route or modify that existing contract. The purpose is narrower: prove a bounded in-process request/response adapter around the exact frozen package.

## Decision

Define a transport-neutral staging-only adapter with these constraints:

- request and response bodies are 8-bit native grayscale PNG;
- color and alpha PNGs fail closed rather than being silently converted;
- request size is limited to 8 MiB, dimensions to 8192 pixels per axis, and total pixels to 16 million;
- request metadata requires a bounded `requestId` and source classification;
- accepted source classifications are `synthetic_only` and `nonheldout_test_only`;
- real-user data is explicitly forbidden at this boundary;
- the adapter delegates restoration to the already validated frozen consumer adapter;
- response shape must equal request image shape;
- request and response SHA-256 identities are returned for evidence binding;
- the exact package SHA-256 is returned in response metadata;
- no network route is registered and `src/st_score_restore/http_api.py` plus `api/openapi.v1.json` remain unchanged.

## Genuine execution

The exact private V2a package was executed on a synthetic `700×900` score-like grayscale PNG. The request was processed twice through the staging request/response boundary.

- input PNG bytes: `5,613`
- output PNG bytes: `21,478`
- request SHA-256: `cfbf82cab845b8b4d2ce3b8d98f76eb9d44326916536a9384a116246f303f352`
- response SHA-256: `7a3033100e433236293700673d847701960252669634a07507069ad045678c60`
- repeat response SHA-256: identical
- repeat metadata: identical
- input/output shape: `700×900`
- consumer tiles: `4`
- output finite and within `[0,1]`

Environment: Python 3.13.5, PyTorch 2.10.0+cpu, NumPy 2.3.5, OpenCV 4.13.0, CPU.

The execution used no held-out data, Stage 9A artifacts, optimizer, backpropagation, weight mutation, private/student/user data or network route.

## Safety and authorization

This validation demonstrates staging request/response mechanics only. It does not establish production readiness, OMR correctness, musical correctness, real-user safety, production deployment, or Stage 12 entry.

Production inference, production promotion, real-user rollout, final production model selection and Stage 12 remain unauthorized.

## Next boundary

The next safe Stage 11 boundary is a shadow-mode handoff into the existing non-production application/job service using synthetic or otherwise non-heldout inputs only. No new public route may be exposed. Production, real-user rollout and Stage 12 remain closed.
