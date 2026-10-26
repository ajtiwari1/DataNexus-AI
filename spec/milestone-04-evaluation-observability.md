# Milestone 04 — Evaluation and observability

## Objective

Create a versioned benchmark for source-level and end-to-end quality, then
instrument graph executions so quality, latency, and failures can be measured
and diagnosed.

## Prerequisites

- Milestone 02 source-specific SQL and RAG paths.
- Milestone 03 integrated graph, answer contracts, source references, and
  failure statuses.
- Milestone 01 optional Langfuse integration and configurable model metadata.

## Scope

### Benchmark design

- Choose a versioned, machine-readable benchmark format with stable case IDs.
- Include representative questions and expected outputs for:
  - SQL results, including joins, filters, aggregations, and empty results.
  - Relevant supporting documents/chunks and acceptable citation targets.
  - Expected calculations with explicit input values and units.
  - Reference answers and required facts/citations.
  - Expected route and acceptable partial/failure behavior where applicable.
- Keep all benchmark data synthetic or otherwise approved for evaluation use.
- Record dataset version, benchmark version, model/provider identifier, and
  evaluation settings with each run.

### Metrics and scoring

- Measure SQL correctness against expected result data with well-defined
  normalization rules.
- Measure retrieval quality at configured K values using relevant-document
  identifiers.
- Measure citation validity and evidence coverage separately from fluency.
- Measure calculation correctness against expected values and tolerances,
  including units and rounding rules.
- Measure end-to-end response correctness, required fact coverage, and
  unsupported-claim rate using reproducible checks where feasible.
- Track latency, timeout/error rate, partial-result rate, and token/usage
  metadata when available.
- Document the limitations of model-based or subjective evaluation and keep
  its scores separate from deterministic checks.

### Evaluation workflow

- Provide a repeatable command or test entry point for the benchmark.
- Support targeted subsets for fast development feedback and full runs for
  release checks.
- Produce a stable machine-readable report and a concise human-readable
  summary.
- Compare results with a prior run when provided; do not silently change
  thresholds or benchmark cases.
- Keep evaluation runs isolated from production data and side effects.

### Langfuse tracing

- Trace request/graph lifecycle, routing, specialist operations, validation,
  retries, source counts/identifiers, timings, and final status.
- Attach non-secret configuration identifiers such as provider/model name and
  prompt/benchmark version.
- Include evidence content only if explicitly approved; prefer IDs, counts,
  and redacted excerpts.
- Propagate trace/run IDs across parallel branches and background work where
  applicable.
- Respect trace disablement and sampling/configuration settings.
- Ensure tracing failures do not silently mask core request failures or cause
  successful responses to be falsely reported as failed.

### Baselines and regression policy

- Run the benchmark on the synthetic dataset and save a baseline report in an
  appropriate project location.
- Set initial regression thresholds only after observing baseline variance.
- Identify which metrics block release and which are informative.
- Review benchmark changes alongside code changes that affect expected outputs.

## Suggested implementation sequence

1. Finalize benchmark case schema and add initial synthetic-data cases.
2. Implement deterministic SQL, retrieval, citation, and calculation scoring.
3. Add end-to-end checks and clearly separated model-judged metrics only where
   useful.
4. Implement subset/full-run command and report formats.
5. Add graph and agent trace metadata with secret/data minimization.
6. Run baseline and assess variance before setting blocking thresholds.
7. Document how to add cases, update versions, and compare runs.

## Deliverables

- Versioned benchmark data and case schema.
- Scorers for SQL, retrieval, citations, calculations, and end-to-end results.
- Repeatable partial/full benchmark workflow and report.
- Langfuse traces for graph/agent execution with safe metadata.
- Baseline report and evaluation-maintenance documentation.

## Validation plan

- Validate benchmark records against the schema and reject missing/duplicate
  case identifiers.
- Test deterministic scorers with correct, incorrect, and boundary values.
- Verify calculation scoring respects documented units and tolerance rules.
- Run benchmark twice on unchanged deterministic data and compare stable
  metrics and report shape.
- Test trace propagation through sequential and parallel branches.
- Test disabled tracing and simulated tracing outages do not alter core
  application behavior.
- Inspect captured trace metadata to confirm secrets and unapproved evidence
  content are excluded.

## Exit criteria

- Benchmark cases cover expected SQL results, supporting documents, expected
  calculations, and reference answers.
- Evaluation is repeatable, versioned, and provides both detailed output and
  a concise summary.
- Quality metrics distinguish source correctness, evidence grounding, and
  answer quality.
- Traces expose request routing, source work, validation, and outcome without
  exposing secrets or unnecessary sensitive content.
- Observability can be disabled/configured without breaking core behavior.

## Risks and decisions to resolve

- Set benchmark size and release thresholds based on variance and project
  quality goals rather than arbitrary initial numbers.
- Decide what data may be retained by Langfuse and how retention/access are
  controlled.
- Avoid overfitting to a small synthetic benchmark; add cases as failure modes
  are discovered.
- Ensure model-based judging is not the sole authority for safety or
  deterministic correctness.
