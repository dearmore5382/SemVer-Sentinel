# SemVer Sentinel v2 specification

## Steward remediation

The original deployment assessed publisher-supplied descriptions without an
authenticated package or immutable release artifact. Version 2 makes artifact
provenance a mandatory prerequisite rather than a documentation disclaimer.

## Proof obligation

For an exact GitHub repository, full commit and JSON release artifact, establish
that validators fetched the committed bytes, recomputed the submitted SHA-256,
confirmed the artifact names the transaction sender as publisher, and then
classified the bound old/new API snapshots. Only after those checks may
deterministic code derive SemVer compliance.

## Artifact schema

The immutable JSON object must contain exactly:

```json
{
  "artifact_schema": "semver-sentinel/v2",
  "package_id": "github:owner/repository",
  "publisher": "0x...",
  "old_version": "1.2.3",
  "new_version": "1.3.0",
  "policy": "...",
  "old_api": "...",
  "new_api": "..."
}
```

The locator must be
`https://raw.githubusercontent.com/<owner>/<repository>/<40-hex-commit>/<path>.json`.
The contract derives `github:owner/repository` and the commit from that locator.
Branches, tags, query strings, fragments, alternate origins and deceptive
hostnames are rejected before state creation.

The `publisher` field is cryptographic attribution to the GenLayer address that
creates the release. It does not prove a legal identity or GitHub account login.

## Actors and lifecycle

- Publisher: the address committed inside the artifact; creates, seals and may
  cancel its own draft.
- Reviewer: any address may trigger assessment of a sealed artifact.
- Lifecycle: `DRAFT -> SEALED -> REVIEWED | REJECTED`, or
  `DRAFT -> CANCELLED`.
- Transport/model failure leaves `SEALED` unchanged and is retryable.
- `REVIEWED`, `REJECTED` and `CANCELLED` are terminal.

## Mandatory provenance gate

Each validator independently:

1. fetches the commit-pinned artifact;
2. hashes the exact returned bytes;
3. requires equality with the sealed SHA-256;
4. requires exact schema and package identity;
5. requires artifact publisher = release creator;
6. requires version pair and policy = sealed inputs;
7. only then submits the embedded API snapshots to semantic classification.

`DIGEST_MISMATCH`, `MANIFEST_INVALID` and `AUTHORITY_MISMATCH` deterministically
produce `ARTIFACT_REJECTED`. `UNAVAILABLE` produces `ASSESSMENT_RETRYABLE` with
no state mutation. None can produce `COMPLIANT`.

## AI and consensus boundary

AI returns only a closed semantic observation. It cannot set provenance,
digest, package, publisher, version, compliance or state. Validators independently
re-fetch, re-hash and reclassify. Equivalence compares deterministic consequence.

## Honest boundary

This proves integrity and publisher attribution for one exact artifact inside one
repository commit. It does not prove the repository is an official registry,
that the artifact describes every source file, that software shipped, or safety.
