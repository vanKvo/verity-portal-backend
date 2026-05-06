import io
import csv
from typing import List, Dict, Any
from fpdf import FPDF

def generate_audit_csv(violations: List[Dict[str, Any]]) -> bytes:
    """
    Generates a sanitized CSV of compliance violations.
    """
    output = io.StringIO()
    if not violations:
        # Define default headers even if empty
        headers = ["employee_id", "risk_level", "violation_type", "details"]
    else:
        headers = list(violations[0].keys())
        
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(violations)
    
    return output.getvalue().encode('utf-8')

def generate_audit_pdf(violations: List[Dict[str, Any]]) -> bytes:
    """
    Generates an auditor-ready PDF report of compliance violations.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Verity Portal - Compliance Audit Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    # Header Info
    from datetime import datetime
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Total Violations: {len(violations)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    if not violations:
        pdf.set_font("helvetica", "I", 12)
        pdf.cell(0, 10, "No compliance violations found in this audit run.", new_x="LMARGIN", new_y="NEXT")
    else:
        # Table Headers
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(200, 220, 255) # Light blue header
        pdf.cell(40, 10, "Employee ID", border=1, fill=True)
        pdf.cell(30, 10, "Risk Level", border=1, fill=True)
        pdf.cell(50, 10, "Violation Type", border=1, fill=True)
        pdf.cell(70, 10, "Details", border=1, fill=True)
        pdf.ln()
        
        # Table Body
        pdf.set_font("helvetica", "", 9)
        for v in violations:
            pdf.cell(40, 10, str(v.get("employee_id", "N/A")), border=1)
            
            # Color code Risk Level
            risk = v.get("risk_level", "N/A")
            if risk == "HIGH":
                pdf.set_text_color(200, 0, 0) # Red for high risk
            else:
                pdf.set_text_color(0, 0, 0)
                
            pdf.cell(30, 10, risk, border=1)
            pdf.set_text_color(0, 0, 0) # Reset color
            
            pdf.cell(50, 10, str(v.get("violation_type", "N/A")), border=1)
            pdf.cell(70, 10, str(v.get("details", "N/A")), border=1)
            pdf.ln()

    return bytes(pdf.output())
