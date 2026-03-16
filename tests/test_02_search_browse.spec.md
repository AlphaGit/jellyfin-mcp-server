# Test Suite: Search & Browse

Tools under test: `search_media`, `get_item_details`, `browse_library`, `get_recent_items`, `get_similar_items`

---

## Suite: search_media

### Test: basic search returns results
- **Given** the server has media in its libraries
- **When** I call `search_media(query="a")`
- **Then** the result is a dict with keys `total_count` (int >= 0) and `items` (list)
- **And** `total_count` is greater than 0
- **And** each item in `items` has at least `id` and `name` keys

### Test: search with no matches returns empty
- **When** I call `search_media(query="zzznonexistentzzzxyz123456")`
- **Then** `total_count` is 0
- **And** `items` is an empty list

### Test: search with media_type filter returns only that type
- **Given** the server has music content
- **When** I call `search_media(query="a", media_type="Audio")`
- **Then** every item in `items` has `type` equal to `"Audio"`

### Test: search with media_type "MusicAlbum"
- **When** I call `search_media(query="a", media_type="MusicAlbum")`
- **Then** every item in `items` has `type` equal to `"MusicAlbum"`

### Test: search with media_type "MusicArtist"
- **When** I call `search_media(query="a", media_type="MusicArtist")`
- **Then** every item in `items` has `type` equal to `"MusicArtist"`

### Test: limit parameter restricts result count
- **When** I call `search_media(query="a", limit=3)`
- **Then** `items` has at most 3 entries

### Test: limit=1 returns exactly one item
- **When** I call `search_media(query="a", limit=1)`
- **Then** `items` has exactly 1 entry (assuming server has content)

### Test: pagination with start_index
- **Given** a search that returns more than 2 results: `search_media(query="a", limit=2, start_index=0)` → page1
- **When** I call `search_media(query="a", limit=2, start_index=2)` → page2
- **Then** page1 and page2 have different items (no overlapping IDs)
- **And** both pages have `total_count` equal to each other (same total)

### Test: start_index beyond total returns empty
- **Given** `search_media(query="a")` returns `total_count` = N
- **When** I call `search_media(query="a", start_index=N+1000)`
- **Then** `items` is an empty list
- **And** `total_count` is still N

