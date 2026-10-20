# Retired publishing inputs

The one-time bootstrap workflow is preserved here as history. It is outside .github/workflows and cannot be run as a GitHub workflow. It must not unpack an old bundle over the current source.

The only active publishing workflow is .github/workflows/runway.yml, using main's sources/ and scripts/ to build site/. GitHub Pages serves https://appconferencerunway.org/.

Daily source checking is scheduled for 04:00 America/New_York, including DST. The existing freshness workflow checks the live result; it does not publish. Archived production snapshots and local recovery copies are historical evidence, not alternate publication sources.
