# SemVer Sentinel v2 remediation plan

1. Translate steward feedback into a provenance proof obligation.
2. Replace free-form snapshots with a commit-pinned GitHub artifact.
3. Derive package/commit identity from an exact canonical locator.
4. Bind artifact publisher to the transaction sender.
5. Make every validator fetch and SHA-256 the exact adjudicated bytes.
6. Fail closed for digest, schema, authority and object mismatch.
7. Preserve retry without mutation for source/model unavailability.
8. Run semantic, Direct Mode, provenance bypass and frontend gates.
9. Freeze source hash and live matrix before deployment.
10. Stop and ask the user to deploy the exact v2 source.
11. After deployment, run the frozen matrix, wire the frontend and publish new
    evidence. Mark the original contract as superseded; never erase its history.
