// Throwaway driver for issue 405: runs the checks through run.mjs and prints one line per check.
// Usage (in the dev container, srt 0.0.81 installed at /tmp/srt): node suite.mjs [weak]
//   weak: add enableWeakerNestedSandbox (needed when the container does not allow a fresh /proc).
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const weak = process.argv[2] === 'weak' ? ['--extra={"enableWeakerNestedSandbox":true}'] : [];
// Throwaway fakes in the real home for the read probes. Refuses to overwrite a file that exists; removes what it made on exit.
const home = homedir();
const sshDir = join(home, '.ssh'), fakes = [join(sshDir, 'id_test'), join(home, 'bk-readable.txt')];
const madeSsh = !existsSync(sshDir);
if (fakes.some(existsSync)) throw new Error(`refusing to run: ${fakes.filter(existsSync).join(' ')} exists`);
mkdirSync(sshDir, { recursive: true });
for (const f of fakes) writeFileSync(f, 'not-a-secret-throwaway\n', { flag: 'wx' });
process.on('exit', () => { for (const f of fakes) rmSync(f, { force: true }); if (madeSsh) rmSync(sshDir, { recursive: true, force: true }); });

const run = (mode, ...args) => {
  const r = spawnSync('node', [join(here, 'run.mjs'), mode, ...args], { encoding: 'utf8', timeout: 400e3 });
  try { return JSON.parse(r.stdout.trim().split('\n').pop()); } catch { return { code: -1, error: `${r.stdout.slice(-300)}${r.stderr.slice(-300)}` }; }
};
const probe = (mode, name, ...args) => {
  for (const f of ['/tmp/bk-outside.txt', join(home, 'bk-outside.txt'), join(home, '.npm', 'bk-marker.txt'), join(home, 'bk-link.txt')]) rmSync(f, { force: true }); // a file left by an earlier run must not decide this one
  const r = run(mode, ...(mode === 'srt' ? weak : []), ...args, `--cmd=${JSON.stringify(['node', join(here, 'probe.mjs'), name])}`);
  try { return JSON.parse(r.stdout); } catch { return { name, ok: null, detail: `code ${r.code} ${r.error ?? ''} ${r.stdout ?? ''} ${r.stderr ?? ''}`.slice(0, 220) }; }
};
const row = (...c) => console.log(c.join(' | '));

// (c) the preview command: same files with and without srt, project and global, and the time it takes.
console.log('## (c) preview command');
for (const g of [[], ['--global']]) {
  const bare = run('bare', ...g), s = run('srt', ...weak, ...g), s2 = run('srt', ...weak, ...g, '--cache=scratch');
  const same = (x) => JSON.stringify(x.files) === JSON.stringify(bare.files);
  row(g[0] ?? 'project', `bare code=${bare.code} files=${bare.count} ${bare.seconds}s`, `srt(real cache) code=${s.code} files=${s.count} same=${same(s)} ${s.seconds}s`, `srt(scratch cache) code=${s2.code} files=${s2.count} same=${same(s2)} ${s2.seconds}s ${s2.error ?? ''}`);
  if (!same(s) || s.code) console.log('  srt stdout/stderr:', s.stdout?.slice(-400), s.stderr?.slice(-400));
}

// (a) writes and reads outside the scratch folder.
console.log('## (a) filesystem probes: bare vs srt (cache real | ro | scratch)');
for (const name of ['write-scratch', 'write-abs-tmp', 'write-real-home', 'write-npm-cache', 'write-through-link', 'write-mandatory-bashrc', 'read-ssh', 'read-home-file']) {
  const b = probe('bare', name), r = probe('srt', name, '--cache=real'), ro = probe('srt', name, '--cache=ro'), sc = probe('srt', name, '--cache=scratch');
  row(name, `bare ok=${b.ok}`, `srt/real ok=${r.ok} ${r.detail}`, `srt/ro ok=${ro.ok} ${ro.detail}`, `srt/scratch ok=${sc.ok} ${sc.detail}`);
}

// (b) network probes under srt with the allow list of the preview.
console.log('## (b) network probes: bare vs srt (allow: registry.npmjs.org, github.com, api.github.com)');
for (const [name, ...a] of [['net-registry'], ['net-github'], ['net-gitlab'], ['net-other-registry'], ['net-raw-tcp']]) {
  const b = probe('bare', name, ...a), s = probe('srt', name, '--cache=scratch', ...a);
  row(name, `bare ok=${b.ok} ${b.detail}`, `srt ok=${s.ok} ${s.detail}`);
}
const extra = probe('srt', 'net-other-registry', '--cache=scratch', '--allow=registry.npmjs.org,github.com,api.github.com,registry.yarnpkg.com');
row('net-other-registry, host added to the allow list', `srt ok=${extra.ok} ${extra.detail}`);
