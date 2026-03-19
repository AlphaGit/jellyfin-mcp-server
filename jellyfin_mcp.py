"""Jellyfin MCP Server — curated tools for managing Jellyfin from Claude Code."""

import asyncio
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load .env from the same directory as this script
load_dotenv(Path(__file__).parent / ".env")

JELLYFIN_URL = os.environ.get("JELLYFIN_URL", "").rstrip("/")
JELLYFIN_API_KEY = os.environ.get("JELLYFIN_API_KEY", "")
JELLYFIN_USERNAME = os.environ.get("JELLYFIN_USERNAME", "")

if not JELLYFIN_URL or not JELLYFIN_API_KEY or not JELLYFIN_USERNAME:
    raise RuntimeError(
        "JELLYFIN_URL, JELLYFIN_API_KEY, and JELLYFIN_USERNAME environment variables must be set"
    )

AUTH_HEADER = (
    f'MediaBrowser Token="{JELLYFIN_API_KEY}", '
    f'Client="JellyfinMCP", Version="1.0.0", '
    f'DeviceId="jellyfin-mcp", Device="Jellyfin MCP Server"'
)

mcp = FastMCP("jellyfin")

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=JELLYFIN_URL,
            headers={"Authorization": AUTH_HEADER},
            timeout=30.0,
        )
    return _client


async def _get(path: str, params: dict | None = None) -> Any:
    r = await _get_client().get(path, params=params)
    r.raise_for_status()
    return r.json()


async def _post(path: str, json: dict | None = None, params: dict | None = None) -> Any:
    r = await _get_client().post(path, json=json, params=params)
    r.raise_for_status()
    if r.status_code == 204 or not r.content:
        return None
    return r.json()


async def _delete(path: str, params: dict | None = None) -> None:
    r = await _get_client().delete(path, params=params)
    r.raise_for_status()


# ---------------------------------------------------------------------------
# User ID (cached, lazy)
# ---------------------------------------------------------------------------

_user_id: str | None = None


async def _get_user_id() -> str:
    """Resolve the configured JELLYFIN_USERNAME to a user ID.

    API-key auth doesn't support /Users/Me, so we look up the user by name.
    The result is cached for the lifetime of the process.
    """
    global _user_id
    if _user_id is None:
        users = await _get("/Users")
        match = next(
            (u for u in users if u.get("Name", "").lower() == JELLYFIN_USERNAME.lower()),
            None,
        )
        if not match:
            available = [u.get("Name", "") for u in users]
            raise RuntimeError(
                f"User '{JELLYFIN_USERNAME}' not found on the Jellyfin server. "
                f"Available users: {available}"
            )
        _user_id = match["Id"]
    return _user_id


# ---------------------------------------------------------------------------
# Item summarizer
# ---------------------------------------------------------------------------


def _summarize_item(item: dict) -> dict:
    """Extract only the LLM-relevant fields from a Jellyfin item."""
    summary: dict[str, Any] = {"id": item["Id"], "name": item.get("Name", "")}

    if t := item.get("Type"):
        summary["type"] = t
    if y := item.get("ProductionYear"):
        summary["year"] = y
    if artists := item.get("Artists"):
        summary["artists"] = artists
    elif artist := item.get("AlbumArtist"):
        summary["artist"] = artist
    if album := item.get("Album"):
        summary["album"] = album
    if series := item.get("SeriesName"):
        summary["series"] = series
    if sn := item.get("ParentIndexNumber"):
        summary["season"] = sn
    if idx := item.get("IndexNumber"):
        if item.get("Type") == "Audio":
            summary["track"] = idx
        else:
            summary["episode"] = idx
    if ticks := item.get("RunTimeTicks"):
        summary["duration_seconds"] = round(ticks / 10_000_000)
    if overview := item.get("Overview"):
        summary["overview"] = overview[:300] + "..." if len(overview) > 300 else overview
    if da := item.get("DateCreated"):
        summary["date_added"] = da
    if (count := item.get("ChildCount")) and item.get("Type") != "Playlist":
        summary["child_count"] = count

    return summary


