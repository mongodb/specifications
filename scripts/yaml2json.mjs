#!/usr/bin/env node
// Usage: node yaml2json.mjs <file.yml>
// Converts a YAML file to JSON, with YAML 1.1 merge key (<<:) support for legacy tests.
// TODO(DRIVERS-3178): after removing legacy tests, consider removing this script and invoking `js-yaml` directly.
import { readFileSync } from 'fs';
import { execSync } from 'child_process';

// Import globally installed `js-yaml` package:
const globalRoot = execSync('npm root -g').toString().trim();
const pkg = JSON.parse(readFileSync(`${globalRoot}/js-yaml/package.json`, 'utf8'));
const entry = pkg.exports?.['.']?.import ?? pkg.module ?? pkg.main;
const { load, CORE_SCHEMA, mergeTag } = await import(`${globalRoot}/js-yaml/${entry}`);

const file = process.argv[2];
const content = readFileSync(file, 'utf8');
const data = load(content, { schema: CORE_SCHEMA.withTags(mergeTag) });
process.stdout.write(JSON.stringify(data, null, 2) + '\n');
