"""把一个 penwash 脚本重跑一遍并录成 mp4：一笔一笔看着画出来。
用法：python3 record.py <脚本.py> <输出.mp4> [every=2] [fps=30]
脚本本身一个字不用改：录制钩子在 penwash_lib 里；脚本里的 out = "...png" 会被改到临时文件，不动原图。
需要系统里有 ffmpeg。
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import penwash_lib as P

script, out_mp4 = sys.argv[1], sys.argv[2]
every = int(sys.argv[3]) if len(sys.argv) > 3 else 2
fps = int(sys.argv[4]) if len(sys.argv) > 4 else 30

src = open(script, encoding="utf-8").read()
tmp_png = os.path.join(os.path.dirname(os.path.abspath(out_mp4)), ".rec-" + os.path.basename(script).replace(".py", ".png"))
src, n = re.subn(r'out = (?:os\.path\.join\([^\n]+\)|"[^"]+\.png")', f'out = "{tmp_png}"', src)
assert n == 1, "脚本里没找到 out = ... 那一行"

t0 = time.time()
P.record_start(out_mp4, fps=fps, every=every, hold=fps * 2)
exec(compile(src, script, "exec"), {"__name__": "__main__", "__file__": os.path.abspath(script)})
frames, path = P.record_stop()
if os.path.exists(tmp_png):
    os.remove(tmp_png)
print(f"{frames} frames -> {path}  ({frames / fps:.1f}s @ {fps}fps, {time.time() - t0:.1f}s to render)")
