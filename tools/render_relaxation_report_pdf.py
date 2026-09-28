from __future__ import annotations

import html
import re
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "notes" / "relaxation-time-survey-2026-08-27.md"
OUTPUT = ROOT / "output" / "动态网络弛豫时间总表-2026-08-27.pdf"

PAGE_SIZE = landscape(A4)
PAGE_W, PAGE_H = PAGE_SIZE
MARGIN_X = 13 * mm
MARGIN_TOP = 14 * mm
MARGIN_BOTTOM = 14 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X
CONTENT_H = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM


pdfmetrics.registerFont(TTFont("CJK", "C:/Windows/Fonts/simhei.ttf"))
pdfmetrics.registerFont(TTFont("Latin", "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFontFamily("CJK", normal="CJK", bold="CJK", italic="CJK", boldItalic="CJK")


styles = getSampleStyleSheet()
BODY = ParagraphStyle(
    "BodyCN",
    parent=styles["BodyText"],
    fontName="CJK",
    fontSize=9.1,
    leading=14.2,
    textColor=colors.HexColor("#344054"),
    spaceAfter=5.5,
    wordWrap="CJK",
)
INTRO = ParagraphStyle(
    "IntroCN",
    parent=BODY,
    fontSize=9.6,
    leading=15,
    textColor=colors.HexColor("#475467"),
    borderColor=colors.HexColor("#6D82D5"),
    borderWidth=0,
    borderLeft=3,
    borderPadding=(6, 8, 6, 10),
    backColor=colors.HexColor("#F6F8FC"),
    spaceAfter=11,
)
H1 = ParagraphStyle(
    "H1CN",
    parent=BODY,
    fontSize=22,
    leading=29,
    textColor=colors.HexColor("#1D2939"),
    spaceAfter=8,
    keepWithNext=True,
)
H2 = ParagraphStyle(
    "H2CN",
    parent=BODY,
    fontSize=15,
    leading=20,
    textColor=colors.HexColor("#253351"),
    spaceBefore=10,
    spaceAfter=7,
    keepWithNext=True,
)
H3 = ParagraphStyle(
    "H3CN",
    parent=BODY,
    fontSize=11.5,
    leading=16,
    textColor=colors.HexColor("#4059A8"),
    spaceBefore=7,
    spaceAfter=5,
    keepWithNext=True,
)
TABLE_CELL = ParagraphStyle(
    "TableCellCN",
    parent=BODY,
    fontSize=7.35,
    leading=10.4,
    spaceAfter=0,
)
TABLE_HEAD = ParagraphStyle(
    "TableHeadCN",
    parent=TABLE_CELL,
    textColor=colors.white,
    alignment=TA_CENTER,
)
CAPTION = ParagraphStyle(
    "CaptionCN",
    parent=BODY,
    fontSize=7.7,
    leading=11,
    textColor=colors.HexColor("#667085"),
    alignment=TA_CENTER,
    spaceBefore=4,
    spaceAfter=8,
)


def inline_markup(text: str) -> str:
    superscript_map = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
    subscript_map = str.maketrans("₀₁₂₃₄₅₆₇₈₉₋₊", "0123456789-+")

    def normalize_superscript(match):
        return "^" + match.group(0).translate(superscript_map)

    def normalize_subscript(match):
        return "_" + match.group(0).translate(subscript_map)

    text = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+", normalize_superscript, text)
    text = re.sub(r"[₀₁₂₃₄₅₆₇₈₉₋₊]+", normalize_subscript, text)
    protected: list[str] = []

    def protect_code(match):
        protected.append(f'<font color="#4059A8">{html.escape(match.group(1))}</font>')
        return f"\u0000{len(protected) - 1}\u0000"

    text = re.sub(r"`([^`]+)`", protect_code, text)
    text = html.escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<link href="\2" color="#4059A8"><u>\1</u></link>',
        text,
    )
    for index, value in enumerate(protected):
        text = text.replace(f"\u0000{index}\u0000", value)
    return text


def split_table_row(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def is_table_separator(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def column_widths(rows: list[list[str]]) -> list[float]:
    columns = len(rows[0])
    if columns == 6:
        return [108, 132, 132, 132, 132, CONTENT_W - 636]
    if columns == 4:
        return [130, 205, 205, CONTENT_W - 540]
    if columns == 3:
        return [155, 270, CONTENT_W - 425]
    if columns == 2:
        return [250, CONTENT_W - 250]
    return [CONTENT_W / columns] * columns


def make_table(rows: list[list[str]]) -> Table:
    styled_rows = []
    for row_index, row in enumerate(rows):
        style = TABLE_HEAD if row_index == 0 else TABLE_CELL
        styled_rows.append([Paragraph(inline_markup(cell), style) for cell in row])
    table = Table(
        styled_rows,
        colWidths=column_widths(rows),
        repeatRows=1,
        splitByRow=1,
        hAlign="LEFT",
    )
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#526CB8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#DCE2EC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
    ]
    for row_index in range(1, len(rows)):
        if row_index % 2 == 0:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), colors.HexColor("#F8FAFC")))
    table.setStyle(TableStyle(commands))
    return table


