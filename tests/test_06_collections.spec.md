# Test Suite: Collection Management

Tools under test: `create_collection`, `list_collections`, `get_collection_items`, `modify_collection`, `delete_collection`

**Important:** All tests that create collections MUST delete them in cleanup, even if the test fails. Collection names should be prefixed with `[TEST]` to make them identifiable.

---

## Suite: create_collection

### Test: create an empty collection with just a name
- **When** I call `create_collection(name="[TEST] Empty Collection")`
- **Then** the result is a dict with `id` (non-empty string) and `name` equal to `"[TEST] Empty Collection"`
- **Cleanup** delete the collection via `delete_collection(collection_id=<id>)`

### Test: create a collection with initial items
- **Given** I obtain two valid movie item IDs via `search_media(query="the", media_type="Movie", limit=2)`
- **When** I call `create_collection(name="[TEST] With Items", item_ids="<id1>,<id2>")`
- **Then** the result has `id` and `name`
- **And** calling `get_collection_items(collection_id=<id>)` returns `total_count` of 2
- **Cleanup** delete the collection

### Test: create a collection with a single initial item
- **Given** one valid movie item ID
- **When** I call `create_collection(name="[TEST] Single Item", item_ids="<id1>")`
- **Then** the collection is created successfully
- **And** `get_collection_items` shows 1 item
- **Cleanup** delete the collection

### Test: create collection with duplicate name succeeds
- **Given** I create `create_collection(name="[TEST] Duplicate Name")` → col1
- **When** I create `create_collection(name="[TEST] Duplicate Name")` → col2
- **Then** both have different `id` values
- **And** both appear in `list_collections()`
- **Cleanup** delete both collections

---

## Suite: list_collections

### Test: returns a list
- **When** I call `list_collections()`
- **Then** the result is a list (may be empty)
- **And** each entry has at least `id`, `name`, `type` keys

### Test: newly created collection appears in list
- **Given** I create `create_collection(name="[TEST] Listed")` → collection
- **When** I call `list_collections()`
- **Then** the result contains an entry with `id` matching the created collection
- **Cleanup** delete the collection

### Test: deleted collection disappears from list
- **Given** I create `create_collection(name="[TEST] To Delete")` → collection
- **And** I delete it via `delete_collection(collection_id=<id>)`
- **When** I call `list_collections()`
- **Then** no entry has the deleted collection's `id`

### Test: collection shows accurate item_count
- **Given** I create a collection with 2 items
- **When** I find it in `list_collections()`
- **Then** it has `item_count` equal to 2
- **Cleanup** delete the collection

---

## Suite: get_collection_items

### Test: returns items from a populated collection
- **Given** I create a collection with 2 movie items
- **When** I call `get_collection_items(collection_id=<id>)`
- **Then** `total_count` is 2
- **And** `items` has 2 entries
- **And** each item has `id` and `name` keys
- **Cleanup** delete the collection

### Test: empty collection returns zero items
- **Given** I create an empty collection
- **When** I call `get_collection_items(collection_id=<id>)`
- **Then** `total_count` is 0
- **And** `items` is an empty list
- **Cleanup** delete the collection

### Test: pagination with limit
- **Given** a collection with 3 items
- **When** I call `get_collection_items(collection_id=<id>, limit=2)`
- **Then** `items` has 2 entries
- **And** `total_count` is 3
- **Cleanup** delete the collection

### Test: pagination with start_index
- **Given** a collection with 3 items
- **When** I call `get_collection_items(collection_id=<id>, limit=2, start_index=0)` → page1
- **And** I call `get_collection_items(collection_id=<id>, limit=2, start_index=2)` → page2
- **Then** page1 has 2 items, page2 has 1 item
- **And** no item IDs overlap between pages
- **Cleanup** delete the collection

---

## Suite: modify_collection

### Test: add items to an empty collection
- **Given** an empty collection and 2 valid movie item IDs
- **When** I call `modify_collection(collection_id=<id>, add_item_ids="<id1>,<id2>")`
- **Then** the result contains `"Added 2 item(s)."`
- **And** `get_collection_items` shows 2 items
- **Cleanup** delete the collection

### Test: add a single item
- **Given** an empty collection and 1 valid movie item ID
- **When** I call `modify_collection(collection_id=<id>, add_item_ids="<id1>")`
- **Then** the result contains `"Added 1 item(s)."`
- **And** `get_collection_items` shows 1 item
- **Cleanup** delete the collection

### Test: remove items from a collection
- **Given** a collection with 2 items
- **When** I call `modify_collection(collection_id=<id>, remove_item_ids="<id1>")`
- **Then** the result contains `"Removed 1 item(s)."`
- **And** `get_collection_items` shows 1 item remaining
- **Cleanup** delete the collection

### Test: remove all items from a collection
- **Given** a collection with 2 items, with IDs obtained via `get_collection_items`
- **When** I call `modify_collection(collection_id=<id>, remove_item_ids="<id1>,<id2>")`
- **Then** the result contains `"Removed 2 item(s)."`
- **And** `get_collection_items` shows 0 items
- **Cleanup** delete the collection

### Test: add and remove in a single call
- **Given** a collection with 1 item (item A), and a new item ID (item B)
- **When** I call `modify_collection(collection_id=<id>, add_item_ids="<B_id>", remove_item_ids="<A_id>")`
- **Then** the result contains both `"Added 1 item(s)."` and `"Removed 1 item(s)."`
- **And** `get_collection_items` shows exactly 1 item (item B, not item A)
- **Cleanup** delete the collection

### Test: no changes when neither add nor remove is provided
- **Given** an empty collection
- **When** I call `modify_collection(collection_id=<id>)` with no add or remove IDs
- **Then** the result is `"No changes requested."`
- **Cleanup** delete the collection

---

## Suite: delete_collection

### Test: delete an existing collection
- **Given** I create `create_collection(name="[TEST] To Be Deleted")` → collection
- **When** I call `delete_collection(collection_id=<id>)`
- **Then** the result is `"Collection <id> deleted."`
- **And** the collection no longer appears in `list_collections()`

### Test: delete a collection with items
- **Given** I create a collection with 2 items
- **When** I call `delete_collection(collection_id=<id>)`
- **Then** the deletion succeeds
- **And** the collection no longer appears in `list_collections()`
- **And** the original media items still exist (verify via `get_item_details`)

### Test: delete with invalid collection_id raises error
- **When** I call `delete_collection(collection_id="00000000-0000-0000-0000-000000000000")`
- **Then** an HTTP error is raised (404 or similar)

### Test: double delete raises error
- **Given** I create and then delete a collection
- **When** I call `delete_collection(collection_id=<same_id>)` again
- **Then** an HTTP error is raised (the collection no longer exists)
