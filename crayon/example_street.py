#!/usr/bin/env python3
"""蜡笔街景范例：Napier（新西兰）的 Art Deco 街——六栋粉彩小楼一栋挨一栋。
楼歪、高低乱、窗户不齐、色块留纸、字一个一个歪着写、指线弯的；街上有老爷车、电线上两只鸟、窗台一只猫、门口花盆、笑脸云。
用法：python3 example_street.py  → 输出 example_street.png（约 3 秒）"""
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))  # crayon_lib.py 放同目录即可
import crayon_lib as C  # noqa: E402

random.seed(1932)
np.random.seed(1932)
W, H = 880, 1250
C.set_size(W, H)
img = Image.new("RGBA", (W, H), C.PAPER + (255,))
INK = (58, 72, 138)
BLACK = (34, 32, 38)


def fill(mask, color, **kw):
    global img
    img = C.crayon(img, mask, color, **kw)


def line(pts, color, **kw):
    global img
    img = C.crayon_line(img, pts, color, **kw)


def wtext(s, xy, font, color, **kw):
    global img
    img = C.wobbly_text(img, s, xy, font, color, **kw)


def squig(a, b, color, **kw):
    global img
    img = C.squiggle(img, a, b, color, **kw)


def scrib(mask, color, **kw):
    global img
    img = C.scribble(img, mask, color, **kw)


def block(poly, color, *, feather=3, grow=3, n=None, alpha=(120, 205), direction=90, dot=(1.0, 2.1)):
    """留纸的色块：alpha 低一点、边缘毛一点，纸从缝里透出来。"""
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    area = max(1, (max(xs) - min(xs)) * (max(ys) - min(ys)))
    n = n or int(area / 10000 * 2100) + 100
    m = C.soft_mask(poly, feather=feather, grow=grow)
    fill(m, color, direction=direction, spread=12, n=n, length=(8, 24), alpha=alpha, dot=dot)
    return m


# ── 天 / 地 ───────────────────────────────────────────────
FX0, FY0, FX1, FY1 = 100, 190, 780, 910
STREET = 690
sky = C.soft_mask(C.quad(FX0, FY0, FX1, STREET + 8, wobble=12), feather=8, grow=2)
fill(sky, (186, 212, 238), direction=0, spread=14, n=7000, length=(24, 64), alpha=(90, 170))
fill(sky, (232, 206, 190), direction=0, spread=14, n=1400, length=(20, 50), alpha=(30, 80))  # 一点黄昏的粉
# 太阳：一个圆 + 放射短线
SX, SYY = 660, 262
sun = C.soft_mask(C.blob(SX, SYY, 26, 26, k=16, rough=0.12), feather=2, grow=2)
fill(sun, (250, 206, 96), direction=0, spread=30, n=700, length=(4, 12), alpha=(160, 240), dot=(1.0, 2.0))
for a in np.linspace(0, 2 * math.pi, 13)[:-1]:
    a += random.uniform(-0.12, 0.12)
    line([(SX + math.cos(a) * 34, SYY + math.sin(a) * 34), (SX + math.cos(a) * (46 + random.uniform(0, 10)), SYY + math.sin(a) * (46 + random.uniform(0, 10)))], (244, 186, 80), width=(1.2, 2.0), alpha=(140, 220), wobble=0.6)
# 云：一朵是笑脸
for i, (cx, cy, rx, ry) in enumerate(((210, 262, 66, 20), (430, 232, 84, 22), (560, 318, 44, 13))):
    cm = C.soft_mask(C.blob(cx, cy, rx, ry, rough=0.3), feather=4, grow=3)
    fill(cm, (252, 252, 250), direction=0, spread=10, n=1200, length=(12, 30), alpha=(140, 230), dot=(1.2, 2.2))
    if i == 2:
        for ex in (-12, 10):
            line([(cx + ex - 2, cy - 3), (cx + ex + 2, cy - 3)], INK, width=(1.4, 2.2), alpha=(200, 255))
        line([(cx - 10, cy + 5), (cx - 3, cy + 10), (cx + 5, cy + 10), (cx + 11, cy + 4)], INK, width=(1.0, 1.6), alpha=(180, 240), wobble=0.4)
