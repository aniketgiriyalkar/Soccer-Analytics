import type { Metric, Player } from "@/types/analytics";

export const POSITION_GROUPS = [
  "Goalkeeper",
  "Centre-back",
  "Full-back",
  "Defensive midfield",
  "Central midfield",
  "Attacking midfield",
  "Winger",
  "Striker",
] as const;

export function formatMetric(value: number, metric: Metric) {
  if (metric.unit === "%") return `${value.toFixed(1)}%`;
  if (metric.unit === "min") return `${value.toFixed(1)} min`;
  if (metric.unit === "seconds") return `${value.toFixed(1)}s`;
  return value.toFixed(metric.unit === "per 90" ? 2 : 1);
}

export function comparisonDomain(players: Player[], key: string) {
  const values = players.map((player) => player.metrics[key] ?? 0);
  const maximum = Math.max(...values, 1);
  return [0, maximum * 1.15] as const;
}

export function scoreColor(percentile: number) {
  if (percentile >= 80) return "#63e6be";
  if (percentile >= 60) return "#a8e063";
  if (percentile >= 40) return "#f4c95d";
  return "#ff786d";
}
