import pytest
import pandas as pd
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from src.verity_portal.data_hub.inventory.service import InventoryService
from src.verity_portal.data_hub.inventory.models import AssetStatus

def test_ingest_inventory_data_auto_mapping_and_normalization():
    db = MagicMock(spec=Session)
    service = InventoryService(db)
    service.ingestor = MagicMock()
    service.ingestor.ingest.return_value = {"success_count": 2, "error_count": 0, "errors": []}

    # Mock raw DataFrame simulating a CSV/Excel read
    data = {
        "Asset Tag": ["TAG-100", "TAG-200"],
        "PO Number": ["PO-1001", "PO-1002"],
        "Status": ["In Use", "Retired"]
    }
    df = pd.DataFrame(data)

    result = service.ingest_master_data(df)

    # Verify ingestor was called
    assert service.ingestor.ingest.called
    called_df = service.ingestor.ingest.call_args[0][0]
    
    # Verify auto-mapping occurred
    assert "asset_tag" in called_df.columns
    assert "po_number" in called_df.columns
    
    # Verify status normalization
    assert called_df.iloc[0]["status"] == AssetStatus.IN_USE
    assert called_df.iloc[1]["status"] == AssetStatus.RETIRED
    
    assert result["success_count"] == 2
