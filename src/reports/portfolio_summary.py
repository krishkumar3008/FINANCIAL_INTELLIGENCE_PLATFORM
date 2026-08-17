import os
import sys

sys.path.insert(0, os.path.abspath("."))
import sqlite3

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def get_trend_symbol(
    curr: float | None, prev: float | None, lower_is_better: bool = False
) -> str:
    """
    Returns ↑ if metric improved, ↓ if declined, → if flat within 2%.
    """
    if curr is None or prev is None or pd.isna(curr) or pd.isna(prev) or prev == 0:
        return "→"

    pct_change = (curr - prev) / abs(prev)

    if abs(pct_change) <= 0.02:
        return "→"

    if lower_is_better:
        return "↑" if pct_change < 0 else "↓"
    else:
        return "↑" if pct_change > 0 else "↓"


def generate_portfolio_summary(
    db_path: str = "nifty100.db",
    output_pdf: str = "reports/portfolio/portfolio_summary.pdf",
) -> str:
    """
    Generates reports/portfolio/portfolio_summary.pdf featuring one company per page in alphabetical order by ticker.
    Includes Top 6 KPIs and trend arrows (↑, ↓, →).
    """
    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    companies = pd.read_sql(
        "SELECT id, company_name, roe_percentage, roce_percentage FROM companies ORDER BY id ASC",
        conn,
    ).to_dict("records")
    sectors_df = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    sector_map = {r["company_id"]: r["broad_sector"] for _, r in sectors_df.iterrows()}

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        leftMargin=25,
        rightMargin=25,
        topMargin=25,
        bottomMargin=25,
    )

    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#FFFFFF"),
        alignment=1,
    )
    style_sub = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#E2E8F0"),
        alignment=1,
    )

    style_comp_name = ParagraphStyle(
        "CompName",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1A365D"),
    )
    style_comp_sub = ParagraphStyle(
        "CompSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#4A5568"),
    )

    style_kpi_label = ParagraphStyle(
        "KPILabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#718096"),
    )
    style_kpi_val = ParagraphStyle(
        "KPIVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        textColor=colors.HexColor("#1A365D"),
    )
    style_kpi_trend = ParagraphStyle(
        "KPITrend",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
    )

    story = []

    # Portfolio Cover Bar
    cover_data = [
        [Paragraph("<b>NIFTY 100 PORTFOLIO SUMMARY REPORT</b>", style_title)],
        [
            Paragraph(
                f"Comprehensive Executive Dashboard | {len(companies)} Companies",
                style_sub,
            )
        ],
    ]
    cover_tbl = Table(cover_data, colWidths=[545])
    cover_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1A365D")),
                ("PADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(cover_tbl)
    story.append(Spacer(1, 15))

    for idx, comp in enumerate(companies):
        comp_id = comp["id"]
        comp_name = comp["company_name"]
        sector = sector_map.get(comp_id, "N/A")

        pnl_df = pd.read_sql(
            "SELECT sales, net_profit, opm_percentage FROM profitandloss WHERE company_id = ? AND year != 9999 ORDER BY year ASC",
            conn,
            params=(comp_id,),
        )
        ratios_df = pd.read_sql(
            "SELECT return_on_equity_pct, debt_to_equity, free_cash_flow_cr FROM financial_ratios WHERE company_id = ? AND year != 9999 ORDER BY year ASC",
            conn,
            params=(comp_id,),
        )
        mcap_df = pd.read_sql(
            "SELECT market_cap_crore, pe_ratio FROM market_cap WHERE company_id = ? AND year != 9999 ORDER BY year ASC",
            conn,
            params=(comp_id,),
        )

        curr_pnl = pnl_df.iloc[-1] if not pnl_df.empty else {}
        prev_pnl = pnl_df.iloc[-2] if len(pnl_df) >= 2 else {}

        curr_rat = ratios_df.iloc[-1] if not ratios_df.empty else {}
        prev_rat = ratios_df.iloc[-2] if len(ratios_df) >= 2 else {}

        curr_mc = mcap_df.iloc[-1] if not mcap_df.empty else {}
        prev_mc = mcap_df.iloc[-2] if len(mcap_df) >= 2 else {}

        # Metric values & Trends
        mcap_c = curr_mc.get("market_cap_crore", 0) or 0
        mcap_p = prev_mc.get("market_cap_crore", 0) or 0
        t_mcap = get_trend_symbol(mcap_c, mcap_p)

        pe_c = curr_mc.get("pe_ratio", 0) or 0
        pe_p = prev_mc.get("pe_ratio", 0) or 0
        t_pe = get_trend_symbol(pe_c, pe_p, lower_is_better=True)

        sales_c = curr_pnl.get("sales", 0) or 0
        sales_p = prev_pnl.get("sales", 0) or 0
        t_sales = get_trend_symbol(sales_c, sales_p)

        pat_c = curr_pnl.get("net_profit", 0) or 0
        pat_p = prev_pnl.get("net_profit", 0) or 0
        t_pat = get_trend_symbol(pat_c, pat_p)

        roe_c = (
            comp.get("roe_percentage") or curr_rat.get("return_on_equity_pct", 0) or 0
        )
        roe_p = prev_rat.get("return_on_equity_pct", 0) or roe_c
        t_roe = get_trend_symbol(roe_c, roe_p)

        de_c = curr_rat.get("debt_to_equity", 0) or 0
        de_p = prev_rat.get("debt_to_equity", 0) or 0
        t_de = get_trend_symbol(de_c, de_p, lower_is_better=True)

        # Company Header Card
        comp_hdr_data = [
            [Paragraph(f"<b>{comp_name} ({comp_id})</b>", style_comp_name)],
            [Paragraph(f"Sector: <b>{sector}</b>", style_comp_sub)],
        ]
        comp_hdr_tbl = Table(comp_hdr_data, colWidths=[545])
        comp_hdr_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
                    ("PADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(comp_hdr_tbl)
        story.append(Spacer(1, 10))

        # Helper for colored trend arrow
        def fmt_trend(symbol: str) -> Paragraph:
            if symbol == "↑":
                c_code = "#2F855A"
            elif symbol == "↓":
                c_code = "#C53030"
            else:
                c_code = "#718096"
            style_arr = ParagraphStyle(
                "TrendArr", parent=style_kpi_trend, textColor=colors.HexColor(c_code)
            )
            return Paragraph(f"<b>{symbol}</b>", style_arr)

        # Top 6 KPIs Grid (2 rows of 3)
        kpi_grid_data = [
            [
                Table(
                    [
                        [Paragraph("MARKET CAP", style_kpi_label)],
                        [Paragraph(f"₹{mcap_c:,.0f} Cr", style_kpi_val)],
                        [fmt_trend(t_mcap)],
                    ],
                    colWidths=[170],
                ),
                Table(
                    [
                        [Paragraph("P/E RATIO", style_kpi_label)],
                        [Paragraph(f"{pe_c:.1f}x" if pe_c else "N/A", style_kpi_val)],
                        [fmt_trend(t_pe)],
                    ],
                    colWidths=[170],
                ),
                Table(
                    [
                        [Paragraph("REVENUE (SALES)", style_kpi_label)],
                        [Paragraph(f"₹{sales_c:,.0f} Cr", style_kpi_val)],
                        [fmt_trend(t_sales)],
                    ],
                    colWidths=[170],
                ),
            ],
            [
                Table(
                    [
                        [Paragraph("NET PROFIT (PAT)", style_kpi_label)],
                        [Paragraph(f"₹{pat_c:,.0f} Cr", style_kpi_val)],
                        [fmt_trend(t_pat)],
                    ],
                    colWidths=[170],
                ),
                Table(
                    [
                        [Paragraph("ROE (%)", style_kpi_label)],
                        [Paragraph(f"{roe_c:.1f}%", style_kpi_val)],
                        [fmt_trend(t_roe)],
                    ],
                    colWidths=[170],
                ),
                Table(
                    [
                        [Paragraph("DEBT / EQUITY", style_kpi_label)],
                        [Paragraph(f"{de_c:.2f}", style_kpi_val)],
                        [fmt_trend(t_de)],
                    ],
                    colWidths=[170],
                ),
            ],
        ]

        grid_table = Table(kpi_grid_data, colWidths=[181, 181, 181])
        grid_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(grid_table)

        if idx < len(companies) - 1:
            story.append(PageBreak())

    conn.close()

    doc.build(story)
    print(f"Portfolio Summary generated -> {output_pdf} ({len(companies)} pages)")
    return output_pdf


if __name__ == "__main__":
    generate_portfolio_summary()
