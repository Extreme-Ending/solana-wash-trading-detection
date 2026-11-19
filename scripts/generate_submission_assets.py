#!/usr/bin/env python3
"""Generate editable and rendered submission documents from verified report source."""

from __future__ import annotations

import os
import re
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/solana_wallet_risk_matplotlib")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as PptxColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches as PptxInches, Pt as PptxPt


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "submission"
ASSETS = OUTPUT / "assets"
REPORT_SOURCE = OUTPUT / "solana_wallet_risk_project_report.md"
REPORT_DOCX = OUTPUT / "solana_wallet_risk_project_report.docx"
REPORT_PDF = OUTPUT / "solana_wallet_risk_project_report.pdf"
PRESENTATION = OUTPUT / "solana_wallet_risk_presentation.pptx"

BURGUNDY = "6F1D3A"
DARK = "29151E"
CREAM = "F8F3F1"
ROSE = "D7A7B7"
MUTED = "6B6266"
WHITE = "FFFFFF"
GREEN = "2E6B57"
AMBER = "B57822"


def _hex(value: str) -> tuple[float, float, float]:
    return tuple(int(value[index : index + 2], 16) / 255 for index in (0, 2, 4))


def _save_figure(path: Path) -> None:
    plt.savefig(path, dpi=180, bbox_inches="tight", facecolor=CREAM_COLOR)
    plt.close()


CREAM_COLOR = f"#{CREAM}"


def _flow_diagram(
    path: Path,
    labels: list[str],
    *,
    title: str,
    rows: int = 1,
) -> None:
    columns = (len(labels) + rows - 1) // rows
    fig, ax = plt.subplots(figsize=(12, 2.8 if rows == 1 else 4.6))
    fig.patch.set_facecolor(CREAM_COLOR)
    ax.set_facecolor(CREAM_COLOR)
    ax.axis("off")
    positions: list[tuple[float, float]] = []
    for index, label in enumerate(labels):
        row = index // columns
        column = index % columns
        if row % 2 == 1:
            column = columns - 1 - column
        x = 0.04 + column * (0.92 / max(columns - 1, 1))
        y = 0.68 if row == 0 else 0.20
        positions.append((x, y))
        box = FancyBboxPatch(
            (x - 0.075, y - 0.10),
            0.15,
            0.20,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            facecolor=f"#{BURGUNDY}" if index % 2 == 0 else f"#{DARK}",
            edgecolor=f"#{BURGUNDY}",
            linewidth=1.2,
        )
        ax.add_patch(box)
        ax.text(x, y, label, ha="center", va="center", color="white", fontsize=9, weight="bold")
    for start, end in zip(positions, positions[1:]):
        arrow = FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=1.4,
            color=f"#{BURGUNDY}",
            connectionstyle="arc3,rad=0" if abs(start[1] - end[1]) < 0.1 else "arc3,rad=0.15",
        )
        ax.add_patch(arrow)
    ax.text(0.5, 0.96, title, ha="center", va="top", fontsize=15, color=f"#{DARK}", weight="bold")
    ax.set_xlim(-0.06, 1.06)
    ax.set_ylim(0.02, 1.02)
    _save_figure(path)


