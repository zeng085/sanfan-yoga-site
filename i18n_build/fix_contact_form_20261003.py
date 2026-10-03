#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""联系页表单可用性修复（2026-10-03，7 个语言版本）

审计发现（客户视角）：
  ① 6 个控件的 `<label>` **既无 `for=` 也未嵌套控件** → `el.labels` 为空
     → 读屏器不念字段名；手机上点标签不聚焦（WCAG 1.3.1 / 3.3.2 失败）
  ② 无反垃圾诱饵 → B2B 询盘表单容易被机器人刷（垃圾询盘占用邮箱）
  ③ 提交期间不禁用按钮 → 网络慢时客户连点会**产生重复询盘**
  ④ `#form-ok` 无 `aria-live` → 读屏器不播报成功/失败结果
  ⑤ 反馈文案按 `lang.startsWith('zh') ? zh : en` 二选一
     → **德/日/韩/法/意/西语页提交成功却显示英文**
     → 改为一页自带 `data-msg-ok` / `data-msg-fail`（本地化），回退到 I18N

做法：按控件自身的 `name` 映射 id（**不依赖 label 文本，也不依赖 data-i18n**
—— 语言页的 label 已被静态翻译、data-i18n 属性已被剥掉，用顺序或文案都会错）。
诱饵字段命名为 `_gotcha`：既被我方 main.js 拦截，也顺便触发 Formspree 服务端过滤。

用法：
    python3 i18n_build/fix_contact_form_20261003.py --dry-run
    python3 i18n_build/fix_contact_form_20261003.py
    python3 i18n_build/fix_contact_form_20261003.py --verify
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]

MSG = {
    "en": ("Thanks! Your inquiry has been sent. We will reply within 1 business day.",
           "Something went wrong. Please email us directly."),
    "de": ("Danke! Ihre Anfrage wurde gesendet. Wir antworten innerhalb eines Werktags.",
           "Es ist ein Fehler aufgetreten. Bitte senden Sie uns eine E-Mail."),
    "ja": ("ありがとうございます。お問い合わせを受け付けました。1 営業日以内にご返信します。",
           "送信中にエラーが発生しました。直接メールでお問い合わせください。"),
    "ko": ("감사합니다. 문의가 접수되었습니다. 영업일 기준 1일 이내에 답변드리겠습니다.",
           "전송 중 오류가 발생했습니다. 이메일로 직접 문의해 주세요."),
    "fr": ("Merci ! Votre demande a bien été envoyée. Nous vous répondrons sous un jour ouvré.",
           "Une erreur s'est produite. Veuillez nous écrire directement."),
    "it": ("Grazie! La tua richiesta è stata inviata. Risponderemo entro un giorno lavorativo.",
           "Si è verificato un errore. Scrivici direttamente via email."),
    "es": ("¡Gracias! Hemos recibido su consulta. Responderemos en un día laborable.",
           "Se ha producido un error. Por favor, escríbanos directamente."),
    "zh": ("已收到！我们将在 1 个工作日内回复。", "发送失败，请直接邮件联系我们。"),
}

RE_FORM = re.compile(r"<form\b.*?</form>", re.S)
RE_FIELD = re.compile(r'(<div class="field">)(.*?)(</div>)', re.S)
RE_CONTROL = re.compile(r"<(input|select|textarea)\b([^>]*)>", re.S)
RE_NAME = re.compile(r'\bname\s*=\s*"([^"]+)"')
RE_ID = re.compile(r'\bid\s*=\s*"([^"]+)"')
RE_LABEL = re.compile(r"(<label\b)([^>]*)(>)")
RE_SUBMIT = re.compile(r'<button\b[^>]*type\s*=\s*"submit"[^>]*>', re.I)
HONEYPOT = ('\n          <input class="form-hp" type="text" name="_gotcha" '
            'tabindex="-1" autocomplete="off" aria-hidden="true" />\n          ')


def field_id(name):
    return "inq-" + re.sub(r"[^a-z0-9_-]", "-", name.lower())


VOID_SELF_CLOSING = {"input", "img", "br", "hr", "meta", "link"}


