# Deployment record — deployed and live-verified

## Frozen candidate

- Contract: `contracts/SemVerSentinel.py`
- SHA-256: `573c0feeda059b10071ba8863f92d5fa51723f10f50c112bd877924217c2e4db`
- Constructor arguments: none
- Runtime header: workspace-pinned v0.2.16 / py-genlayer dependency
- Public surface: 4 write methods, 3 view methods
- External fetches: none
- Value custody: none
- Upgrade authority: none

## Passed gates

- 21 pytest tests pass.
- GenVM lint and semantic validation pass.
- GenVM typecheck passes.
- Frontend has 5 passing tests; lint, strict TypeScript and production build pass.
- Desktop and mobile rendering checked; supplied logo loads; English-only UI;
  pending deployment disables all writes.
- P1/P2 review found and fixed prompt-boundary, observation-contradiction and
  frontend type-boundary issues.

## Deployment and verification

The exact frozen source was deployed at
`0xfdA283EF4D39763ECbFf3BC739cBfB12fF5E3594` with no constructor arguments.
Read-only preflight proved chain ID 61999 and exact deployed-source byte parity.

The 15-step matrix reached finality for every planned transaction. Fourteen
produced their expected outcome on the first assessment attempt. The final
prompt-injection assessment safely returned `ASSESSMENT_RETRYABLE` and left the
record sealed. One separately authorized retry then finalized with
`VERSION_VIOLATION`; no automatic resubmission occurred. See `LIVE_RESULTS.md`.
