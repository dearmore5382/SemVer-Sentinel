# Frozen v2 live matrix — execute only after user deployment

Before deployment, publish distinct artifacts in this repository and pin their
raw URLs to the commit containing them. Each file includes the authorized test
publisher and its exact SHA-256 is recomputed from fetched bytes.

| ID | Path | Expected result and readback |
| --- | --- | --- |
| H1 | authenticated additive minor | `REVIEWED / NON_BREAKING / COMPLIANT`; expected digest = actual digest |
| H2 | authenticated breaking major | `REVIEWED / BREAKING / COMPLIANT` |
| A1 | breaking patch with prompt injection | `REVIEWED / BREAKING / VERSION_VIOLATION` |
| F1 | branch `main` locator | `IMMUTABLE_GITHUB_ARTIFACT_REQUIRED`; count unchanged |
| F2 | deceptive GitHub hostname | `IMMUTABLE_GITHUB_ARTIFACT_REQUIRED`; count unchanged |
| F3 | correct URL with one-byte-wrong digest | `REJECTED / ARTIFACT_REJECTED / DIGEST_MISMATCH` |
| F4 | artifact publisher differs from creator | `REJECTED / ARTIFACT_REJECTED / AUTHORITY_MISMATCH` |
| F5 | artifact package differs from URL-derived package | `REJECTED / ARTIFACT_REJECTED / MANIFEST_INVALID` |
| R1 | missing pinned artifact | `ASSESSMENT_RETRYABLE`; record remains byte-for-byte `SEALED` |
| G1 | outsider seal/cancel | `PUBLISHER_ONLY`; no mutation |
| G2 | replay reviewed/rejected assessment | `RELEASE_NOT_ASSESSABLE`; no mutation |

For every write verify exact sender, recipient, calldata, hash, `FINALIZED`,
successful execution, `MAJORITY_AGREE`, exact return and authoritative readback.
Never automatically resubmit. Preserve every retry or failed attempt.

The frontend remains write-disabled until deployed-source parity and every
mandatory live case pass.
