# OrderServiceAPI
## Project overview
A FastAPI service to accept stock orders, persist them, and guarantee eventual placement on an external exchange using the outbox pattern.I have used the Repository pattern to create the endpoint, Introduced poetry for package management  and pyenv to handle my virtualenv for local testing incases I don't want to use docker.
## Architecture Decision: Why Outbox Pattern?

**Problem:** The requirement states "it is guaranteed that the order WILL be placed" but the exchange is unreliable (10% failure rate). A synchronous approach would make our endpoint unreliable too.

**Solution:**
- Persist order + outbox entry in a single transaction
- Return 201 immediately (endpoint is fast and reliable)
- Background worker polls outbox and retries placement until success
- This decouples endpoint reliability from exchange reliability

**Trade-off:** Orders aren't placed immediately, but placement is guaranteed (if worker runs).

## How the guarantee is satisfied

The requirement states: "it is guaranteed that the order **WILL** be placed on the stock exchange."

**Design:**
1. POST /orders persists order + creates a pending outbox entry in the same transaction (atomic).
2. Endpoint returns 201 immediately (no waiting for exchange).
3. Separate worker process polls outbox table every 5 seconds.
4. Worker fetches pending entries, calls `_place_order_with_retry()` (up to 3 attempts with backoff).
5. On success → outbox entry status = "placed".
6. On failure after retries → outbox entry status = "failed" (logged; needs dead-letter handling).

**Operational requirement:** The worker MUST be deployed and running continuously for the guarantee to hold. See docker-compose.yml service `outbox_worker` and "How to run" section.

**Current limitations:**
- No dead-letter queue or alerting for permanently failed entries.
- No idempotency (duplicate placements if worker retries).
- Worker is a simple poller; not production-ready for high scale.

See "Improvements" section for production hardening.
┌─────────┐      ┌─────────┐      ┌──────────┐      ┌──────────┐
│ Client  │─────▶│   API   │─────▶│ Database │      │ Exchange │
└─────────┘      └─────────┘      └──────────┘      └──────────┘
                      │                  │                 ▲
                      │             ┌────▼────┐           │
                      │             │ Outbox  │           │
                      │             │  Table  │           │
                      │             └────┬────┘           │
                      │                  │                │
                      │             ┌────▼────┐           │
                      └─────────────│ Workers  │───────────┘
                                    └─────────┘

## Project structure
order-service/
|
src/
├── app/
│   ├── api/
│   │   └── endpoints/
│   │       ├── health.py
│   │       ├── order.py
│   │       └── meta.py
│   ├── database/
│   │   └── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── order.py
│   │   └── outbox.py
│   ├── repositories/
│   │   └── order.py
│   ├── schemas/
│   │   └── enums/
│   │       └── order.py
│   │   └── order.py
│   ├── services/
│   │   └── order.py
│   ├── workers/
│   │   └── outbox_worker.py
│   ├── exceptions.py
│   ├── deps.py
│   ├── main.py
│   └── settings.py
├── migration/
│   ├── env.py
│   └── versions/
│       ├── create_order_table.py
│       └── create_order_outbox_table.py
├── tests/
│   └── health_test.py
├── alembic.ini
├── pytest.ini
├── pyproject.toml
├── poetry.lock
├── readme.md
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── conftest.py

## Key design decisions
- Guarantee and reliability:
  - Persist order to DB and write a pending outbox entry.
  - A separate worker  polls the outbox and calls the placement routine  to ensure eventual placement.
  - The POST /orders endpoint returns 201 once persistence and outbox entry creation succeed.
- Simulated exchange behavior:
  - A dummy placement function emulates 10% failure and 0.5s latency.
- Error handling:
  - Domain exceptions are centralized in [src/app/exceptions.py].
  - Repository/database errors raise `OrderSaveError`. Placement failures raise `OrderPlacementError`.
- Migrations:
  - Alembic uses `Base.metadata` for autogenerate migrations.

## Assumptions
- A single PostgreSQL DB is used. DB connection strings are in [src/app/settings.py].
- Worker runs as a separate process in production.
- The outbox table is small and polled periodically for high scale i can switch to an event broker or message queue

## How to run the application
1. Start databases:
   make start
2. Apply migrations:
   make migrate-local
3. Start app:
   make serve
4. Start worker (separate process on a different terminal):
   cd src && poetry run python -m app.workers.outbox_worker
5. Tests
    make test migrate-local
6. Coverage
   make test-with-coverage
   
Files used:
- API router & endpoints 
- Service
- Repository & outbox
- Worker
- Exceptions

## Testing
- Unit tests for service and repository with DB fixtures.
- Integration tests using in-memory or test Postgres instance (docker-compose includes a test DB).
- Example tests exist for health and meta endpoints in `src/tests/`.

## Improvements
- Replace polling worker with a message broker like kafka  or use transactional outbox + CDC for higher throughput.
- Add idempotency keys for placement to handle retry duplicates.
- Add metrics / tracing.
- Harden failure handling: dead-letter queue for permanently failing outbox entries and alerting.
- Add comprehensive test coverage and CI pipeline  to run tests and linter(pre-commit).
- Add Datadog for observability

## Known gaps
- Worker is a simple poller for demo not production-ready for very high throughput.
- No authentication and authorization, rate-limiting or RBAC implemented.
- Add graceful shutdown and concurrency controls for the worker.


## References
- Task description: [readme.md](readme.md) 
- Packaging & deps: [pyproject.toml](pyproject.toml), [Dockerfile](Dockerfile), [Makefile](Makefile)