# 人行道 + 马路
block(C.quad(FX0 - 4, STREET, FX1 + 4, STREET + 44, wobble=5), (218, 210, 196), direction=0, alpha=(120, 200))
line(C.catmull([(FX0, STREET + 44), (300, STREET + 41), (520, STREET + 46), (FX1, STREET + 43)], per=12), (166, 156, 146), width=(0.8, 1.4), alpha=(100, 180), wobble=0.7)
road = block(C.quad(FX0 - 4, STREET + 44, FX1 + 4, FY1, wobble=7), (180, 176, 174), direction=0, alpha=(110, 190), dot=(1.3, 2.6))
scrib(road, (150, 146, 148), n=14, length=(30, 90), direction=-8, alpha=(30, 70))
for k in range(6):
    x = FX0 + 30 + k * 115 + random.uniform(-8, 8)
    line([(x, STREET + 124 + random.uniform(-3, 3)), (x + random.uniform(36, 58), STREET + 124 + random.uniform(-3, 3))], (240, 222, 150), width=(1.4, 2.2), alpha=(120, 200), wobble=0.8)

# ── 楼（歪的、高低乱的、留纸的）─────────────────────────────
PAL = {
    "mint": ((160, 214, 192), (112, 170, 148)),
    "peach": ((246, 186, 160), (216, 138, 112)),
    "cream": ((248, 226, 150), (212, 184, 104)),
    "lilac": ((204, 184, 226), (158, 136, 190)),
    "sky": ((168, 202, 234), (120, 158, 200)),
    "white": ((248, 240, 224), (204, 190, 168)),
}
WIN = (88, 98, 130)
WIN_L = (250, 222, 130)


def win(cx, cy, w, h, lit=False, arch=False):
    """一扇歪窗：位置尺寸都抖，可选拱顶。"""
    w *= random.uniform(0.85, 1.2); h *= random.uniform(0.85, 1.2)
    cx += random.uniform(-4, 4); cy += random.uniform(-4, 4)
    col = WIN_L if lit else WIN
    m = C.soft_mask(C.quad(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, wobble=1.6), feather=0.8, grow=1)
    fill(m, col, direction=90, spread=10, n=int(w * h / 3) + 40, length=(3, 9), alpha=(180, 250), dot=(0.8, 1.6))
    if arch:
        am = C.soft_mask(C.blob(cx, cy - h / 2, w / 2, w / 2.4, k=12, rough=0.1), feather=0.8, grow=1)
        fill(am, col, direction=0, spread=20, n=int(w * w / 4) + 30, length=(2, 7), alpha=(180, 250), dot=(0.8, 1.6))
    line([(cx - w / 2 + 1, cy + random.uniform(-2, 2)), (cx + w / 2 - 1, cy + random.uniform(-2, 2))], (248, 246, 240), width=(0.5, 0.9), alpha=(90, 170), wobble=0.4)


def door(cx, bottom, color=(96, 78, 66)):
    w, h = random.uniform(20, 26), random.uniform(38, 48)
    m = C.soft_mask(C.quad(cx - w / 2, bottom - h, cx + w / 2, bottom, wobble=1.5), feather=0.8, grow=1)
    fill(m, color, direction=90, spread=10, n=300, length=(4, 10), alpha=(190, 255), dot=(0.8, 1.6))
    line([(cx - w / 2 - 9, bottom - h - 5 + random.uniform(-2, 2)), (cx + w / 2 + 9, bottom - h - 5 + random.uniform(-2, 2))], (124, 104, 90), width=(1.4, 2.4), alpha=(150, 230), wobble=0.7)
    # 门口一个花盆
    px = cx + random.choice((-1, 1)) * (w / 2 + 12)
    pm = C.soft_mask([(px - 6, bottom - 12), (px + 6, bottom - 12), (px + 5, bottom), (px - 5, bottom)], feather=0.6, grow=1)
    fill(pm, (196, 116, 84), direction=90, spread=10, n=80, length=(2, 6), alpha=(180, 250), dot=(0.8, 1.5))
    for _ in range(3):
        fx, fy = px + random.uniform(-6, 6), bottom - 16 + random.uniform(-4, 2)
        fm = C.soft_mask(C.blob(fx, fy, 3.2, 3.2, k=8, rough=0.2), feather=0.4, grow=0)
        fill(fm, random.choice(((236, 96, 110), (250, 200, 80), (236, 150, 184))), direction=0, spread=30, n=30, length=(1, 3), alpha=(200, 255), dot=(0.6, 1.2))


