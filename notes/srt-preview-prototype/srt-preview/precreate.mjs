// Throwaway: the preview command under srt without a pre-created .claude folder (srt covers a missing .claude with an empty read-only folder).
// Usage: node precreate.mjs [weak]
import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const weak = process.argv[2] === 'weak' ? ['--extra={"enableWeakerNestedSandbox":true}'] : [];
for (const g of [[], ['--global']]) {
  const j = JSON.parse(spawnSync('node', [join(here, 'run.mjs'), 'srt', ...weak, '--no-precreate', '--cache=scratch', ...g], { encoding: 'utf8', timeout: 400e3 }).stdout.trim().split('\n').pop());
  console.log(g[0] ?? 'project', 'code', j.code, 'files', j.count, 'claude files', j.files.filter((f) => f.startsWith('.claude')).length, JSON.stringify(j.stdout).slice(-260));
}
