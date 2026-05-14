import pandas as pd
from sqlalchemy.orm import Session
from fastapi import UploadFile
from src.verity_portal.shared.models import PersonnelModel
from src.verity_portal.itar.models import ProjectModel, ProjectAssignmentModel
from src.verity_portal.core.exceptions import ValidationError

class ITARMappingError(ValidationError):
    """Raised when data mapping fails for ITAR roster."""
    pass

class ItarService:
    @staticmethod
    def ingest_roster(db: Session, file: UploadFile):
        """Parses a CSV roster and creates project assignments.
        
        Args:
            db: The database session.
            file: The uploaded CSV file.
            
        Raises:
            ITARMappingError: If the CSV is malformed or missing headers.
        """
        try:
            df = pd.read_csv(file.file)
        except Exception as e:
            raise ITARMappingError(f"Failed to parse CSV: {str(e)}")

        required_cols = ["employee_id", "project_id"]
        if not all(col in df.columns for col in required_cols):
            raise ITARMappingError(f"Missing required columns: {required_cols}")

        assignments_created = 0
        for _, row in df.iterrows():
            emp_id = str(row["employee_id"])
            proj_id = str(row["project_id"])

            # Lookup personnel
            personnel = db.query(PersonnelModel).filter(PersonnelModel.employee_id == emp_id).first()
            if not personnel:
                # In a real scenario, we might collect these errors. 
                # For now, let's keep it simple.
                continue

            # Lookup project
            project = db.query(ProjectModel).filter(ProjectModel.project_id == proj_id).first()
            if not project:
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
                assignments_created += 1

        db.commit()
        return assignments_created

    @staticmethod
    def run_reconciliation_audit(db: Session):
        """Cross-references personnel citizenship against project sensitivity to detect ITAR violations.
        
        A violation occurs if a FOREIGN_NATIONAL is assigned to an ITAR_RESTRICTED project.
        """
        from src.verity_portal.shared.models import CitizenshipStatus
        from src.verity_portal.itar.models import ProjectSensitivity, ComplianceViolationModel

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
        
        db.commit()
        return violations_found
