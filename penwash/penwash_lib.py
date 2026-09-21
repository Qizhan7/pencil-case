"""钢笔淡彩（pen & wash）引擎——细钢笔线抖着走、暗部排线、几块水彩故意不贴线、米色纸留白。

三种笔：
  pen_path   钢笔线：沿平滑曲线一小段一小段画，线宽随手压变化，偶尔断墨
  hatch      排线：mask 内铺一组平行短线做暗部（灯罩/瓶身那种竖线、斜线）
  wash       淡彩：不规则色块 + 偏移 + 羽化 + 边缘沉淀，颜色故意跑出线稿

跟油画棒/蜡笔那种堆颗粒的画法是两种手：这个是线 + 透明水。
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 900, 1100
PAPER = (243, 236, 221)
PAPER_VINTAGE = (234, 222, 196)
INK = (58, 44, 36)          # 深褐钢笔墨
INK_SOFT = (96, 78, 66)     # 淡一点的墨（排线用）

# 手写感的中文字体。默认找 macOS 的「娃娃体」（WawaSC），找不到依次退到苹方 / 冬青黑 / Noto，都没有就用 PIL 默认字体。
# 想用别的字体：P.FONT = "/path/to/font.ttf"，或者给 vertical_text / pen_text 传 font_path。
import glob as _glob
import os as _os


def _find_font():
    cands = []
    cands += _glob.glob("/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/WawaSC-Regular.otf")
    cands += ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc",
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
              "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]
    for c in cands:
        if _os.path.exists(c):
            return c
    return None


FONT = _find_font()
FONT_WAWA = FONT  # 兼容旧名


def _load_font(font_path, size):
    path = font_path or FONT
    if path:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def set_size(w, h):
    global W, H
    W, H = w, h


# ---------- 录制：一笔一笔看着画出来 ----------
# record_start(path) 之后，每次 pen_path / wash / speckle / 文字落下去都会往 ffmpeg 喂一帧（every 笔一帧），
# record_stop() 收尾。默认关，不影响任何现有脚本。录制需要系统里有 ffmpeg。
_REC = None


class _Recorder:
    def __init__(self, path, fps=30, every=2, hold=45, scale=1.0):
        self.path, self.fps, self.every, self.hold, self.scale = path, fps, every, hold, scale
        self.count = 0
        self.frames = 0
        self.proc = None
        self.size = None

    def _open(self, w, h):
        import subprocess
        self.size = (w, h)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
               "-r", str(self.fps), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
               "-movflags", "+faststart", self.path]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write(self, img, times=1):
        rgb = img.convert("RGB")
        if self.scale != 1.0:
            rgb = rgb.resize((int(rgb.width * self.scale), int(rgb.height * self.scale)), Image.BILINEAR)
        w, h = rgb.width - rgb.width % 2, rgb.height - rgb.height % 2   # yuv420p 要偶数边
        if (w, h) != (rgb.width, rgb.height):
            rgb = rgb.crop((0, 0, w, h))
        if self.proc is None:
            self._open(w, h)
        data = rgb.tobytes()
        for _ in range(times):
            self.proc.stdin.write(data)
        self.frames += times
        self.last = rgb

    def snap(self, img, weight=1):
        self.count += weight
        if self.count < self.every:
            return
        self.count = 0
        self.write(img)

    def close(self):
        if self.proc is None:
            return
        if self.hold and getattr(self, "last", None) is not None:
            data = self.last.tobytes()
            for _ in range(self.hold):
                self.proc.stdin.write(data)
            self.frames += self.hold
        self.proc.stdin.close()
        self.proc.wait()
        self.proc = None


def record_start(path, fps=30, every=2, hold=45, scale=1.0):
    """开始录制。every：每几笔一帧（刺、排线这种小线多的画调大）；hold：结尾停几帧；scale：视频缩放。"""
    global _REC
    _REC = _Recorder(path, fps=fps, every=every, hold=hold, scale=scale)
    return _REC


def record_snap(img, weight=None):
    """脚本里手动打一帧（比如一个物件画完想停一下：weight 传大数）。"""
    if _REC:
        _REC.snap(img, weight if weight is not None else _REC.every)


def record_hold(img, frames=15):
    """停在当前画面几帧。"""
    if _REC:
        _REC.write(img, times=frames)


def record_stop():
    global _REC
    if _REC:
        _REC.close()
        n, path = _REC.frames, _REC.path
        _REC = None
        return n, path
    return 0, None


def _snap(img, weight=1):
    if _REC:
        _REC.snap(img, weight)


# ---------- 纸 ----------
def paper(w=None, h=None, color=PAPER, grain=9, fibers=900, vintage=False):
    """米色纸：细噪 + 随机短纤维（纸浆纹）。
    vintage=True：更暖更深的旧纸——低频斑驳 + 粗颗粒 + 更多更深的纤维（像加了旧照片滤镜）。"""
    w = w or W
    h = h or H
    if vintage and color == PAPER:
        color = PAPER_VINTAGE
    arr = np.zeros((h, w, 3), dtype=np.float32)
    arr[:] = color
    if vintage:
        # 低频斑驳：旧纸受潮不均
        rs = np.random.RandomState(random.randint(0, 10 ** 6))
        small = rs.uniform(-1, 1, (max(2, h // 90), max(2, w // 90))).astype(np.float32)
        blotch = np.asarray(Image.fromarray(((small + 1) * 127.5).astype(np.uint8)).resize((w, h), Image.BICUBIC), dtype=np.float32) / 127.5 - 1
        arr += blotch[:, :, None] * 7.0
        # 粗颗粒：大颗一点的暗点
        coarse = rs.uniform(0, 1, (h // 2, w // 2)).astype(np.float32)
        coarse = np.asarray(Image.fromarray((coarse * 255).astype(np.uint8)).resize((w, h), Image.NEAREST), dtype=np.float32) / 255
        arr -= (coarse > 0.93)[:, :, None] * rs.uniform(8, 22)
        grain = max(grain, 12)
        fibers = max(fibers, 1150)
    noise = np.random.normal(0, grain, (h, w, 1)).astype(np.float32)
    arr += noise
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    palette = [(255, 252, 244, 90), (222, 212, 192, 70), (235, 228, 210, 80)]
    if vintage:
        palette = [(250, 244, 228, 70), (214, 202, 178, 60), (226, 214, 190, 64), (196, 182, 156, 34)]
    for _ in range(fibers):
        x = random.uniform(0, w)
        y = random.uniform(0, h)
        ang = random.uniform(0, math.pi)
        L = random.uniform(3, 11 if vintage else 14)
        c = random.choice(palette)
        d.line([(x, y), (x + math.cos(ang) * L, y + math.sin(ang) * L)], fill=c, width=1)
    if _REC:
        _REC.write(img, times=30)
    return img


# ---------- 几何 ----------
def catmull(points, per=16, closed=False):
    """Catmull-Rom 平滑，手画的线要弯。"""
    pts = list(points)
    if closed:
        pts = [pts[-1]] + pts + [pts[0], pts[1]]
    else:
        pts = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(tuple(pts[-2]))
    return out


def ellipse_pts(cx, cy, rx, ry, n=48, rough=0.0, rot=0.0, start=0.0, end=2 * math.pi):
    pts = []
    for i in range(n + 1):
        a = start + (end - start) * i / n
        r1 = 1 + random.uniform(-rough, rough)
        x = math.cos(a) * rx * r1
        y = math.sin(a) * ry * r1
        if rot:
            x, y = x * math.cos(rot) - y * math.sin(rot), x * math.sin(rot) + y * math.cos(rot)
        pts.append((cx + x, cy + y))
    return pts


def blob(cx, cy, rx, ry, k=14, rough=0.14):
    return ellipse_pts(cx, cy, rx, ry, n=k, rough=rough)


def poly_mask(polygon, feather=0, grow=0, shrink=0):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in polygon], fill=255)
    if grow:
        m = m.filter(ImageFilter.MaxFilter(grow * 2 + 1))
    if shrink:
        m = m.filter(ImageFilter.MinFilter(shrink * 2 + 1))
    if feather:
        m = m.filter(ImageFilter.GaussianBlur(feather))
    return m


def _smooth_noise(n, scale=0.5, octaves=3):
    """一维平滑噪声，做抖线用。"""
    v = np.zeros(n)
    amp = 1.0
    freq = max(2, n // 40)
    for _ in range(octaves):
        knots = np.random.uniform(-1, 1, freq + 2)
        xs = np.linspace(0, freq, n)
        v += amp * np.interp(xs, np.arange(freq + 2), knots)
        amp *= 0.5
        freq *= 2
    return v * scale


# ---------- 钢笔 ----------
def pen_path(base, pts, *, ink=INK, width=(0.8, 1.6), alpha=(150, 235), wobble=1.1,
             step=2.0, gaps=0.05, gap_len=(2, 6), smooth=True, per=12, overdraw=0,
             jitter=0.0, overshoot=0.0, nib=False, shift=(0, 0)):
    """钢笔线：沿路径每 step 像素画一小段，线宽随手压变化，偶尔断墨。
    overdraw>0 时再描 overdraw 遍（更淡、更抖、整体偏 1–3px）——手绘会重复描线。
    jitter: 高频小抖（每段 ±jitter px），让线"硬"一点像钢笔不像铅笔。
    overshoot: 折线（smooth=False）每段末尾画过头的像素数，角上出头。
    nib: 起笔加重（钢笔落纸那一点墨）。
    shift: 整条线平移。"""
    if len(pts) < 2:
        return base
    pts = [(x + shift[0], y + shift[1]) for x, y in pts]
    if overshoot and not smooth:
        ext = []
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            L = math.hypot(x1 - x0, y1 - y0) or 1
            o = random.uniform(overshoot * 0.4, overshoot)
            ext.append((x0, y0))
            ext.append((x1 + (x1 - x0) / L * o, y1 + (y1 - y0) / L * o))
        pts = ext
    path = catmull(pts, per=per) if smooth and len(pts) > 2 else list(pts)
    # 等距重采样
    # 等距重采样：carry 是距上一个采样点已经走过的距离，跨小段累积。
    # （余量必须跨段累积：输入点比 step 还密时——闭合 blob、per 大的圆——否则一个采样点都放不下，整条线画成几根直线）
    seg = []
    carry = 0.0
    seg.append(path[0])
    for i in range(1, len(path)):
        x0, y0 = path[i - 1]
        x1, y1 = path[i]
        L = math.hypot(x1 - x0, y1 - y0)
        if L == 0:
            continue
        pos = 0.0
        while pos + (step - carry) <= L:
            pos += step - carry
            carry = 0.0
            t = pos / L
            seg.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
        carry += L - pos
    n = len(seg)
    if n < 2:
        return base
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    nx = _smooth_noise(n, wobble)
    ny = _smooth_noise(n, wobble)
    wn = _smooth_noise(n, 1.0)
    w_lo, w_hi = width
    a_lo, a_hi = alpha
    in_gap = 0
    for i in range(1, n):
        if in_gap:
            in_gap -= 1
            continue
        if random.random() < gaps:
            in_gap = random.randint(*gap_len)
            continue
        jx0 = random.uniform(-jitter, jitter) if jitter else 0.0
        jy0 = random.uniform(-jitter, jitter) if jitter else 0.0
        jx1 = random.uniform(-jitter, jitter) if jitter else 0.0
        jy1 = random.uniform(-jitter, jitter) if jitter else 0.0
        x0, y0 = seg[i - 1][0] + nx[i - 1] + jx0, seg[i - 1][1] + ny[i - 1] + jy0
        x1, y1 = seg[i][0] + nx[i] + jx1, seg[i][1] + ny[i] + jy1
        pressure = 0.5 + 0.5 * wn[i]
        wv = w_lo + (w_hi - w_lo) * pressure
        a = int(a_lo + (a_hi - a_lo) * pressure * random.uniform(0.85, 1.0))
        if nib and i <= 3:          # 起笔那一点墨
            wv *= 1.35
            a = min(255, int(a * 1.1))
        if nib and i >= n - 3:      # 收笔提起来，变细变淡
            wv *= 0.7
            a = int(a * 0.75)
        d.line([(x0, y0), (x1, y1)], fill=ink + (a,), width=max(1, int(round(wv))))
        if wv > 1.25 and random.random() < 0.5:  # 粗一点的地方补个圆头
            d.ellipse([x1 - wv / 2, y1 - wv / 2, x1 + wv / 2, y1 + wv / 2], fill=ink + (a,))
    out = Image.alpha_composite(base, layer)
    _snap(out)
    for _ in range(overdraw):
        sh = (random.uniform(-2.2, 2.2), random.uniform(-2.2, 2.2))
        out = pen_path(out, [(x - shift[0], y - shift[1]) for x, y in pts], ink=ink, width=(w_lo * 0.75, w_hi * 0.75), alpha=(a_lo // 2, a_hi // 2),
                       wobble=wobble * 1.5, step=step, gaps=gaps * 2.5, smooth=smooth, per=per, overdraw=0,
                       jitter=jitter, overshoot=0.0, nib=False, shift=(shift[0] + sh[0], shift[1] + sh[1]))
    return out


def pen_ellipse(base, cx, cy, rx, ry, *, rough=0.02, rot=0.0, n=40, **kw):
    pts = ellipse_pts(cx, cy, rx, ry, n=n, rough=rough, rot=rot)
    return pen_path(base, pts, smooth=False, **kw)


def pen_arc(base, cx, cy, rx, ry, start_deg, end_deg, *, rough=0.02, n=24, **kw):
    pts = ellipse_pts(cx, cy, rx, ry, n=n, rough=rough, start=math.radians(start_deg), end=math.radians(end_deg))
    return pen_path(base, pts, smooth=False, **kw)


# ---------- 排线 ----------
def hatch(base, mask, *, angle=90, spacing=4.0, ink=INK_SOFT, width=(0.6, 1.2), alpha=(90, 170),
          wobble=0.7, jitter=1.5, length=(0.6, 1.0), density=1.0, cross=False):
    """mask 内铺平行短线。angle 90 = 竖线，0 = 横线。length 是每条线相对可用长度的比例区间。
    density<1 随机漏掉一些线；cross=True 再铺一层 +60° 的交叉排线。"""
    bbox = mask.getbbox()
    if not bbox:
        return base
    x0, y0, x1, y1 = bbox
    marr = np.asarray(mask, dtype=np.float32) / 255.0
    ang = math.radians(angle)
    dx, dy = math.cos(ang), math.sin(ang)          # 线方向
    px, py = -dy, dx                                # 垂直方向（排线推进方向）
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    diag = math.hypot(x1 - x0, y1 - y0)
    out = base
    k = -diag / 2
    while k <= diag / 2:
        k += spacing * random.uniform(0.75, 1.3)
        if random.random() > density:
            continue
        # 这条线的中心
        ox, oy = cx + px * k, cy + py * k
        # 沿线方向扫描找在 mask 内的段
        segs = []
        cur = None
        t = -diag / 2
        while t <= diag / 2:
            x, y = ox + dx * t, oy + dy * t
            inside = 0 <= x < W and 0 <= y < H and marr[int(y), int(x)] > 0.5
            if inside and cur is None:
                cur = t
            if (not inside or t + 2 > diag / 2) and cur is not None:
                segs.append((cur, t))
                cur = None
            t += 2
        for (ta, tb) in segs:
            Lfull = tb - ta
            if Lfull < 3:
                continue
            frac = random.uniform(*length)
            L = Lfull * frac
            ta2 = ta + random.uniform(0, Lfull - L)
            tb2 = ta2 + L
            j1 = random.uniform(-jitter, jitter)
            j2 = random.uniform(-jitter, jitter)
            p1 = (ox + dx * ta2 + px * j1, oy + dy * ta2 + py * j1)
            p2 = (ox + dx * tb2 + px * j2, oy + dy * tb2 + py * j2)
            mid = ((p1[0] + p2[0]) / 2 + random.uniform(-wobble * 2, wobble * 2),
                   (p1[1] + p2[1]) / 2 + random.uniform(-wobble * 2, wobble * 2))
            out = pen_path(out, [p1, mid, p2], ink=ink, width=width, alpha=alpha, wobble=wobble,
                           step=2.5, gaps=0.03, smooth=True, per=6)
    if cross:
        out = hatch(out, mask, angle=angle + 60, spacing=spacing * 1.4, ink=ink, width=width,
                    alpha=(alpha[0] // 2, alpha[1] // 2), wobble=wobble, jitter=jitter, length=length,
                    density=density * 0.8, cross=False)
    return out


# ---------- 淡彩 ----------
_TEX_CACHE = {}


def _wc_texture(scale=36, seed=None):
    """低频平滑噪声（0..1），做水彩不均匀的水痕。"""
    key = (W, H, scale, seed)
    if key in _TEX_CACHE:
        return _TEX_CACHE[key]
    rs = np.random.RandomState(seed if seed is not None else random.randint(0, 10 ** 6))
    small = rs.uniform(0, 1, (max(2, H // scale), max(2, W // scale))).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    fine = rs.uniform(0, 1, (max(2, H // 6), max(2, W // 6))).astype(np.float32)
    im2 = Image.fromarray((fine * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    arr = 0.7 * np.asarray(im, dtype=np.float32) / 255 + 0.3 * np.asarray(im2, dtype=np.float32) / 255
    _TEX_CACHE[key] = arr
    return arr


def wash(base, polygon, color, *, alpha=(70, 120), offset=(3, 2), feather=2.5, grow=0, shrink=0,
         layers=2, edge=0.35, edge_width=3, rough=0.0, k=None, texture=0.45):
    """水彩色块：多边形 → 偏移 + 羽化 → 半透明填色；边缘再压一圈稍深（颜料沉淀）。
    offset 让颜色故意不贴线稿；layers 叠几层（每层再随机偏一点，水彩堆积的感觉）；
    texture 0..1 用低频噪声调制 alpha，做水痕不均匀。"""
    out = base
    poly = [tuple(p) for p in polygon]
    if rough and k:
        # 用 blob 打散边缘：把多边形每点向外随机抖
        poly = [(x + random.uniform(-rough, rough), y + random.uniform(-rough, rough)) for x, y in poly]
    for i in range(layers):
        ox = offset[0] + random.uniform(-2, 2) * i
        oy = offset[1] + random.uniform(-2, 2) * i
        p = [(x + ox, y + oy) for x, y in poly]
        m = poly_mask(p, feather=feather, grow=grow, shrink=shrink)
        a = random.randint(*alpha) // (1 + i * 0.6)
        marr = np.asarray(m, dtype=np.float32) / 255.0
        if texture:
            tex = _wc_texture(seed=random.randint(0, 10 ** 6))
            marr = marr * ((1 - texture) + texture * tex * 1.6)
            marr = np.clip(marr, 0, 1)
        lay = Image.new("RGBA", (W, H), color + (0,))
        lay.putalpha(Image.fromarray((marr * a).astype(np.uint8)))
        out = Image.alpha_composite(out, lay)
        if edge and i == 0:
            inner = m.filter(ImageFilter.MinFilter(edge_width * 2 + 1))
            ring = Image.fromarray(np.clip(np.asarray(m, dtype=np.int16) - np.asarray(inner, dtype=np.int16), 0, 255).astype(np.uint8))
            ring = ring.filter(ImageFilter.GaussianBlur(1.2))
            dark = tuple(max(0, int(c * (1 - 0.18))) for c in color)
            lay2 = Image.new("RGBA", (W, H), dark + (0,))
            lay2.putalpha(ring.point(lambda v, a=int(a * edge): int(v * a / 255)))
            out = Image.alpha_composite(out, lay2)
    _snap(out, weight=10 ** 6)
    return out


def wash_mask(base, mask, color, *, alpha=(70, 120), edge=0.3, edge_width=3):
    """已有 L 蒙版直接上淡彩。"""
    a = random.randint(*alpha)
    lay = Image.new("RGBA", (W, H), color + (0,))
    lay.putalpha(mask.point(lambda v: int(v * a / 255)))
    out = Image.alpha_composite(base, lay)
    if edge:
        inner = mask.filter(ImageFilter.MinFilter(edge_width * 2 + 1))
        ring = Image.fromarray(np.clip(np.asarray(mask, dtype=np.int16) - np.asarray(inner, dtype=np.int16), 0, 255).astype(np.uint8))
        dark = tuple(max(0, int(c * 0.82)) for c in color)
        lay2 = Image.new("RGBA", (W, H), dark + (0,))
        lay2.putalpha(ring.point(lambda v: int(v * a * edge / 255)))
        out = Image.alpha_composite(out, lay2)
    _snap(out, weight=10 ** 6)
    return out


def speckle(base, polygon, color, *, n=60, r=(0.6, 1.6), alpha=(60, 140)):
    """色块上撒点（杯座、桌面那种一圈小点）。"""
    m = poly_mask(polygon)
    marr = np.asarray(m) > 128
    bbox = m.getbbox()
    if not bbox:
        return base
    x0, y0, x1, y1 = bbox
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    placed = 0
    tries = 0
    while placed < n and tries < n * 8:
        tries += 1
        x, y = random.uniform(x0, x1), random.uniform(y0, y1)
        if not marr[int(min(y, H - 1)), int(min(x, W - 1))]:
            continue
        rr = random.uniform(*r)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=color + (random.randint(*alpha),))
        placed += 1
    out = Image.alpha_composite(base, lay)
    _snap(out, weight=10 ** 6)
    return out


# ---------- 字 ----------
def vertical_text(base, text, xy, *, size=26, ink=INK, alpha=200, gap=4, rot=3, font_path=None):
    """竖写一列小字（右侧署名那种）。逐字轻微旋转。"""
    font = _load_font(font_path, size)
    x, y = xy
    out = base
    for ch in text:
        lay = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.text((size // 2, size // 2), ch, font=font, fill=ink + (alpha,))
        lay = lay.rotate(random.uniform(-rot, rot), resample=Image.BICUBIC, center=(size, size))
        out.alpha_composite(lay, (int(x - size // 2 + random.uniform(-1, 1)), int(y - size // 2)))
        y += size + gap
        _snap(out, weight=10 ** 6)
    return out


def pen_text(base, text, xy, *, size=22, ink=INK, alpha=190, rot=2, font_path=None):
    font = _load_font(font_path, size)
    x, y = xy
    out = base
    for ch in text:
        w = font.getlength(ch)
        lay = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.text((size // 2, size // 2), ch, font=font, fill=ink + (alpha,))
        lay = lay.rotate(random.uniform(-rot, rot), resample=Image.BICUBIC, center=(size, size))
        out.alpha_composite(lay, (int(x - size // 2), int(y - size // 2 + random.uniform(-1.5, 1.5))))
        x += w + 1
        _snap(out, weight=10 ** 6)
    return out
