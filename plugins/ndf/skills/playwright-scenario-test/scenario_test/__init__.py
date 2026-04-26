"""pytest-playwright 上で動く Web E2E シナリオテストパッケージ。

利用方法:
- pytest plugin として ``--ndf-config=...`` で読み込む (entry-point 経由で auto-load)
- ``ndf_config`` / ``ndf_role_<id>`` / ``ndf_evidence`` 等の fixture を test に注入
- ``@pytest.mark.page_role(...)`` で a11y / CWV を autouse

詳細は SKILL.md を参照。
"""

__version__ = "0.3.0"
