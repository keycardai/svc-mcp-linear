# svc-mcp-linear

Linear MCP Server for Cloudflare Workers.

This is a "dumb" MCP server that receives pre-exchanged tokens from an MCP Gateway. It does not handle authentication itself - the gateway handles OAuth and token exchange.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  MCP Client │────▶│ MCP Gateway │────▶│ This Server │────▶ Linear API
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                    (Token Exchange)     (Bearer token in
                           │              Auth header)
                    ┌──────▼──────┐
                    │   Keycard   │
                    └─────────────┘
```

The gateway exchanges tokens and passes the Linear API token in the `Authorization` header as a Bearer token. This server simply reads that token and uses it for Linear API calls.

## Tools

| Tool | Type | Description |
|------|------|-------------|
| `my_issues` | Query | Get issues assigned to authenticated user |
| `issue` | Query | Get details of a specific issue by identifier (e.g., ENG-123) |
| `search` | Query | Search issues by text query (searches title and description) |
| `create_issue` | Mutation | Create a new issue (requires team_id and title) |
| `update_issue` | Mutation | Update issue fields (title, description, priority, etc.) |
| `update_status` | Mutation | Change issue workflow state |
| `states` | Query | List available workflow states for a team |

### Tool Details

#### `my_issues`
Returns issues assigned to the authenticated user.

**Response:**
```json
{
  "success": true,
  "issues": [
    {
      "id": "uuid",
      "identifier": "ENG-123",
      "title": "Fix login bug",
      "description": "...",
      "state": { "name": "In Progress" },
      "priority": 2,
      "project": { "name": "Backend" }
    }
  ],
  "count": 1
}
```

#### `issue`
Get details of a specific issue.

**Parameters:**
- `identifier` (required): Issue identifier like "ENG-123"

**Response:**
```json
{
  "success": true,
  "issue": {
    "id": "uuid",
    "identifier": "ENG-123",
    "title": "Fix login bug",
    "description": "...",
    "state": { "id": "state-uuid", "name": "In Progress" },
    "priority": 2,
    "labels": { "nodes": [{ "name": "bug" }] },
    "assignee": { "name": "John Doe", "email": "john@example.com" },
    "team": { "id": "team-uuid", "name": "Engineering" },
    "comments": { "nodes": [...] }
  }
}
```

#### `search`
Search issues by text query.

**Parameters:**
- `query` (required): Search text (case-insensitive, searches title and description)

#### `create_issue`
Create a new issue.

**Parameters:**
- `team_id` (required): Team UUID
- `title` (required): Issue title
- `description` (optional): Issue description (markdown supported)
- `priority` (optional): 0=none, 1=urgent, 2=high, 3=medium, 4=low
- `state_id` (optional): Initial workflow state UUID
- `assignee_id` (optional): Assignee user UUID

#### `update_issue`
Update an existing issue.

**Parameters:**
- `issue_id` (required): Issue UUID (from issue query, not the identifier)
- `title` (optional): New title
- `description` (optional): New description
- `priority` (optional): New priority
- `state_id` (optional): New workflow state UUID
- `assignee_id` (optional): New assignee UUID

#### `update_status`
Change issue workflow state.

**Parameters:**
- `issue_id` (required): Issue UUID
- `state_id` (required): Target workflow state UUID (get from `states` tool)

#### `states`
Get available workflow states.

**Parameters:**
- `team_id` (optional): Team UUID. If not provided, returns states for all teams.

**Response (single team):**
```json
{
  "success": true,
  "team": { "id": "team-uuid", "name": "Engineering" },
  "states": [
    { "id": "state-1", "name": "Backlog", "type": "backlog" },
    { "id": "state-2", "name": "In Progress", "type": "started" },
    { "id": "state-3", "name": "Done", "type": "completed" }
  ]
}
```

## Local Development

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Clone and enter the directory:
   ```bash
   cd svc-mcp-linear
   ```

2. Create virtual environment and install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

3. Create `.env` from example:
   ```bash
   cp .env.example .env
   # Edit .env with your Linear API token
   ```

4. Get a Linear API token:
   - Go to Linear Settings > API > Personal API Keys
   - Create a new key and copy it to your `.env` file

### Run Locally

```bash
uv run python -m src.server
```

Server starts at `http://localhost:8000/mcp`

### Testing with MCP Inspector

You can test the server with the MCP Inspector or curl:

```bash
# List tools
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer lin_api_xxx" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# Call my_issues tool
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer lin_api_xxx" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"my_issues","arguments":{}},"id":2}'
```

## Running Tests

```bash
uv run pytest
```

With coverage:
```bash
uv run pytest --cov=src --cov-report=term-missing
```

## Cloudflare Deployment

> Note: Cloudflare deployment is out of scope for initial implementation. The `wrangler.toml` is provided for future deployment.

```bash
# Install pywrangler (when ready for deployment)
pip install pywrangler

# Deploy
pywrangler deploy

# Set secrets
wrangler secret put LINEAR_API_TOKEN
```

## Error Handling

All tools return a consistent response structure:

**Success:**
```json
{
  "success": true,
  "issues": [...],
  "count": 5
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message describing what went wrong",
  "isError": true
}
```

Common errors:
- `Missing Authorization header` - No Bearer token provided
- `Linear API returned HTTP 401` - Invalid or expired token
- `Issue ENG-999 not found` - Issue doesn't exist or no access

## Project Structure

```
svc-mcp-linear/
├── src/
│   ├── __init__.py
│   ├── server.py          # FastMCP entry point
│   ├── client.py          # Linear GraphQL client
│   └── tools/
│       ├── __init__.py
│       ├── issues.py      # my_issues, issue, search
│       ├── mutations.py   # create_issue, update_issue, update_status
│       └── states.py      # states
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_client.py
│   └── test_tools.py
├── pyproject.toml
├── wrangler.toml
├── .env.example
└── README.md
```

## License

Internal use only.
