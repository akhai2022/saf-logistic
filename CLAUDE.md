# CLAUDE.md

## Mission

This repository is an existing production-oriented full-stack application built with:

- **Backend:** Python + FastAPI
- **Frontend:** Next.js + React
- **Deployment:** AWS

All work in this repository must meet a **professional production-grade standard** for:

- architecture
- code quality
- UX/UI quality
- security
- testing
- observability
- deployment safety
- maintainability

The required standard is not “working code.”
The required standard is:
      
- correct
- secure
- tested
- maintainable
- observable
- production-ready

This repository is assumed to be an **existing project**, not a greenfield codebase, unless explicitly stated otherwise.

---

## Non-Negotiable Operating Rules

1. **Check existing implementation first**
   - Never start by inventing a new architecture blindly.
   - Always inspect the current code paths, current patterns, and current tests in the affected area first.

2. **Preserve good existing conventions**
   - Reuse good patterns already in the codebase.
   - Improve weak areas incrementally.
   - Do not introduce unnecessary rewrites.

3. **Production-first mindset**
   - Every change must consider:
     - validation
     - security
     - logging
     - metrics
     - failure modes
     - performance
     - deployability
     - rollback safety

4. **Tests are mandatory**
   - No meaningful code change is complete without automated tests.
   - No bugfix is complete without a regression test.

5. **UX/UI quality is mandatory**
   - Frontend work must include loading, empty, error, success, and responsive states.
   - Accessibility is required, not optional.

6. **No shallow fixes**
   - Do not patch symptoms while ignoring obvious structural issues in the touched area.
   - Fix the root cause where safely possible.

7. **No silent failure**
   - Do not swallow exceptions.
   - Do not hide broken states.
   - Surface actionable errors with proper logging and user-safe messaging.

8. **No fake production readiness**
   - Do not claim a change is production-ready if testing, security, observability, or deployment implications are missing.

---

## Existing Project First Rule

This is an existing codebase.

Before implementing any feature, refactor, bugfix, or enhancement, always first identify:

- which files currently own the behavior
- which architectural pattern is currently used there
- which shared components/services/utilities already exist
- which tests already cover that area
- what UX/UI pattern already exists in that area
- what deployment impact the change could have

For every non-trivial task, the expected order is:

1. current state assessment
2. identified problems or gaps
3. proposed safe change plan
4. implementation
5. tests
6. rollout / validation notes

Do not introduce a new architectural style unless the current one is clearly broken or the change explicitly requires a deliberate migration.

If the project contains inconsistent patterns:

- prefer the strongest existing pattern in the local area
- standardize locally when touching that area
- do not trigger broad rewrites unless explicitly requested

---

## Required Existing Project Audit

Before meaningful implementation, inspect and summarize the affected area.

### Backend audit checklist

- application entrypoint
- router registration
- dependency injection usage
- config and environment loading
- auth and authorization flow
- error handling approach
- database session pattern
- model / schema separation
- service / repository separation
- background jobs or async workflows
- logging and observability
- current test coverage and gaps

### Frontend audit checklist

- App Router or Pages Router usage
- layout structure
- feature/module organization
- data fetching approach
- state management approach
- form handling
- validation approach
- styling system
- shared UI components
- accessibility quality
- responsive behavior
- current test setup and gaps

### Delivery audit checklist

- lint commands
- typecheck commands
- unit test commands
- integration test commands
- E2E test commands
- build commands
- deployment sequence
- migration process
- rollback readiness

No major implementation should proceed without checking the existing affected area first.

---

## Core Engineering Principles

1. **Prefer simplicity over cleverness**
   - Choose the simplest solution that is correct, testable, and maintainable.

2. **Optimize for maintainability**
   - Code should be understandable by another engineer months later.

3. **Strong boundaries**
   - Validate and type all boundary inputs and outputs.
   - Keep API, business logic, and persistence concerns separated.

4. **Explicit over implicit**
   - Prefer clear naming, explicit contracts, and predictable control flow.

5. **Correctness before optimization**
   - Performance matters, but not at the expense of correctness or clarity.

