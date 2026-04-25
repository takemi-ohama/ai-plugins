"""trace.zip を Google Drive にアップロードし playwright.dev の閲覧 URL を生成する。

bug report に zip 単体ではなく URL を載せると、開発者が即座に trace を開けるようになる。
docs/05-bug-report.md の「evidence」項目で必須。

Usage:
    python trace_link.py /path/to/trace.zip --parent-folder-id <DRIVE_FOLDER_ID>
    python trace_link.py reports/20260425/TC-50/trace.zip
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import quote

# google-drive スキルの sibling-skill discovery と同じパターン
_CANDIDATES = (
    os.environ.get("GOOGLE_AUTH_SCRIPTS"),
    os.path.expanduser("~/.claude/skills/google-auth/scripts"),
    str(Path(__file__).resolve().parent.parent.parent / "google-auth" / "scripts"),
)


def _ensure_google_auth_on_path() -> None:
    for p in _CANDIDATES:
        if p and os.path.isdir(p):
            if p not in sys.path:
                sys.path.insert(0, p)
            return
    raise RuntimeError(
        "google-auth スキルが見つかりません。GOOGLE_AUTH_SCRIPTS env で明示してください。"
    )


def upload_and_link(
    trace_zip: Path,
    *,
    parent_folder_id: str | None = None,
    public: bool = True,
) -> dict:
    """trace.zip をアップロードして playwright.dev URL を返す。"""
    _ensure_google_auth_on_path()
    from google_auth import get_credentials  # type: ignore  # noqa: E402
    from googleapiclient.discovery import build  # noqa: E402
    from googleapiclient.http import MediaFileUpload  # noqa: E402

    creds = get_credentials(["drive.file"])
    service = build("drive", "v3", credentials=creds)

    metadata: dict = {"name": trace_zip.name}
    if parent_folder_id:
        metadata["parents"] = [parent_folder_id]
    media = MediaFileUpload(str(trace_zip), mimetype="application/zip")
    f = service.files().create(
        body=metadata, media_body=media, fields="id,webViewLink",
    ).execute()
    file_id = f["id"]

    if public:
        service.permissions().create(
            fileId=file_id, body={"type": "anyone", "role": "reader"}
        ).execute()

    direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    viewer_url = f"https://trace.playwright.dev/?trace={quote(direct_url, safe='')}"

    return {
        "file_id": file_id,
        "drive_view": f.get("webViewLink"),
        "direct_download": direct_url,
        "playwright_trace_viewer": viewer_url,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="trace.zip を Drive アップして playwright.dev の閲覧 URL を生成"
    )
    parser.add_argument("trace_zip", type=Path, help="trace.zip のパス")
    parser.add_argument("--parent-folder-id", default=None,
                        help="Drive の親フォルダ ID (省略時はマイドライブ直下)")
    parser.add_argument("--no-public", action="store_true",
                        help="パブリック共有を付与しない (社内利用)")
    args = parser.parse_args()

    if not args.trace_zip.exists():
        print(f"ERROR: trace.zip not found: {args.trace_zip}", file=sys.stderr)
        return 2

    result = upload_and_link(
        args.trace_zip,
        parent_folder_id=args.parent_folder_id,
        public=not args.no_public,
    )

    print(f"file_id: {result['file_id']}")
    print(f"Drive: {result['drive_view']}")
    print(f"Direct: {result['direct_download']}")
    print()
    print("Playwright Trace Viewer URL (bug report に記載):")
    print(f"  {result['playwright_trace_viewer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
