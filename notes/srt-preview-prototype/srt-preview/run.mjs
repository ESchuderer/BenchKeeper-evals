// Throwaway prototype for issue 405: the skill install preview command, bare or wrapped in srt, in a scratch folder.
// Mirrors app/src/prerun.mjs: scratch HOME, empty git config, npmrc without credentials, the env of the plan step.
// Usage: node run.mjs <bare|srt> [--cache=real|scratch|ro] [--allow=h1,h2] [--global] [--debug] [--keep] [--extra=<json merged into the srt settings>] [--env=<json of extra variables>] [--cmd=<json argv>]
// Spawns with an argv array and no shell. Prints one JSON line: code, seconds, files below the scratch folder, stderr tail.
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { join, relative } from 'node:path';
import { parseArgs } from 'node:util';

const { positionals: [mode], values: o } = parseArgs({ allowPositionals: true, options: {
  cache: { type: 'string', default: 'real' }, allow: { type: 'string', default: 'registry.npmjs.org,github.com,api.github.com' },
  global: { type: 'boolean' }, 'no-precreate': { type: 'boolean' }, debug: { type: 'boolean' }, keep: { type: 'boolean' }, cmd: { type: 'string' }, extra: { type: 'string', default: '{}' }, env: { type: 'string', default: '{}' }, writes: { type: 'string', default: '' },
} });
const SRT = process.env.SRT_BIN ?? '/tmp/srt/node_modules/.bin/srt'; // npm i --save-exact @anthropic-ai/sandbox-runtime@0.0.81 in /tmp/srt
const SPEC = 'skills@npm:skills@1.7.2';
const argv = o.cmd ? JSON.parse(o.cmd) : ['npx', '-y', SPEC, 'add', 'https://github.com/anthropics/skills', '-s', 'skill-creator', ...(o.global ? ['-g'] : []), '-a', 'claude-code', '-a', 'codex', '--copy', '-y'];

const t = mkdtempSync(join(tmpdir(), 'bk-srt-'));
const h = join(t, 'h'), p = join(t, 'p'), root = o.global ? h : p;
for (const d of [h, p]) mkdirSync(d, { recursive: true });
writeFileSync(join(t, 'gitconfig'), '', { mode: 0o600 });
writeFileSync(join(t, 'npmrc'), '', { mode: 0o600 });
const realCache = process.env.npm_config_cache ?? join(homedir(), '.npm');
const cache = o.cache === 'scratch' ? join(t, 'npm-cache') : realCache;
const env = {
  PATH: process.env.PATH, LANG: 'C.UTF-8', TMPDIR: process.env.TMPDIR, HOME: h, USERPROFILE: h,
  BK_REAL_HOME: homedir(), DO_NOT_TRACK: '1', npm_config_registry: 'https://registry.npmjs.org/', npm_config_ignore_scripts: 'true',
  npm_config_before: new Date(Date.now() - 7 * 864e5).toISOString(),
  npm_config_cache: cache, npm_config_userconfig: join(t, 'npmrc'), GIT_CONFIG_GLOBAL: join(t, 'gitconfig'), GIT_CONFIG_NOSYSTEM: '1',
};
Object.assign(env, JSON.parse(o.env)); // extra variables for the command, e.g. npm_config_offline
env.NODE_OPTIONS = process.env.NODE_OPTIONS ?? undefined;
for (const k of Object.keys(env)) if (env[k] === undefined) delete env[k];

let cmd = argv;
if (mode === 'srt') {
  // srt points TMPDIR at CLAUDE_CODE_TMPDIR (default /tmp/claude, which must exist and is shared): a folder in the scratch folder instead.
  // srt denies writes to .claude/commands and .claude/agents; a missing .claude is then covered by an empty read-only folder and the
  // skills CLI cannot create .claude/skills. An existing .claude (empty is enough) keeps the cover on the two folders.
  if (!o['no-precreate']) for (const d of new Set([p, h])) mkdirSync(join(d, '.claude', 'skills'), { recursive: true });
  mkdirSync(join(t, 'tmp')); env.CLAUDE_CODE_TMPDIR = join(t, 'tmp');
  // The scratch folder is the only writable root; the npm cache is writable (real), read-only (ro) or inside the scratch folder.
  const allowWrite = [t, ...(o.cache === 'real' ? [cache] : []), ...o.writes.split(',').filter(Boolean)];
  const settings = { network: { allowedDomains: o.allow.split(',').filter(Boolean), deniedDomains: [] },
    filesystem: { denyRead: [join(homedir(), '.ssh')], allowRead: [], allowWrite, denyWrite: [] } };
  writeFileSync(join(t, 'srt.json'), JSON.stringify({ ...settings, ...JSON.parse(o.extra), filesystem: { ...settings.filesystem, ...JSON.parse(o.extra).filesystem } }, null, 1));
  cmd = [SRT, ...(o.debug ? ['-d'] : []), '--settings', join(t, 'srt.json'), '--', ...argv];
}
const t0 = Date.now();
const r = spawnSync(cmd[0], cmd.slice(1), { cwd: root, env, encoding: 'utf8', timeout: 300e3 });
const seconds = +((Date.now() - t0) / 1e3).toFixed(1);

// Files the command left in the scratch folder (the npm cache and npx folders are not part of what it installs).
const SKIP = [/^\.tmp-none/, /^\.npm(\/|$)/, /^\.cache(\/|$)/, /^\.config\/npm(\/|$)/, /^npm-cache(\/|$)/];
const files = [];
const walk = (d) => { for (const n of readdirSync(d)) { const f = join(d, n), st = statSync(f); if (st.isDirectory()) walk(f); else files.push(relative(root, f) + ' ' + createHash('sha1').update(readFileSync(f)).digest('hex').slice(0, 10)); } };
walk(root);
const kept = files.filter((f) => !SKIP.some((s) => s.test(f))).sort();
const tail = (s) => (s ?? '').trim().split('\n').slice(-(o.debug ? 60 : 6)).join('\n');
console.log(JSON.stringify({ mode, cache: o.cache, global: !!o.global, code: r.status, signal: r.signal, error: r.error?.message, seconds, count: kept.length, files: kept, stdout: tail(r.stdout), stderr: tail(r.stderr), scratch: o.keep ? t : undefined }));
if (!o.keep) rmSync(t, { recursive: true, force: true });
