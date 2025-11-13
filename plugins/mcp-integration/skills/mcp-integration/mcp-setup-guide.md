# MCP Setup Guide

Complete guide for setting up MCP servers in your Claude Code project.

## Prerequisites

- Claude Code installed
- Python 3.10 or higher (for Serena and BigQuery MCPs)
- `uvx` installed (`pip install uv`)
- GitHub Personal Access Token (for GitHub MCP)
- Google Cloud credentials (for BigQuery MCP)
- Notion integration token (for Notion MCP)

## Step-by-Step Setup

### 1. Create `.mcp.json` Configuration

Copy the template from [mcp-config-template.md](./mcp-config-template.md) to your project root as `.mcp.json`.

```bash
# In your project root
cp mcp-config-template.md .mcp.json
# Edit .mcp.json to customize
```

### 2. Set Up Authentication

Follow the [Authentication Guide](./mcp-authentication-guide.md) to configure:
- GitHub Personal Access Token
- Notion integration
- BigQuery credentials

### 3. Install Required Tools

```bash
# Install uvx for local MCP servers
pip install uv

# Verify installation
uvx --version
```

### 4. Restart Claude Code

After creating `.mcp.json` and setting environment variables, restart Claude Code to load the MCP servers.

### 5. Verify MCP Servers

Check that MCP tools are available in Claude Code. You should see tools prefixed with:
- `mcp__github__*` (GitHub operations)
- `mcp__notion__*` (Notion operations)
- `mcp__serena__*` (Code analysis and editing)
- `mcp__awslabs_aws-documentation-mcp-server__*` (AWS docs)
- `mcp__mcp-server-bigquery__*` (BigQuery operations)

### 6. Activate Serena MCP (First Use)

After loading Serena MCP for the first time:

```bash
mcp__serena__activate_project(".")
```

This initializes Serena's code understanding for your project.

## Usage Examples

### GitHub MCP

```bash
# List open pull requests
mcp__github__list_pull_requests(owner="username", repo="repository", state="open")

# Create an issue
mcp__github__issue_write(
    method="create",
    owner="username",
    repo="repository",
    title="New feature request",
    body="Description here"
)

# Search code
mcp__github__search_code(query="function calculateScore language:python")
```

### Serena MCP

```bash
# Get project overview
mcp__serena__get_symbols_overview(relative_path="src/main.py")

# Find a symbol
mcp__serena__find_symbol(
    name_path="MyClass/my_method",
    relative_path="src/main.py",
    include_body=true
)

# Replace symbol body
mcp__serena__replace_symbol_body(
    name_path="MyClass/my_method",
    relative_path="src/main.py",
    body="def my_method(self):\n    return 'updated'"
)

# Write to memory
mcp__serena__write_memory(
    memory_file_name="project-setup",
    content="# Project Setup Notes\n..."
)
```

### BigQuery MCP

```bash
# List tables
mcp__mcp-server-bigquery__list-tables()

# Describe table schema
mcp__mcp-server-bigquery__describe-table(table_name="dataset.table")

# Execute query
mcp__mcp-server-bigquery__execute-query(
    query="SELECT * FROM dataset.table LIMIT 10"
)
```

### Notion MCP

```bash
# Search workspace
mcp__notion__notion-search(
    query="project documentation",
    query_type="internal"
)

# Fetch page
mcp__notion__notion-fetch(id="page-url-or-id")

# Create page
mcp__notion__notion-create-pages(
    pages=[{
        "properties": {"title": "New Page"},
        "content": "# Content here"
    }]
)
```

### AWS Documentation MCP

```bash
# Search AWS docs
mcp__awslabs_aws-documentation-mcp-server__search_documentation(
    search_phrase="Lambda function URLs"
)

# Read specific documentation
mcp__awslabs_aws-documentation-mcp-server__read_documentation(
    url="https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html"
)
```

## Best Practices

### 1. Security
- Store tokens in `.env` file using the `envFile` configuration
- The MCP Integration skill automatically adds `.env` to `.gitignore`
- `.mcp.json` can be safely committed as it only references the `.env` file
- Use different `.env` files for different environments (e.g., `.env.dev`, `.env.prod`)

### 2. Performance
- Disable unused MCP servers with `"disabled": true`
- Use Serena's memory system to cache project knowledge
- Batch BigQuery operations when possible

### 3. Project Organization
- Create Serena memories for project-specific knowledge
- Use consistent naming conventions for memories
- Document MCP usage in project README

### 4. Troubleshooting
- Check Claude Code logs for MCP connection issues
- Verify environment variables are set correctly
- Ensure Python dependencies are installed
- Restart Claude Code after configuration changes

## Common Issues

### MCP Server Not Loading
1. Check `.mcp.json` syntax (valid JSON)
2. Verify `uvx` is installed and in PATH
3. Check Python version (3.10+)
4. Review Claude Code logs for errors

### Authentication Failures
1. Verify tokens are set correctly
2. Check token permissions/scopes
3. Ensure tokens haven't expired
4. Restart Claude Code after setting environment variables

### Serena Performance Issues
1. Reduce `max_answer_chars` in Serena tool calls
2. Use targeted queries instead of broad searches
3. Leverage memory system for frequently accessed information

### BigQuery Connection Issues
1. Verify credentials path is correct
2. Check BigQuery API is enabled
3. Ensure service account has required permissions
4. Validate project ID

## Advanced Configuration

### Custom MCP Server Locations

If you have MCP servers in non-standard locations:

```json
"custom-mcp": {
  "command": "/full/path/to/mcp-server",
  "args": ["--option", "value"],
  "env": {
    "CUSTOM_VAR": "value"
  }
}
```

### Environment-Specific Configurations

Create multiple `.mcp.json` files:
- `.mcp.json` (development)
- `.mcp.production.json` (production)
- `.mcp.testing.json` (testing)

Switch between them as needed.

### Logging and Debugging

Enable verbose logging:

```json
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
    "True"
  ]
}
```

## Next Steps

- Explore [mcp-config-template.md](./mcp-config-template.md) for configuration options
- Review [mcp-authentication-guide.md](./mcp-authentication-guide.md) for security best practices
- Check MCP server documentation for advanced features:
  - [GitHub MCP](https://github.com/github/github-mcp-server)
  - [Serena MCP](https://github.com/oraios/serena)
  - [BigQuery MCP](https://github.com/ergut/mcp-server-bigquery)
  - [Notion MCP](https://mcp.notion.com)
