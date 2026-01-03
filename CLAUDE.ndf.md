<!-- NDF_PLUGIN_GUIDE_START_8k3jf9s2n4m5p7q1w6e8r0t2y4u6i8o -->
<!-- VERSION: 3 -->
# NDF Plugin - AI Agent Guidelines (v2.0.0)

## Overview

NDF plugin provides **7 MCP servers, 6 commands, and 5 specialized sub-agents**. Delegate complex tasks to appropriate sub-agents for better results.

> **Note (v2.0.0)**: GitHub MCP, Serena MCP, Context7 MCPは公式プラグイン（`anthropics/claude-plugins-official`）に移行しました。directorエージェントはClaude Code組み込み機能（Plan Mode、Explore Agent）と重複するため削除されました。

## Core Policies

### 1. Language
- All responses, documentation, and commit messages must be in **Japanese**.

### 2. Git Restrictions
- **No unauthorized git push/merge**
- **Never push/merge directly to default branch (main/master)**
- Always confirm with user before commit/push/PR merge (except explicit slash commands)
- Use feature branches and create pull requests

## Action Guidelines

### 1. Context Management

**Critical**: Load only necessary information progressively.

- Check symbol overview before reading entire files
- Load only required portions
- Be conscious of token usage

### 2. Sub-Agent Delegation

**Main Agent Responsibilities:**
- Receive user requests
- **Classify tasks and delegate to appropriate specialized sub-agents**
- Use Claude Code's **Plan Mode** for complex multi-step tasks
- Use Claude Code's **Explore Agent** for codebase investigation
- Coordinate multi-agent workflows
- Pass through final results to user

**Core Principle:**
- **Match task type to specialized sub-agent**
- Use Plan Mode (EnterPlanMode) for implementation planning
- Use Explore Agent for code exploration
- Specialized sub-agents handle domain-specific tasks

### 3. Claude Code Built-in Features

**Use Claude Code's built-in features** for planning and exploration:

#### Plan Mode
For complex implementation tasks requiring planning:
```
EnterPlanMode() → Explore codebase → Design approach → User approval → ExitPlanMode → Implement
```

#### Explore Agent
For codebase investigation:
```
Task(subagent_type="Explore", prompt="Find how authentication is implemented", description="Explore auth code")
```

### 4. Serena MCP Usage (Official Plugin)

**Serena MCP is now available via official plugin.** Install separately:
```bash
/plugin install serena@anthropics/claude-plugins-official
```

#### Key Commands

**Read code progressively (not entire files):**
```bash
# 1. Get symbol overview first
mcp__plugin_official_serena__get_symbols_overview relative_path="path/to/file.py"

# 2. Find specific symbol
mcp__plugin_official_serena__find_symbol name_path="/ClassName" relative_path="src/" include_body=true

# 3. Search pattern if symbol name unknown
mcp__plugin_official_serena__search_for_pattern substring_pattern="TODO" relative_path="src/"
```

#### Best Practices

- Get symbol overview before reading files
- Use symbol-based editing
- Don't read entire files, don't use for binary files (PDF/images)

### 5. Research Facts

**For technically challenging tasks, research external resources instead of guessing.**

- Static website content -> **WebFetch tool** (fast, lightweight)
- Cloud services (AWS, GCP) -> **researcher agent** with AWS Docs MCP
- Latest libraries/frameworks -> **corder agent** (Context7 via official plugin)
- Dynamic content requiring JavaScript -> **researcher agent** with Chrome DevTools MCP

### 6. Skills Usage

**Claude Code Skills are model-invoked**: Claude autonomously activates Skills based on request and Skill description.

**8 Available Skills (v2.0.0):**

**Data Analyst Skills (2):**
- `data-analyst-sql-optimization` - SQL optimization patterns and best practices
- `data-analyst-export` - Export query results to CSV/JSON/Excel/Markdown formats

**Corder Skills (2):**
- `corder-code-templates` - Code generation templates (REST API, React, database models, authentication)
- `corder-test-generation` - Automated unit/integration test generation with AAA pattern

**Researcher Skills (1):**
- `researcher-report-templates` - Structured research report templates with comparison tables and best practices

**Scanner Skills (2):**
- `scanner-pdf-analysis` - PDF text extraction, table detection, and summarization
- `scanner-excel-extraction` - Excel data extraction and conversion to JSON/CSV

**QA Skills (1):**
- `qa-security-scan` - Security scanning with OWASP Top 10 checklist

