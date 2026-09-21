"""钢笔淡彩示例：一只马克杯、一颗切开的柠檬、一枚新月吊坠。
拷这个文件改。坐标全是变量，改构图只动那几个数。
先在下面写清楚三样东西各是哪件真事——没有真事不动手。
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import penwash_lib as P
import numpy as np

SEED = 7
random.seed(SEED)
np.random.seed(SEED)

W, H = 900, 1100
P.set_size(W, H)
img = P.paper(W, H)

INK = P.INK
SOFT = P.INK_SOFT
COFFEE = (146, 104, 68)
COFFEE_LT = (206, 168, 124)
MUG = (232, 226, 214)
MUG_DK = (176, 168, 156)
LEMON = (226, 196, 96)
LEMON_LT = (240, 226, 160)
LEMON_PITH = (246, 240, 220)
SILVER_LT = (216, 220, 224)
SILVER = (180, 186, 194)
SHADOW = (186, 194, 200)

LINE = dict(ink=INK, width=(1.1, 2.2), alpha=(185, 245), wobble=1.1, gaps=0.04)
LINE_SOFT = dict(ink=SOFT, width=(0.7, 1.3), alpha=(110, 180), wobble=1.1, gaps=0.08)


def ru(r):
    return random.uniform(-r, r)


def crescent(cx, cy, r1, dx, dy, r2, n=64):
    """新月：大圆 (cx,cy,r1) 减去偏移 (dx,dy) 的圆 r2。返回闭合多边形。"""
    th2 = math.atan2(dy, dx)
    outer, inner = [], []
    for i in range(n * 3):
        a = 2 * math.pi * i / (n * 3)
        x, y = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
        if (x - (cx + dx)) ** 2 + (y - (cy + dy)) ** 2 > r2 * r2:
            outer.append(((a - th2) % (2 * math.pi), (x, y)))
    for i in range(n * 3):
        a = 2 * math.pi * i / (n * 3)
        x, y = cx + dx + r2 * math.cos(a), cy + dy + r2 * math.sin(a)
        if (x - cx) ** 2 + (y - cy) ** 2 < r1 * r1:
            inner.append(((math.atan2(y - cy, x - cx) - th2) % (2 * math.pi), (x, y)))
    outer.sort(key=lambda t: t[0])
    inner.sort(key=lambda t: -t[0])
    return [p for _, p in outer] + [p for _, p in inner]


# ---------- 构图坐标 ----------
table_y = 720          # 桌面线，三样东西的底都落在这条线 ±10px
mx, my = 330, table_y  # 马克杯底部中心
mw, mh = 92, 210       # 杯半宽、杯高
lx, ly = 600, table_y - 30   # 柠檬中心
px, py = 720, 300      # 吊坠中心

# ---------- 投影（先画，压在最底下） ----------
img = P.wash(img, P.blob(mx + 18, my + 8, mw + 30, 16, k=18, rough=0.1), SHADOW, alpha=(40, 60), offset=(10, 3), feather=6, layers=1, edge=0.0, texture=0.4)
img = P.wash(img, P.blob(lx + 10, ly + 34, 66, 12, k=16, rough=0.1), SHADOW, alpha=(40, 60), offset=(8, 2), feather=5, layers=1, edge=0.0, texture=0.4)

# ---------- 马克杯 ----------
# 杯身：一个上宽下窄一点的梯形，竖边手画着微弯
body = [(mx - mw, my - mh), (mx - mw - 3, my - mh * 0.5), (mx - mw + 6, my), (mx + mw - 6, my), (mx + mw + 3, my - mh * 0.5), (mx + mw, my - mh)]
body_sm = P.catmull(body, per=10)
img = P.wash(img, body_sm + [(mx + mw, my - mh)], MUG, alpha=(60, 90), offset=(6, 4), feather=3, layers=2, edge=0.35, texture=0.5)
# 右侧暗部：一片深一点的 wash + 竖排线
dark = [(mx + 20, my - 4), (mx + mw - 6, my - 2), (mx + mw + 2, my - mh * 0.5), (mx + mw - 2, my - mh + 4), (mx + 36, my - mh + 8)]
img = P.wash(img, dark, MUG_DK, alpha=(60, 90), offset=(4, 3), feather=6, layers=1, edge=0.3, texture=0.5)
img = P.hatch(img, P.poly_mask(dark, shrink=2), angle=86, spacing=3.4, ink=SOFT, alpha=(90, 160), width=(0.6, 1.2), length=(0.4, 0.9), density=0.8)
# 高光留白：左侧一条竖的
img = P.wash(img, [(mx - mw + 10, my - mh + 20), (mx - mw + 24, my - mh + 18), (mx - mw + 22, my - 20), (mx - mw + 12, my - 24)], (246, 242, 234), alpha=(90, 130), offset=(0, 0), feather=2, layers=1, edge=0.0, texture=0.2)
# 杯口：椭圆别画圆；里面的咖啡是一片深色椭圆，边上一圈留白当奶泡
img = P.wash(img, P.ellipse_pts(mx, my - mh, mw, 26, n=40, rough=0.04), MUG, alpha=(80, 110), offset=(0, 0), feather=2, layers=1, edge=0.4, texture=0.3)
img = P.wash(img, P.ellipse_pts(mx + 2, my - mh + 3, mw - 14, 18, n=40, rough=0.05), COFFEE, alpha=(110, 150), offset=(2, 1), feather=2, layers=2, edge=0.5, texture=0.5)
img = P.speckle(img, P.ellipse_pts(mx - 30, my - mh - 2, 30, 10, n=24), LEMON_PITH, n=40, r=(0.8, 2.0), alpha=(90, 160))
# 轮廓：主线 overdraw，杯口两道弧
img = P.pen_path(img, body_sm, overdraw=1, **LINE)
img = P.pen_ellipse(img, mx, my - mh, mw, 26, rough=0.05, overdraw=1, **LINE)
img = P.pen_arc(img, mx + 2, my - mh + 3, mw - 14, 18, 10, 170, rough=0.06, **LINE_SOFT)
img = P.pen_arc(img, mx, my, mw - 4, 18, 10, 170, rough=0.05, **LINE_SOFT)   # 杯底那道弧
# 把手：先 wash 一条环带，再排线，最后描外弧内弧（线永远最后画，不然被 wash 压淡）
hx, hy = mx + mw - 4, my - mh * 0.55
handle_band = P.ellipse_pts(hx, hy, 58, 64, n=30, rough=0.03, start=math.radians(-75), end=math.radians(75)) + \
    P.ellipse_pts(hx, hy, 36, 44, n=30, rough=0.03, start=math.radians(75), end=math.radians(-75))
img = P.wash(img, handle_band, MUG, alpha=(60, 90), offset=(4, 3), feather=2.5, layers=1, edge=0.35, texture=0.4)
img = P.hatch(img, P.poly_mask(P.ellipse_pts(hx, hy, 58, 64, n=20, start=math.radians(-20), end=math.radians(75)) +
                               P.ellipse_pts(hx, hy, 36, 44, n=20, start=math.radians(75), end=math.radians(-20)), shrink=1),
              angle=70, spacing=3.4, ink=SOFT, alpha=(80, 150), width=(0.6, 1.1), length=(0.4, 0.9), density=0.75)
img = P.pen_arc(img, hx, hy, 58, 64, -75, 75, rough=0.05, overdraw=1, **LINE)
img = P.pen_arc(img, hx, hy, 36, 44, -70, 70, rough=0.06, **LINE)

# ---------- 半颗柠檬 ----------
# 外皮：一个稍扁的 blob；切面：内一圈白瓤 + 八瓣放射线
skin = P.blob(lx, ly, 62, 52, k=22, rough=0.05)
img = P.wash(img, skin, LEMON, alpha=(100, 140), offset=(5, 4), feather=3, layers=2, edge=0.45, texture=0.55)
img = P.wash(img, [(lx + 10, ly + 48), (lx + 56, ly + 30), (lx + 62, ly - 10), (lx + 40, ly + 10)], (196, 160, 70), alpha=(50, 80), offset=(3, 2), feather=6, layers=1, edge=0.3, texture=0.5)
pith = P.ellipse_pts(lx - 2, ly - 2, 50, 41, n=36, rough=0.04)
img = P.wash(img, pith, LEMON_PITH, alpha=(150, 190), offset=(0, 0), feather=2, layers=1, edge=0.2, texture=0.2)
pulp = P.ellipse_pts(lx - 2, ly - 2, 42, 34, n=36, rough=0.05)
img = P.wash(img, pulp, LEMON_LT, alpha=(90, 126), offset=(2, 1), feather=2, layers=2, edge=0.4, texture=0.5)
for i in range(8):
    a = i * math.pi / 4 + ru(0.12)
    img = P.pen_path(img, [(lx - 2 + 6 * math.cos(a), ly - 2 + 5 * math.sin(a)), (lx - 2 + 40 * math.cos(a) + ru(2), ly - 2 + 32 * math.sin(a) + ru(2))],
                     ink=SOFT, width=(0.6, 1.1), alpha=(100, 160), wobble=0.8, smooth=False, gaps=0.1)
img = P.speckle(img, pulp, (250, 246, 230), n=50, r=(0.5, 1.4), alpha=(70, 130))
img = P.pen_path(img, skin + [skin[0]], overdraw=1, **LINE)
img = P.pen_path(img, pith + [pith[0]], **LINE_SOFT)
img = P.pen_path(img, pulp, ink=INK, width=(0.8, 1.5), alpha=(150, 215), wobble=0.9, gaps=0.06, per=4)
# 皮的厚度：右下一小段深线
img = P.pen_arc(img, lx, ly, 60, 50, 20, 80, rough=0.06, ink=INK, width=(1.0, 1.8), alpha=(170, 230), wobble=0.8)

# ---------- 新月吊坠（银 = 留白 + 一条深边） ----------
moon = crescent(px, py, 54, 18, -10, 48)
img = P.wash(img, moon, SILVER_LT, alpha=(28, 44), offset=(4, 3), feather=3, layers=2, edge=0.3, texture=0.5)
img = P.wash(img, [moon[i] for i in range(0, len(moon) // 3)] + [(px - 10, py + 30)], SILVER, alpha=(56, 86), offset=(4, 3), feather=5, layers=1, edge=0.4, texture=0.5)
img = P.hatch(img, P.poly_mask([moon[i] for i in range(0, len(moon) // 3)] + [(px - 14, py + 24)], shrink=1), angle=60, spacing=3.2, ink=INK, alpha=(110, 190), width=(0.7, 1.3), length=(0.45, 0.9), density=0.85)
img = P.pen_path(img, moon + [moon[0]], ink=INK, width=(1.0, 1.9), alpha=(180, 240), wobble=0.8, gaps=0.03, per=4, overdraw=1)
# 顶环 + 链子往右上甩出画外
ring_y = py - 62
img = P.pen_ellipse(img, px - 22, ring_y, 11, 12, rough=0.05, overdraw=1, **LINE)
img = P.pen_ellipse(img, px - 22, ring_y, 5, 6, rough=0.06, ink=INK, width=(0.9, 1.6), alpha=(160, 230), wobble=0.6)
chain = P.catmull([(px - 22, ring_y - 12), (px - 4, 190), (px + 40, 130), (px + 110, 96), (px + 170, 40), (px + 210, -30)], per=10)
acc, last, nodes = 0.0, chain[0], [chain[0]]
for p in chain[1:]:
    acc += math.hypot(p[0] - last[0], p[1] - last[1])
    last = p
    if acc >= 15.0:
        nodes.append(p)
        acc = 0.0
for i in range(len(nodes) - 1):
    x, y = nodes[i]
    if y < -10:
        break
    ang = math.atan2(nodes[i + 1][1] - y, nodes[i + 1][0] - x)
    if i % 2 == 0:
        img = P.pen_ellipse(img, x, y, 8.4, 5.0, rot=ang, rough=0.06, n=20, ink=INK, width=(0.9, 1.7), alpha=(160, 235), wobble=0.5)
    else:
        img = P.pen_ellipse(img, x, y, 5.4, 3.0, rot=ang + math.pi / 2, rough=0.08, n=16, ink=INK, width=(0.8, 1.4), alpha=(140, 210), wobble=0.4)

# ---------- 桌面线：断断续续的一条 ----------
img = P.pen_path(img, [(120, table_y + 2), (300, table_y - 2), (520, table_y + 3), (760, table_y - 1)], ink=SOFT, width=(0.8, 1.4), alpha=(110, 170), wobble=1.2, gaps=0.14)

# ---------- 署名：右侧竖写主题 + 日期，角落一个字母 ----------
img = P.vertical_text(img, "静物", (836, 420), size=28, alpha=200, gap=6)
img = P.vertical_text(img, "一·一", (836, 512), size=22, alpha=160, gap=4)
img = P.pen_text(img, "A.", (812, 1040), size=30, alpha=190)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example.png")
img.convert("RGB").save(out, quality=95)
print(out)