def generate_figures() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.titleweight": "bold"})

    _flow_diagram(
        ASSETS / "pipeline_architecture.png",
        ["Dune\nexport", "Audit", "Preprocess", "29 features", "Train", "Evaluate", "Artifact", "API"],
        title="Reproducible machine-learning pipeline",
    )
    _flow_diagram(
        ASSETS / "application_architecture.png",
        ["External client\nor React demo", "JSON +\nID token", "FastAPI", "UID policy", "Feature\nbuilder", "Isolation\nForest", "Scores", "Client view"],
        title="API-first scoring and authentication path",
    )

    fig, ax = plt.subplots(figsize=(9, 4.8))
    fig.patch.set_facecolor(CREAM_COLOR)
    ax.set_facecolor(CREAM_COLOR)
    roles = ["Training\nSep 1", "Validation\nOct 1", "Holdout\nDec 1"]
    counts = [1754, 1930, 2312]
    bars = ax.bar(roles, counts, color=[f"#{BURGUNDY}", f"#{ROSE}", f"#{DARK}"])
    ax.bar_label(bars, padding=4, fontsize=11, weight="bold")
    ax.set_ylabel("Wallet snapshots")
    ax.set_title("Chronological cumulative cohorts")
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(0.5, -0.18, "All 1,754 training wallets recur later; entrants are reported separately.", transform=ax.transAxes, ha="center", color=f"#{MUTED}")
    _save_figure(ASSETS / "temporal_cohorts.png")

    fig, ax = plt.subplots(figsize=(9, 4.8))
    fig.patch.set_facecolor(CREAM_COLOR)
    ax.set_facecolor(CREAM_COLOR)
    pairs = ["IF vs MAD", "IF vs LOF", "LOF vs MAD"]
    values = [0.8662, 0.0488, -0.0187]
    colors = [f"#{GREEN}", f"#{ROSE}", f"#{AMBER}"]
    bars = ax.barh(pairs, values, color=colors)
    ax.axvline(0, color=f"#{DARK}", linewidth=0.8)
    ax.set_xlim(-0.15, 1.0)
    ax.bar_label(bars, fmt="%.4f", padding=4, fontsize=10)
    ax.set_xlabel("Spearman rank correlation")
    ax.set_title("Holdout detector agreement")
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(0.5, -0.16, "Agreement measures ranking similarity, not correctness.", transform=ax.transAxes, ha="center", color=f"#{MUTED}")
    _save_figure(ASSETS / "holdout_rank_agreement.png")

    fig, ax = plt.subplots(figsize=(9, 5.3))
    fig.patch.set_facecolor(CREAM_COLOR)
    ax.set_facecolor(CREAM_COLOR)
    labels = ["IF 100 trees", "IF 500 trees", "IF samples 128", "IF samples 512", "LOF 15 neighbors", "LOF 70 neighbors"]
    values = [0.9938, 0.9980, 0.9929, 0.9923, 0.6052, 0.7827]
    colors = [f"#{BURGUNDY}"] * 4 + [f"#{ROSE}"] * 2
    bars = ax.barh(labels[::-1], values[::-1], color=colors[::-1])
    ax.set_xlim(0, 1.05)
    ax.bar_label(bars, fmt="%.4f", padding=4, fontsize=9)
    ax.set_xlabel("Spearman correlation with primary validation ranking")
    ax.set_title("Validation-only parameter sensitivity")
    ax.spines[["top", "right"]].set_visible(False)
    _save_figure(ASSETS / "parameter_sensitivity.png")


def _clean_inline(text: str) -> str:
    text = re.sub(r"!\[([^]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"\1", text)
    return text.strip()


def _set_cell_shading(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    properties.append(shading)


def _add_page_number(paragraph) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, end])


