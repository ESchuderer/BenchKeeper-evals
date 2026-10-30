// Throwaway: the file lists of a bare and an srt run of the preview command, side by side. Usage: node diff.mjs [--global] [weak]
import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const g = process.argv.includes('--global') ? ['--global'] : [];
const weak = process.argv.includes('weak') ? ['--extra={"enableWeakerNestedSandbox":true}'] : [];
const run = (mode, ...a) => JSON.parse(spawnSync('node', [join(here, 'run.mjs'), mode, ...a], { encoding: 'utf8' }).stdout.trim().split('\n').pop());
// bare-bare: how much two runs without srt differ already (timestamps in the global lock file)
const s = process.argv.includes('bare-bare') ? run('bare', ...g) : run('srt', ...weak, ...g), b = run('bare', ...g);
console.log('only bare:', b.files.filter((f) => !s.files.includes(f)));
console.log('only srt:', s.files.filter((f) => !b.files.includes(f)));
console.log('codes', b.code, s.code, 'counts', b.count, s.count);
