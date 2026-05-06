import pytest
import io
import csv
from app.domain.services.exporter import generate_audit_csv, generate_audit_pdf

@pytest.fixture
def sample_violations():
    return [
        {
            "employee_id": "EMP001",
            "hr_termination_date": "2023-10-01",
            "last_system_login": "2023-10-05",
            "risk_level": "HIGH",
            "violation_type": "LEAVER_ACCESS",
            "details": "Access after termination"
        }
    ]

def test_generate_audit_csv_returns_valid_csv(sample_violations):
    csv_bytes = generate_audit_csv(sample_violations)
    
    assert isinstance(csv_bytes, bytes)
    
    # Read back CSV to verify
    csv_text = csv_bytes.decode('utf-8')
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]["employee_id"] == "EMP001"
    assert rows[0]["risk_level"] == "HIGH"

def test_generate_audit_pdf_returns_pdf_bytes(sample_violations):
    pdf_bytes = generate_audit_pdf(sample_violations)
    
    assert isinstance(pdf_bytes, bytes)
    # PDF header check
    assert pdf_bytes.startswith(b"%PDF-")

def test_generate_audit_csv_handles_empty():
    csv_bytes = generate_audit_csv([])
    assert isinstance(csv_bytes, bytes)
    assert len(csv_bytes) > 0 # Header only
