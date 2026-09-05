# V2 adversarial audit

The remediation is locally verified. Live claims remain open until deployment.

## Happy paths

- authenticated additive minor -> `NON_BREAKING / COMPLIANT`;
- authenticated breaking major -> `BREAKING / COMPLIANT`;
- package, commit, expected digest and validator digest persist together.

## Failure and adversarial paths

- mutable branch and deceptive origin rejected before state;
- one-byte digest mismatch, publisher mismatch and object mismatch produce
  terminal `ARTIFACT_REJECTED`;
- unavailable source/model is retryable with sealed state unchanged;
- wrong actor, wrong state and replay cannot bypass lifecycle;
- prompt injection plus a newly required input produces `VERSION_VIOLATION`;
- semantic output cannot override failed provenance.

## Honest boundary

The GitHub coordinate is the package identity for this protocol. A committed
wallet binds the on-chain publisher to that artifact. This is not GitHub OAuth,
package-registry verification, complete Git-tree attestation, malware analysis
or proof of distribution.