**How Skills Work:**
- **Model-invoked**: Claude decides when to use based on request keywords and context
- **Trigger keywords**: Each Skill description contains keywords (e.g., "optimize SQL", "security scan")
- **Progressive disclosure**: Main documentation <=500 lines, detailed references loaded as needed
- **Sub-agent specialization**: Skills complement each sub-agent's existing capabilities

## Sub-Agent Invocation

Use **Task tool** to invoke sub-agents:

```
Task(
  subagent_type="ndf:corder",          # Agent name (ndf: prefix required)
  prompt="detailed instructions",      # Instructions for agent
  description="Task description"       # 3-5 word description
)
```

**Available subagent_type:**
- `ndf:corder` - Coding expert
- `ndf:data-analyst` - Data analysis expert
- `ndf:researcher` - Research expert
- `ndf:scanner` - File reading expert
- `ndf:qa` - Quality assurance expert

### 5 Specialized Sub-Agents

**Important:** All specialized sub-agents **MUST NOT** call other sub-agents. They can only use MCP tools directly. Task delegation and coordination is exclusively the role of the Main agent.

#### 1. @data-analyst - Data Analysis Expert

**Use Cases:**
- Database queries
- SQL generation/optimization
- Data analysis/statistics
- Save query results to files (CSV/JSON/Excel)

**MCP Tools:** BigQuery MCP, DBHub MCP

**Example:**
```
User: "Analyze last month's sales data in BigQuery and show top 10 products"

Main Agent: Data analysis task -> delegate to ndf:data-analyst

Task(
  subagent_type="ndf:data-analyst",
  prompt="Analyze last month's sales data in BigQuery and extract top 10 products. Use sales_data.transactions dataset.",
  description="Analyze sales data"
)
```

#### 2. @corder - Coding Expert

**Use Cases:**
- Writing new code
- Refactoring existing code
- Code review/security check
- Applying design patterns/architecture
- Checking latest best practices

**MCP Tools:** Codex CLI MCP

> **Note**: Serena MCP and Context7 MCP are available via official plugins. Install separately to use with corder.

**Example:**
```
User: "Implement user authentication feature"

Main Agent: Coding task -> delegate to ndf:corder

Task(
  subagent_type="ndf:corder",
  prompt="Implement user authentication feature using JWT. Include login/logout/token refresh endpoints. Follow security best practices and review with Codex.",
  description="Implement user authentication"
)
```

#### 3. @researcher - Research Expert

**Use Cases:**
- Research AWS official documentation
- Collect information from websites
- Investigate technical specifications/best practices
- Research competitor site features
- Capture screenshots/PDFs

**MCP Tools:** WebFetch tool (priority), AWS Documentation MCP, Chrome DevTools MCP, Codex CLI MCP

**Example:**
```
User: "Research AWS Lambda best practices"

Main Agent: Research task -> delegate to ndf:researcher

Task(
  subagent_type="ndf:researcher",
  prompt="Research AWS Lambda best practices. Reference AWS official documentation and summarize from performance optimization, security, and cost reduction perspectives.",
  description="Research AWS Lambda best practices"
)
```

#### 4. @scanner - File Reading Expert

**Use Cases:**
- Reading PDF files
- Extracting text from images (OCR)
- Reading PowerPoint/Excel files
- Describing image content

**MCP Tools:** Codex CLI MCP

**Example:**
```
User: "Read document.pdf and summarize"

Main Agent: File reading task -> delegate to ndf:scanner

Task(
  subagent_type="ndf:scanner",
  prompt="Read /path/to/document.pdf and summarize key points in 3-5 items.",
  description="Read and summarize PDF"
)
```

#### 5. @qa - Quality Assurance Expert

**Use Cases:**
- Code quality review
- Security vulnerability check
- Web application performance measurement
- Test coverage verification
- Documentation quality validation

**MCP Tools:** WebFetch tool (priority), Codex CLI MCP, Chrome DevTools MCP

**Examples:**
```
User: "Review this code's quality and security"

Main Agent: QA task -> delegate to ndf:qa

Task(
  subagent_type="ndf:qa",
  prompt="Review src/auth.js code. Check code quality (readability, maintainability), security (OWASP Top 10), best practices compliance, and provide improvement suggestions. Perform security scan with Codex.",
  description="Code quality and security review"
)
```

```
User: "Measure web application performance"

Main Agent: Performance test task -> delegate to ndf:qa

Task(
  subagent_type="ndf:qa",
  prompt="Measure performance of https://example.com. Evaluate Core Web Vitals (LCP, FID, CLS) with Chrome DevTools, analyze network and rendering performance. Include improvement suggestions if bottlenecks found.",
  description="Performance testing with Chrome DevTools"
)
```

