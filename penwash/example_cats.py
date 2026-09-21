"""潦草线条小猫：速写本一页，五个姿势。
潦草 = 线找形：每条线画两三遍各自偏几个像素、抖得大、不闭合、断墨。几乎不上色，三处一点粉。
拷这个改姿势、改数量；SEED 换一个就是同一只手再画一遍。
"""
import math
import random
import sys

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import penwash_lib as P
import numpy as np

SEED = 2253
random.seed(SEED)
np.random.seed(SEED)

W, H = 900, 1100
P.set_size(W, H)
img = P.paper(W, H)

INK = P.INK
SOFT = P.INK_SOFT
PINK = (232, 160, 176)
GREY = (150, 146, 142)

SCR = dict(ink=INK, width=(0.9, 2.4), alpha=(170, 240), wobble=2.0, gaps=0.07, jitter=0.4, nib=True)
SCR_SOFT = dict(ink=SOFT, width=(0.7, 1.6), alpha=(90, 160), wobble=2.2, gaps=0.12, jitter=0.4)


def ru(r):
    return random.uniform(-r, r)


def scr(base, pts, k=2, smooth=True, per=8, over=0.0, **kw):
    """潦草线：主线一遍 + (k-1) 遍找形线，各自整体偏 2–5px、更淡更抖。"""
    args = dict(SCR)
    args.update(kw)
    base = P.pen_path(base, pts, smooth=smooth, per=per, overshoot=over if not smooth else 0.0, **args)
    for i in range(k - 1):
        a2 = dict(args)
        a2["alpha"] = (int(args["alpha"][0] * 0.45), int(args["alpha"][1] * 0.55))
        a2["width"] = (args["width"][0] * 0.8, args["width"][1] * 0.8)
        a2["wobble"] = args["wobble"] * 1.3
        a2["gaps"] = min(0.3, args["gaps"] * 2)
        base = P.pen_path(base, pts, smooth=smooth, per=per, overshoot=over if not smooth else 0.0, shift=(ru(5), ru(5)), **a2)
    return base


def arc_pts(cx, cy, rx, ry, a0, a1, n=18, rough=0.1):
    return P.ellipse_pts(cx, cy, rx, ry, n=n, rough=rough, start=math.radians(a0), end=math.radians(a1))


def ears(base, cx, cy, s, spread=30, h=44, tilt=0.0, k=2):
    for side in (-1, 1):
        e = [(cx + side * (spread - 4) * s, cy - 10 * s), (cx + side * (spread + 8 + tilt) * s, cy - h * s), (cx + side * 8 * s, cy - 24 * s)]
        base = scr(base, e, k=k, smooth=False, over=5)
    return base


def face(base, cx, cy, s, eyes="open", k=2):
    # 眼睛
    if eyes == "open":
        for side in (-1, 1):
            ex = cx + side * 12 * s
            base = scr(base, [(ex, cy - 4 * s), (ex + ru(1), cy + 4 * s)], k=1, smooth=False, width=(1.6, 2.8), gaps=0.0, wobble=0.6)
    elif eyes == "closed":
        for side in (-1, 1):
            ex = cx + side * 12 * s
            base = scr(base, arc_pts(ex, cy - 2 * s, 7 * s, 5 * s, 200, 340, n=8, rough=0.08), k=1, smooth=False, width=(1.0, 1.9), gaps=0.0, wobble=0.6)
    elif eyes == "dot":
        for side in (-1, 1):
            ex = cx + side * 11 * s
            base = P.wash(base, P.ellipse_pts(ex, cy, 2.6 * s, 2.8 * s, n=10), INK, alpha=(200, 240), offset=(0, 0), feather=0.5, layers=1, edge=0.0, texture=0.0)
    # 鼻子一个小 v，嘴 ω
    base = scr(base, [(cx - 4 * s, cy + 9 * s), (cx, cy + 14 * s), (cx + 4 * s, cy + 9 * s)], k=1, smooth=False, width=(1.0, 1.8), gaps=0.0, wobble=0.5)
    base = scr(base, arc_pts(cx - 5 * s, cy + 15 * s, 5 * s, 4 * s, 10, 170, n=8, rough=0.1), k=1, smooth=False, width=(0.8, 1.5), gaps=0.0, wobble=0.6)
    base = scr(base, arc_pts(cx + 5 * s, cy + 15 * s, 5 * s, 4 * s, 10, 170, n=8, rough=0.1), k=1, smooth=False, width=(0.8, 1.5), gaps=0.0, wobble=0.6)
    # 胡子三根一边，飞出去
    for side in (-1, 1):
        for j, dy in enumerate((-4, 3, 10)):
            x0 = cx + side * 16 * s
            base = scr(base, [(x0, cy + dy * s + 4 * s), (x0 + side * (34 + j * 4) * s + ru(4), cy + (dy - 6 + j * 6) * s + ru(4))], k=1, smooth=False, width=(0.6, 1.4), alpha=(120, 200), wobble=1.2, gaps=0.1)
    return base


