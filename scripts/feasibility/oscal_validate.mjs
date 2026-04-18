#!/usr/bin/env node
/**
 * Phase 0.5b feasibility proof — validate a generated OSCAL Component Definition
 * against NIST's published OSCAL v1.1.1 JSON schema using Ajv.
 *
 * Why Node+Ajv and not Python jsonschema / jsonschema-rs?
 *   - NIST's OSCAL schemas use ECMA-262 Unicode property escapes in patterns
 *     (\p{L}, \p{N}). Python's `re` module does not support those.
 *   - jsonschema-rs supports ECMA-262 regex, but does not correctly resolve
 *     NIST's ~119 anchor-style $ref values ("$ref": "#assembly_oscal-...").
 *     Even a minimal-valid component-definition fails at
 *     schema_path=['definitions', 'URIReferenceDatatype', 'type'] because the
 *     validator falls through to the $schema directive's type.
 *   - Ajv (the reference JSON Schema validator in the JS ecosystem) handles
 *     both ECMA-262 regex and anchor-style $refs natively, and is what most
 *     OSCAL-aware tooling uses. See https://ajv.js.org/options.html
 *
 * Usage:
 *   node scripts/feasibility/oscal_validate.mjs <path-to-instance.json> [--schema <path>]
 *
 * Exit codes:
 *   0 — instance validates
 *   1 — instance fails validation
 *   2 — setup error (missing file, unreadable JSON, schema load failure)
 */

import { readFileSync } from "node:fs";
import { resolve, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";

import Ajv from "ajv";
import addFormats from "ajv-formats";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = resolve(__dirname, "..", "..");

const DEFAULT_SCHEMA = resolve(
  REPO_ROOT,
  "vendor",
  "oscal",
  "oscal_component_schema_v1.1.1.json",
);

/** Parse argv into { instancePath, schemaPath }. */
function parseArgs(argv) {
  const args = argv.slice(2);
  if (args.length === 0) {
    return null;
  }
  let instancePath = null;
  let schemaPath = DEFAULT_SCHEMA;
  for (let i = 0; i < args.length; i += 1) {
    const a = args[i];
    if (a === "--schema") {
      schemaPath = resolve(args[i + 1] ?? "");
      i += 1;
    } else if (!instancePath) {
      instancePath = resolve(a);
    }
  }
  if (!instancePath) return null;
  return { instancePath, schemaPath };
}

function loadJson(path, label) {
  let raw;
  try {
    raw = readFileSync(path, "utf-8");
  } catch (err) {
    process.stderr.write(
      `ERROR: cannot read ${label} at ${path}: ${err.message}\n`,
    );
    process.exit(2);
  }
  try {
    return JSON.parse(raw);
  } catch (err) {
    process.stderr.write(
      `ERROR: ${label} at ${path} is not valid JSON: ${err.message}\n`,
    );
    process.exit(2);
  }
}

function main() {
  const parsed = parseArgs(process.argv);
  if (!parsed) {
    process.stderr.write(
      "Usage: node scripts/feasibility/oscal_validate.mjs <instance.json> [--schema <schema.json>]\n",
    );
    process.exit(2);
  }

  const schema = loadJson(parsed.schemaPath, "OSCAL schema");
  const instance = loadJson(parsed.instancePath, "OSCAL instance");

  const ajv = new Ajv({
    strict: false,
    allErrors: true,
    verbose: true,
  });
  addFormats(ajv);

  let validate;
  try {
    validate = ajv.compile(schema);
  } catch (err) {
    process.stderr.write(`ERROR: failed to compile OSCAL schema: ${err.message}\n`);
    process.exit(2);
  }

  const ok = validate(instance);
  const relInstance = relative(REPO_ROOT, parsed.instancePath) || parsed.instancePath;
  const relSchema = relative(REPO_ROOT, parsed.schemaPath) || parsed.schemaPath;

  if (ok) {
    process.stdout.write(
      `PASS: ${relInstance} validates against ${relSchema} (Ajv).\n`,
    );
    process.exit(0);
  }

  const errors = validate.errors ?? [];
  process.stderr.write(
    `FAIL: ${relInstance} has ${errors.length} schema violation(s) against ${relSchema}:\n`,
  );
  for (const err of errors.slice(0, 25)) {
    const path = err.instancePath || "(root)";
    const msg = err.message ?? "(no message)";
    const extra = err.params ? JSON.stringify(err.params) : "";
    process.stderr.write(`  - ${path}: ${msg} ${extra}\n`);
  }
  if (errors.length > 25) {
    process.stderr.write(`  ...and ${errors.length - 25} more\n`);
  }
  process.exit(1);
}

main();
