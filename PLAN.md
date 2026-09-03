# SemVer Sentinel — build plan

## Product boundary

SemVer Sentinel records a publisher-declared comparison between two API
snapshots and uses GenLayer consensus to classify semantic compatibility. It
does not fetch repositories, prove that submitted text matches shipped code,
or certify security. Its consequential output is a permanent compatibility
record for the exact snapshots stored by the contract.

## Build phases

1. Freeze the proof obligation, observation schema, precedence and lifecycle.
2. Implement deterministic SemVer parsing, input bounds and state guards.
3. Implement one bounded text-only model call and independent validation.
4. Persist only a canonical effect-aligned review result.
5. Test happy, failure, adversarial, replay and model-error paths.
6. Build a distinct release-console frontend with the supplied logo.
7. Run lint, typecheck, production build and a P1/P2 review.
8. Freeze the exact contract source hash and live verification matrix.
9. Stop before deployment; the user deploys the frozen source.
10. After deployment, verify source parity and run the frozen live matrix once.

## Stop condition

Do not deploy during the build. Deployment readiness requires all local gates
to pass and `verification/DEPLOYMENT_READINESS.md` to contain the exact source
SHA-256.