def markdown_to_docx() -> None:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

    normal = document.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.08
    for name, size in (("Title", 24), ("Heading 1", 17), ("Heading 2", 14), ("Heading 3", 12)):
        style = document.styles[name]
        style.font.name = "Aptos Display"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor.from_string(BURGUNDY)
    document.styles["Title"].font.bold = True

    properties = document.core_properties
    properties.title = "Solana Wallet Risk: Unsupervised Wallet Anomaly Detection on Solana"
    properties.subject = "Applied machine-learning project report"
    properties.author = "Student submission"
    properties.created = datetime(2026, 11, 19, tzinfo=UTC)
    properties.modified = datetime(2026, 11, 19, tzinfo=UTC)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Solana Wallet Risk  |  ")
    _add_page_number(footer)

    lines = REPORT_SOURCE.read_text(encoding="utf-8").splitlines()
    index = 0
    code_mode = False
    code_lines: list[str] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            document.add_paragraph(_clean_inline(" ".join(paragraph_lines)))
            paragraph_lines.clear()

    while index < len(lines):
        line = lines[index]
        if line.startswith("```"):
            flush_paragraph()
            if code_mode:
                paragraph = document.add_paragraph()
                paragraph.style = document.styles["Normal"]
                run = paragraph.add_run("\n".join(code_lines))
                run.font.name = "Liberation Mono"
                run.font.size = Pt(8.5)
                _set_cell_shading_dummy = None
                code_lines.clear()
                code_mode = False
            else:
                code_mode = True
            index += 1
            continue
        if code_mode:
            code_lines.append(line)
            index += 1
            continue
        if not line.strip():
            flush_paragraph()
            index += 1
            continue
        image_match = re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", line.strip())
        if image_match:
            flush_paragraph()
            image_path = (REPORT_SOURCE.parent / image_match.group(2)).resolve()
            document.add_picture(str(image_path), width=Inches(6.25))
            caption = document.add_paragraph(image_match.group(1))
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            caption.runs[0].italic = True
            caption.runs[0].font.size = Pt(9)
            index += 1
            continue
        if line.startswith("#"):
            flush_paragraph()
            level = len(line) - len(line.lstrip("#"))
            text = _clean_inline(line[level:].strip())
            if level == 1:
                document.add_heading(text, 0)
            elif level == 2:
                document.add_heading(text, 1)
            elif level == 3:
                document.add_heading(text, 2)
            else:
                document.add_heading(text, 3)
            index += 1
            continue
        if line.startswith("|"):
            flush_paragraph()
            raw_rows: list[list[str]] = []
            while index < len(lines) and lines[index].startswith("|"):
                raw_rows.append([_clean_inline(item) for item in lines[index].strip().strip("|").split("|")])
                index += 1
            rows = [row for row in raw_rows if not all(re.fullmatch(r":?-+:?", item.replace(" ", "")) for item in row)]
            if rows:
                table = document.add_table(rows=len(rows), cols=len(rows[0]))
                table.style = "Table Grid"
                for row_index, row in enumerate(rows):
                    for column_index, value in enumerate(row):
                        cell = table.cell(row_index, column_index)
                        cell.text = value
                        for run in cell.paragraphs[0].runs:
                            run.font.size = Pt(8.5)
                            run.font.bold = row_index == 0
                            run.font.color.rgb = RGBColor.from_string(WHITE if row_index == 0 else DARK)
                        if row_index == 0:
                            _set_cell_shading(cell, BURGUNDY)
                document.add_paragraph()
            continue
        bullet = re.match(r"^-\s+(.+)", line)
        numbered = re.match(r"^\d+\.\s+(.+)", line)
        if bullet or numbered:
            flush_paragraph()
            text = _clean_inline((bullet or numbered).group(1))
            document.add_paragraph(text, style="List Bullet" if bullet else "List Number")
            index += 1
            continue
        paragraph_lines.append(line.strip().removesuffix("  "))
        index += 1
    flush_paragraph()
    document.save(REPORT_DOCX)


def _slide_background(slide, color: str = CREAM) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = PptxColor.from_string(color)


def _add_footer(slide, number: int) -> None:
    box = slide.shapes.add_textbox(PptxInches(0.45), PptxInches(7.18), PptxInches(12.4), PptxInches(0.22))
    frame = box.text_frame
    frame.clear()
    paragraph = frame.paragraphs[0]
    paragraph.text = f"Solana Wallet Risk  |  anomaly analysis, not confirmed fraud  |  {number}"
    paragraph.font.size = PptxPt(8)
    paragraph.font.color.rgb = PptxColor.from_string(MUTED)
    paragraph.alignment = PP_ALIGN.RIGHT


def _add_title(slide, title: str, subtitle: str | None = None) -> None:
    box = slide.shapes.add_textbox(PptxInches(0.6), PptxInches(0.35), PptxInches(12.1), PptxInches(0.75))
    frame = box.text_frame
    frame.clear()
    paragraph = frame.paragraphs[0]
    paragraph.text = title
    paragraph.font.size = PptxPt(25)
    paragraph.font.bold = True
    paragraph.font.color.rgb = PptxColor.from_string(BURGUNDY)
    if subtitle:
        p = frame.add_paragraph()
        p.text = subtitle
        p.font.size = PptxPt(11)
        p.font.color.rgb = PptxColor.from_string(MUTED)


