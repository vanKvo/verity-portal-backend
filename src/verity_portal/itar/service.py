import pandas as pd
from sqlalchemy.orm import Session
from fastapi import UploadFile
from src.verity_portal.data_hub.personnel.models import PersonnelModel, CitizenshipStatus
from src.verity_portal.data_hub.projects.models import ProjectModel, ProjectSensitivity
from src.verity_portal.itar.models import ProjectAssignmentModel, ComplianceViolationModel
from src.verity_portal.core.exceptions import ValidationError

class ITARMappingError(ValidationError):
    """Raised when data mapping fails for ITAR roster."""
    pass

class ItarService:
    @staticmethod
    def ingest_roster(db: Session, file: UploadFile, column_mapping: dict = None):
        """Parses a CSV roster and creates project assignments.
        
        Supports dynamic column mapping.
        """
        try:
            df = pd.read_csv(file.file)
        except Exception as e:
            raise ITARMappingError(f"Failed to parse CSV: {str(e)}")

        # Apply mapping if provided
        if column_mapping:
            rename_map = { v: k for k, v in column_mapping.items() if v }
            df = df.rename(columns=rename_map)

        required_cols = ["employee_id", "project_id"]
        if not all(col in df.columns for col in required_cols):
            raise ITARMappingError(f"Missing required columns after mapping: {required_cols}")

        success_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                emp_id = str(row["employee_id"]).strip()
                proj_id = str(row["project_id"]).strip()

                # Lookup personnel from Data Hub
                personnel = db.query(PersonnelModel).filter(PersonnelModel.employee_id == emp_id).first()
                if not personnel:
                    errors.append({"row": index, "error": f"Personnel ID {emp_id} not found in Data Hub. Sync HR Master Data first."})
                    continue

                # Lookup project from Data Hub
                project = db.query(ProjectModel).filter(ProjectModel.project_id == proj_id).first()
                if not project:
                    errors.append({"row": index, "error": f"Project ID {proj_id} not found in Data Hub. Sync Project Master Data first."})
                    continue

                # Check if assignment already exists
                existing = db.query(ProjectAssignmentModel).filter(
                    ProjectAssignmentModel.personnel_id == personnel.id,
                    ProjectAssignmentModel.project_id == project.id
                ).first()

                if not existing:
                    new_assignment = ProjectAssignmentModel(
                        personnel_id=personnel.id,
                        project_id=project.id
                    )
                    db.add(new_assignment)
                    success_count += 1
                else:
                    success_count += 1 # Already exists, count as success
            except Exception as e:
                errors.append({"row": index, "error": str(e)})

        db.commit()
        return {
            "success_count": success_count,
            "error_count": len(errors),
            "errors": errors[:10]
        }

    @staticmethod
    def run_reconciliation_audit(db: Session):
        """Cross-references personnel citizenship against project sensitivity to detect ITAR violations.
        
        Implements AUTO-RESOLUTION logic for eventual consistency.
        """
        # 1. NEW VIOLATIONS DETECTION
        # Find all Foreign Nationals on ITAR Restricted projects
        violations = (
            db.query(ProjectAssignmentModel)
            .join(PersonnelModel)
            .join(ProjectModel)
            .filter(
                PersonnelModel.citizenship_status == CitizenshipStatus.FOREIGN_NATIONAL,
                ProjectModel.sensitivity == ProjectSensitivity.ITAR_RESTRICTED
            )
            .all()
        )

        violations_found = 0
        for v in violations:
            # Check if this violation is already recorded
            existing = db.query(ComplianceViolationModel).filter(
                ComplianceViolationModel.personnel_id == v.personnel_id,
                ComplianceViolationModel.project_id == v.project_id,
                ComplianceViolationModel.status == "OPEN"
            ).first()

            if not existing:
                new_violation = ComplianceViolationModel(
                    personnel_id=v.personnel_id,
                    project_id=v.project_id,
                    status="OPEN",
                    notes="Automated detection: Foreign National assigned to ITAR project."
                )
                db.add(new_violation)
                violations_found += 1
        
        # 2. AUTO-RESOLUTION LOGIC
        # Find OPEN violations that are no longer violations
        open_violations = (
            db.query(ComplianceViolationModel)
            .filter(ComplianceViolationModel.status == "OPEN")
            .all()
        )
        
        resolved_count = 0
        for v in open_violations:
            personnel = db.query(PersonnelModel).get(v.personnel_id)
            project = db.query(ProjectModel).get(v.project_id)
            
            # If citizenship is no longer FOREIGN_NATIONAL or project is no longer ITAR_RESTRICTED
            if (personnel.citizenship_status != CitizenshipStatus.FOREIGN_NATIONAL or 
                project.sensitivity != ProjectSensitivity.ITAR_RESTRICTED):
                
                v.status = "RESOLVED"
                v.resolution_reason = "SYSTEM_AUTO_RESOLVED"
                v.notes = f"System auto-resolved: Data mismatch cleared (Status: {personnel.citizenship_status})"
                resolved_count += 1

        db.commit()
        return {
            "new_violations": violations_found,
            "auto_resolved": resolved_count
        }
