#!/bin/bash
# T2：用 DeepL 生成 fr/it/es 三语各 10 页（逐页独立进程，避免长驻进程被 OOM kill）
cd /Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16/i18n_build || exit 1
PY=/Users/mac-zlg/.workbuddy/binaries/python/versions/3.13.12/bin/python3
PAGES=(index.html about.html products.html faq.html contact.html \
       products/ym1.html products/ym2.html products/ym3.html products/fr1.html products/rb2.html)
for L in fr it es; do
  for P in "${PAGES[@]}"; do
    OUT=$("$PY" -c "
import sys; sys.path.insert(0,'.')
import build_pages as B
try:
    B.build_one('$P','$L',verbose=False); print('OK')
except Exception as e:
    import translator as T; T.flush(); print('ERR:'+str(e)[:60])
" 2>&1 | tail -1)
    echo "$L/$P -> $OUT"
    sleep 0.5
  done
done
echo "=== T2 GEN DONE ==="
