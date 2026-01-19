<!-- NDF_PLUGIN_GUIDE_START_8k3jf9s2n4m5p7q1w6e8r0t2y4u6i8o -->
<!-- VERSION: 6 -->
# NDF Plugin - AI Agent Guidelines (v2.1.3)

## Overview

NDF plugin provides **7 MCP servers, 6 commands, and 6 specialized sub-agents**. Delegate complex tasks to appropriate sub-agents for better results.

> **Note (v2.1.0)**: GitHub MCP, Serena MCP, Context7 MCPは公式プラグイン（`anthropics/claude-plugins-official`）に移行しました。directorエージェントはClaude Code機能を活用する指揮者として再定義されました。

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
- **For complex multi-step tasks, delegate to `ndf:director`** (recommended)
- For simple tasks, delegate directly to specialized sub-agents
- Pass through final results to user

**Core Principle:**
- **director is the orchestrator** - coordinates other sub-agents
- **Specialized sub-agents cannot call other sub-agents**
- Match task complexity to appropriate delegation level

### 3. Director Agent - The Orchestrator

**`ndf:director` reports to Main Agent, which then calls sub-agents.**

> **重要**: directorは他のサブエージェントを**直接呼び出しません**。Main Agentに必要なエージェントを報告し、Main Agentがサブエージェントを起動します。これによりメモリエラーを防止します。

Use director when:
- Task requires multiple sub-agents
- Task needs planning and coordination
- Main agent's context consumption should be minimized

```
Task(
  subagent_type="ndf:director",
  prompt="Implement user authentication with JWT. Research best practices, implement code, and review security.",
  description="Implement auth feature"
)
```

Director will:
1. Analyze task scale (small/medium/large)
2. Use Plan Mode for large tasks
3. **Save plans/research to project files** (issues/, docs/, specs/)
4. **Report required sub-agents to Main Agent**
5. Main Agent calls sub-agents based on report
6. Director integrates results and reports to user

### 4. Claude Code Built-in Features

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

### 5. Serena MCP Usage (Official Plugin)

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

### 6. Research Facts

**For technically challenging tasks, research external resources instead of guessing.**

- Static website content -> **WebFetch tool** (fast, lightweight)
- Cloud services (AWS, GCP) -> **researcher agent** with AWS Docs MCP
- Latest libraries/frameworks -> **corder agent** (Context7 via official plugin)
- Dynamic content requiring JavaScript -> **researcher agent** with Chrome DevTools MCP

### 7. Skills Usage

**Claude Code Skills are model-invoked**: Claude autonomously activates Skills based on request and Skill description.

**8 Available Skills (v2.1.0):**

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

## Sub-Agent Invocation

Use **Task tool** to invoke sub-agents:

```
Task(
  subagent_type="ndf:director",        # Agent name (ndf: prefix required)
  prompt="detailed instructions",      # Instructions for agent
  description="Task description"       # 3-5 word description
)
```

**Available subagent_type (with proactive triggers):**
- `ndf:director` - **Orchestrator** | Use proactively for: complex multi-step tasks, planning/design decisions, multi-agent coordination
- `ndf:corder` - Coding expert | Use proactively for: code implementation, refactoring, code review, design patterns
- `ndf:data-analyst` - Data analysis expert | Use proactively for: SQL queries, BigQuery, data analysis, data export
- `ndf:researcher` - Research expert | Use proactively for: AWS docs research, technical investigation, web scraping
- `ndf:scanner` - File reading expert | Use proactively for: PDF reading, image OCR, Office file extraction
- `ndf:qa` - QA expert | Use proactively for: security review (OWASP), code quality, performance testing

### 6 Specialized Sub-Agents

#### 1. @director - Orchestrator

**Reports to Main Agent for sub-agent coordination (does NOT call sub-agents directly).**

> メモリエラー防止のため、directorは他のサブエージェントを直接呼び出しません。

**Use proactively for:** complex multi-step tasks, planning/design decisions, multi-agent coordination

**Use Cases:**
- Complex multi-step tasks requiring coordination
- Tasks needing multiple specialized agents
- Main agent context minimization

