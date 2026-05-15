import pandas as pd
from typing import List, Type, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from pydantic import BaseModel, ValidationError
import logging

logger = logging.getLogger(__name__)

class MasterDataIngestor:
    """Generic engine for ingesting master data from DataFrames into SQLAlchemy models."""

    def __init__(self, db: Session, model: Any, schema: Type[BaseModel], unique_key: str = "employee_id"):
        self.db = db
        self.model = model
        self.schema = schema
        self.unique_key = unique_key

    def ingest(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validates and ingests the data in bulk.
        
        Returns a summary of the ingestion process.
        """
        success_count = 0
        errors = []

        # Convert DF to records for validation
        records = df.to_dict(orient="records")
        
        for index, record in enumerate(records):
            try:
                # Use a savepoint (sub-transaction) for each row.
                with self.db.begin_nested():
                    # 1. Validate against Pydantic schema
                    validated_data = self.schema(**record)
                    
                    # 2. Check for existing record to perform UPSERT
                    existing_record = self.db.query(self.model).filter(
                        getattr(self.model, self.unique_key) == getattr(validated_data, self.unique_key)
                    ).first()

                    if existing_record:
                        # Update existing
                        for key, value in validated_data.model_dump().items():
                            setattr(existing_record, key, value)
                    else:
                        # Create new
                        new_record = self.model(**validated_data.model_dump())
                        self.db.add(new_record)
                    
                    # Flush inside the savepoint to catch DB errors immediately for this row
                    self.db.flush()
                    success_count += 1

            except ValidationError as e:
                err_details = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
                errors.append({"row": index + 2, "error": f"Validation Error: {err_details}"})
            except Exception as e:
                errors.append({"row": index + 2, "error": f"Database Error: {str(e)}"})
                logger.error(f"Error ingesting row {index}: {e}")

        self.db.commit()
        
        return {
            "success_count": success_count,
            "error_count": len(errors),
            "errors": errors[:20]  # Return first 20 errors for feedback
        }
