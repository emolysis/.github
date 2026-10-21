## Emolysis

A local-first coding agent for data engineering and BI on Databricks, Snowflake and
Microsoft Fabric.

### What it does

Emolysis builds data pipelines and dashboards from a prompt. Instead of writing pipeline
code from scratch, the agent picks a known pipeline shape (batch ingest, incremental
append, CDC merge, SCD Type 2, snapshot, backfill, late-arriving, dedupe / conform,
aggregation / gold, reverse ETL), fills a tested template for your target
platform, and proves it on your machine against DuckDB before anything runs on your
platform.

- **Local first.** You iterate on sampled data on your own machine. Production runs on
  the platform you already use.
- **Platform aware.** Each platform has its own templates, SQL dialect and lint rules,
  so Databricks code is written for Databricks and Snowflake code for Snowflake.
- **Works from your tools.** A CLI (`emo`) and an MCP server (`emo mcp`) for Claude
  Code, Cursor, Codex and other MCP clients.

### Status

In private development. Nothing is released yet: there is no installable build, CLI
or package. The public repositories below are early scaffolds and will change.

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