**Capabilities:**
- Claude Code features (Plan Mode, TodoWrite)
- **Direct use of Claude Code agents** (Explore, Plan, general-purpose)
- **Report NDF sub-agents to Main Agent** (Main Agent calls them)
- Parallel/sequential execution planning
- **Save plans/research to project files** (for session recovery)
- Progress tracking and reporting

**Task Scale Handling:**
| Scale | Characteristics | Director's Approach |
|-------|-----------------|---------------------|
| Small | Single file, clear change | Direct execution with MCP tools |
| Medium | Multiple files, multiple steps | TodoWrite + report to Main Agent |
| Large | Design decisions needed | Plan Mode → save to file → staged reports |

**File Output (Required for Medium/Large tasks):**
- Plans saved to `issues/`, `docs/research/`, or `specs/`
- Enables recovery if Claude Code stops mid-task

**Example:**
```
User: "Add authentication feature with security review"

Main Agent: Complex multi-step task -> delegate to ndf:director

Task(
  subagent_type="ndf:director",
  prompt="Add JWT authentication feature. Research best practices, implement auth endpoints, and perform security review.",
  description="Implement auth with review"
)
```

Director reports to Main Agent:
```
調査・計画が完了しました。以下のサブエージェントが必要です：

1. ndf:researcher - AWS認証ベストプラクティス調査
2. ndf:corder - JWT認証実装
3. ndf:qa - セキュリティレビュー

実行順序: 順次実行（各タスクが前のタスクに依存）

Main Agentは上記順序でエージェントを起動してください。
```

#### 2. @data-analyst - Data Analysis Expert

**Use proactively for:** SQL queries, BigQuery operations, data analysis, statistics, data export (CSV/JSON/Excel)

**Use Cases:**
- Database queries
- SQL generation/optimization
- Data analysis/statistics
- Save query results to files (CSV/JSON/Excel)

**MCP Tools:** BigQuery MCP, DBHub MCP

**Example:**
```
Task(
  subagent_type="ndf:data-analyst",
  prompt="Analyze last month's sales data in BigQuery and extract top 10 products.",
  description="Analyze sales data"
)
```

#### 3. @corder - Coding Expert

**Use proactively for:** code implementation, refactoring, code review, design patterns, writing new features

**Use Cases:**
- Writing new code
- Refactoring existing code
- Code review/security check
- Applying design patterns/architecture

**MCP Tools:** Codex CLI MCP

**Example:**
```
Task(
  subagent_type="ndf:corder",
  prompt="Implement JWT authentication with login/logout/token refresh endpoints.",
  description="Implement JWT auth"
)
```

#### 4. @researcher - Research Expert

**Use proactively for:** AWS documentation research, technical investigation, web scraping, best practices research, external API documentation

**Use Cases:**
- Research AWS official documentation
- Collect information from websites
- Investigate technical specifications/best practices

**MCP Tools:** WebFetch tool (priority), AWS Documentation MCP, Chrome DevTools MCP

**Example:**
```
Task(
  subagent_type="ndf:researcher",
  prompt="Research AWS Lambda best practices for performance and security.",
  description="Research Lambda practices"
)
```

#### 5. @scanner - File Reading Expert

**Use proactively for:** reading PDF files, image OCR, PowerPoint/Excel/Word file extraction, document summarization

**Use Cases:**
- Reading PDF files
- Extracting text from images (OCR)
- Reading PowerPoint/Excel files

**MCP Tools:** Codex CLI MCP

**Example:**
```
Task(
  subagent_type="ndf:scanner",
  prompt="Read /path/to/document.pdf and summarize key points.",
  description="Read and summarize PDF"
)
```

#### 6. @qa - Quality Assurance Expert

**Use proactively for:** security review (OWASP Top 10), code quality review, performance testing, test coverage analysis

**Use Cases:**
- Code quality review
- Security vulnerability check
- Web application performance measurement

**MCP Tools:** WebFetch tool (priority), Codex CLI MCP, Chrome DevTools MCP

**Example:**
```
Task(
  subagent_type="ndf:qa",
  prompt="Review src/auth.js for security (OWASP Top 10) and code quality.",
  description="Security and quality review"
)
```

