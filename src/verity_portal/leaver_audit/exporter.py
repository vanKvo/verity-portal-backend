import io
import csv
from typing import List, Dict, Any
from fpdf import FPDF
from datetime import datetime

def generate_audit_csv(violations: List[Dict[str, Any]]) -> bytes:
    output = io.StringIO()
    if not violations:
        headers = ["employee_id", "risk_level", "violation_type", "details"]
    else:
        headers = list(violations[0].keys())
        
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(violations)
    
    return output.getvalue().encode('utf-8')

def generate_audit_pdf(violations: List[Dict[str, Any]]) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Verity Portal - Compliance Audit Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Total Violations: {len(violations)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    if not violations:
        pdf.set_font("helvetica", "I", 12)
        pdf.cell(0, 10, "No compliance violations found in this audit run.", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("helvetica", "", 10)
        # Using fpdf2's table feature for automatic line wrapping and column management
        with pdf.table(
            borders_layout="SINGLE_TOP_LINE",
            cell_fill_color=(245, 245, 245),
            cell_fill_mode="ROWS",
            line_height=pdf.font_size * 2.5,
            text_align="LEFT",
            width=190,
            col_widths=(35, 25, 45, 85)
        ) as table:
            # Header Row
            pdf.set_font("helvetica", "B", 10)
            header = table.row()
            header.cell("Employee ID")
            header.cell("Risk Level")
            header.cell("Violation Type")
            header.cell("Details")
            
            # Data Rows
            pdf.set_font("helvetica", "", 9)
            for v in violations:
                row = table.row()
                row.cell(str(v.get("employee_id", "N/A")))
                
                risk = str(v.get("risk_level", "N/A"))
                row.cell(risk)
                
                row.cell(str(v.get("violation_type", "N/A")))
                row.cell(str(v.get("details", "N/A")))

    return bytes(pdf.output())
