# Milestone 01 — Foundation

## Objective

Establish a runnable, configurable application foundation with the core
infrastructure integrations, model selection, a reproducible synthetic
dataset, and baseline tests.

## Scope

### Application and configuration

- Establish the Python project layout for the API, configuration, infrastructure
  adapters, data generation, and tests. Follow repository conventions once
  they exist.
- Create a FastAPI application factory or equivalent testable application
  entry point.
- Define validated settings for application mode, service endpoints, model
  selection, logging, and optional integrations.
- Load secrets from environment or a local ignored environment file. Provide a
  safe example configuration containing placeholders, not credentials.
- Document required versus optional settings and make invalid configuration
  errors actionable without printing secret values.

### Service integrations

- Configure PostgreSQL connection lifecycle and a repeatable schema
  initialization/migration path.
- Configure Qdrant connection lifecycle and a named collection setup/reset
  path appropriate to local development.
- Add explicit readiness checks for PostgreSQL and Qdrant; keep liveness
  independent of optional external integrations.
- Add LangGraph as the graph/orchestration foundation, but defer multi-agent
  business flows to Milestone 03.
- Integrate Langfuse behind configuration. Core startup and tests should work
  when tracing is disabled.
- Ensure startup/shutdown owns and closes resources cleanly.

### Model factory

- Define the supported provider interface and a factory that selects a
  provider/model from validated configuration.
- Keep provider credentials out of source and traces.
- Make unsupported providers, missing required settings, and provider
  initialization failures explicit.
- Support dependency injection or a lightweight fake implementation so
  application and factory tests do not require paid or remote model calls.
- Choose the initial provider set during implementation based on available
  dependencies and project requirements; do not assume a provider in advance.

### Synthetic enterprise dataset

- Define a small but coherent enterprise scenario with related records and
  documents suitable for later SQL, RAG, and joined-question testing.
- Generate deterministic identifiers and values from a fixed seed or checked-in
  source data.
- Include cross-references between relational rows and source documents where
  useful for citation tests.
- Provide a command/script to initialize, reload, and reset local data safely.
- Document the dataset's fictional nature and intended test use.

### Developer experience

- Document environment setup, required service startup, application launch,
  health checks, and test commands.
- Add a minimal dependency/service check so missing local services fail with
  direct guidance.
- Add baseline formatting, linting, and test commands only in line with the
  project's chosen toolchain.

## Suggested implementation sequence

1. Establish project/dependency configuration and validated settings.
2. Build the FastAPI app and liveness/readiness behavior.
3. Add PostgreSQL and Qdrant lifecycle/configuration.
4. Add optional Langfuse and LangGraph wiring.
5. Implement and test the configurable model factory with fakes.
6. Define and load deterministic synthetic data.
7. Complete setup documentation and run the focused test suite from a clean
   local configuration.

## Deliverables

- Runnable FastAPI service with health and readiness endpoints.
- Documented settings contract and safe example environment file.
- PostgreSQL and Qdrant setup/reset path.
- Optional tracing integration and graph foundation.
- Configurable model factory with test doubles.
- Synthetic data and reproducible load/reset command.
- Baseline tests and developer setup instructions.

## Validation plan

- Unit-test settings validation, defaults, missing required values, and secret
  redaction.
- Test application liveness without external dependencies.
- Test readiness response for healthy and unavailable required services.
- Test model factory selection, unsupported provider, missing credentials, and
  provider construction failure using fakes.
- Verify dataset generation/load produces stable counts, identifiers, and
  relationships on repeated runs.
- Run PostgreSQL/Qdrant integration tests when local services are available;
  keep these distinct from unit tests.
- Verify disabled Langfuse does not require credentials or network access.

## Exit criteria

- A developer can follow the documented steps to configure and start the
  application and required local dependencies.
- Liveness and readiness are distinct and readiness identifies unavailable
  required services.
- Data loading is reproducible and reset behavior is documented.
- Model configuration is provider-selectable and failures are explicit.
- Tests run without real model credentials or remote model calls.
- No credentials or private data are committed or emitted in logs.

## Risks and decisions to resolve

- Choose dependency manager, local service orchestration, migration tool, and
  supported Python version based on project requirements.
- Confirm the first model provider(s) and whether a local development provider
  is required.
- Confirm whether Langfuse is strictly optional in every environment.
- Keep the synthetic dataset small enough for fast tests but rich enough to
  support later calculations and citations.
