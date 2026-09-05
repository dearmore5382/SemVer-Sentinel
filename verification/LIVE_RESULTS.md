# V2 Studionet results

## Identity

- Contract: `0x118f353B758ca1B26d07ec1082B12495107Cf5b3`
- Chain ID: `61999`
- Frozen source SHA-256:
  `24c3b47811ff42d3733edfbd49259f3ed04770ea1171f1c425c153c81ac6298a`
- Artifact revision: `c199fa1b2eab1b8daa76c86ebe448f1c6dfac1f6`
- Exact deployed/local byte parity: verified.
- Preflight: `preflight-0x118f353b758ca1b26d07ec1082b12495107cf5b3.json`
- Sanitized 28-step journal:
  `live-matrix-0x118f353b758ca1b26d07ec1082b12495107cf5b3.json`

## Outcomes

| Case | Authoritative outcome |
| --- | --- |
| Immutable locator guards | Mutable revision and deceptive hostname rejected; count unchanged |
| H1 authenticated additive minor | `REVIEWED / NON_BREAKING / COMPLIANT`; fetched digest matched |
| H2 authenticated breaking major | `REVIEWED / BREAKING / COMPLIANT`; fetched digest matched |
| A1 prompt injection in breaking patch | `REVIEWED / BREAKING / VERSION_VIOLATION` |
| F3 wrong expected digest | `REJECTED / ARTIFACT_REJECTED / DIGEST_MISMATCH` |
| F4 wrong publisher in artifact | `REJECTED / ARTIFACT_REJECTED / AUTHORITY_MISMATCH` |
| F5 wrong package in artifact | `REJECTED / ARTIFACT_REJECTED / MANIFEST_INVALID` |
| Missing GitHub raw path | GitHub returned 404 bytes; exact digest check produced terminal `DIGEST_MISMATCH` |
| Authority and lifecycle | Outsider seal/cancel denied, replay denied, publisher cancel succeeded |

All 28 frozen steps finished `FINALIZED / MAJORITY_AGREE`, returned the
documented value and passed authoritative readback. H2 assessment first returned
`ASSESSMENT_RETRYABLE` while the record remained byte-for-byte `SEALED`; one
documented retry then passed. No automatic resubmission occurred.

During the final draft creation, the SDK received an HTTP 502 while waiting for
the receipt after broadcast. The public Explorer and chain state showed the
transaction had finalized. Hash
`0x5ad83484fd16ea9be27be47d58965a2a8064e844a80cbe57958fc381b87cf693`
was recovered and verified against sender, recipient, exact calldata, return and
readback before the runner resumed; the create was not submitted twice.

## Evidence boundary

V2 proves that validators assessed exact bytes at an immutable GitHub commit,
that those bytes match the on-chain digest and package identity, and that the
artifact names the release creator as publisher. It does not prove that a binary
was distributed, that the artifact covers every source file, or software safety.

---

# Historical v1 Studionet results — superseded

These results belong only to contract
`0xfdA283EF4D39763ECbFf3BC739cBfB12fF5E3594`. They do not demonstrate the v2
artifact-binding remediation and must not be used as v2 resubmission evidence.

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
