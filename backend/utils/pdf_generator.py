from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
from pathlib import Path
import uuid

class PDFReportGenerator:
    """Generate professional PDF reports for document analysis"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a365d'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c5282'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # Risk level styles
        self.styles.add(ParagraphStyle(
            name='RiskCritical',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.red,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='RiskHigh',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.orange,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='RiskMedium',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#f59e0b'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='RiskLow',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.green,
            fontName='Helvetica-Bold'
        ))
    
    def generate_report(self, document_data: dict, output_folder: Path) -> str:
        """
        Generate PDF report
        
        Args:
            document_data: Document analysis data
            output_folder: Folder to save the report
            
        Returns:
            Path to generated PDF
        """
        # Create output path
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)
        
        report_id = str(uuid.uuid4())[:8]
        pdf_path = output_folder / f"legal_analysis_{report_id}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph("Legal Document Analysis Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        # Document info
        story.append(Paragraph(f"<b>Document:</b> {document_data.get('filename', 'Unknown')}", self.styles['Normal']))
        story.append(Paragraph(f"<b>Analysis Date:</b> {datetime.now().strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        summary = document_data.get('summary', {})
        if summary:
            story.append(Paragraph("Executive Summary", self.styles['CustomHeading']))
            story.append(Paragraph(summary.get('executive_summary', 'N/A'), self.styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Document details
            story.append(Paragraph(f"<b>Document Type:</b> {summary.get('document_type', 'Unknown')}", self.styles['Normal']))
            story.append(Paragraph(f"<b>Purpose:</b> {summary.get('purpose', 'N/A')}", self.styles['Normal']))
            
            if summary.get('parties'):
                parties_text = ', '.join(summary['parties'])
                story.append(Paragraph(f"<b>Parties:</b> {parties_text}", self.styles['Normal']))
            
            story.append(Spacer(1, 20))
        
        # Risk Assessment
        risk_assessment = document_data.get('risk_assessment', {})
        if risk_assessment:
            story.append(Paragraph("Risk Assessment", self.styles['CustomHeading']))
            
            risk_level = risk_assessment.get('overall_risk_level', 'unknown').upper()
            risk_score = risk_assessment.get('overall_risk_score', 0)
            
            # Risk level with color
            risk_style = f'Risk{risk_level.title()}'
            if risk_style in self.styles:
                story.append(Paragraph(f"Overall Risk Level: {risk_level} ({risk_score:.1f}/100)", self.styles[risk_style]))
            else:
                story.append(Paragraph(f"Overall Risk Level: {risk_level} ({risk_score:.1f}/100)", self.styles['Normal']))
            
            story.append(Spacer(1, 12))
            
            # Risk factors
            if risk_assessment.get('risk_factors'):
                story.append(Paragraph("<b>Risk Factors:</b>", self.styles['Normal']))
                for factor in risk_assessment['risk_factors']:
                    story.append(Paragraph(
                        f"• {factor['factor']}: {factor['description']} (Score: {factor['score']:.1f})",
                        self.styles['Normal']
                    ))
                story.append(Spacer(1, 12))
            
            # Missing clauses
            if risk_assessment.get('missing_clauses'):
                story.append(Paragraph("<b>Missing Essential Clauses:</b>", self.styles['Normal']))
                for clause in risk_assessment['missing_clauses']:
                    story.append(Paragraph(f"• {clause}", self.styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Recommendations
            if risk_assessment.get('recommendations'):
                story.append(Paragraph("<b>Recommendations:</b>", self.styles['Normal']))
                for rec in risk_assessment['recommendations']:
                    story.append(Paragraph(f"• {rec}", self.styles['Normal']))
            
            story.append(Spacer(1, 20))
        
        # Detected Clauses
        clauses = document_data.get('clauses', [])
        if clauses:
            story.append(PageBreak())
            story.append(Paragraph("Detected Clauses", self.styles['CustomHeading']))
            story.append(Spacer(1, 12))
            
            # Group by category
            clauses_by_category = {}
            for clause in clauses:
                category = clause.get('category', 'Other')
                if category not in clauses_by_category:
                    clauses_by_category[category] = []
                clauses_by_category[category].append(clause)
            
            # Display by category
            for category, category_clauses in clauses_by_category.items():
                story.append(Paragraph(f"<b>{category.replace('_', ' ').title()}</b>", self.styles['Heading3']))
                
                for clause in category_clauses:
                    # Clause text (truncated)
                    text = clause.get('text', '')
                    if len(text) > 300:
                        text = text[:300] + '...'
                    
                    story.append(Paragraph(text, self.styles['Normal']))
                    
                    # Risk info
                    risk_level = clause.get('risk_level', 'low')
                    story.append(Paragraph(
                        f"<i>Risk Level: {risk_level.upper()} | Confidence: {clause.get('confidence', 0):.2f}</i>",
                        self.styles['Normal']
                    ))
                    
                    # Issues
                    if clause.get('issues'):
                        story.append(Paragraph("<b>Issues:</b>", self.styles['Normal']))
                        for issue in clause['issues']:
                            story.append(Paragraph(f"  • {issue}", self.styles['Normal']))
                    
                    # Recommendations
                    if clause.get('recommendations'):
                        story.append(Paragraph("<b>Recommendations:</b>", self.styles['Normal']))
                        for rec in clause['recommendations']:
                            story.append(Paragraph(f"  • {rec}", self.styles['Normal']))
                    
                    story.append(Spacer(1, 12))
        
        # Key Terms
        key_terms = document_data.get('key_terms', [])
        if key_terms:
            story.append(PageBreak())
            story.append(Paragraph("Key Terms & Entities", self.styles['CustomHeading']))
            story.append(Spacer(1, 12))
            
            # Create table data
            table_data = [['Term', 'Category', 'Importance']]
            for term in key_terms[:15]:  # Limit to top 15
                table_data.append([
                    term.get('text', ''),
                    term.get('category', ''),
                    f"{term.get('importance_score', 0):.1f}"
                ])
            
            # Create table
            table = Table(table_data, colWidths=[3*inch, 1.5*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        
        # Build PDF
        doc.build(story)
        
        return str(pdf_path)