def stepped(cx, top, widths, step, color):
    y = top
    for wdt in widths:
        m = C.soft_mask(C.quad(cx - wdt / 2, y - step, cx + wdt / 2, y + 3, wobble=2.5), feather=1.5, grow=2)
        fill(m, color, direction=90, spread=12, n=int(wdt * step / 3) + 40, length=(4, 12), alpha=(120, 205), dot=(1.0, 2.0))
        y -= step


def stripes(x0, x1, y0, y1, color, k):
    for i in range(k):
        x = x0 + (x1 - x0) * (i + 1) / (k + 1) + random.uniform(-2, 2)
        line([(x, y0 + random.uniform(-3, 3)), (x + random.uniform(-3, 3), y1 + random.uniform(-3, 3))], color, width=(1.2, 2.2), alpha=(110, 200), wobble=0.8)


def sunburst(cx, cy, r, color, rays=8):
    arc = [(cx + math.cos(a) * r * random.uniform(0.95, 1.05), cy - math.sin(a) * r * random.uniform(0.95, 1.05)) for a in np.linspace(0, math.pi, 26)]
    line(arc, color, width=(1.2, 2.0), alpha=(140, 230), wobble=0.7)
    for a in np.linspace(0.18, math.pi - 0.18, rays):
        line([(cx + math.cos(a) * r * 0.28, cy - math.sin(a) * r * 0.28), (cx + math.cos(a) * r * random.uniform(0.8, 0.95), cy - math.sin(a) * r * random.uniform(0.8, 0.95))], color, width=(1.0, 1.7), alpha=(120, 210), wobble=0.6)


def zigzag(x0, x1, y, amp, color, n=10):
    pts = [(x0 + (x1 - x0) * i / n + random.uniform(-1.5, 1.5), y + (amp if i % 2 else -amp) + random.uniform(-1.5, 1.5)) for i in range(n + 1)]
    line(pts, color, width=(1.0, 1.7), alpha=(130, 220), wobble=0.5)


