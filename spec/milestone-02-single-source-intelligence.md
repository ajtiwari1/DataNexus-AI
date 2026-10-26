# Milestone 02 — Single-source intelligence

## Objective

Deliver structured-data question answering and document retrieval as separate,
bounded, independently testable capabilities. Each path must return answers
with evidence that can be inspected and validated.

## Prerequisites

- Milestone 01 application configuration, PostgreSQL/Qdrant setup, model
  factory, and synthetic enterprise dataset.
- Stable identifiers or metadata fields for records and documents that can be
  surfaced as references.

## Scope

### Shared request and answer contracts

- Define typed request, answer, error, and source-reference structures.
- Include a stable source type and identifier, concise display metadata, and
  enough context for a caller to inspect the evidence.
- Set explicit maximum question length, number of results, and response size.
- Distinguish no evidence found from service failure and from answer
  generation/validation failure.
- Preserve the original evidence returned by SQL/retrieval rather than relying
  only on a model-generated explanation.

### SQL intelligence

- Discover usable schemas, tables, columns, types, and relevant foreign-key
  relationships from PostgreSQL metadata.
- Exclude internal/system schemas and allow an explicit schema/table allowlist.
- Present schema context in a bounded form suitable for query generation.
- Generate or construct SQL from the user's question using the configured
  model, with a clearly typed boundary between generation and execution.
- Validate the SQL before execution. Enforce read-only behavior at both the
  query-validation layer and database-credential/transaction layer.
- Reject multi-statement input and disallowed operations; do not rely on
  prompt instructions as the security boundary.
- Apply configurable statement timeout, maximum returned rows, and maximum
  schema context size.
- Return the executed query in a safe/normalized representation when
  appropriate, the bounded result data, and references identifying the
  records/tables used.
- Make empty results, rejected SQL, timeout, and database errors explicit.

### Document RAG

- Define document ingestion metadata, including stable document ID, title,
  source, timestamps/version where available, and access metadata needed by
  later security work.
- Implement deterministic chunking with source offsets or page/section
  metadata retained for citation.
- Generate embeddings through a configurable integration and store vectors and
  metadata in Qdrant.
- Make ingestion idempotent or provide a documented replace/reindex operation.
- Retrieve a bounded number of relevant chunks using configurable thresholds
  and filters.
- Generate answers grounded in retrieved chunks and attach document references
  with enough location detail to locate the cited text.
- Return an explicit no-relevant-evidence result when retrieval is empty or
  below the configured threshold.

### Retrieval evaluation

- Create an initial small evaluation set mapping questions to relevant
  document/chunk identifiers.
- Implement a repeatable evaluation command or test that measures retrieval
  quality at configured K values.
- Record dataset/version and retrieval settings with evaluation output.
- Keep the initial evaluation independent of supervisor orchestration.

## Suggested implementation sequence

1. Define answer, evidence, and error contracts shared by both source paths.
2. Add SQL schema discovery and verify its allowlist and size bounds.
3. Implement SQL generation/validation/execution with read-only and limit
   enforcement.
4. Add SQL source references and test query/result behavior.
5. Add document metadata, chunking, embedding, and Qdrant indexing.
6. Implement retrieval, grounded answer generation, and document citations.
7. Create the first retrieval evaluation set and repeatable evaluator.
8. Add standalone interfaces/routes or commands for each capability, without
   coupling them to a supervisor.

## Deliverables

- Typed source reference and answer contracts.
- Bounded SQL schema discovery and question-answering path.
- Read-only SQL execution with time/result limits.
- Document ingestion, indexing, retrieval, and cited-answer path.
- Initial document retrieval evaluation set and report command.
- Component, integration, and failure-path tests for both capabilities.

## Validation plan

- Test schema discovery against the synthetic schema and confirm excluded
  schemas/tables do not appear.
- Test malformed, multi-statement, write, and disallowed SQL is rejected
  without database mutation.
- Test row limits and statement timeout behavior.
- Test record references for empty, single-table, and joined results.
- Test deterministic chunk boundaries and preservation of source locations.
- Test repeated ingestion behavior and document replacement/deletion.
- Test retrieval citations refer to retrieved chunk IDs and source locations.
- Test empty and low-relevance retrieval does not produce an unsupported
  success-shaped answer.
- Run retrieval evaluation twice and confirm stable output for the same data
  and settings.

## Exit criteria

- SQL and document RAG can be invoked and tested separately without LangGraph
  supervisor routing.
- SQL execution is read-only by design and bounded by configured limits.
- Answers expose their evidence through stable source references.
- Missing evidence and dependency errors are distinguishable.
- Retrieval evaluation is repeatable and reports its dataset/settings.

## Risks and decisions to resolve

- Choose SQL validation approach and ensure it is complemented by database
  permissions and timeouts.
- Decide how to represent record-level citations without leaking sensitive
  fields.
- Select embedding model and establish how embedding model/version changes
  trigger reindexing.
- Define tenant/access filters early enough that retrieval APIs do not assume
  globally visible documents.