## Task Classification

**Quick Decision Flow for Main Agent:**

| Task Type | Action |
|-----------|--------|
| **Complex multi-step task** | Delegate to `ndf:director` (recommended) |
| **Simple data analysis/SQL** | Delegate to `ndf:data-analyst` |
| **Simple coding task** | Delegate to `ndf:corder` |
| **Simple research task** | Delegate to `ndf:researcher` |
| **File reading (PDF/images)** | Delegate to `ndf:scanner` |
| **Simple quality review** | Delegate to `ndf:qa` |

## Multi-Agent Collaboration

For complex tasks requiring multiple agents, **delegate to director**.

**Architecture:**
```
User Request
    ↓
Main Agent → ndf:director (planning & analysis)
    ↓
Director reports required agents to Main Agent
    ↓
Main Agent calls sub-agents (based on director's report)
    ↓
Director integrates results → User
```

**Example: Complex Feature Implementation**
```
User: "Add dashboard feature with BigQuery data and performance metrics"

1. Main Agent -> ndf:director

2. Director:
   - Explores codebase
   - Creates plan (saves to issues/i002.md)
   - Reports to Main Agent:
     "以下のエージェントが必要です:
      - ndf:data-analyst (BigQueryクエリ設計)
      - ndf:corder (UI実装)
      - ndf:qa (コード品質レビュー)
      並列実行可能: data-analyst と corder"

3. Main Agent calls sub-agents based on report

4. Director integrates results and reports to user
```

## Best Practices

### DO (Recommended)

- **Delegate complex multi-step tasks to director**
- **Use specialized agents for simple domain-specific tasks**
- **Let director handle multi-agent coordination**
- **Trust director to choose appropriate execution strategy**

### DON'T (Not Recommended)

- **Manually coordinate multiple agents when director can do it**
- **Skip director for tasks requiring planning**
- **Handle specialized tasks directly in main agent**
- **Try to process PDFs/images without scanner**

## Available MCP Tools (Reference)

**Built-in Tools:**
- **WebFetch**: Fast web content retrieval, HTML to Markdown conversion

**Official Plugins (install separately):**
- **GitHub MCP**: `/plugin install github@anthropics/claude-plugins-official`
- **Serena MCP**: `/plugin install serena@anthropics/claude-plugins-official`
- **Context7 MCP**: `/plugin install context7@anthropics/claude-plugins-official`

**NDF Plugin MCPs:**
- **Codex CLI MCP**: -> Delegate to @corder or @scanner
- **BigQuery MCP**: -> Delegate to @data-analyst
- **AWS Docs MCP**: -> Delegate to @researcher
- **Chrome DevTools MCP**: -> Delegate to @researcher or @qa

## Summary

**Main Agent Role:**
- Receive user requests
- **Delegate complex tasks to director** (context minimization)
- Delegate simple domain-specific tasks directly to specialized agents
- **Call sub-agents based on director's report** (for complex tasks)
- Pass through final results to user

**Director Role (NEW):**
- **Orchestrate complex multi-step tasks**
- **Report required sub-agents to Main Agent** (does NOT call directly)
- Use Plan Mode for large tasks
- **Save plans/research to project files** (for session recovery)
- Coordinate parallel/sequential execution planning
- Track progress with TodoWrite

**Specialized Sub-Agent Roles:**
- High-quality execution in specialized domains
- Effective use of specialized MCP tools
- **Cannot call other sub-agents**

**Architecture:**
```
Main Agent
    ├── Simple task → Specialized Agent (direct)
    └── Complex task → Director → Report → Main Agent → Specialized Agents
```

**Why This Architecture:**
- **Prevents memory errors** (no agent-to-agent direct calls)
- **Enables session recovery** (plans saved to files)
- **Main Agent controls sub-agent execution** (based on director's report)

**Success Key:**
For complex tasks, **delegate to director**. Director leverages Claude Code built-in features (Plan Mode, Explore Agent), saves plans to project files for recovery, and reports to Main Agent which sub-agents are needed.
<!-- NDF_PLUGIN_GUIDE_END_8k3jf9s2n4m5p7q1w6e8r0t2y4u6i8o -->
