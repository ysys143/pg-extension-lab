# Experiment ledger — [campaign name]

<!--
The ledger is the authoritative state of a multi-session experiment campaign: which
hypotheses are live, which cells were spent, what changed in the environment. Read it FIRST
at the start of every session (human or agent) and commit every update — an agent must never
re-plan from memory what the ledger already records. One ledger per campaign, next to the
configs and reports it indexes.
-->

- campaign goal: [one sentence — what decision will this campaign settle?]
- started: [YYYY-MM-DD]
- status: active | concluded
- decision reached: [fill when concluded, with the report that settles it]

## Hypotheses

| id | claim (falsifiable) | status | evidence artifact |
|---|---|---|---|
| H1 | [claim] | open / survived / failed / narrowed | [results_*.json + REPORT_*.md] |

## Runs spent

| date | config (path @ commit) | cells | run_id | artifact | verdict |
|---|---|---|---:|---|---|
| [YYYY-MM-DD] | [bench_config.toml @ abc1234] | [n] | [id] | [results_*.json] | [one line] |

## Environment changes

Anything that invalidates comparison across the rows above: host, PG version, extension
commit, dataset regeneration, GUC defaults.

| date | change | runs affected |
|---|---|---|

## Parameter-space state

- axes retired (knee/cliff located, no longer worth cells): [axis: finding]
- axes still open: [axis: what would change a decision]
- budget remaining vs `parameter_space.toml` [budget]: [n cells / m minutes]

## Open questions / next session

- [ ] [next smallest check that can disprove a live hypothesis]
