import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reportlab.lib.pagesizes  import A4
from reportlab.lib.styles     import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units      import cm
from reportlab.lib            import colors
from reportlab.platypus       import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums      import TA_CENTER, TA_LEFT

# Color palette
URA_BLUE   = colors.HexColor("#003087")
URA_GOLD   = colors.HexColor("#FFD700")
GREEN      = colors.HexColor("#00C896")
AMBER      = colors.HexColor("#FFC107")
RED        = colors.HexColor("#FF4444")
LIGHT_GREY = colors.HexColor("#F5F5F5")
MID_GREY   = colors.HexColor("#CCCCCC")
DARK_GREY  = colors.HexColor("#333333")

def build_styles():
    styles = {
        "title": ParagraphStyle("title",
            fontSize=22, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER, spaceAfter=6),
        "subtitle": ParagraphStyle("subtitle",
            fontSize=12, fontName="Helvetica",
            textColor=URA_GOLD, alignment=TA_CENTER, spaceAfter=4),
        "h1": ParagraphStyle("h1",
            fontSize=14, fontName="Helvetica-Bold",
            textColor=URA_BLUE, spaceBefore=14, spaceAfter=6),
        "h2": ParagraphStyle("h2",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=DARK_GREY, spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("body",
            fontSize=9, fontName="Helvetica",
            textColor=DARK_GREY, leading=14, spaceAfter=4),
        "caption": ParagraphStyle("caption",
            fontSize=8, fontName="Helvetica-Oblique",
            textColor=colors.grey, alignment=TA_CENTER),
        "kpi": ParagraphStyle("kpi",
            fontSize=26, fontName="Helvetica-Bold",
            alignment=TA_CENTER),
        "kpi_label": ParagraphStyle("kpi_label",
            fontSize=8, fontName="Helvetica",
            textColor=colors.grey, alignment=TA_CENTER),
    }
    return styles

def build_cover(styles, dq_results, pipeline_run):
    story = []
    score = dq_results["overall_dq_score"]

    # Header banner
    header_data = [
        [Paragraph("UGANDA REVENUE AUTHORITY", styles["title"])],
        [Paragraph("Data Quality Assessment Report", styles["subtitle"])],
    ]
    header = Table(header_data, colWidths=[17*cm])
    header.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), URA_BLUE),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,0),  18),
        ("BOTTOMPADDING", (0,-1),(-1,-1), 18),
    ]))
    story.append(header)
    story.append(Spacer(1, 1*cm))

    # Overall score
    if score >= 95:
        score_color = GREEN
    elif score >= 80:
        score_color = AMBER
    else:
        score_color = RED

    score_para = Paragraph(
        f'<font color="{score_color.hexval()}">{score}%</font>',
        styles["kpi"]
    )
    label_para = Paragraph("Overall Data Quality Score", styles["kpi_label"])

    score_table = Table([[score_para], [label_para]], colWidths=[17*cm])
    score_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), LIGHT_GREY),
        ("BOX",           (0,0), (-1,-1), 1, MID_GREY),
        ("TOPPADDING",    (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.6*cm))

    # Report metadata
    meta = [
        ["Report Date",       datetime.now().strftime("%B %d, %Y")],
        ["Pipeline Run",      pipeline_run],
        ["Datasets Assessed", "Tax Returns, Taxpayer Register"],
        ["Total Issues Found",str(dq_results["total_issues"])],
        ["Classification",    "INTERNAL"],
    ]
    meta_table = Table(meta, colWidths=[5*cm, 12*cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (0,-1),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("TEXTCOLOR",     (0,0), (0,-1),  URA_BLUE),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [colors.white, LIGHT_GREY]),
        ("GRID",          (0,0), (-1,-1), 0.5, MID_GREY),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph(
        "This report was generated automatically by the URA Data Governance Pipeline. "
        "It is intended for internal use by the Data Science and IT departments only.",
        styles["caption"]
    ))
    story.append(PageBreak())
    return story