6. **Evidence-driven improvement**
   - Do not optimize or refactor blindly.
   - Use concrete findings from the current codebase.

---

## Architecture Rules

## Backend structure

Preferred backend organization:

- `app/api/` → FastAPI routers / HTTP layer
- `app/schemas/` → Pydantic request/response schemas
- `app/services/` → business logic
- `app/repositories/` → persistence access
- `app/models/` → ORM models
- `app/core/` → config, security, shared utilities
- `app/db/` → session, migrations, seed helpers
- `app/tests/` → tests

Rules:

- route handlers must stay thin
- business logic must not live in routers
- repository/database logic must not be mixed into route handlers
- services must be testable without FastAPI request objects
- avoid circular dependencies
- avoid giant multi-purpose modules

## Frontend structure

Preferred frontend organization:

- `src/app/` or `src/pages/` → routing and top-level entrypoints
- `src/features/` → feature-scoped logic and UI
- `src/components/` → reusable shared components
- `src/lib/` → API clients, config, utilities
- `src/types/` → shared types
- `src/styles/` → tokens, globals, styling system
- `src/tests/` → shared test helpers

Rules:

- do not put heavy business logic inside React components
- do not duplicate shared UI patterns
- do not mix multiple state or fetch patterns in the same feature without reason
- feature logic should be modular and composable
- presentation and stateful logic should be separated when complexity grows

---

## Backend Standards (Python + FastAPI)

## Python rules

- use type hints everywhere
- public functions should be explicitly typed
- avoid global mutable state
- prefer explicit dependency injection
- prefer readable code over dense abstractions
- use docstrings for non-trivial public behavior

## FastAPI rules

- use routers organized by domain
- define explicit request and response schemas
- keep endpoints focused on:
  - parsing input
  - auth context
  - service invocation
  - response mapping
- use correct HTTP status codes
- ensure protected routes enforce auth and authorization server-side

## Schema rules

- validate all inbound payloads with Pydantic
- separate request schemas from response schemas
- never expose raw ORM models directly
- use explicit field constraints
- reject malformed or unexpected data early

## Service layer rules

- business logic belongs in services
- services should be deterministic and testable
- services may orchestrate repositories, queues, external APIs, and domain rules
- split complex workflows into smaller composable functions

## Repository / database rules

- isolate database access clearly
- avoid leaking ORM details into service or API layers
- prevent N+1 queries
- use transactions for multi-step write operations
- design idempotency for retry-prone actions
- use pagination for collection endpoints
- never allow unbounded data fetches in production APIs

## Error handling rules

- define consistent exception handling for:
  - validation errors
  - unauthorized
  - forbidden
  - not found
  - conflict
  - rate limiting
  - external dependency failure
  - internal server error
- map internal exceptions to stable API responses
- never expose stack traces or secrets in API responses
- log errors with sufficient operational context

## Async rules

- use async only where appropriate
- avoid blocking I/O inside async endpoints
- use background processing for slow non-request-critical work
- do not mix sync/async carelessly

---

## Frontend Standards (Next.js + React)

## React rules

- use functional components
- keep components focused and composable
- isolate client-side interactivity cleanly
- avoid monolithic page components
- prefer reuse of existing quality components before creating new ones

## Data fetching rules

- standardize API access via shared clients/hooks/utilities
- explicitly handle:
  - loading
  - empty
  - partial
  - error
  - success
- avoid unnecessary duplicate fetching
- avoid request waterfalls when possible
- use caching thoughtfully

## State management rules

- use local state first
- use server-state patterns for remote data
- use global state only for genuine cross-cutting needs
- do not duplicate backend truth on the client unnecessarily

## Form rules

Every form must include:

- clear labels
- typed validation
- accessible error messages
- loading / submitting state
- duplicate submit protection
- sensible defaults where appropriate
- success feedback or next-step guidance

## UI component rules

- prefer shared primitives for repeated patterns
- improve shared components instead of cloning them
- avoid one-off ad hoc styling when a reusable pattern should exist
- use semantic HTML first

---

## UX/UI Quality Standard

Every frontend change must meet a professional UX/UI baseline.