# 六栋：x 范围、高度、倾斜、类型
BUILD = [
    (108, 222, 230, 0.02, "mint", "step"),
    (218, 322, 318, -0.025, "peach", "tower"),
    (318, 438, 214, 0.015, "cream", "sun"),
    (432, 556, 336, -0.02, "lilac", "step2"),
    (550, 652, 238, 0.03, "sky", "round"),
    (646, 758, 288, -0.015, "white", "flag"),
]
tops = {}
for (x0, x1, hgt, lean, pal, kind) in BUILD:
    base, dark = PAL[pal]
    top = STREET - hgt
    tops[kind] = (x0, x1, top)
    poly = C.quad(x0, top, x1, STREET + 2, wobble=6, lean=lean)
    m = block(poly, base, feather=3, grow=3)
    scrib(m, dark, n=9, length=(18, 50), direction=random.choice((-40, -30, 60)), alpha=(30, 80))
    cx = (x0 + x1) / 2 + (x1 - x0) * lean
    if kind == "step":
        stepped(cx, top, (74, 48, 24), 13, base)
        line([(x0 + 8, top + 12), (x1 - 8, top + 10)], dark, width=(1.0, 1.8), alpha=(120, 200), wobble=0.9)
        for (wx, wy, lit) in ((x0 + 30, top + 50, False), (x1 - 28, top + 46, True), (x0 + 34, top + 110, False), (x1 - 30, top + 118, False), (cx, top + 82, False)):
            win(wx, wy, 17, 21, lit)
    elif kind == "tower":
        tm = block(C.quad(cx - 24, top - 46, cx + 24, top + 6, wobble=3), base, feather=1.5, grow=2)
        stripes(cx - 19, cx + 19, top - 40, top + 44, dark, 3)
        zigzag(x0 + 10, x1 - 10, top + 56, 5, dark, n=11)
        for (wx, wy, lit, arch) in ((x0 + 28, top + 84, False, True), (x1 - 26, top + 88, True, True), (x0 + 30, top + 150, False, False), (x1 - 28, top + 146, False, False), (cx, top + 200, False, False), (x0 + 26, top + 212, False, False)):
            win(wx, wy, 16, 22, lit, arch)
    elif kind == "sun":
        block(C.quad(cx - 32, top - 20, cx + 32, top + 6, wobble=3), base, feather=1.5, grow=2)
        sunburst(cx, top + 2, 27, dark, rays=9)
        line([(x0 + 8, top + 18), (x1 - 8, top + 15)], dark, width=(1.0, 1.7), alpha=(120, 200), wobble=0.9)
        for (wx, wy, lit) in ((x0 + 26, top + 50, False), (cx, top + 46, True), (x1 - 26, top + 52, False), (x0 + 30, top + 110, False), (x1 - 30, top + 106, False)):
            win(wx, wy, 18, 20, lit)
    elif kind == "step2":
        stepped(cx, top, (96, 66, 40, 18), 12, base)
        stripes(cx - 30, cx + 30, top - 34, top + 58, dark, 5)
        zigzag(x0 + 12, x1 - 12, top + 76, 5, dark, n=13)
        for (wx, wy, lit, arch) in ((x0 + 30, top + 110, True, False), (cx, top + 104, False, True), (x1 - 30, top + 112, False, False), (x0 + 32, top + 170, False, False), (x1 - 32, top + 176, False, False), (cx - 4, top + 232, False, False), (x1 - 30, top + 240, True, False)):
            win(wx, wy, 17, 21, lit, arch)
    elif kind == "round":
        stepped(cx, top, (66, 40), 13, base)
        rm = C.soft_mask(C.blob(cx, top + 32, 13, 13, k=14, rough=0.1), feather=0.8, grow=1)
        fill(rm, WIN_L, direction=0, spread=20, n=300, length=(3, 8), alpha=(190, 255), dot=(0.8, 1.6))
        line([(cx - 13, top + 32), (cx + 13, top + 30)], dark, width=(0.6, 1.0), alpha=(100, 180), wobble=0.4)
        line([(cx + 1, top + 19), (cx - 1, top + 45)], dark, width=(0.6, 1.0), alpha=(100, 180), wobble=0.4)
        for (wx, wy, lit) in ((x0 + 26, top + 78, False), (x1 - 26, top + 84, False), (x0 + 30, top + 140, False), (x1 - 28, top + 136, False)):
            win(wx, wy, 17, 21, lit)
        # 窗台上一只猫（剪影，尾巴翘着）
        kx, ky = x1 - 26, top + 74
        km = C.soft_mask(C.blob(kx, ky, 8, 5, k=10, rough=0.15), feather=0.6, grow=1)
        fill(km, BLACK, direction=0, spread=20, n=90, length=(2, 6), alpha=(200, 255), dot=(0.7, 1.4))
        hm = C.soft_mask(C.blob(kx + 7, ky - 4, 4, 4, k=8, rough=0.1), feather=0.5, grow=1)
        fill(hm, BLACK, direction=0, spread=20, n=40, length=(1, 4), alpha=(200, 255), dot=(0.6, 1.2))
        for ex in (-2, 2):
            line([(kx + 7 + ex, ky - 7), (kx + 7 + ex * 1.5, ky - 11)], BLACK, width=(0.8, 1.2), alpha=(200, 255))
        line(C.catmull([(kx - 7, ky), (kx - 13, ky - 4), (kx - 12, ky - 12)], per=8), BLACK, width=(1.0, 1.6), alpha=(200, 255), wobble=0.4)
    elif kind == "flag":
        block(C.quad(cx - 16, top - 16, cx + 16, top + 6, wobble=2.5), base, feather=1.5, grow=2)
        stripes(x0 + 12, x1 - 12, top + 8, top + 52, dark, 6)
        line([(cx, top - 16), (cx + 2, top - 56)], (120, 110, 100), width=(0.9, 1.5), alpha=(150, 230), wobble=0.5)
        fm = C.soft_mask([(cx + 2, top - 56), (cx + 26, top - 48), (cx + 3, top - 40)], feather=0.8, grow=1)
        fill(fm, (222, 74, 62), direction=0, spread=10, n=120, length=(2, 6), alpha=(190, 255), dot=(0.8, 1.5))
        for (wx, wy, lit, arch) in ((x0 + 28, top + 84, False, True), (x1 - 28, top + 80, False, True), (x0 + 30, top + 148, True, False), (x1 - 30, top + 152, False, False), (cx, top + 208, False, False)):
            win(wx, wy, 17, 21, lit, arch)
    door(cx + random.uniform(-10, 10), STREET)

