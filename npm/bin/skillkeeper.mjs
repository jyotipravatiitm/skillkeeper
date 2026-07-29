#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { delimiter, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function candidates() {
  const configured = process.env.SKILLKEEPER_PYTHON;
  const result = [];
  if (configured) {
    result.push({ command: configured, prefix: [] });
  }
  if (process.platform === "win32") {
    result.push({ command: "py", prefix: ["-3"] });
  }
  result.push({ command: "python3", prefix: [] });
  result.push({ command: "python", prefix: [] });
  return result;
}

function supportsSkillkeeper(candidate) {
  const probe = spawnSync(
    candidate.command,
    [
      ...candidate.prefix,
      "-c",
      "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)",
    ],
    { stdio: "ignore" },
  );
  return probe.status === 0;
}

const python = candidates().find(supportsSkillkeeper);

if (!python) {
  console.error(
    [
      "Skillkeeper requires Python 3.10 or newer.",
      "Install Python from https://www.python.org/downloads/ and retry.",
      "You can also set SKILLKEEPER_PYTHON to the Python executable to use.",
    ].join("\n"),
  );
  process.exit(1);
}

const existingPythonPath = process.env.PYTHONPATH;
const pythonPath = existingPythonPath
  ? `${packageRoot}${delimiter}${existingPythonPath}`
  : packageRoot;

const run = spawnSync(
  python.command,
  [...python.prefix, "-m", "skillkeeper", ...process.argv.slice(2)],
  {
    env: { ...process.env, PYTHONPATH: pythonPath },
    stdio: "inherit",
  },
);

if (run.error) {
  console.error(`Unable to start Skillkeeper: ${run.error.message}`);
  process.exit(1);
}

process.exit(run.status ?? 1);
