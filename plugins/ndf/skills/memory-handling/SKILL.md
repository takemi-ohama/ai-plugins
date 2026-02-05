# Skill: Memory Handling Strategy

## Purpose
This skill defines **how the agent should handle memory**,
not **what should be remembered**.

All decisions, principles, and project-specific rules must be retrieved
from Serena MCP memory.

---

## Core Rules

### 1. Skill must remain thin
- Do not store project-specific rules here
- Do not store decisions, reasons, or constraints
- This skill defines behavior only

---

### 2. When to read memory
Before starting a task, check whether:
- the task depends on project-specific assumptions
- the task may conflict with past decisions
- the task requires architectural, legal, or organizational constraints

If yes:
- list available Serena memories
- read only the relevant ones

---

### 3. When to write memory
After completing a task, write to Serena memory if:
- a new decision was made
- an assumption was confirmed or invalidated
- a reusable insight emerged
- repeating this explanation later would be costly

---

### 4. What NOT to write as memory
Do NOT store:
- step-by-step procedures
- implementation details
- temporary working notes
- raw logs or dumps

---

### 5. Memory hygiene behavior
- Prefer updating existing memory over creating duplicates
- If a memory seems outdated, mark it for review
- Do not assume old memories are always valid

---

## Interaction Pattern (Summary)

1. Identify whether memory is needed
2. Read only relevant memories
3. Execute the task
4. Persist only durable knowledge back to memory

---

## Guiding Principle

> The agent acts.
> The memory decides.

---

## Japanese Summary (日本語要約)

このスキルは「記憶をどう扱うか」の行動ルールを定義します。

**基本原則**:
- Skillは薄く保つ（プロジェクト固有のルールはプロジェクトスコープに）
- 判断・前提・制約はSerena MCP Memoryから取得
- タスク開始前に関連するメモリーを読み込む
- タスク完了後に再利用価値のある知見をメモリーに保存
- 手順や実装詳細は保存しない

**使い分け**:
- **Skill**: 行動の型（やり方）
- **Memory**: 判断・前提（なぜ・何を）