# ── 电线杆 + 电线 + 两只鸟 ────────────────────────────────
PX0 = 330
line([(PX0, STREET + 2), (PX0 + 2, STREET - 250)], (110, 92, 78), width=(1.6, 2.6), alpha=(170, 240), wobble=0.5)
line([(PX0 - 16, STREET - 236), (PX0 + 18, STREET - 238)], (110, 92, 78), width=(1.4, 2.2), alpha=(170, 240), wobble=0.5)
wire = C.catmull([(PX0 - 14, STREET - 236), (200, STREET - 214), (110, STREET - 232)], per=14)
line(wire, (120, 108, 100), width=(0.7, 1.1), alpha=(120, 200), wobble=0.5)
wire2 = C.catmull([(PX0 + 16, STREET - 238), (470, STREET - 212), (600, STREET - 232), (720, STREET - 220)], per=14)
line(wire2, (120, 108, 100), width=(0.7, 1.1), alpha=(120, 200), wobble=0.5)
for (bx, by) in ((236, STREET - 218), (262, STREET - 214)):
    bm = C.soft_mask(C.blob(bx, by - 6, 7, 5, k=10, rough=0.15), feather=0.5, grow=1)
    fill(bm, BLACK, direction=0, spread=20, n=70, length=(2, 5), alpha=(200, 255), dot=(0.7, 1.4))
    hm = C.soft_mask(C.blob(bx + 6, by - 10, 3.5, 3.5, k=8, rough=0.1), feather=0.4, grow=0)
    fill(hm, BLACK, direction=0, spread=20, n=30, length=(1, 3), alpha=(200, 255), dot=(0.6, 1.2))
    line([(bx + 9, by - 10), (bx + 13, by - 9)], (236, 160, 60), width=(0.8, 1.2), alpha=(200, 255))

# ── 诺福克松（歪一点）───────────────────────────────────
TX = 752
trunk = C.catmull([(TX, STREET + 2), (TX + 3, STREET - 180), (TX - 2, STREET - 370)], per=10)
line(trunk, (96, 74, 56), width=(1.6, 2.6), alpha=(170, 240), wobble=0.5)
for i, y in enumerate(range(STREET - 360, STREET - 50, 26)):
    wdt = 9 + i * 4.4 + random.uniform(-3, 3)
    tri = C.soft_mask([(TX - wdt, y + 20), (TX + random.uniform(-3, 3), y), (TX + wdt, y + 20)], feather=1.4, grow=2)
    fill(tri, random.choice(((62, 98, 66), (74, 112, 74), (54, 88, 60))), direction=0, spread=25, n=int(60 + wdt * 8), length=(3, 9), alpha=(150, 235), dot=(0.9, 1.8))

# ── 老爷车（Napier 周末满街跑的那种圆头车）──────────────────
CX, CY = 590, STREET + 92
bodym = C.soft_mask([(CX - 44, CY), (CX - 40, CY - 16), (CX - 22, CY - 20), (CX - 14, CY - 34), (CX + 16, CY - 34), (CX + 24, CY - 20), (CX + 44, CY - 16), (CX + 46, CY)], feather=1.2, grow=2)
fill(bodym, (214, 78, 70), direction=0, spread=12, n=900, length=(5, 14), alpha=(180, 250), dot=(0.9, 1.8))
wm = C.soft_mask(C.quad(CX - 10, CY - 31, CX + 12, CY - 21, wobble=1), feather=0.6, grow=1)
fill(wm, (222, 234, 244), direction=0, spread=10, n=120, length=(2, 6), alpha=(190, 255), dot=(0.7, 1.4))
for wx in (CX - 26, CX + 28):
    wl = C.soft_mask(C.blob(wx, CY + 1, 9, 9, k=12, rough=0.08), feather=0.6, grow=1)
    fill(wl, BLACK, direction=0, spread=20, n=140, length=(2, 6), alpha=(200, 255), dot=(0.7, 1.4))
    hub = C.soft_mask(C.blob(wx, CY + 1, 3.5, 3.5, k=8, rough=0.1), feather=0.4, grow=0)
    fill(hub, (230, 226, 216), direction=0, spread=20, n=30, length=(1, 3), alpha=(200, 255), dot=(0.6, 1.2))