def build_executive_summary(styles, dq_results, clean_summary):
    story = []
    score = dq_results["overall_dq_score"]
    sev   = dq_results["severity_summary"]

    story.append(Paragraph("1. Executive Summary", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=URA_BLUE))
    story.append(Spacer(1, 0.3*cm))

    # Plain English verdict
    if score >= 95:
        verdict = "The datasets assessed are in GOOD condition and ready for analytical use."
    elif score >= 80:
        verdict = "The datasets require MODERATE remediation before analytical use."
    else:
        verdict = "The datasets are in POOR condition. Significant remediation is required."

    story.append(Paragraph(
        f"The data quality assessment of URA tax return and taxpayer register datasets "
        f"returned an <b>overall score of {score}%</b>. {verdict}",
        styles["body"]
    ))
    story.append(Spacer(1, 0.4*cm))

    # KPI row
    kpi_data = [
        [
            Paragraph(str(dq_results["total_issues"]), styles["kpi"]),
            Paragraph(str(sev["HIGH"]),   styles["kpi"]),
            Paragraph(str(sev["MEDIUM"]), styles["kpi"]),
            Paragraph(str(sev["LOW"]),    styles["kpi"]),
            Paragraph(f"{clean_summary['retention_pct']}%", styles["kpi"]),
        ],
        [
            Paragraph("Total Issues",  styles["kpi_label"]),
            Paragraph("HIGH",          styles["kpi_label"]),
            Paragraph("MEDIUM",        styles["kpi_label"]),
            Paragraph("LOW",           styles["kpi_label"]),
            Paragraph("Data Retained", styles["kpi_label"]),
        ],
    ]
    kpi_table = Table(kpi_data, colWidths=[3.4*cm] * 5)
    kpi_table.setStyle(TableStyle([
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [LIGHT_GREY, colors.white]),
        ("BOX",           (0,0), (-1,-1), 0.5, MID_GREY),
        ("INNERGRID",     (0,0), (-1,-1), 0.5, MID_GREY),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("TEXTCOLOR",     (1,0), (1,0),   RED),
        ("TEXTCOLOR",     (2,0), (2,0),   AMBER),
        ("TEXTCOLOR",     (3,0), (3,0),   GREEN),
        ("TEXTCOLOR",     (4,0), (4,0),   GREEN),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        f"After automated remediation, <b>{clean_summary['rows_after']:,} of "
        f"{clean_summary['rows_before']:,} records</b> were retained "
        f"({clean_summary['retention_pct']}%). "
        f"{clean_summary['rows_removed']:,} records were removed due to critical quality failures.",
        styles["body"]
    ))
    story.append(PageBreak())
    return story

def build_dimension_section(styles, dq_results):
    story = []

    story.append(Paragraph("2. Quality Dimension Scores", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=URA_BLUE))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(
        "Data quality is assessed across six dimensions aligned with the DAMA Data Management "
        "Body of Knowledge. Each dimension is scored 0–100%. A score of 95% or above is "
        "acceptable. Between 80–94% requires monitoring. Below 80% requires immediate action.",
        styles["body"]
    ))
    story.append(Spacer(1, 0.3*cm))

    dim_data = [["Dimension", "Score", "Status"]]

    for dim, score in dq_results["dimension_scores"].items():
        if score >= 95:
            status = "PASS"
        elif score >= 80:
            status = "MONITOR"
        else:
            status = "FAIL"

        dim_data.append([
            Paragraph(f"<b>{dim}</b>", styles["body"]),
            Paragraph(f"<b>{score}%</b>", styles["body"]),
            Paragraph(status, styles["body"]),
        ])

    dim_table = Table(dim_data, colWidths=[9*cm, 3*cm, 3*cm])
    style_cmds = [
        ("BACKGROUND",    (0,0),  (-1,0),  URA_BLUE),
        ("TEXTCOLOR",     (0,0),  (-1,0),  colors.white),
        ("FONTNAME",      (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),  (-1,-1), 9),
        ("ALIGN",         (1,0),  (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS",(0,1),  (-1,-1), [colors.white, LIGHT_GREY]),
        ("GRID",          (0,0),  (-1,-1), 0.5, MID_GREY),
        ("TOPPADDING",    (0,0),  (-1,-1), 6),
        ("BOTTOMPADDING", (0,0),  (-1,-1), 6),
        ("LEFTPADDING",   (0,0),  (-1,-1), 6),
    ]
    # Color code each status cell
    for i, (dim, score) in enumerate(dq_results["dimension_scores"].items(), start=1):
        if score >= 95:
            style_cmds.append(("TEXTCOLOR", (2,i), (2,i), GREEN))
        elif score >= 80:
            style_cmds.append(("TEXTCOLOR", (2,i), (2,i), AMBER))
        else:
            style_cmds.append(("TEXTCOLOR", (2,i), (2,i), RED))

    dim_table.setStyle(TableStyle(style_cmds))
    story.append(dim_table)
    story.append(PageBreak())
    return story

def build_issues_section(styles, issues):
    story = []

    story.append(Paragraph("3. Detailed Issue Log", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=URA_BLUE))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(
        "All detected data quality issues are listed below, sorted by severity. "
        "Each issue includes the number of affected rows and the pass rate for that check.",
        styles["body"]
    ))
    story.append(Spacer(1, 0.3*cm))

    # Sort issues HIGH first
    sorted_issues = sorted(
        issues,
        key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["severity"]]
    )

    issue_data = [["#", "Dimension", "Field", "Description", "Affected", "Pass %", "Severity"]]

    for i, issue in enumerate(sorted_issues, 1):
        issue_data.append([
            str(i),
            issue["dimension"],
            Paragraph(f"<font size=7>{issue['field']}</font>",       styles["body"]),
            Paragraph(f"<font size=7>{issue['description']}</font>", styles["body"]),
            f"{issue['affected_rows']:,}",
            f"{issue['pass_rate']}%",
            issue["severity"],
        ])

    col_widths = [0.7*cm, 3.5*cm, 2.5*cm, 5*cm, 1.5*cm, 1.4*cm, 1.7*cm]
    issue_table = Table(issue_data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ("BACKGROUND",    (0,0),  (-1,0),  URA_BLUE),
        ("TEXTCOLOR",     (0,0),  (-1,0),  colors.white),
        ("FONTNAME",      (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),  (-1,-1), 8),
        ("ALIGN",         (0,0),  (0,-1),  "CENTER"),
        ("ALIGN",         (4,0),  (-1,-1), "CENTER"),
        ("VALIGN",        (0,0),  (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0,1),  (-1,-1), [colors.white, LIGHT_GREY]),
        ("GRID",          (0,0),  (-1,-1), 0.4, MID_GREY),
        ("TOPPADDING",    (0,0),  (-1,-1), 4),
        ("BOTTOMPADDING", (0,0),  (-1,-1), 4),
        ("LEFTPADDING",   (0,0),  (-1,-1), 4),
    ]

    # Color each severity cell
    for i, issue in enumerate(sorted_issues, 1):
        if issue["severity"] == "HIGH":
            style_cmds.append(("TEXTCOLOR", (6,i), (6,i), RED))
        elif issue["severity"] == "MEDIUM":
            style_cmds.append(("TEXTCOLOR", (6,i), (6,i), AMBER))
        else:
            style_cmds.append(("TEXTCOLOR", (6,i), (6,i), GREEN))
        style_cmds.append(("FONTNAME", (6,i), (6,i), "Helvetica-Bold"))

    issue_table.setStyle(TableStyle(style_cmds))
    story.append(issue_table)
    story.append(PageBreak())
    return story

