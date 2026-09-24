#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sameAs 单一可信源 + 写入前黑名单闸（供 add_sameas.py / add_org_sameas_*.py 共用）。

为什么要独立成模块：黑名单必须**只有一份**。两个注入脚本各写一份名单，
迟早出现"一个拦一个不拦"，而漏拦的代价是主动向 Google 声明"我们和同名同业是一家"。

用法:
    from sameas_guard import load_sameas
    SAMEAS = load_sameas()      # 命中黑名单会打印原因并 sys.exit(1)
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, 'i18n_build', 'sameas.json')

# ⛔ 同名同业 XIAMEN SANFAN FITNESS 的自有主页。
# sameAs 是"实体同一性"声明，填错 = 主动告诉 Google 两家是一家，比不填更糟。
BLACKLIST = [
    'sanfanyoga.com',                     # 同业官网
    'sanfanfitness.com',                  # 同业邮箱域/备用域名
    'linkedin.com/company/sanfanyoga',    # 同业 LinkedIn（handle 与本司 FB 同名，最易误填）
    'linkedin.com/showcase/sanfanyogamat',
    'xiamen-sanfan-fitness',              # 同业 Facebook 页
    'xiamensanfan',
]

# 规范化后的本司实体身份（与 index.html 的 Organization 节点保持一致）
ORG_ID = 'https://fjsanfan.com/#organization'
ORG_NAME = 'FUJIAN SANFAN Sports Products Co., Ltd.'


def load_sameas(path=None):
    """读 sameas.json，过黑名单闸，返回 URL 列表。不通过即退出（不写任何文件）。"""
    path = path or CFG
    if not os.path.exists(path):
        print(f'⛔ 找不到 {path}')
        sys.exit(1)
    data = json.load(open(path, encoding='utf-8'))
    urls = data.get('sameAs') or []
    if not urls:
        print('sameas.json 为空 —— 先填入 URL 再跑。')
        sys.exit(1)
    for u in urls:
        if not isinstance(u, str) or not u.startswith('https://'):
            print(f'⛔ sameAs 必须是 https:// 绝对地址：{u!r}')
            sys.exit(1)
        low = u.lower()
        for b in BLACKLIST:
            if b in low:
                print(f'⛔ sameAs 命中同业黑名单 [{b}]，拒绝写入：{u}')
                print('   那是 XIAMEN SANFAN FITNESS 的自有主页，属于同名同业，不是本司实体。')
                sys.exit(1)
    return urls


if __name__ == '__main__':
    for _u in load_sameas():
        print('OK  -', _u)
