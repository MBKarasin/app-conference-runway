# Public publication

Owner authorization: October 17, 2026. Website and repository public; owner contributions MIT licensed. Purpose: exchange of ideas and promotion of human health. See LICENSE and THIRD_PARTY_NOTICES.md.

## How the main domain is published (since October 19, 2026)

One source, one site. The nightly workflow (`.github/workflows/runway.yml`) checks organizer sources, rebuilds `site/`, validates it and commits the result to `main`. Cloudflare Pages is connected to this repository and publishes https://appconferencerunway.org/ from `site/` on every commit to `main`. A curator push is rebuilt and committed by the same workflow. `.github/workflows/freshness.yml` fails, and notifies the owner, when the live site has not updated in 30 hours.

The October 17 manual reconciliation is carried into every build through `sources/curated.json`. Earlier copies (the hand-uploaded Cloudflare snapshot and the GitHub Pages copy) are retired and archived under `archive/`; every later version stays in the repository history and the daily data archive in `data/snapshots/`.

## Search discovery

robots.txt allows crawling and references sitemap.xml. The canonical domain is https://appconferencerunway.org/. Search engines decide whether and when to index.
