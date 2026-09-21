---
name: crayon
description: 「蜡笔」——用 Python 手搓油画棒/蜡笔风格的画（一笔一笔撒颗粒，不是滤镜、不是生图）。触发词：蜡笔、油画棒、crayon、画成蜡笔、蜡笔风、蜡笔地图、手帐蜡笔
---

# 蜡笔 —— 油画棒质感，Python 撒出来的

不是滤镜，不是生图模型。每一道笔触是一条短线，沿线撒几十个小圆点——颜色抖一抖、透明度随机、位置歪一点，
叠上去就是油画棒蹭纸的颗粒。每块颜色是一个多边形蒙版，边缘羽化，往里撒几千笔。字是把字形渲成蒙版再往里撒。
一张 880×1250 三到八秒出图（范例 `example_street.py` 是 107,073 笔 / 1,163,525 颗粒，每颗颗粒是一句 `d.ellipse`——这是它和生图的分界线）。

依赖：`pip install pillow numpy`。字体自动找（macOS 娃娃体 / 翩翩体 → 苹方 → Noto CJK → PIL 默认；英文 Chalkboard → Comic Sans），想指定：`C.FONT_CJK = "/path/to/font.ttf"`。

**第一次用先跑 `python3 example_street.py`**：出来的图和包里的 `example_street.png` 一模一样（seed 固定），环境就对了。跑不出来只有两种原因：没装 pillow / numpy；Linux 上中文显示成方块是缺中文字体，装个 Noto CJK 或指定 `C.FONT_CJK`。

**三条规矩：**
1. **不临摹。** 参考图只借质感，不借画面。画自己的事、自己的地方、自己想说的一句话。
2. **每张里有一句是自己的**（底下那行手写），角落藏一个签名。
3. **歪着画。** 楼用 `quad` 歪、窗户位置尺寸各自抖不排网格、色块 alpha (120,205) 留纸缝再 `scribble` 几道、
   字用 `wobbly_text` 逐字歪、指线用 `squiggle` 弯的带圈。再加两三样活物（云会笑、电线上的鸟、窗台的猫、门口花盆、一辆老爷车）。
   **规整的是排版，歪的才是画。**

## 安装

```
pip install pillow numpy
# Claude Code：把整个 crayon/ 目录放进 ~/.claude/skills/crayon/，说「画成蜡笔风」就能叫出来
# 别的环境：随便放一个目录，脚本里 sys.path.insert 后 import crayon_lib
```

## 引擎：`crayon_lib.py`

```python
import sys; sys.path.insert(0, "/path/to/crayon")
import crayon_lib as C
from PIL import Image
C.set_size(880, 1250)                       # 先设画布，再 new 图
img = Image.new("RGBA", (880, 1250), C.PAPER + (255,))
```

