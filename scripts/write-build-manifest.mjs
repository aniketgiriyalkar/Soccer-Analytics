import { execFileSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const data = JSON.parse(await readFile(resolve("public/data/football-lab.json"), "utf8"));
let commit = process.env.GITHUB_SHA;

if (!commit) {
  try {
    commit = execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim();
  } catch {
    commit = "unknown";
  }
}

const manifest = {
  product: "football-lab",
  sourceRepository: "aniketgiriyalkar/Soccer-Analytics",
  sourceCommit: commit,
  dataVersion: data.manifest.dataVersion,
  schemaVersion: data.manifest.schemaVersion,
  builtAt: new Date().toISOString(),
  canonicalPath: "/football-lab/",
};

await mkdir(resolve("public"), { recursive: true });
await writeFile(resolve("public/build-manifest.json"), JSON.stringify(manifest, null, 2));
console.log(`Wrote Football Lab build manifest for ${commit.slice(0, 12)}`);