def _summarize_items(items: list[dict]) -> list[dict]:
    return [_summarize_item(i) for i in items]


def _parse_csv_ids(raw: str) -> list[str]:
    return [s for s in (i.strip() for i in raw.split(",")) if s]


# ---------------------------------------------------------------------------
# Tools — Library Rescans
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_libraries() -> list[dict]:
    """List all Jellyfin media libraries with their IDs, names, types, and folder paths."""
    folders = await _get("/Library/VirtualFolders")
    return [
        {
            "id": f.get("ItemId", ""),
            "name": f["Name"],
            "type": f.get("CollectionType", "unknown"),
            "locations": f.get("Locations", []),
        }
        for f in folders
    ]


@mcp.tool()
async def scan_all_libraries() -> str:
    """Trigger a full rescan of all Jellyfin libraries. Returns immediately; scan runs in background."""
    await _post("/Library/Refresh")
    return "Full library scan triggered."


@mcp.tool()
async def scan_library(library_id: str) -> str:
    """Trigger a recursive rescan of a specific library.

    Args:
        library_id: The library/item ID from list_libraries().
    """
    await _post(f"/Items/{library_id}/Refresh", json={"Recursive": True})
    return f"Library scan triggered for {library_id}."


# ---------------------------------------------------------------------------
# Tools — Search & Browse
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_media(
    query: str,
    media_type: str | None = None,
    limit: int = 20,
    start_index: int = 0,
) -> dict:
    """Search the Jellyfin library by name/keyword.

    Args:
        query: Search term.
        media_type: Optional filter — one of Audio, MusicAlbum, MusicArtist, Movie, Series, Episode, Book, Playlist.
        limit: Max results to return (default 20).
        start_index: Offset for pagination.
    """
    params: dict[str, Any] = {
        "SearchTerm": query,
        "Limit": limit,
        "StartIndex": start_index,
        "Recursive": True,
        "Fields": "Overview,DateCreated",
    }
    if media_type:
        params["IncludeItemTypes"] = media_type
    data = await _get("/Items", params=params)
    return {
        "total_count": data.get("TotalRecordCount", 0),
        "items": _summarize_items(data.get("Items", [])),
    }


@mcp.tool()
async def get_item_details(item_id: str) -> dict:
    """Get detailed information about a specific Jellyfin item (album, track, movie, etc.).

    Args:
        item_id: The item's Jellyfin ID.
    """
    user_id = await _get_user_id()
    data = await _get(f"/Users/{user_id}/Items/{item_id}", params={"Fields": "Overview,DateCreated,Genres,Tags,Studios,People,Path,MediaSources,ProviderIds"})
    detail = _summarize_item(data)
    # Add extra detail fields
    if genres := data.get("Genres"):
        detail["genres"] = genres
    if tags := data.get("Tags"):
        detail["tags"] = tags
    if studios := data.get("Studios"):
        detail["studios"] = [s["Name"] for s in studios]
    if people := data.get("People"):
        detail["people"] = [
            {"name": p["Name"], "role": p.get("Role", ""), "type": p.get("Type", "")}
            for p in people[:20]
        ]
    if path := data.get("Path"):
        detail["path"] = path
    if container := data.get("Container"):
        detail["container"] = container
    if media := data.get("MediaSources"):
        for src in media[:1]:
            detail["bitrate"] = src.get("Bitrate")
            detail["size_bytes"] = src.get("Size")
    if prov_ids := data.get("ProviderIds"):
        detail["provider_ids"] = prov_ids
    return detail


