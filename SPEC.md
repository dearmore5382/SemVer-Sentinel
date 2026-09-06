# SemVer Sentinel v3 specification

## Steward remediation

V2 authenticated a publisher-authored JSON manifest, not the software that
shipped. V3 removes API descriptions, evidence URLs and digests from caller
input. The caller supplies only an npm package, two exact SemVer versions and a
policy.

## Proof obligation

For two exact releases of one npm package, establish from npm registry authority
that each version exists, fetch its canonical release tarball, recompute the
registry-published SHA-512 integrity, extract the shipped TypeScript declaration
file, and semantically compare those shipped declarations. Only verified source
may produce a compatibility result.

## Evidence chain

1. Contract constructs `registry.npmjs.org/<package>/<version>`; caller cannot
   choose the origin or URL.
2. Metadata must name the exact package and version.
3. `dist.tarball` must equal the contract-derived canonical npm tarball URL.
4. `dist.integrity` must be `sha512-*` and match the fetched tarball bytes.
5. The `types`/`typings` path (or npm's conventional `index.d.ts`) must exist
   inside that verified tarball and remain within size bounds.
6. Validators compare only the extracted old/new declarations.
7. Successful readback persists both npm `dist.integrity` values and SHA-256 of
   both extracted declaration byte sequences. Validators require exact binding
   equality in addition to deterministic outcome equality.

`REGISTRY_INVALID`, `INTEGRITY_MISMATCH`, and `SOURCE_MISSING` produce terminal
`ARTIFACT_REJECTED`. Network/model unavailability produces
`ASSESSMENT_RETRYABLE` without state mutation.

## AI and consensus boundary

AI returns closed observations about export, parameter, input, return and
behavior compatibility. It cannot set registry facts, integrity, package,
versions, SemVer compliance or lifecycle state. Validators independently repeat
registry fetch, integrity verification, extraction and classification;
equivalence compares deterministic consequence.

## Scope

V3 deliberately supports npm releases with a declaration entry point and
tarballs no larger than 300 KB. It proves assessment of declarations shipped in
the registry release tarballs. It does not prove runtime implementation behavior,
malware safety, maintainer legal identity, or compatibility outside the exported
declaration surface.
