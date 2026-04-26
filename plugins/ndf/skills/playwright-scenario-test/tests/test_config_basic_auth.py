"""scenario_test/config.py の Maj-4 fail-fast 検証 + Maj-10 tolerated_console_errors。

`requires_basic_auth=True` なロール宣言のときに `target.basic_auth.user` が空ならば
Config.load 時点で ValueError を投げることを確認する。
"""

from __future__ import annotations

import pytest

from scenario_test.config import Config


_BASE_RAW = {
    "target": {
        "base_url": "https://example.com",
    },
    "roles": {
        "user": {
            "label": "user",
            "login": {
                "path": "/login",
                "requires_basic_auth": False,
                "fields": {"username": "u", "password": "p"},
                "fail_if_url_contains": "/login",
            },
        },
    },
}


def _from_dict(raw: dict) -> Config:
    from pathlib import Path
    return Config._from_dict(raw, config_path=Path("/tmp/_test.yaml"))


def test_no_basic_auth_when_not_required_passes():
    cfg = _from_dict(_BASE_RAW)
    assert cfg.basic_auth.user == ""
    assert not cfg.roles["user"].login.requires_basic_auth


def test_requires_basic_auth_with_empty_user_raises():
    raw = {
        **_BASE_RAW,
        "roles": {
            "admin": {
                "label": "admin",
                "login": {
                    "path": "/admin/login",
                    "requires_basic_auth": True,
                    "fields": {"username": "u", "password": "p"},
                    "fail_if_url_contains": "/login",
                },
            },
        },
    }
    with pytest.raises(ValueError, match="requires_basic_auth"):
        _from_dict(raw)


def test_requires_basic_auth_with_user_passes():
    raw = {
        "target": {
            "base_url": "https://example.com",
            "basic_auth": {"user": "stage", "password": "secret"},
        },
        "roles": {
            "admin": {
                "label": "admin",
                "login": {
                    "path": "/admin/login",
                    "requires_basic_auth": True,
                    "fields": {"username": "u", "password": "p"},
                    "fail_if_url_contains": "/login",
                },
            },
        },
    }
    cfg = _from_dict(raw)
    assert cfg.basic_auth.user == "stage"


def test_tolerated_patterns_default_empty():
    cfg = _from_dict(_BASE_RAW)
    assert cfg.tolerated_console_errors == []
    assert cfg.tolerated_page_errors == []


def test_tolerated_patterns_loaded():
    raw = {
        **_BASE_RAW,
        "tolerated_console_errors": [r"favicon\.ico", "ResizeObserver loop limit"],
        "tolerated_page_errors": ["ChunkLoadError"],
    }
    cfg = _from_dict(raw)
    assert cfg.tolerated_console_errors == [
        r"favicon\.ico",
        "ResizeObserver loop limit",
    ]
    assert cfg.tolerated_page_errors == ["ChunkLoadError"]
