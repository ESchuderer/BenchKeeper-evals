// Throwaway probes run bare and under srt. Prints one JSON line: { name, ok, detail }. ok=true means the action succeeded.
import { spawnSync } from 'node:child_process';
import { readFileSync, symlinkSync, writeFileSync } from 'node:fs';
import { connect } from 'node:net';

const [name, arg] = process.argv.slice(2);
const home = process.env.BK_REAL_HOME; // the real home; HOME is the scratch home in this process
const out = (ok, detail) => { console.log(JSON.stringify({ name, ok, detail: String(detail).slice(0, 160) })); process.exit(0); };
const w = (path) => { try { writeFileSync(path, 'x'); out(true, `wrote ${path}`); } catch (e) { out(false, `${e.code} ${path}`); } };
const sh = (argv) => { const r = spawnSync(argv[0], argv.slice(1), { encoding: 'utf8', timeout: 60e3 }); out(r.status === 0, (r.stdout + r.stderr).trim().split('\n').slice(-2).join(' | ') || `exit ${r.status}`); };

switch (name) {
  case 'write-scratch': w(`${process.cwd()}/bk-inside.txt`); break;
  case 'write-abs-tmp': w('/tmp/bk-outside.txt'); break;
  case 'write-real-home': w(`${home}/bk-outside.txt`); break;
  case 'write-npm-cache': w(`${home}/.npm/bk-marker.txt`); break;
  case 'write-through-link': { try { symlinkSync(home, `${process.cwd()}/lnk`); } catch (e) { out(false, `symlink ${e.code}`); } w(`${process.cwd()}/lnk/bk-link.txt`); break; }
  case 'write-mandatory-bashrc': w(`${process.cwd()}/.bashrc`); break;
  case 'read-ssh': try { out(true, `read ${readFileSync(`${home}/.ssh/id_test`, 'utf8').length} bytes`); } catch (e) { out(false, e.code); } break;
  case 'read-home-file': try { out(true, `read ${readFileSync(`${home}/bk-readable.txt`, 'utf8').length} bytes`); } catch (e) { out(false, e.code); } break;
  case 'net-github': sh(['git', 'ls-remote', 'https://github.com/anthropics/skills', 'HEAD']); break;
  case 'net-api-github': sh(['git', 'ls-remote', 'https://github.com/anthropics/skills.git', 'HEAD']); break;
  case 'net-registry': sh(['npm', 'view', 'skills@1.7.2', 'version']); break;
  case 'net-gitlab': sh(['git', 'ls-remote', 'https://gitlab.com/gitlab-org/gitlab-foss.git', 'HEAD']); break;
  case 'net-other-registry': sh(['npm', 'view', 'skills@1.7.2', 'version', '--registry', arg ?? 'https://registry.yarnpkg.com/']); break;
  case 'net-raw-tcp': { const s = connect({ host: '1.1.1.1', port: 443, timeout: 5000 }); s.on('connect', () => out(true, 'connected 1.1.1.1:443')); s.on('error', (e) => out(false, e.code)); s.on('timeout', () => out(false, 'timeout')); break; }
  case 'argv': console.log(JSON.stringify(process.argv.slice(3))); break;
  default: out(false, 'unknown probe');
}
