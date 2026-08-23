import io
import os
import sqlite3

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_chart_revenue_pat(pnl_df: pd.DataFrame) -> io.BytesIO:
    """Generates 10-year Revenue and Net Profit side-by-side bar chart."""
    df_clean = pnl_df[pnl_df["year"] != 9999].sort_values("year").tail(10)
    years = [str(y) for y in df_clean["year"]]
    sales = df_clean["sales"].fillna(0).tolist()
    pat = df_clean["net_profit"].fillna(0).tolist()

    x = np.arange(len(years))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7.5, 2.3), dpi=150)
    ax.bar(x - width / 2, sales, width, label="Revenue (Sales)", color="#1A365D")
    ax.bar(x + width / 2, pat, width, label="Net Profit (PAT)", color="#2B6CB0")

    ax.set_title(
        "10-Year Revenue & Net Profit Trend (Rs. Cr)",
        fontsize=10,
        fontweight="bold",
        pad=4,
        color="#1A365D",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(years, fontsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close("all")
    buf.seek(0)
    return buf


def generate_chart_roe_roce(ratios_df: pd.DataFrame, comp_row: dict) -> io.BytesIO:
    """Generates ROE and ROCE line chart."""
    df_clean = ratios_df[ratios_df["year"] != 9999].sort_values("year").tail(10)
    years = [str(y) for y in df_clean["year"]]
    roe = df_clean["return_on_equity_pct"].fillna(0).tolist()

    # Use roce from ratios or fallback to company level
    roce = []
    for _, r in df_clean.iterrows():
        val = r.get("roce_percentage")
        if pd.isna(val) or val is None:
            val = comp_row.get("roce_percentage", 15.0)
        roce.append(val if pd.notna(val) else 15.0)

    if not years:
        years = ["Latest"]
        roe = [comp_row.get("roe_percentage", 15.0)]
        roce = [comp_row.get("roce_percentage", 15.0)]

    fig, ax = plt.subplots(figsize=(7.5, 2.1), dpi=150)
    ax.plot(years, roe, marker="o", linewidth=2, label="ROE (%)", color="#2F855A")
    ax.plot(
        years,
        roce,
        marker="s",
        linewidth=2,
        linestyle="--",
        label="ROCE (%)",
        color="#D69E2E",
    )

    ax.set_title(
        "ROE & ROCE Return Trends (%)",
        fontsize=10,
        fontweight="bold",
        pad=4,
        color="#1A365D",
    )
    ax.tick_params(axis="both", labelsize=8)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close("all")
    buf.seek(0)
    return buf


def generate_chart_bs_composition(bs_df: pd.DataFrame) -> io.BytesIO:
    """Generates Balance Sheet stacked bar chart."""
    df_clean = bs_df[bs_df["year"] != 9999].sort_values("year").tail(10)
    years = [str(y) for y in df_clean["year"]]

    equity = (
        df_clean["equity_capital"].fillna(0) + df_clean["reserves"].fillna(0)
    ).tolist()
    borrowings = df_clean["borrowings"].fillna(0).tolist()
    other_liab = df_clean["other_liabilities"].fillna(0).tolist()

    x = np.arange(len(years))
    width = 0.55

    fig, ax = plt.subplots(figsize=(7.5, 2.2), dpi=150)
    ax.bar(x, equity, width, label="Equity & Reserves", color="#2B6CB0")
    ax.bar(x, borrowings, width, bottom=equity, label="Borrowings", color="#C53030")
    bottom_other = np.array(equity) + np.array(borrowings)
    ax.bar(
        x,
        other_liab,
        width,
        bottom=bottom_other,
        label="Other Liabilities",
        color="#718096",
    )

    ax.set_title(
        "Balance Sheet Liabilities Composition (Rs. Cr)",
        fontsize=10,
        fontweight="bold",
        pad=4,
        color="#1A365D",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(years, fontsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close("all")
    buf.seek(0)
    return buf


def generate_chart_cashflow_waterfall(cf_df: pd.DataFrame) -> io.BytesIO:
    """Generates Cash Flow components bar chart for latest year."""
    df_clean = cf_df[cf_df["year"] != 9999]
    latest = df_clean.iloc[-1] if not df_clean.empty else {}

    cfo = float(latest.get("operating_activity", 0) or 0)
    cfi = float(latest.get("investing_activity", 0) or 0)
    cff = float(latest.get("financing_activity", 0) or 0)
    net_cf = float(latest.get("net_cash_flow", 0) or (cfo + cfi + cff))

    categories = ["CFO (Ops)", "CFI (Inv)", "CFF (Fin)", "Net Cash Flow"]
    values = [cfo, cfi, cff, net_cf]
    bar_colors = ["#2F855A" if v >= 0 else "#C53030" for v in values]

    fig, ax = plt.subplots(figsize=(7.5, 2.1), dpi=150)
    bars = ax.bar(categories, values, color=bar_colors, width=0.45)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")

    min_val, max_val = min(values), max(values)
    span = max(abs(min_val), abs(max_val), 100)
    ax.set_ylim(min_val - (span * 0.3), max_val + (span * 0.3))

    for bar, val in zip(bars, values):
        y_offset = span * 0.06 if val >= 0 else -span * 0.12
        va = "bottom" if val >= 0 else "top"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + y_offset,
            f"Rs.{val:,.0f}",
            ha="center",
            va=va,
            fontsize=8,
            fontweight="bold",
            color="#1A365D",
        )

    latest_yr = latest.get("year", "Latest")
    ax.set_title(
        f"Latest Cash Flow Breakdown FY{latest_yr} (Rs. Cr)",
        fontsize=10,
        fontweight="bold",
        pad=4,
        color="#1A365D",
    )
    ax.tick_params(axis="both", labelsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close("all")
    buf.seek(0)
    return buf


def format_kpi_value(val, is_currency=False, is_ratio=False, is_pct=False, default="N/A") -> str:
    """Formats numeric values cleanly and safely handles NaN / None."""
    if val is None or pd.isna(val):
        return default
    try:
        val_f = float(val)
        if np.isnan(val_f):
            return default
        if is_currency:
            return f"Rs.{val_f:,.0f} Cr"
        if is_ratio:
            return f"{val_f:.1f}x"
        if is_pct:
            return f"{val_f:.1f}%"
        return f"{val_f:.2f}"
    except Exception:
        return default


def generate_company_tearsheet(
    company_id: str,
    db_path: str = "nifty100.db",
    output_pdf: str | None = None,
    pros_cons_df: pd.DataFrame | None = None,
    intel_df: pd.DataFrame | None = None,
) -> str:
    """
    Generates a 2-page ReportLab PDF Tearsheet for the given company.
    """
    if output_pdf is None:
        output_pdf = f"reports/tearsheets/{company_id}_tearsheet.pdf"

    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    comp = conn.execute(
        "SELECT * FROM companies WHERE id = ?", (company_id,)
    ).fetchone()
    if not comp:
        conn.close()
        raise ValueError(f"Company {company_id} not found in database.")

    comp_dict = dict(comp)
    sector_row = conn.execute(
        "SELECT broad_sector, sub_sector FROM sectors WHERE company_id = ?",
        (company_id,),
    ).fetchone()
    broad_sector = sector_row["broad_sector"] if sector_row else "N/A"

    pnl_df = pd.read_sql(
        "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC",
        conn,
        params=(company_id,),
    )
    bs_df = pd.read_sql(
        "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year ASC",
        conn,
        params=(company_id,),
    )
    cf_df = pd.read_sql(
        "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year ASC",
        conn,
        params=(company_id,),
    )
    ratios_df = pd.read_sql(
        "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year ASC",
        conn,
        params=(company_id,),
    )
    mcap_df = pd.read_sql(
        "SELECT * FROM market_cap WHERE company_id = ? ORDER BY year ASC",
        conn,
        params=(company_id,),
    )

    conn.close()

    # Fetch Pros & Cons
    if pros_cons_df is not None:
        c_pros = pros_cons_df[
            (pros_cons_df["company_id"] == company_id) & (pros_cons_df["type"] == "pro")
        ]["text"].tolist()
        c_cons = pros_cons_df[
            (pros_cons_df["company_id"] == company_id) & (pros_cons_df["type"] == "con")
        ]["text"].tolist()
    else:
        c_pros = ["Strong financial performance and leading market positioning."]
        c_cons = ["Market volatility and competitive pressure."]

    # Latest Metrics for KPI Tiles
    latest_r = ratios_df.iloc[-1] if not ratios_df.empty else {}
    latest_m = mcap_df.iloc[-1] if not mcap_df.empty else {}

    mcap_str = format_kpi_value(latest_m.get("market_cap_crore"), is_currency=True)
    pe_str = format_kpi_value(latest_m.get("pe_ratio"), is_ratio=True)
    
    roe_val = comp_dict.get("roe_percentage") or latest_r.get("return_on_equity_pct")
    roe_str = format_kpi_value(roe_val, is_pct=True)

    roce_val = comp_dict.get("roce_percentage") or latest_r.get("roce_percentage")
    roce_str = format_kpi_value(roce_val, is_pct=True)

    de_val = latest_r.get("debt_to_equity")
    de_str = format_kpi_value(de_val, default="0.00x" if pd.notna(de_val) else "N/A")
    if de_str != "N/A" and not de_str.endswith("x"):
        de_str += "x"

    fcf_val = latest_r.get("free_cash_flow_cr")
    if (fcf_val is None or pd.isna(fcf_val)) and not cf_df.empty:
        l_cf = cf_df.iloc[-1]
        fcf_val = (l_cf.get("operating_activity", 0) or 0) + (
            l_cf.get("investing_activity", 0) or 0
        )
    fcf_str = format_kpi_value(fcf_val, is_currency=True)

    # ReportLab Document Setup
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    style_header_title = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=18,
        textColor=colors.HexColor("#FFFFFF"),
    )
    style_header_sub = ParagraphStyle(
        "HeaderSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#E2E8F0"),
    )
    style_kpi_label = ParagraphStyle(
        "KPILabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#4A5568"),
        alignment=1,
    )
    style_kpi_val = ParagraphStyle(
        "KPIVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#1A365D"),
        alignment=1,
    )
    style_sec_title = ParagraphStyle(
        "SecTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        textColor=colors.HexColor("#1A365D"),
    )
    style_pro_bullet = ParagraphStyle(
        "ProBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#2F855A"),
    )
    style_con_bullet = ParagraphStyle(
        "ConBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#C53030"),
    )

    story = []

    # PAGE 1
    # 1. Header Bar
    header_data = [
        [
            Paragraph(
                f"<b>{comp_dict.get('company_name', company_id).strip()} ({company_id})</b>",
                style_header_title,
            )
        ],
        [
            Paragraph(
                f"Sector: {broad_sector} | Nifty 100 Financial Intelligence Tearsheet",
                style_header_sub,
            )
        ],
    ]
    header_table = Table(header_data, colWidths=[555])
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1A365D")),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 8))

    # 2. KPI Tiles (6 tiles in 2 rows of 3)
    kpi_data = [
        [
            [
                Paragraph("MARKET CAP", style_kpi_label),
                Paragraph(mcap_str, style_kpi_val),
            ],
            [Paragraph("P/E RATIO", style_kpi_label), Paragraph(pe_str, style_kpi_val)],
            [Paragraph("ROE (%)", style_kpi_label), Paragraph(roe_str, style_kpi_val)],
        ],
        [
            [
                Paragraph("ROCE (%)", style_kpi_label),
                Paragraph(roce_str, style_kpi_val),
            ],
            [
                Paragraph("DEBT / EQUITY", style_kpi_label),
                Paragraph(de_str, style_kpi_val),
            ],
            [
                Paragraph("FREE CASH FLOW", style_kpi_label),
                Paragraph(fcf_str, style_kpi_val),
            ],
        ],
    ]
    kpi_table = Table(kpi_data, colWidths=[180, 180, 180], rowHeights=[36, 36])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # 3. Chart 1: Revenue & PAT Bar Chart
    buf_pnl = generate_chart_revenue_pat(pnl_df)
    story.append(Image(buf_pnl, width=555, height=170))
    story.append(Spacer(1, 10))

    # 4. Chart 2: ROE & ROCE Dual Axis Chart
    buf_ratios = generate_chart_roe_roce(ratios_df, comp_dict)
    story.append(Image(buf_ratios, width=555, height=155))

    # PAGE BREAK
    story.append(PageBreak())

    # PAGE 2
    # 1. Header Bar
    p2_header = [
        [
            Paragraph(
                f"<b>FINANCIAL STRUCTURE & NLP ANALYSIS — {company_id}</b>",
                style_header_title,
            )
        ],
        [
            Paragraph(
                "Capital Allocation Pattern, Balance Sheet & Cash Flow Diagnostics",
                style_header_sub,
            )
        ],
    ]
    p2_table = Table(p2_header, colWidths=[555])
    p2_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1A365D")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(p2_table)
    story.append(Spacer(1, 8))

    # 2. Chart 3: Balance Sheet Composition
    buf_bs = generate_chart_bs_composition(bs_df)
    story.append(Image(buf_bs, width=555, height=160))
    story.append(Spacer(1, 8))

    # 3. Chart 4: Cash Flow Waterfall
    buf_cf = generate_chart_cashflow_waterfall(cf_df)
    story.append(Image(buf_cf, width=555, height=155))
    story.append(Spacer(1, 10))

    # 4. Capital Allocation & Pros/Cons Section
    pros_html = "<br/>".join([f"• {p}" for p in c_pros[:4]])
    cons_html = "<br/>".join([f"• {c}" for c in c_cons[:5]])

    nlp_data = [
        [
            Paragraph("<b>CAPITAL ALLOCATION PATTERN: SHAREHOLDER RETURNS</b>", style_sec_title),
            Paragraph("", style_sec_title),
        ],
        [
            Paragraph("<b>STRENGTHS & PROS</b>", style_pro_bullet),
            Paragraph("<b>RISKS & CONS</b>", style_con_bullet),
        ],
        [
            Paragraph(pros_html, style_pro_bullet),
            Paragraph(cons_html, style_con_bullet),
        ],
    ]
    nlp_table = Table(nlp_data, colWidths=[270, 275])
    nlp_table.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (1, 0)),
                ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#2B6CB0")),
                ("TEXTCOLOR", (0, 0), (1, 0), colors.white),
                ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#F0FDF4")),
                ("BACKGROUND", (1, 1), (1, -1), colors.HexColor("#FEF2F2")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 1), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(nlp_table)

    # Build PDF
    doc.build(story)
    return output_pdf


if __name__ == "__main__":
    print("Testing tearsheet generation for ABB and ADANIENSOL...")
    generate_company_tearsheet("ABB")
    generate_company_tearsheet("ADANIENSOL")
    print("Tearsheet PDFs generated successfully.")
