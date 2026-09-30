import io
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_savings_pdf(goals: List[Dict[str, Any]], summary: Dict[str, Any], ai_insights: List[Dict[str, Any]] = None) -> bytes:
    """Generates an executive-level PDF financial savings report using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Brand Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=14
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )

    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#065f46')
    )

    elements = []

    # Header Section
    header_data = [
        [
            Paragraph("<b>SaveIQ</b> <font color='#6366f1'>AI Savings Tracker</font>", title_style),
            Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y - %H:%M')}<br/><b>Audit ID:</b> SIQ-{int(datetime.now().timestamp())}", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[3.8 * inch, 3.7 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT')
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#6366f1'), spaceAfter=14))

    # Executive Financial Metric Cards (4 Columns)
    total_target = summary.get("total_target", 0.0)
    total_saved = summary.get("total_saved", 0.0)
    progress_pct = summary.get("overall_progress", 0.0)
    active_count = summary.get("active_goals", 0)
    completed_count = summary.get("completed_goals", 0)

    summary_cards_data = [
        [
            Paragraph("<b>TOTAL TARGET</b>", ParagraphStyle('C1', parent=body_style, textColor=colors.HexColor('#64748b'), fontSize=8)),
            Paragraph("<b>TOTAL SAVED</b>", ParagraphStyle('C2', parent=body_style, textColor=colors.HexColor('#64748b'), fontSize=8)),
            Paragraph("<b>COMPLETION RATE</b>", ParagraphStyle('C3', parent=body_style, textColor=colors.HexColor('#64748b'), fontSize=8)),
            Paragraph("<b>ACTIVE / COMPLETED</b>", ParagraphStyle('C4', parent=body_style, textColor=colors.HexColor('#64748b'), fontSize=8))
        ],
        [
            Paragraph(f"<b>${total_target:,.2f}</b>", ParagraphStyle('V1', parent=body_style, fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor('#0f172a'))),
            Paragraph(f"<b>${total_saved:,.2f}</b>", ParagraphStyle('V2', parent=body_style, fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor('#10b981'))),
            Paragraph(f"<b>{progress_pct:.1f}%</b>", ParagraphStyle('V3', parent=body_style, fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor('#6366f1'))),
            Paragraph(f"<b>{active_count} Active / {completed_count} Done</b>", ParagraphStyle('V4', parent=body_style, fontName='Helvetica-Bold', fontSize=13, textColor=colors.HexColor('#0f172a')))
        ]
    ]
    summary_table = Table(summary_cards_data, colWidths=[1.87 * inch] * 4)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    # Goal Breakdown Table
    elements.append(Paragraph("<b>Savings Goals Portfolio & Progress Audit</b>", section_heading))

    goal_table_rows = [
        [
            Paragraph("Goal / Purpose", table_header_style),
            Paragraph("Category", table_header_style),
            Paragraph("Target", table_header_style),
            Paragraph("Current", table_header_style),
            Paragraph("Progress", table_header_style),
            Paragraph("Days Left", table_header_style),
            Paragraph("Daily Req.", table_header_style),
            Paragraph("Status", table_header_style)
        ]
    ]

    for g in goals:
        pct = (g.get('current_amount', 0) / g.get('target_amount', 1)) * 100 if g.get('target_amount', 0) > 0 else 0
        rem = max(0, g.get('target_amount', 0) - g.get('current_amount', 0))
        days = g.get('days_remaining', 30)
        daily = round(rem / max(1, days), 2)
        status = g.get('status', 'Active')

        status_color = '#10b981' if status == 'Completed' else ('#ef4444' if status == 'Overdue' else '#3b82f6')

        goal_table_rows.append([
            Paragraph(f"<b>{g.get('name', '')}</b><br/><font color='#64748b' size='7'>{g.get('purpose', '') or 'Personal'}</font>", body_style),
            Paragraph(g.get('category', 'General'), body_style),
            Paragraph(f"${g.get('target_amount', 0):,.0f}", body_style),
            Paragraph(f"${g.get('current_amount', 0):,.0f}", body_style),
            Paragraph(f"<b>{pct:.1f}%</b>", body_style),
            Paragraph(f"{days}d", body_style),
            Paragraph(f"${daily:,.1f}", body_style),
            Paragraph(f"<font color='{status_color}'><b>{status}</b></font>", badge_style)
        ])

    goal_table = Table(goal_table_rows, colWidths=[1.8*inch, 1.1*inch, 0.8*inch, 0.8*inch, 0.7*inch, 0.65*inch, 0.75*inch, 0.9*inch])
    goal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('ALIGN', (2, 0), (6, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6)
    ]))
    elements.append(goal_table)
    elements.append(Spacer(1, 14))

    # AI Financial Guidance Box
    elements.append(Paragraph("<b>AI Financial Advisory & Recommendations (Groq LLaMA 3.3-70B)</b>", section_heading))
    
    advice_content = "• Consistently automate 20% of your earnings to hit high-priority targets.<br/>• Your savings velocity for Emergency Fund is on track. Keep up the momentum.<br/>• Consider trimming variable weekend dining to close the remaining gap on your shortest-deadline target."
    if ai_insights and len(ai_insights) > 0:
        advice_content = "<br/>".join([f"• <b>{i.get('goal_name', 'Insight')}:</b> {i.get('recommendation', '')}" for i in ai_insights[:3]])

    ai_box_data = [
        [
            Paragraph(
                f"<b>Personalized Strategic Guidance:</b><br/>{advice_content}",
                ParagraphStyle('AIBox', parent=body_style, fontSize=8.5, leading=13, textColor=colors.HexColor('#1e1b4b'))
            )
        ]
    ]
    ai_table = Table(ai_box_data, colWidths=[7.5 * inch])
    ai_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eef2ff')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#c7d2fe')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12)
    ]))
    elements.append(ai_table)
    elements.append(Spacer(1, 16))

    # Footer note
    footer_text = Paragraph(
        "<i>SaveIQ Confidential Financial Report. Built with FastAPI, SQLite, Groq AI & ReportLab. Keep for your financial records.</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#94a3b8'), alignment=1)
    )
    elements.append(footer_text)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
