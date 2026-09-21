"""crayon_lib — 蜡笔（油画棒）笔触库。每笔一条短线沿线撒颗粒点，羽化 mask 留毛边；字逐字歪着写；指线弯的。
依赖：Pillow、numpy。字体自动找（见下面 FONT_CJK / FONT_LATIN），也可以自己指定。"""
import glob as _glob
import math
import os as _os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 880, 1250
PAPER = (252, 251, 248)


def set_size(w, h):
    global W, H
    W, H = w, h


# ── 字体 ──────────────────────────────────────────────────
# 中文手写体：macOS 娃娃体 → 翩翩体 → 苹方 / 冬青黑 → Noto CJK（Linux）→ 微软雅黑 / 黑体（Windows）。
# 英文手写体：Chalkboard（macOS）→ Comic Sans → 退到中文字体。
# 都没有就用 PIL 默认字体（英文能显示，中文会缺）。想指定：C.FONT_CJK = "/path/to/font.ttf"，再 C.font_cjk(size)。

def _first_existing(cands):
    for c in cands:
        if c and _os.path.exists(c):
            return c
    return None


FONT_CJK = _first_existing(
    _glob.glob("/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/WawaSC-Regular.otf")
    + _glob.glob("/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/Hanzipen.ttc")
    + ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc",
       "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
       "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"])
FONT_LATIN = _first_existing(["/System/Library/Fonts/Supplemental/Chalkboard.ttc",
                              "/System/Library/Fonts/Supplemental/ChalkboardSE.ttc",
                              "/System/Library/Fonts/Supplemental/Comic Sans MS.ttf",
                              "C:/Windows/Fonts/comic.ttf"]) or FONT_CJK


def load_font(path, size):
    """指定路径加载；路径为空或打不开就退到 PIL 默认字体（不报错，中文会缺字形）。"""
    if path:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # 旧版 Pillow 的 load_default 不收 size
        return ImageFont.load_default()


def font_cjk(size):
    """中文手写体（注记、底句）。"""
    return load_font(FONT_CJK, size)


def font_latin(size):
    """英文手写体（标题）。"""
    return load_font(FONT_LATIN, size)

def soft_mask(polygon, feather=5, grow=4):
    """多边形 → 羽化 mask（L）。grow 让笔触稍微溢出边界，蜡笔就是不整齐的。"""
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.polygon(polygon, fill=255)
    if grow:
        m = m.filter(ImageFilter.MaxFilter(grow * 2 + 1))
    return m.filter(ImageFilter.GaussianBlur(feather))