### Test: limit=0 returns zero items
- **When** I call `search_media(query="a", limit=0)`
- **Then** `items` is an empty list (or the call doesn't error)

### Test: default limit is 20
- **When** I call `search_media(query="a")` with no explicit limit
- **Then** `items` has at most 20 entries

---

## Suite: get_item_details

### Test: returns details for a valid item
- **Given** I obtain a valid `item_id` by searching: `search_media(query="a", limit=1)` → first item's `id`
- **When** I call `get_item_details(item_id=<valid_id>)`
- **Then** the result is a dict containing at least `id`, `name`, `type`
- **And** `id` matches the requested item_id

### Test: includes extended detail fields
- **Given** a valid item_id for an audio track (search with `media_type="Audio"`)
- **When** I call `get_item_details(item_id=<id>)`
- **Then** the result includes `path` (string)
- **And** may include `bitrate`, `size_bytes`, `container`, `genres`, `provider_ids`

### Test: album details include child_count
- **Given** a valid item_id for an album (search with `media_type="MusicAlbum"`)
- **When** I call `get_item_details(item_id=<id>)`
- **Then** the result includes `child_count` (integer)

### Test: returns internal root item for zero UUID
- **Given** the zero UUID `"00000000-0000-0000-0000-000000000000"`
- **When** I call `get_item_details(item_id=<zero_uuid>)`
- **Then** the result is a dict (Jellyfin maps the zero UUID to its internal root folder)
- **And** the result has `type` equal to `"UserRootFolder"`
- **Note** This is Jellyfin API behavior — the zero UUID is valid and maps to the root

### Test: raises error for a truly nonexistent item ID
- **Given** a fabricated item ID `"ffffffffffffffffffffffffffffffff"`
- **When** I call `get_item_details(item_id=<invalid>)`
- **Then** an HTTP error is raised (404 or similar)

### Test: overview is truncated to 300 chars
- **Given** an item that has an overview longer than 300 characters
- **When** I call `get_item_details(item_id=<id>)`
- **Then** if `overview` is present and was truncated, it ends with `"..."`
- **And** `len(overview)` <= 303

---

## Suite: browse_library

### Test: browse with no filters returns items
- **When** I call `browse_library()` with all defaults
- **Then** the result has `total_count` (int >= 0) and `items` (list)
- **And** items are returned (assuming server has content)

### Test: browse scoped to a specific library
- **Given** a valid `library_id` from `list_libraries()`
- **When** I call `browse_library(library_id=<id>)`
- **Then** the result contains items
- **And** `total_count` reflects items in that library only

### Test: browse with media_type filter
- **When** I call `browse_library(media_type="MusicAlbum")`
- **Then** every item in `items` has `type` equal to `"MusicAlbum"`

### Test: browse combining library_id and media_type
- **Given** a music library ID from `list_libraries()` (type="music")
- **When** I call `browse_library(library_id=<music_lib_id>, media_type="Audio")`
- **Then** every item has `type` equal to `"Audio"`

### Test: browse with artist_ids filter
- **Given** an artist ID obtained via `search_media(query="a", media_type="MusicArtist", limit=1)`
- **When** I call `browse_library(media_type="MusicAlbum", artist_ids=<artist_id>)`
- **Then** all returned albums are by that artist (or result is empty if artist has no albums)

### Test: sort_by DateCreated descending
- **When** I call `browse_library(sort_by="DateCreated", sort_order="Descending", limit=5)`
- **Then** the items are ordered by `date_added` descending (each item's date >= next item's date)

### Test: sort_by SortName ascending (default)
- **When** I call `browse_library(sort_by="SortName", sort_order="Ascending", limit=5)`
- **Then** items are in alphabetical order by name

### Test: sort_order Descending reverses order
- **Given** results from `browse_library(sort_by="SortName", sort_order="Ascending", limit=5)` → asc_items
- **And** results from `browse_library(sort_by="SortName", sort_order="Descending", limit=5)` → desc_items
- **Then** asc_items and desc_items contain different orderings (first items differ)

### Test: pagination with limit and start_index
- **Given** `browse_library(limit=2, start_index=0)` → page1
- **When** I call `browse_library(limit=2, start_index=2)` → page2
- **Then** page1 and page2 items do not overlap (different IDs)

### Test: browse with invalid library_id returns empty or errors
- **When** I call `browse_library(library_id="00000000-0000-0000-0000-000000000000")`
- **Then** the result has `total_count` of 0 and empty `items`, or an HTTP error is raised

---

## Suite: get_recent_items

### Test: returns recently added items
- **When** I call `get_recent_items()` with defaults
- **Then** the result has `total_count` (int) and `items` (list)
- **And** items have `date_added` fields

### Test: items are sorted newest first
- **Given** `get_recent_items(limit=5)` → items
- **Then** each item's `date_added` is >= the next item's `date_added`

### Test: media_type filter works
- **When** I call `get_recent_items(media_type="Audio", limit=5)`
- **Then** every item has `type` equal to `"Audio"`

### Test: media_type "MusicAlbum"
- **When** I call `get_recent_items(media_type="MusicAlbum", limit=5)`
- **Then** every item has `type` equal to `"MusicAlbum"`

### Test: limit restricts count
- **When** I call `get_recent_items(limit=3)`
- **Then** `items` has at most 3 entries

### Test: default limit is 20
- **When** I call `get_recent_items()` with no explicit limit
- **Then** `items` has at most 20 entries

---

## Suite: get_similar_items

### Test: returns similar items for a valid item
- **Given** a valid `item_id` for an album: `search_media(query="a", media_type="MusicAlbum", limit=1)`
- **When** I call `get_similar_items(item_id=<id>)`
- **Then** the result is a list of dicts
- **And** each dict has at least `id` and `name` keys

### Test: similar items share the same type
- **Given** an album item_id
- **When** I call `get_similar_items(item_id=<id>)`
- **Then** all returned items have `type` equal to `"MusicAlbum"` (same type as input)

### Test: limit parameter works
- **Given** a valid item_id
- **When** I call `get_similar_items(item_id=<id>, limit=3)`
- **Then** the result has at most 3 entries

### Test: default limit is 10
- **Given** a valid item_id
- **When** I call `get_similar_items(item_id=<id>)` with no explicit limit
- **Then** the result has at most 10 entries

### Test: zero UUID returns root aggregate folder
- **When** I call `get_similar_items(item_id="00000000-0000-0000-0000-000000000000")`
- **Then** the result is a list (Jellyfin maps zero UUID to root, which returns its "similar" items)
- **Note** This is Jellyfin API behavior — the zero UUID resolves to a valid internal item

### Test: raises error for a truly nonexistent item ID
- **When** I call `get_similar_items(item_id="ffffffffffffffffffffffffffffffff")`
- **Then** an HTTP error is raised (404 or similar)

### Test: returns empty list when no similar items exist
- **Given** an item with very unique characteristics (or a fabricated edge case)
- **When** I call `get_similar_items(item_id=<id>)`
- **Then** the result may be an empty list (this is a valid response)
