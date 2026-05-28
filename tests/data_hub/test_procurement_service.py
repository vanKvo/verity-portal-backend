import pytest
import pandas as pd
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from src.verity_portal.data_hub.procurement.service import ProcurementService
from src.verity_portal.data_hub.procurement.models import ProcurementModel

def test_ingest_procurement_data_auto_mapping():
    db = MagicMock(spec=Session)
    service = ProcurementService(db)
    service.ingestor = MagicMock()
    service.ingestor.ingest.return_value = {"success_count": 2, "error_count": 0, "errors": []}

    # Mock raw DataFrame simulating a CSV read
    data = {
        "PO Number": ["PO-1001", "PO-1002"],
        "Purchase Date": ["2023-01-15", "2023-02-20"],
        "Vendor Name": ["Apple", "Dell"],
        "Total Cost": ["1500.00", "800.50"]
    }
    df = pd.DataFrame(data)

    result = service.ingest_master_data(df)

    # Verify ingestor was called
    assert service.ingestor.ingest.called
    called_df = service.ingestor.ingest.call_args[0][0]
    
    # Verify auto-mapping occurred
    assert "po_number" in called_df.columns
    assert "purchase_date" in called_df.columns
    assert "vendor" in called_df.columns
    assert "total_cost" in called_df.columns
    
    assert result["success_count"] == 2