Each feature or screen must be reviewed for:

- visual consistency
- clarity of actions
- information hierarchy
- accessibility
- responsiveness
- loading state
- empty state
- error state
- success state
- predictable navigation
- low-friction task completion

## UI rules

- use consistent spacing
- use consistent typography hierarchy
- use reusable components/tokens where possible
- avoid inconsistent button and form styles
- prefer clean, professional UI over flashy or inconsistent UI

## UX behavior rules

Every flow must explicitly handle:

- initial load
- slow network
- empty results
- partial results
- validation failure
- server failure
- permission failure
- success feedback
- retry path
- cancellation/backout path where relevant

## Accessibility baseline

Minimum required accessibility:

- semantic HTML
- keyboard navigation
- visible focus states
- correct label/input relationships
- accessible icon buttons
- sufficient contrast
- alt text for meaningful images
- ARIA only when needed

Accessibility is mandatory.

---

## API Contract Rules

Every endpoint must define:

- purpose
- auth requirement
- request schema
- response schema
- error cases

Rules:

- breaking API changes are forbidden without explicit approval
- keep contracts stable and predictable
- prefer nouns for resources
- use consistent naming
- use ISO 8601 timestamps
- use stable IDs
- support pagination/filtering/sorting when appropriate
- avoid ambiguous response shapes

---

## Security Guardrails

Security is a default requirement, not an enhancement.

## Authentication

- centralize auth logic
- validate tokens/session on every protected request
- protect refresh/session flows
- enforce expiration/revocation strategy

## Authorization

- enforce authorization on the backend
- never trust frontend-only access control
- check object-level permissions where needed
- validate tenant/user ownership for protected resources

## Secrets management

- never hardcode secrets
- never commit credentials
- use AWS-managed secret storage in production
- minimize secret scope
- rotate secrets appropriately

## Input/output safety

- validate all inputs
- sanitize untrusted content when required
- protect against:
  - injection
  - XSS
  - CSRF where applicable
  - SSRF
  - unsafe redirects
  - insecure file handling
- encode/escape UI-rendered untrusted content

## Data protection

- encrypt data in transit
- use proper at-rest protections for sensitive data
- minimize PII retention
- redact secrets and sensitive fields from logs
- audit sensitive operations where appropriate

## Abuse protection

- apply rate limiting on sensitive endpoints
- protect auth, signup, reset, and expensive endpoints
- make abuse signals observable

## Dependency security

- keep dependencies current
- remove unused dependencies
- scan dependencies in CI/CD
- scan container images in CI/CD
- do not ignore critical security findings without explicit documented acceptance

---

## Testing Standards

Testing is mandatory.

## Minimum requirement for any meaningful change

The following must pass when relevant:

- lint
- formatting checks
- type checks
- automated tests

## Backend testing requirements

As applicable, include:

- unit tests for service/business logic
- integration tests for route + service + DB paths
- schema/contract tests where useful
- auth and permission tests for protected endpoints
- regression tests for bugfixes

Recommended tooling:

- `pytest`
- `pytest-asyncio` when needed
- `httpx`
- test database
- fixtures/factories
- migration-backed integration setup where applicable

## Frontend testing requirements

As applicable, include:

- unit tests for logic-heavy utilities/hooks
- component or integration tests for UI behavior
- Playwright E2E tests for critical user journeys
- regression tests for bugs

Recommended tooling:

- `vitest` or `jest`
- React Testing Library
- Playwright

## Testing philosophy

- test behavior, not implementation trivia
- prefer deterministic tests
- avoid brittle snapshots
- mock only true external boundaries
- keep tests CI-stable
- every production bug should add a regression test when applicable

---

## Playwright Requirement

Playwright is the required end-to-end framework for frontend critical flows.

For every meaningful frontend feature or bugfix, evaluate which Playwright scenarios must be added or updated.

## Required Playwright scenario categories

At minimum, cover where relevant:

1. authentication flows
   - login
   - logout
   - invalid credentials
   - protected route access
   - session expiration or auth failure handling

2. core user journeys
   - create flow
   - read/view flow
   - update/edit flow
   - delete/archive flow