def crayon(base, mask, color, *, direction=0, spread=18, n=2600, length=(18, 48),
           dot=(1.2, 2.6), alpha=(70, 150), jitter=14, coverage=1.0):
    """在 mask 内撒油画棒笔触：每笔一条短线，沿线撒带颗粒的小点。"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bbox = mask.getbbox()
    if not bbox:
        return base
    x0, y0, x1, y1 = bbox
    marr = np.asarray(mask, dtype=np.float32) / 255.0
    r, g, b = color
    count = int(n * coverage)
    tries = 0
    placed = 0
    while placed < count and tries < count * 6:
        tries += 1
        sx = random.uniform(x0, x1)
        sy = random.uniform(y0, y1)
        if marr[int(min(max(sy, 0), H - 1)), int(min(max(sx, 0), W - 1))] < 0.25:
            continue
        placed += 1
        ang = math.radians(direction + random.uniform(-spread, spread))
        L = random.uniform(*length)
        dx, dy = math.cos(ang), math.sin(ang)
        cr = max(0, min(255, r + random.randint(-jitter, jitter)))
        cg = max(0, min(255, g + random.randint(-jitter, jitter)))
        cb = max(0, min(255, b + random.randint(-jitter, jitter)))
        a_base = random.randint(*alpha)
        step = 1.6
        t = 0.0
        while t < L:
            px = sx + dx * t + random.uniform(-0.8, 0.8)
            py = sy + dy * t + random.uniform(-0.8, 0.8)
            rr = random.uniform(*dot)
            a = int(a_base * random.uniform(0.35, 1.0))
            d.ellipse((px - rr, py - rr, px + rr, py + rr), fill=(cr, cg, cb, a))
            t += step
    # 用羽化 mask 裁 alpha（边缘自然毛，不硬切）
    la = np.asarray(layer.split()[3], dtype=np.float32)
    la = (la * np.clip(marr * 1.15, 0, 1)).astype(np.uint8)
    layer.putalpha(Image.fromarray(la))
    return Image.alpha_composite(base, layer)


def poly_rect(x0, y0, x1, y1, wobble=6):
    pts = []
    for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        pts.append((x + random.uniform(-wobble, wobble), y + random.uniform(-wobble, wobble)))
    return pts


def blob(cx, cy, rx, ry, k=14, rough=0.18):
    pts = []
    for i in range(k):
        a = 2 * math.pi * i / k
        rr = 1 + random.uniform(-rough, rough)
        pts.append((cx + math.cos(a) * rx * rr, cy + math.sin(a) * ry * rr))
    return pts


def crayon_text(base, text, xy, font, color, *, dot=(1.0, 1.9), density=0.55, alpha=(150, 235), solid_alpha=0.72):
    """把字先渲成 mask，再在 mask 里撒颗粒——字也是蜡笔写的。"""
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).text(xy, text, font=font, fill=255)
    marr = np.asarray(m)
    ys, xs = np.nonzero(marr > 90)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # 实心底（半透明），让字先读得出来；颗粒叠在上面给蜡笔味
    solid = Image.new("RGBA", (W, H), color + (0,))
    solid.putalpha(Image.fromarray((marr * solid_alpha).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)))
    layer = Image.alpha_composite(layer, solid)
    d = ImageDraw.Draw(layer)
    idx = np.random.choice(len(xs), int(len(xs) * density), replace=False)
    r, g, b = color
    for i in idx:
        px, py = xs[i] + random.uniform(-0.7, 0.7), ys[i] + random.uniform(-0.7, 0.7)
        rr = random.uniform(*dot)
        d.ellipse((px - rr, py - rr, px + rr, py + rr),
                  fill=(r + random.randint(-10, 10), g + random.randint(-10, 10), b + random.randint(-10, 10), random.randint(*alpha)))
    return Image.alpha_composite(base, layer)


def paper_grain(img, strength=0.10):
    """纸纹：只在有色处轻轻调制亮度。"""
    arr = np.asarray(img).astype(np.float32)
    noise = np.random.normal(0, 1, (H, W)).astype(np.float32)
    noise = np.asarray(Image.fromarray(np.clip(noise * 40 + 128, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), dtype=np.float32)
    mod = 1 + (noise - 128) / 128 * strength
    colored = (np.abs(arr[..., :3] - np.array(PAPER, dtype=np.float32)).sum(axis=-1) > 18)[..., None]
    arr[..., :3] = np.where(colored, np.clip(arr[..., :3] * mod[..., None], 0, 255), arr[..., :3])
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def crayon_line(base, pts, color, *, width=(1.0, 2.0), alpha=(140, 230), wobble=0.9, step=1.4, jitter=10):
    """沿折线撒颗粒——画路线、轮廓、笔画。pts 是点列表。"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r, g, b = color
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        n = max(2, int(L / step))
        for t in np.linspace(0, 1, n):
            px = ax + (bx - ax) * t + random.uniform(-wobble, wobble)
            py = ay + (by - ay) * t + random.uniform(-wobble, wobble)
            rr = random.uniform(*width)
            d.ellipse((px - rr, py - rr, px + rr, py + rr),
                      fill=(max(0, min(255, r + random.randint(-jitter, jitter))),
                            max(0, min(255, g + random.randint(-jitter, jitter))),
                            max(0, min(255, b + random.randint(-jitter, jitter))), random.randint(*alpha)))
    return Image.alpha_composite(base, layer)


def catmull(points, per=14):
    """Catmull-Rom 平滑，手画的路线要弯。"""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(points[-1])
    return out


# ── 可爱/手抖工具：规整的是排版，歪的才是画 ───────────────

def mask_to_crayon(base, mask_img, color, *, dot=(0.8, 1.5), density=0.25, alpha=(120, 210), solid_alpha=0.9):
    """任意 L 蒙版 → 蜡笔（实心底 + 颗粒）。wobbly_text / 图章 / 贴纸都走这里。"""
    marr = np.asarray(mask_img)
    ys, xs = np.nonzero(marr > 90)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    solid = Image.new("RGBA", (W, H), color + (0,))
    solid.putalpha(Image.fromarray((marr * solid_alpha).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)))
    layer = Image.alpha_composite(layer, solid)
    d = ImageDraw.Draw(layer)
    if len(xs):
        idx = np.random.choice(len(xs), int(len(xs) * density), replace=False)
        r, g, b = color
        for i in idx:
            px, py = xs[i] + random.uniform(-0.7, 0.7), ys[i] + random.uniform(-0.7, 0.7)
            rr = random.uniform(*dot)
            d.ellipse((px - rr, py - rr, px + rr, py + rr),
                      fill=(r + random.randint(-10, 10), g + random.randint(-10, 10), b + random.randint(-10, 10), random.randint(*alpha)))
    return Image.alpha_composite(base, layer)


