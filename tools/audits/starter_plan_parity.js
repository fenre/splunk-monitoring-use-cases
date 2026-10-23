#!/usr/bin/env node
// Starter-plan parity check: runs src/scripts/07-starter-plan.js against
// tests/fixtures/starter-plan-parity.json and compares every case with the
// recorded expectation. mcp/tests/test_starter_plan_parity.py checks the
// Python mirror against the same expectations.
//
//   node tools/audits/starter_plan_parity.js           # check (exit 1 on mismatch)
//   node tools/audits/starter_plan_parity.js --write   # re-record expectations from JS

'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..', '..');
const PLANNER = path.join(ROOT, 'src', 'scripts', '07-starter-plan.js');
const FIXTURE = path.join(ROOT, 'tests', 'fixtures', 'starter-plan-parity.json');

function loadPlanner() {
  const ctx = vm.createContext({});
  vm.runInContext(fs.readFileSync(PLANNER, 'utf8'), ctx, { filename: PLANNER });
  return ctx;
}

function canonical(value) {
  return JSON.stringify(value, (key, val) => {
    if (val && typeof val === 'object' && !Array.isArray(val)) {
      return Object.keys(val).sort().reduce((acc, k) => { acc[k] = val[k]; return acc; }, {});
    }
    return val;
  });
}

function main() {
  const write = process.argv.includes('--write');
  const planner = loadPlanner();
  const fixture = JSON.parse(fs.readFileSync(FIXTURE, 'utf8'));
  let failures = 0;

  fixture.planCases.forEach((c) => {
    const got = JSON.parse(JSON.stringify(planner.spPlanRollout(fixture.index, c.opts)));
    if (write) { c.expected = got; return; }
    if (canonical(got) !== canonical(c.expected)) {
      failures++;
      console.error(`plan case ${c.name}: mismatch\n  got:      ${canonical(got)}\n  expected: ${canonical(c.expected)}`);
    }
  });
  fixture.pasteCases.forEach((c) => {
    const got = JSON.parse(JSON.stringify(planner.spParsePaste(c.text)));
    if (write) { c.expected = got; return; }
    if (canonical(got) !== canonical(c.expected)) {
      failures++;
      console.error(`paste case ${c.name}: mismatch\n  got:      ${canonical(got)}\n  expected: ${canonical(c.expected)}`);
    }
  });

  if (write) {
    fs.writeFileSync(FIXTURE, JSON.stringify(fixture, null, 2) + '\n');
    console.log(`Recorded ${fixture.planCases.length} plan + ${fixture.pasteCases.length} paste expectations.`);
    return 0;
  }
  if (failures) {
    console.error(`starter-plan parity: ${failures} mismatch(es)`);
    return 1;
  }
  console.log(`starter-plan parity: ${fixture.planCases.length} plan + ${fixture.pasteCases.length} paste cases OK`);
  return 0;
}

process.exit(main());
