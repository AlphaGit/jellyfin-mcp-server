# Test Suite: Playlist Management

Tools under test: `create_playlist`, `list_playlists`, `get_playlist_items`, `modify_playlist`, `delete_playlist`

**Important:** All tests that create playlists MUST delete them in cleanup, even if the test fails. Playlist names should be prefixed with `[TEST]` to make them identifiable.

---

## Suite: create_playlist

### Test: create an empty playlist with just a name
- **When** I call `create_playlist(name="[TEST] Empty Playlist")`
- **Then** the result is a dict with `id` (non-empty string) and `name` equal to `"[TEST] Empty Playlist"`
- **Cleanup** delete the playlist via `delete_playlist(playlist_id=<id>)`

### Test: create a playlist with initial items
- **Given** I obtain two valid audio item IDs via `search_media(query="a", media_type="Audio", limit=2)`
- **When** I call `create_playlist(name="[TEST] With Items", item_ids="<id1>,<id2>")`
- **Then** the result has `id` and `name`
- **And** calling `get_playlist_items(playlist_id=<id>)` returns `total_count` of 2
- **Cleanup** delete the playlist

### Test: create a playlist with a single initial item
- **Given** one valid audio item ID
- **When** I call `create_playlist(name="[TEST] Single Item", item_ids="<id1>")`
- **Then** the playlist is created successfully
- **And** `get_playlist_items` shows 1 item
- **Cleanup** delete the playlist

### Test: create a playlist with media_type "Video"
- **When** I call `create_playlist(name="[TEST] Video Playlist", media_type="Video")`
- **Then** the playlist is created successfully with a valid `id`
- **Cleanup** delete the playlist

### Test: default media_type is "Audio"
- **When** I call `create_playlist(name="[TEST] Default Type")` without specifying media_type
- **Then** the playlist is created successfully
- **Cleanup** delete the playlist

### Test: create playlist with duplicate name succeeds
- **Given** I create `create_playlist(name="[TEST] Duplicate Name")` → playlist1
- **When** I create `create_playlist(name="[TEST] Duplicate Name")` → playlist2
- **Then** both have different `id` values
- **And** both appear in `list_playlists()`
- **Cleanup** delete both playlists

---

## Suite: list_playlists

### Test: returns a list
- **When** I call `list_playlists()`
- **Then** the result is a list of dicts
- **And** each dict has at least `id`, `name`, `type` keys

### Test: newly created playlist appears in list
- **Given** I create `create_playlist(name="[TEST] Listed")` → playlist
- **When** I call `list_playlists()`
- **Then** the result contains an entry with `id` matching the created playlist
- **Cleanup** delete the playlist

### Test: deleted playlist disappears from list
- **Given** I create `create_playlist(name="[TEST] To Delete")` → playlist
- **And** I delete it via `delete_playlist(playlist_id=<id>)`
- **When** I call `list_playlists()`
- **Then** no entry has the deleted playlist's `id`

### Test: playlist type is "Playlist"
- **Given** I create a playlist
- **When** I find it in `list_playlists()`
- **Then** its `type` is `"Playlist"`
- **Cleanup** delete the playlist

### Test: playlist shows accurate item_count
- **Given** I create a playlist with 2 items
- **When** I find it in `list_playlists()`
- **Then** it has `item_count` equal to 2 (fetched via playlist items endpoint, not ChildCount)
- **Cleanup** delete the playlist

---

## Suite: get_playlist_items

### Test: returns items from a populated playlist
- **Given** I create a playlist with 2 audio items
- **When** I call `get_playlist_items(playlist_id=<id>)`
- **Then** `total_count` is 2
- **And** `items` has 2 entries
- **And** each item has `id`, `name`, and `playlist_item_id` keys
- **Cleanup** delete the playlist

### Test: empty playlist returns zero items
- **Given** I create an empty playlist
- **When** I call `get_playlist_items(playlist_id=<id>)`
- **Then** `total_count` is 0
- **And** `items` is an empty list
- **Cleanup** delete the playlist

### Test: playlist_item_id is present on each item
- **Given** a playlist with items
- **When** I call `get_playlist_items(playlist_id=<id>)`
- **Then** every item has a non-empty `playlist_item_id` string
- **Cleanup** delete the playlist

### Test: pagination with limit
- **Given** a playlist with 3 items
- **When** I call `get_playlist_items(playlist_id=<id>, limit=2)`
- **Then** `items` has 2 entries
- **And** `total_count` is 3
- **Cleanup** delete the playlist

