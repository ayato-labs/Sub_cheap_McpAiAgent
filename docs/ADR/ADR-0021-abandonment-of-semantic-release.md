# ADR-0021: Abandonment of Semantic Release

## Status
Accepted

## Context
We previously used `python-semantic-release` to automate versioning and changelog generation. However, it required direct pushes to the `main` branch to commit version bumps and push tags. Our repository security policy enforces strict branch protection rules on `main`, requiring all changes to be made through pull requests (GH013 violation).

While potential workarounds exist (such as using Personal Access Tokens (PATs) to bypass protections or configuring complex pull-request-based release flows), these introduce significant management overhead, security risks (managing PAT secrets), or fragility in the automation pipeline.

## Decision
We have decided to abandon `python-semantic-release` and remove the associated automation workflow.

## Consequences
- **Pros**:
  - Removed dependency on complex release automation that conflicted with our security policies.
  - Simplified repository maintenance.
- **Cons**:
  - Versioning and changelog updates must now be managed manually or through a different, less intrusive mechanism.
  - Lost automated GitHub Release creation.

Manual releases will be performed by updating `pyproject.toml` and tagging the repository directly during the release process.
