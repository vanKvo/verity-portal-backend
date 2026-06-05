import pytest
import pandas as pd
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from src.verity_portal.data_hub.inventory.service import InventoryService
from src.verity_portal.data_hub.inventory.models import AssetStatus
from src.verity_portal.data_hub.personnel.models import PersonnelModel
from src.verity_portal.data_hub.procurement.models import ProcurementModel

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

def test_ingest_inventory_data_fk_coercion():

    db = MagicMock(spec=Session)
    
    # Mock Personnel query response
    emp_mock_1 = MagicMock()
    emp_mock_1.employee_id = "E101"
    emp_mock_2 = MagicMock()
    emp_mock_2.employee_id = "E102"
    
    # Mock Procurement query response
    po_mock_1 = MagicMock()
    po_mock_1.po_number = "PO-1001"
    
    # Set up mock returns
    def mock_query(model):
        query_mock = MagicMock()
        if model == PersonnelModel.employee_id:
            query_mock.all.return_value = [emp_mock_1, emp_mock_2]
        elif model == ProcurementModel.po_number:
            query_mock.all.return_value = [po_mock_1]
        return query_mock
        
    db.query.side_effect = mock_query

    service = InventoryService(db)
    service.ingestor = MagicMock()
    service.ingestor.ingest.return_value = {"success_count": 2, "error_count": 0, "errors": []}

    # Mock raw DataFrame simulating a CSV/Excel read
    data = {
        "Asset Tag": ["TAG-100", "TAG-200"],
        "PO Number": ["PO-1001", "PO-9999"], # PO-9999 is invalid, should be coerced to None
        "Status": ["In Use", "Retired"],
        "Assigned To": ["E101", "E999"] # E999 is invalid employee, should be coerced to None
    }
    df = pd.DataFrame(data)
    
    mapping = {
        "asset_tag": "Asset Tag",
        "po_number": "PO Number",
        "status": "Status",
        "assigned_employee_id": "Assigned To"
    }

    result = service.ingest_master_data(df, column_mapping=mapping)

    assert service.ingestor.ingest.called
    called_df = service.ingestor.ingest.call_args[0][0]
    
    # Check valid values are retained
    assert called_df.iloc[0]["po_number"] == "PO-1001"
    assert called_df.iloc[0]["assigned_employee_id"] == "E101"
    
    # Check invalid values are coerced to None
    assert pd.isna(called_df.iloc[1]["po_number"])
    assert pd.isna(called_df.iloc[1]["assigned_employee_id"])
    
    assert result["success_count"] == 2
