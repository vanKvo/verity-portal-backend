"""Core ingestion engine for the Data Hub.

This module provides generic low-level data parsing and transactional bulk 
ingestion tools to convert Pandas DataFrames into database records, 
ensuring modularity and strict boundary separation.
"""

import logging
from typing import Any, Dict, Type, List
import pandas as pd
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session
from sqlalchemy import func

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
        efficient UPSERTs and logs row-by-row failures using database savepoints.

        Args:
            df: The inbound processed pandas DataFrame.

        Returns:
            A results dictionary containing success_count, error_count, and errors list.
        """
        success_count: int = 0
        errors: List[Dict[str, Any]] = []

        # Convert DF to records for validation
        records: List[Dict[str, Any]] = df.to_dict(orient="records")
        
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
            except Exception as e:
                errors.append({"row": index + 2, "error": f"Exception for ingesting data: {str(e)}"})
                logger.error(f"Error ingesting row {index}: {e}")

        self.db.commit()
        
        return {
            "success_count": success_count,
            "error_count": len(errors),
            "errors": errors[:20]  # Return first 20 errors for feedback
        }


