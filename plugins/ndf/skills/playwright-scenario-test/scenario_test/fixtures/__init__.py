"""playwright-scenario-test pytest fixtures。

利用者は通常の pytest テストを書き、`ndf_config` / `ndf_role_<id>` 等の
fixture をパラメタ宣言するだけで NDF の機能 (config / 認証 / evidence /
a11y / CWV / HUD / Drive) を享受できる。

各 fixture の実体はサブモジュールに分離する:
- ``auth``     : ``ndf_config`` / ``ndf_role_<id>`` (login 済 storage_state)
- ``evidence`` : ``ndf_evidence`` (HAR / trace / console listeners)
- ``a11y``     : autouse hook で page_role marker に応じ axe-core
- ``cwv``      : autouse hook で page_role marker に応じ CWV 計測

pytest plugin (``scenario_test.pytest_plugin``) から ``pytest_plugins`` で
読み込まれる想定。利用者プロジェクトの ``conftest.py`` で個別 import する必要は無い。
"""

from __future__ import annotations

__all__ = ["auth"]