line([(CX + 46, CY - 8), (CX + 52, CY - 8)], (250, 226, 120), width=(1.6, 2.4), alpha=(200, 255))  # 车灯
for k in range(3):  # 尾气小圈
    ex, ey = CX - 52 - k * 12, CY - 6 - k * 5
    circ = [(ex + math.cos(t) * (3 + k), ey + math.sin(t) * (3 + k)) for t in np.linspace(0, 2 * math.pi, 14)]
    line(circ, (180, 176, 184), width=(0.6, 1.0), alpha=(70, 140), wobble=0.4)

# ── 她：黄雨衣小人，影子是豹 ──────────────────────────────
PX, PY = 300, STREET + 98
shb = C.soft_mask(C.blob(PX - 64, PY + 5, 60, 14, k=14, rough=0.12), feather=3, grow=0)
fill(shb, (104, 100, 104), direction=0, spread=10, n=900, length=(6, 16), alpha=(90, 160), dot=(1.0, 2.0))
shh = C.soft_mask(C.blob(PX - 126, PY - 3, 17, 11, k=12, rough=0.1), feather=2.5, grow=0)
fill(shh, (104, 100, 104), direction=0, spread=10, n=340, length=(4, 10), alpha=(90, 160), dot=(1.0, 2.0))
for ex in (-10, 4):
    ear = C.soft_mask([(PX - 126 + ex - 5, PY - 11), (PX - 126 + ex, PY - 22), (PX - 126 + ex + 5, PY - 11)], feather=1.5, grow=0)
    fill(ear, (104, 100, 104), direction=0, spread=10, n=80, length=(2, 6), alpha=(90, 160), dot=(0.9, 1.7))
line(C.catmull([(PX - 6, PY + 5), (PX + 18, PY + 12), (PX + 42, PY + 3), (PX + 54, PY - 12)], per=10), (104, 100, 104), width=(2.2, 3.4), alpha=(90, 160), wobble=0.6)
coat = C.soft_mask(C.quad(PX - 12, PY - 46, PX + 12, PY - 3, wobble=2.5, lean=0.06), feather=1, grow=1)
fill(coat, (238, 198, 62), direction=90, spread=10, n=560, length=(4, 12), alpha=(190, 255), dot=(0.9, 1.7))
hood = C.soft_mask(C.blob(PX + 1, PY - 54, 12, 11, k=12, rough=0.12), feather=1, grow=1)
fill(hood, (238, 198, 62), direction=0, spread=20, n=280, length=(3, 8), alpha=(190, 255), dot=(0.9, 1.7))
face = C.soft_mask(C.blob(PX + 3, PY - 53, 6.5, 6.5, k=10, rough=0.1), feather=0.6, grow=0)
fill(face, (244, 226, 208), direction=0, spread=20, n=100, length=(2, 5), alpha=(190, 255), dot=(0.7, 1.4))
for ex in (0, 5):
    line([(PX + 1 + ex, PY - 54), (PX + 2 + ex, PY - 54)], BLACK, width=(0.9, 1.3), alpha=(220, 255))
line([(PX + 1, PY - 50), (PX + 4, PY - 48), (PX + 7, PY - 50)], BLACK, width=(0.6, 1.0), alpha=(180, 240), wobble=0.2)  # 笑
for lx in (-5, 5):
    line([(PX + lx, PY - 3), (PX + lx + (3 if lx > 0 else -3), PY + 4)], (60, 58, 70), width=(1.4, 2.2), alpha=(190, 255), wobble=0.3)
