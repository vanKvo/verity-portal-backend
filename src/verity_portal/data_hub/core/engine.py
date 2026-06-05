"""Core ingestion engine for the Data Hub.

This module provides generic low-level data parsing and transactional bulk 
Ingestion tools to convert Pandas DataFrames into database records, 
Ensuring modularity and strict boundary separation.
"""

import logging
import uuid
from typing import Any, Dict, Type, List
import pandas as pd
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


class MasterDataIngestor:
    """A generic transactional bulk ingestion engine for SQLAlchemy models.

    Validates, handles, and upserts master records using nested savepoints.
    """

    def __init__(
        self, 
        db: Session, 
        model: Any, 
        schema: Type[BaseModel], 
        unique_key: str = "employee_id"
    ) -> None:
        """Initializes the bulk ingestion engine.

        Args:
            db: The active database session wrapper.
            model: The target SQLAlchemy model class to populate.
            schema: The validating Pydantic presentation schema/DTO.
            unique_key: The string name of the primary/unique identity column.
        """
        self.db: Session = db
        self.model: Any = model
        self.schema: Type[BaseModel] = schema
        self.unique_key: str = unique_key

    def ingest(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validates and transactionalizes bulk DataFrame records.

        Validates records against the Pydantic schema individually. Performs
        Efficient UPSERTs and logs row-by-row failures using database savepoints.

        Args:
            df: The inbound processed pandas DataFrame.

        Returns:
            A results dictionary containing success_count, error_count, and errors list.
        """
        success_count: int = 0
        errors: List[Dict[str, Any]] = []

        # Convert DF to records for validation
        raw_records: List[Dict[str, Any]] = df.to_dict(orient="records")
        records: List[Dict[str, Any]] = []
        for rec in raw_records:
            cleaned_rec = {
                k: (None if pd.isna(v) else v)
                for k, v in rec.items()
            }
            records.append(cleaned_rec)
        
        for index, record in enumerate(records):
            try:
                # Use a savepoint (sub-transaction) for each row.
                with self.db.begin_nested():
                    # 1. Validate against Pydantic schema
                    validated_data: BaseModel = self.schema(**record)
                    
                    # 2. Check for existing record to perform UPSERT
                    existing_record: Any = self.db.query(self.model).filter(
                        getattr(self.model, self.unique_key) == getattr(validated_data, self.unique_key)
                    ).first()

                    if existing_record:
                        # Update existing
                        for key, value in validated_data.model_dump().items():
                            setattr(existing_record, key, value)
                        if hasattr(existing_record, "updated_at"):
                            existing_record.updated_at = func.now()
                    else:
                        # Create new
                        new_record: Any = self.model(**validated_data.model_dump())
                        self.db.add(new_record)
                    
                    # Flush inside the savepoint to catch DB errors immediately for this row
                    self.db.flush()
                    success_count += 1

            except ValidationError as e:
                err_details: str = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
                errors.append({"row": index + 2, "error": f"Validation Error: {err_details}"})
            except IntegrityError as e:
                # Capture and sanitize database integrity errors (Foreign Key, Unique constraints)
                error_msg = str(e.orig).lower() if e.orig else ""
                
                if "foreign key" in error_msg or "violates foreign key" in error_msg:
                    user_error = "Database integrity violation: Associated relation or reference key not found."
                elif "unique" in error_msg or "duplicate key" in error_msg:
                    user_error = "Database integrity violation: A record with this unique identifier already exists."
                else:
                    user_error = "Database integrity violation: Inbound data fails to satisfy database constraints."
                
                # Generate correlation ID for security auditing
                correlation_id = uuid.uuid4().hex[:8].upper()
                logger.error(
                    f"IntegrityError on row {index} (Ref: ERR-INT-{correlation_id}): {e}",
                    exc_info=True
                )
                errors.append({
                    "row": index + 2, 
                    "error": f"{user_error} (Reference ID: ERR-INT-{correlation_id})"
                })
            except Exception as e:
                # General catch-all: Completely redact raw system errors to protect table structure
                correlation_id = uuid.uuid4().hex[:8].upper()
                logger.error(
                    f"Unexpected ingestion failure on row {index} (Ref: ERR-SYS-{correlation_id}): {e}", 
                    exc_info=True
                )
                errors.append({
                    "row": index + 2, 
                    "error": f"Internal database error occurred. (Reference ID: ERR-SYS-{correlation_id})"
                })

        self.db.commit()
        
        return {
            "success_count": success_count,
            "error_count": len(errors),
            "errors": errors[:20]  # Return first 20 errors for feedback
        }