### Test: pagination with start_index
- **Given** a playlist with 3 items
- **When** I call `get_playlist_items(playlist_id=<id>, limit=2, start_index=0)` → page1
- **And** I call `get_playlist_items(playlist_id=<id>, limit=2, start_index=2)` → page2
- **Then** page1 has 2 items, page2 has 1 item
- **And** no item IDs overlap between pages
- **Cleanup** delete the playlist

### Test: default limit is 50
- **Given** a playlist with items
- **When** I call `get_playlist_items(playlist_id=<id>)` with no explicit limit
- **Then** up to 50 items are returned (no error)
- **Cleanup** delete the playlist

### Test: invalid playlist_id raises error
- **When** I call `get_playlist_items(playlist_id="00000000-0000-0000-0000-000000000000")`
- **Then** an HTTP error is raised

---

## Suite: modify_playlist

### Test: add items to an empty playlist
- **Given** an empty playlist and 2 valid audio item IDs
- **When** I call `modify_playlist(playlist_id=<id>, add_item_ids="<id1>,<id2>")`
- **Then** the result contains `"Added 2 item(s)."`
- **And** `get_playlist_items` shows 2 items
- **Cleanup** delete the playlist

### Test: add a single item
- **Given** an empty playlist and 1 valid audio item ID
- **When** I call `modify_playlist(playlist_id=<id>, add_item_ids="<id1>")`
- **Then** the result contains `"Added 1 item(s)."`
- **And** `get_playlist_items` shows 1 item
- **Cleanup** delete the playlist

### Test: remove items from a playlist
- **Given** a playlist with 2 items
- **And** I get the `playlist_item_id` values via `get_playlist_items`
- **When** I call `modify_playlist(playlist_id=<id>, remove_item_ids="<playlist_item_id_1>")`
- **Then** the result contains `"Removed 1 item(s)."`
- **And** `get_playlist_items` shows 1 item remaining
- **Cleanup** delete the playlist

### Test: remove all items from a playlist
- **Given** a playlist with 2 items, with playlist_item_ids obtained
- **When** I call `modify_playlist(playlist_id=<id>, remove_item_ids="<pid1>,<pid2>")`
- **Then** the result contains `"Removed 2 item(s)."`
- **And** `get_playlist_items` shows 0 items
- **Cleanup** delete the playlist

### Test: add and remove in a single call
- **Given** a playlist with 1 item (item A), and a new item ID (item B)
- **And** I obtain the `playlist_item_id` for item A
- **When** I call `modify_playlist(playlist_id=<id>, add_item_ids="<B_id>", remove_item_ids="<A_playlist_item_id>")`
- **Then** the result contains both `"Added 1 item(s)."` and `"Removed 1 item(s)."`
- **And** `get_playlist_items` shows exactly 1 item (item B, not item A)
- **Cleanup** delete the playlist

### Test: no changes when neither add nor remove is provided
- **Given** an empty playlist
- **When** I call `modify_playlist(playlist_id=<id>)` with no add or remove IDs
- **Then** the result is `"No changes requested."`
- **And** `get_playlist_items` still shows 0 items
- **Cleanup** delete the playlist

### Test: adding duplicate item ID succeeds (Jellyfin allows duplicates)
- **Given** a playlist and one audio item ID
- **When** I call `modify_playlist(playlist_id=<id>, add_item_ids="<id1>")` twice
- **Then** both calls succeed
- **And** `get_playlist_items` shows 2 items (the same track twice)
- **Cleanup** delete the playlist

---

## Suite: delete_playlist

### Test: delete an existing playlist
- **Given** I create `create_playlist(name="[TEST] To Be Deleted")` → playlist
- **When** I call `delete_playlist(playlist_id=<id>)`
- **Then** the result is `"Playlist <id> deleted."`
- **And** the playlist no longer appears in `list_playlists()`

### Test: delete a playlist with items
- **Given** I create a playlist with 2 items
- **When** I call `delete_playlist(playlist_id=<id>)`
- **Then** the deletion succeeds
- **And** the playlist no longer appears in `list_playlists()`
- **And** the original media items still exist (verify via `get_item_details`)

### Test: delete with invalid playlist_id raises error
- **When** I call `delete_playlist(playlist_id="00000000-0000-0000-0000-000000000000")`
- **Then** an HTTP error is raised (404 or similar)

### Test: double delete raises error
- **Given** I create and then delete a playlist
- **When** I call `delete_playlist(playlist_id=<same_id>)` again
- **Then** an HTTP error is raised (the playlist no longer exists)