3. form behavior
   - successful submit
   - client validation errors
   - server validation errors
   - disabled/loading submit state
   - duplicate submission protection

4. data states
   - loading state
   - populated state
   - empty state
   - API/server failure state
   - retry behavior

5. navigation
   - route transitions
   - deep links
   - back/forward behavior where relevant

6. authorization / permissions
   - unauthorized user blocked
   - forbidden action handling
   - hidden or disabled controls where appropriate

7. responsive flows
   - desktop critical path
   - at least one mobile viewport for critical flows

8. regressions
   - every major frontend production bug should add a regression E2E test when applicable

## Playwright quality rules

- use stable selectors
- prefer role-based selectors where possible
- do not use arbitrary sleeps
- wait for meaningful UI conditions
- keep tests deterministic and CI-safe
- do not use Playwright as a substitute for all other tests

---

## Scenario Matrix Requirement

For any significant frontend feature, define and validate a scenario matrix covering:

- happy path
- validation failure
- backend failure
- empty state
- loading state
- permission edge case
- cancellation/backout path
- responsive/mobile path

A feature is not complete until important scenarios are covered by tests or explicitly justified.

---

## Observability Standards

Production systems must be observable.

## Logging

- use structured logs
- include request/correlation IDs where possible
- log:
  - request lifecycle
  - auth failures
  - permission denials
  - external dependency failures
  - background job failures
  - important business events where appropriate
- never log passwords, tokens, secrets, or raw sensitive payloads

## Metrics

Track at minimum where practical:

- request count
- latency
- error rate
- DB latency
- external dependency latency/failures
- job success/failure
- infrastructure health metrics

## Tracing

- use tracing for cross-service workflows where practical
- propagate request/trace identifiers through backend and downstream calls

## Alerting

Alerts should be actionable and cover:

- elevated 5xx rate
- elevated latency
- queue backlog
- deployment failure
- dependency outage
- resource saturation
- auth anomaly spikes

---

## AWS Deployment Standards

Deployments must be production-safe and reversible.

Preferred default production posture:

### Frontend

- Next.js deployed in a production-safe mode appropriate to the project
- CDN/edge caching for static assets where relevant
- no secret leakage into client bundles
- explicit environment variable exposure rules

### Backend

- FastAPI deployed behind a load balancer or equivalent production entrypoint
- health checks required
- graceful startup and shutdown required
- multiple instances/tasks where high availability is needed

### Data / infrastructure

- use managed data services where practical
- automated backups enabled
- least-privilege IAM
- private networking for internal resources
- TLS enforcement
- secrets managed outside code and repo

### Delivery

- CI/CD must gate deployments
- safe rollout strategy preferred:
  - rolling
  - blue/green
  - canary
- fast rollback path required

---

## Database and Migration Rules

- all schema changes must use migrations
- destructive migrations require explicit review
- migrations should be reversible where practical
- preserve backward compatibility during rolling deploys
- separate deploy-safe schema expansion from later cleanup when needed
- seed operations must be idempotent
- large indexes and heavy migrations must be planned carefully

---

## Performance Rules

- measure before optimizing
- use pagination for collections
- avoid unbounded queries
- minimize unnecessary payload size
- prevent N+1 DB access
- avoid frontend request waterfalls
- batch external requests where possible
- protect expensive operations with limits, queues, or async workflows

Performance review is required for:

- dashboards
- search
- report generation
- file uploads/downloads
- large lists
- high-frequency views
- complex joins or fan-out requests

---

## CI/CD Guardrails

Every PR / merge pipeline should include, where relevant:

1. formatting check
2. lint
3. typecheck
4. backend unit tests
5. backend integration tests
6. frontend unit/component tests
7. Playwright E2E tests
8. dependency vulnerability scan
9. container/image scan
10. build validation
11. migration safety checks
12. staging or preview validation where applicable

## Merge rules

- do not merge with failing checks
- do not skip tests for convenience
- do not bypass critical security findings without explicit acceptance
- do not add undocumented env vars
- do not mark work complete without updated tests where needed

---

## Pre-Deploy Test Gate

