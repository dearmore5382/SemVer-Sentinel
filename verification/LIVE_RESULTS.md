# Studionet live verification results

## Identity

- Contract: `0xfdA283EF4D39763ECbFf3BC739cBfB12fF5E3594`
- Chain ID: `61999`
- Frozen source SHA-256:
  `573c0feeda059b10071ba8863f92d5fa51723f10f50c112bd877924217c2e4db`
- Preflight evidence:
  `preflight-0xfda283ef4d39763ecbff3bc739cbfb12ff5e3594.json`
- Sanitized matrix evidence:
  `live-matrix-0xfda283ef4d39763ecbff3bc739cbfb12ff5e3594.json`
- Sanitized retry evidence:
  `a2-single-retry-0xfda283ef4d39763ecbff3bc739cbfb12ff5e3594.json`

## Outcomes

| Case | Final authoritative outcome | Evidence |
| --- | --- | --- |
| H1 additive minor | `NON_BREAKING / COMPLIANT` | First attempt |
| F1 wrong publisher seal | `PUBLISHER_ONLY`, no mutation | First attempt |
| F2 equal version | `INVALID_VERSION_TRANSITION`, no new record | First attempt |
| A1 breaking patch | `BREAKING / VERSION_VIOLATION` | First attempt |
| H2 breaking major | `BREAKING / COMPLIANT` | First attempt |
| A3 assessment replay | `RELEASE_NOT_ASSESSABLE`, no mutation | First attempt |
| A2 prompt injection + required input | `BREAKING / VERSION_VIOLATION` | One unavailable result, then one authorized retry |

All 15 planned transactions finalized. The initial A2 assessment transaction
`0x1b870ce9b251ccff199789c006b23fe2161439c7f5f4ea9da416b38a59d47db5`
reached `MAJORITY_AGREE` but returned `ASSESSMENT_RETRYABLE`; its closed
observation was `UNAVAILABLE` with uncertain fields, and the release remained
`SEALED`. There was no GenVM execution error and no automatic retry.

The user then authorized exactly one retry. Transaction
`0xa21963982af865702a9a2ec4dc170813a99855d9b9e7a50284f0de37362b9b11`
finalized with `MAJORITY_AGREE`, returned `VERSION_VIOLATION`, and authoritative
readback showed `REVIEWED / BREAKING / VERSION_VIOLATION /
BREAKING_CHANGE_DETECTED`.

## Evidence boundary

These records demonstrate the frozen cases on this Studionet deployment. They
do not prove external repository provenance, shipped API behavior, universal
model availability, production security, or compatibility of inputs that were
not tested. Test-wallet private keys and wallet balances are excluded from the
public evidence files.