@mcp.tool()
async def browse_library(
    library_id: str | None = None,
    media_type: str | None = None,
    artist_ids: str | None = None,
    sort_by: str = "SortName",
    sort_order: str = "Ascending",
    limit: int = 20,
    start_index: int = 0,
) -> dict:
    """Browse items in a library with sorting and pagination.

    Args:
        library_id: Optional library ID to scope results.
        media_type: Optional type filter (Audio, MusicAlbum, MusicArtist, Movie, Series, Episode, Book).
        artist_ids: Optional comma-separated artist IDs to filter by (e.g. for albums by a specific artist).
        sort_by: Sort field — SortName, DateCreated, CommunityRating, ProductionYear, Random, etc.
        sort_order: Ascending or Descending.
        limit: Max results (default 20).
        start_index: Offset for pagination.
    """
    params: dict[str, Any] = {
        "SortBy": sort_by,
        "SortOrder": sort_order,
        "Limit": limit,
        "StartIndex": start_index,
        "Recursive": True,
        "Fields": "Overview,DateCreated",
    }
    if library_id:
        params["ParentId"] = library_id
    if media_type:
        params["IncludeItemTypes"] = media_type
    if artist_ids:
        params["ArtistIds"] = artist_ids
    data = await _get("/Items", params=params)
    return {
        "total_count": data.get("TotalRecordCount", 0),
        "items": _summarize_items(data.get("Items", [])),
    }


@mcp.tool()
async def get_recent_items(
    media_type: str | None = None,
    limit: int = 20,
) -> dict:
    """Get recently added items, sorted by date added (newest first).

    Args:
        media_type: Optional type filter (Audio, MusicAlbum, Movie, Series, Episode, Book).
        limit: Max results (default 20).
    """
    params: dict[str, Any] = {
        "SortBy": "DateCreated",
        "SortOrder": "Descending",
        "Limit": limit,
        "Recursive": True,
        "Fields": "Overview,DateCreated",
    }
    if media_type:
        params["IncludeItemTypes"] = media_type
    data = await _get("/Items", params=params)
    return {
        "total_count": data.get("TotalRecordCount", 0),
        "items": _summarize_items(data.get("Items", [])),
    }


@mcp.tool()
async def get_similar_items(item_id: str, limit: int = 10) -> list[dict]:
    """Get items similar to a given item (works for albums, movies, series, etc.).

    Args:
        item_id: The item's Jellyfin ID.
        limit: Max results (default 10).
    """
    data = await _get(f"/Items/{item_id}/Similar", params={"Limit": limit})
    return _summarize_items(data.get("Items", []))


# ---------------------------------------------------------------------------
# Tools — Playlist Management
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_playlists() -> list[dict]:
    """List all playlists on the server."""
    user_id = await _get_user_id()
    data = await _get("/Items", params={
        "IncludeItemTypes": "Playlist",
        "Recursive": True,
    })
    playlists = _summarize_items(data.get("Items", []))

    async def _fetch_count(pl: dict) -> None:
        count_data = await _get(f"/Playlists/{pl['id']}/Items", params={
            "UserId": user_id,
            "Limit": 0,
        })
        pl["item_count"] = count_data.get("TotalRecordCount", 0)

    await asyncio.gather(*[_fetch_count(pl) for pl in playlists])
    return playlists


@mcp.tool()
async def create_playlist(
    name: str,
    item_ids: str | None = None,
    media_type: str = "Audio",
) -> dict:
    """Create a new playlist, optionally with initial items.

    Args:
        name: Playlist name.
        item_ids: Optional comma-separated item IDs to add initially.
        media_type: Media type for the playlist — Audio, Video, etc. (default Audio).
    """
    user_id = await _get_user_id()
    body: dict[str, Any] = {
        "Name": name,
        "UserId": user_id,
        "MediaType": media_type,
    }
    if item_ids:
        body["Ids"] = [i.strip() for i in item_ids.split(",")]
    data = await _post("/Playlists", json=body)
    return {"id": data["Id"], "name": name}


@mcp.tool()
async def get_playlist_items(
    playlist_id: str,
    limit: int = 50,
    start_index: int = 0,
) -> dict:
    """Get items in a playlist. Each item includes a playlist_item_id needed for removal.

    Args:
        playlist_id: The playlist's Jellyfin ID.
        limit: Max results (default 50).
        start_index: Offset for pagination.
    """
    user_id = await _get_user_id()
    data = await _get(f"/Playlists/{playlist_id}/Items", params={
        "UserId": user_id,
        "Limit": limit,
        "StartIndex": start_index,
    })
    items = []
    for item in data.get("Items", []):
        s = _summarize_item(item)
        s["playlist_item_id"] = item.get("PlaylistItemId", item["Id"])
        items.append(s)
    return {
        "total_count": data.get("TotalRecordCount", 0),
        "items": items,
    }


