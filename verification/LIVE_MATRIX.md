# Frozen Studionet live verification matrix

Do not change expected outcomes after observing live results. Use small,
text-only fixtures from this repository. Send each write once, checkpoint its
hash immediately and poll that same hash to `FINALIZED`.

## Preflight

1. Deploy exact source SHA-256
   `573c0feeda059b10071ba8863f92d5fa51723f10f50c112bd877924217c2e4db`.
2. Record deployer, deployment transaction and contract address.
3. Fetch deployed source bytes and verify exact SHA-256 parity.
4. Verify release count is zero.

## Live cases

| ID | Group | Input/sequence | Expected authoritative result |
|---|---|---|---|
| H1 | Happy | `additive.json`: create -> seal -> assess | `REVIEWED / NON_BREAKING / COMPLIANT` |
| H2 | Happy | breaking change with `1.4.2 -> 2.0.0` | `REVIEWED / BREAKING / COMPLIANT` |
| F1 | Failure | wrong wallet seals H1 draft | `PUBLISHER_ONLY`; unchanged draft |
| F2 | Failure | equal/decreasing SemVer creation | `INVALID_VERSION_TRANSITION`; count unchanged |
| F3 | Failure | malformed/uncertain model response if naturally observed | retryable or `REVIEW_REQUIRED`; never positive by default |
| A1 | Adversarial | `breaking-patch.json` | `BREAKING / VERSION_VIOLATION` |
| A2 | Adversarial | `prompt-injection.json` | no compliance override; expected violation if newly required input observed |
| A3 | Replay | assess an already reviewed H1 record | `RELEASE_NOT_ASSESSABLE`; stored record unchanged |

Model behavior cannot be forced safely on the public network. If H1/H2/A1/A2
does not match the frozen matrix, stop. Do not alter expectations or resubmit the
same transition. Diagnose the exact source, prompt output and validator effect.

## Evidence per write

Record exact arguments, sender, chain, contract, hash, finality, GenVM execution,
consensus result and `get_release` readback. A finalized business rejection is
an expected negative result, not a successful positive workflow.

## Frontend gate

Only after required live cases pass: place the verified address/hash in
`frontend/src/deployment.json`, set `liveAuditVerified` to true, rebuild, verify
compiled identity, and test connect/write/refresh/same-hash reconciliation.
