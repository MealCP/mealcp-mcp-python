# MealCP MCP

Official [Model Context Protocol](https://modelcontextprotocol.io) server for
[MealCP](https://mealcp.com) — the grocery & food data layer for AI agents.

Exposes two tools over the MealCP public API:

- **`search_products`** — search the grocery product catalog by keyword with
  faceted filtering (country, retailer, chain, brand, tag, category, city,
  price range, sort, pagination).
- **`get_price_history`** — aggregated price-history stats (min/max/avg/first/
  last, net change) for one product over a date range.

## Requirements

- Python 3.10+
- An API key from MealCP (each tool call consumes 1 credit)

## Usage

Run directly with [uv](https://docs.astral.sh/uv/):

```bash
uvx mealcp-mcp
```

Or install:

```bash
pip install mealcp-mcp
mealcp-mcp
```

The server speaks MCP over stdio; any MCP host (Claude Desktop, opencode,
Cursor, …) can spawn it.

### Claude Desktop

```json
{
  "mcpServers": {
    "mealcp": {
      "command": "uvx",
      "args": ["mealcp-mcp"],
      "env": {
        "MEALCP_API_URL": "https://api.mealcp.com",
        "MEALCP_API_KEY": "mcp_live_your_key_here"
      }
    }
  }
}
```

### opencode

```json
{
  "mcp": {
    "mealcp": {
      "type": "local",
      "command": ["uvx", "mealcp-mcp"],
      "enabled": true,
      "environment": {
        "MEALCP_API_URL": "https://api.mealcp.com",
        "MEALCP_API_KEY": "mcp_live_your_key_here"
      }
    }
  }
}
```

## Configuration

| Variable         | Default                | Description                          |
| ---------------- | ---------------------- | ------------------------------------ |
| `MEALCP_API_URL` | `http://localhost:8000`| Base URL of the MealCP API           |
| `MEALCP_API_KEY` | _(none)_               | `X-API-Key` sent with every request  |

## Errors

Tool errors surface the API's stable error tokens, formatted
`<code>: <message>` (e.g. `not_found: Product not found`). Branch on the code,
never the message.

## Contract

Response models are generated from the API's OpenAPI spec
(`contract/openapi.json`, currently version **0.1.0**). Refresh with:

```bash
uvx --from datamodel-code-generator datamodel-codegen \
  --input contract/openapi.json \
  --output src/mealcp_mcp/models.py \
  --output-model-type pydantic_v2.BaseModel \
  --target-python-version 3.10 --disable-timestamp
```

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
```

## License

MIT
