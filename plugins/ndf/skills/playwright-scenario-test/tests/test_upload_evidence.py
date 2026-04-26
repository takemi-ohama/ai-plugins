"""scripts/upload_evidence.py の純粋関数をテストする (Drive API は呼ばない)。"""

from __future__ import annotations

from pathlib import Path

from upload_evidence import detect_kind


class TestDetectKind:
    def test_zip_is_trace(self):
        assert detect_kind(Path("foo.trace.zip")) == "trace"
        assert detect_kind(Path("simple.zip")) == "trace"

    def test_har(self):
        assert detect_kind(Path("session.har")) == "har"

    def test_video(self):
        assert detect_kind(Path("recording.mp4")) == "video"
        assert detect_kind(Path("recording.webm")) == "video"

    def test_unknown_extension_falls_back_to_any(self):
        assert detect_kind(Path("unknown.bin")) == "any"
        assert detect_kind(Path("README.md")) == "any"
