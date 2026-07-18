"""
PDF Receipt Generator for Elite Wealth Capital
Generates professional receipts for deposits, investments, and withdrawals
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import qrcode
from django.conf import settings
import os


class ReceiptGenerator:
    """Generate PDF receipts for transactions"""
    
    def __init__(self):
        self.pagesize = A4
        self.width, self.height = self.pagesize
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Company name style
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0A1F44'),
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # Receipt title style
        self.styles.add(ParagraphStyle(
            name='ReceiptTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#00A86B'),
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        
        # Receipt number style
        self.styles.add(ParagraphStyle(
            name='ReceiptNumber',
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_RIGHT,
            spaceAfter=20
        ))
        
        # Amount style
        self.styles.add(ParagraphStyle(
            name='Amount',
            fontSize=28,
            textColor=colors.HexColor('#00A86B'),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        ))
    
    def _generate_receipt_number(self, transaction_type, transaction_id, created_at):
        """Generate unique receipt number: EWC-DEP-20260718-123"""
        type_code = {
            'deposit': 'DEP',
            'investment': 'INV',
            'withdrawal': 'WDL',
            'profit': 'PRF'
        }.get(transaction_type, 'TXN')
        
        date_str = created_at.strftime('%Y%m%d')
        return f"EWC-{type_code}-{date_str}-{transaction_id}"
    
    def _generate_qr_code(self, data):
        """Generate QR code image"""
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
    
    def generate_deposit_receipt(self, deposit):
        """Generate deposit receipt PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.pagesize,
                               topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        story = []
        
        # Receipt number
        receipt_num = self._generate_receipt_number('deposit', deposit.id, deposit.created_at)
        story.append(Paragraph(f"Receipt No: {receipt_num}", self.styles['ReceiptNumber']))
        
        # Company header
        story.append(Paragraph("ELITE WEALTH CAPITAL", self.styles['CompanyName']))
        story.append(Paragraph("Investment Platform", self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Receipt title
        story.append(Paragraph("DEPOSIT RECEIPT", self.styles['ReceiptTitle']))
        story.append(Spacer(1, 0.1*inch))
        
        # Status badge
        status_color = {
            'pending': colors.orange,
            'confirmed': colors.green,
            'rejected': colors.red
        }.get(deposit.status, colors.grey)
        
        status_text = f'<font color="{status_color.hexval()}">● {deposit.status.upper()}</font>'
        story.append(Paragraph(status_text, self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Amount
        story.append(Paragraph(f"${deposit.amount:,.2f}", self.styles['Amount']))
        story.append(Spacer(1, 0.3*inch))
        
        # Transaction details table
        data = [
            ['Transaction Details', ''],
            ['User:', f"{deposit.user.first_name} {deposit.user.last_name}"],
            ['Email:', deposit.user.email],
            ['Date:', deposit.created_at.strftime('%B %d, %Y at %I:%M %p')],
            ['Method:', deposit.method.upper() if deposit.method else 'N/A'],
            ['Status:', deposit.status.title()],
        ]
        
        if deposit.crypto_address:
            data.append(['Crypto Address:', deposit.crypto_address[:20] + '...'])
        
        if deposit.confirmed_at:
            data.append(['Confirmed:', deposit.confirmed_at.strftime('%B %d, %Y at %I:%M %p')])
        
        table = Table(data, colWidths=[2.5*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A1F44')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.4*inch))
        
        # QR Code for verification
        qr_data = f"https://portal.elitewealthcapita.uk/verify-receipt/{receipt_num}"
        qr_buffer = self._generate_qr_code(qr_data)
        qr_img = Image(qr_buffer, width=1.5*inch, height=1.5*inch)
        story.append(qr_img)
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph("Scan to verify receipt authenticity", self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_style = ParagraphStyle(
            name='Footer',
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        story.append(Paragraph("This is a computer-generated receipt and does not require a signature.", footer_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
        story.append(Paragraph("Elite Wealth Capital | portal.elitewealthcapita.uk | admin@elitewealthcapita.uk", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_investment_receipt(self, investment):
        """Generate investment confirmation receipt PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.pagesize,
                               topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        story = []
        
        # Receipt number
        receipt_num = self._generate_receipt_number('investment', investment.id, investment.start_date)
        story.append(Paragraph(f"Certificate No: {receipt_num}", self.styles['ReceiptNumber']))
        
        # Company header
        story.append(Paragraph("ELITE WEALTH CAPITAL", self.styles['CompanyName']))
        story.append(Paragraph("Investment Platform", self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Certificate title
        story.append(Paragraph("INVESTMENT CERTIFICATE", self.styles['ReceiptTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Amount
        story.append(Paragraph(f"${investment.amount:,.2f}", self.styles['Amount']))
        story.append(Spacer(1, 0.3*inch))
        
        # Investment details table
        data = [
            ['Investment Details', ''],
            ['Investor:', f"{investment.user.first_name} {investment.user.last_name}"],
            ['Email:', investment.user.email],
            ['Plan:', investment.plan.name],
            ['Amount Invested:', f"${investment.amount:,.2f}"],
            ['Expected ROI:', f"{investment.plan.roi_percentage}%"],
            ['Expected Profit:', f"${investment.expected_profit:,.2f}" if investment.expected_profit else 'Calculating...'],
            ['Duration:', f"{investment.plan.duration_days} days"],
            ['Start Date:', investment.start_date.strftime('%B %d, %Y')],
            ['Maturity Date:', investment.end_date.strftime('%B %d, %Y') if investment.end_date else 'Calculating...'],
            ['Status:', investment.status.title()],
        ]
        
        table = Table(data, colWidths=[2.5*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A1F44')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.4*inch))
        
        # QR Code
        qr_data = f"https://portal.elitewealthcapita.uk/verify-certificate/{receipt_num}"
        qr_buffer = self._generate_qr_code(qr_data)
        qr_img = Image(qr_buffer, width=1.5*inch, height=1.5*inch)
        story.append(qr_img)
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph("Scan to verify certificate authenticity", self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_style = ParagraphStyle(
            name='Footer',
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        story.append(Paragraph("This is a computer-generated certificate and does not require a signature.", footer_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
        story.append(Paragraph("Elite Wealth Capital | portal.elitewealthcapita.uk | admin@elitewealthcapita.uk", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_withdrawal_receipt(self, withdrawal):
        """Generate withdrawal receipt PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.pagesize,
                               topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        story = []
        
        # Receipt number
        receipt_num = self._generate_receipt_number('withdrawal', withdrawal.id, withdrawal.created_at)
        story.append(Paragraph(f"Receipt No: {receipt_num}", self.styles['ReceiptNumber']))
        
        # Company header
        story.append(Paragraph("ELITE WEALTH CAPITAL", self.styles['CompanyName']))
        story.append(Paragraph("Investment Platform", self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Receipt title
        story.append(Paragraph("WITHDRAWAL RECEIPT", self.styles['ReceiptTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Amount
        story.append(Paragraph(f"${withdrawal.amount:,.2f}", self.styles['Amount']))
        story.append(Spacer(1, 0.3*inch))
        
        # Withdrawal details table
        data = [
            ['Withdrawal Details', ''],
            ['User:', f"{withdrawal.user.first_name} {withdrawal.user.last_name}"],
            ['Email:', withdrawal.user.email],
            ['Date:', withdrawal.created_at.strftime('%B %d, %Y at %I:%M %p')],
            ['Method:', withdrawal.method.upper() if withdrawal.method else 'N/A'],
            ['Status:', withdrawal.status.title()],
        ]
        
        if withdrawal.wallet_address:
            data.append(['Wallet Address:', withdrawal.wallet_address[:20] + '...'])
        
        if withdrawal.processed_at:
            data.append(['Processed:', withdrawal.processed_at.strftime('%B %d, %Y at %I:%M %p')])
        
        table = Table(data, colWidths=[2.5*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A1F44')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.4*inch))
        
        # QR Code
        qr_data = f"https://portal.elitewealthcapita.uk/verify-receipt/{receipt_num}"
        qr_buffer = self._generate_qr_code(qr_data)
        qr_img = Image(qr_buffer, width=1.5*inch, height=1.5*inch)
        story.append(qr_img)
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph("Scan to verify receipt authenticity", self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_style = ParagraphStyle(
            name='Footer',
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        story.append(Paragraph("This is a computer-generated receipt and does not require a signature.", footer_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
        story.append(Paragraph("Elite Wealth Capital | portal.elitewealthcapita.uk | admin@elitewealthcapita.uk", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer


# Convenience function
def generate_receipt(transaction_type, transaction):
    """
    Generate receipt for any transaction type
    
    Args:
        transaction_type: 'deposit', 'investment', 'withdrawal'
        transaction: Model instance (Deposit, Investment, Withdrawal)
    
    Returns:
        BytesIO buffer containing PDF
    """
    generator = ReceiptGenerator()
    
    if transaction_type == 'deposit':
        return generator.generate_deposit_receipt(transaction)
    elif transaction_type == 'investment':
        return generator.generate_investment_receipt(transaction)
    elif transaction_type == 'withdrawal':
        return generator.generate_withdrawal_receipt(transaction)
    else:
        raise ValueError(f"Unsupported transaction type: {transaction_type}")
