"""CSV/Excel upload routes — database-backed import lifecycle."""
import os
import json
from datetime import datetime, date, time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.import_session import ImportSession
from app.services.ingestion_service import parse_csv, parse_excel, validate_and_normalize, commit_import

router = APIRouter()


class ImportConfirmRequest(BaseModel):
    import_id: str
    organization_id: int = 1


# ── JSON-safe normalization ─────────────────────────────────────
def make_json_safe(value):
    """Recursively convert non-JSON-serializable values to safe types.

    Handles: datetime, date, time, pandas.Timestamp/NaT,
    numpy scalars, tuples, NaN, NaT, None.
    """
    if value is None:
        return None

    # datetime / date / time
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()

    # pandas types (gracefully skip if pandas not installed)
    try:
        import pandas as pd
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        if value is pd.NaT:
            return None
    except ImportError:
        pass

    # numpy scalars
    try:
        import numpy as np
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.floating):
            v = float(value)
            return None if v != v else v  # NaN → None
        if isinstance(value, np.bool_):
            return bool(value)
        if value is np.nan:
            return None
    except ImportError:
        pass

    # float NaN check
    if isinstance(value, float) and value != value:
        return None

    # Containers
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [make_json_safe(i) for i in value]

    return value


def _gen_import_id(db: Session) -> str:
    year = datetime.utcnow().year
    count = db.query(ImportSession).count() + 1
    return f"IMP-{year}-{count:05d}"


@router.post("/import/preview")
async def preview_import(
    file: UploadFile = File(...),
    organization_id: int = 1,
    db: Session = Depends(get_db),
):
    """Upload CSV/Excel, validate, store as pending ImportSession."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported. Use CSV or Excel.")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    try:
        rows, headers = parse_csv(content) if ext == ".csv" else parse_excel(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing file: {e}")

    if not rows:
        raise HTTPException(status_code=400, detail="No data rows found in the file")

    result = validate_and_normalize(rows, headers, db, organization_id)

    # Build the full dict to store, then normalize ALL values to JSON-safe types
    serializable = {k: v for k, v in result.items() if not k.startswith("_")}
    serializable["_all_valid"] = result.get("_all_valid", [])
    serializable = make_json_safe(serializable)

    session = ImportSession(
        import_id=_gen_import_id(db),
        organization_id=organization_id,
        filename=file.filename,
        status="pending",
        total_rows=result["total_rows"],
        valid_rows=result["valid_rows"],
        invalid_rows=result["invalid_rows"],
        errors_json=make_json_safe(result.get("errors", [])),
        validated_data_json=serializable,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "import_id": session.import_id,
        "filename": session.filename,
        "status": session.status,
        "total_rows": session.total_rows,
        "valid_rows": session.valid_rows,
        "invalid_rows": session.invalid_rows,
        "errors": session.errors_json,
        "preview_data": make_json_safe(result.get("preview_data", [])),
    }


@router.post("/import/confirm")
def confirm_import(data: ImportConfirmRequest, db: Session = Depends(get_db)):
    """Confirm and commit a previously previewed import by import_id."""
    import_id = data.import_id
    organization_id = data.organization_id

    if not import_id:
        raise HTTPException(status_code=400, detail="import_id is required. Upload a file first.")

    session = db.query(ImportSession).filter(ImportSession.import_id == import_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Import {import_id} not found.")

    if session.status == "completed":
        raise HTTPException(status_code=400, detail=f"Import {import_id} has already been completed.")

    if session.status == "failed":
        raise HTTPException(status_code=400, detail=f"Import {import_id} previously failed.")

    if session.organization_id != organization_id:
        raise HTTPException(status_code=400, detail="This import belongs to a different organization.")

    # Deserialize validated data
    validated_data = session.validated_data_json or {}
    if not validated_data.get("_all_valid"):
        raise HTTPException(status_code=400, detail="No valid rows to import.")

    result = commit_import(db, validated_data)

    session.status = "completed"
    session.created_count = result.get("created", 0)
    session.skipped_count = result.get("skipped", 0)
    session.errors_json = result.get("errors", [])
    session.completed_at = datetime.utcnow()
    db.commit()

    if result.get("errors"):
        raise HTTPException(status_code=422, detail={
            "message": "Import completed with errors",
            "import_id": import_id,
            "errors": result["errors"],
            "imported": result["created"],
            "rejected": result["skipped"],
        })

    return {
        "success": True,
        "import_id": import_id,
        "status": "completed",
        "total_rows": session.total_rows,
        "imported": result["created"],
        "rejected": result["skipped"],
        "message": f"{result['created']} resources imported successfully.",
    }
