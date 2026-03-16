# Test Suite: Libraries

Tools under test: `list_libraries`, `scan_all_libraries`, `scan_library`

---

## Suite: list_libraries

### Test: returns a list of libraries
- **Given** the Jellyfin server is running and has at least one library configured
- **When** I call `list_libraries()` with no arguments
- **Then** the result is a list of dicts
- **And** each dict contains keys: `id` (non-empty string), `name` (non-empty string), `type` (string), `locations` (list)
- **And** the list contains at least one entry

### Test: library types are recognized values
- **Given** the result of `list_libraries()`
- **Then** each library's `type` is one of: `music`, `tvshows`, `movies`, `books`, `unknown`, or another string (no crash)

### Test: library IDs are unique
- **Given** the result of `list_libraries()`
- **Then** all `id` values are distinct

---

## Suite: scan_all_libraries

### Test: triggers a full scan successfully
- **Given** the server is running
- **When** I call `scan_all_libraries()` with no arguments
- **Then** the result is the string `"Full library scan triggered."`
- **And** the call does not raise an exception

### Test: is idempotent
- **Given** the server is running
- **When** I call `scan_all_libraries()` twice in succession
- **Then** both calls return success without error

---

## Suite: scan_library

### Test: triggers a scan for a valid library ID
- **Given** I obtain a valid `library_id` from `list_libraries()`
- **When** I call `scan_library(library_id=<valid_id>)`
- **Then** the result is `"Library scan triggered for <valid_id>."`
- **And** the call does not raise an exception

### Test: raises an error for an invalid library ID
- **Given** a fabricated library ID that does not exist (e.g., `"00000000-0000-0000-0000-000000000000"`)
- **When** I call `scan_library(library_id=<invalid_id>)`
- **Then** an HTTP error is raised (4xx status code)

### Test: each library from list_libraries can be scanned
- **Given** all library IDs from `list_libraries()`
- **When** I call `scan_library(library_id=<id>)` for each one
- **Then** each call returns a success string without error
