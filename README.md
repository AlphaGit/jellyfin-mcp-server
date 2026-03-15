# Jellyfin MCP Server

An [MCP](https://modelcontextprotocol.io/) server that lets AI assistants manage a [Jellyfin](https://jellyfin.org/) media server. Built with [FastMCP](https://github.com/jlowin/fastmcp) and designed for use with [Claude Code](https://docs.anthropic.com/en/docs/claude-code), but compatible with any MCP client.

## Capabilities

### Library Management
- **List libraries** — enumerate all configured libraries (Movies, Music, Shows, Books, etc.)
- **Scan libraries** — trigger a full rescan or rescan a specific library

### Search & Browse
- **Search media** — find items by keyword with optional type filtering (Audio, MusicAlbum, MusicArtist, Movie, Series, Episode, Book)
- **Browse library** — paginated browsing with configurable sorting (by name, date added, rating, year, etc.)
- **Get item details** — full metadata for any item including genres, tags, people, file path, bitrate, and provider IDs
- **Get recent items** — recently added content, sorted newest first
- **Find similar items** — discover related content based on a given item

### Playlist Management
- **List, create, and delete playlists**
- **Modify playlists** — add and remove items in a single operation
- **Inspect playlist contents** — includes playlist-item IDs needed for removal

### Scheduled Tasks
- **List scheduled tasks** — see all tasks with their current state and progress percentage
- **Run tasks on demand** — trigger any scheduled task immediately (library scans, lyrics downloads, etc.)

### Server Monitoring
- **Server status** — version info, active sessions (with now-playing), scheduled task states, and recent activity log — all in a single configurable call

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A Jellyfin server with an API key

## Installation

```bash
git clone https://github.com/AlphaGit/jellyfin-mcp-server.git
cd jellyfin-mcp-server
uv sync
```

## Configuration

1. Generate an API key in the Jellyfin dashboard under **Administration > Advanced > API Keys**

2. Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

```env
JELLYFIN_URL=https://your-jellyfin-server.com
JELLYFIN_API_KEY=your-api-key-here
JELLYFIN_USERNAME=your-username-here
```

The username is resolved to a user ID at startup. This is required for user-scoped API calls (playlists, item details, etc.) since API key authentication doesn't support the `/Users/Me` endpoint.

## Usage with Claude Code

The repository includes a `.mcp.json` that registers the server automatically. Just open Claude Code in the project directory and restart — the tools will be available immediately.

To use this server from a different project, add it to that project's `.mcp.json`:

```json
{
  "mcpServers": {
    "jellyfin": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--project", "/path/to/jellyfin-mcp-server", "python", "jellyfin_mcp.py"]
    }
  }
}
```

## Usage with other MCP clients

Run the server directly:

```bash
uv run python jellyfin_mcp.py
```

The server communicates over stdio using the MCP protocol.

## License

MIT
