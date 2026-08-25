# Parallel Downloads Plan

## Goal

Allow the application to process multiple queued downloads at the same time while keeping queue ordering, pause/cancel behavior, persistence, and progress updates reliable.

## Decisions

- Desktop exposes a `parallel_downloads` setting in the native settings UI.
- Desktop default is based on CPU count, with safe limits.
- Web does not expose a UI control for this setting.
- Web uses `MAX_PARALLEL_DOWNLOADS` as the effective runtime limit.
- Web may still expose `parallel_downloads` in `GET /api/config` as the effective value.

## Backend Design

- Replace the single active download state with a map of active item IDs to cancel functions.
- Keep `queueOrder` as the scheduling order.
- The queue worker fills available slots up to the effective parallel limit.
- Each download runs in its own goroutine and signals the worker when it exits, allowing the next pending item to start.
- Pause cancels every active download and resets them to pending.
- Cancel-all cancels every active download and marks all active or pending items as cancelled.
- Individual cancel/remove operations address the item by ID in the active map.

## Configuration

- Add `parallel_downloads` to `Config`.
- Normalize the value to a safe range.
- Desktop uses the persisted config value.
- Web uses the environment override as the effective limit.

## Tests

- Config round-trip, normalization, and legacy config migration.
- Scheduler starts up to the configured limit and does not exceed it.
- Scheduler fills a freed slot with the next pending item.
- Pause cancels all active items and returns them to pending.
- Individual cancel and cancel-all work with multiple active items.
- Web config exposes the effective parallel value from the environment-backed override.
