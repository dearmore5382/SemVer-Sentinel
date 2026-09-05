# SemVer Sentinel v2

SemVer Sentinel reviews API compatibility only after an immutable release
artifact is bound to an authenticated publisher and exact repository commit.

## Remediation status

**Version 2 is deployed and live-verified on Studionet.** The original contract
`0xfdA283EF4D39763ECbFf3BC739cBfB12fF5E3594` is historical v1 evidence and must
not be used for resubmission.

The v2 frontend is bound to `0x118f353B758ca1B26d07ec1082B12495107Cf5b3`
only after byte-for-byte source parity and the frozen 28-step live matrix passed.

## Steward feedback addressed

The original design trusted descriptions typed by the publisher. Version 2:

- accepts only a canonical GitHub raw URL pinned to a full 40-hex commit;
- derives package identity from the URL's owner/repository;
- requires the artifact to name the GenLayer creator address as publisher;
- makes every validator fetch and SHA-256 the exact artifact bytes;
- requires digest, schema, package, publisher, versions and policy to match;
- classifies semantics only after those bindings succeed;
- prevents provenance failure from producing `COMPLIANT`;
- preserves sealed state when source/model availability is uncertain.

## Honest boundary

This proves integrity and publisher attribution for one artifact at one commit.
It does not prove GitHub-login ownership, completeness of the Git tree,
distribution to users or package security.

## Local gates

- 19 Python semantic/static/Direct Mode tests pass.
- GenVM lint, schema validation and typecheck pass.
- 5 frontend tests, TypeScript, lint and production build pass.
- Regression coverage includes mutable branch, deceptive hostname, digest
  mismatch, package substitution, authority mismatch, source failure, replay and
  prompt injection.

```powershell
python -m pytest -q
genvm-lint check contracts\SemVerSentinel.py
genvm-lint typecheck contracts\SemVerSentinel.py
cd frontend
npm test
npm run typecheck
npm run lint
npm run build
```

See `SPEC.md`, `PLAN.md`, `fixtures/artifacts/` and
`verification/LIVE_MATRIX.md`. Historical v1 evidence remains clearly labelled
in `verification/` until it is archived in the remediation commit.
