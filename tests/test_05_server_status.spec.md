# Test Suite: Server Status

Tool under test: `server_status`

---

## Suite: server_status — default (info only)

### Test: default returns info section
- **When** I call `server_status()` with no arguments
- **Then** the result is a dict with key `"info"`
- **And** `info` contains: `server_name` (string), `version` (string), `os` (string), `has_pending_restart` (bool), `local_address` (string)

### Test: default does not include other sections
- **When** I call `server_status()` with no arguments
- **Then** the result does NOT contain keys `"sessions"`, `"tasks"`, or `"activity"`

---

## Suite: server_status — include parameter combinations

### Test: include="info"
- **When** I call `server_status(include="info")`
- **Then** the result contains `"info"` and no other sections

### Test: include="sessions"
- **When** I call `server_status(include="sessions")`
- **Then** the result contains `"sessions"` (a list)
- **And** does NOT contain `"info"`, `"tasks"`, or `"activity"`

### Test: include="tasks"
- **When** I call `server_status(include="tasks")`
- **Then** the result contains `"tasks"` (a list)
- **And** each task has `id`, `name`, `state`, `last_execution`

### Test: include="activity"
- **When** I call `server_status(include="activity")`
- **Then** the result contains `"activity"` (a list)
- **And** each entry has `date`, `type`, `overview`, `user`

### Test: include="info,sessions"
- **When** I call `server_status(include="info,sessions")`
- **Then** the result contains both `"info"` and `"sessions"` keys
- **And** does NOT contain `"tasks"` or `"activity"`

### Test: include="info,tasks"
- **When** I call `server_status(include="info,tasks")`
- **Then** the result contains both `"info"` and `"tasks"` keys

### Test: include="info,activity"
- **When** I call `server_status(include="info,activity")`
- **Then** the result contains both `"info"` and `"activity"` keys

### Test: include="sessions,tasks"
- **When** I call `server_status(include="sessions,tasks")`
- **Then** the result contains both `"sessions"` and `"tasks"` keys

### Test: include="info,sessions,tasks"
- **When** I call `server_status(include="info,sessions,tasks")`
- **Then** the result contains `"info"`, `"sessions"`, and `"tasks"` keys

### Test: include all sections
- **When** I call `server_status(include="info,sessions,tasks,activity")`
- **Then** the result contains all four keys: `"info"`, `"sessions"`, `"tasks"`, `"activity"`

### Test: include with extra spaces is handled
- **When** I call `server_status(include="info , sessions , tasks")`
- **Then** the result contains `"info"`, `"sessions"`, and `"tasks"` (spaces are stripped)

### Test: include with unknown section is silently ignored
- **When** I call `server_status(include="info,nonexistent")`
- **Then** the result contains `"info"` only
- **And** no error is raised

### Test: include with empty string returns empty dict
- **When** I call `server_status(include="")`
- **Then** the result is an empty dict `{}`

---

## Suite: server_status — session details

### Test: session entries have expected fields
- **Given** `server_status(include="sessions")` returns sessions
- **Then** each session has: `user` (string), `client` (string), `device` (string), `last_activity` (string), `now_playing` (dict or None)

### Test: now_playing is None when nothing is playing
- **Given** no active playback on the server
- **When** I call `server_status(include="sessions")`
- **Then** sessions with no active playback have `now_playing` equal to `None`

---

## Suite: server_status — info field validation

### Test: version is a semver-like string
- **Given** `server_status(include="info")` → info
- **Then** `info["version"]` matches a pattern like `X.Y.Z` (contains dots and digits)

### Test: has_pending_restart is a boolean
- **Given** `server_status(include="info")` → info
- **Then** `info["has_pending_restart"]` is either `True` or `False`
