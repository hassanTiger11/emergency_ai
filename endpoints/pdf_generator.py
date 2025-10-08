"""
PDF Report Generator
Creates professional EMS reports in PDF format matching template standards
"""

from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, blue, red, green, grey, HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import PageBreak, Image, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def create_professional_report_pdf(analysis_data, output_path):
    """
    Create a professional EMS report PDF matching the template format
    """
    doc = SimpleDocTemplate(output_path, pagesize=A4, 
                          rightMargin=72, leftMargin=72, 
                          topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Professional color scheme matching template
    primary_blue = HexColor('#2E5BBA')  # Dark teal/blue for section headers
    subtitle_gray = HexColor('#666666')  # Gray for subtitle
    line_gray = HexColor('#E0E0E0')     # Light gray for separator lines
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Professional title style - large, bold, centered
    title_style = ParagraphStyle(
        'ProfessionalTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=15,
        spaceBefore=0,
        alignment=TA_CENTER,
        textColor=black,
        fontName='Helvetica-Bold',
        leading=28
    )
    
    # Elegant subtitle style - smaller, gray, centered
    subtitle_style = ParagraphStyle(
        'ElegantSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=subtitle_gray,
        fontName='Helvetica',
        leading=16
    )
    
    # Section headers - teal/blue, bold, left-aligned
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontSize=16,
        spaceAfter=15,
        spaceBefore=25,
        textColor=primary_blue,
        fontName='Helvetica-Bold',
        leading=18
    )
    
    # Field labels - standard black, with bullet points
    field_style = ParagraphStyle(
        'FieldLabel',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=8,
        spaceBefore=0,
        textColor=black,
        fontName='Helvetica',
        leading=14,
        leftIndent=12
    )
    
    # Normal text style
    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6,
        textColor=black,
        fontName='Helvetica',
        leading=14
    )
    
    # Professional Report Header
    elements.append(Paragraph("PARAMEDIC PATIENT CARE REPORT", title_style))
    elements.append(Paragraph("An Elegant Standard for Emergency Medical Documentation", subtitle_style))
    
    # Add horizontal separator line
    elements.append(Spacer(1, 20))
    elements.append(Table([[None]], colWidths=[6*inch], rowHeights=[1], 
                         style=TableStyle([('LINEABOVE', (0, 0), (0, 0), 1, line_gray)])))
    elements.append(Spacer(1, 20))
    
    # Patient Demographics Section - Professional Format
    if analysis_data.get('patient'):
        elements.append(Paragraph("Patient Information", section_style))
        
        patient = analysis_data['patient']
        
        # Create bullet-pointed fields with clean formatting
        patient_fields = [
            f"• Full Name: {patient.get('name', 'Unknown')}",
            f"• Date of Birth: {patient.get('dob', 'Unknown')}",
            f"• Age: {patient.get('age', 'Unknown')} years",
            f"• Sex: {patient.get('gender', 'Unknown')}",
            f"• Nationality: {patient.get('nationality', 'Unknown')}",
            f"• ID Number: {patient.get('ID', 'Unknown')}",
            f"• Weight: {patient.get('weight', 'Unknown')} kg"
        ]
        
        for field in patient_fields:
            elements.append(Paragraph(field, field_style))
            elements.append(Spacer(1, 12))  # Space for writing
        
        # Add separator line
        elements.append(Spacer(1, 10))
        elements.append(Table([[None]], colWidths=[6*inch], rowHeights=[1], 
                             style=TableStyle([('LINEABOVE', (0, 0), (0, 0), 1, line_gray)])))
        elements.append(Spacer(1, 15))
    
    # Incident Details Section - Professional Format
    if analysis_data.get('scene'):
        elements.append(Paragraph("Incident Details", section_style))
        
        scene = analysis_data['scene']
        current_time = datetime.now()
        
        # Create bullet-pointed fields
        scene_fields = [
            f"• Date: {current_time.strftime('%Y-%m-%d')}",
            f"• Time: {current_time.strftime('%H:%M')}",
            f"• Call Number: {scene.get('call_number', 'TBD')}",
            f"• Response Address: {scene.get('location', 'Unknown')}",
            f"• Caller Name: {scene.get('caller_name', 'Unknown')}",
            f"• Caller Phone: {scene.get('caller_phone', 'Unknown')}",
            f"• Incident Type: {scene.get('case_type', 'Medical Emergency')}",
            f"• Priority: {analysis_data.get('severity', 'Unknown')}"
        ]
        
        for field in scene_fields:
            elements.append(Paragraph(field, field_style))
            elements.append(Spacer(1, 12))
        
        # Add separator line
        elements.append(Spacer(1, 10))
        elements.append(Table([[None]], colWidths=[6*inch], rowHeights=[1], 
                             style=TableStyle([('LINEABOVE', (0, 0), (0, 0), 1, line_gray)])))
        elements.append(Spacer(1, 15))
    
    # Chief Complaint Section - Professional Format
    elements.append(Paragraph("Chief Complaint", section_style))
    chief_complaint = analysis_data.get('chief_complaint') or analysis_data.get('scene', {}).get('chief_complaint', 'Not provided')
    elements.append(Paragraph(f"• Primary Complaint: {chief_complaint}", field_style))
    elements.append(Spacer(1, 12))
    
    # Add separator line
    elements.append(Spacer(1, 10))
    elements.append(Table([[None]], colWidths=[6*inch], rowHeights=[1], 
                         style=TableStyle([('LINEABOVE', (0, 0), (0, 0), 1, line_gray)])))
    elements.append(Spacer(1, 15))
    
    # Medical History Section - Simplified Professional Format
    if analysis_data.get('history'):
        elements.append(Paragraph("Medical History", section_style))
        
        history = analysis_data['history']
        
        medical_history_fields = [
            f"• Past Medical History: {history.get('past_history', 'None significant')}",
            f"• Current Medications: {history.get('medications', 'None')}",
            f"• Allergies: {history.get('allergies', 'None known')}",
            f"• Family History: {history.get('family_history', 'None significant')}"
        ]
        
        for field in medical_history_fields:
            elements.append(Paragraph(field, field_style))
            elements.append(Spacer(1, 12))
        
        # Add separator line
        elements.append(Spacer(1, 10))
        elements.append(Table([[None]], colWidths=[6*inch], rowHeights=[1], 
                             style=TableStyle([('LINEABOVE', (0, 0), (0, 0), 1, line_gray)])))
        elements.append(Spacer(1, 15))
    
    # Patient Assessment Section with Professional Vital Signs Table
    elements.append(Paragraph("Patient Assessment", section_style))
    
    # Initial Assessment bullet points
    initial_assessment_fields = [
        "• Initial Assessment: (General appearance, distress level, consciousness, etc.)",
        f"• Initial Assessment: {analysis_data.get('exam', {}).get('general_appearance', 'Stable condition')}"
    ]
    
    for field in initial_assessment_fields:
        elements.append(Paragraph(field, field_style))
        elements.append(Spacer(1, 12))
    
    # Professional Vital Signs Table
    if analysis_data.get('vitals'):
        vitals = analysis_data['vitals']
        current_time = datetime.now().strftime('%H:%M')
        
        vitals_data = [
            ["Time", "Blood Pressure", "Pulse", "Respiratory Rate", "SpO2", "Temperature", "GCS"],
            [current_time, 
             f"{vitals.get('bp_systolic', '___')}/{vitals.get('bp_diastolic', '___')}",
             f"{vitals.get('hr', '___')}",
             f"{vitals.get('rr', '___')}",
             f"{vitals.get('spo2', '___')}%",
             f"{vitals.get('temp', '___')}°C",
             f"{vitals.get('gcs', '___')}"],
            ["_____", "_____", "_____", "_____", "_____", "_____", "_____"],
            ["_____", "_____", "_____", "_____", "_____", "_____", "_____"]
        ]
        
        vitals_table = Table(vitals_data, colWidths=[0.7*inch, 0.9*inch, 0.7*inch, 1.0*inch, 0.7*inch, 0.9*inch, 0.7*inch])
        vitals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header row
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.white, colors.white, colors.white])
        ]))
        
        elements.append(vitals_table)
        elements.append(Spacer(1, 15))
    
    # Add separator line
    elements.append(Spacer(1, 10))
    elements.append(Table([[None]], colWidths=[6*inch], rowHeights=[1], 
                         style=TableStyle([('LINEABOVE', (0, 0), (0, 0), 1, line_gray)])))
    elements.append(Spacer(1, 15))
    
    # Interventions & Treatments Section
    elements.append(Paragraph("Interventions & Treatments", section_style))
    
    if analysis_data.get('interventions'):
        for i, intervention in enumerate(analysis_data['interventions'], 1):
            elements.append(Paragraph(f"• Intervention {i}: {intervention}", field_style))
            elements.append(Spacer(1, 12))
    else:
        elements.append(Paragraph("• Intervention: (Oxygen Therapy, IV Access, Medication, CPR)", field_style))
        elements.append(Spacer(1, 12))
    
    # Add separator line
    elements.append(Spacer(1, 10))
    elements.append(Table([[None]], colWidths=[6*inch], rowHeights=[1], 
                         style=TableStyle([('LINEABOVE', (0, 0), (0, 0), 1, line_gray)])))
    elements.append(Spacer(1, 15))
    
    # Transport & Disposition Section
    elements.append(Paragraph("Transport & Disposition", section_style))
    
    disposition_fields = [
        f"• Transport Priority: {analysis_data.get('disposition', 'To be determined')}",
        "• Receiving Hospital: _________________________",
        "• Patient Condition on Arrival: _________________________"
    ]
    
    for field in disposition_fields:
        elements.append(Paragraph(field, field_style))
        elements.append(Spacer(1, 12))
    
    # Add separator line
    elements.append(Spacer(1, 10))
    elements.append(Table([[None]], colWidths=[6*inch], rowHeights=[1], 
                         style=TableStyle([('LINEABOVE', (0, 0), (0, 0), 1, line_gray)])))
    elements.append(Spacer(1, 15))
    
    # Narrative Summary Section
    elements.append(Paragraph("Narrative Summary", section_style))
    
    narrative_text = analysis_data.get('reasoning', 'Assessment pending') or 'Provide a detailed, chronological account of observations, actions, and patient responses:'
    elements.append(Paragraph("• Narrative:", field_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(narrative_text, normal_style))
    elements.append(Spacer(1, 12))
    
    # Add separator line
    elements.append(Spacer(1, 10))
    elements.append(Table([[None]], colWidths=[6*inch], rowHeights=[1], 
                         style=TableStyle([('LINEABOVE', (0, 0), (0, 0), 1, line_gray)])))
    elements.append(Spacer(1, 15))
    
    # EMS Crew Information Section
    elements.append(Paragraph("EMS Crew Information", section_style))
    
    crew_fields = [
        "• Paramedic Name(s): _________________________",
        "• EMT Name(s): _________________________",
        "• Time: _________________________",
        "• Unit Number: _________________________"
    ]
    
    for field in crew_fields:
        elements.append(Paragraph(field, field_style))
        elements.append(Spacer(1, 12))
    
    # Add separator line
    elements.append(Spacer(1, 10))
    elements.append(Table([[None]], colWidths=[6*inch], rowHeights=[1], 
                         style=TableStyle([('LINEABOVE', (0, 0), (0, 0), 1, line_gray)])))
    elements.append(Spacer(1, 15))
    
    # Additional Remarks Section
    elements.append(Paragraph("Additional Remarks", section_style))
    
    additional_remarks = analysis_data.get('follow_up', 'As needed') or 'Additional notes or special considerations:'
    elements.append(Paragraph(f"• Remarks: {additional_remarks}", field_style))
    elements.append(Spacer(1, 12))
    
    # Build PDF
    doc.build(elements)
    
    return output_path
