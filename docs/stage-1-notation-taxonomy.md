# Stage 1 notation taxonomy

**Status:** Binding clarification for Stage 1 corpus classification  
**Date:** 2026-09-01  
**Scope:** `staff`, `guitar_tab`, `combined_staff_tab`

## Purpose

This note removes an ambiguity in the phrase "standalone guitar TAB" used by Stage 1C/C17 planning. The word **standalone** describes the corpus artifact role, not a requirement that the page contain TAB and nothing else.

## Normative definitions

### `staff`

Use when the artifact contains conventional staff notation and is not being admitted as a guitar-TAB-bearing score for the relevant coverage claim.

### `guitar_tab`

Use for a dedicated guitar-TAB-bearing score artifact. A qualifying `guitar_tab` artifact **may contain standard staff notation above the TAB system**. A paired layout with standard notation above and six-line guitar TAB below is valid guitar-TAB evidence; pure TAB-only layout is **not required**.

The defining requirement is that a real six-line guitar TAB layer is a primary musical layer of the admitted artifact and that the artifact is intentionally admitted for the guitar-TAB coverage dimension.

### `combined_staff_tab`

Use for the mixed-layout dimension where standard staff notation and guitar TAB appear together in a paired or otherwise combined visual layout. This label captures layout complexity and must not by itself imply that the artifact was admitted as the independent/dedicated `guitar_tab` corpus target.

An artifact may legitimately carry both `guitar_tab` and `combined_staff_tab` when both claims are independently supported and explicitly admitted.

## C17 interpretation

- **C17A remains unchanged.** Its accepted admission scope is `["combined_staff_tab"]` only. This historical C17A decision is not retroactively rewritten by this clarification.
- **C17B is the independent/dedicated guitar-TAB corpus target.** C17B does **not** require a TAB-only page. A score with standard notation above and TAB below is eligible for C17B when the exact artifact, rights, provenance, custody, purpose, privacy and C11 gates pass.
- If a C17B artifact visibly and consistently contains the paired staff+TAB layout, its future item metadata may declare both `guitar_tab` and `combined_staff_tab`; that decision must be based on exact admitted bytes and must be covered by regression tests.

## Coverage rule

The historical C15/C16 report remains immutable. This clarification does not retroactively change historical counts or C17A metadata. Future expanded snapshots evaluate only explicitly admitted metadata from their selected versioned items.

`guitar_tab` and `combined_staff_tab` therefore remain separate coverage dimensions:

- `guitar_tab` measures presence of an independently admitted dedicated guitar-TAB-bearing artifact;
- `combined_staff_tab` measures the paired/mixed staff+TAB visual layout dimension.

The same future artifact may satisfy both dimensions only when both labels are explicitly supported and admitted. No implicit double counting of artifacts, source families, or metadata versions is allowed.

## Prohibited interpretations

- Do not define `guitar_tab` as "TAB-only".
- Do not reject a guitar-TAB score merely because it also contains standard notation above the TAB.
- Do not relabel C17A retroactively to close a missing category.
- Do not infer a coverage label from a filename, provider title, or thumbnail without exact-byte inspection.
- Do not count one exact artifact as two independent corpus artifacts merely because it has two notation labels.
