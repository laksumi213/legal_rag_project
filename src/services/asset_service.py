# src/services/asset_service.py

import logging
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from src.legal_system.models.tables import FinancialAsset, BankMaster, BranchMaster, AccountTypeMaster

logger = logging.getLogger(__name__)

def _get_or_create_master(session: Session, model, **kwargs):
    """Finds a master record or creates it if it doesn't exist."""
    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
        session.flush() # Flush to get the ID for relationships
    return instance

def sync_bank_assets(session: Session, case_id: int, asset_data_list: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Reconciles the state of bank assets in the DB with the provided list from the UI.
    """
    result = {"added": 0, "updated": 0, "deleted": 0}
    
    existing_assets = session.query(FinancialAsset).filter(
        FinancialAsset.case_id == case_id,
        (FinancialAsset.asset_type == "BANK") | (FinancialAsset.asset_type == None)
    ).all()
    existing_ids = {a.id for a in existing_assets}
    
    incoming_ids = set()

    for data in asset_data_list:
        asset_id = data.get("id")
        bank_name = data.get("銀行名", "").strip()
        branch_name = data.get("支店名", "").strip()
        account_type_name = data.get("種別", "普通").strip()
        
        # Skip empty rows from the data editor
        if not bank_name:
            continue

        # Get or create master data records
        bank = _get_or_create_master(session, BankMaster, bank_name=bank_name)
        branch = _get_or_create_master(session, BranchMaster, bank_id=bank.id, branch_name=branch_name) if branch_name else None
        account_type = _get_or_create_master(session, AccountTypeMaster, type_name=account_type_name)

        if asset_id and asset_id in existing_ids:
            # This is an existing asset, so update it
            incoming_ids.add(asset_id)
            target = session.query(FinancialAsset).get(asset_id)
            
            target.bank_id = bank.id
            target.branch_id = branch.id if branch else None
            target.account_type_id = account_type.id
            target.account_number = data.get("口座番号", "")
            target.balance = data.get("残高", 0) or 0
            target.status = data.get("状況", "")
            
            result["updated"] += 1
        else:
            # This is a new asset, so create it
            new_asset = FinancialAsset(
                case_id=case_id,
                asset_type="BANK",
                bank_id=bank.id,
                branch_id=branch.id if branch else None,
                account_type_id=account_type.id,
                account_number=data.get("口座番号", ""),
                balance=data.get("残高", 0) or 0,
                status=data.get("状況", "入力中"),
            )
            session.add(new_asset)
            result["added"] += 1

    # Determine which assets to delete
    ids_to_delete = existing_ids - incoming_ids
    if ids_to_delete:
        session.query(FinancialAsset).filter(FinancialAsset.id.in_(ids_to_delete)).delete(synchronize_session=False)
        result["deleted"] = len(ids_to_delete)
        
    return result
