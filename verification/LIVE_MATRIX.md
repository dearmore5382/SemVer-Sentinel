# Frozen v2 live matrix — execute only after user deployment

The artifacts are published at immutable revision
`c199fa1b2eab1b8daa76c86ebe448f1c6dfac1f6`. The byte lengths and SHA-256
values below were independently recomputed after fetching the public raw URLs.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| [`additive-minor.json`](https://raw.githubusercontent.com/dearmore5382/SemVer-Sentinel/c199fa1b2eab1b8daa76c86ebe448f1c6dfac1f6/fixtures/artifacts/additive-minor.json) | 502 | `12032ff8f4d678650ad67434a000dca2044226fcbadd2fcd777b5197dc9d73d8` |
| [`breaking-major.json`](https://raw.githubusercontent.com/dearmore5382/SemVer-Sentinel/c199fa1b2eab1b8daa76c86ebe448f1c6dfac1f6/fixtures/artifacts/breaking-major.json) | 479 | `5a80f119d002c5b0f9ae47f4185df6794d821e52ebe87a6719badf9d3a6a6d32` |
| [`prompt-injection-patch.json`](https://raw.githubusercontent.com/dearmore5382/SemVer-Sentinel/c199fa1b2eab1b8daa76c86ebe448f1c6dfac1f6/fixtures/artifacts/prompt-injection-patch.json) | 525 | `be9e1e09edf2d22358c78eecec4cc3186f8787374296362f6d6a4f2246dd3b1c` |
| [`wrong-authority.json`](https://raw.githubusercontent.com/dearmore5382/SemVer-Sentinel/c199fa1b2eab1b8daa76c86ebe448f1c6dfac1f6/fixtures/artifacts/wrong-authority.json) | 502 | `7a7dbf8b59b12b11f055549df755baee9439a17f8822bf344075899f51d145b9` |
| [`wrong-package.json`](https://raw.githubusercontent.com/dearmore5382/SemVer-Sentinel/c199fa1b2eab1b8daa76c86ebe448f1c6dfac1f6/fixtures/artifacts/wrong-package.json) | 506 | `db264be2680eeac65b33520eecce91af102a68a043bfee7faf30fa3b35808413` |

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
