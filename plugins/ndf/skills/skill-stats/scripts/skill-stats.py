#!/usr/bin/env python3
"""NDF skill usage statistics from Claude Code transcripts.

Scans ~/.claude/projects/**/*.jsonl and counts, for each NDF skill:
  - invocations: tool_use where name="Skill" and input.skill="ndf:<name>"
  - triggers:    user messages whose text contains keywords from the skill's
                 description / "Triggers:" line
  - hits:        user messages that (a) matched a trigger AND (b) were followed
                 by an invocation of the same skill before the next user turn
  - hit_rate:    hits / triggers (percent)
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from collections import Counter
from datetime import datetime, timedelta
from typing import Iterable


def plugin_root_default() -> pathlib.Path:
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return pathlib.Path(env)
    # scripts/skill-stats.py -> plugins/ndf/skills/skill-stats/scripts/
    return pathlib.Path(__file__).resolve().parents[3]


def iter_transcripts(days: int) -> Iterable[pathlib.Path]:
    root = pathlib.Path.home() / ".claude" / "projects"
    if not root.exists():
        return
    cutoff = datetime.now() - timedelta(days=days)
    for p in root.rglob("*.jsonl"):
        try:
            mtime = datetime.fromtimestamp(p.stat().st_mtime)
        except OSError:
            continue
        if mtime >= cutoff:
            yield p


def iter_events(path: pathlib.Path) -> Iterable[dict]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_QUOTED_RE = re.compile(r"['\"]([^'\"]+)['\"]")
_JA_WORD_RE = re.compile(r"[一-龥ぁ-んァ-ヶー]{2,}|[A-Za-z][A-Za-z0-9_-]{2,}")
_STOPWORDS = {
    "true", "false", "null", "none", "when", "triggers", "trigger",
    "description", "use", "used", "using",
}


def parse_front_matter(text: str) -> dict[str, str]:
    m = _FRONT_MATTER_RE.match(text)
    if not m:
        return {}
    fm = m.group(1)
    out: dict[str, str] = {}
    key = None
    buf: list[str] = []
    for line in fm.splitlines():
        if re.match(r"^[A-Za-z_-]+:\s*", line):
            if key is not None:
                out[key] = "\n".join(buf).strip()
            k, _, v = line.partition(":")
            key = k.strip()
            buf = [v.strip()]
        else:
            buf.append(line)
    if key is not None:
        out[key] = "\n".join(buf).strip()
    return out


def extract_triggers(description: str, include_fallback: bool = False) -> tuple[list[str], str]:
    """Extract trigger keywords from a skill description.

    Returns (triggers, source) where source is one of:
      - "explicit":  from a "Triggers: '...', '...'" line (precise)
      - "fallback":  from Japanese/English words in the description (noisy)
      - "none":      no explicit triggers and fallback disabled
    """
    triggers: list[str] = []
    m = re.search(r"Triggers?:\s*(.+)", description, re.IGNORECASE | re.DOTALL)
    if m:
        for q in _QUOTED_RE.findall(m.group(1)):
            triggers.append(q.strip())
    if triggers:
        return _dedupe_ci(triggers), "explicit"
    if not include_fallback:
        return [], "none"
    flat = description.replace('"', " ").replace("'", " ")
    seen: set[str] = set()
    for w in _JA_WORD_RE.findall(flat):
        w = w.strip()
        if not w or w.lower() in _STOPWORDS:
            continue
        if len(w) < 3:
            continue
        if w not in seen:
            seen.add(w)
            triggers.append(w)
        if len(triggers) >= 10:
            break
    return _dedupe_ci(triggers), "fallback"


def _dedupe_ci(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for t in items:
        tl = t.lower()
        if tl in seen:
            continue
        seen.add(tl)
        out.append(t)
    return out


def load_skills(plugin_root: pathlib.Path, include_fallback: bool = False) -> list[dict]:
    out: list[dict] = []
    skills_dir = plugin_root / "skills"
    if not skills_dir.is_dir():
        return out
    for d in sorted(skills_dir.iterdir()):
        if not d.is_dir():
            continue
        f = d / "SKILL.md"
        if not f.exists():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        fm = parse_front_matter(text)
        name = fm.get("name", d.name).strip().strip('"')
        desc = fm.get("description", "").strip().strip('"')
        triggers, source = extract_triggers(desc, include_fallback=include_fallback)
        out.append({
            "name": name,
            "qualified": f"ndf:{name}",
            "triggers": triggers,
            "triggers_source": source,
            "dir": d.name,
        })
    return out


_SYSTEM_TAG_RE = re.compile(r"^\s*<(local-command|command-name|command-message|command-args|system-reminder)")


def extract_user_text(ev: dict) -> str:
    if ev.get("type") != "user":
        return ""
    msg = ev.get("message") or {}
    c = msg.get("content")
    if isinstance(c, str):
        if _SYSTEM_TAG_RE.match(c):
            return ""
        return c
    if isinstance(c, list):
        parts: list[str] = []
        for b in c:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text":
                t = b.get("text", "")
                if t and not _SYSTEM_TAG_RE.match(t):
                    parts.append(t)
        return "\n".join(parts)
    return ""


def extract_skill_invocations(ev: dict) -> list[str]:
    """Return list of 'ndf:<name>' skill names invoked by this assistant turn."""
    if ev.get("type") != "assistant":
        return []
    msg = ev.get("message") or {}
    content = msg.get("content") or []
    invoked: list[str] = []
    for c in content:
        if not isinstance(c, dict):
            continue
        if c.get("type") != "tool_use":
            continue
        if c.get("name") != "Skill":
            continue
        inp = c.get("input") or {}
        skill = inp.get("skill") or inp.get("name") or ""
        if skill:
            invoked.append(skill)
    return invoked


def build_timeline(path: pathlib.Path) -> list[tuple[str, object]]:
    timeline: list[tuple[str, object]] = []
    for ev in iter_events(path):
        t = ev.get("type")
        if t == "user":
            text = extract_user_text(ev)
            if text:
                timeline.append(("user", text))
        elif t == "assistant":
            for skill in extract_skill_invocations(ev):
                timeline.append(("skill", skill))
    return timeline


def aggregate(
    transcripts: list[pathlib.Path],
    skills: list[dict],
    lookahead_cap: int = 100,
) -> tuple[Counter, Counter, Counter]:
    invocations: Counter = Counter()
    triggers_hits: Counter = Counter()
    hits: Counter = Counter()

    # pre-lower triggers for fast matching
    skill_triggers = [
        (s["qualified"], [t.lower() for t in s["triggers"] if t])
        for s in skills
    ]

    for path in transcripts:
        tl = build_timeline(path)
        for i, (kind, data) in enumerate(tl):
            if kind == "skill":
                invocations[data] += 1
                continue
            if kind != "user":
                continue
            text_l = str(data).lower()
            for qualified, trs in skill_triggers:
                if not trs:
                    continue
                if any(t in text_l for t in trs):
                    triggers_hits[qualified] += 1
                    # lookahead: next user message breaks the window
                    end = min(i + 1 + lookahead_cap, len(tl))
                    for j in range(i + 1, end):
                        k2, d2 = tl[j]
                        if k2 == "user":
                            break
                        if k2 == "skill" and d2 == qualified:
                            hits[qualified] += 1
                            break
    return invocations, triggers_hits, hits


def format_markdown(rows: list[dict], total: dict) -> str:
    lines = [
        "| skill | triggers源 | 呼び出し数 | 関連話題 | ヒット | ヒット率 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        src = r["triggers_source"]
        if src == "none":
            rate = "-"
            trig = "-"
            hit = "-"
        else:
            rate = f"{r['hit_rate_pct']}%" if r["triggers"] else "-"
            trig = str(r["triggers"])
            hit = str(r["hits"])
        lines.append(
            f"| {r['skill']} | {src} | {r['invocations']} | {trig} | {hit} | {rate} |"
        )
    lines.append(
        f"| **合計** | | **{total['invocations']}** | **{total['triggers']}** | **{total['hits']}** | **{total['hit_rate_pct']}%** |"
    )
    return "\n".join(lines)


def build_rows(
    skills: list[dict],
    invocations: Counter,
    triggers_hits: Counter,
    hits: Counter,
) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    total_inv = total_trig = total_hit = 0
    for s in sorted(skills, key=lambda x: x["name"]):
        q = s["qualified"]
        inv = invocations.get(q, 0)
        trig = triggers_hits.get(q, 0)
        hit = hits.get(q, 0)
        rate = round(hit / trig * 100, 1) if trig else 0.0
        rows.append({
            "skill": q,
            "triggers_source": s["triggers_source"],
            "invocations": inv,
            "triggers": trig,
            "hits": hit,
            "hit_rate_pct": rate,
            "trigger_keywords": s["triggers"],
        })
        total_inv += inv
        # totalは explicit triggers を持つ skill のみ加算 (fallback はノイズが多いので除外)
        if s["triggers_source"] == "explicit":
            total_trig += trig
            total_hit += hit
    total_rate = round(total_hit / total_trig * 100, 1) if total_trig else 0.0
    total = {
        "invocations": total_inv,
        "triggers": total_trig,
        "hits": total_hit,
        "hit_rate_pct": total_rate,
    }
    return rows, total


def main() -> int:
    ap = argparse.ArgumentParser(
        description="NDF skill usage statistics from Claude Code transcripts",
    )
    ap.add_argument("--days", type=int, default=90,
                    help="集計対象の遡及日数 (default: 90)")
    ap.add_argument("--plugin-root", default=None,
                    help="NDFプラグインのルート (default: 自動検出)")
    ap.add_argument("--format", choices=["md", "json"], default="md",
                    help="出力形式 (default: md)")
    ap.add_argument("--skill", default=None,
                    help="skill名(部分一致)でフィルタ")
    ap.add_argument("--show-keywords", action="store_true",
                    help="各skillに抽出されたトリガーキーワードを出力")
    ap.add_argument("--include-fallback", action="store_true",
                    help="Triggers欄が無いskillでも description 全体から語彙抽出してマッチ(ノイズ多)")
    args = ap.parse_args()

    plugin_root = pathlib.Path(args.plugin_root) if args.plugin_root else plugin_root_default()
    if not (plugin_root / "skills").is_dir():
        print(f"[skill-stats] plugin root not found: {plugin_root}", file=sys.stderr)
        return 2

    skills = load_skills(plugin_root, include_fallback=args.include_fallback)
    if args.skill:
        skills = [s for s in skills if args.skill in s["name"]]

    transcripts = list(iter_transcripts(args.days))
    print(
        f"# NDF Skill 使用統計 (過去{args.days}日 / transcript {len(transcripts)}件 / plugin {plugin_root})",
        file=sys.stderr,
    )

    invocations, triggers_hits, hits = aggregate(transcripts, skills)
    rows, total = build_rows(skills, invocations, triggers_hits, hits)

    if args.format == "json":
        out = {
            "meta": {
                "days": args.days,
                "transcripts": len(transcripts),
                "plugin_root": str(plugin_root),
            },
            "total": total,
            "skills": rows,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(rows, total))
        if args.show_keywords:
            print("\n## 抽出トリガーキーワード")
            for r in rows:
                kw = ", ".join(r["trigger_keywords"]) or "-"
                print(f"- `{r['skill']}`: {kw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