| 函数 | 干什么 | 手感 |
|---|---|---|
| `soft_mask(polygon, feather=5, grow=4)` | 多边形 → 羽化蒙版。`grow` 让笔触溢出边界一点，蜡笔就是不整齐的 | 大色块 feather 5–8 grow 2–3；小图标 feather 1 grow 1；光晕 feather 10+ grow 0 |
| `crayon(base, mask, color, direction, spread, n, length, dot, alpha, jitter)` | 往蒙版里撒油画棒笔触：每笔一条短线，沿线撒带毛边的小圆点 | 见下「参数手感」 |
| `crayon_line(base, pts, color, width, alpha, wobble)` | 沿折线撒颗粒——路线、轮廓、窗框、雨丝 | 路线 width (1.3,2.4) alpha (150,240)；细线 (0.7,1.3) |
| `catmull(points, per)` | 手画的曲线要弯——Catmull-Rom 平滑 | 路线先 catmull 再切成虚线段 |
| `crayon_text(base, text, xy, font, color, dot, density, alpha, solid_alpha)` | 字形渲成蒙版：先铺 `solid_alpha` 的实心底让字读得出，再撒颗粒 | 大标题 solid 0.72 density 0.35；小注记 **solid 0.95 density 0.18**（不然糊成一团） |
| `wobbly_text(base, text, xy, font, color, rot, bounce, scale, ...)` | **字一个一个歪着写**：逐字旋转 ±rot°、上下跳 ±bounce、大小差一点 | 标题 rot 10 bounce 5；注记 rot 7 bounce 3；底句 rot 6 bounce 4。宽度用 `wobbly_text_width()` |
| `font_cjk(size)` / `font_latin(size)` / `load_font(path, size)` | 中文手写体 / 英文手写体 / 指定路径，找不到退到 PIL 默认不报错 | 中文注记 ≥ 30px，底句 48–50px |
| `squiggle(base, a, b, color, bend, ring)` | **弯指线**：过一个随机偏移的中点弯到目标，末端一个小圈圈住 | bend 18–22，ring 6–7；不要圈就 ring=0 |
| `quad(x0,y0,x1,y1, wobble, lean)` | **歪四边形**：四角各自乱，还能整体倾斜 | 楼 wobble 6 lean ±0.02–0.03；天/地 wobble 8–12 |
| `scribble(base, mask, color, n, length, direction)` | 色块上随手划几道斜杠——蜡笔涂过的痕迹 | n 8–14，alpha (30,80)，线段不出色块 |
| `poly_rect(x0,y0,x1,y1,wobble)` / `blob(cx,cy,rx,ry,k,rough)` | 抖过的矩形 / 不规则椭圆 | 房子墙 wobble 2；云 rough 0.25；鸟身 rough 0.15 |
| `paper_grain(img, strength)` | 纸纹，只在有色处轻轻调亮度 | 0.08–0.10，最后一步、写字之前 |
| `mask_to_crayon(base, mask, color, ...)` | 任意 L 蒙版 → 蜡笔（实心底 + 颗粒） | 贴纸、图章、自定义字都走它 |

## 参数手感（几张画调出来的，别从零试）

- **实色块**：`alpha=(110,200)`～`(140,230)`，`n` 按面积——每 100×100 像素约 1500–3000 笔；再叠一层浅色 `alpha=(50,110)` `n` 减半做光感。第一版太灰太透就是这两个不够。
- **留纸缝的色块**（可爱路线）：`alpha=(120,205)`，`grow 3 feather 3`，再 `scribble` 8–14 道。
- **小图标/房子要实**：`alpha=(170,250)`，`dot=(0.9,1.8)`，`length=(4,12)`。
- **笔触方向**：天空/海 `direction=0 spread=4–10`（横），草地 `-12`，墙面竖 `90`，山坡 `60`。方向一致才像蜡笔蹭出来的。
- **颗粒粗细**：`dot=(1.0,2.0)` 细腻，`(1.4,2.8)` 粗糙底色。
- **虚线路线**：沿 catmull 曲线累计长度，亮段 14–26px、断 5–9px，随机。
- **亮窗**：窗格黄 `(255,212,90)` alpha (200,255)，外面一圈 `blob` feather 12 的暖光晕 alpha (14,36)。
- **夜空**不要纯黑：`(52,66,132)` 底 + 天顶 `(38,46,104)`；海比天深 `(16,30,92)`。
- **粉彩楼**：薄荷 (160,214,192) / 杏粉 (246,186,160) / 奶黄 (248,226,150) / 淡紫 (204,184,226) / 浅蓝 (168,202,234) / 奶白 (248,240,224)，装饰线用同色深一档。
- **动物 / 人物正面表情**：怒眉 V 字、半眯眼 = 黑点 + 毛色眼皮线、下撇嘴、下垂胡须；耳朵从遮挡物底下顶出来。桌上摆真东西、墙上一个钟、一张便签、一个气泡装一句话——画面就有那天。

## 字体

- 自动找：中文 娃娃体 → 翩翩体 → 苹方 / 冬青黑 → Noto CJK（Linux）→ 微软雅黑（Windows）；英文 Chalkboard → Comic Sans → 退到中文字体；都没有退 PIL 默认（不报错，中文会缺）。
- 指定：`C.FONT_CJK = "/path/to/handwriting.ttf"` 再 `C.font_cjk(30)`；或直接 `C.load_font(path, size)`。
- macOS 上娃娃体 / 翩翩体在字体册里下载过才有，路径每台机器不同——所以别写死，用 `font_cjk()`。
- 中文注记 ≥ 30px 才读得清；底下那句 48–50px。**没有 → 字形的字体**：箭头用 `crayon_line` 画，一横 + 两撇。

