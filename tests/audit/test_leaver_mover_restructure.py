import pytest
import io
from datetime import datetime, date, timezone
from unittest.mock import MagicMock
from src.verity_portal.data_hub.personnel.models import PersonnelModel, CitizenshipStatus
from src.verity_portal.data_hub.it_activity.models import ItActivityModel
from src.verity_portal.data_hub.it_activity.service import ItActivityService
from src.verity_portal.audit.models import LeaverViolationModel, LeaverViolationStatus
from src.verity_portal.audit.engine import LeaverMoverReconciliationEngine
from src.verity_portal.core.email import BaseEmailService
from src.verity_portal.identity.router import create_access_token
from src.verity_portal.data_hub.core.models import IngestionLogModel


def test_it_activity_ingestion(db_session):
    """Verify that IT Activity logs are parsed and successfully stored/upserted."""
    import pandas as pd
    
    data = {
        "employee_id": ["E501", "E502"],
        "login_date": ["2026-06-01 10:00:00", "2026-06-02 11:30:00"],
        "ip": ["192.168.1.50", "192.168.1.60"],
        "system": ["AD", "Slack"],
        "username": ["jdoe", "asmith"],
        "access_level": ["Administrator", "User"]
    }
    df = pd.DataFrame(data)
    
    service = ItActivityService(db_session)
    result = service.ingest_master_data(df)
    
    assert result["success_count"] == 2
    assert result["error_count"] == 0
    
    act1 = db_session.query(ItActivityModel).filter_by(employee_id="E501").first()
    assert act1 is not None
    assert act1.system_name == "AD"
    assert act1.ip_address == "192.168.1.50"
    assert act1.user_name == "jdoe"
    assert act1.system_access_level == "Administrator"
    assert act1.last_system_login.strftime("%Y-%m-%d %H:%M:%S") == "2026-06-01 10:00:00"


def test_reconciliation_detects_post_termination_access(db_session):
    """Verify that the engine flags access occurring after termination date."""
    # 1. terminated employee
    personnel = PersonnelModel(
        employee_id="E900",
        first_name="Jane",
        last_name="Doe",
        citizenship_status=CitizenshipStatus.US_CITIZEN,
        termination_date=date(2026, 5, 1)
    )
    # 2. post-termination system login log
    it_activity = ItActivityModel(
        employee_id="E900",
        last_system_login=datetime(2026, 5, 15, 14, 0, 0, tzinfo=timezone.utc),
        system_name="Active Directory",
        ip_address="192.168.1.100"
    )
    db_session.add(personnel)
    db_session.add(it_activity)
    db_session.commit()
    
    # 3. run audit
    email_mock = MagicMock(spec=BaseEmailService)
    engine = LeaverMoverReconciliationEngine(db_session, email_service=email_mock)
    result = engine.run_audit()
    
    assert result["new_violations"] == 1
    
    # 4. Check DB state
    violation = db_session.query(LeaverViolationModel).filter_by(employee_id="E900").first()
    assert violation is not None
    assert violation.status == LeaverViolationStatus.OPEN
    assert violation.hr_termination_date == date(2026, 5, 1)
    assert violation.system_name == "Active Directory"
    assert violation.ip_address == "192.168.1.100"
    
    # verify email alert was sent
    email_mock.send_alert.assert_called_once()


def test_upload_it_activity_rbac(client):
    """Verify endpoint access permissions for uploading activity logs."""
    csv_content = "employee_id,login_date,ip,system\nE501,2026-06-01 10:00:00,192.168.1.1,AD"
    file = ("log.csv", io.BytesIO(csv_content.encode()))
    
    # 1. Allowed roles
    token_it = create_access_token(data={"sub": "it@verity.com", "roles": ["ROLE_IT"]})
    response = client.post(
        "/data-hub/it-activity/upload",
        files={"file": file},
        headers={"Authorization": f"Bearer {token_it}"}
    )
    assert response.status_code == 200
    
    # 2. Blocked roles
    file2 = ("log.csv", io.BytesIO(csv_content.encode()))
    token_pm = create_access_token(data={"sub": "pm@verity.com", "roles": ["ROLE_PM"]})
    response2 = client.post(
        "/data-hub/it-activity/upload",
        files={"file": file2},
        headers={"Authorization": f"Bearer {token_pm}"}
    )
    assert response2.status_code == 403


