# pg-extension-lab

A [Claude Code](https://docs.claude.com/en/docs/claude-code) **skill** for building,
testing, benchmarking, and tuning **PostgreSQL extensions** — distilled from real C/PGXS,
Rust/pgrx, GPU/CUDA, and extension+microservice projects.

It is a lab/workbench, not just a scaffolder: use it to develop an extension from scratch,
**or** to design tuning experiments, write scenarios, and run isolation/regression tests
against an existing one.

## What it covers

Three architecture shapes — **A** pure in-process (C/PGXS or Rust/pgrx), **B** extension +
external microservice, **C** extension + co-located sidecar daemon (GPU/accelerator context,
resident model, JIT pool) — across five reference categories:

| Category | Highlights |
|---|---|
| **testing** | C unit / `pg_regress` golden-file / `pg_isolation_regress` concurrency ladder; red→green discipline |
| **benchmarking** | adversarial correlated fixtures, exact ground truth, matched-recall, SOLID-vs-INDICATIVE trust labeling, the `min_ms` anti-pattern, accelerator-vs-CPU crossover, cost-per-query |
| **performance** | config-Pareto-before-code, recall-QPS frontiers, lock-contention build profiling, resource governance |
| **architecture** | Shape B/C, Rust/pgrx conventions, transactional-outbox NOTIFY/LISTEN workers, external AI/LLM provider integration, security hardening |
| **accelerator** | GPU/CUDA build/ops/benchmark specifics (a specialization, deep path) |

Start at [`SKILL.md`](SKILL.md); each category has a `README.md` index linking to dense,
single-topic detail files (progressive disclosure).

## Install

Clone and symlink into your Claude Code skills directory:

```bash
git clone https://github.com/ysys143/pg-extension-lab.git ~/src/pg-extension-lab
ln -s ~/src/pg-extension-lab ~/.claude/skills/pg-extension-lab
```

Claude Code auto-discovers the skill by its `description` and activates it when you work on a
PostgreSQL extension. You can also invoke it explicitly with `/pg-extension-lab`.

## License

MIT
