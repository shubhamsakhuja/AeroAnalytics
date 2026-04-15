"""
PDF Report Generator — clean layout, high-res chart, branded.
"""
import os, base64, tempfile
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Image as RLImage, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


BRAND  = colors.HexColor("#c96442")
DARK   = colors.HexColor("#1a1a1a")
GRAY   = colors.HexColor("#6b7280")
LIGHT  = colors.HexColor("#f9f9f7")
ACCENT = colors.HexColor("#fff0ed")
GREEN  = colors.HexColor("#2d8a5e")


def _fmt_col(col: str) -> str:
    return col.replace("_", " ").title()


def generate_report(
    question: str,
    sql: str,
    df: pd.DataFrame,
    insight: str,
    chart_image: str = None,
    output_dir: str = None
) -> str:
    if output_dir is None:
        output_dir = tempfile.gettempdir()

    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"aeroanalytics_{ts}.pdf")

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=22*mm, bottomMargin=20*mm
    )

    # ── Styles ───────────────────────────────────────────────
    def sty(name, **kw):
        defaults = dict(fontName="Helvetica", fontSize=10,
                        textColor=DARK, leading=14, spaceAfter=4)
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    s_logo    = sty("logo",   fontName="Helvetica-Bold", fontSize=22,
                               textColor=DARK, spaceAfter=2, leading=26)
    s_sub     = sty("sub",    fontSize=10, textColor=BRAND, spaceAfter=0, leading=13)
    s_h2      = sty("h2",     fontName="Helvetica-Bold", fontSize=12,
                               textColor=DARK, spaceBefore=10, spaceAfter=5)
    s_body    = sty("body",   fontSize=10, textColor=colors.HexColor("#333333"),
                               leading=16, spaceAfter=4)
    s_code    = sty("code",   fontName="Courier", fontSize=8,
                               textColor=colors.HexColor("#7dd3fc"),
                               backColor=colors.HexColor("#0d1117"),
                               leftIndent=8, rightIndent=8, leading=12)
    s_footer  = sty("footer", fontSize=7, textColor=GRAY,
                               alignment=TA_CENTER, leading=10)
    s_note    = sty("note",   fontSize=8, textColor=GRAY, leading=11)

    story = []

    # ── HEADER — logo on left, date on right ─────────────────
    header_data = [[
        Paragraph("AeroAnalytics", s_logo),
        Paragraph(datetime.now().strftime("%d %B %Y, %H:%M"), 
                  sty("date", fontSize=9, textColor=GRAY, alignment=1))
    ]]
    header_tbl = Table(header_data, colWidths=[130*mm, 44*mm])
    header_tbl.setStyle(TableStyle([
        ("VALIGN",  (0,0), (-1,-1), "BOTTOM"),
        ("PADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(header_tbl)
    story.append(Paragraph("AI-Generated Business Intelligence Report", s_sub))
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BRAND))
    story.append(Spacer(1, 6*mm))

    # ── METADATA TABLE ────────────────────────────────────────
    meta = [
        ["Question",      question],
        ["Rows returned", f"{len(df):,}"],
        ["Columns",       ", ".join(_fmt_col(c) for c in df.columns[:6]) +
                          ("…" if len(df.columns) > 6 else "")],
    ]
    mt = Table(meta, colWidths=[36*mm, 138*mm])
    mt.setStyle(TableStyle([
        ("FONTNAME",       (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",       (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE",       (0,0), (-1,-1), 9),
        ("TEXTCOLOR",      (0,0), (0,-1), DARK),
        ("TEXTCOLOR",      (1,0), (1,-1), GRAY),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [ACCENT, colors.white]),
        ("TOPPADDING",     (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 6),
        ("LEFTPADDING",    (0,0), (-1,-1), 8),
        ("BOX",  (0,0), (-1,-1), 0.5, colors.HexColor("#e0ddd8")),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#e0ddd8")),
    ]))
    story.append(mt)
    story.append(Spacer(1, 7*mm))

    # ── CHART IMAGE ───────────────────────────────────────────
    if chart_image:
        try:
            if "," in chart_image:
                chart_image = chart_image.split(",", 1)[1]
            img_data = base64.b64decode(chart_image)
            img_path = os.path.join(output_dir, f"chart_{ts}.png")
            with open(img_path, "wb") as f:
                f.write(img_data)

            story.append(Paragraph("Chart", s_h2))
            # Render at 2x resolution (174mm wide, auto height)
            # Chart.js canvas is typically 800-1200px wide → looks sharp
            story.append(RLImage(img_path, width=174*mm, height=88*mm,
                                  kind="proportional"))
            story.append(Spacer(1, 6*mm))
        except Exception as e:
            print(f"[pdf] chart embed failed: {e}")

    # ── KEY INSIGHT ───────────────────────────────────────────
    story.append(Paragraph("Key Insight", s_h2))
    clean = (insight or "—").replace("**", "").replace("*", "")
    story.append(Paragraph(clean, s_body))
    story.append(Spacer(1, 5*mm))

    # ── SQL QUERY ─────────────────────────────────────────────
    if sql:
        story.append(Paragraph("SQL Query Used", s_h2))
        sql_tbl = Table(
            [[Paragraph(sql.replace("\n", "<br/>"), s_code)]],
            colWidths=[174*mm]
        )
        sql_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#0d1117")),
            ("TOPPADDING",    (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
            ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ]))
        story.append(sql_tbl)
        story.append(Spacer(1, 6*mm))

    # ── DATA TABLE ────────────────────────────────────────────
    story.append(Paragraph("Results Data", s_h2))
    display_df  = df.head(50)
    header_row  = [_fmt_col(c) for c in display_df.columns]
    data_rows   = [header_row] + [
        [str(v) if v is not None else "" for v in row]
        for row in display_df.values.tolist()
    ]
    col_w = 174 * mm / len(header_row)
    dt = Table(data_rows, colWidths=[col_w]*len(header_row), repeatRows=1)
    dt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),  (-1,0),  BRAND),
        ("TEXTCOLOR",     (0,0),  (-1,0),  colors.white),
        ("FONTNAME",      (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),  (-1,-1), 8),
        ("ROWBACKGROUNDS",(0,1),  (-1,-1), [colors.white, LIGHT]),
        ("GRID",          (0,0),  (-1,-1), 0.3, colors.HexColor("#e0ddd8")),
        ("TOPPADDING",    (0,0),  (-1,-1), 5),
        ("BOTTOMPADDING", (0,0),  (-1,-1), 5),
        ("LEFTPADDING",   (0,0),  (-1,-1), 6),
        ("ALIGN",         (0,0),  (-1,-1), "LEFT"),
    ]))
    story.append(dt)

    if len(df) > 50:
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(
            f"Showing first 50 of {len(df):,} rows. Download CSV for the full dataset.",
            s_note))

    # ── FOOTER ────────────────────────────────────────────────
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#e0ddd8")))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "Generated by AeroAnalytics &nbsp;·&nbsp; Powered by Claude on AWS Bedrock "
        "&nbsp;·&nbsp; © 2026 Shubham Sakhuja",
        s_footer))

    doc.build(story)
    return path