def _add_bullets(slide, items: list[str], *, x=0.75, y=1.35, w=5.6, h=5.4, size=20) -> None:
    box = slide.shapes.add_textbox(PptxInches(x), PptxInches(y), PptxInches(w), PptxInches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    for index, item in enumerate(items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = f"• {item}"
        paragraph.level = 0
        paragraph.font.size = PptxPt(size)
        paragraph.font.color.rgb = PptxColor.from_string(DARK)
        paragraph.space_after = PptxPt(11)


def _add_stat_card(slide, x: float, y: float, value: str, label: str, *, color: str = BURGUNDY) -> None:
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptxInches(x), PptxInches(y), PptxInches(2.65), PptxInches(1.25))
    shape.fill.solid()
    shape.fill.fore_color.rgb = PptxColor.from_string(color)
    shape.line.color.rgb = PptxColor.from_string(color)
    frame = shape.text_frame
    frame.clear()
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = frame.paragraphs[0]
    p.text = value
    p.alignment = PP_ALIGN.CENTER
    p.font.size = PptxPt(24)
    p.font.bold = True
    p.font.color.rgb = PptxColor.from_string(WHITE)
    p2 = frame.add_paragraph()
    p2.text = label
    p2.alignment = PP_ALIGN.CENTER
    p2.font.size = PptxPt(10)
    p2.font.color.rgb = PptxColor.from_string(WHITE)


def _add_picture(slide, name: str, *, x=6.3, y=1.25, w=6.45) -> None:
    slide.shapes.add_picture(str(ASSETS / name), PptxInches(x), PptxInches(y), width=PptxInches(w))


def generate_presentation() -> None:
    presentation = Presentation()
    presentation.slide_width = PptxInches(13.333)
    presentation.slide_height = PptxInches(7.5)
    presentation.core_properties.title = "Solana Wallet Risk"
    presentation.core_properties.subject = "Unsupervised Wallet Anomaly Detection on Solana"
    presentation.core_properties.author = "Student submission"
    presentation.core_properties.created = datetime(2026, 11, 19, tzinfo=UTC)
    presentation.core_properties.modified = datetime(2026, 11, 19, tzinfo=UTC)
    blank = presentation.slide_layouts[6]

    slide = presentation.slides.add_slide(blank)
    _slide_background(slide, BURGUNDY)
    title = slide.shapes.add_textbox(PptxInches(0.85), PptxInches(1.7), PptxInches(11.8), PptxInches(2.1))
    frame = title.text_frame
    frame.clear()
    p = frame.paragraphs[0]
    p.text = "Solana Wallet Risk"
    p.font.size = PptxPt(40)
    p.font.bold = True
    p.font.color.rgb = PptxColor.from_string(WHITE)
    p.alignment = PP_ALIGN.CENTER
    p2 = frame.add_paragraph()
    p2.text = "Unsupervised Wallet Anomaly Detection on Solana"
    p2.font.size = PptxPt(22)
    p2.font.color.rgb = PptxColor.from_string(CREAM)
    p2.alignment = PP_ALIGN.CENTER
    p3 = frame.add_paragraph()
    p3.text = "DEX event audit • point-in-time features • comparative anomaly ranking • secured delivery"
    p3.font.size = PptxPt(13)
    p3.font.color.rgb = PptxColor.from_string(ROSE)
    p3.alignment = PP_ALIGN.CENTER
    _add_footer(slide, 1)

    slide = presentation.slides.add_slide(blank)
    _slide_background(slide)
    _add_title(slide, "Problem and objectives")
    _add_bullets(slide, [
        "DEX activity is temporal, sparse and not reliably labelled.",
        "Build wallet snapshots using only events available before scoring.",
        "Compare three different definitions of statistical unusualness.",
        "Deliver reproducible results through a protected review application.",
    ], w=6.3)
    _add_stat_card(slide, 7.2, 1.65, "0", "verified fraud labels")
    _add_stat_card(slide, 10.0, 1.65, "29", "registered features", color=DARK)
    _add_stat_card(slide, 7.2, 3.2, "3", "unsupervised methods", color=GREEN)
    _add_stat_card(slide, 10.0, 3.2, "1", "selected ranker", color=AMBER)
    _add_footer(slide, 2)

    slide = presentation.slides.add_slide(blank)
    _slide_background(slide)
    _add_title(slide, "Dune Analytics dataset", "Query 6561080, confirmed source")
    _add_stat_card(slide, 0.75, 1.35, "10,800", "DEX swap events")
    _add_stat_card(slide, 3.65, 1.35, "2,312", "wallet identifiers", color=DARK)
    _add_stat_card(slide, 6.55, 1.35, "9,221", "transaction hashes", color=GREEN)
    _add_stat_card(slide, 9.45, 1.35, "18", "source columns", color=AMBER)
    _add_bullets(slide, [
        "January to November 2025 UTC",
        "Wallet-attributed DEX swap-event schema",
        "11 month-bounded blocks: ten at 1,000 rows, April at 800",
        "Historical extraction metadata and data-sharing rights are incomplete",
    ], x=1.0, y=3.15, w=11.2, h=3.0, size=18)
    _add_footer(slide, 3)

    slide = presentation.slides.add_slide(blank)
    _slide_background(slide)
    _add_title(slide, "End-to-end pipeline", "Training is local and offline; the API never fits on request")
    _add_picture(slide, "pipeline_architecture.png", x=0.65, y=1.3, w=12.0)
    _add_footer(slide, 4)

    slide = presentation.slides.add_slide(blank)
    _slide_background(slide)
    _add_title(slide, "Data quality and preprocessing")
    _add_stat_card(slide, 0.75, 1.25, "10,798", "retained")
    _add_stat_card(slide, 3.65, 1.25, "2", "quarantined", color=AMBER)
    _add_stat_card(slide, 6.55, 1.25, "0", "silently removed", color=GREEN)
    _add_stat_card(slide, 9.45, 1.25, "7,303", "missing fees retained", color=DARK)
    _add_bullets(slide, [
        "Raw values and stable row lineage are preserved.",
        "Timestamps are normalized to UTC and ordering is deterministic.",
        "Repeated transaction hashes are not blindly deduplicated.",
        "Large-value review flags are retained without capping.",
    ], x=1.0, y=3.1, w=11.2, h=3.0, size=18)
    _add_footer(slide, 5)

    slide = presentation.slides.add_slide(blank)
    _slide_background(slide)
    _add_title(slide, "Features and temporal design", "Strict rule: block_time < as_of")
    _add_bullets(slide, [
        "29 features across activity, value, time, diversity, concentration and coverage.",
        "Wallet and transaction identifiers are not direct predictors.",
        "Training-fitted transformations never learn from later snapshots.",
        "Full later cohorts are longitudinal; entrants are reported separately.",
    ], w=5.6, size=17)
    _add_picture(slide, "temporal_cohorts.png", x=6.2, y=1.25, w=6.4)
    _add_footer(slide, 6)

    slide = presentation.slides.add_slide(blank)
    _slide_background(slide)
    _add_title(slide, "Three models, three anomaly concepts")
    _add_stat_card(slide, 0.85, 1.5, "Isolation Forest", "global nonlinear isolation", color=BURGUNDY)
    _add_stat_card(slide, 3.85, 1.5, "LOF", "local-density comparison", color=ROSE)
    _add_stat_card(slide, 6.85, 1.5, "Robust MAD", "transparent deviations", color=GREEN)
    _add_stat_card(slide, 9.85, 1.5, "Sep 2025", "shared training reference", color=DARK)
    _add_bullets(slide, [
        "Median imputation is fitted on training only.",
        "LOF additionally uses a training-fitted robust scaler.",
        "Higher scores mean more unusual relative to the reference.",
        "No score is a probability or verified fraud label.",
    ], x=1.1, y=3.25, w=11.0, h=2.6, size=18)
    _add_footer(slide, 7)

    slide = presentation.slides.add_slide(blank)
    _slide_background(slide)
    _add_title(slide, "Model selection and evaluation")
    _add_bullets(slide, [
        "IF validation stability: 0.9923 to 0.9980",
        "IF versus MAD holdout agreement: 0.8662",
        "IF versus LOF holdout agreement: 0.0488",
        "All-three overlap: 0 at top 10, 7 at top 100",
    ], w=5.45, size=17)
    _add_picture(slide, "holdout_rank_agreement.png", x=6.1, y=1.25, w=6.55)
    _add_footer(slide, 8)

    slide = presentation.slides.add_slide(blank)
    _slide_background(slide)
    _add_title(slide, "Application architecture", "Firebase identity, FastAPI authorization and checksum-bound inference")
    _add_picture(slide, "application_architecture.png", x=0.65, y=1.2, w=12.0)
    _add_footer(slide, 9)

    slide = presentation.slides.add_slide(blank)
    _slide_background(slide)
    _add_title(slide, "Live demonstration", "https://solana-wallet-risk.web.app/#home")
    _add_bullets(slide, [
        "Sign in with an approved Google account.",
        "Load the clearly labelled synthetic example.",
        "Run single and batch analysis.",
        "Explain score, rank, review capacity and feature context.",
        "Sign out and confirm protected results are cleared.",
    ], w=6.3, size=18)
    _add_stat_card(slide, 8.0, 1.55, "200", "/v1/health", color=GREEN)
    _add_stat_card(slide, 10.0, 3.15, "401", "protected without token", color=AMBER)
    _add_stat_card(slide, 8.0, 4.75, "200", "/readyz model ready", color=GREEN)
    _add_footer(slide, 10)

    slide = presentation.slides.add_slide(blank)
    _slide_background(slide)
    _add_title(slide, "Results and limitations")
    _add_bullets(slide, [
        "Deterministic audit, feature, model and artifact reproduction passed.",
        "Detector rankings differ materially, especially at small review budgets.",
        "No verified outcomes exist for detection-effectiveness metrics.",
        "No counterparty evidence exists for coordination claims.",
        "Historical Dune extraction metadata and data-sharing rights remain incomplete.",
    ], x=0.85, y=1.35, w=6.1, size=17)
    _add_picture(slide, "parameter_sensitivity.png", x=6.7, y=1.25, w=5.9)
    _add_footer(slide, 11)

    slide = presentation.slides.add_slide(blank)
    _slide_background(slide, BURGUNDY)
    title = slide.shapes.add_textbox(PptxInches(1.0), PptxInches(1.25), PptxInches(11.3), PptxInches(1.0))
    frame = title.text_frame
    frame.clear()
    p = frame.paragraphs[0]
    p.text = "Conclusion"
    p.font.size = PptxPt(34)
    p.font.bold = True
    p.font.color.rgb = PptxColor.from_string(WHITE)
    p.alignment = PP_ALIGN.CENTER
    body = slide.shapes.add_textbox(PptxInches(1.4), PptxInches(2.45), PptxInches(10.5), PptxInches(3.3))
    tf = body.text_frame
    tf.clear()
    statements = [
        "A reproducible and secured anomaly-ranking workflow is implemented.",
        "Isolation Forest is the most stable tested operational ranker.",
        "The output supports review prioritization, not fraud accusation.",
        "Stronger claims require lawful provenance, independent outcomes and relational evidence.",
    ]
    for index, statement in enumerate(statements):
        p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        p.text = statement
        p.font.size = PptxPt(20)
        p.font.color.rgb = PptxColor.from_string(CREAM)
        p.alignment = PP_ALIGN.CENTER
        p.space_after = PptxPt(16)
    _add_footer(slide, 12)

    presentation.save(PRESENTATION)


def render_pdf() -> None:
    profile = Path("/tmp/solana_wallet_risk_libreoffice")
    profile.mkdir(parents=True, exist_ok=True)
    command = [
        "libreoffice",
        "--headless",
        f"-env:UserInstallation=file://{profile}",
        "--convert-to",
        "pdf",
        "--outdir",
        str(OUTPUT),
        str(REPORT_DOCX),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0 or not REPORT_PDF.is_file():
        raise RuntimeError(
            "LibreOffice could not render the report PDF: "
            + (completed.stderr.strip() or completed.stdout.strip())
        )


def verify_outputs() -> None:
    for path in (REPORT_DOCX, PRESENTATION):
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad is not None:
                raise RuntimeError(f"Corrupt Office archive member in {path.name}: {bad}")
    if REPORT_PDF.stat().st_size < 10_000:
        raise RuntimeError("Rendered PDF is unexpectedly small")
    document = Document(REPORT_DOCX)
    if len(document.paragraphs) < 50 or len(document.tables) < 3:
        raise RuntimeError("Generated DOCX is missing expected report content")
    presentation = Presentation(PRESENTATION)
    if len(presentation.slides) != 12:
        raise RuntimeError("Generated presentation must contain exactly 12 slides")


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    generate_figures()
    markdown_to_docx()
    generate_presentation()
    render_pdf()
    verify_outputs()
    print(f"Report source: {REPORT_SOURCE}")
    print(f"Editable report: {REPORT_DOCX}")
    print(f"Rendered report: {REPORT_PDF}")
    print(f"Editable presentation: {PRESENTATION}")
    print("Submission asset validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
