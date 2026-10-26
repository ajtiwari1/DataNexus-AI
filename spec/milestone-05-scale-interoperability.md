# Milestone 05 — Scale and interoperability

## Objective

Harden the system for sustained use and approved integrations by adding
measured operational capabilities, access controls, and deployment guidance.
Treat each item as a scoped feature with its own acceptance evidence rather
than adopting infrastructure speculatively.

## Prerequisites

- Milestone 01 service configuration and lifecycle.
- Milestones 02–03 bounded source and graph interfaces.
- Milestone 04 benchmark, tracing, and baseline latency/failure measurements.

## Scope

### Access control and data boundaries

- Define identity, organization/tenant, roles, and authorization policy based
  on actual deployment requirements.
- Enforce access checks before SQL execution, document retrieval, tool use,
  checkpoint resume, cached response use, and job execution.
- Scope database queries, Qdrant filters, cache keys, checkpoint identity, and
  background jobs consistently to the authorized principal/tenant.
- Use least-privilege service credentials and protect service-to-service
  secrets.
- Audit security-relevant actions without logging secrets or full sensitive
  evidence.
- Add tests that attempt cross-user and cross-tenant access at each entry
  point.

### MCP tools

- Select only stable, approved application capabilities to expose as MCP
  tools.
- Define tool names, input/output schemas, descriptions, and error contracts.
- Reuse application validation, query limits, authorization, and source
  reference behavior; do not create a less-protected alternate execution path.
- Apply request timeouts, output-size limits, and tool concurrency controls.
- Test malformed input, unauthorized access, dependency failure, and
  unsupported operations.
- Document how tools are configured, authenticated, and run by an MCP client.

### Durable background jobs

- Identify operations that need to survive request/process termination, such
  as large ingestion or benchmark tasks; keep normal interactive queries
  synchronous unless evidence supports a change.
- Define job request, status, progress, result, retry, cancellation, and
  expiration contracts.
- Persist jobs using a selected durable backend and make job execution
  idempotent where retries are possible.
- Bound retries, execution time, queue depth, and per-tenant concurrency.
- Re-check authorization at enqueue and execution time.
- Trace jobs with stable IDs and ensure failures are visible to operators and
  callers.

### Caching

- Use Milestone 04 measurements to choose high-value, safe cache candidates.
- Define cache key composition, TTL, invalidation, and data/model version
  semantics.
- Include tenant/authorization scope and relevant model, prompt, embedding,
  and source-data versions in keys as appropriate.
- Avoid caching sensitive results in shared scopes or returning stale data
  after access revocation.
- Track hit/miss rate and stale/invalidation behavior without exposing
  sensitive payloads.
- Test isolation, invalidation, expiration, and cache backend failure.

### Concurrency and backpressure

- Set explicit concurrency limits for model calls, database work, retrieval,
  MCP tools, and background workers.
- Use bounded queues/semaphores and define overload responses and retry
  guidance.
- Ensure cancellation and timeout behavior releases resources.
- Avoid retry storms by using bounded retry policies and backoff for transient
  failures only.
- Tune limits from baseline load tests and observed service capacity.

### Deployment and operations

- Select deployment target and document required services, environment
  variables, networking, secrets, migrations, and startup ordering.
- Provide deployment configuration with health checks, graceful shutdown, and
  safe resource limits.
- Define backup/restore and data migration expectations for persistent
  application data.
- Document logs, traces, metrics, operational alerts, and common dependency
  failure recovery.
- Include a non-production deployment validation procedure and rollback
  approach.
- Keep production secrets out of repository files and container images.

### A2A decision

- Assess whether agent capabilities need independent deployment, ownership,
  scaling, or lifecycle boundaries that justify A2A.
- Document the decision and evidence. If services remain within one
  application, defer A2A rather than adding a protocol without a use case.
- If justified, define authentication, service discovery, versioning, failure,
  and trust boundaries before implementation.

## Suggested implementation sequence

1. Review benchmark and operational data to identify actual bottlenecks and
   target deployment needs.
2. Define identity/authorization boundaries and test isolation across existing
   interfaces.
3. Expose the smallest useful set of MCP tools through existing service
   contracts.
4. Add durable jobs only for operations that need asynchronous persistence.
5. Add cache only to measured safe candidates and establish invalidation.
6. Add concurrency controls and load-test overload/failure behavior.
7. Build deployment configuration, operational documentation, and recovery
   checks.
8. Make and document an evidence-based A2A go/no-go decision.

## Deliverables

- Authorization policy enforced across user, tool, cache, job, and checkpoint
  boundaries.
- MCP server/tools with validated contracts and documented setup.
- Durable job path for selected operations, including status and failure
  handling.
- Measured, scoped caching with invalidation and isolation.
- Concurrency limits and backpressure behavior.
- Deployment configuration, operational/runbook guidance, and recovery plan.
- A2A decision record within this milestone plan or an appropriate project
  design document.

## Validation plan

- Test denied and allowed access for each resource path, including tenant
  isolation.
- Test MCP tool schema validation, permissions, limits, and error responses.
- Test job restart recovery, bounded retry, idempotency, cancellation, and
  authorization re-check.
- Test cache isolation, invalidation after data/access changes, expiry, and
  backend outage behavior.
- Load-test configured concurrency limits and verify overload is bounded and
  clearly reported.
- Validate deployment health checks, graceful shutdown, migration/startup
  behavior, and secret injection using a non-production environment.
- Verify backup/restore or documented equivalent for persistent state.

## Exit criteria

- All exposed entry points enforce consistent authorization and limits.
- Durable work survives process interruption and has observable terminal
  states.
- Cache results cannot cross access boundaries and have a tested invalidation
  strategy.
- Concurrency and overload are bounded with clear caller/operator behavior.
- Deployment and operational procedures are documented and validated outside
  a developer-only environment.
- A2A is implemented only if the documented service-boundary decision
  justifies it.

## Risks and decisions to resolve

- Authentication, tenancy, deployment platform, and compliance needs must be
  known before finalizing access-control and retention designs.
- Select job/cache technologies based on existing infrastructure and measured
  needs, not as prerequisites to application correctness.
- Ensure caches and durable state do not outlive authorization or data
  retention policy.
- Do not interpret "scale and interoperability" as a requirement to adopt all
  listed technologies regardless of need.
