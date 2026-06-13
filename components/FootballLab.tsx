"use client";

import { useMemo, useState } from "react";
import { formatMetric, scoreColor } from "@/lib/analytics";
import type {
  FootballLabData,
  Manager,
  Metric,
  PipelineStage,
  Player,
  Shot,
  Team,
} from "@/types/analytics";

type View =
  | "overview"
  | "players"
  | "teams"
  | "managers"
  | "match"
  | "coverage"
  | "architecture";

const PLAYER_COLORS = ["#63e6be", "#8c7cff", "#ffb454", "#69c7ff", "#ff786d"];
const PRIMARY_PLAYER_METRICS = [
  "goals_per90",
  "xg_per90",
  "xa_per90",
  "key_passes_per90",
  "progressive_actions_per90",
  "duel_win_pct",
  "recoveries_per90",
  "cards_per90",
];

export function FootballLab({ initialData }: { initialData: FootballLabData }) {
  const [view, setView] = useState<View>("overview");
  const [competition, setCompetition] = useState("All competitions");
  const [season, setSeason] = useState("2025/26");
  const competitions = [
    "All competitions",
    ...new Set(initialData.coverage.map((row) => row.competition)),
  ];
  const seasons = [...new Set(initialData.coverage.map((row) => row.season))].sort().reverse();
  const visibleData = useMemo<FootballLabData>(() => {
    const competitionMatches = (value: string) =>
      competition === "All competitions" || value === competition;
    return {
      ...initialData,
      players: initialData.players.filter(
        (player) => competitionMatches(player.competition) && player.season === season,
      ),
      teams: initialData.teams.filter(
        (team) => competitionMatches(team.competition) && team.season === season,
      ),
      managers:
        season === "2025/26"
          ? initialData.managers.filter((manager) => competitionMatches(manager.competition))
          : [],
      shots:
        season === "2025/26" &&
        (competition === "All competitions" || competition === "Premier League")
          ? initialData.shots
          : [],
      coverage: initialData.coverage.filter(
        (row) => competitionMatches(row.competition) && row.season === season,
      ),
    };
  }, [competition, initialData, season]);

  return (
    <main>
      <header className="lab-header">
        {/* This intentionally leaves the /football-lab base path. */}
        {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
        <a className="brand" href="/">
          <span className="brand-mark">AG</span>
          <span>
            Football Lab
            <small>European performance intelligence</small>
          </span>
        </a>
        {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
        <a className="portfolio-link" href="/">
          Portfolio <span aria-hidden="true">↗</span>
        </a>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Football / Data / Context</p>
          <h1>Performance is never <em>one number.</em></h1>
          <p>
            Compare players, teams, matches, and managers through shooting,
            creation, progression, defending, discipline, expected performance,
            and game-state context.
          </p>
        </div>
        <div className="hero-status" aria-label="Data status">
          <span className="live-dot" />
          <div>
            <strong>{initialData.manifest.status}</strong>
            <small>Data build {initialData.manifest.dataVersion}</small>
          </div>
        </div>
      </section>

      <div className="control-bar">
        <nav className="view-tabs" aria-label="Analytics views">
          {(
            [
              ["overview", "Overview"],
              ["players", "Players"],
              ["teams", "Teams"],
              ["managers", "Managers"],
              ["match", "Match centre"],
              ["coverage", "Coverage"],
              ["architecture", "Architecture"],
            ] as [View, string][]
          ).map(([key, label]) => (
            <button
              className={view === key ? "active" : ""}
              key={key}
              onClick={() => setView(key)}
              type="button"
            >
              {label}
            </button>
          ))}
        </nav>
        <div className="filters">
          <label>
            <span>Competition</span>
            <select value={competition} onChange={(event) => setCompetition(event.target.value)}>
              {competitions.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Season</span>
            <select value={season} onChange={(event) => setSeason(event.target.value)}>
              {seasons.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <section id="analysis" className="analysis-shell">
        {view === "overview" && <Overview data={visibleData} />}
        {view === "players" && <PlayerCompare data={visibleData} />}
        {view === "teams" && <TeamCompare data={visibleData} />}
        {view === "managers" && <ManagerCompare data={visibleData} />}
        {view === "match" && <MatchCentre shots={visibleData.shots} />}
        {view === "coverage" && <CoveragePanel data={visibleData} />}
        {view === "architecture" && <ArchitecturePanel data={initialData} />}
      </section>

      <footer>
        <p>{initialData.manifest.disclaimer}</p>
        <p>
          Sources are attributed per dataset. Derived metrics are descriptive,
          not claims of intent or causation.
        </p>
      </footer>
    </main>
  );
}

function SectionHeading({
  eyebrow,
  title,
  copy,
}: {
  eyebrow: string;
  title: string;
  copy: string;
}) {
  return (
    <div className="section-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      <p>{copy}</p>
    </div>
  );
}

function Overview({ data }: { data: FootballLabData }) {
  const cards = [
    ["5", "Domestic leagues", "Backfill-ready from 2014/15"],
    ["8", "Position groups", "Role-specific comparison templates"],
    ["10", "Metric categories", "Expected and observed performance"],
    ["1", "European competition", "Champions League coverage-aware"],
  ];
  const topPlayers = [...data.players]
    .sort((a, b) => (b.percentiles.xg_per90 ?? 0) - (a.percentiles.xg_per90 ?? 0))
    .slice(0, 5);
  if (!data.players.length || !data.teams.length) {
    return <EmptyDataset title="No published analytical snapshot for this selection." />;
  }

  return (
    <>
      <SectionHeading
        eyebrow="Command centre"
        title="A wider view of the game."
        copy="Every insight carries its denominator, peer group, source coverage, and freshness. Expected metrics sit beside observed actions rather than replacing them."
      />
      <div className="stat-grid">
        {cards.map(([value, label, note]) => (
          <article className="stat-card" key={label}>
            <strong>{value}</strong>
            <h3>{label}</h3>
            <p>{note}</p>
          </article>
        ))}
      </div>
      <div className="dashboard-grid">
        <article className="panel span-7">
          <PanelTitle title="Attacking output" note="Position percentiles · per 90" />
          <ScatterPlot
            players={data.players}
            xKey="xg_per90"
            xLabel="Expected goals / 90"
            yKey="xa_per90"
            yLabel="Expected assists / 90"
          />
        </article>
        <article className="panel span-5">
          <PanelTitle title="Player radar" note="Multi-category profile" />
          <RadarChart
            player={data.players[0]}
            metrics={data.metrics.filter((metric) =>
              PRIMARY_PLAYER_METRICS.slice(0, 6).includes(metric.key),
            )}
          />
        </article>
        <article className="panel span-7">
          <PanelTitle title="Team performance trajectory" note="Rolling five-match points" />
          <LineChart teams={data.teams.slice(0, 4)} />
        </article>
        <article className="panel span-5">
          <PanelTitle title="xG leaders" note="One signal among many" />
          <div className="rank-list">
            {topPlayers.map((player, index) => (
              <div key={player.id}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <strong>{player.name}</strong>
                  <small>{player.team} · {player.position}</small>
                </div>
                <b>{player.metrics.xg_per90.toFixed(2)}</b>
              </div>
            ))}
          </div>
        </article>
      </div>
    </>
  );
}

function PlayerCompare({ data }: { data: FootballLabData }) {
  const [position, setPosition] = useState("All positions");
  const eligible = data.players.filter(
    (player) => position === "All positions" || player.position === position,
  );
  const [selectedIds, setSelectedIds] = useState(data.players.slice(0, 3).map((player) => player.id));
  const [category, setCategory] = useState("All");
  const selected = data.players.filter((player) => selectedIds.includes(player.id)).slice(0, 5);
  const categories = ["All", ...new Set(data.metrics.map((metric) => metric.category))];
  const metrics = data.metrics.filter(
    (metric) =>
      PRIMARY_PLAYER_METRICS.includes(metric.key) &&
      (category === "All" || metric.category === category),
  );
  if (!data.players.length) {
    return <EmptyDataset title="Player comparisons are awaiting an ingested dataset." />;
  }

  function togglePlayer(id: string) {
    setSelectedIds((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : current.length < 5
          ? [...current, id]
          : current,
    );
  }

  return (
    <>
      <SectionHeading
        eyebrow="Role-aware comparison"
        title="Compare what the role demands."
        copy="Select up to five players. Values are shown per 90 with position-specific percentiles and a 900-minute sample floor."
      />
      <div className="selection-panel">
        <div className="chip-row" aria-label="Position filter">
          {["All positions", ...new Set(data.players.map((player) => player.position))].map((item) => (
            <button
              className={position === item ? "active" : ""}
              key={item}
              onClick={() => setPosition(item)}
              type="button"
            >
              {item}
            </button>
          ))}
        </div>
        <div className="player-picker">
          {eligible.map((player) => (
            <label className={selectedIds.includes(player.id) ? "selected" : ""} key={player.id}>
              <input
                checked={selectedIds.includes(player.id)}
                onChange={() => togglePlayer(player.id)}
                type="checkbox"
              />
              <span>{initials(player.name)}</span>
              <div>
                <strong>{player.name}</strong>
                <small>{player.team} · {player.minutes.toLocaleString()} min</small>
              </div>
            </label>
          ))}
        </div>
      </div>
      <div className="category-select">
        <span>Metric family</span>
        <select value={category} onChange={(event) => setCategory(event.target.value)}>
          {categories.map((item) => <option key={item}>{item}</option>)}
        </select>
      </div>
      <div className="dashboard-grid">
        <article className="panel span-5">
          <PanelTitle title="Percentile fingerprint" note="Compared with positional peers" />
          {selected[0] && <RadarChart player={selected[0]} metrics={metrics.slice(0, 6)} />}
        </article>
        <article className="panel span-7">
          <PanelTitle title="Metric comparison" note="Raw values and positional percentile" />
          <MetricBars players={selected} metrics={metrics} />
        </article>
        <article className="panel span-12 table-panel">
          <PanelTitle title="Comparison matrix" note="No hidden composite score" />
          <ComparisonTable players={selected} metrics={metrics} />
        </article>
      </div>
    </>
  );
}

function TeamCompare({ data }: { data: FootballLabData }) {
  const [teamIds, setTeamIds] = useState(data.teams.slice(0, 3).map((team) => team.id));
  const selected = data.teams.filter((team) => teamIds.includes(team.id));
  const metrics = [
    ["goals_per_match", "Goals / match"],
    ["xg_per_match", "xG / match"],
    ["shots_per_match", "Shots / match"],
    ["possession_pct", "Possession %"],
    ["progressive_actions", "Progressive actions"],
    ["ppda", "PPDA"],
    ["cards_per_match", "Cards / match"],
    ["restart_delay_seconds", "Restart delay"],
  ];
  if (!data.teams.length) {
    return <EmptyDataset title="Team comparisons are awaiting an ingested dataset." />;
  }

  return (
    <>
      <SectionHeading
        eyebrow="Team intelligence"
        title="Style, output, control, and conduct."
        copy="Compare attacking and defensive output alongside possession, progression, discipline, and neutral game-management indicators."
      />
      <div className="chip-row teams">
        {data.teams.map((team) => (
          <button
            className={teamIds.includes(team.id) ? "active" : ""}
            key={team.id}
            onClick={() =>
              setTeamIds((current) =>
                current.includes(team.id)
                  ? current.filter((id) => id !== team.id)
                  : current.length < 4
                    ? [...current, team.id]
                    : current,
              )
            }
            type="button"
          >
            {team.name}
          </button>
        ))}
      </div>
      <div className="dashboard-grid">
        <article className="panel span-7">
          <PanelTitle title="Team style map" note="Chance creation vs defensive disruption" />
          <TeamScatter teams={selected} />
        </article>
        <article className="panel span-5">
          <PanelTitle title="Recent trajectory" note="Rolling five-match points" />
          <LineChart teams={selected} />
        </article>
        <article className="panel span-12 table-panel">
          <PanelTitle
            title="Team comparison"
            note="Restart delay is descriptive context, not proof of intent"
          />
          <TeamTable teams={selected} metrics={metrics} />
        </article>
      </div>
    </>
  );
}

function ManagerCompare({ data }: { data: FootballLabData }) {
  const [selected, setSelected] = useState(data.managers.slice(0, 3).map((manager) => manager.id));
  const managers = data.managers.filter((manager) => selected.includes(manager.id));
  const metrics = [
    ["points_per_game", "Points / game"],
    ["xg_difference_per90", "xG difference / 90"],
    ["win_pct", "Win rate"],
    ["sub_first_minute", "First substitution"],
    ["sub_goal_contributions", "Substitute goal contributions"],
    ["cards_per_match", "Team cards / match"],
    ["restart_delay_seconds", "Restart delay"],
  ];
  if (!data.managers.length) {
    return <EmptyDataset title="Manager tenures are not available for this selection." />;
  }

  return (
    <>
      <SectionHeading
        eyebrow="Tenure analysis"
        title="Compare decisions in context."
        copy="Manager records are segmented by club tenure and normalized by match count. Team outcomes are not treated as proof of individual causation."
      />
      <div className="manager-cards">
        {data.managers.map((manager) => (
          <button
            className={selected.includes(manager.id) ? "selected" : ""}
            key={manager.id}
            onClick={() =>
              setSelected((current) =>
                current.includes(manager.id)
                  ? current.filter((id) => id !== manager.id)
                  : current.length < 4
                    ? [...current, manager.id]
                    : current,
              )
            }
            type="button"
          >
            <span>{initials(manager.name)}</span>
            <strong>{manager.name}</strong>
            <small>{manager.club}</small>
            <em>{manager.tenure}</em>
          </button>
        ))}
      </div>
      <div className="dashboard-grid">
        <article className="panel span-7">
          <PanelTitle title="Tenure fingerprint" note="Output, control, discipline, substitutions" />
          <ManagerBars managers={managers} metrics={metrics} />
        </article>
        <article className="panel span-5">
          <PanelTitle title="Match-state management" note="Share of substitutions by state" />
          <DonutChart managers={managers} />
        </article>
        <article className="panel span-12 table-panel">
          <PanelTitle title="Manager comparison" note="Minimum sample: 20 matches" />
          <ManagerTable managers={managers} metrics={metrics} />
        </article>
      </div>
    </>
  );
}

function MatchCentre({ shots }: { shots: Shot[] }) {
  if (!shots.length) {
    return <EmptyDataset title="No shot-level match is published for this selection." />;
  }
  const home = shots.filter((shot) => shot.team === "Arsenal FC");
  const away = shots.filter((shot) => shot.team !== "Arsenal FC");
  const homeXg = home.reduce((sum, shot) => sum + shot.xg, 0);
  const awayXg = away.reduce((sum, shot) => sum + shot.xg, 0);
  return (
    <>
      <SectionHeading
        eyebrow="Match centre"
        title="See how the match developed."
        copy="Shot quality, score events, discipline, substitutions, and stoppages are presented on a common timeline."
      />
      <div className="scoreboard">
        <div><strong>Arsenal FC</strong><span>{home.filter((shot) => shot.result === "Goal").length}</span><small>{homeXg.toFixed(2)} xG</small></div>
        <em>FT</em>
        <div><strong>Manchester Blue</strong><span>{away.filter((shot) => shot.result === "Goal").length}</span><small>{awayXg.toFixed(2)} xG</small></div>
      </div>
      <div className="dashboard-grid">
        <article className="panel span-7">
          <PanelTitle title="Shot map" note="Marker size represents xG" />
          <ShotMap shots={shots} />
        </article>
        <article className="panel span-5">
          <PanelTitle title="Shot ledger" note={`${shots.length} attempts`} />
          <div className="shot-ledger">
            {[...shots].sort((a, b) => a.minute - b.minute).map((shot) => (
              <div key={shot.id}>
                <span>{shot.minute}&apos;</span>
                <i className={shot.result.toLowerCase()} />
                <div><strong>{shot.player}</strong><small>{shot.situation} · {shot.result}</small></div>
                <b>{shot.xg.toFixed(2)}</b>
              </div>
            ))}
          </div>
        </article>
        <article className="panel span-12">
          <PanelTitle title="Cumulative xG" note="Goals shown as event markers" />
          <XgTimeline shots={shots} />
        </article>
      </div>
    </>
  );
}

function CoveragePanel({ data }: { data: FootballLabData }) {
  if (!data.coverage.length) {
    return <EmptyDataset title="No coverage record exists for this selection." />;
  }
  return (
    <>
      <SectionHeading
        eyebrow="Trust layer"
        title="Coverage before conclusions."
        copy="Metric availability varies by competition, season, and provider. The interface never silently fills unavailable statistics."
      />
      <div className="coverage-grid">
        {data.coverage.map((row) => (
          <article key={`${row.competition}-${row.season}`}>
            <span>{row.season}</span>
            <h3>{row.competition}</h3>
            <CoverageRow label="Standard statistics" level={row.standardStats} />
            <CoverageRow label="Expected metrics" level={row.xg} />
            <CoverageRow label="Detailed events" level={row.events} />
          </article>
        ))}
      </div>
      <div className="methodology">
        <h2>Methodology guardrails</h2>
        <div>
          <p><strong>Game management</strong> uses factual event timing and neutral proxies. It does not claim a team intentionally wasted time.</p>
          <p><strong>Manager analysis</strong> describes team performance during a tenure. Club resources, opponents, injuries, and inherited squads remain material context.</p>
          <p><strong>xG</strong> is provider-supplied and kept separate from observed goals. Missing xG is never reconstructed from aggregate shots.</p>
        </div>
      </div>
    </>
  );
}

function ArchitecturePanel({ data }: { data: FootballLabData }) {
  const [selectedId, setSelectedId] = useState("orchestration");
  const selected =
    data.pipeline.stages.find((stage) => stage.id === selectedId) ??
    data.pipeline.stages[0];
  const completeXg = data.coverage.filter((row) => row.xg === "complete").length;
  const partialEvents = data.coverage.filter((row) => row.events === "partial").length;
  const coreStages = data.pipeline.stages.filter((stage) => stage.id !== "notebooks");
  const notebook = data.pipeline.stages.find((stage) => stage.id === "notebooks");
  const generated = new Date(data.manifest.generatedAt);

  return (
    <>
      <SectionHeading
        eyebrow="Live system map"
        title="From source to portfolio."
        copy="Select any stage to inspect its contract. Status and freshness come from the same published manifest that travels with the application artifact."
      />

      <div className="architecture-status">
        <article>
          <span className="pulse-dot" />
          <div>
            <small>Current build</small>
            <strong>{data.manifest.status}</strong>
          </div>
        </article>
        <article>
          <small>Generated</small>
          <strong>{formatTimestamp(generated)}</strong>
        </article>
        <article>
          <small>Ingestion schedule</small>
          <strong>{data.pipeline.schedule}</strong>
        </article>
        <article>
          <small>xG coverage</small>
          <strong>{completeXg} complete snapshots</strong>
        </article>
        <article>
          <small>Event coverage</small>
          <strong>{partialEvents} partial snapshots</strong>
        </article>
      </div>

      <div className="architecture-layout">
        <div className="flow-canvas" aria-label="Football Lab data engineering architecture">
          <div className="flow-track" aria-hidden="true">
            <i />
          </div>
          {coreStages.map((stage, index) => (
            <div className="flow-step" key={stage.id}>
              <ArchitectureNode
                active={selected.id === stage.id}
                index={index + 1}
                onSelect={() => setSelectedId(stage.id)}
                stage={stage}
              />
              {stage.id === "warehouse" && notebook && (
                <div className="branch-wrap">
                  <span className="branch-line" aria-hidden="true" />
                  <ArchitectureNode
                    active={selected.id === notebook.id}
                    branch
                    index={0}
                    onSelect={() => setSelectedId(notebook.id)}
                    stage={notebook}
                  />
                </div>
              )}
              {index < coreStages.length - 1 && (
                <span className="flow-arrow" aria-hidden="true">
                  <i />
                  <b>›</b>
                </span>
              )}
            </div>
          ))}
        </div>

        <aside className="stage-inspector" aria-live="polite">
          <div className="stage-inspector-head">
            <span className={`stage-status ${selected.status}`}>
              {selected.status}
            </span>
            <small>{selected.layer}</small>
          </div>
          <h3>{selected.label}</h3>
          <strong>{selected.technology}</strong>
          <p>{selected.detail}</p>
          <dl>
            <div>
              <dt>Input</dt>
              <dd>{selected.input}</dd>
            </div>
            <div>
              <dt>Output</dt>
              <dd>{selected.output}</dd>
            </div>
          </dl>
        </aside>
      </div>

      <div className="architecture-contracts">
        <article>
          <span>01 / Reliability</span>
          <h3>Last-known-good promotion</h3>
          <p>
            Ingestion, validation, and the static build must pass before a release
            can replace the artifact currently published by the portfolio.
          </p>
        </article>
        <article>
          <span>02 / Security</span>
          <h3>Credentials stay upstream</h3>
          <p>
            Provider keys exist only in scheduled workflows. GitHub Pages receives
            optimized JSON and static assets, never source credentials.
          </p>
        </article>
        <article>
          <span>03 / Reproducibility</span>
          <h3>One analytical foundation</h3>
          <p>
            DuckDB and Parquet support both the web product and notebooks, keeping
            published analysis aligned with reproducible research.
          </p>
        </article>
      </div>

      <div className="deployment-ledger">
        <PanelTitle title="Build identity" note={data.pipeline.promotion} />
        <div>
          <span>Schema</span><strong>{data.manifest.schemaVersion}</strong>
          <span>Data version</span><strong>{data.manifest.dataVersion}</strong>
          <span>Source commit</span><strong>{data.manifest.sourceCommit.slice(0, 12)}</strong>
          <span>Canonical route</span><strong>/football-lab/</strong>
        </div>
      </div>
    </>
  );
}

function ArchitectureNode({
  active,
  branch = false,
  index,
  onSelect,
  stage,
}: {
  active: boolean;
  branch?: boolean;
  index: number;
  onSelect: () => void;
  stage: PipelineStage;
}) {
  return (
    <button
      aria-pressed={active}
      className={`architecture-node ${active ? "active" : ""} ${branch ? "branch" : ""}`}
      onClick={onSelect}
      type="button"
    >
      <span>{branch ? "↳" : String(index).padStart(2, "0")}</span>
      <small>{stage.layer}</small>
      <strong>{stage.label}</strong>
      <em>{stage.technology}</em>
      <i className={`stage-light ${stage.status}`} title={`${stage.status} stage`} />
    </button>
  );
}

function PanelTitle({ title, note }: { title: string; note: string }) {
  return <div className="panel-title"><h3>{title}</h3><span>{note}</span></div>;
}

function CoverageRow({ label, level }: { label: string; level: string }) {
  return <div className="coverage-row"><span>{label}</span><b className={level}>{level}</b></div>;
}

function RadarChart({ player, metrics }: { player: Player; metrics: Metric[] }) {
  if (!metrics.length) return <p className="empty-state">Select another metric family.</p>;
  const center = 150;
  const radius = 105;
  const points = metrics.map((metric, index) => {
    const angle = (Math.PI * 2 * index) / metrics.length - Math.PI / 2;
    const percentile = player.percentiles[metric.key] ?? 0;
    const r = radius * percentile / 100;
    return `${center + Math.cos(angle) * r},${center + Math.sin(angle) * r}`;
  }).join(" ");

  return (
    <div className="radar-wrap">
      <svg aria-label={`Percentile radar for ${player.name}`} className="radar" viewBox="0 0 300 300">
        {[20, 40, 60, 80, 100].map((level) => (
          <circle cx={center} cy={center} fill="none" key={level} r={radius * level / 100} />
        ))}
        {metrics.map((metric, index) => {
          const angle = (Math.PI * 2 * index) / metrics.length - Math.PI / 2;
          const x = center + Math.cos(angle) * radius;
          const y = center + Math.sin(angle) * radius;
          return <line key={metric.key} x1={center} x2={x} y1={center} y2={y} />;
        })}
        <polygon points={points} />
      </svg>
      <div className="radar-legend">
        <strong>{player.name}</strong>
        {metrics.map((metric) => (
          <div key={metric.key}><span>{metric.label}</span><b>{ordinal(player.percentiles[metric.key] ?? 0)}</b></div>
        ))}
      </div>
    </div>
  );
}

function ScatterPlot({
  players, xKey, xLabel, yKey, yLabel,
}: {
  players: Player[]; xKey: string; xLabel: string; yKey: string; yLabel: string;
}) {
  const width = 680;
  const height = 390;
  const pad = 58;
  const maxX = Math.max(...players.map((player) => player.metrics[xKey] ?? 0)) * 1.15;
  const maxY = Math.max(...players.map((player) => player.metrics[yKey] ?? 0)) * 1.15;
  return (
    <svg className="scatter" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${xLabel} compared with ${yLabel}`}>
      {[0, 1, 2, 3, 4].map((tick) => (
        <g key={tick}>
          <line x1={pad} x2={width - pad} y1={pad + tick * ((height - pad * 2) / 4)} y2={pad + tick * ((height - pad * 2) / 4)} />
          <line x1={pad + tick * ((width - pad * 2) / 4)} x2={pad + tick * ((width - pad * 2) / 4)} y1={pad} y2={height - pad} />
        </g>
      ))}
      {players.map((player, index) => {
        const x = pad + (player.metrics[xKey] / maxX) * (width - pad * 2);
        const y = height - pad - (player.metrics[yKey] / maxY) * (height - pad * 2);
        return (
          <g key={player.id}>
            <circle cx={x} cy={y} fill={PLAYER_COLORS[index % PLAYER_COLORS.length]} r="8" />
            <text x={x + 12} y={y + 4}>{player.name.split(" ").at(-1)}</text>
          </g>
        );
      })}
      <text className="axis-label" x={width / 2} y={height - 10}>{xLabel}</text>
      <text className="axis-label" transform={`translate(16 ${height / 2}) rotate(-90)`}>{yLabel}</text>
    </svg>
  );
}

function MetricBars({ players, metrics }: { players: Player[]; metrics: Metric[] }) {
  return (
    <div className="metric-bars">
      {metrics.map((metric) => (
        <div className="metric-row" key={metric.key}>
          <div><strong>{metric.label}</strong><span title={metric.description}>ⓘ</span></div>
          {players.map((player, index) => (
            <div className="bar-row" key={player.id}>
              <span>{player.name}</span>
              <div><i style={{ background: PLAYER_COLORS[index], width: `${player.percentiles[metric.key] ?? 0}%` }} /></div>
              <b>{formatMetric(player.metrics[metric.key] ?? 0, metric)}</b>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function ComparisonTable({ players, metrics }: { players: Player[]; metrics: Metric[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Metric</th>{players.map((player) => <th key={player.id}>{player.name}<small>{player.position}</small></th>)}</tr></thead>
        <tbody>
          {metrics.map((metric) => (
            <tr key={metric.key}>
              <th>{metric.label}<small>{metric.category} · {metric.unit}</small></th>
              {players.map((player) => (
                <td key={player.id}>
                  <strong>{formatMetric(player.metrics[metric.key] ?? 0, metric)}</strong>
                  <span style={{ color: scoreColor(player.percentiles[metric.key] ?? 0) }}>{player.percentiles[metric.key] ?? 0}th pct</span>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TeamScatter({ teams }: { teams: Team[] }) {
  const pseudoPlayers = teams.map((team) => ({
    id: team.id, name: team.name, team: team.name, competition: team.competition,
    season: team.season, position: "Team", age: 0, minutes: 0,
    metrics: { xg: team.metrics.xg_per_match, xa: team.metrics.progressive_actions / 40 },
    percentiles: {},
  }));
  return <ScatterPlot players={pseudoPlayers} xKey="xg" xLabel="xG / match" yKey="xa" yLabel="Progression index" />;
}

function LineChart({ teams }: { teams: Team[] }) {
  const width = 620, height = 300, pad = 38;
  return (
    <svg className="line-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Rolling points trajectories">
      {[0, 5, 10, 15].map((tick) => {
        const y = height - pad - (tick / 15) * (height - pad * 2);
        return <g key={tick}><line x1={pad} x2={width - pad} y1={y} y2={y} /><text x="8" y={y + 4}>{tick}</text></g>;
      })}
      {teams.map((team, index) => {
        const points = team.form.map((value, pointIndex) => {
          const x = pad + pointIndex * ((width - pad * 2) / Math.max(team.form.length - 1, 1));
          const y = height - pad - (value / 15) * (height - pad * 2);
          return `${x},${y}`;
        }).join(" ");
        return <g key={team.id}><polyline fill="none" points={points} stroke={PLAYER_COLORS[index]} /><text fill={PLAYER_COLORS[index]} x={width - 128} y={22 + index * 19}>{team.name}</text></g>;
      })}
    </svg>
  );
}

function TeamTable({ teams, metrics }: { teams: Team[]; metrics: string[][] }) {
  return <SimpleEntityTable entities={teams} metrics={metrics} />;
}

function ManagerBars({ managers, metrics }: { managers: Manager[]; metrics: string[][] }) {
  return (
    <div className="manager-bars">
      {metrics.slice(0, 5).map(([key, label]) => {
        const max = Math.max(...managers.map((manager) => manager.metrics[key] ?? 0), 1);
        return <div key={key}><strong>{label}</strong>{managers.map((manager, index) => <div className="bar-row" key={manager.id}><span>{manager.name}</span><div><i style={{ background: PLAYER_COLORS[index], width: `${Math.max(4, (manager.metrics[key] / max) * 100)}%` }} /></div><b>{manager.metrics[key].toFixed(key.includes("pct") ? 1 : 2)}</b></div>)}</div>;
      })}
    </div>
  );
}

function DonutChart({ managers }: { managers: Manager[] }) {
  const manager = managers[0];
  if (!manager) return <p className="empty-state">Select a manager.</p>;
  const leading = manager.metrics.subs_while_leading_pct;
  const drawing = manager.metrics.subs_while_drawing_pct;
  const trailing = Math.max(0, 100 - leading - drawing);
  const gradient = `conic-gradient(#63e6be 0 ${leading}%, #8c7cff ${leading}% ${leading + drawing}%, #ff786d ${leading + drawing}% 100%)`;
  return (
    <div className="donut-wrap">
      <div className="donut" style={{ background: gradient }}><span>{manager.matches}<small>matches</small></span></div>
      <div className="donut-legend">
        <strong>{manager.name}</strong>
        <span><i style={{ background: "#63e6be" }} /> Leading {leading.toFixed(0)}%</span>
        <span><i style={{ background: "#8c7cff" }} /> Drawing {drawing.toFixed(0)}%</span>
        <span><i style={{ background: "#ff786d" }} /> Trailing {trailing.toFixed(0)}%</span>
      </div>
    </div>
  );
}

function ManagerTable({ managers, metrics }: { managers: Manager[]; metrics: string[][] }) {
  return <SimpleEntityTable entities={managers} metrics={metrics} />;
}

function SimpleEntityTable({
  entities, metrics,
}: {
  entities: (Team | Manager)[]; metrics: string[][];
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Metric</th>{entities.map((entity) => <th key={entity.id}>{entity.name}<small>{"club" in entity ? entity.club : entity.competition}</small></th>)}</tr></thead>
        <tbody>{metrics.map(([key, label]) => <tr key={key}><th>{label}</th>{entities.map((entity) => <td key={entity.id}><strong>{entity.metrics[key]?.toFixed(2) ?? "—"}</strong></td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}

function ShotMap({ shots }: { shots: Shot[] }) {
  return (
    <svg className="pitch" viewBox="0 0 680 440" role="img" aria-label="Shot map">
      <rect height="400" width="640" x="20" y="20" />
      <line x1="340" x2="340" y1="20" y2="420" />
      <circle cx="340" cy="220" r="52" />
      <rect height="210" width="100" x="20" y="115" />
      <rect height="210" width="100" x="560" y="115" />
      {shots.map((shot) => (
        <g key={shot.id}>
          <circle
            className={shot.result === "Goal" ? "shot-goal" : ""}
            cx={20 + shot.x * 640}
            cy={20 + shot.y * 400}
            fill={shot.team === "Arsenal FC" ? "#63e6be" : "#8c7cff"}
            r={5 + shot.xg * 22}
          />
          <title>{shot.player}: {shot.xg.toFixed(2)} xG, {shot.result}</title>
        </g>
      ))}
    </svg>
  );
}

function XgTimeline({ shots }: { shots: Shot[] }) {
  const width = 900, height = 250, pad = 38;
  const teams = [...new Set(shots.map((shot) => shot.team))];
  const max = Math.max(...teams.map((team) => shots.filter((shot) => shot.team === team).reduce((sum, shot) => sum + shot.xg, 0))) * 1.15;
  return (
    <svg className="xg-timeline" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Cumulative expected goals timeline">
      {[0, 30, 60, 90].map((minute) => <g key={minute}><line x1={pad + minute / 90 * (width - pad * 2)} x2={pad + minute / 90 * (width - pad * 2)} y1={pad} y2={height - pad} /><text x={pad + minute / 90 * (width - pad * 2) - 8} y={height - 10}>{minute}&apos;</text></g>)}
      {teams.map((team, index) => {
        let cumulative = 0;
        const teamShots = shots.filter((shot) => shot.team === team).sort((a, b) => a.minute - b.minute);
        const points = [`${pad},${height - pad}`];
        for (const shot of teamShots) {
          cumulative += shot.xg;
          points.push(`${pad + shot.minute / 90 * (width - pad * 2)},${height - pad - cumulative / max * (height - pad * 2)}`);
        }
        points.push(`${width - pad},${height - pad - cumulative / max * (height - pad * 2)}`);
        return <g key={team}><polyline fill="none" points={points.join(" ")} stroke={PLAYER_COLORS[index]} /><text fill={PLAYER_COLORS[index]} x={width - 180} y={22 + index * 20}>{team} · {cumulative.toFixed(2)}</text></g>;
      })}
    </svg>
  );
}

function initials(name: string) {
  return name.split(" ").map((part) => part[0]).join("").slice(0, 2);
}

function ordinal(value: number) {
  const remainder = value % 100;
  const suffix =
    remainder >= 11 && remainder <= 13
      ? "th"
      : value % 10 === 1
        ? "st"
        : value % 10 === 2
          ? "nd"
          : value % 10 === 3
            ? "rd"
            : "th";
  return `${value}${suffix}`;
}

function EmptyDataset({ title }: { title: string }) {
  return (
    <div className="empty-dataset">
      <p className="eyebrow">Coverage-aware result</p>
      <h2>{title}</h2>
      <p>
        The interface will not substitute demonstration values from another
        competition or season. Check Coverage or run the relevant backfill.
      </p>
    </div>
  );
}

function formatTimestamp(value: Date) {
  if (Number.isNaN(value.getTime())) return "Unknown";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(value);
}
