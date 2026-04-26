"""tests/ から scripts/ と scenario_test/ の両方を import 可能にする path 設定。

scenario_test は scripts/ にディレクトリされていないので import 可能だが、
scripts/generate_test_plan.py は package ではないため sys.path 追加が必要。

v0.3.0+: pytest plugin の自己テスト用に ``pytester`` を有効化する。
"""

from __future__ import annotations

import sys
from pathlib import Path

# ``pytester`` fixture (test 内で別 pytest を実行するためのサンドボックス) を有効化。
# scenario_test.pytest_plugin の addoption / markers / fixture 動的登録を
# 隔離環境で検証するために使う。
pytest_plugins = ["pytester"]

_SKILL_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _SKILL_ROOT / "scripts"

for p in (str(_SKILL_ROOT), str(_SCRIPTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)
