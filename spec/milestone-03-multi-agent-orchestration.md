# Milestone 03 — Multi-agent orchestration

## Objective

Coordinate the independently tested SQL and document capabilities through a
supervised LangGraph workflow with explicit state, bounded validation, optional
parallel work, checkpoints, and reliable failure behavior.

## Prerequisites

- Milestone 01 graph/model configuration and service lifecycle.
- Milestone 02 standalone SQL and document RAG interfaces, answer contracts,
  and source references.

## Scope

### Shared state and graph contracts

- Define typed graph input, shared state, node result, and final response
  schemas.
- Store only data needed for routing, evidence, validation, and recovery; avoid
  putting credentials or unnecessary sensitive content into checkpoint state.
- Represent each specialist's status and result independently so partial
  completion is explicit.
- Establish limits for question size, total graph steps, execution time,
  validation attempts, and evidence size.

### Supervisor and routing

- Add a supervisor that selects SQL, document RAG, both, or a clear
  clarification/unsupported path.
- Provide a deterministic routing fallback for known request types where
  practical; do not let untrusted model output invoke arbitrary tools.
- Record a brief routing rationale for tracing and debugging, while ensuring
  the final response is based on validated specialist outputs.
- Reject or safely handle requests outside supported capabilities.

### Parallel and sequential execution

- Run SQL and document retrieval concurrently when both can answer the
  question independently.
- Run dependent nodes sequentially when later work requires earlier results.
- Merge outputs deterministically and retain the originating source and
  status for every evidence item.
- Bound concurrent execution per request and ensure cancellation/timeout is
  propagated to outstanding work.

### Validation and answer composition

- Validate that requested specialists completed or failed explicitly.
- Validate citations against evidence actually returned by specialist nodes.
- Check required output structure, evidence coverage, and answer completeness.
- Add a bounded repair/retry loop for correctable validation failures.
- Stop after the configured attempt limit and return a clear failure or
  partial-result response with available evidence.
- Avoid claiming calculations or facts not supported by the specialist
  results.

### Checkpoints and recovery

- Configure checkpointing behind an explicit persistence setting and define the
  thread/conversation identity requirements.
- Ensure checkpoint state is isolated between users/tenants.
- Define which workflow states may be resumed and prevent accidental replay of
  non-idempotent operations.
- Set retention/cleanup behavior and avoid persisting sensitive content unless
  required and protected.
- Test interrupted execution and resume behavior using the selected backend.

### Failure handling

- Handle specialist timeout, provider error, malformed tool/model response,
  checkpoint failure, and validation exhaustion.
- For one failed specialist, preserve successful independent results and
  indicate the missing source in the response.
- For total failure, return an explicit error rather than an empty successful
  answer.
- Apply bounded retries only to transient, safe-to-repeat operations; expose
  retry exhaustion and failure category.
- Keep logs and traces free of credentials and avoid leaking restricted
  evidence in error messages.

## Suggested implementation sequence

1. Define graph state and node contracts using the Milestone 02 result types.
2. Implement deterministic single-source routes through the graph.
3. Add supervisor-based source selection and unsupported/clarification paths.
4. Add parallel execution for independent SQL and document branches.
5. Add deterministic merge, citation checks, and final answer composition.
6. Add bounded validation repair and failure/partial-result handling.
7. Add configured checkpointing and user/thread isolation.
8. Run orchestration tests with fakes before service-backed integration tests.

## Deliverables

- Typed supervisor graph state and node interfaces.
- Routing and parallel execution for SQL and document RAG.
- Deterministic evidence merge and validated final answer.
- Checkpoint persistence/resume configuration.
- Bounded retry, timeout, partial-result, and failure behavior.
- Graph unit and integration tests.

## Validation plan

- Test routing to SQL, RAG, both, and unsupported/clarification outcomes.
- Test parallel branches complete independently and preserve correct source
  attribution.
- Test a specialist failure alongside a successful specialist returns an
  explicitly partial result.
- Test citation validation rejects IDs not present in specialist evidence.
- Test validation retries stop at the configured bound.
- Test timeouts cancel or safely abandon outstanding work and report status.
- Test checkpoint resume, isolation across thread/user identities, and
  non-resumption after terminal failure.
- Test graph limits prevent unbounded loops or excessive evidence accumulation.

## Exit criteria

- The supervisor can route requests to one or both single-source capabilities.
- Parallel execution is restricted to independent work and merges
  deterministically.
- Every returned claim/source reference is tied to specialist evidence.
- Retries, graph steps, execution time, and evidence growth are bounded.
- Partial success, total failure, and checkpoint behavior are explicit and
  automated-test covered.

## Risks and decisions to resolve

- Decide checkpoint backend, retention, encryption, and tenant/thread identity.
- Keep model-based routing from expanding tool permissions or bypassing
  source-level validation.
- Establish trace/checkpoint policies for sensitive prompts and retrieved
  content.
- Confirm whether validation should use deterministic rules, a model-based
  judge, or both; deterministic safety checks must remain authoritative.
