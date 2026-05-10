from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def generate_investment_report(product_name, country, demand_result, attention_result, competition_result, triple_match_result):
    path = f"reports/ultraai_report_{product_name.replace(' ', '_')}.pdf"
    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # ستايل مخصص للعنوان
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontSize=20, textColor=colors.HexColor("#0f172a"), spaceAfter=20)
    
    story = []
    
    # الهيدر
    story.append(Paragraph(f"UltraAI Market Intelligence Report", title_style))
    story.append(Paragraph(f"<b>Product:</b> {product_name} | <b>Country:</b> {country}", styles['Normal']))
    story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # جدول الملخص التنفيذي
    data = [
        ["Metric", "Value"],
        ["Final Decision", triple_match_result['decision']],
        ["Confidence Score", f"{triple_match_result['confidence']}%"],
        ["Recommendation", triple_match_result['recommendation']]
    ]
    
    t = Table(data, colWidths=[150, 300])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1"))
    ]))
    
    story.append(Paragraph("<b>1. Executive Summary</b>", styles['Heading2']))
    story.append(t)
    story.append(Spacer(1, 20))

    # قسم الإشارات الثلاثية
    story.append(Paragraph("<b>2. Triple-Match Signals</b>", styles['Heading2']))
    signals = [
        ["Signal Type", "Result"],
        ["Demand (Google Trends)", f"{demand_result.get('baseline_growth_pct') or demand_result.get('current_value') or triple_match_result.get('confidence', 'N/A')}% Growth"],
        ["Attention (TikTok)", f"{attention_result.get('attention_score')}/100 Intent"],
        ["Supply (Competition)", competition_result.get('market_saturation') or competition_result.get('supply_status') or competition_result.get('competition_level') or triple_match_result.get('checks', {}).get('market_saturation') or "N/A"]
    ]
    st = Table(signals, colWidths=[150, 300])
    st.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 1, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
    story.append(st)

    doc.build(story)
    return path
