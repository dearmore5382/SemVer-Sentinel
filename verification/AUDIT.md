# Adversarial audit — local and Studionet evidence

## Scope and result

The audit covers the exact contract source identified in
`DEPLOYMENT_READINESS.md`. It includes local happy paths, expected failures and
multi-input adversarial combinations plus the corresponding Studionet matrix.

## Happy paths

- additive minor release -> `NON_BREAKING / COMPLIANT`;
- breaking major release -> `BREAKING / COMPLIANT`;
- documentation-only patch -> `DOC_ONLY / COMPLIANT`;
- full `DRAFT -> SEALED -> REVIEWED` persistence and readback.

## Failure paths

- invalid, equal, decreasing and prerelease version strings rejected before state;
- wrong publisher cannot seal or cancel;
- cancelled/reviewed records are terminal;
- malformed schema, invalid enum and oversized output become retryable without mutation;
- uncertainty becomes `REVIEW_REQUIRED`, not a fabricated compatibility claim.

## Adversarial combinations

- removal plus secondary uncertainty: substantive breaking evidence wins;
- documentation-only contradiction plus additive change: safe uncertainty wins;
- prompt-injection text plus newly required input: deterministic breaking outcome;
- same semantic effect with different nonconsequential model details does not
  require prose equality;
- replayed assessment cannot invoke the model after terminal review.

## Findings fixed before freeze

1. The initial tagged prompt allowed untrusted text to imitate closing markers.
   Inputs are now encoded as a JSON evidence object and explicitly treated as data.
2. The first precedence table allowed `documentation_only=YES` alongside an
   additive/API compatibility claim. Contradictory non-breaking observations now
   produce `REVIEW_REQUIRED`.
3. Frontend module declarations exposed three TypeScript boundary errors. Local
   explicit types and a string-normalized transaction hash fixed them.
4. The initial transaction reconciler did not decode the returned ID from
   `create_release`. It now verifies receipt identity, method, arguments, exact
   return and method-specific authoritative readback before marking any write
   verified.

## Live result and remaining boundaries

Deployment parity and the contract-level live matrix are complete. All 16 live
writes (15 planned writes and one separately authorized retry) finalized with
majority agreement. The first A2 assessment exercised the designed unavailable
branch and preserved `SEALED`; the single retry reached the frozen expected
result. This is evidence for these fixtures and this deployment, not a guarantee
that every future model call succeeds or that publisher-authored snapshots match
an external repository or shipped service. Browser-wallet end-to-end execution
has not been used as audit evidence.
