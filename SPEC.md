# SemVer Sentinel specification

## Proof obligation

Given two publisher-supplied API snapshots, a compatibility policy and a valid
old/new SemVer pair, determine whether the described change is breaking. The
contract, not the model, determines whether the selected version bump complies.

## Actors and lifecycle

- Publisher: creates, seals and may cancel its own draft.
- Reviewer: any address may trigger assessment after sealing.
- Lifecycle: `DRAFT -> SEALED -> REVIEWED`, or `DRAFT -> CANCELLED`.
- `REVIEWED` and `CANCELLED` are terminal.
- Model/runtime failure leaves `SEALED` unchanged and returns
  `ASSESSMENT_RETRYABLE`.

## Closed observations

- `analysis_status`: `AVAILABLE | UNAVAILABLE`
- `surface_change`: `NONE | ADDITIVE | REMOVAL | REPLACEMENT | UNCERTAIN`
- `request_compatibility`: `NONE | COMPATIBLE | INCOMPATIBLE | UNCERTAIN`
- `response_compatibility`: `NONE | COMPATIBLE | INCOMPATIBLE | UNCERTAIN`
- `behavior_compatibility`: `NONE | COMPATIBLE | INCOMPATIBLE | UNCERTAIN`
- `documentation_only`: `YES | NO | UNCERTAIN`

The model may return observations only. It may not return the release verdict.

## Deterministic precedence

1. `UNAVAILABLE` -> retry without mutation.
2. Removal, replacement or any incompatible observation -> `BREAKING`.
3. Any remaining uncertainty -> `UNCERTAIN`.
4. Explicit documentation-only with no API/behavior change -> `DOC_ONLY`.
5. Otherwise -> `NON_BREAKING`.

Compliance derivation:

- `BREAKING + MAJOR` -> `COMPLIANT`.
- `BREAKING + MINOR/PATCH` -> `VERSION_VIOLATION`.
- `NON_BREAKING` or `DOC_ONLY` -> `COMPLIANT`.
- `UNCERTAIN` -> `REVIEW_REQUIRED`.

## Invariants

- SemVer accepts exactly three unsigned integer components with no prerelease.
- New version must be strictly greater than old version.
- Authority/state guards run before nondeterminism.
- Snapshot text and its contract-computed SHA-256 never change after creation.
- A reviewed release cannot be assessed again.
- Consensus compares deterministic category, compliance and reason, not prose.
- No token custody, payment, upgrade or external fetch exists.
- The UI must not enable writes before a non-zero release contract is configured.

## Honest boundary

The result means only: validators classified the exact submitted descriptions
under the exact submitted policy. It does not prove repository provenance,
runtime behavior, package safety or that the publisher shipped those bytes.
