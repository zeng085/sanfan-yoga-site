#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IndexNow 主动推送：把 sitemap 里的全部 URL 提交给 Bing / Yandex / Naver / Seznam。
（Bing 的索引会供 ChatGPT 等 AI 搜索使用，对 GEO 目标价值高。）

用法:
  python3 submit_indexnow.py              # 从线上 sitemap 取 URL 并提交
  python3 submit_indexnow.py --dry-run    # 只打印不提交
"""
import os, re, sys, json, time
import urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".indexnow_key")
SITEMAP = "https://fjsanfan.com/sitemap.xml"
HOST = "fjsanfan.com"
ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://search.seznam.cz/indexnow",
    "https://yandex.com/indexnow",
]

_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": _proxy, "https": _proxy})) \
    if _proxy else urllib.request.build_opener()


def get_urls():
    raw = _opener.open(SITEMAP, timeout=30).read().decode("utf-8")
    urls = re.findall(r"<loc>(.*?)</loc>", raw)
    # 去重保序，只保留本站
    seen, out = set(), []
    for u in urls:
        u = u.strip()
        if u.startswith("https://" + HOST) and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def submit(urls, key):
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": "https://%s/%s.txt" % (HOST, key),
        "urlList": urls,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    results = []
    for ep in ENDPOINTS:
        req = urllib.request.Request(ep, data=data,
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        try:
            r = _opener.open(req, timeout=40)
            results.append((ep, r.status, "OK"))
        except urllib.error.HTTPError as e:
            results.append((ep, e.code, (e.read().decode()[:80] or e.reason)))
        except Exception as e:
            results.append((ep, "-", "%s: %s" % (type(e).__name__, str(e)[:60])))
    return results


def main():
    dry = "--dry-run" in sys.argv
    if not os.path.exists(KEY_FILE):
        print("缺少 key 文件:", KEY_FILE)
        return 1
    key = open(KEY_FILE).read().strip()
    urls = get_urls()
    print("sitemap URL 数: %d" % len(urls))
    for lg in ("de", "ja", "ko"):
        n = sum(1 for u in urls if "/" + lg + "/" in u)
        print("  %s: %d 条" % (lg.upper(), n))
    if dry:
        for u in urls[:8]:
            print("  ", u)
        print("  ...(dry-run，未提交)")
        return 0
    # 确认 key 文件已线上可访问（IndexNow 会校验）
    try:
        r = _opener.open("https://%s/%s.txt" % (HOST, key), timeout=25)
        body = r.read().decode().strip()
        if body != key:
            print("!! key 文件内容不匹配，放弃提交（线上='%s'）" % body[:40])
            return 1
        print("key 文件校验通过: https://%s/%s.txt" % (HOST, key))
    except Exception as e:
        print("!! key 文件不可访问(%s)，请先部署后重试" % str(e)[:60])
        return 1
    print("\n提交中...")
    for ep, code, msg in submit(urls, key):
        print("  [%s] %s -> %s" % (code, ep, msg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
