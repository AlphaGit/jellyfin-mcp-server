# Jellyfin MCP Server

An MCP (Model Context Protocol) server that exposes Jellyfin media server management tools for use with Claude Code and other MCP-compatible clients.

## Setup

1. Install dependencies: `uv sync`
2. Generate an API key in the Jellyfin dashboard: **Administration > Advanced > API Keys**
3. Copy `.env.example` to `.env` and fill in your server URL, API key, and username
4. If using Claude Code, the `.mcp.json` registers the server automatically on restart

## Available Tools

| Tool | Description |
|------|-------------|
| `list_libraries` | List all libraries with IDs, names, types, and paths |
| `scan_all_libraries` | Trigger a full rescan of all libraries |
| `scan_library` | Rescan a specific library by ID |
| `search_media` | Search by name/keyword with optional type filter and pagination |
| `get_item_details` | Get full details for a specific item |
| `browse_library` | Browse items with sorting and pagination |
| `get_recent_items` | Get recently added items (newest first) |
| `get_similar_items` | Find items similar to a given item |
| `list_playlists` | List all playlists |
| `create_playlist` | Create a playlist with optional initial items |
| `get_playlist_items` | List items in a playlist (includes IDs needed for removal) |
| `modify_playlist` | Add and/or remove items from a playlist |
| `delete_playlist` | Delete a playlist |
| `list_scheduled_tasks` | List all scheduled tasks with IDs, names, and states |
| `run_scheduled_task` | Trigger a scheduled task to run immediately |
| `server_status` | Get server info, active sessions, scheduled tasks, and activity log |

## Authentication

This server uses API key authentication (not user tokens). The `JELLYFIN_USERNAME` is resolved to a user ID at startup via the `/Users` endpoint, which is needed for user-scoped operations like playlists.