def build_governance_section(styles):
    story = []

    story.append(Paragraph("4. Data Governance Policy Summary", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=URA_BLUE))
    story.append(Spacer(1, 0.3*cm))

    policies = [
        ("Data Ownership",
         "Each dataset has a designated Data Owner responsible for quality and access control. "
         "The Supervisor Data Science maintains ownership of all analytical datasets."),
        ("Data Quality SLA",
         "A minimum DQ score of 95% is required before any dataset is promoted to production. "
         "Scores below 80% trigger an incident and block pipeline progression."),
        ("Access Control",
         "Datasets are classified as INTERNAL, RESTRICTED, or PUBLIC. "
         "Access is granted on a need-to-know basis via role-based access control."),
        ("Incident Management",
         "HIGH severity issues must be resolved within 3 business days. "
         "MEDIUM issues within 10 business days. "
         "LOW issues addressed in the next sprint cycle."),
        ("Retention Policy",
         "Tax return records are retained for a minimum of 10 years per URA regulations. "
         "Audit logs are retained for 7 years."),
        ("Pipeline Cadence",
         "The DQ pipeline runs daily at 02:00 EAT. "
         "Reports are distributed to the Data Science team by 06:00 EAT."),
    ]

    for title, body in policies:
        row = [[
            Paragraph(f"<b>{title}</b>", styles["body"]),
            Paragraph(body, styles["body"]),
        ]]
        t = Table(row, colWidths=[4*cm, 13*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (0,0),  URA_BLUE),
            ("TEXTCOLOR",     (0,0), (0,0),  colors.white),
            ("VALIGN",        (0,0), (-1,-1),"TOP"),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
            ("GRID",          (0,0), (-1,-1), 0.5, MID_GREY),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2*cm))

    return story

def generate_report(output_dir="outputs/reports"):
    with open("outputs/pipeline_summary.json") as f:
        data = json.load(f)

    dq_results    = data["dq_results"]
    clean_summary = data["cleaning_summary"]
    pipeline_run  = data["pipeline_run"]

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"{output_dir}/URA_DQ_Report_{timestamp}.pdf"

    doc = SimpleDocTemplate(
        output_path,
        pagesize     = A4,
        rightMargin  = 2*cm,
        leftMargin   = 2*cm,
        topMargin    = 2*cm,
        bottomMargin = 2*cm,
        title        = "URA Data Quality Report",
    )

    styles = build_styles()
    story  = []

    story += build_cover(styles, dq_results, pipeline_run)
    story += build_executive_summary(styles, dq_results, clean_summary)
    story += build_dimension_section(styles, dq_results)
    story += build_issues_section(styles, dq_results["issues"])
    story += build_governance_section(styles)

    doc.build(story)
    print(f"Report generated → {output_path}")
    return output_path


if __name__ == "__main__":
    generate_report()