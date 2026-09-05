# V2 deployed-source verification

Local remediation gates and deployed-source parity pass. The exact frozen source
was deployed with no constructor arguments at
`0x118f353B758ca1B26d07ec1082B12495107Cf5b3`.

- Frozen v2 source SHA-256:
  `24c3b47811ff42d3733edfbd49259f3ed04770ea1171f1c425c153c81ac6298a`
- Frozen source revision:
  [`c199fa1b2eab1b8daa76c86ebe448f1c6dfac1f6`](https://github.com/dearmore5382/SemVer-Sentinel/blob/c199fa1b2eab1b8daa76c86ebe448f1c6dfac1f6/contracts/SemVerSentinel.py)
- Public surface: 4 write methods, 2 view methods.
- External source: exact commit-pinned GitHub raw JSON only.

## V2 mechanism

- Canonical commit-pinned GitHub artifact only.
- URL-derived package and commit identity.
- Artifact publisher must match creator wallet.
- Validator-recomputed SHA-256 over exact fetched bytes.
- Exact schema, package, versions and policy binding.
- Closed semantic observations and deterministic compliance.
- Fail-closed rejection or retry without mutation.

## Historical deployment

`0xfdA283EF4D39763ECbFf3BC739cBfB12fF5E3594` is superseded v1. Its
transactions do not prove v2 and must not be the resubmission deployment.
