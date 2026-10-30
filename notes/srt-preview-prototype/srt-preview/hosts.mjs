// Throwaway: which hosts the preview command needs, project and global mode. Usage: node hosts.mjs [weak]
import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const weak = process.argv[2] === 'weak' ? ['--extra={"enableWeakerNestedSandbox":true}'] : [];
const run = (...a) => JSON.parse(spawnSync('node', [join(here, 'run.mjs'), 'srt', ...weak, ...a], { encoding: 'utf8', timeout: 400e3 }).stdout.trim().split('\n').pop());
for (const g of [[], ['--global']]) {
  for (const allow of ['registry.npmjs.org,github.com', 'registry.npmjs.org,github.com,api.github.com']) {
    const j = run('--cache=scratch', ...g, `--allow=${allow}`);
    console.log(g[0] ?? 'project', `allow=[${allow}]`, 'code', j.code, 'files', j.count, `${j.seconds}s`, j.code ? JSON.stringify(j.stdout).slice(-200) : '');
  }
}
// What the proxy decided, from the debug log, with registry and github allowed.
const d = run('--cache=scratch', '--debug', '--allow=registry.npmjs.org,github.com');
console.log((d.stderr ?? '').split('\n').filter((l) => /Allowed|denied|Denied/.test(l)).join('\n'));
