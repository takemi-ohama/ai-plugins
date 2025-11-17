<!-- NDF_PLUGIN_GUIDE_START_8k3jf9s2n4m5p7q1w6e8r0t2y4u6i8o -->
<!-- VERSION: 1 -->
# NDF Plugin - AI Agent Guidelines (Mini)

## Overview

NDF plugin provides **10 MCP servers, 6 commands, and 5 specialized sub-agents**. Delegate complex tasks to appropriate sub-agents for better results.

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
- **TodoList management**: Track overall task progress
- **Result integration**: Consolidate results from sub-agents
- **Task distribution**: Delegate to appropriate sub-agents

**Core Principle:**
- Delegate complex/specialized tasks to sub-agents
- Main agent handles only simple coordination
- Use specialized agents for data analysis, coding, research, file reading, QA

### 3. Serena MCP Usage

**Use Serena MCP actively** for efficient code exploration and editing.

#### Key Commands

**Read code progressively (not entire files):**
```bash
# 1. Get symbol overview first
mcp__plugin_ndf_serena__get_symbols_overview relative_path="path/to/file.py"

# 2. Find specific symbol
mcp__plugin_ndf_serena__find_symbol name_path="/ClassName" relative_path="src/" include_body=true

# 3. Search pattern if symbol name unknown
mcp__plugin_ndf_serena__search_for_pattern substring_pattern="TODO" relative_path="src/"
```

**Edit code safely:**
```bash
# Replace symbol body (preferred)
mcp__plugin_ndf_serena__replace_symbol_body name_path="/function_name" relative_path="file.py" body="new code"

# Rename across codebase
mcp__plugin_ndf_serena__rename_symbol name_path="/OldName" relative_path="file.py" new_name="NewName"

# Find all references
mcp__plugin_ndf_serena__find_referencing_symbols name_path="function_name" relative_path="source.py"
```

**Use memories:**
```bash
mcp__plugin_ndf_serena__read_memory project-overview.md
mcp__plugin_ndf_serena__write_memory memory_file_name="feature.md" content="..."
```

#### Best Practices

✅ **DO**: Get symbol overview before reading files, use symbol-based editing
❌ **DON'T**: Read entire files, use for binary files (PDF/images)

### 4. Research Facts

**For technically challenging tasks, research external resources instead of guessing.**

- Cloud services (AWS, GCP) → **researcher agent** with AWS Docs MCP
- Latest libraries/frameworks → **corder agent** with Context7 MCP
- Website behavior → **researcher agent** with Chrome DevTools MCP

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

#### 1. @data-analyst - Data Analysis Expert

**Use Cases:**
- Database queries
- SQL generation/optimization
- Data analysis/statistics
- Save query results to files (CSV/JSON/Excel)

**MCP Tools:** BigQuery MCP

**Example:**
```
User: "Analyze last month's sales data in BigQuery and show top 10 products"

Main Agent: Data analysis task → delegate to ndf:data-analyst

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

**MCP Tools:** Codex CLI MCP, Serena MCP, Context7 MCP

**Example:**
```
User: "Implement user authentication feature"

Main Agent: Coding task → delegate to ndf:corder

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

**MCP Tools:** AWS Documentation MCP, Chrome DevTools MCP, Codex CLI MCP

**Example:**
```
User: "Research AWS Lambda best practices"

Main Agent: Research task → delegate to ndf:researcher

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

Main Agent: File reading task → delegate to ndf:scanner

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
- Claude Code plugin specification compliance check

**MCP Tools:** Codex CLI MCP, Serena MCP, Chrome DevTools MCP

**Examples:**
```
User: "Review this code's quality and security"

Main Agent: QA task → delegate to ndf:qa

Task(
  subagent_type="ndf:qa",
  prompt="Review src/auth.js code. Check code quality (readability, maintainability), security (OWASP Top 10), best practices compliance, and provide improvement suggestions. Perform security scan with Codex.",
  description="Code quality and security review"
)
```

```
User: "Measure web application performance"

Main Agent: Performance test task → delegate to ndf:qa

Task(
  subagent_type="ndf:qa",
  prompt="Measure performance of https://example.com. Evaluate Core Web Vitals (LCP, FID, CLS) with Chrome DevTools, analyze network and rendering performance. Include improvement suggestions if bottlenecks found.",
  description="Performance testing with Chrome DevTools"
)
```

## Task Classification

**Quick Decision Flow:**

1. **Data-related?** (SQL, database, data analysis) → `ndf:data-analyst`
2. **Coding-related?** (implementation, refactoring, review) → `ndf:corder`
3. **Research-related?** (documentation, web scraping) → `ndf:researcher`
4. **File reading?** (PDF, images, Office docs) → `ndf:scanner`
5. **QA-related?** (code review, security, performance) → `ndf:qa`
6. **Simple coordination** → Handle by main agent

## Multi-Agent Collaboration

For complex tasks, use **multiple sub-agents sequentially or in parallel**.

**Example 1: Data Analysis → Reporting**
```
User: "Analyze sales data in BigQuery and create PowerPoint report"

Steps:
1. Task(ndf:data-analyst) for data analysis
2. Main agent receives results
3. Main agent creates PowerPoint
4. Task(ndf:scanner) to verify PowerPoint creation
```

**Example 2: Research → Implementation**
```
User: "Research AWS Lambda best practices and write code based on findings"

Steps:
1. Task(ndf:researcher) to research AWS Lambda best practices
2. Main agent receives research results
3. Task(ndf:corder) to implement code based on best practices
```

**Example 3: PDF Reading → Data Analysis**
```
User: "Read sales data from PDF, import to database, and analyze"

Steps:
1. Task(ndf:scanner) to read PDF and extract data
2. Main agent verifies extracted data
3. Task(ndf:data-analyst) to import to database
4. Task(ndf:data-analyst) to perform data analysis
```

## Best Practices

### DO (Recommended)

✅ **Use specialized agents for each task type**
✅ **Decompose complex tasks and delegate to multiple agents**
✅ **Validate and integrate agent results**
✅ **Start parallel tasks simultaneously when possible**

### DON'T (Not Recommended)

❌ **Handle specialized tasks with main agent** → Delegate to sub-agents
❌ **Respond with guesses without sub-agents** → Research with appropriate agent
❌ **Implement complex code without review** → Delegate to corder with Codex review
❌ **Try to process PDFs/images directly** → Delegate to scanner

## Available MCP Tools (Reference)

Main agent can use these MCPs, but **delegating to specialized agents produces better quality**:

**Core MCPs (frequently used):**
- **Serena MCP**: Code structure understanding, symbol editing
- **GitHub MCP**: PR/issue management, code search
- **Codex CLI MCP**: → **Delegate to @corder or @scanner**
- **Context7 MCP**: Latest library documentation → **Delegate to @corder**

**Specialized MCPs (delegate to agents):**
- **BigQuery MCP**: Database queries → **Delegate to @data-analyst**
- **AWS Docs MCP**: AWS documentation → **Delegate to @researcher**
- **Chrome DevTools MCP**: Web performance/debugging → **Delegate to @researcher or @qa**

## Summary

**Main Agent Role:**
- Overall task management and coordination
- Delegation decisions
- Result integration
- Final reporting to user

**Sub-Agent Role:**
- High-quality execution in specialized domains
- Effective use of specialized MCP tools
- Detailed analysis and implementation

**Success Key:**
Don't try to handle complex tasks alone. **Delegate to appropriate sub-agents** for higher quality and more specialized results.
<!-- NDF_PLUGIN_GUIDE_END_8k3jf9s2n4m5p7q1w6e8r0t2y4u6i8o -->
