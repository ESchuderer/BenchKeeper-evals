# Rule file review prompt: fixture check

Throwaway research for issue #531. `prompt.txt` is the fixed review prompt, `fixtures/` holds one rule file per problem kind plus a clean one, `expected.json` the findings each should yield (kind and first line). `bash run.sh claude [model]` or `bash run.sh codex [model]` runs the prompt once per fixture in an empty folder with no tools and prints PASS or FAIL per fixture, time, cost and tokens. Each run spends a few cents of the signed-in account.
