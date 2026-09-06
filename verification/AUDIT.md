# V3 pre-deployment adversarial audit

Status: local gates passed; live chain cases pending a fresh v3 deployment.

## Happy path

The Direct Mode suite serves two generated npm tarballs, matching registry metadata and SHA-512 integrity values. The contract extracts each `index.d.ts`, classifies an additive change and persists `NON_BREAKING / COMPLIANT` together with both tarball integrity strings and both declaration SHA-256 hashes.

## Failure paths

- metadata package/version mismatch -> `ARTIFACT_REJECTED`;
- non-canonical tarball locator -> `ARTIFACT_REJECTED`;
- one-byte integrity mismatch -> `ARTIFACT_REJECTED`;
- missing/oversized declaration -> `ARTIFACT_REJECTED`;
- registry/model unavailable -> retryable, sealed state unchanged;
- wrong actor, wrong state and replay -> rejected.

## Adversarial combinations

Caller-controlled URLs, source descriptions and digests do not exist in the ABI. Prompt-like text inside a declaration remains untrusted evidence. The model cannot set registry facts, integrity, SemVer compliance or lifecycle state. Every validator independently repeats metadata acquisition, tarball hashing, source extraction and classification. Consensus requires exact equality of all four artifact/source bindings plus deterministic outcome equality.

## Evidence honesty

Mocks prove deterministic mechanics and negative controls; they are not live npm or Studionet evidence. A submission-ready claim requires fresh deployment, byte-for-byte explorer source parity, real registry happy/failure cases, finality, execution success, accepted consensus and authoritative contract readback.