@mcp.tool()
async def modify_playlist(
    playlist_id: str,
    add_item_ids: str | None = None,
    remove_item_ids: str | None = None,
) -> str:
    """Add and/or remove items from a playlist in a single operation.

    Args:
        playlist_id: The playlist's Jellyfin ID.
        add_item_ids: Comma-separated item IDs to add to the playlist.
        remove_item_ids: Comma-separated playlist-item IDs to remove (use playlist_item_id from get_playlist_items).
    """
    messages = []
    if add_item_ids:
        ids = [i.strip() for i in add_item_ids.split(",")]
        user_id = await _get_user_id()
        await _post(f"/Playlists/{playlist_id}/Items", params={
            "Ids": ",".join(ids),
            "UserId": user_id,
        })
        messages.append(f"Added {len(ids)} item(s).")
    if remove_item_ids:
        ids = [i.strip() for i in remove_item_ids.split(",")]
        await _delete(f"/Playlists/{playlist_id}/Items", params={
            "EntryIds": ",".join(ids),
        })
        messages.append(f"Removed {len(ids)} item(s).")
    return " ".join(messages) or "No changes requested."


@mcp.tool()
async def delete_playlist(playlist_id: str) -> str:
    """Permanently delete a playlist.

    Args:
        playlist_id: The playlist's Jellyfin ID.
    """
    await _delete(f"/Items/{playlist_id}")
    return f"Playlist {playlist_id} deleted."


# ---------------------------------------------------------------------------
# Tools — Collection Management
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_collections() -> list[dict]:
    """List all collections (box sets) on the server."""
    data = await _get("/Items", params={
        "IncludeItemTypes": "BoxSet",
        "Recursive": True,
    })
    collections = _summarize_items(data.get("Items", []))

    semaphore = asyncio.Semaphore(10)

    async def _fetch_count(col: dict) -> None:
        async with semaphore:
            count_data = await _get("/Items", params={
                "ParentId": col["id"],
                "Recursive": True,
                "Limit": 0,
            })
            col["item_count"] = count_data.get("TotalRecordCount", 0)

    await asyncio.gather(*[_fetch_count(col) for col in collections])
    return collections


@mcp.tool()
async def create_collection(
    name: str,
    item_ids: str | None = None,
) -> dict:
    """Create a new collection, optionally with initial items.

    Args:
        name: Collection name.
        item_ids: Optional comma-separated item IDs to add initially.
    """
    params: dict[str, Any] = {"name": name}
    if item_ids:
        ids = _parse_csv_ids(item_ids)
        if ids:
            params["ids"] = ",".join(ids)
    data = await _post("/Collections", params=params)
    return {"id": data["Id"], "name": name}


@mcp.tool()
async def get_collection_items(
    collection_id: str,
    limit: int = 50,
    start_index: int = 0,
) -> dict:
    """Get items in a collection.

    Args:
        collection_id: The collection's Jellyfin ID.
        limit: Max results (default 50).
        start_index: Offset for pagination.
    """
    data = await _get("/Items", params={
        "ParentId": collection_id,
        "Recursive": True,
        "Limit": limit,
        "StartIndex": start_index,
        "Fields": "Overview,DateCreated",
    })
    return {
        "total_count": data.get("TotalRecordCount", 0),
        "items": _summarize_items(data.get("Items", [])),
    }