# ================= 1. 坐着看你的 =================
cx, cy, s = 224, 250, 1.0
# 头：一个不闭合的圆，口在左上耳根
base_head = arc_pts(cx, cy, 34 * s, 31 * s, -60, 255, n=20, rough=0.1)
img = scr(img, base_head, k=3)
img = ears(img, cx, cy, s)
img = P.wash(img, [(cx - 30 * s, cy - 16 * s), (cx - 36 * s, cy - 36 * s), (cx - 16 * s, cy - 24 * s)], PINK, alpha=(70, 100), offset=(3, 2), feather=2, layers=1, edge=0.2, texture=0.3)
img = face(img, cx, cy, s, eyes="open")
# 身体：豆形，从头两侧下来，底下不合拢
img = scr(img, [(cx - 22 * s, cy + 28 * s), (cx - 42 * s, cy + 70 * s), (cx - 38 * s, cy + 112 * s), (cx - 10 * s, cy + 124 * s)], k=2)
img = scr(img, [(cx + 24 * s, cy + 28 * s), (cx + 44 * s, cy + 66 * s), (cx + 40 * s, cy + 110 * s), (cx + 14 * s, cy + 124 * s)], k=2)
# 前爪两根线 + 小弧爪
for side in (-1, 1):
    px = cx + side * 13 * s
    img = scr(img, [(px, cy + 84 * s), (px + ru(2), cy + 122 * s)], k=2, smooth=False)
    img = scr(img, arc_pts(px, cy + 122 * s, 9 * s, 6 * s, 0, 180, n=8, rough=0.12), k=1, smooth=False, width=(0.9, 1.8))
# 尾巴从右屁股绕出来
img = scr(img, [(cx + 36 * s, cy + 104 * s), (cx + 68 * s, cy + 100 * s), (cx + 84 * s, cy + 72 * s), (cx + 76 * s, cy + 48 * s)], k=2, width=(1.0, 2.6))
# 胸口一小撮毛
img = scr(img, [(cx - 6 * s, cy + 40 * s), (cx + 2 * s, cy + 48 * s), (cx + 8 * s, cy + 40 * s)], k=1, smooth=False, **SCR_SOFT)

