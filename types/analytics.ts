export type CoverageLevel = "complete" | "partial" | "unavailable";

export type Metric = {
  key: string;
  label: string;
  category: string;
  unit: string;
  higherIsBetter: boolean;
  description: string;
};

export type Player = {
  id: string;
  name: string;
  team: string;
  competition: string;
  season: string;
  position: string;
  age: number;
  minutes: number;
  metrics: Record<string, number>;
  percentiles: Record<string, number>;
};

export type Team = {
  id: string;
  name: string;
  competition: string;
  season: string;
  matches: number;
  metrics: Record<string, number>;
  form: number[];
};

export type Manager = {
  id: string;
  name: string;
  club: string;
  competition: string;
  tenure: string;
  matches: number;
  metrics: Record<string, number>;
};

export type Shot = {
  id: string;
  player: string;
  team: string;
  minute: number;
  x: number;
  y: number;
  xg: number;
  result: "Goal" | "Saved" | "Blocked" | "Missed";
  situation: string;
};

export type Coverage = {
  competition: string;
  season: string;
  standardStats: CoverageLevel;
  xg: CoverageLevel;
  events: CoverageLevel;
};

export type PipelineStage = {
  id: string;
  label: string;
  layer: string;
  technology: string;
  status: "active" | "ready" | "pending" | "external";
  detail: string;
  input: string;
  output: string;
};

export type FootballLabData = {
  manifest: {
    schemaVersion: string;
    dataVersion: string;
    generatedAt: string;
    sourceCommit: string;
    status: string;
    disclaimer: string;
  };
  pipeline: {
    schedule: string;
    promotion: string;
    stages: PipelineStage[];
  };
  metrics: Metric[];
  players: Player[];
  teams: Team[];
  managers: Manager[];
  shots: Shot[];
  coverage: Coverage[];
};
