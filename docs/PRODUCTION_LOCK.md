# ZyraXis-AI — Production Lock (v1)

## Status
System is considered **feature-complete (MVP production stage)**.

All core subsystems are implemented:

- Telegram webhook ingestion ✔
- Redis queue architecture ✔
- Worker execution engine (v2) ✔
- Retry + DLQ system ✔
- Billing + orchestration layer ✔
- Docker orchestration ✔
- Heartbeat monitoring ✔

---

## What this system is

This is a **distributed message processing backend**.

It is not a finite project. It is a running system.

---

## Production Definition (MINIMUM STABLE STATE)

System is considered stable when:

1. Webhook receives messages without failure
2. Redis queue processes messages without backlog overflow
3. Worker v2 processes events continuously
4. Telegram responses are delivered successfully
5. Failed jobs are captured in DLQ
6. Heartbeat is visible in Redis

---

## Hard Constraints (DO NOT CHANGE WITHOUT NEED)

- Do not reintroduce PTB webhook execution
- Do not bypass Redis queue layer
- Do not add new worker architectures without scaling reason
- Do not modify DLQ semantics unless failure model changes

---

## Scaling Rules (when load increases)

If traffic increases:

- Scale worker horizontally (multiple containers of `start_consumer.py`)
- Redis remains single queue backbone
- API remains stateless

Do NOT add complexity before scaling is required.

---

## Operational Model

```
Telegram → API → Redis Queue → Worker Pool → Telegram
```

Workers are disposable.
API is stateless.
Redis is the system backbone.

---

## Failure Model

- Retry queue handles transient failures
- DLQ captures permanent failures
- Heartbeat detects worker downtime

No silent failure paths are allowed.

---

## Definition of "DONE"

This system is "done" when:

- It runs 24/7 without manual intervention
- Worker restarts automatically on failure
- Queue does not accumulate unprocessed backlog
- Error rate is observable and controlled

---

## Next Phase (NOT CODE)

Only proceed to:

- scaling optimization
- monitoring dashboards
- deployment hardening

No new features should be added at this stage.