# ================= 2. 趴成面包的 =================
cx, cy, s = 620, 330, 1.0
# 身体：扁团，一块随手抹的灰
loaf = P.ellipse_pts(cx + 10 * s, cy + 18 * s, 96 * s, 44 * s, n=22, rough=0.08)
img = P.wash(img, loaf, GREY, alpha=(34, 52), offset=(12, 8), feather=5, layers=1, edge=0.3, texture=0.6)
img = scr(img, arc_pts(cx + 10 * s, cy + 18 * s, 96 * s, 44 * s, -40, 235, n=24, rough=0.08), k=3)
# 头在左上，压在身体上
hx, hy = cx - 62 * s, cy - 12 * s
img = scr(img, arc_pts(hx, hy, 32 * s, 29 * s, -50, 250, n=18, rough=0.1), k=3)
img = ears(img, hx, hy, s, spread=28, h=40)
img = face(img, hx, hy, s, eyes="closed")
# 前爪折在胸前：两个小弧
img = scr(img, arc_pts(hx + 22 * s, hy + 36 * s, 14 * s, 8 * s, 180, 360, n=8, rough=0.1), k=1, smooth=False, width=(0.9, 1.8))
img = scr(img, arc_pts(hx + 48 * s, hy + 38 * s, 14 * s, 8 * s, 180, 360, n=8, rough=0.1), k=1, smooth=False, width=(0.9, 1.8))
# 尾巴绕身前
img = scr(img, [(cx + 100 * s, cy + 30 * s), (cx + 80 * s, cy + 66 * s), (cx + 30 * s, cy + 72 * s), (cx - 10 * s, cy + 60 * s)], k=2, width=(1.0, 2.6))
# 背上几根乱毛
for i in range(4):
    x = cx + 20 * s + i * 18 * s + ru(4)
    img = scr(img, [(x, cy - 24 * s + ru(3)), (x + ru(3) + 4, cy - 34 * s + ru(4))], k=1, smooth=False, **SCR_SOFT)

# ================= 3. 伸懒腰的 =================
cx, cy, s = 300, 610, 1.0
hx, hy = cx - 72 * s, cy + 6 * s
# 背线：从头顶后面拱到屁股再下去
img = scr(img, [(hx + 14 * s, hy - 26 * s), (cx - 30 * s, cy - 30 * s), (cx + 30 * s, cy - 56 * s), (cx + 72 * s, cy - 44 * s), (cx + 84 * s, cy - 6 * s)], k=3, width=(1.0, 2.6))
# 头：低着，侧面圆
img = scr(img, arc_pts(hx, hy, 30 * s, 28 * s, 20, 330, n=18, rough=0.1), k=3)
img = ears(img, hx, hy, s, spread=24, h=40, tilt=-6)
img = face(img, hx - 4 * s, hy + 2 * s, s, eyes="closed")
# 前腿伸直往左下
img = scr(img, [(hx + 10 * s, hy + 28 * s), (hx - 20 * s, hy + 62 * s), (hx - 34 * s, hy + 74 * s)], k=2, width=(1.0, 2.4))
img = scr(img, [(hx + 26 * s, hy + 30 * s), (hx - 4 * s, hy + 66 * s), (hx - 18 * s, hy + 78 * s)], k=2, width=(1.0, 2.4))
img = scr(img, [(hx - 36 * s, hy + 76 * s), (hx - 8 * s, hy + 84 * s)], k=1, smooth=False, width=(0.9, 1.8))
# 肚线
img = scr(img, [(hx + 30 * s, hy + 40 * s), (cx + 10 * s, cy + 34 * s), (cx + 60 * s, cy + 36 * s)], k=2, **SCR_SOFT)
# 后腿：两根线立着
img = scr(img, [(cx + 56 * s, cy + 30 * s), (cx + 54 * s, cy + 70 * s), (cx + 70 * s, cy + 72 * s)], k=2, smooth=False, over=3)
img = scr(img, [(cx + 82 * s, cy - 4 * s), (cx + 84 * s, cy + 70 * s), (cx + 96 * s, cy + 72 * s)], k=2, smooth=False, over=3)
# 尾巴竖起来
img = scr(img, [(cx + 66 * s, cy - 46 * s), (cx + 84 * s, cy - 60 * s), (cx + 96 * s, cy - 84 * s), (cx + 88 * s, cy - 112 * s), (cx + 104 * s, cy - 130 * s)], k=2, width=(1.0, 2.6))

