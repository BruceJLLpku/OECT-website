from __future__ import annotations

import csv
import math
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PNG_PATH = ROOT / "assets" / "cans-relaxation-time-arrow.png"
SVG_PATH = ROOT / "assets" / "cans-relaxation-time-arrow.svg"
CSV_PATH = ROOT / "notes" / "relaxation-time-arrow-data.csv"

WIDTH = 3600
LEFT = 1080
RIGHT = 3380
TOP = 445
ROW_H = 63
X_MIN = -2.2
X_MAX = 6.4

COLORS = {
    "light": "#3F8FD2",
    "temperature": "#E4872B",
    "composition": "#8767C8",
    "fixed": "#344054",
    "local": "#199A8E",
}


DATA = [
    dict(name="ALYDS（AFM 局部）", paper="Lu/Zheng 2025", lo=0.012, hi=0.017, value="约 12–17 ms", kind="local", driver="488 nm 光/暗"),
    dict(name="gel-MA", paper="Zhang/Kalow 2023", lo=0.672, hi=0.672, value="0.672 s", kind="fixed", driver="固定条件"),
    dict(name="CY-Net", paper="El-Zaatari/Kalow 2020", lo=3.7, hi=39.3, value="3.7–39.3 s", kind="temperature", driver="150→100 °C"),
    dict(name="Marozas allyl-sulfide gel", paper="Marozas 2019", lo=14.1, hi=214, value="14.1–214 s", kind="light", driver="365 nm 光强"),
    dict(name="Wei living polymer network", paper="Wei/Campos 2024", lo=20, hi=670, value="约 20–670 s", kind="light", driver="蓝光/暗；tau_R"),
    dict(name="BA-Net", paper="El-Zaatari/Kalow 2020", lo=36.1, hi=393, value="36.1–393 s", kind="temperature", driver="150→100 °C"),
    dict(name="CY/MA-Net", paper="El-Zaatari/Kalow 2020", lo=45.785, hi=45.785, value="45.8 s", kind="fixed", driver="140 °C"),
    dict(name="BA/MA-Net", paper="El-Zaatari/Kalow 2020", lo=106.799, hi=106.799, value="106.8 s", kind="fixed", driver="140 °C"),
    dict(name="gel-CH", paper="Zhang/Kalow 2023", lo=115, hi=115, value="115 s", kind="fixed", driver="固定条件"),
    dict(name="PBEDS", paper="Lu/Zheng 2025", lo=100, hi=500, value="100–500 s", kind="light", driver="445 nm 光强/暗"),
    dict(name="gel-AA", paper="Zhang/Kalow 2023", lo=173, hi=173, value="173 s", kind="fixed", driver="固定条件"),
    dict(name="IND-Net", paper="El-Zaatari/Kalow 2020", lo=148, hi=2043, value="148–2043 s", kind="temperature", driver="150→100 °C"),
    dict(name="BA/DP-Net", paper="El-Zaatari/Kalow 2020", lo=233.629, hi=233.629, value="233.6 s", kind="fixed", driver="140 °C"),
    dict(name="MA-Net", paper="El-Zaatari/Kalow 2020", lo=288, hi=2967, value="288–2967 s", kind="temperature", driver="150→100 °C"),
    dict(name="gel-MM", paper="Zhang/Kalow 2023", lo=621, hi=621, value="621 s", kind="fixed", driver="固定条件"),
    dict(name="gel-AA_cap", paper="Zhang/Kalow 2023", lo=675, hi=675, value="675 s", kind="composition", driver="巯基封端"),
    dict(name="DASA Net-1", paper="Garcia Villatoro/Kalow 2025", lo=660, hi=9000, value="约 660–9000 s", kind="temperature", driver="160→100 °C"),
    dict(name="gel-ctrl", paper="Zhang/Kalow 2023", lo=1553, hi=1553, value="1553 s", kind="fixed", driver="非动态对照"),
    dict(name="MDADS", paper="Lu/Zheng 2025", lo=1300, hi=2500, value="约 1300–2500 s", kind="light", driver="445 nm 光/暗"),
    dict(name="ALYDS（宏观流变）", paper="Lu/Zheng 2025", lo=1500, hi=3400, value="1500–3400 s", kind="light", driver="445 nm 光/暗"),
    dict(name="C3-ALY", paper="Lu/Zheng 2025", lo=2700, hi=2700, value="2700 s", kind="fixed", driver="光不响应对照"),
    dict(name="DASA Net-2", paper="Garcia Villatoro/Kalow 2025", lo=4020, hi=12000, value="约 4020–12000 s", kind="temperature", driver="160→100 °C"),
    dict(name="CN-Net", paper="El-Zaatari/Kalow 2020", lo=18152, hi=18152, value="18152 s", kind="fixed", driver="150 °C；外推"),
    dict(name="DP-Net", paper="El-Zaatari/Kalow 2020", lo=22481, hi=22481, value="22481 s", kind="fixed", driver="150 °C；外推"),
    dict(name="DASA Control-1", paper="Garcia Villatoro/Kalow 2025", lo=30000, hi=30000, value="30000 s", kind="fixed", driver="100 °C；外推"),
    dict(name="DASA Control-2", paper="Garcia Villatoro/Kalow 2025", lo=99000, hi=99000, value="99000 s", kind="fixed", driver="100 °C；外推"),
    dict(name="PEG thioester gels", paper="Carberry/Anseth 2020", lo=2.1e5, hi=1.8e6, value="约 2.1×10^5–1.8×10^6 s", kind="composition", driver="过量巯基 200→0%"),
]


