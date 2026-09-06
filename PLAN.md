# SemVer Sentinel v3 remediation plan

1. Convert the second steward rejection into a shipped-artifact proof obligation.
2. Remove publisher-authored API descriptions, locators and digests from input.
3. Restrict v3 to exact npm releases with bounded TypeScript declarations.
4. Derive registry metadata and tarball URLs inside the contract.
5. Verify package/version identity and npm-published SHA-512 over tarball bytes.
6. Extract the declaration entrypoint from the verified release tarball.
7. Make validators repeat acquisition, verification, extraction and classification.
8. Persist and consensus-check tarball integrity plus extracted-source hashes.
9. Pass local happy, failure, adversarial, GenVM and frontend gates.
10. Freeze and push the pre-deploy source; stop for user deployment.
11. After deployment, verify source parity and run real npm live cases before
    wiring or publishing the frontend and before claiming submission readiness.
