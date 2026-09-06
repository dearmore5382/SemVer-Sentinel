# V3 Studionet results

The checkpointed nine-step matrix completed on contract
`0xd44DF7b3D9bdD91731D46801E8a7eb057640be0E`. Every recorded transaction reached
`FINALIZED / MAJORITY_AGREE`, returned the documented value and passed
authoritative contract readback.

## Real-package happy workflow

`p-limit` versions `3.0.0` and `3.1.0` were supplied only as package/version
coordinates. The contract derived both npm metadata and canonical tarball URLs,
verified npm SHA-512 integrity, extracted the shipped declaration sources and
persisted both integrity values plus both source SHA-256 values.

The assessment returned `BREAKING / VERSION_VIOLATION`: validators found an
incompatible declaration replacement under a minor bump. This is a successful
workflow outcome, not a claim that the releases are compatible.

- create: `0xe98a915924f2dfeff0c6b71c08b880ab2f14e1a6645c1c048bf90369c534ca87`
- seal: `0xc7d0313af7e22f2c4d523e246dd8af277ede01d8f942010740b990c5635b301b`
- successful assessment: `0xca5782f03d79a7de75e838d7b95cba7e273b098f613fe15b0312beeace5e2491`

The first assessment returned `ASSESSMENT_RETRYABLE` at
`0xb8469a726e88421fe759c109d6c2123c52370cb877eb7540ad062e20dbbe1f59`;
readback remained `SEALED / UNEVALUATED`. One documented retry was performed.

## Failure and adversarial paths

- malformed package input rejected with count unchanged;
- outsider could not seal the owner's release;
- assessment replay was rejected;
- a deliberately nonexistent npm package produced terminal
  `REGISTRY_INVALID / ARTIFACT_REJECTED`.

The full sanitized journal is
`live-matrix-0xd44df7b3d9bdd91731d46801e8a7eb057640be0e.json`.

## Evidence boundary

These records prove the assessed declaration bytes came from the integrity-
verified npm tarballs observed by validators. They do not establish runtime
behavior, malware safety, legal maintainer identity, or compatibility outside
the exported TypeScript declaration surface.