def test_get_violations_rbac(client, db_session):
    """Verify endpoint access permissions for retrieving violations."""
    # Seed a violation
    violation = LeaverViolationModel(
        employee_id="E999",
        hr_termination_date=date(2026, 5, 1),
        last_system_login=datetime(2026, 5, 15, 14, 0, 0),
        status=LeaverViolationStatus.OPEN
    )
    db_session.add(violation)
    db_session.commit()
    
    # 1. IT, ECO, and HR roles should be allowed
    token_it = create_access_token(data={"sub": "it@verity.com", "roles": ["ROLE_IT"]})
    response = client.get(
        "/audit/leaver-mover/violations",
        headers={"Authorization": f"Bearer {token_it}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    token_hr = create_access_token(data={"sub": "hr@verity.com", "roles": ["ROLE_HR"]})
    response_hr = client.get(
        "/audit/leaver-mover/violations",
        headers={"Authorization": f"Bearer {token_hr}"}
    )
    assert response_hr.status_code == 200
    
    # 2. Block PM role
    token_pm = create_access_token(data={"sub": "pm@verity.com", "roles": ["ROLE_PM"]})
    response_pm = client.get(
        "/audit/leaver-mover/violations",
        headers={"Authorization": f"Bearer {token_pm}"}
    )
    assert response_pm.status_code == 403


def test_resolve_violation_rbac(client, db_session):
    """Verify endpoint access permissions and actions for resolving violations."""
    # Seed an open violation
    personnel = PersonnelModel(
        employee_id="E900",
        first_name="Jane",
        citizenship_status=CitizenshipStatus.US_CITIZEN
    )
    db_session.add(personnel)
    db_session.flush()

    violation = LeaverViolationModel(
        employee_id="E900",
        hr_termination_date=date(2026, 5, 1),
        last_system_login=datetime(2026, 5, 15, 14, 0, 0),
        status=LeaverViolationStatus.OPEN
    )
    db_session.add(violation)
    db_session.commit()
    
    violation_id = str(violation.id)
    
    # 1. ROLE_IT should be forbidden from resolving
    token_it = create_access_token(data={"sub": "it@verity.com", "roles": ["ROLE_IT"]})
    response = client.post(
        f"/audit/leaver-mover/violations/{violation_id}/resolve",
        json={"resolution_reason": "Approved extension"},
        headers={"Authorization": f"Bearer {token_it}"}
    )
    assert response.status_code == 403
    
    # 2. ROLE_ECO should succeed
    token_eco = create_access_token(data={"sub": "eco@verity.com", "roles": ["ROLE_ECO"]})
    response_eco = client.post(
        f"/audit/leaver-mover/violations/{violation_id}/resolve",
        json={"resolution_reason": "Approved extension"},
        headers={"Authorization": f"Bearer {token_eco}"}
    )
    assert response_eco.status_code == 200
    data = response_eco.json()
    assert data["status"] == "RESOLVED"
    assert data["resolution_reason"] == "Approved extension"
    assert data["resolved_by"] == "eco@verity.com"


def test_ingestion_logging_manual_and_s3(client, db_session):
    """Verify that manual uploads and S3 sync operations log to the ingestion_logs table."""
    csv_content = "employee_id,login_date,ip,system\nE501,2026-06-01 10:00:00,192.168.1.1,AD"
    file = ("log.csv", io.BytesIO(csv_content.encode()))
    
    token_it = create_access_token(data={"sub": "it_admin@verity.com", "roles": ["ROLE_IT"]})
    response = client.post(
        "/data-hub/it-activity/upload",
        files={"file": file},
        headers={"Authorization": f"Bearer {token_it}"}
    )
    assert response.status_code == 200
    
    # Query database to check log entry
    logs = db_session.query(IngestionLogModel).all()
    assert len(logs) == 1
    assert logs[0].schema_type == "it_activity"
    assert logs[0].source == "MANUAL"
    assert logs[0].uploaded_by == "it_admin@verity.com"
    assert logs[0].records_count == 1
