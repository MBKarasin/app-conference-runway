# Public publication

Owner authorization: October 17, 2026. Website and repository public; owner contributions MIT licensed. Purpose: exchange of ideas and promotion of human health. See LICENSE and THIRD_PARTY_NOTICES.md.

## How the main domain is published (since October 19, 2026)

One source, one site. The nightly workflow (`.github/workflows/runway.yml`) checks organizer sources, rebuilds `site/`, validates it and commits the result to `main`. GitHub Pages publishes https://appconferencerunway.org/ from `site/` on `main` at the end of each run; the domain's DNS at Cloudflare points to GitHub Pages. A curator push is rebuilt and committed by the same workflow. `.github/workflows/freshness.yml` fails, and notifies the owner, when the live site has not updated in 30 hours.

The October 17 manual reconciliation is carried into every build through `sources/curated.json`. The earlier hand-uploaded Cloudflare snapshot is retired and archived under `archive/`; every later version stays in the repository history and the daily data archive in `data/snapshots/`.

## Search discovery

robots.txt allows crawling and references sitemap.xml. The canonical domain is https://appconferencerunway.org/. Search engines decide whether and when to index.
