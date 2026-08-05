# Architecture Decision Records

Architecture Decision Records (ADRs) preserve important technical and governance decisions for ST Score Restore Engine.

## When an ADR is required

Create or update an ADR when a change affects:

- repository boundaries or integration architecture,
- public API or event contracts,
- PDF or image-processing backends,
- AI model selection or training strategy,
- musical-safety validation rules,
- teacher approval or audit behavior,
- storage, privacy, retention or consent,
- licensing or model-weight distribution,
- deployment, rollback or compatibility strategy.

## File naming

Use four-digit sequential identifiers:

```text
0001-short-decision-title.md
0002-next-decision.md
```

## Required sections

Each ADR should contain:

1. Status
2. Context
3. Decision
4. Consequences
5. Safety and privacy impact
6. Alternatives considered
7. Reversal or migration path

## Status values

- `Proposed`
- `Accepted`
- `Superseded`
- `Deprecated`
- `Rejected`

An accepted ADR is changed by adding a new ADR that supersedes it, rather than rewriting the historical decision without explanation.
