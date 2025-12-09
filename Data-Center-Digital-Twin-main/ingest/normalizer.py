import json
from typing import Dict

def normalize_doc(doc: Dict) -> Dict:
    """Extracts only the required payload fields for initial DB insertion."""
    if not isinstance(doc, dict):
        raise ValueError("normalize_doc expects a dict")
    meta = doc.get("meta_data", {})
    payload = doc.get("payload", {})
    return {
        "entity_id": meta.get("entityId"),
        "server_workload_percent": payload.get("server_workload_percent"),
        "inlet_temp_c": payload.get("inlet_temp_c"),
        "ambient_temp_c": payload.get("ambient_temp_c"),
    }

def record_tuple_from_normalized(normalized: Dict) -> tuple:
    """Converts normalized dict to a tuple for DB insertion."""
    return (
        normalized.get("entity_id"),
        normalized.get("server_workload_percent"),
        normalized.get("inlet_temp_c"),
        normalized.get("ambient_temp_c"),
    )

