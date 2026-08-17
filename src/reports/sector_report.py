import os
import sqlite3

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_sector_report(
    sector_name: str, db_path: str = "nifty100.db", output_pdf: str | None = None
) -> str:
    """
    Generates a sector summary PDF report for a given sector.
    Includes sector summary page with median KPIs + list of companies with 8 metrics.
    """
    if output_pdf is None:
        slug = sector_name.lower().replace(" ", "_").replace("&", "and")
        output_pdf = f"reports/sector/{slug}_report.pdf"

    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Fetch companies in sector
    if sector_name in ["Overall Portfolio", "All Sectors"]:
        comp_df = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    elif sector_name in ["Utilities & Infrastructure", "Utilities"]:
        comp_df = pd.read_sql(
            "SELECT company_id, broad_sector FROM sectors WHERE broad_sector IN ('Energy', 'Industrials') OR sub_sector LIKE '%Power%' OR sub_sector LIKE '%Infrastructure%'",
            conn,
        )
    else:
        comp_df = pd.read_sql(
            "SELECT company_id, broad_sector FROM sectors WHERE broad_sector = ?",
            conn,
            params=(sector_name,),
        )

    if comp_df.empty:
        # Fallback to energy/industrials if custom sector
        comp_df = pd.read_sql(
            "SELECT company_id, broad_sector FROM sectors LIMIT 10", conn
        )

    company_ids = comp_df["company_id"].tolist()

    # Query metrics for each company in sector
    company_metrics = []
    for comp_id in company_ids:
        c_row = conn.execute(
            "SELECT company_name, roe_percentage, roce_percentage FROM companies WHERE id = ?",
            (comp_id,),
        ).fetchone()
        comp_name = c_row["company_name"] if c_row else comp_id

        pnl_df = pd.read_sql(
            "SELECT sales, operating_profit, opm_percentage, net_profit FROM profitandloss WHERE company_id = ? AND year != 9999 ORDER BY year ASC",
            conn,
            params=(comp_id,),
        )
        ratios_df = pd.read_sql(
            "SELECT return_on_equity_pct, debt_to_equity, free_cash_flow_cr FROM financial_ratios WHERE company_id = ? AND year != 9999 ORDER BY year ASC",
            conn,
            params=(comp_id,),
        )
        mcap_df = pd.read_sql(
            "SELECT market_cap_crore FROM market_cap WHERE company_id = ? AND year != 9999 ORDER BY year ASC",
            conn,
            params=(comp_id,),
        )

        latest_pnl = pnl_df.iloc[-1] if not pnl_df.empty else {}
        latest_rat = ratios_df.iloc[-1] if not ratios_df.empty else {}
        latest_mc = mcap_df.iloc[-1] if not mcap_df.empty else {}

        mcap = latest_mc.get("market_cap_crore", 0) or 0
        sales = latest_pnl.get("sales", 0) or 0
        pat = latest_pnl.get("net_profit", 0) or 0
        opm = latest_pnl.get("opm_percentage", 0) or 0

        roe = (
            c_row["roe_percentage"]
            if (c_row and c_row["roe_percentage"] is not None)
            else latest_rat.get("return_on_equity_pct", 0) or 0
        )
        roce = (
            c_row["roce_percentage"]
            if (c_row and c_row["roce_percentage"] is not None)
            else latest_rat.get("roce_percentage", 0) or 0
        )
        de = latest_rat.get("debt_to_equity", 0) or 0
        fcf = latest_rat.get("free_cash_flow_cr", 0) or 0

        company_metrics.append(
            {
                "ticker": comp_id,
                "name": comp_name[:25],
                "mcap": mcap,
                "sales": sales,
                "pat": pat,
                "opm": opm,
                "roe": roe,
                "roce": roce,
                "de": de,
                "fcf": fcf,
            }
        )

    conn.close()

    df_m = pd.DataFrame(company_metrics)

    # Median Sector KPIs
    med_mcap = df_m["mcap"].median() if not df_m.empty else 0
    med_sales = df_m["sales"].median() if not df_m.empty else 0
    med_pat = df_m["pat"].median() if not df_m.empty else 0
    med_opm = df_m["opm"].median() if not df_m.empty else 0
    med_roe = df_m["roe"].median() if not df_m.empty else 0
    med_roce = df_m["roce"].median() if not df_m.empty else 0
    med_de = df_m["de"].median() if not df_m.empty else 0
    med_fcf = df_m["fcf"].median() if not df_m.empty else 0

    # Build PDF
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    styles = getSampleStyleSheet()

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
    style_th = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#FFFFFF"),
        alignment=1,
    )
    style_td = ParagraphStyle(
        "TD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#2D3748"),
        alignment=1,
    )
    style_td_left = ParagraphStyle(
        "TDLeft",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1A365D"),
    )
    style_kpi_title = ParagraphStyle(
        "KPITitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#4A5568"),
    )
    style_kpi_val = ParagraphStyle(
        "KPIVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        textColor=colors.HexColor("#1A365D"),
    )

    story = []

    # Header Bar
    hdr_data = [
        [
            Paragraph(
                f"<b>SECTOR FINANCIAL REPORT — {sector_name.upper()}</b>",
                style_header_title,
            )
        ],
        [
            Paragraph(
                f"Total Companies: {len(df_m)} | Sector Benchmark & Comparative Analytics",
                style_header_sub,
            )
        ],
    ]
    hdr_tbl = Table(hdr_data, colWidths=[555])
    hdr_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1A365D")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(hdr_tbl)
    story.append(Spacer(1, 10))

    # Sector Median Overview Box (4x2 table)
    med_box_data = [
        [
            Paragraph("MEDIAN MARKET CAP", style_kpi_title),
            Paragraph(f"₹{med_mcap:,.0f} Cr", style_kpi_val),
            Paragraph("MEDIAN SALES", style_kpi_title),
            Paragraph(f"₹{med_sales:,.0f} Cr", style_kpi_val),
        ],
        [
            Paragraph("MEDIAN NET PROFIT", style_kpi_title),
            Paragraph(f"₹{med_pat:,.0f} Cr", style_kpi_val),
            Paragraph("MEDIAN OPM (%)", style_kpi_title),
            Paragraph(f"{med_opm:.1f}%", style_kpi_val),
        ],
        [
            Paragraph("MEDIAN ROE (%)", style_kpi_title),
            Paragraph(f"{med_roe:.1f}%", style_kpi_val),
            Paragraph("MEDIAN ROCE (%)", style_kpi_title),
            Paragraph(f"{med_roce:.1f}%", style_kpi_val),
        ],
        [
            Paragraph("MEDIAN DEBT / EQUITY", style_kpi_title),
            Paragraph(f"{med_de:.2f}", style_kpi_val),
            Paragraph("MEDIAN FREE CASH FLOW", style_kpi_title),
            Paragraph(f"₹{med_fcf:,.0f} Cr", style_kpi_val),
        ],
    ]

    med_tbl = Table(med_box_data, colWidths=[140, 137, 140, 138])
    med_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(med_tbl)
    story.append(Spacer(1, 12))

    # Company Comparison Table (8 metrics per company)
    table_headers = [
        Paragraph("Ticker", style_th),
        Paragraph("Company Name", style_th),
        Paragraph("MCap (Cr)", style_th),
        Paragraph("Sales (Cr)", style_th),
        Paragraph("PAT (Cr)", style_th),
        Paragraph("OPM%", style_th),
        Paragraph("ROE%", style_th),
        Paragraph("D/E", style_th),
    ]

    table_rows = [table_headers]

    for _, r in df_m.iterrows():
        row_cells = [
            Paragraph(str(r["ticker"]), style_td_left),
            Paragraph(str(r["name"]), style_td_left),
            Paragraph(f"₹{r['mcap']:,.0f}" if r["mcap"] else "-", style_td),
            Paragraph(f"₹{r['sales']:,.0f}" if r["sales"] else "-", style_td),
            Paragraph(f"₹{r['pat']:,.0f}" if r["pat"] else "-", style_td),
            Paragraph(f"{r['opm']:.1f}%", style_td),
            Paragraph(f"{r['roe']:.1f}%", style_td),
            Paragraph(f"{r['de']:.2f}", style_td),
        ]
        table_rows.append(row_cells)

    # Width total: 45+120+65+65+65+65+65+65 = 555
    comp_table = Table(table_rows, colWidths=[55, 130, 65, 65, 60, 60, 60, 60])
    comp_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.HexColor("#FFFFFF"), colors.HexColor("#F7FAFC")],
                ),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(comp_table)

    doc.build(story)
    return output_pdf


def generate_all_sector_reports(db_path: str = "nifty100.db") -> list[str]:
    """Generates all 11 sector PDF reports."""
    sectors = [
        "Communication Services",
        "Consumer Discretionary",
        "Consumer Staples",
        "Energy",
        "Financials",
        "Healthcare",
        "Industrials",
        "Information Technology",
        "Materials",
        "Real Estate",
        "Utilities & Infrastructure",
    ]

    pdf_paths = []
    print(f"Generating batch sector reports for {len(sectors)} sectors...")
    for sec in sectors:
        pdf = generate_sector_report(sec, db_path=db_path)
        size_kb = os.path.getsize(pdf) / 1024.0
        pdf_paths.append(pdf)
        print(f"Sector Report -> {pdf} ({size_kb:.1f} KB)")

    return pdf_paths


if __name__ == "__main__":
    generate_all_sector_reports()
