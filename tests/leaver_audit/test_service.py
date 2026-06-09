import pytest
from src.verity_portal.audit.service import audit_leaver_mover
from src.verity_portal.audit.exceptions import AuditDataInconsistencyError

def test_audit_leaver_mover_identifies_violation():
    hr_records = [
        {"employee_id": "EMP001", "hr_termination_date": "2023-10-01"}
    ]
    access_records = [
        {"employee_id": "EMP001", "last_system_login": "2023-10-05"}
    ]
    
    violations = audit_leaver_mover(hr_records, access_records)
    
    assert len(violations) == 1
    assert violations[0]["employee_id"] == "EMP001"
    assert violations[0]["risk_level"] == "HIGH"

def test_audit_leaver_mover_ignores_valid_access():
    hr_records = [
        {"employee_id": "EMP002", "hr_termination_date": "2023-10-10"}
    ]
    access_records = [
        {"employee_id": "EMP002", "last_system_login": "2023-10-05"}
    ]
    
    violations = audit_leaver_mover(hr_records, access_records)
    assert len(violations) == 0

def test_audit_leaver_mover_handles_active_employees():
    hr_records = [
        {"employee_id": "EMP003", "hr_termination_date": None} # Active
    ]
    access_records = [
        {"employee_id": "EMP003", "last_system_login": "2023-11-01"}
    ]
    
    violations = audit_leaver_mover(hr_records, access_records)
    assert len(violations) == 0

def test_audit_leaver_mover_handles_empty_records():
    assert audit_leaver_mover([], []) == []

def test_audit_leaver_mover_raises_exception_on_invalid_dates():
    hr_records = [{"employee_id": "EMP004", "hr_termination_date": "not-a-date"}]
    access_records = [{"employee_id": "EMP004", "last_system_login": "2023-10-05"}]
    
    with pytest.raises(AuditDataInconsistencyError) as excinfo:
        audit_leaver_mover(hr_records, access_records)
    
    assert "Invalid date format" in str(excinfo.value)
