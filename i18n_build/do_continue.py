#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多语言续翻执行器（供定时任务调用）

用法:
  python3 do_continue.py                      # 调度模式：逐页开子进程，避免长驻进程被 OOM kill
  python3 do_continue.py --page <lang> <rel>  # 单页模式（由调度模式内部调用）
  python3 do_continue.py --no-push            # 不推送 GitHub

特性:
- 逐页独立进程，单页崩溃不影响整体
- 命中缓存不消耗翻译配额，配额耗尽安全停止且进度全落盘
- 未译率 <= PASS_RATE 才正式上线，否则暂存 _pending/
- 全部完成后自动更新 hreflang/sitemap 并推送 GitHub
"""
import os, sys, json, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import translator as T
import build_pages as B
import fix_cache as F
import verify as V
import update_seo as U

ROOT = F.ROOT
HERE = os.path.dirname(os.path.abspath(__file__))
LANGS = ["de", "ja", "ko"]
PASS_RATE = 8.0          # 未译率阈值(%)
PENDING = os.path.join(HERE, "_pending")


def untranslated_rate(lang, rel):
    """
    未译率：只统计「长度 >= 20 字符且非专有名词」的条目。
    短标签(FAQ/Blog/SAN/2013/100 pcs/ISO 9001/邮箱电话/品牌)保留原文是正确行为，
    计入分子会把合格页面误判为不合格。
    """
    srcs = list(dict.fromkeys([s for s in F.collect_srcs(rel, lang) if s and s.strip()]))
    checked, un = 0, 0
    for s in srcs:
        if len(s.strip()) < 20:
            continue
        if V.ADDRESS_HINT.search(s) or V.COMPANY_HINT.search(s) or V.SPEC_HINT.search(s):
            continue
        checked += 1
        v = T._cache.get(T._ck(s, lang))
        if v is None or v.strip() == s.strip():
            un += 1
    return 100.0 * un / max(1, checked), un, checked


def run_one(lang, rel):
    """处理单页 -> (status, msg)

    安全约束：已存在的页面一律 skip，**绝不重新评判或移走**。
    （曾因误判把已上线的合格页面移入 _pending，故改为只补缺失页面。）
    """
    out_path = os.path.join(ROOT, lang, rel)
    if os.path.exists(out_path):
        return "skip", "已存在"
    try:
        B.build_one(rel, lang, verbose=False)
    except SystemExit:
        T.flush()
        return "quota", ""
    except Exception as e:
        T.flush()
        return "err", str(e)[:70]
    if not os.path.exists(out_path):
        return "err", "no output"
    rate, un, tot = untranslated_rate(lang, rel)
    if rate <= PASS_RATE:
        T.flush()
        return "ok", "%.1f%% (%d/%d)" % (rate, un, tot)
    dst = os.path.join(PENDING, "%s__%s" % (lang, rel.replace("/", "__")))
    os.makedirs(PENDING, exist_ok=True)
    shutil.move(out_path, dst)
    T.flush()
    return "pending", "%.1f%% (%d/%d)" % (rate, un, tot)


def dispatch():
    """逐页子进程调度"""
    os.makedirs(PENDING, exist_ok=True)
    tally = {"ok": [], "skip": [], "pending": [], "quota": [], "err": []}
    quota_stop = False
    for lang in LANGS:
        if quota_stop:
            break
        for rel in B.PAGES:
            r = subprocess.run([sys.executable, os.path.abspath(__file__), "--page", lang, rel],
                               capture_output=True, text=True, cwd=HERE)
            raw = (r.stdout or "").strip().splitlines()
            try:
                payload = json.loads(raw[-1]) if raw else {"status": "err", "msg": "no output"}
            except Exception:
                payload = {"status": "err", "msg": (r.stderr or "crash").strip()[-70:]}
            st = payload.get("status", "err")
            tally.setdefault(st, []).append("%s/%s %s" % (lang, rel, payload.get("msg", "")))
            print("[%-7s] %s/%s %s" % (st, lang, rel, payload.get("msg", "")), flush=True)
            if st == "quota":
                quota_stop = True
                break
    # 收尾：同步 hreflang 与 sitemap
    U.fix_en_pages(); U.fix_lang_pages(); U.update_sitemap()
    print("\n==== 汇总 ====")
    print("新上线: %d | 已达标跳过: %d | 暂存未达标: %d | 配额中断: %s | 出错: %d"
          % (len(tally["ok"]), len(tally["skip"]), len(tally["pending"]),
             "是" if quota_stop else "否", len(tally["err"])))
    for k in ("ok", "pending", "err"):
        for line in tally[k]:
            print("  [%s] %s" % (k, line))
    return tally, quota_stop


def git_push():
    cmds = [
        ["git", "add", "-A"],
        ["git", "-c", "user.name=sanfan", "-c", "user.email=zenglinggun@gmail.com",
         "commit", "-m", "i18n: 自动续翻多语言页面 (DE/JA/KO)"],
        ["git", "push", "origin", "main"],
    ]
    for c in cmds:
        r = subprocess.run(c, cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            print("git %s -> %s" % (" ".join(c[:2]), (r.stderr or r.stdout).strip()[:150]))
            return False
    return True


if __name__ == "__main__":
    if "--page" in sys.argv:
        i = sys.argv.index("--page")
        lang, rel = sys.argv[i + 1], sys.argv[i + 2]
        st, msg = run_one(lang, rel)
        print(json.dumps({"status": st, "msg": msg}, ensure_ascii=False))
    else:
        tally, quota_stop = dispatch()
        if tally["ok"] and "--no-push" not in sys.argv:
            print("\n推送 GitHub...")
            print("推送成功" if git_push() else "推送失败(代码已本地提交，稍后可手动 push)")
        elif not tally["ok"]:
            print("本次无新增页面，不推送")
