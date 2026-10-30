// Throwaway driver for issue 405, second part: allow list needed, read-only cache, exact argv, missing prerequisites, timing, strict read.
// Usage (dev container, srt 0.0.81 at /tmp/srt): node extra.mjs [weak]
import { spawnSync } from 'node:child_process';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const weak = process.argv[2] === 'weak' ? ['--extra={"enableWeakerNestedSandbox":true}'] : [];
const run = (mode, ...args) => {
  const r = spawnSync('node', [join(here, 'run.mjs'), mode, ...args], { encoding: 'utf8', timeout: 400e3 });
  try { return JSON.parse(r.stdout.trim().split('\n').pop()); } catch { return { code: -1, error: `${r.stdout.slice(-300)}${r.stderr.slice(-300)}` }; }
};
const merge = (o) => `--extra=${JSON.stringify({ ...(weak.length ? { enableWeakerNestedSandbox: true } : {}), ...o })}`;
const bare = run('bare');
const same = (x) => JSON.stringify(x.files) === JSON.stringify(bare.files);
const show = (label, x) => console.log(`${label}: code=${x.code} files=${x.count} same=${same(x)} ${x.seconds}s ${x.error ?? ''} ${x.code ? (x.stdout ?? '').slice(-250).replace(/\n/g, ' ') : ''}`);

console.log('## allow list needed by the preview command (cache scratch)');
for (const allow of ['registry.npmjs.org,github.com', 'registry.npmjs.org,github.com,api.github.com', 'registry.npmjs.org', 'github.com', '']) show(`allow=[${allow}]`, run('srt', ...weak, '--cache=scratch', `--allow=${allow}`));

console.log('## hosts the command asked for (debug log of denied and allowed requests), allow list registry+github only');
{
  const d = run('srt', ...weak, '--cache=scratch', '--debug', '--allow=registry.npmjs.org,github.com');
  console.log((d.stderr ?? '').split('\n').filter((l) => /allow|deny|denied|block|CONNECT|host/i.test(l)).slice(0, 15).join('\n'));
}

console.log('## npm cache: warm real cache outside the sandbox, read-only vs writable vs scratch');
run('bare', '--cache=real'); // warm
for (const c of ['real', 'ro', 'scratch']) show(`srt cache=${c}`, run('srt', ...weak, `--cache=${c}`));

console.log('## timing, 4 runs each (seconds)');
const times = (label, f) => console.log(label, Array.from({ length: 4 }, () => f().seconds).join(' '));
times('bare   ', () => run('bare'));
times('srt real cache   ', () => run('srt', ...weak, '--cache=real'));
times('srt ro cache     ', () => run('srt', ...weak, '--cache=ro'));
times('srt scratch cache', () => run('srt', ...weak, '--cache=scratch'));

console.log('## (d) exact argv: process.argv of a node child, bare vs srt, with shell metacharacters');
{
  const args = ['a b', '$(touch bk-inject1)', '; touch bk-inject2', "it's", 'back`touch bk-inject3`', 'multi\nline', '', '*', '-s', '--', '-y', '\\n', '~', '$HOME', '"dq"', '|x', '&&'];
  const cmd = `--cmd=${JSON.stringify(['node', join(here, 'probe.mjs'), 'argv', ...args])}`;
  const b = run('bare', cmd), s = run('srt', ...weak, cmd);
  console.log('args passed:', JSON.stringify(args));
  console.log('bare stdout :', b.stdout);
  console.log('srt  stdout :', s.stdout, 'code', s.code);
  console.log('identical:', b.stdout === s.stdout, '| files left by an injected command:', s.files.filter((f) => f.startsWith('bk-inject')));
  const d = run('srt', ...weak, '--debug', cmd);
  console.log((d.stderr ?? '').split('\n').filter((l) => /Original command|Wrapped command/i.test(l)).map((l) => l.slice(0, 400)).join('\n'));
}

console.log('## (5) a missing prerequisite: the command must not run unconfined (marker written by the command in the scratch folder)');
for (const [label, o] of [['bwrapPath missing', { bwrapPath: '/nonexistent/bwrap' }], ['socatPath missing', { socatPath: '/nonexistent/socat' }], ['ripgrep missing', { ripgrep: { command: '/nonexistent/rg' } }]]) {
  const r = run('srt', ...weak, merge(o), `--cmd=${JSON.stringify(['node', join(here, 'probe.mjs'), 'write-scratch'])}`);
  console.log(`${label}: code=${r.code} marker written=${(r.files ?? []).some((f) => f.startsWith('bk-inside'))} stderr=${(r.stderr ?? r.error ?? '').replace(/\n/g, ' ').slice(0, 300)}`);
}

console.log('## strict read: deny the whole home, allow only the scratch folder and the cache for reads');
{
  const o = merge({ filesystem: { denyRead: [homedir()], allowRead: [join(homedir(), '.npm')] } });
  show('strict read (denyRead home, allowRead cache), cache read-only', run('srt', ...weak, '--cache=ro', o));
}
