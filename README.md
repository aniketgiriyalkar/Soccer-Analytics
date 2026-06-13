# Football Lab

Football Lab modernizes the original Soccer Analytics capstone into a
coverage-aware web application and reproducible data pipeline. The historical
2018 World Cup notebooks and StatsBomb open-data snapshot remain preserved at
the repository root.

## Product

The static Next.js application supports:

- Position-aware player comparisons across shooting, creation, progression,
  defending, duels, discipline, goalkeeping, and expected metrics.
- Team style and performance comparisons.
- Manager comparisons segmented by club tenure.
- Match shot maps and cumulative xG timelines.
- Neutral game-management analysis based on observed events, without claiming
  intent.
- Explicit competition, season, and metric coverage labels.
- A live architecture view covering sources, orchestration, quality gates,
  storage, notebooks, application builds, artifact promotion, portfolio sync,
  and GitHub Pages delivery.

The application exports with `/football-lab/` as its base path so the portfolio
can publish it at `aniketgiriyalkar.github.io/football-lab/`.

## Web Development

```bash
npm install
npm run dev
```

Validate and export:

```bash
npm run check
```

The static application is written to `out/`.

## Data Pipeline

Install the package:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Historical Understat backfill:

```bash
football-lab backfill \
  --league premier-league \
  --from-season 2014 \
  --to-season 2025 \
  --include-shots
```

Other commands:

```bash
football-lab refresh-current
football-lab refresh-season --league la-liga --season 2020
football-lab rebuild-aggregates
football-lab audit-coverage
football-lab export-schema
football-lab publish-frontend
```

Understat is used for domestic-league expected metrics and shot data. The
football-data.org adapter supplements fixtures, tables, and Champions League
structure when `FOOTBALL_DATA_API_KEY` is configured. Raw responses are cached,
normalized data is partitioned as Parquet, and DuckDB provides notebook access.

## Data Integrity

- Source-specific payloads remain behind provider adapters.
- Ingestion is cache-backed, idempotent, and restartable by league-season.
- Provider xG is preserved separately from observed goals.
- Missing metrics remain unavailable rather than being estimated silently.
- Discipline is factual; game-management indicators are descriptive proxies.
- Manager outcomes are reported with tenure and sample-size context.

The committed JSON dataset is a clearly labelled demonstration snapshot. The
scheduled and manually dispatched workflows produce validated provider-backed
artifacts without committing raw caches or large Parquet files.

## Automation

- `validate.yml` runs Python and web checks on pushes and pull requests.
- `ingest.yml` refreshes active seasons daily and supports historical backfills.
- After validation, `ingest.yml` commits only `public/data/*.json` to `master`
  using the `football-lab-data-bot` identity. Raw responses, checkpoints,
  Parquet, and DuckDB remain private workflow artifacts.
- Normalized Parquet and checkpoints use a rolling Actions cache so manual
  historical backfills remain available to subsequent daily refreshes.
- A changed snapshot also updates the `football-lab-latest` release. The
  portfolio independently checks this validated release on its daily schedule
  and atomically republishes `/football-lab/`, so no cross-repository token is
  stored.
- `promote.yml` publishes a last-known-good static ZIP to the
  `football-lab-latest` release.

### GitHub Actions secrets

Authenticate the GitHub CLI, then run the interactive setup:

```bash
gh auth login
./scripts/configure-github-secrets.sh
```

The script reads values without echoing them and uploads them directly to the
`Soccer-Analytics` repository. It does not write a local credentials file.
`FOOTBALL_DATA_API_KEY` and `API_FOOTBALL_KEY` are optional supplemental data
providers. They are exposed only to the ingestion commands that require them,
not to validation, frontend builds, or third-party publishing steps.

Local `.env` files, private key material, and common secret-file patterns are
ignored. `.env.example` contains names only and is safe to commit.
