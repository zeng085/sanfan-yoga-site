#!/bin/bash
# 分进程逐页生成（避免长驻进程被 OOM kill），每页独立 python 进程
cd /Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16/i18n_build || exit 1
PY=/Users/mac-zlg/.workbuddy/binaries/python/versions/3.13.12/bin/python3
PAGES=(index.html about.html products.html faq.html contact.html products/ym1.html products/ym2.html products/ym3.html products/fr1.html products/rb2.html)
for L in ja ko; do
  for P in "${PAGES[@]}"; do
    OUT=$("$PY" -c "
import sys; sys.path.insert(0,'.')
import build_pages as B
try:
    B.build_one('$P','$L'); print('OK')
except SystemExit:
    import translator as T; T.flush(); print('QUOTA')
except Exception as e:
    import translator as T; T.flush(); print('ERR:'+str(e)[:70])
" 2>&1 | tail -1)
    echo "$L/$P -> $OUT"
    sleep 1
  done
done
echo "ALL_DONE"
