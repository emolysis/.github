<img src="https://github.com/emolysis/.github/raw/main/profile/banner.png" alt="EMOLYSIS. An entire data team. One download. The agentic lakehouse for data engineering and analytics." width="100%">

## An entire data team. One download.

Emolysis is the agentic lakehouse for data engineering and analytics.

A team of agents you direct from your laptop: to investigate business questions, develop
dashboards, and build and test pipelines for your data platform.

### What it does

Business users want answers to the questions that matter. Data teams need the
definitions, transformations and pipelines behind those answers. Emolysis brings these
needs into one development workflow, with you directing the work and reviewing the
results.

- **From the question to the dashboard.** You start from a business question, find the
  sources, confirm the metric definition, and get the dashboard and the tested pipeline
  behind it.
- **Developed and tested locally.** You iterate on sampled data on your own machine and
  test each pipeline against DuckDB before it runs anywhere else. Prompts go to the
  model provider you choose.
- **Built for your platform.** Each pipeline starts from a known shape (batch ingest,
  incremental append, CDC merge, SCD Type 2, snapshot, backfill, late-arriving,
  dedupe / conform, aggregation / gold, reverse ETL) and a template written for your
  target platform, with its own SQL dialect and rules. Production pipelines run on the
  platform you already use: Databricks first, Snowflake and Microsoft Fabric next.
- **Works from your tools.** One download: a desktop app with a CLI (`emo`) and an MCP
  server (`emo mcp`) for Claude Code, Cursor, Codex and other MCP clients. An Emolysis
  account is required.

### Status

In private development. Nothing is released yet: there is no installable build, CLI
or package. Early access is by invitation. The public repositories below are early
scaffolds and change often.

### Public repositories

- [integrations](https://github.com/emolysis/integrations) — Claude Code plugin,
  Cursor and Codex configuration, and the `@emolysis/mcp` shim that connects MCP clients
  to Emolysis.
- [template-sdk](https://github.com/emolysis/template-sdk) — the pipeline template
  format, a validator and an SDK for writing your own templates.
- [.github](https://github.com/emolysis/.github) — this profile, default issue and pull
  request templates, and a preview of the reusable `emo check` workflow.

### Security

Report vulnerabilities privately; see the
[security policy](https://github.com/emolysis/.github/blob/main/SECURITY.md).
