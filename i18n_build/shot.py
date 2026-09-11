#!/usr/bin/env python3
"""用本机 Chrome headless 截图，规避 shell 里带空格路径的引号坑。
用法: shot.py <file|url> <out.png> [width] [height]
"""
import subprocess, sys, os

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def shot(url, out, w=1440, h=2000, wait=6000):
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           f"--virtual-time-budget={wait}", f"--window-size={w},{h}",
           f"--screenshot={out}", url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    ok = os.path.exists(out)
    if not ok:
        print("FAILED:", r.returncode, r.stderr[-600:])
    return ok

def trim_bottom(png, out=None, bg=(255, 255, 255), tol=12):
    """裁掉底部多余留白"""
    from PIL import Image
    import numpy as np
    im = Image.open(png).convert("RGB")
    a = np.asarray(im).astype(int)
    rows = np.where(np.abs(a - np.array(bg)).sum(axis=2).max(axis=1) > tol)[0]
    h = int(rows.max()) + 30
    im.crop((0, 0, im.width, min(h, im.height))).save(out or png)
    return h

if __name__ == "__main__":
    url = sys.argv[1]
    out = sys.argv[2]
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 1440
    h = int(sys.argv[4]) if len(sys.argv) > 4 else 2000
    if shot(url, out, w, h):
        print("→", out, os.path.getsize(out), "B")
