# Accelerator crossover report — example layout

> **Illustrative layout, not a measurement.** Angle-bracket fields are placeholders that show
> the shape of a crossover report: stage, ring, a conclusion line, per-metric trust labels, and
> the reproduce command. A real report is generated from result artifacts, named `REPORT_*.md`,
> and must pass `validation/lint_report.py`.

- run_id: `<run_id>`
- stage: forced physical curve
- ring: A
- conclusion: smoke only; no accelerator claim
- command: `<exact command that produced the artifact>`

| target | rows | dims | k | recall (SOLID) | qps (INDICATIVE) |
|---|---:|---:|---:|---:|---:|
| cpu-reference | `<rows>` | `<dims>` | `<k>` | `<recall>` | `<qps>` |
| `<accelerated target>` | `<rows>` | `<dims>` | `<k>` | `<recall>` | `<qps>` |

## Reproduce

```bash
<exact commands, one per artifact>
```
