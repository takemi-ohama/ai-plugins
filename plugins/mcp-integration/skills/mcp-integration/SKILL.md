---
name: MCP Integration Setup
description: Automatically set up GitHub, Serena, BigQuery, Notion, DBHub, and Chrome DevTools MCP servers for enhanced Claude Code capabilities including code analysis, data operations, database management, browser automation, and project management
---

# MCP Integration Project Skill

This skill automatically sets up Model Context Protocol (MCP) servers in your Claude Code project, enabling powerful integrations with:

- **GitHub MCP**: Repository management, PR reviews, issue tracking
- **Serena MCP**: Semantic code understanding, symbol-based editing, memory management
- **BigQuery MCP**: Database queries, table operations, schema management
- **Notion MCP**: Document search, page creation, database operations
- **AWS Documentation MCP**: AWS service documentation access
- **DBHub MCP**: Universal database gateway (PostgreSQL, MySQL, SQL Server, MariaDB, SQLite)
- **Chrome DevTools MCP**: Browser automation, debugging, performance analysis

**Smart Merge**: If you already have `.mcp.json` or `.env` files, this skill intelligently adds only the missing configurations while preserving your existing settings and credentials.

## When This Skill Is Invoked

This skill activates when you mention:
- Setting up MCP servers
- Integrating external services (GitHub, BigQuery, Notion)
- Enabling code analysis capabilities
- Configuring Serena for semantic operations

## What This Skill Does

When invoked, this skill will:

1. **Create or update `.mcp.json`**
   - New setup: Create with all MCP server configurations
   - Existing setup: Add only missing MCP servers, preserve existing ones (smart merge)
   - All servers configured with `envFile` pointing to `.env`

2. **Create or update `.env` template**
   - New setup: Create with all required environment variables (empty values)
   - Existing setup: Append only missing variables, preserve existing values (smart merge)
   - Includes helpful comments with links for obtaining tokens

3. **Protect secrets**
   - Automatically add `.env` to `.gitignore` if not already present
   - Verify and confirm protection status

4. **Verify prerequisites**
   - Check if Python 3.10+ is installed
   - Verify `uvx` is available (required for Serena and BigQuery)
   - Provide installation instructions if missing

5. **Guide next steps**
   - Explain which `.env` values need to be filled
   - Provide links and instructions for obtaining tokens
   - Remind to restart Claude Code
   - Explain how to verify MCP servers are loaded
   - Show how to activate Serena for the current project

**Smart Merge Benefits:**
- ✅ Safe to run multiple times without losing configurations
- ✅ Existing credentials are never overwritten
- ✅ Custom MCP servers and variables are preserved
- ✅ Updates existing projects without breaking them

## Automatic Setup Instructions

**IMPORTANT: When this skill is invoked, follow these steps:**

### Step 1: Read the Configuration Template

Read the complete configuration from `mcp-config-template.md` to get the `.mcp.json` content.

### Step 2: Create or Update `.mcp.json` and `.env` Template

**2a. Create or Update `.mcp.json`**

Check if `.mcp.json` exists:

**If `.mcp.json` does NOT exist:**
- Use the Write tool to create `.mcp.json` with the full configuration from the template

**If `.mcp.json` already exists:**
- Read the existing `.mcp.json` file
- Parse the JSON to identify existing MCP servers in `mcpServers` object
- Compare with the template MCP servers: `github`, `notion`, `serena`, `awslabs.aws-documentation-mcp-server`, `mcp-server-bigquery`, `dbhub`, `chrome-devtools-mcp`
- For each MCP server in the template that does NOT exist in the current config:
  - Add it to the `mcpServers` object
- Preserve all existing MCP servers and their configurations
- Use the Edit tool to add only the missing MCP servers
- Inform the user which MCP servers were added

**Example merge logic:**
```
Existing .mcp.json has: github, custom-server
Template has: github, notion, serena, awslabs.aws-documentation-mcp-server, mcp-server-bigquery, dbhub, chrome-devtools-mcp

Result: Add notion, serena, awslabs.aws-documentation-mcp-server, mcp-server-bigquery, dbhub, chrome-devtools-mcp
Keep: github (existing), custom-server (user's custom server)
```

**2b. Create or Update `.env` Template**

Check if `.env` exists:

**If `.env` does NOT exist:**
- Create a new `.env` file with all required variable names (empty values):

```bash
# GitHub MCP (Required - basic functionality)
# Get token from: https://github.com/settings/tokens
# Required scopes: repo, read:org, workflow
GITHUB_PERSONAL_ACCESS_TOKEN=

# Notion MCP (Optional - only if using Notion)
# Get token from: https://www.notion.so/my-integrations
NOTION_API_KEY=

# BigQuery MCP (Optional - only if using BigQuery)
# Create service account at: https://console.cloud.google.com/iam-admin/serviceaccounts
# Required roles: BigQuery Data Editor, BigQuery Job User
GOOGLE_APPLICATION_CREDENTIALS=

# DBHub MCP (Optional - only if using database operations)
# Database connection string (DSN) - examples:
# PostgreSQL: postgres://user:password@localhost:5432/dbname?sslmode=disable
# MySQL: mysql://user:password@localhost:3306/dbname
# SQLite: sqlite:///path/to/database.db
DATABASE_DSN=

# Note: Serena MCP, AWS Documentation MCP, and Chrome DevTools MCP do not require authentication
```

