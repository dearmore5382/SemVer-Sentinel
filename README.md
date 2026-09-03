# SemVer Sentinel

SemVer Sentinel is a narrow GenLayer DApp that records whether a submitted API
change is semantically compatible with its proposed version bump. Publishers
seal the old API, new API, SemVer pair and compatibility policy directly in the
contract. Validators independently classify compatibility observations; the
contract deterministically derives the final compliance result.

## Current status

**Deployed and live-verified on Studionet.** Deployed byte-for-byte source parity
and the predefined behavioral matrix have been verified against contract
`0xfdA283EF4D39763ECbFf3BC739cBfB12fF5E3594`.

- Contract: 7 public methods, no constructor arguments, no web fetch, no custody.
- Local suite: 21 pytest tests covering happy, failure and adversarial behavior.
- GenVM lint, schema validation and typecheck pass.
- Frontend: 5 unit tests, TypeScript, lint and production build pass.
- Desktop and 390 px mobile QA pass with no broken images or horizontal overflow.
- Live verification: 15 predefined writes plus one explicitly authorized,
  single-attempt retry; every transaction finalized with majority agreement.
- The first prompt-injection assessment returned `ASSESSMENT_RETRYABLE` without
  mutation. Its one controlled retry produced the expected
  `BREAKING / VERSION_VIOLATION` state. Both attempts remain in the evidence.
- Exact contract source SHA-256:
  `573c0feeda059b10071ba8863f92d5fa51723f10f50c112bd877924217c2e4db`
  (case-insensitive hexadecimal; canonical lowercase is recorded below).

Canonical source hash:

```text
573c0feeda059b10071ba8863f92d5fa51723f10f50c112bd877924217c2e4db
```

## Why GenLayer

Whether an API description removes a behavior, makes an input newly required,
or changes a response incompatibly is semantic judgment. Ordinary deterministic
code then parses SemVer and decides whether that observed category complies.
The model cannot write a compliance verdict directly.

## Lifecycle

```text
DRAFT -> SEALED -> REVIEWED
  └----> CANCELLED
```

Model/runtime failure returns `ASSESSMENT_RETRYABLE` and leaves the sealed state
unchanged. Reviewed and cancelled records are terminal.

## Local verification

```powershell
python -m pytest -q
$env:PYTHONIOENCODING='utf-8'
genvm-lint check contracts\SemVerSentinel.py
genvm-lint typecheck contracts\SemVerSentinel.py
cd frontend
npm ci
npm test
npm run typecheck
npm run lint
npm run build
```

## Repository map

- `SPEC.md`: proof obligation, closed observations and invariants.
- `PLAN.md`: staged build and deployment stop condition.
- `contracts/SemVerSentinel.py`: sole authoritative contract source.
- `fixtures/`: compact text/JSON happy and adversarial samples.
- `tests/`: semantic, static and Direct Mode tests.
- `verification/AUDIT.md`: findings and honest boundaries.
- `verification/LIVE_MATRIX.md`: exact post-deploy verification plan.
- `verification/LIVE_RESULTS.md`: live outcomes, transaction hashes and boundaries.
- `verification/DEPLOYMENT_READINESS.md`: frozen handoff.
- `frontend/`: distinct English-only release review console.

## Honest limitations

The publisher authors both API snapshots and policy. The contract hashes and
preserves those exact strings but does not prove they match a repository or
deployed service. A review is not a security audit, package certification or
proof of shipped behavior. This design creates an attributable semantic record;
it does not create external provenance.
