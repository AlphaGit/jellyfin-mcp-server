# Test Suite: Scheduled Tasks

Tools under test: `list_scheduled_tasks`, `run_scheduled_task`

---

## Suite: list_scheduled_tasks

### Test: returns a list of tasks
- **When** I call `list_scheduled_tasks()`
- **Then** the result is a list of dicts
- **And** the list is non-empty (Jellyfin always has built-in tasks)

### Test: each task has required fields
- **Given** the result of `list_scheduled_tasks()`
- **Then** each task dict contains: `id` (non-empty string), `name` (non-empty string), `state` (string)
- **And** each task contains `last_execution` (string or None) and `last_result` (string or None)

### Test: task states are recognized values
- **Given** the result of `list_scheduled_tasks()`
- **Then** each task's `state` is one of: `"Idle"`, `"Running"`, `"Cancelling"`

### Test: task IDs are unique
- **Given** the result of `list_scheduled_tasks()`
- **Then** all `id` values are distinct

### Test: running task includes progress_percent
- **Given** any task in `list_scheduled_tasks()` that has `state` equal to `"Running"`
- **Then** it includes `progress_percent` (a number between 0 and 100)
- **Note** This test may be skipped if no tasks are currently running — that's acceptable

---

## Suite: run_scheduled_task

### Test: trigger a safe task successfully
- **Given** I find a lightweight task from `list_scheduled_tasks()` (e.g., one named "Clean Cache" or similar non-destructive task)
- **When** I call `run_scheduled_task(task_id=<id>)`
- **Then** the result is `"Scheduled task <id> triggered."`
- **And** the call does not raise an exception

### Test: raises error for invalid task ID
- **When** I call `run_scheduled_task(task_id="nonexistent-task-id-12345")`
- **Then** an HTTP error is raised (404 or similar)

### Test: task state changes after triggering
- **Given** I find an idle task from `list_scheduled_tasks()`
- **When** I call `run_scheduled_task(task_id=<id>)`
- **And** I immediately call `list_scheduled_tasks()` again
- **Then** the triggered task's `state` may be `"Running"` or back to `"Idle"` (if it completed instantly)
- **Note** This is a best-effort check — fast tasks may already finish before the second call
