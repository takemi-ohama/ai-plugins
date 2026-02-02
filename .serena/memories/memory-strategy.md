# Memory Strategy for AI Agent
type: policy
confidence: high
project: global
expires: none
review_after_commits: none
created_at: 2026-02-02
status: active

---

## Purpose

This memory defines **how mid-term and long-term memories are structured,
classified, and maintained** across projects.

It is the single source of truth for deciding:
- what belongs in memory
- what belongs in skills
- how memories evolve over time

---

## Memory Layer Definitions

### Short-term Memory
- Exists only within a session
- Not persisted
- Used for immediate task context

---

### Mid-term Memory
- Valid for weeks to months (or 10-30 commits)
- Represents temporary or revisitable decisions
- Must include a review condition (commit-based)

Typical contents:
- phase-specific decisions
- PoC constraints
- experimental results
- temporary architectural choices

Required metadata:
- type: decision | assumption | experiment
- confidence: low | medium | high
- review_after_commits: N (10-30 recommended)
- last_reviewed_commit: <hash>
- project: <project-name>

**Commit-based Review:**
- confidence: low → 10 commits
- confidence: medium → 20 commits
- confidence: high → 30 commits

---

### Long-term Memory
- Stable across the project lifecycle
- Represents principles and non-negotiable constraints

Typical contents:
- architectural principles
- legal / IP constraints
- organizational policies
- technology philosophy

Required metadata:
- type: principle | constraint | policy
- confidence: high
- expires: none
- review_after_commits: none
- project: <project-name or global>

---

## Skill vs Memory Decision Checklist

If any of the following are true, the information must be stored as memory:

- it will be reused in future sessions
- it is project-specific
- it explains *why*, not *how*
- it restricts future choices
- it may need revision or expiration
- it would bloat an agent skill

Otherwise, it belongs in a skill or remains transient.

---

## Memory Granularity Rules

- One memory entry = one decision or principle
- Do not mix facts, assumptions, and conclusions
- Prefer clarity over completeness
- Avoid embedding procedures

---

## Memory Maintenance Policy

- Mid-term memories must be reviewed based on commit count
- Use `/ndf:mem-review` to check for overdue reviews
- Obsolete memories should be archived or deleted
- Long-term memories should rarely change and must be updated carefully

---

## Anti-Patterns

- Storing procedures in memory
- Encoding decisions inside skills
- Creating duplicate memories for similar topics
- Leaving experimental assumptions unreviewed
- Using date-based review (use commit-based instead)

---

## Commit-based Review Strategy

**Why commit-based?**
- Aligns with actual development activity
- Active periods → frequent reviews
- Inactive periods → no wasted reviews
- Automatic adjustment to project pace

**How it works:**
1. Memory stores: `review_after_commits: 20`
2. Memory stores: `last_reviewed_commit: abc123`
3. On review: Calculate `git rev-list --count abc123..HEAD`
4. If count >= 20, review is due

**Tools:**
- `/ndf:mem-review` - Check and review due memories
- `/ndf:mem-capture` - Capture new memories with commit-based review

---

## One-line Rule

> Skills describe behavior.
> Memory defines reality.