Before every deploy, run the required automated checks.

Minimum deployment gate:

1. backend lint
2. backend format check
3. backend typecheck
4. backend tests
5. frontend lint
6. frontend typecheck
7. frontend unit/component tests
8. Playwright E2E tests
9. frontend build
10. dependency/security scan

If a required check fails, deployment must stop.

For production deployment, also verify where applicable:

- migrations are safe
- env vars are present
- backward compatibility is preserved
- monitoring remains intact
- critical-path Playwright suite passes
- smoke tests pass in staging or equivalent validation environment

---

## Required Command Policy

Expected script categories should exist where appropriate:

- `dev`
- `build`
- `lint`
- `format`
- `typecheck`
- `test`
- `test:unit`
- `test:integration`
- `test:e2e`
- `check`
- `migrate`
- `seed`

Recommended root-level check behavior:

- one command should run the full validation gate used before deploy

Example expectation:

- backend checks
- frontend checks
- Playwright checks
- build validation

---

## Code Quality Rules

## Forbidden patterns

- business logic inside FastAPI route handlers
- business logic inside React render bodies
- hardcoded secrets
- broad exception swallowing without proper handling
- raw SQL scattered without clear isolation
- duplicated validation logic without reason
- giant files mixing multiple concerns
- untyped public functions
- hidden side-effect utilities
- commented-out dead code
- duplicate UI components for the same pattern
- ad hoc inconsistent styling in existing shared UI areas

## Preferred patterns

- typed interfaces
- explicit schemas
- service/repository separation
- focused modules
- reusable UI primitives
- deterministic tests
- stable error mapping
- structured logging
- idempotent operations for retry-prone workflows

---

## Documentation Standards

Update docs for any non-trivial change, as applicable:

- API docs
- environment variable docs
- migration notes
- operational runbooks
- architecture notes
- README usage instructions
- testing instructions for new flows

Significant changes should be understandable without reverse-engineering the code.

---

## Environment Strategy

Maintain separate environments at minimum:

- local
- test
- staging
- production

Rules:

- maximize parity where practical
- keep defaults safe
- document all env vars
- minimize production-only behavior
- do not rely on hidden local assumptions

---

## Branch / PR Expectations

Each meaningful PR should include:

- what changed
- why it changed
- risks
- tests added or updated
- migration notes if applicable
- rollout notes if applicable
- screenshots or recordings for UI changes where useful

PRs should stay reviewable in size whenever practical.

---

## Definition of Done

A task is only done when all applicable items are satisfied:

- current implementation was reviewed first
- solution fits the existing architecture or improves it safely
- implementation is complete
- tests were added or updated
- regression risk was considered
- security impact was considered
- performance impact was considered
- logs/metrics/error handling are adequate
- docs were updated where needed
- env/config changes are documented
- deployment impact was checked
- feature is safe to deploy

## Definition of Done for frontend work

Frontend work is only done when:

- UI is visually consistent
- accessibility baseline is met
- loading/empty/error/success states are implemented
- responsive behavior is verified
- tests are added or updated
- Playwright scenarios are added or updated for critical flows
- pre-deploy checks pass

---

## AI Assistant Behavior Rules for This Repository

When acting in this repository:

- always inspect the current implementation first
- identify existing patterns before proposing changes
- prefer safe incremental improvement over wholesale rewrites
- produce production-quality code, not prototypes
- default to secure implementations
- default to typed code
- default to tests
- preserve good conventions already present
- avoid unnecessary dependencies
- state assumptions clearly
- flag risks and rollout concerns explicitly
- do not leave TODOs instead of core implementation
- do not invent features not requested

For non-trivial changes, expected output order is:

1. current state assessment
2. identified issues/gaps
3. proposed change plan
4. implementation
5. tests
6. validation / rollout notes

For major features, expected deliverables include:

- implementation
- tests
- config updates
- docs updates
- operational notes where relevant

---

## Final Quality Bar

Every delivered change must be something a strong senior engineer would be comfortable merging into a production system after review.

The quality bar is:

- clean
- correct
- secure
- accessible
- tested
- observable
- maintainable
- deployable