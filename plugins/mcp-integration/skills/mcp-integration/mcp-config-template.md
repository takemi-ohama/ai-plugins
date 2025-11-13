# MCP Configuration Template

Create a `.mcp.json` file in your project root with this configuration:

```json
{
  "name": "Your Project MCP Configuration",
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp",
      "headers": {
        "Authorization": "Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}"
      },
      "envFile": "${workspaceFolder}/.env"
    },
    "notion": {
      "type": "http",
      "url": "https://mcp.notion.com/mcp",
      "envFile": "${workspaceFolder}/.env"
    },
    "serena": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--context",
        "ide-assistant",
        "--enable-web-dashboard",
        "False"
      ],
      "envFile": "${workspaceFolder}/.env"
    },
    "awslabs.aws-documentation-mcp-server": {
      "command": "uvx",
      "args": [
        "awslabs.aws-documentation-mcp-server@latest"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR",
        "AWS_DOCUMENTATION_PARTITION": "aws"
      },
      "envFile": "${workspaceFolder}/.env",
      "disabled": false
    },
    "mcp-server-bigquery": {
      "command": "uvx",
      "args": [
        "mcp-server-bigquery@latest"
      ],
      "envFile": "${workspaceFolder}/.env",
      "disabled": false
    },
    "dbhub": {
      "command": "npx",
      "args": [
        "@bytebase/dbhub",
        "--transport",
        "http",
        "--port",
        "8080",
        "--dsn",
        "${DATABASE_DSN}"
      ],
      "envFile": "${workspaceFolder}/.env",
      "disabled": false
    },
    "chrome-devtools-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "chrome-devtools-mcp@latest"
      ],
      "envFile": "${workspaceFolder}/.env",
      "disabled": false
    }
  }
}
```

## Environment File (.env)

Create a `.env` file in your project root with the following variables:

```bash
# GitHub MCP (Required for full functionality)
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here

# Notion MCP (Optional - only if using Notion)
NOTION_API_KEY=secret_your_token_here

# BigQuery MCP (Optional - only if using BigQuery)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# DBHub MCP (Optional - only if using database operations)
# Database connection string (DSN) - examples:
# PostgreSQL: postgres://user:password@localhost:5432/dbname?sslmode=disable
# MySQL: mysql://user:password@localhost:3306/dbname
# SQLite: sqlite:///path/to/database.db
DATABASE_DSN=

# Note: Serena MCP, AWS Documentation MCP, and Chrome DevTools MCP do not require authentication
```

**IMPORTANT**: The MCP Integration skill automatically adds `.env` to your `.gitignore` to prevent committing sensitive credentials.

✅ **Automatically handled by the skill:**
- `.env` is added to `.gitignore` during setup
- No manual action required
- Your credentials are protected from accidental commits

If you created the `.env` file manually, verify it's in `.gitignore`:
```bash
grep "^\.env$" .gitignore
```

If not found, add it manually:
```bash
echo ".env" >> .gitignore
```

## MCP Server Descriptions

### GitHub MCP (HTTP-based)
- **Purpose**: Repository operations, PR management, issue tracking
- **Authentication**: Requires `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable
- **Tools**: create_pull_request, add_issue_comment, merge_pull_request, search_code, etc.

### Notion MCP (HTTP-based)
- **Purpose**: Document management, database operations
- **Authentication**: Automatic via Notion's authentication flow
- **Tools**: notion-search, notion-fetch, notion-create-pages, notion-update-page, etc.

### Serena MCP (Local)
- **Purpose**: Semantic code understanding and editing
- **Requirements**: Python 3.10+, uvx
- **Tools**: find_symbol, replace_symbol_body, search_for_pattern, write_memory, etc.

### AWS Documentation MCP (Local, Optional)
- **Purpose**: AWS service documentation access
- **Tools**: read_documentation, search_documentation, recommend

### BigQuery MCP (Local)
- **Purpose**: Database operations
- **Authentication**: Google Cloud credentials via application default credentials
- **Tools**: execute-query, list-tables, describe-table

### DBHub MCP (Local)
- **Purpose**: Universal database gateway supporting PostgreSQL, MySQL, SQL Server, MariaDB, and SQLite
- **Authentication**: Database connection string (DSN) via environment variable
- **Tools**: Schema exploration (resources), SQL execution (tools), AI-assisted SQL generation (prompts)
- **Requirements**: Node.js (for npx)

### Chrome DevTools MCP (Local)
- **Purpose**: Control and inspect live Chrome browsers for automation, debugging, and performance analysis
- **Authentication**: Not required (optional for remote connections)
- **Tools**: Input automation (click, fill, drag), navigation, emulation, performance tracing, network monitoring, debugging
- **Requirements**: Node.js (for npx), Chrome browser

## Customization

### Disabling MCP Servers

Add `"disabled": true` to any server configuration:

```json
"serena": {
  "command": "uvx",
  "args": ["..."],
  "disabled": true
}
```

### Using Environment File

All MCP servers are configured to read from a single `.env` file via the `envFile` property:

```json
"envFile": "${workspaceFolder}/.env"
```

This approach provides:
- **Centralized management**: All credentials in one file
- **Security**: Easy to add to `.gitignore`
- **Portability**: Share `.mcp.json` safely without exposing secrets
- **Team collaboration**: Each team member maintains their own `.env` file

### Adding Additional Environment Variables

To add more environment variables, simply add them to your `.env` file:

```bash
# Custom variables
BIGQUERY_PROJECT_ID=your-project-id
CUSTOM_API_KEY=your-custom-key
```

These variables will be available to all MCP servers that have `envFile` configured.

## Verification

After creating `.mcp.json` and `.env`:

1. **Verify `.env` exists in project root**
   ```bash
   ls -la .env
   ```

2. **Verify `.env` is in `.gitignore`**
   ```bash
   grep "^\.env$" .gitignore
   ```

3. **Restart Claude Code** to load MCP servers

4. **Check available tools** - Look for:
   - `mcp__github__*`
   - `mcp__serena__*`
   - `mcp__notion__*` (if Notion configured)
   - `mcp__awslabs_aws-documentation-mcp-server__*`
   - `mcp__mcp-server-bigquery__*` (if BigQuery configured)
   - `mcp__dbhub__*` (if DBHub configured)
   - `mcp__chrome-devtools-mcp__*` (if Chrome DevTools configured)