def fix_field(m):
    head, body, tail = m.group(1), m.group(2), m.group(3)
    cm = RE_CONTROL.search(body)
    if not cm:
        return m.group(0)
    tag = cm.group(1).lower()          # input / select / textarea
    cmatch = cm.group(0)
    nm = RE_NAME.search(cmatch)
    if not nm:
        return m.group(0)
    fid = field_id(nm.group(1))
    if RE_ID.search(cmatch):
        return m.group(0)                      # 已有 id，不动
    # ⚠️ 只有 void 元素能自闭合；给 <textarea> / <select> 加 `/>` 会产出
    #    `<textarea ... />` 这种坏标签（2026-10-03 实测踩到，7 个页面全被改坏后回滚）
    if tag in VOID_SELF_CLOSING:
        if cmatch.endswith("/>"):
            newc = cmatch[:-2].rstrip() + ' id="%s" />' % fid
        else:
            newc = cmatch[:-1].rstrip() + ' id="%s" />' % fid
    else:
        newc = cmatch[:-1].rstrip() + ' id="%s">' % fid
    body2 = body.replace(cmatch, newc, 1)
    # 同 block 内的 label 加 for=
    lm = RE_LABEL.search(body2)
    if lm and "for=" not in lm.group(2):
        body2 = (body2[:lm.start()] + lm.group(1) + ' for="%s"' % fid + lm.group(2) + lm.group(3)
                 + body2[lm.end():])
    return head + body2 + tail


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    stat = []
    for lang in LANGS:
        rel = ("%s/contact.html" % lang) if lang else "contact.html"
        p = os.path.join(ROOT, rel)
        h = io.open(p, encoding="utf-8").read()
        orig = h
        key = lang if lang else "en"
        ok_msg, fail_msg = MSG[key]

        # ① form 内：label 关联 + 诱饵字段
        def do_form(fm):
            blk = fm.group(0)
            blk = RE_FIELD.sub(fix_field, blk)
            if "_gotcha" not in blk:
                blk = RE_SUBMIT.sub(lambda m: HONEYPOT + m.group(0), blk, count=1)
            return blk
        h = RE_FORM.sub(do_form, h)

        # ② #form-ok 加 aria-live + 本地化文案
        def do_ok(om):
            tag = om.group(0)
            if "aria-live" not in tag:
                tag = tag[:-1].rstrip() + ' aria-live="polite" role="status">'
            if "data-msg-ok" not in tag:
                tag = (tag[:-1].rstrip()
                       + ' data-msg-ok="%s" data-msg-fail="%s">'
                       % (ok_msg.replace('"', "&quot;"), fail_msg.replace('"', "&quot;")))
            return tag + om.group(1) if False else tag
        h = re.sub(r'<div id="form-ok"[^>]*>', do_ok, h, count=1)

        # 校验模式：不管文件是否已被改过，都要如实统计各项指标
        if mode == "--verify":
            n_for = len(re.findall(r'<label\b[^>]*\bfor\s*=', h))
            n_id = len(re.findall(r'<(?:input|select|textarea)\b[^>]*\bid="inq-', h))
            # 非自闭合元素被错加 `/>` 的坏标签（textarea/select）
            badtag = len(re.findall(r"<(?:textarea|select)\b[^>]*/>", h))
            stat.append((rel, "label[for]=%d 控件[id]=%d 诱饵=%s aria-live=%s data-msg=%s 坏自闭合=%d"
                         % (n_for, n_id, "_gotcha" in h, "aria-live" in h, "data-msg-ok" in h, badtag)))
            continue

        if h == orig:
            stat.append((rel, "无需改动"))
            continue
        if mode == "--dry-run":
            stat.append((rel, "待改（label 关联 + 诱饵 + aria-live + 本地化文案）"))
            continue
        io.open(p, "w", encoding="utf-8").write(h)
        stat.append((rel, "已改"))

    for rel, s in stat:
        print("  %-20s %s" % (rel, s))
    if mode == "--verify":
        bad = [r for r, s in stat if "label[for]=6" not in s or "控件[id]=6" not in s
               or "诱饵=True" not in s or "aria-live=True" not in s
               or "data-msg=True" not in s or "坏自闭合=0" not in s]
        print("\n不合格页面 = %d" % len(bad))
        if bad:
            for b in bad:
                print("   ✗ " + b)
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