**If `.env` already exists:**
- Read the existing `.env` file
- Parse to identify which environment variables are already defined
- Check for required variables: `GITHUB_PERSONAL_ACCESS_TOKEN`, `NOTION_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, `DATABASE_DSN`
- For each variable that does NOT exist:
  - Append it to the end of the `.env` file with comments and empty value
- Preserve all existing variables and their values
- Use bash `echo` or Edit tool to append only missing variables
- Inform the user which variables were added

**Example merge logic:**
```
Existing .env has: GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx, CUSTOM_VAR=value
Template needs: GITHUB_PERSONAL_ACCESS_TOKEN, NOTION_API_KEY, GOOGLE_APPLICATION_CREDENTIALS, DATABASE_DSN

Result: Append to .env:
# Notion MCP (Optional - only if using Notion)
NOTION_API_KEY=

# BigQuery MCP (Optional - only if using BigQuery)
GOOGLE_APPLICATION_CREDENTIALS=

# DBHub MCP (Optional - only if using database operations)
DATABASE_DSN=

Keep: GITHUB_PERSONAL_ACCESS_TOKEN and CUSTOM_VAR with their existing values
```

**2c. Add `.env` to `.gitignore`**

Check if `.env` is already in `.gitignore`:

```bash
grep "^\.env$" .gitignore
```

If NOT found, add it:
```bash
echo ".env" >> .gitignore
```

Confirm to the user what was done:
- If added: "✅ Added `.env` to `.gitignore`"
- If already present: "✅ `.env` is already in `.gitignore`"

### Step 3: Verify Prerequisites

Check and inform the user about required tools:

```bash
# Check Python version
python --version

# Check uvx installation
uvx --version
```

If missing, provide installation instructions:
- Python 3.10+: Link to python.org
- uvx: `pip install uv`

### Step 4: Guide User to Fill `.env` File

Inform the user about what was created or updated and guide them to fill in the values.

**Explain what was done:**

**For new setup (no existing files):**
- ✅ `.mcp.json` has been created with all MCP server configurations
- ✅ `.env` template has been created with empty values
- ✅ `.env` has been added to `.gitignore`

**For existing setup (files already present):**
- ✅ `.mcp.json` has been updated with missing MCP servers: [list the servers that were added]
- ✅ `.env` has been updated with missing variables: [list the variables that were added]
- ✅ `.env` is already in `.gitignore` (or was just added)
- ✅ Your existing configurations and credentials were preserved

**Next steps for the user:**

1. **Open the `.env` file** in the project root
2. **Fill in the empty values** (variables without values after `=`):

**GitHub Personal Access Token (Required):**
- Visit: https://github.com/settings/tokens
- Click "Generate new token (classic)"
- Select scopes: `repo`, `read:org`, `workflow`
- Copy token and paste after `GITHUB_PERSONAL_ACCESS_TOKEN=`

**Notion API Key (Optional - only if using Notion):**
- Visit: https://www.notion.so/my-integrations
- Create new integration
- Copy token and paste after `NOTION_API_KEY=`
- Connect integration to Notion pages/databases

**BigQuery Credentials (Optional - only if using BigQuery):**
- Visit: https://console.cloud.google.com/iam-admin/serviceaccounts
- Create service account with roles: `BigQuery Data Editor`, `BigQuery Job User`
- Download JSON key
- Add file path after `GOOGLE_APPLICATION_CREDENTIALS=`

**Example `.env` after filling:**
```bash
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_abc123xyz789...
NOTION_API_KEY=secret_abc123xyz789...
GOOGLE_APPLICATION_CREDENTIALS=/Users/you/Downloads/my-project-key.json
```

### Step 5: Next Steps Instructions

Provide clear next steps:

1. **Fill in `.env` file** with your credentials (see Step 4)
2. **Restart Claude Code** to load MCP servers
3. **Verify MCP tools** are available (look for `mcp__github__*`, `mcp__serena__*`, etc.)
4. **Activate Serena** for the current project:
   ```
   mcp__serena__activate_project(".")
   ```

**Summary of what was automated:**
- ✅ `.mcp.json` created or updated (missing MCP servers added, existing ones preserved)
- ✅ `.env` template created or updated (missing variables added, existing values preserved)
- ✅ `.env` added to `.gitignore` to protect secrets
- ✅ Smart merge: existing configurations and credentials were not overwritten
- ⏭️ User only needs to fill in empty values in `.env` and restart Claude Code

## Configuration Details

The `.mcp.json` file includes:

### GitHub MCP (HTTP-based)
- Repository operations, PR management, issue tracking
- Requires: `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable

### Notion MCP (HTTP-based)
- Document management, database operations
- Authentication handled automatically via Notion's flow

### Serena MCP (Local)
- Semantic code understanding and editing
- Requires: Python 3.10+, uvx
- No authentication needed

### AWS Documentation MCP (Local, Optional)
- AWS service documentation access
- No authentication needed

### BigQuery MCP (Local)
- Database operations
- Requires: Google Cloud credentials

## Customization Options

Users can customize by:
- Disabling specific MCP servers: Add `"disabled": true`
- Adding environment variables to the `env` object
- Adjusting command arguments

See [mcp-config-template.md](./mcp-config-template.md) for examples.

## Troubleshooting

If MCP servers don't load after setup:
1. Check `.mcp.json` syntax (must be valid JSON)
2. Verify environment variables: `echo $GITHUB_PERSONAL_ACCESS_TOKEN`
3. Restart Claude Code completely
4. Check Claude Code logs for errors

For detailed troubleshooting, see [mcp-setup-guide.md](./mcp-setup-guide.md).