## Task Classification

**Quick Decision Flow for Main Agent:**

| Task Type | Action |
|-----------|--------|
| **Complex multi-step implementation** | Use **Plan Mode** (EnterPlanMode) |
| **Codebase exploration/investigation** | Use **Explore Agent** |
| **Data analysis/SQL** | Delegate to `ndf:data-analyst` |
| **Coding/implementation** | Delegate to `ndf:corder` |
| **Research/documentation** | Delegate to `ndf:researcher` |
| **File reading (PDF/images)** | Delegate to `ndf:scanner` |
| **Quality/security review** | Delegate to `ndf:qa` |

## Multi-Agent Collaboration

For complex tasks, **Main Agent coordinates multiple sub-agents**.

### Parallel Execution (Recommended)

Main Agent should identify tasks that can run in parallel when:

- Target files do not overlap
- Tasks are independent (no dependencies)
- Memory usage is manageable

**Example: Complex Feature Implementation**
```
User: "Add a new dashboard feature that fetches data from BigQuery and displays performance metrics"

Step 1: Main Agent uses Plan Mode to design approach
EnterPlanMode() -> Investigate codebase -> Create plan -> Get user approval

Step 2: Main Agent delegates to specialized agents
Task(subagent_type="ndf:data-analyst", ...)  # BigQuery query design
Task(subagent_type="ndf:corder", ...)        # UI implementation (can run in parallel with qa)
Task(subagent_type="ndf:qa", ...)            # Code quality review (parallel)

Step 3: Main Agent integrates results and reports to user
```

**Example: Research -> Implementation**
```
User: "Research AWS Lambda best practices and write code based on findings"

Main Agent -> researcher (AWS Lambda best practices)
Main Agent -> corder (Implementation based on findings)
Main Agent -> User (Final code)
```

## Best Practices

### DO (Recommended)

- **Use Plan Mode for complex multi-step implementations**
- **Use Explore Agent for codebase investigation**
- **Use specialized agents for each task type**
- **Decompose complex tasks and delegate to multiple agents**
- **Validate and integrate agent results**
- **Start parallel tasks simultaneously when possible**

### DON'T (Not Recommended)

- **Handle specialized tasks with main agent** -> Delegate to sub-agents
- **Respond with guesses without research** -> Research with appropriate agent
- **Implement complex code without review** -> Delegate to corder with Codex review
- **Try to process PDFs/images directly** -> Delegate to scanner

## Available MCP Tools (Reference)

Main agent can use these MCPs, but **delegating to specialized agents produces better quality**:

**Built-in Tools:**
- **WebFetch**: Fast web content retrieval, HTML to Markdown conversion, AI-based processing (15-min cache)

**Official Plugins (install separately):**
- **GitHub MCP**: PR/issue management, code search (`/plugin install github@anthropics/claude-plugins-official`)
- **Serena MCP**: Code structure understanding, symbol editing (`/plugin install serena@anthropics/claude-plugins-official`)
- **Context7 MCP**: Latest library documentation (`/plugin install context7@anthropics/claude-plugins-official`)

**NDF Plugin MCPs:**
- **Codex CLI MCP**: -> **Delegate to @corder or @scanner**
- **BigQuery MCP**: Database queries -> **Delegate to @data-analyst**
- **AWS Docs MCP**: AWS documentation -> **Delegate to @researcher**
- **Chrome DevTools MCP**: Web performance/debugging -> **Delegate to @researcher or @qa**

## Summary

**Main Agent Role:**
- Receive user requests
- **Use Plan Mode for complex implementation planning**
- **Use Explore Agent for codebase investigation**
- **Classify tasks and delegate to appropriate specialized sub-agents**
- Coordinate multi-agent workflows
- Pass through final results to user

**Specialized Sub-Agent Roles:**
- High-quality execution in specialized domains (coding, data, research, scanning, QA)
- Effective use of specialized MCP tools
- Detailed analysis and implementation
- **Cannot call other sub-agents**

**Success Key:**
**Main Agent uses Claude Code built-in features (Plan Mode, Explore Agent) for planning and investigation, then delegates domain-specific tasks to specialized sub-agents.** This architecture leverages both Claude Code's powerful built-in capabilities and NDF's specialized agents for optimal results.
<!-- NDF_PLUGIN_GUIDE_END_8k3jf9s2n4m5p7q1w6e8r0t2y4u6i8o -->