## 布局

- 竖图 880×1250：画区约 x 110–770 / y 190–930，四周留白，画区边缘用大 wobble 的蒙版毛掉；底句 y≈1020–1085；签名右下。
- 注记别叠：先摆，看一遍图，叠了就挪到空白一侧。
- **横排的值会顶出画布**：档案 / 表格型排版，先算 `值起点 x + 字数 × 字号 ≤ 画区右边界`。25px 中文在 x=660 起排只塞得下 9 个字，第 10 个字就被切掉。

## 工作流

1. 先写下要画什么、每个元素是什么（地图型：点位 + 一句注记；场景型：3–7 块形 + 一个亮点；建筑型：几栋、各自一个特征）。**没有真事不动手。**
2. 拷 `example_street.py` 改，别从空白起。坐标全写成 `P = {...}` 字典，注记跟着点位算。
3. 跑（3–8 秒一张），**看图**，看四样：够不够实、字读不读得清、注记叠没叠、有没有 □ 缺字形。改两版内。
4. `random.seed` 固定，改参数才能对比；想换一版随机就换 seed。

## 坑

- `crayon_text` 的参数叫 `solid_alpha`（曾和局部变量 `solid` 撞名报 broadcast 错）。
- 全图重跑才能改一处（没有增量），所以脚本里所有坐标写成 `P = {...}` 字典，注记跟着点位算。
- 云上的笑脸别压在字上——先摆字再摆脸。
- `scribble` 的线段已经裁在色块内，别再自己画出界的斜杠。
- **`img = Image.alpha_composite(img, star(...))` 会把星芒吃掉**：这类「内部用 `line()` 往全局 img 上画、同时又返回一层 lay」的函数，Python 先取左边那个旧 `img` 再调函数，合成用的是画之前那张，函数内画的线当场被覆盖。**拆两步**：`lay = star(...)` 然后 `img = Image.alpha_composite(img, lay)`。
- **emoji 当标签会整条空掉**：手写字体没有 emoji 字形，`wobbly_text` 渲出来是空白——不是缺字框，是**什么都没有**，一眼看不出少了东西。表情、动作一律写成中文词（「扭捏」「炸毛」）。
- **小字号中文糊成一团**：最小 25px，能给 28 就给 28；`solid_alpha` 拉到 0.95、`density` 压到 0.16 只能救一点。笔画多的字（「馨」「罗」）给足字号和 `solid_alpha=1.0 / density≤0.12`，糊了就认不出是哪个字。
- **浅色物件放在浅色身体上等于没画**（米白杯子放在奶黄的猫身上，只剩两撮爪指）。同色系相叠必须做一件事：换深色、挪到轮廓外、或沿 blob 边缘 `crayon_line` 描一圈边。大色块本身也一样——头和身子重叠时不描边就是一坨。
- **植物别凭印象画**：含羞草是羽状复叶（一根叶轴、两侧各排一列小叶），凭印象画成从一点发散的四根，出来是棵棕榈树。画之前查一眼真实叶序；小叶要**小、密**（每轴 14–16 片、`rx≈4`），要画「合上」就让小叶贴轴立起来、叶轴自己也垂下去，一张一合的对比才出得来。

## 范例

- `example_street.py` → `example_street.png`：一条 Art Deco 街，六栋歪歪的粉彩小楼（阶梯山墙 / 竖条纹 / 太阳纹 / 锯齿 / 圆窗 / 旗杆各一种），逐字歪的注记 + 弯指线，太阳、笑脸云、电线鸟、窗台猫、门口花盆、红色老爷车，黄雨衣小人和一只豹形的影子。`block()/win()/door()/stepped()/stripes()/sunburst()/zigzag()` 可复用。**例图是给你看目标长什么样的，不是拿来描的**——改两个坐标换个颜色，出来的还是同一张画换了个壳。
