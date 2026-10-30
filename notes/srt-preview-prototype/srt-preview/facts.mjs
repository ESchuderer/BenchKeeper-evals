// Throwaway: facts checked in the container. Usage: node facts.mjs
import { readdirSync } from 'node:fs';

const { quote } = await import('/tmp/srt/node_modules/@anthropic-ai/sandbox-runtime/dist/utils/shell-quote.js');
console.log('quoted string srt hands to bash -c:', quote(['npx', '-y', 'skills@npm:skills@1.7.2', 'add', 'https://github.com/o/r', '-s', 'a b', '$(id)']));
console.log('srt temp folders left in /tmp (claude-empty-*):', readdirSync('/tmp').filter((n) => n.startsWith('claude-empty')).length);
for (const u of ['https://github.com/anthropics/sandbox-runtime', 'https://github.com/anthropic-experimental/sandbox-runtime']) {
  const r = await fetch(u, { redirect: 'manual' });
  console.log(u, r.status, r.headers.get('location'));
}
const t = await (await fetch('https://docs.podman.io/en/latest/markdown/podman-run.1.html')).text();
const i = t.indexOf('unmask=');
console.log('podman-run doc mentions unmask:', i > 0, t.slice(i - 20, i + 300).replace(/<[^>]+>/g, '').replace(/\s+/g, ' '));
