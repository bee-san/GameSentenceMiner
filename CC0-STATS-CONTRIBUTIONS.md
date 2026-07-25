# CC0 dedication for Autumn Skerritt's statistics contributions

Effective 25 July 2026, Autumn Skerritt ("Affirmer") applies
[CC0 1.0 Universal](LICENSES/CC0-1.0.txt) to every copyrightable
statistics-related contribution in this repository for which the Affirmer owns
the applicable Copyright and Related Rights.

Those contributions remain available under the repository's existing
GPL-3.0 terms as well. A recipient may therefore use a covered contribution
under the existing GPL terms **or** under the CC0 waiver and public-license
fallback.

## Contributor identities

The Git audit found the Affirmer's statistics work under these identities:

- `Autumn (Bee) <github@skerritt.blog>`
- `Autumn Skerritt <skerraut@amazon.com>`
- `bee <autumn@skerritt.blog>`
- `bee <github@skerritt.blog>`

Identity metadata is evidence used to locate contributions; the dedication
also covers a contribution the Affirmer can prove they authored and own even
if an import, squash, or merge changed its recorded identity.

## Exact scope

The covered work is the Affirmer-authored portion of commits present in this
fork's Git object graph on the effective date that implements, tests,
documents, styles, or configures statistics, dashboards, goals, heatmaps,
rollups, Anki statistics, reading/mining analytics, or statistics export.

The principal path families are:

- `GameSentenceMiner/util/**/*stat*`, including rollups and third-party stats;
- `GameSentenceMiner/web/**/*stat*`, `**/*dashboard*`, `**/*goal*`,
  `**/*heatmap*`, and their templates, CSS, JavaScript, and API/repository
  support;
- statistics-related database migrations, cron jobs, config, images, and
  Jiten integration;
- `scripts/benchmark_stats.py`;
- `tests/**/*stat*`, and tests whose subject is a covered dashboard, goal,
  heatmap, rollup, or statistics integration.

This path list locates the work but does not turn an entire mixed-authorship
file into CC0. In a covered file, the dedication reaches only the
copyrightable lines, blocks, tests, documentation, and other expression owned
by the Affirmer.

Representative audited commits include:

- `b36aedf7ebc2dbfc578621345f54363560528b57` — Add stats
- `63838e097d722d207684251626c65b57f6c59457` — complete refactor of stats
- `9e7834cbc5d5993c0c26dee8e46bda77e06454cf` — add better export csv
- `b71c2868fa8b36d72722f4ac468223bc94e8450c` — stats
- `d91dffdd8d3f582d3fea777323578a3c59bc3117` — stats rollup
- `72e94349ba9f64c945ab718a4e805753dfb006a5` — initial goals
- `cfbfb6e0967493d75cdfa1bd268411670ad4bfed` — Add new Anki & GSM stats page
- `4fc9390be90c529afb149d98d43aaf1177074f65` — daily streak, mining efficiency, and character frequency charts
- `670bb9f7f9f427aa9a0fb3490dd71c10d023fb4b` — reading activity heatmap and reading speed chart

The complete set is determined from Git, not only this representative list:
a commit is included when it is present in the fork on the effective date,
uses one of the audited identities (or is otherwise provably owned by the
Affirmer), and its diff satisfies the statistics-purpose and path scope above.

## Exclusions and file notices

This declaration does not apply to:

- code, art, documentation, or data authored or owned by another person;
- another contributor's portion of a co-authored, merged, or later-modified
  file;
- third-party dependencies, generated artifacts, trademarks, patent rights,
  privacy/publicity rights, or content for which the Affirmer cannot grant
  rights.

Because the audited statistics files have mixed histories, this change adds no
file-wide `SPDX-License-Identifier: CC0-1.0` notices. Such a notice may be added
later only where Git and authorship review establish that the whole file is
covered. The repository-wide GPL license continues to govern everything not
expressly covered by this declaration or another notice.

