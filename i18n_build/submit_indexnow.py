#!/usr/bin/env python3
"""Notify IndexNow of specific public URLs after deployment."""

import argparse
import json
from pathlib import Path
import re
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

HOST = "fjsanfan.com"
BASE = f"https://{HOST}"
ENDPOINT = "https://api.indexnow.org/indexnow"
DEFAULT_KEY_FILE = Path(__file__).with_name(".indexnow_key")


def public_url(value):
    """Accept an absolute site path or an HTTPS URL on the canonical host."""
    if any(char.isspace() or ord(char) < 32 for char in value) or "\\" in value:
        raise argparse.ArgumentTypeError(f"无效 URL：{value!r}")
    try:
        parts = urlsplit(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"无效 URL：{value!r}") from error
    same_host = parts.scheme == "https" and parts.netloc == HOST
    site_path = not parts.scheme and not parts.netloc and value.startswith("/") and not value.startswith("//")
    if not (same_host or site_path) or "?" in value or "#" in value:
        raise argparse.ArgumentTypeError(f"请填写本站主域 URL 或绝对路径：{value!r}")
    path = quote(parts.path or "/", safe="/%:@!$&'()*+,;=-._~")
    return BASE + path


def submit(urls, key_file):
    key = key_file.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[A-Za-z0-9-]{8,128}", key):
        raise ValueError("IndexNow 验证值格式无效")
    key_location = f"{BASE}/{key}.txt"
    with urlopen(key_location, timeout=15) as response:
        if response.geturl() != key_location or response.read().decode("utf-8").strip() != key:
            raise ValueError("主域上的 IndexNow 验证文件未直接返回预期内容")

    payload = {"host": HOST, "key": key, "keyLocation": key_location, "urlList": urls}
    request = Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urlopen(request, timeout=30) as response:
        return response.status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", type=public_url, help="已上线新增、更新或删除的规范 URL")
    parser.add_argument("--key-file", type=Path, default=DEFAULT_KEY_FILE, help="本地 IndexNow 验证文件")
    parser.add_argument("--dry-run", action="store_true", help="离线查看去重后的提交清单")
    args = parser.parse_args()
    urls = list(dict.fromkeys(args.urls))
    if len(urls) > 10_000:
        parser.error("每批最多 10,000 条 URL")

    print(f"IndexNow URL 数：{len(urls)}")
    if args.dry_run:
        print("\n".join(urls))
        return 0

    try:
        code = submit(urls, args.key_file)
    except (OSError, ValueError) as error:
        print(f"IndexNow 未完成：{error}")
        return 1
    print(f"IndexNow HTTP {code}，请在站长工具查看后续状态")
    return 0 if code in (200, 202) else 1


if __name__ == "__main__":
    raise SystemExit(main())