def wobbly_text(base, text, xy, font, color, *, rot=9, bounce=4, scale=(0.9, 1.12), kern=1.0, **kw):
    """一个字一个字写：每个字自己歪一点、上下跳一点、大小差一点。像手写不像排版。"""
    x, y = xy
    mask = Image.new("L", (W, H), 0)
    size = font.size
    for ch in text:
        if ch == " ":
            x += size * 0.35 * kern
            continue
        s = random.uniform(*scale)
        f = font.font_variant(size=max(8, int(size * s)))
        pad = int(size * 1.2)
        tile = Image.new("L", (pad * 2, pad * 2), 0)
        ImageDraw.Draw(tile).text((pad * 0.5, pad * 0.35), ch, font=f, fill=255)
        tile = tile.rotate(random.uniform(-rot, rot), resample=Image.BICUBIC, expand=False)
        adv = f.getlength(ch)
        mask.paste(tile, (int(x - pad * 0.5), int(y + random.uniform(-bounce, bounce) - pad * 0.35)), tile)
        x += adv * kern + random.uniform(-1, 2)
    return mask_to_crayon(base, mask, color, **kw)


def wobbly_text_width(text, font, kern=1.0):
    return sum((font.size * 0.35 * kern) if ch == " " else font.getlength(ch) * kern + 0.5 for ch in text)


def squiggle(base, a, b, color, *, bend=18, width=(0.7, 1.2), alpha=(100, 180), ring=6):
    """手画的弯指线：从 a 弯到 b，末端一个小圈圈住目标。"""
    mx, my = (a[0] + b[0]) / 2 + random.uniform(-bend, bend), (a[1] + b[1]) / 2 + random.uniform(-bend, bend)
    pts = catmull([a, (mx, my), b], per=16)
    base = crayon_line(base, pts, color, width=width, alpha=alpha, wobble=0.6)
    if ring:
        circ = [(b[0] + math.cos(t) * ring * random.uniform(0.85, 1.15), b[1] + math.sin(t) * ring * random.uniform(0.85, 1.15)) for t in np.linspace(0, 2 * math.pi + 0.6, 26)]
        base = crayon_line(base, circ, color, width=width, alpha=alpha, wobble=0.5)
    return base


def quad(x0, y0, x1, y1, wobble=8, lean=0.0):
    """歪的四边形：四角各自乱，还能整体往一边倾（lean 是顶边相对底边的横向偏移比例）。"""
    dx = (x1 - x0) * lean
    return [(x0 + dx + random.uniform(-wobble, wobble), y0 + random.uniform(-wobble, wobble)),
            (x1 + dx + random.uniform(-wobble, wobble), y0 + random.uniform(-wobble, wobble)),
            (x1 + random.uniform(-wobble, wobble), y1 + random.uniform(-wobble, wobble)),
            (x0 + random.uniform(-wobble, wobble), y1 + random.uniform(-wobble, wobble))]


def scribble(base, mask, color, *, n=8, length=(20, 60), direction=-35, width=(1.0, 1.8), alpha=(40, 100)):
    """色块上随手划几道斜杠——蜡笔涂过的痕迹，让平的块不平。"""
    bbox = mask.getbbox()
    if not bbox:
        return base
    x0, y0, x1, y1 = bbox
    marr = np.asarray(mask, dtype=np.float32) / 255.0
    for _ in range(n * 4):
        if n <= 0:
            break
        sx, sy = random.uniform(x0, x1), random.uniform(y0, y1)
        if marr[int(min(max(sy, 0), H - 1)), int(min(max(sx, 0), W - 1))] < 0.5:
            continue
        L = random.uniform(*length)
        a = math.radians(direction + random.uniform(-10, 10))
        ex, ey = min(max(sx + math.cos(a) * L, x0), x1), min(max(sy + math.sin(a) * L, y0), y1)  # 不出色块
        base = crayon_line(base, [(sx, sy), (ex, ey)], color, width=width, alpha=alpha, wobble=0.8)
        n -= 1
    return base
