# pg-skills

[Claude Code](https://docs.claude.com/en/docs/claude-code) **skills** for engineering
PostgreSQL extensions — building, testing, benchmarking, and tuning them. Distilled from real
C/PGXS, Rust/pgrx, GPU/CUDA, and extension+microservice projects.

Packaged as a Claude Code **plugin marketplace** (`.claude-plugin/`) so it installs without
manual symlinks, with each skill under [`skills/`](skills/).

## Skills

| Skill | What it does |
|---|---|
| [`pg-extension-lab`](skills/pg-extension-lab/SKILL.md) | A lab/workbench for PostgreSQL extensions: develop from scratch, **or** design tuning experiments, scenarios, and isolation/regression tests for an existing one. Three architecture shapes (in-process / microservice / out-of-process daemon) across testing, benchmarking, performance, architecture, and accelerator categories. |

## Install

### As a Claude Code plugin (recommended)

```text
/plugin marketplace add ysys143/pg-skills
/plugin install pg-skills
```

Claude Code clones the repo, registers the bundled skills, and handles updates via the plugin
manager. Skills auto-activate by their `description`; invoke one explicitly with
`/pg-extension-lab`.

### Manual (clone + symlink a single skill)

```bash
git clone https://github.com/ysys143/pg-skills.git ~/src/pg-skills
ln -s ~/src/pg-skills/skills/pg-extension-lab ~/.claude/skills/pg-extension-lab
```

## Layout

```
pg-skills/
  .claude-plugin/
    marketplace.json     # marketplace manifest (this repo as a marketplace)
    plugin.json          # plugin manifest; skills: ./skills/
  skills/
    pg-extension-lab/
      SKILL.md           # overview + navigation
      references/        # testing/ benchmarking/ performance/ architecture/ accelerator/
  README.md
  LICENSE
```

## Adding a skill

Create `skills/<name>/SKILL.md` (with YAML frontmatter `name` + `description`), keep heavy
detail in `skills/<name>/references/<category>/`, and add a row to the **Skills** table above.
The plugin manifest's `"skills": "./skills/"` picks it up automatically.

## License

MIT
