# SemVer Sentinel v3

SemVer Sentinel checks whether the version bump between two exact npm releases matches compatibility changes in the TypeScript declarations that actually shipped in their registry tarballs.

## Why v3 exists

The steward correctly rejected v2: a commit-pinned JSON manifest was immutable, but its `old_api` and `new_api` fields were still publisher-authored claims. V3 removes descriptions, URLs and hashes from caller input. A caller supplies only an npm package, two exact versions and a review policy.

For each version the contract constructs the npm registry URL, verifies exact package/version identity, requires the canonical npm tarball URL, recomputes the published SHA-512 integrity, and extracts the shipped `.d.ts` entrypoint. Only then may validators classify compatibility. The on-chain observation records both registry integrity values and both extracted-source SHA-256 values.

## Current status

V3 is deployed at `0xd44DF7b3D9bdD91731D46801E8a7eb057640be0E`.
Exact deployed/local source parity and the checkpointed nine-step Studionet
matrix passed. The frontend is bound only to this verified deployment.

Historical deployments `0xfdA283EF4D39763ECbFf3BC739cBfB12fF5E3594` (v1) and `0x118f353B758ca1B26d07ec1082B12495107Cf5b3` (v2) do not satisfy the latest steward request and must not be submitted as v3 evidence.

## Honest boundary

V3 supports npm tarballs up to 300 KB with a TypeScript declaration entrypoint. It proves the assessed declarations were bytes inside integrity-verified npm release tarballs. It does not prove runtime behavior, malware safety, legal maintainer identity, or compatibility outside the exported declaration surface.

## Verified local gates

- 14 Python semantic, static and Direct Mode tests pass.
- GenVM lint, schema validation and typecheck pass (6 methods, no constructor).
- 5 frontend tests, TypeScript, lint and production build pass.
- Coverage includes happy path, canonical origin, package/version substitution, tarball locator mismatch, integrity mismatch, missing source, unavailable registry, authority, replay and prompt injection.

See `SPEC.md`, `verification/AUDIT.md`, `verification/DEPLOYMENT_READINESS.md`
and `verification/LIVE_RESULTS.md` for the evidence and its limits.
