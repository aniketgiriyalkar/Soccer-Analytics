import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

test("published dataset has required collections and coverage labels", async () => {
  const raw = await readFile(new URL("../public/data/football-lab.json", import.meta.url));
  const data = JSON.parse(raw);

  assert.equal(data.manifest.schemaVersion, "1.0");
  assert.ok(data.players.length >= 6);
  assert.ok(data.teams.length >= 5);
  assert.ok(Array.isArray(data.managers));
  assert.ok(data.metrics.some((metric) => metric.key === "xg_per90"));
  assert.ok(data.metrics.some((metric) => metric.category === "Discipline"));
  assert.ok(data.metrics.some((metric) => metric.category === "Game management"));
  assert.equal(data.pipeline.stages.at(0).id, "sources");
  assert.equal(data.pipeline.stages.at(-1).id, "delivery");
  assert.ok(data.pipeline.stages.some((stage) => stage.id === "notebooks"));
  assert.ok(
    data.coverage.every((row) =>
      ["complete", "partial", "unavailable"].includes(row.xg),
    ),
  );
});

test("all percentiles stay within a valid range", async () => {
  const raw = await readFile(new URL("../public/data/football-lab.json", import.meta.url));
  const data = JSON.parse(raw);

  for (const player of data.players) {
    for (const percentile of Object.values(player.percentiles)) {
      assert.ok(percentile >= 0 && percentile <= 100);
    }
  }
});
