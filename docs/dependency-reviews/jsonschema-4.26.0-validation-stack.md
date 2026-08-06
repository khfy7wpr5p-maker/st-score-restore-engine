# Dependency review: JSON Schema validation stack

- **Status:** Approved only for Stage 1A offline schema validation and tests
- **Related decision:** ADR 0013
- **Pull request:** #35
- **Python:** 3.11 and 3.12
- **Runtime restoration impact:** None

## Purpose

Use a real JSON Schema Draft 2020-12 implementation to validate the Stage 1A
catalog and snapshot schemas and execute a shared schema/Python parity corpus.
The stack is installed only by repository validation and test workflows. It is
not imported by restoration, API, persistence or job-processing modules.

## Exact graph

| Package | Version | Role | License |
|---|---:|---|---|
| `jsonschema` | `4.26.0` | Draft 2020-12 validator | MIT |
| `attrs` | `26.1.0` | `jsonschema` runtime dependency | MIT |
| `jsonschema-specifications` | `2025.9.1` | packaged meta-schemas/vocabularies | MIT |
| `referencing` | `0.37.0` | local schema registry and references | MIT |
| `rpds-py` | `2026.5.1` | persistent data structures used by referencing | MIT |
| `typing-extensions` | `4.15.0` | TypeVar default support required by referencing on Python <3.13 | PSF-2.0 |

The complete graph is exact-pinned in `requirements.validation.lock`. CI uses
`--only-binary=:all:` and `--no-deps`; implicit dependency resolution and source
builds are rejected. CI also runs `pip check` to prove that the exact graph is complete.

## Canonical sources

- `jsonschema`: Python JSON Schema project on PyPI/GitHub
- `attrs`: Python attrs project on PyPI/GitHub
- `jsonschema-specifications` and `referencing`: Python JSON Schema project
- `rpds-py`: crate-py/rpds project
- `typing-extensions`: Python typing-extensions project

## Security and privacy

- Validation is offline and receives repository-owned JSON only.
- No format extras are installed.
- No network resolver, URL fetcher or remote schema registry is configured.
- Both schemas use local `#/$defs/...` references only.
- The validator does not read document artifacts or custody storage.
- Schema validation does not replace the Python semantic validator.
- Untrusted inputs remain subject to repository input-size and execution limits
  before any future service integration.

## Redistribution and bundled components

`jsonschema`, `attrs`, `jsonschema-specifications`, `referencing`, and `rpds-py` use the MIT license. `typing-extensions` uses PSF-2.0. `rpds-py` contains native Rust code and may
bundle third-party notices in its wheel. Redistributors must retain license and
notice material shipped with the exact wheels.

## Removal and fallback

Removing `requirements.validation.lock`, the optional `validation` group and the
Draft 2020-12 parity tests removes the stack without changing runtime
restoration behavior. There is intentionally no weaker parity fallback: PRs
that modify dataset schemas must fail validation until a reviewed Draft 2020-12
engine is available.