# ================= 4. 背对着你的 =================
cx, cy, s = 650, 660, 1.0
# 屁股：一个大团，上面开口接头
img = scr(img, arc_pts(cx, cy + 44 * s, 56 * s, 64 * s, -70, 250, n=22, rough=0.09), k=3)
img = P.wash(img, P.ellipse_pts(cx + 10 * s, cy + 60 * s, 40 * s, 36 * s, n=16, rough=0.1), GREY, alpha=(28, 44), offset=(14, 6), feather=6, layers=1, edge=0.2, texture=0.6)
# 后脑勺：圆 + 两耳，没脸
hx, hy = cx, cy - 34 * s
img = scr(img, arc_pts(hx, hy, 32 * s, 30 * s, -60, 250, n=18, rough=0.1), k=3)
img = ears(img, hx, hy, s, spread=26, h=42)
# 后脑勺上一撮毛
img = scr(img, [(hx - 6 * s, hy - 24 * s), (hx, hy - 34 * s), (hx + 6 * s, hy - 26 * s)], k=1, smooth=False, **SCR_SOFT)
# 尾巴从底下中间竖起来，S 形，尖端到头旁边
img = scr(img, [(cx + 8 * s, cy + 104 * s), (cx + 40 * s, cy + 88 * s), (cx + 66 * s, cy + 50 * s), (cx + 56 * s, cy + 10 * s), (cx + 70 * s, cy - 24 * s)], k=3, width=(1.1, 2.8))
# 后脚两个小弧露在下面
for dx in (-22, 14):
    img = scr(img, arc_pts(cx + dx * s, cy + 108 * s, 12 * s, 6 * s, 0, 180, n=8, rough=0.12), k=1, smooth=False, width=(0.9, 1.8))

# ================= 5. 只有一张脸的 + 喵 =================
cx, cy, s = 206, 900, 0.9
img = scr(img, arc_pts(cx, cy, 34 * s, 31 * s, -60, 255, n=20, rough=0.12), k=3)
img = ears(img, cx, cy, s, spread=30, h=46)
img = P.wash(img, P.ellipse_pts(cx, cy + 10 * s, 4 * s, 3 * s, n=10), PINK, alpha=(90, 130), offset=(1, 1), feather=1, layers=1, edge=0.0, texture=0.0)
img = face(img, cx, cy, s, eyes="dot")
# 腮红两块
for side in (-1, 1):
    img = P.wash(img, P.ellipse_pts(cx + side * 22 * s, cy + 8 * s, 7 * s, 4 * s, n=12, rough=0.1), PINK, alpha=(50, 80), offset=(2, 1), feather=2.5, layers=1, edge=0.0, texture=0.3)
img = P.pen_text(img, "喵", (cx + 62, cy - 30), size=34, alpha=200, rot=8)
img = P.pen_text(img, "?", (cx + 98, cy - 36), size=26, ink=SOFT, alpha=150, rot=6)

# ---------- 纸角一个小爪印 ----------
px_, py_ = 520, 960
img = P.wash(img, P.ellipse_pts(px_, py_ + 8, 11, 9, n=12, rough=0.1), INK, alpha=(150, 200), offset=(0, 0), feather=0.8, layers=1, edge=0.0, texture=0.0)
for i, (dx, dy) in enumerate(((-13, -6), (-5, -13), (5, -13), (13, -6))):
    img = P.wash(img, P.ellipse_pts(px_ + dx, py_ + dy, 4.2, 4.6, n=10, rough=0.1), INK, alpha=(150, 200), offset=(0, 0), feather=0.6, layers=1, edge=0.0, texture=0.0)

# ---------- 署名 ----------
img = P.vertical_text(img, "小猫", (846, 130), size=30, alpha=205, gap=8)
img = P.vertical_text(img, "一·一", (846, 226), size=22, alpha=160, gap=4)
img = P.pen_text(img, "A.", (826, 1040), size=30, alpha=190)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example_cats.png")
img.convert("RGB").save(out, quality=95)
print(out)