line([(PX - 12, PY - 32), (PX - 22, PY - 18)], (238, 198, 62), width=(1.7, 2.5), alpha=(190, 255), wobble=0.4)
line([(PX + 12, PY - 30), (PX + 20, PY - 40)], (238, 198, 62), width=(1.7, 2.5), alpha=(190, 255), wobble=0.4)  # 另一只手举着（指楼）
pk = C.soft_mask(C.blob(PX + 5, PY - 20, 3.6, 3.2, k=8, rough=0.1), feather=0.5, grow=0)
fill(pk, BLACK, direction=0, spread=20, n=40, length=(1, 3), alpha=(200, 255), dot=(0.6, 1.2))

img = C.paper_grain(img, 0.09)

# ── 字（一个一个歪着写，指线弯的）────────────────────────
wawa_big = C.font_cjk(50)      # 中文手写体：自动找（娃娃体 → 翩翩体 → 苹方 → Noto CJK …），想指定改 C.FONT_CJK
wawa_note = C.font_cjk(30)
wawa_s = C.font_cjk(27)
chalk = C.font_latin(52)       # 英文手写体：Chalkboard → Comic Sans → 退到中文字体
chalk_s = C.font_latin(24)

wtext("Napier", (126, 208), chalk, INK, rot=10, bounce=5, dot=(0.9, 1.7), density=0.3, alpha=(120, 210), solid_alpha=0.8)
wtext("art deco since 1931", (330, 232), chalk_s, INK, rot=8, bounce=3, dot=(0.7, 1.2), density=0.25, alpha=(110, 200), solid_alpha=0.85)

# 注记：字歪着，颜色跟楼走，指线弯的末端圈住
notes = [
    ("阶梯山墙", (118, 350), (166, tops["step"][2] - 20), PAL["mint"][1]),
    ("竖条纹", (232, 300), (270, tops["tower"][2] - 20), PAL["peach"][1]),
    ("太阳纹", (372, 400), (378, tops["sun"][2] - 6), PAL["cream"][1]),
    ("锯齿", (596, 372), (494, tops["step2"][2] + 76), PAL["lilac"][1]),
    ("窗台有猫", (452, 300), (626, tops["round"][2] + 74), PAL["sky"][1]),
]
for s, (tx, ty), tip, col in notes:
    wtext(s, (tx, ty), wawa_note, col, rot=7, bounce=3, dot=(0.6, 1.0), density=0.18, alpha=(110, 190), solid_alpha=0.95)
    bw = C.wobbly_text_width(s, wawa_note)
    squig((tx + bw / 2, ty + 34), tip, col, bend=22, ring=7)
wtext("影子是一只豹", (PX + 66, PY - 44), wawa_note, INK, rot=7, bounce=3, dot=(0.6, 1.0), density=0.18, alpha=(110, 190), solid_alpha=0.95)
squig((PX + 64, PY - 24), (PX - 60, PY + 4), INK, bend=14, ring=0)
wtext("一栋一个颜色，像一排书", (124, 840), wawa_s, INK, rot=6, bounce=3, dot=(0.6, 1.0), density=0.18, alpha=(110, 190), solid_alpha=0.95)

s1 = "它们在这儿站了九十五年。"
wtext(s1, ((W - C.wobbly_text_width(s1, wawa_big)) / 2, 1020), wawa_big, INK, rot=6, bounce=4, dot=(0.7, 1.3), density=0.28, alpha=(120, 200), solid_alpha=0.9)
for i, s2 in enumerate(("1931 年地震把整座城震平了，全城按当年最时髦的样子重盖，", "就定格在那一年。所以不是一坨，是一条街一条街排开的。")):
    wtext(s2, ((W - C.wobbly_text_width(s2, wawa_s)) / 2, 1100 + i * 42), wawa_s, INK, rot=5, bounce=2.5, dot=(0.6, 1.0), density=0.18, alpha=(100, 180), solid_alpha=0.95)

out = Path(__file__).resolve().parent / "example_street.png"
img.convert("RGB").save(out, quality=95)
print(out)
