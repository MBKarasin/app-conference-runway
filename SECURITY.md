# Security

This repository and its owner-authored code are public under MIT. Public reading and reuse do not grant write or deployment access.

Never commit passwords, private keys, deployment tokens, private records, or local systems inventories. Keep credentials in platform-managed secrets with the minimum needed scope. Do not paste credentials into issue reports.

Workflows use explicit job permissions and commit-pinned external actions. Source checks and publishing run on GitHub-hosted runners; external pull requests must not receive publishing credentials. Review workflow changes before merging.

A source-reader failure is an operational data-quality exception, not a security incident. See data/manual-review.json and data/check_report.md for reconciled source evidence.

For security concerns, contact the repository owner privately using the contact route on the public website. Avoid public reports containing exploitable details or secrets.
