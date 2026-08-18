# GitHub Upload and Release Guide

## Double-blind warning

Do not publish the anonymous repository from an account, organization, commit history, issue tracker, or profile that reveals the authors. If the venue permits anonymous external artifacts, use a venue-approved anonymous repository workflow. Replace anonymous citation metadata only after the review policy allows author disclosure.

## Files prepared for upload

- `relation_aware_multichart_editing_repo_v1.zip`: extract this and upload its contents as the repository root.
- `relation_aware_multichart_public_v1.zip`: upload as a GitHub Release asset; do not commit it to Git.
- `anonymous_evaluation_artifact_public298_v1.zip`: upload as the same GitHub Release; do not commit it to Git.
- `RELEASE_SHA256SUMS.txt`: upload with the two archives.

## Suggested release

1. Create the repository and upload the extracted repository files.
2. Confirm that no author identity, API key, email address, local absolute path, or hidden Git history is present.
3. Create tag and release `v1.0.0`.
4. Attach both large ZIP files and `RELEASE_SHA256SUMS.txt`.
5. Download each asset once and verify its SHA-256 hash.
6. Send the repository URL back so the manuscript placeholder can be replaced in the anonymous and named versions.

GitHub rejects ordinary committed files above 100 MiB. The complete benchmark is therefore a Release asset. Each prepared archive is also checked against GitHub's per-asset size ceiling before delivery.