DATA.sort(key=lambda item: (item["lo"], item["hi"]))
HEIGHT = TOP + len(DATA) * ROW_H + 330


def x_pos(value: float) -> float:
    fraction = (math.log10(value) - X_MIN) / (X_MAX - X_MIN)
    return LEFT + fraction * (RIGHT - LEFT)


def load_font(size: int, bold: bool = False):
    path = Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/NotoSansSC-VF.ttf")
    return ImageFont.truetype(str(path), size=size)


def text(draw: ImageDraw.ImageDraw, xy, value, font, fill="#1D2939", anchor="la"):
    draw.text(xy, value, font=font, fill=fill, anchor=anchor)


def build_png():
    image = Image.new("RGB", (WIDTH, HEIGHT), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title_font = load_font(62, True)
    subtitle_font = load_font(29)
    axis_font = load_font(28, True)
    tick_font = load_font(25)
    label_font = load_font(27, True)
    paper_font = load_font(22)
    value_font = load_font(23, True)
    note_font = load_font(23)

    text(draw, (70, 62), "动态网络弛豫时间箭头图", title_font)
    text(draw, (72, 142), "按特征时间由小到大排列；范围线表示光照、温度或配方改变造成的可调区间", subtitle_font, "#52617A")

    legend_x = 75
    legend_y = 222
    for key, label in [("light", "光照范围"), ("temperature", "温度范围"), ("composition", "配方/封端范围"), ("fixed", "单一条件"), ("local", "局部 AFM")]:
        color = COLORS[key]
        draw.rounded_rectangle((legend_x, legend_y, legend_x + 34, legend_y + 20), radius=10, fill=color)
        text(draw, (legend_x + 46, legend_y + 10), label, tick_font, "#344054", "lm")
        legend_x += 260

    arrow_y0, arrow_y1 = 303, 356
    gradient_w = RIGHT - LEFT - 50
    gradient = Image.new("RGB", (gradient_w, arrow_y1 - arrow_y0), "white")
    gp = gradient.load()
    start = (70, 148, 211)
    end = (220, 225, 230)
    for xx in range(gradient_w):
        t = xx / max(1, gradient_w - 1)
        color = tuple(round(start[i] * (1 - t) + end[i] * t) for i in range(3))
        for yy in range(arrow_y1 - arrow_y0):
            gp[xx, yy] = color
    image.paste(gradient, (LEFT, arrow_y0))
    draw.polygon([(RIGHT - 50, arrow_y0 - 12), (RIGHT, (arrow_y0 + arrow_y1) // 2), (RIGHT - 50, arrow_y1 + 12)], fill=end)
    text(draw, (LEFT + 22, (arrow_y0 + arrow_y1) // 2), "快弛豫  Fast", axis_font, "#FFFFFF", "lm")
    text(draw, (RIGHT - 80, (arrow_y0 + arrow_y1) // 2), "慢弛豫  Slow", axis_font, "#344054", "rm")

    ticks = [(1e-2, "0.01"), (1e-1, "0.1"), (1, "1"), (10, "10"), (100, "100"), (1000, "1k"), (1e4, "10k"), (1e5, "100k"), (1e6, "1M")]
    grid_bottom = TOP + len(DATA) * ROW_H - 15
    for value, label in ticks:
        x = x_pos(value)
        draw.line((x, arrow_y1 + 6, x, grid_bottom), fill="#E5EAF1", width=2)
        draw.line((x, arrow_y1, x, arrow_y1 + 17), fill="#94A3B8", width=3)
        text(draw, (x, arrow_y1 + 29), label, tick_font, "#52617A", "ma")
    text(draw, ((LEFT + RIGHT) / 2, 419), "弛豫时间 / s（log scale）", axis_font, "#344054", "ma")

    for index, item in enumerate(DATA):
        cy = TOP + index * ROW_H + ROW_H // 2
        if index % 2:
            draw.rectangle((55, cy - ROW_H // 2, WIDTH - 55, cy + ROW_H // 2), fill="#FAFBFD")
        color = COLORS[item["kind"]]
        text(draw, (70, cy - 7), item["name"], label_font, "#1D2939", "lm")
        text(draw, (590, cy - 7), item["paper"], paper_font, "#667085", "lm")
        text(draw, (590, cy + 20), item["driver"], paper_font, color, "lm")
        lo_x, hi_x = x_pos(item["lo"]), x_pos(item["hi"])
        if math.isclose(item["lo"], item["hi"]):
            draw.ellipse((lo_x - 10, cy - 10, lo_x + 10, cy + 10), fill=color, outline="#FFFFFF", width=3)
        else:
            draw.line((lo_x, cy, hi_x, cy), fill=color, width=10)
            draw.line((lo_x, cy - 13, lo_x, cy + 13), fill=color, width=5)
            draw.line((hi_x, cy - 13, hi_x, cy + 13), fill=color, width=5)
            draw.ellipse((lo_x - 7, cy - 7, lo_x + 7, cy + 7), fill="#FFFFFF", outline=color, width=4)
            draw.ellipse((hi_x - 7, cy - 7, hi_x + 7, cy + 7), fill="#FFFFFF", outline=color, width=4)
        if hi_x > RIGHT - 330:
            text(draw, (hi_x - 18, cy - 19), item["value"], value_font, color, "rb")
        else:
            text(draw, (hi_x + 18, cy - 19), item["value"], value_font, color, "lb")

    note_y = TOP + len(DATA) * ROW_H + 60
    text(draw, (72, note_y), "读图说明", axis_font, "#253351")
    notes = [
        "• 所有值统一换算为秒并放在对数轴上；点为单一条件，范围线为同一网络在不同光照、温度或配方下的最小–最大值。",
        "• tau_sr、tau*、<tau>、tau_1/2、tau_R=1/omega_c 与 AFM 局部 tau'_1/2 的定义并不相同；本图用于时间尺度定位，不代表这些模型参数可直接等同。",
        "• 带“约”的端点含原图估读；DASA 高温端、Zheng 中间光强及部分 Carberry 数值均应结合完整核对表读取。",
    ]
    for idx, line in enumerate(notes):
        text(draw, (72, note_y + 52 + idx * 40), line, note_font, "#52617A")
    watermark = Image.new("RGBA", image.size, (0, 0, 0, 0))
    watermark_draw = ImageDraw.Draw(watermark)
    watermark_draw.text(
        (WIDTH - 78, HEIGHT - 148),
        "Jionglin Li",
        font=load_font(46, True),
        fill=(64, 81, 124, 76),
        anchor="ra",
    )
    watermark_draw.text(
        (WIDTH - 78, HEIGHT - 94),
        "(PKU Zheng Group)",
        font=load_font(31),
        fill=(64, 81, 124, 76),
        anchor="ra",
    )
    image = Image.alpha_composite(image.convert("RGBA"), watermark).convert("RGB")
    draw = ImageDraw.Draw(image)
    text(draw, (WIDTH - 70, HEIGHT - 38), "数据来源：用户提供的 19 篇论文及其公开补充信息｜整理：2026-08-27", paper_font, "#98A2B3", "ra")
    image.save(PNG_PATH, dpi=(300, 300), optimize=True)


def svg_text(x, y, value, size, fill="#1D2939", weight=400, anchor="start"):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-family="Noto Sans SC, Microsoft YaHei, sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>'


def build_svg():
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<defs><linearGradient id="axisGradient" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4694D3"/><stop offset="1" stop-color="#DCE1E6"/></linearGradient></defs>',
        '<rect width="100%" height="100%" fill="#FFFFFF"/>',
        svg_text(70, 110, "动态网络弛豫时间箭头图", 62, weight=700),
        svg_text(72, 170, "按特征时间由小到大排列；范围线表示光照、温度或配方改变造成的可调区间", 29, "#52617A"),
    ]
    legend_x = 75
    for key, label in [("light", "光照范围"), ("temperature", "温度范围"), ("composition", "配方/封端范围"), ("fixed", "单一条件"), ("local", "局部 AFM")]:
        parts.append(f'<rect x="{legend_x}" y="222" width="34" height="20" rx="10" fill="{COLORS[key]}"/>')
        parts.append(svg_text(legend_x + 46, 241, label, 25, "#344054"))
        legend_x += 260
    parts.extend([
        f'<rect x="{LEFT}" y="303" width="{RIGHT - LEFT - 50}" height="53" fill="url(#axisGradient)"/>',
        f'<polygon points="{RIGHT - 50},291 {RIGHT},329 {RIGHT - 50},368" fill="#DCE1E6"/>',
        svg_text(LEFT + 22, 340, "快弛豫  Fast", 28, "#FFFFFF", 700),
        svg_text(RIGHT - 80, 340, "慢弛豫  Slow", 28, "#344054", 700, "end"),
    ])
    ticks = [(1e-2, "0.01"), (1e-1, "0.1"), (1, "1"), (10, "10"), (100, "100"), (1000, "1k"), (1e4, "10k"), (1e5, "100k"), (1e6, "1M")]
    grid_bottom = TOP + len(DATA) * ROW_H - 15
    for value, label in ticks:
        x = x_pos(value)
        parts.append(f'<line x1="{x}" y1="362" x2="{x}" y2="{grid_bottom}" stroke="#E5EAF1" stroke-width="2"/>')
        parts.append(f'<line x1="{x}" y1="356" x2="{x}" y2="373" stroke="#94A3B8" stroke-width="3"/>')
        parts.append(svg_text(x, 401, label, 25, "#52617A", anchor="middle"))
    parts.append(svg_text((LEFT + RIGHT) / 2, 430, "弛豫时间 / s（log scale）", 28, "#344054", 700, "middle"))
    for index, item in enumerate(DATA):
        cy = TOP + index * ROW_H + ROW_H // 2
        if index % 2:
            parts.append(f'<rect x="55" y="{cy - ROW_H // 2}" width="{WIDTH - 110}" height="{ROW_H}" fill="#FAFBFD"/>')
        color = COLORS[item["kind"]]
        parts.append(svg_text(70, cy + 2, item["name"], 27, weight=700))
        parts.append(svg_text(590, cy + 2, item["paper"], 22, "#667085"))
        parts.append(svg_text(590, cy + 27, item["driver"], 22, color))
        lo_x, hi_x = x_pos(item["lo"]), x_pos(item["hi"])
        if math.isclose(item["lo"], item["hi"]):
            parts.append(f'<circle cx="{lo_x}" cy="{cy}" r="10" fill="{color}" stroke="#FFFFFF" stroke-width="3"/>')
        else:
            parts.append(f'<line x1="{lo_x}" y1="{cy}" x2="{hi_x}" y2="{cy}" stroke="{color}" stroke-width="10" stroke-linecap="round"/>')
            parts.append(f'<line x1="{lo_x}" y1="{cy - 13}" x2="{lo_x}" y2="{cy + 13}" stroke="{color}" stroke-width="5"/>')
            parts.append(f'<line x1="{hi_x}" y1="{cy - 13}" x2="{hi_x}" y2="{cy + 13}" stroke="{color}" stroke-width="5"/>')
            parts.append(f'<circle cx="{lo_x}" cy="{cy}" r="7" fill="#FFFFFF" stroke="{color}" stroke-width="4"/>')
            parts.append(f'<circle cx="{hi_x}" cy="{cy}" r="7" fill="#FFFFFF" stroke="{color}" stroke-width="4"/>')
        if hi_x > RIGHT - 330:
            parts.append(svg_text(hi_x - 18, cy - 18, item["value"], 23, color, 700, "end"))
        else:
            parts.append(svg_text(hi_x + 18, cy - 18, item["value"], 23, color, 700))
    note_y = TOP + len(DATA) * ROW_H + 60
    parts.append(svg_text(72, note_y, "读图说明", 28, "#253351", 700))
    notes = [
        "• 所有值统一换算为秒并放在对数轴上；点为单一条件，范围线为同一网络在不同光照、温度或配方下的最小–最大值。",
        "• tau_sr、tau*、<tau>、tau_1/2、tau_R=1/omega_c 与 AFM 局部 tau'_1/2 的定义并不相同；本图用于时间尺度定位，不代表这些模型参数可直接等同。",
        "• 带“约”的端点含原图估读；DASA 高温端、Zheng 中间光强及部分 Carberry 数值均应结合完整核对表读取。",
    ]
    for idx, line in enumerate(notes):
        parts.append(svg_text(72, note_y + 52 + idx * 40, line, 23, "#52617A"))
    parts.append(f'<g opacity="0.30">{svg_text(WIDTH - 78, HEIGHT - 148, "Jionglin Li", 46, "#40517C", 700, "end")}{svg_text(WIDTH - 78, HEIGHT - 94, "(PKU Zheng Group)", 31, "#40517C", 400, "end")}</g>')
    parts.append(svg_text(WIDTH - 70, HEIGHT - 38, "数据来源：用户提供的 19 篇论文及其公开补充信息｜整理：2026-08-27", 22, "#98A2B3", anchor="end"))
    parts.append("</svg>")
    SVG_PATH.write_text("\n".join(parts), encoding="utf-8")


def build_csv():
    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["network", "paper", "tau_min_s", "tau_max_s", "display_value", "range_type", "driver"])
        writer.writeheader()
        for item in DATA:
            writer.writerow({
                "network": item["name"],
                "paper": item["paper"],
                "tau_min_s": item["lo"],
                "tau_max_s": item["hi"],
                "display_value": item["value"],
                "range_type": item["kind"],
                "driver": item["driver"],
            })


if __name__ == "__main__":
    build_png()
    build_svg()
    build_csv()
    print(PNG_PATH)
    print(SVG_PATH)
    print(CSV_PATH)
