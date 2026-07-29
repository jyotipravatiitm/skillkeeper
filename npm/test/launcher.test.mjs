import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";

test("npm launcher starts the Skillkeeper CLI", () => {
  const result = spawnSync(
    process.execPath,
    ["npm/bin/skillkeeper.mjs", "--help"],
    { encoding: "utf8" },
  );

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Observe, test, stage, and improve Agent Skills/);
  assert.match(result.stdout, /scan/);
  assert.match(result.stdout, /rollback/);
});

test("npm launcher exposes the packaged version", () => {
  const result = spawnSync(
    process.execPath,
    ["npm/bin/skillkeeper.mjs", "--version"],
    { encoding: "utf8" },
  );

  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout.trim(), "skillkeeper 0.1.1");
});

test("npm launcher explains the Python requirement", () => {
  const result = spawnSync(
    process.execPath,
    ["npm/bin/skillkeeper.mjs", "--help"],
    {
      encoding: "utf8",
      env: {
        ...process.env,
        PATH: "",
        SKILLKEEPER_PYTHON: "/missing/python",
      },
    },
  );

  assert.equal(result.status, 1);
  assert.match(result.stderr, /requires Python 3\.10 or newer/);
});