def make_image(relative_path: str, alt: str):
    path = (SOURCE.parent / relative_path).resolve()
    with PILImage.open(path) as image:
        width, height = image.size
    max_width = CONTENT_W - 6
    max_height = CONTENT_H - 92
    scale = min(max_width / width, max_height / height)
    flowable = Image(str(path), width=width * scale, height=height * scale)
    flowable.hAlign = "CENTER"
    return [flowable, Paragraph(inline_markup(alt), CAPTION)]


def parse_markdown() -> list:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story: list = []
    index = 0
    first_body = True
    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        image_match = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if image_match:
            story.extend(make_image(image_match.group(2), image_match.group(1)))
            index += 1
            continue
        if stripped.startswith("# "):
            story.append(Paragraph(inline_markup(stripped[2:]), H1))
            index += 1
            continue
        if stripped.startswith("## "):
            story.append(Paragraph(inline_markup(stripped[3:]), H2))
            index += 1
            continue
        if stripped.startswith("### "):
            story.append(Paragraph(inline_markup(stripped[4:]), H3))
            index += 1
            continue
        if stripped.startswith("|") and index + 1 < len(lines) and is_table_separator(lines[index + 1]):
            rows = [split_table_row(stripped)]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(split_table_row(lines[index]))
                index += 1
            story.append(make_table(rows))
            story.append(Spacer(1, 8))
            continue
        if stripped.startswith("- "):
            items = []
            while index < len(lines) and lines[index].strip().startswith("- "):
                item_text = lines[index].strip()[2:].strip()
                items.append(ListItem(Paragraph(inline_markup(item_text), BODY), leftIndent=10))
                index += 1
            story.append(ListFlowable(items, bulletType="bullet", start="circle", leftIndent=18, bulletFontName="CJK", bulletFontSize=6, spaceAfter=6))
            continue
        if re.match(r"\d+\. ", stripped):
            items = []
            while index < len(lines) and re.match(r"\d+\. ", lines[index].strip()):
                item_text = re.sub(r"^\d+\.\s+", "", lines[index].strip())
                items.append(ListItem(Paragraph(inline_markup(item_text), BODY), leftIndent=12))
                index += 1
            story.append(ListFlowable(items, bulletType="1", leftIndent=20, bulletFontName="CJK", bulletFontSize=8, spaceAfter=6))
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate:
                break
            if candidate.startswith(("#", "- ", "|", "![")) or re.match(r"\d+\. ", candidate):
                break
            paragraph_lines.append(candidate)
            index += 1
        paragraph_text = " ".join(paragraph_lines)
        style = INTRO if first_body else BODY
        story.append(Paragraph(inline_markup(paragraph_text), style))
        if first_body:
            story.append(PageBreak())
        first_body = False
    return story


class ReportDocTemplate(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(
            filename,
            pagesize=PAGE_SIZE,
            leftMargin=MARGIN_X,
            rightMargin=MARGIN_X,
            topMargin=MARGIN_TOP,
            bottomMargin=MARGIN_BOTTOM,
            title="19篇光响应/动态网络论文：材料弛豫时间总表",
            author="OECT Knowledge Base",
            subject="动态网络材料弛豫时间文献汇总",
        )
        frame = Frame(MARGIN_X, MARGIN_BOTTOM, CONTENT_W, CONTENT_H, id="main")
        self.addPageTemplates(PageTemplate(id="report", frames=[frame], onPage=self.draw_header_footer))

    @staticmethod
    def draw_header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("CJK", 7.5)
        canvas.setFillColor(colors.HexColor("#98A2B3"))
        canvas.drawString(MARGIN_X, PAGE_H - 8 * mm, "动态网络材料弛豫时间文献总表")
        canvas.drawRightString(PAGE_W - MARGIN_X, 7 * mm, f"第 {doc.page} 页")
        canvas.setStrokeColor(colors.HexColor("#E4E7EC"))
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN_X, PAGE_H - 9.5 * mm, PAGE_W - MARGIN_X, PAGE_H - 9.5 * mm)
        canvas.restoreState()


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = ReportDocTemplate(str(OUTPUT))
    doc.build(parse_markdown())
    print(OUTPUT)


if __name__ == "__main__":
    main()