@mcp.tool()
async def modify_collection(
    collection_id: str,
    add_item_ids: str | None = None,
    remove_item_ids: str | None = None,
) -> str:
    """Add and/or remove items from a collection in a single operation.

    Args:
        collection_id: The collection's Jellyfin ID.
        add_item_ids: Comma-separated item IDs to add.
        remove_item_ids: Comma-separated item IDs to remove.
    """
    messages = []
    if add_item_ids:
        ids = _parse_csv_ids(add_item_ids)
        if ids:
            await _post(f"/Collections/{collection_id}/Items", params={"ids": ",".join(ids)})
            messages.append(f"Added {len(ids)} item(s).")
    if remove_item_ids:
        ids = _parse_csv_ids(remove_item_ids)
        if ids:
            await _delete(f"/Collections/{collection_id}/Items", params={"ids": ",".join(ids)})
            messages.append(f"Removed {len(ids)} item(s).")
    return " ".join(messages) or "No changes requested."


@mcp.tool()
async def delete_collection(collection_id: str) -> str:
    """Permanently delete a collection. Media files are not affected.

    Args:
        collection_id: The collection's Jellyfin ID.
    """
    await _delete(f"/Items/{collection_id}")
    return f"Collection {collection_id} deleted."


# ---------------------------------------------------------------------------
# Tools — Scheduled Tasks
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_scheduled_tasks() -> list[dict]:
    """List all scheduled tasks on the Jellyfin server with their IDs, names, and states."""
    tasks = await _get("/ScheduledTasks")
    result = []
    for t in tasks:
        entry: dict[str, Any] = {
            "id": t["Id"],
            "name": t["Name"],
            "state": t["State"],
            "last_execution": t.get("LastExecutionResult", {}).get("EndTimeUtc"),
            "last_result": t.get("LastExecutionResult", {}).get("Status"),
        }
        if (pct := t.get("CurrentProgressPercentage")) is not None:
            entry["progress_percent"] = round(pct, 1)
        result.append(entry)
    return result


@mcp.tool()
async def run_scheduled_task(task_id: str) -> str:
    """Trigger a scheduled task to run immediately.

    Args:
        task_id: The task ID from list_scheduled_tasks().
    """
    await _post(f"/ScheduledTasks/Running/{task_id}")
    return f"Scheduled task {task_id} triggered."


# ---------------------------------------------------------------------------
# Tools — Server Status
# ---------------------------------------------------------------------------


@mcp.tool()
async def server_status(include: str = "info") -> dict:
    """Get Jellyfin server status information.

    Args:
        include: Comma-separated sections to include — any combination of "info", "sessions", "tasks", "activity".
                 Defaults to "info" if not specified.
    """
    sections = [s.strip() for s in include.split(",")]

    result: dict[str, Any] = {}

    if "info" in sections:
        info = await _get("/System/Info")
        result["info"] = {
            "server_name": info.get("ServerName"),
            "version": info.get("Version"),
            "os": info.get("OperatingSystem"),
            "has_pending_restart": info.get("HasPendingRestart", False),
            "local_address": info.get("LocalAddress"),
        }

    if "sessions" in sections:
        sessions = await _get("/Sessions")
        result["sessions"] = [
            {
                "user": s.get("UserName", ""),
                "client": s.get("Client", ""),
                "device": s.get("DeviceName", ""),
                "last_activity": s.get("LastActivityDate", ""),
                "now_playing": (
                    _summarize_item(s["NowPlayingItem"]) if s.get("NowPlayingItem") else None
                ),
            }
            for s in sessions
        ]

    if "tasks" in sections:
        tasks = await _get("/ScheduledTasks")
        result["tasks"] = [
            {
                "id": t["Id"],
                "name": t["Name"],
                "state": t["State"],
                "last_execution": t.get("LastExecutionResult", {}).get("EndTimeUtc"),
            }
            for t in tasks
        ]

    if "activity" in sections:
        log = await _get("/System/ActivityLog/Entries", params={"Limit": 20})
        result["activity"] = [
            {
                "date": e.get("Date", ""),
                "type": e.get("Type", ""),
                "overview": e.get("Overview", e.get("ShortOverview", "")),
                "user": e.get("UserName", ""),
            }
            for e in log.get("Items", [])
        ]

    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
