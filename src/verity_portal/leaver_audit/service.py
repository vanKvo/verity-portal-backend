from datetime import datetime
from typing import List, Dict, Any
from src.verity_portal.leaver_audit.exceptions import AuditDataInconsistencyError

def audit_leaver_mover(hr_records: List[Dict[str, Any]], access_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Reconciles HR termination records with system access logs to identify violations.
    """
    violations = []
    hr_map = {hr.get("employee_id"): hr for hr in hr_records if hr.get("employee_id")}
        
    for access in access_records:
        eid = access.get("employee_id")
        login_date_str = access.get("last_system_login")
        
        if not eid or not login_date_str:
            continue
            
        hr_info = hr_map.get(eid)
        if not hr_info:
            continue 
            
        term_date_str = hr_info.get("hr_termination_date")
        if not term_date_str:
            continue 
            
        try:
            term_date = datetime.fromisoformat(term_date_str)
            login_date = datetime.fromisoformat(login_date_str)
            
            if login_date > term_date:
                violations.append({
                    "employee_id": eid,
                    "hr_termination_date": term_date_str,
                    "last_system_login": login_date_str,
                    "risk_level": "HIGH",
                    "violation_type": "LEAVER_ACCESS",
                    "details": f"System access logged on {login_date_str} after termination on {term_date_str}"
                })
        except ValueError as e:
            raise AuditDataInconsistencyError(f"Invalid date format for employee {eid}: {str(e)}")
            
    return violations
