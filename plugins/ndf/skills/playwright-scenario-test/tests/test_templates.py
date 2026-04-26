"""templates/*.yaml.template が placeholder 置換後に valid YAML となることを検証する (Maj-9)。

テンプレに登場する placeholder (`{role}` `{slug}` `{id}` 等) を stub 値に str.format で
置換し、yaml.safe_load が成功することを確認する。
これにより、テンプレ編集時の YAML 構文ミス (インデント崩れ・コロン忘れ等) が CI で
検出可能になる。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

_SKILL_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATES_DIR = _SKILL_ROOT / "templates"

# 既知 placeholder の stub 値。新規 placeholder を導入した場合は明示登録する。
# str.format ではなく re.sub で「ASCII 識別子のみ」を置換するので、コメント中の
# 日本語 placeholder ({変数名} 等) はそのまま残る (YAML 上はコメントなので無害)。
_PLACEHOLDERS: dict[str, str] = {
    "role": "user",
    "slug": "demo",
    "id": "stub-id-001",
    "first_id": "stub-first-001",
    "item_id": "stub-item-001",
    "image_id": "stub-image-001",
    "var": "stub_var",
}

_ASCII_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _render(raw: str) -> tuple[str, list[str]]:
    """ASCII placeholder のみ既知値で置換し、未登録の placeholder は missing として返す。"""
    missing: list[str] = []

    def sub(m: re.Match) -> str:
        name = m.group(1)
        if name in _PLACEHOLDERS:
            return _PLACEHOLDERS[name]
        missing.append(name)
        return m.group(0)

    return _ASCII_PLACEHOLDER_RE.sub(sub, raw), missing


def _template_files() -> list[Path]:
    return sorted(_TEMPLATES_DIR.glob("testcase-*.yaml.template"))


@pytest.mark.parametrize(
    "tpl_path",
    _template_files(),
    ids=lambda p: p.name,
)
def test_template_safe_load(tpl_path: Path):
    raw = tpl_path.read_text(encoding="utf-8")
    rendered, missing = _render(raw)
    if missing:
        pytest.fail(
            f"{tpl_path.name}: 未登録 placeholder {sorted(set(missing))} を使用 — "
            "tests/test_templates.py の _PLACEHOLDERS に追加してください。"
        )
    try:
        loaded = yaml.safe_load(rendered)
    except yaml.YAMLError as exc:
        pytest.fail(f"{tpl_path.name}: YAML parse error: {exc}")
    # 最低限、testcase の必須キー (id / type) が存在すること
    assert isinstance(loaded, dict), f"{tpl_path.name}: トップが dict でない"
    assert "id" in loaded, f"{tpl_path.name}: id 欠如"
    assert "type" in loaded, f"{tpl_path.name}: type 欠如"


def test_config_example_safe_load():
    """templates/config.example.yaml も valid YAML であることを確認 (Maj-9 補強)。"""
    cfg_path = _TEMPLATES_DIR / "config.example.yaml"
    loaded = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    # 必須トップキー
    assert "target" in loaded
    assert "roles" in loaded
