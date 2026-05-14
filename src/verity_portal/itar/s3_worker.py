import io
import pandas as pd
import boto3
from sqlalchemy.orm import Session
from thefuzz import process
from src.verity_portal.shared.models import PersonnelModel, CitizenshipStatus

class S3WorkerService:
    """Service for background processing of HR data from AWS S3."""

    CITIZENSHIP_MAP = {
        "US_CITIZEN": ["US", "USA", "United States", "U.S.", "U.S. Citizen", "Citizen"],
        "PERMANENT_RESIDENT": ["Permanent Resident", "Green Card", "LPR"],
        "FOREIGN_NATIONAL": ["Foreign National", "Non-US", "H1B", "L1"]
    }

    def __init__(self, db: Session):
        self.db = db
        self.s3 = boto3.client("s3")

    def normalize_citizenship(self, raw_status: str) -> CitizenshipStatus:
        """Uses fuzzy matching to map a string to a CitizenshipStatus ENUM.
        
        Args:
            raw_status: The string from the HR system.
            
        Returns:
            The normalized CitizenshipStatus.
        """
        if not raw_status or pd.isna(raw_status):
            return CitizenshipStatus.UNKNOWN

        # Flatten choices for fuzzy process
        choices = []
        mapping = {}
        for status, aliases in self.CITIZENSHIP_MAP.items():
            for alias in aliases:
                choices.append(alias)
                mapping[alias] = status

        # Find best match
        best_match, score = process.extractOne(raw_status, choices)
        
        if score > 80:
            status_str = mapping[best_match]
            return CitizenshipStatus[status_str]
        
        return CitizenshipStatus.UNKNOWN

    def sync_hr_data(self, bucket: str, key: str) -> int:
        """Downloads HR data from S3 and updates personnel citizenship statuses.
        
        Args:
            bucket: S3 bucket name.
            key: S3 object key.
            
        Returns:
            Number of records processed.
        """
        response = self.s3.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8")
        
        df = pd.read_csv(io.StringIO(content))
        
        processed_count = 0
        for _, row in df.iterrows():
            emp_id = str(row["employee_id"])
            raw_cit = str(row.get("citizenship", ""))

            personnel = self.db.query(PersonnelModel).filter(PersonnelModel.employee_id == emp_id).first()
            if personnel:
                personnel.citizenship_status = self.normalize_citizenship(raw_cit)
                processed_count += 1
        
        self.db.commit()
        return processed_count
