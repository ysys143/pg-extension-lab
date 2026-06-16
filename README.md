# pg-extension-lab

**pg-extension-lab is a harness for developing, testing, benchmarking, and tuning a
PostgreSQL extension — validating observable behavior in an isolated, reproducible
environment, separately from the implementation.**

> pg-extension-lab은 PostgreSQL 익스텐션의 동작을 격리된 환경에서 구현(코드)과 분리해
> 테스트·벤치마크·튜닝하는 하네스입니다.

A [Claude Code](https://docs.claude.com/en/docs/claude-code) skill, distilled from real
C/PGXS, Rust/pgrx, GPU/CUDA, and extension+microservice projects. Use it to build an
extension from scratch, **or** to design tuning experiments, write scenarios, and run
isolation/regression tests against an existing one. Packaged as a Claude Code **plugin
marketplace** (`.claude-plugin/`) so it installs without manual symlinks.

## What's inside

The skill lives at [`skills/pg-extension-lab/`](skills/pg-extension-lab/SKILL.md): three
architecture shapes (in-process / microservice / out-of-process daemon) across five reference
categories — **testing** (C unit / `pg_regress` golden-file / `pg_isolation_regress`
concurrency), **benchmarking** (matched-recall, trust labeling, accelerator-vs-CPU crossover,
cost-per-query), **performance** (resource-vs-performance Pareto, governance), **architecture**
(Rust/pgrx, async outbox workers, external-provider integration, security), and **accelerator**
(GPU/CUDA specifics).

## Install

### As a Claude Code plugin (recommended)

```text
/plugin marketplace add ysys143/pg-extension-lab
/plugin install pg-extension-lab
```

Claude Code clones the repo, registers the bundled skill, and handles updates via the plugin
manager. The skill auto-activates by its `description`; invoke it explicitly with
`/pg-extension-lab`.

### Manual (clone + symlink)

```bash
git clone https://github.com/ysys143/pg-extension-lab.git ~/src/pg-extension-lab
ln -s ~/src/pg-extension-lab/skills/pg-extension-lab ~/.claude/skills/pg-extension-lab
```

## Layout

```
pg-extension-lab/
  .claude-plugin/
    marketplace.json     # this repo as a Claude Code marketplace
    plugin.json          # plugin manifest; skills: ./skills/
  skills/
    pg-extension-lab/
      SKILL.md           # overview + navigation
      references/        # testing/ benchmarking/ performance/ architecture/ accelerator/
  README.md
  LICENSE
```

The `skills/` layout leaves room to add more skills later (`skills/<name>/SKILL.md`); the
plugin manifest's `"skills": "./skills/"` picks them up automatically.

## License

MIT
