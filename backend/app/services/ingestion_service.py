"""CSV/Excel Ingestion Service.

Resolves human-readable organization/department names to database IDs,
converts textual utilization values to integers, converts years→months,
validates specifications JSON, and uses transactions for safety.
"""
import io
import csv
import json
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

import openpyxl
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.resource import Resource
from app.models.organization import Organization
from app.models.department import Department

REQUIRED_COLUMNS = {"resource_id", "category", "type", "name", "organization", "department"}


# ---------------------------------------------------------------------------
# File parsing
# ---------------------------------------------------------------------------

def parse_csv(file_content: bytes) -> Tuple[List[Dict[str, str]], List[str]]:
    """Parse CSV bytes into (rows, headers)."""
    text = file_content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = [row for row in reader]
    return rows, reader.fieldnames or []


def parse_excel(file_content: bytes) -> Tuple[List[Dict[str, str]], List[str]]:
    """Parse Excel bytes into (rows, headers)."""
    wb = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    headers = [str(h).strip().lower().replace(" ", "_") if h else "" for h in next(rows_iter)]
    rows = []
    for row in rows_iter:
        rows.append({
            headers[i]: str(val) if val is not None else ""
            for i, val in enumerate(row)
            if i < len(headers) and headers[i]
        })
    wb.close()
    return rows, headers


# ---------------------------------------------------------------------------
# Utilization text → int
# ---------------------------------------------------------------------------

_UTILIZATION_MAP = {
    "unused": 0,
    "highly underutilized": 5,
    "underutilized": 20,
    "low": 25,
    "moderate": 50,
    "normal": 60,
    "medium": 60,
    "high": 80,
    "highly utilized": 90,
    "fully utilized": 100,
}


def _parse_utilization(raw: str) -> int:
    """Convert a textual or numeric utilization value to 0-100 integer.

    Accepts:
      • Numeric strings  → clamped to 0-100
      • Textual labels   → looked up in _UTILIZATION_MAP
    Falls back to 0 when unrecognised.
    """
    raw = (raw or "").strip()
    if not raw:
        return 0

    # Try numeric first
    try:
        val = int(float(raw))
        return max(0, min(100, val))
    except (ValueError, TypeError):
        pass

    # Textual lookup (case-insensitive)
    return _UTILIZATION_MAP.get(raw.lower().strip(), 0)


# ---------------------------------------------------------------------------
# Remaining life: years → months
# ---------------------------------------------------------------------------

def _parse_remaining_life_months(raw: str) -> int:
    """Parse remaining useful life from CSV.

    The CSV column may be ``remaining_useful_life_years`` (numeric years)
    or ``remaining_life`` (months).  The database column is always months.
    """
    raw = (raw or "").strip()
    if not raw:
        return 36  # default

    try:
        val = float(raw)
    except (ValueError, TypeError):
        return 36

    # If the value is ≤ 5 we treat it as years; otherwise as months.
    # (A remaining life of 5 months is plausible but uncommon; ≤ 5 years
    # is the more likely interpretation for a CSV user.)
    if val <= 5:
        return int(val * 12)
    return int(val)


# ---------------------------------------------------------------------------
# Organization / Department resolution
# ---------------------------------------------------------------------------

def _resolve_organization(
    db: Session,
    org_name: str,
    created_orgs: Dict[str, Organization],
) -> Tuple[Optional[Organization], Optional[str]]:
    """Resolve an organization name to an Organization instance.

    Returns (org, error_message).  error_message is ``None`` on success.
    New organisations are created and cached in *created_orgs* so the
    same name within a single import doesn't hit the DB repeatedly.
    """
    name = org_name.strip()
    if not name:
        return None, "Organization name is empty"

    # Fast path: already resolved during this import
    if name in created_orgs:
        return created_orgs[name], None

    # Look up existing organisation (case-insensitive)
    org = (
        db.query(Organization)
        .filter(Organization.name.ilike(name))
        .first()
    )
    if org:
        created_orgs[name] = org
        return org, None

    # Create new organisation (matches existing app design in seed_data.py)
    code = name.upper().replace(" ", "")[:50]
    # Ensure unique code
    existing_code = db.query(Organization).filter(Organization.code == code).first()
    if existing_code:
        created_orgs[name] = existing_code
        return existing_code, None

    org = Organization(name=name, code=code)
    db.add(org)
    db.flush()  # assign id
    created_orgs[name] = org
    return org, None


def _resolve_department(
    db: Session,
    org: Organization,
    dept_name: str,
    created_depts: Dict[Tuple[int, str], Department],
) -> Tuple[Optional[Department], Optional[str]]:
    """Resolve a department name under a specific organisation.

    Returns (dept, error_message).
    """
    name = dept_name.strip()
    if not name:
        return None, "Department name is empty"

    cache_key = (org.id, name.lower())
    if cache_key in created_depts:
        return created_depts[cache_key], None

    # Look up existing department under this organisation
    dept = (
        db.query(Department)
        .filter(
            Department.organization_id == org.id,
            Department.name.ilike(name),
        )
        .first()
    )
    if dept:
        created_depts[cache_key] = dept
        return dept, None

    # Create new department under the correct organisation
    code = name.upper().replace(" ", "")[:50]
    dept = Department(organization_id=org.id, name=name, code=code)
    db.add(dept)
    db.flush()
    created_depts[cache_key] = dept
    return dept, None


# ---------------------------------------------------------------------------
# Specifications JSON parsing
# ---------------------------------------------------------------------------
def _build_specifications(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Build the normalized specifications JSON from CSV columns.

    Supports both:
    1. A JSON `specifications` column
    2. Individual columns such as cpu, ram, storage, material_or_specs
    """

    specs: Dict[str, Any] = {}

    # If an explicit JSON specifications column exists, use it first.
    raw_json = (row.get("specifications") or "").strip()

    if raw_json:
        parsed, error = _parse_specifications(raw_json)
        if error is None and parsed:
            specs.update(parsed)

    # Individual specification columns
    cpu = (row.get("cpu") or "").strip()
    ram = (row.get("ram") or "").strip()
    storage = (row.get("storage") or "").strip()

    if cpu:
        specs["cpu"] = cpu

    if ram:
        specs["ram"] = ram

    if storage:
        specs["storage"] = storage

    # material_or_specs is used for things such as GPU or material.
    extra = (row.get("material_or_specs") or "").strip()

    if extra:
        category = (row.get("category") or "").strip().lower()
        resource_type = (row.get("type") or "").strip().lower()

        if category == "computer" or "computer" in resource_type:
            specs["gpu"] = extra
        else:
            specs["material"] = extra

    return specs
def _parse_specifications(raw: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Parse a JSON string into a dict.

    Returns (specs_dict, error_message).  On error the dict is ``None``.
    """
    raw = (raw or "").strip()
    if not raw:
        return {}, None

    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        return None, f"Invalid specifications JSON: {exc}"

    if not isinstance(parsed, dict):
        return None, "Specifications must be a JSON object, not an array or primitive"

    return parsed, None


# ---------------------------------------------------------------------------
# Main validation entry-point
# ---------------------------------------------------------------------------

def validate_and_normalize(
    rows: List[Dict[str, str]],
    headers: List[str],
    db: Session,
    organization_id: int = 1,
) -> Dict[str, Any]:
    """Validate, normalise, and prepare rows for import.

    This function resolves human-readable ``organization`` and ``department``
    CSV values to the corresponding database IDs, creates missing
    organisations/departments as needed, and reports clear per-row errors.
    """
    # ── Header check ───────────────────────────────────────────────
    normalized_headers = [h.strip().lower().replace(" ", "_") for h in headers]
    missing_cols = REQUIRED_COLUMNS - set(normalized_headers)
    if missing_cols:
        return {
            "total_rows": len(rows),
            "valid_rows": 0,
            "invalid_rows": len(rows),
            "errors": [{"row": 0, "error": f"Missing required columns: {', '.join(sorted(missing_cols))}"}],
            "preview_data": [],
        }

    # Caches so we don't repeat lookups / creates within one import
    created_orgs: Dict[str, Organization] = {}
    created_depts: Dict[Tuple[int, str], Department] = {}

    valid_rows: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for i, row in enumerate(rows, 1):
        row_errors: List[str] = []

        # ── Required field presence ────────────────────────────────
        for field in ("resource_id", "category", "type", "name"):
            if not (row.get(field) or "").strip():
                row_errors.append(f"Missing required field: {field}")

        if row_errors:
            errors.append({"row": i, "errors": row_errors})
            continue

        # ── Resolve organisation ───────────────────────────────────
        org_name = (row.get("organization") or "").strip()
        org, org_err = _resolve_organization(db, org_name, created_orgs)
        if org_err:
            errors.append({"row": i, "errors": [f"Organization: {org_err}"]})
            continue

        # ── Resolve department (under the correct organisation) ────
        dept_name = (row.get("department") or "").strip()
        dept, dept_err = _resolve_department(db, org, dept_name, created_depts)
        if dept_err:
            errors.append({"row": i, "errors": [f"Department: {dept_err}"]})
            continue

        # ── Condition ──────────────────────────────────────────────
        condition = (row.get("condition") or "Good").strip() or "Good"
        valid_conditions = {"excellent", "good", "fair", "poor", "non-functional"}
        if condition.lower() not in valid_conditions:
            condition = "Good"

        # ── Availability ───────────────────────────────────────────
        availability = (row.get("availability") or "available").strip() or "available"

        # ── Utilization (text or numeric → int 0-100) ─────────────
        utilization = _parse_utilization(row.get("utilization", ""))

        # ── Remaining life (years or months → months) ─────────────
        remaining_months = _parse_remaining_life_months(
            row.get("remaining_useful_life_years")
            or row.get("remaining_life")
            or ""
        )

        # ── Purchase date ──────────────────────────────────────────
        purchase_date = None
        pd_str = (row.get("purchase_date") or "").strip()
        if pd_str:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
                try:
                    purchase_date = datetime.strptime(pd_str, fmt)
                    break
                except ValueError:
                    continue

        # ── Specifications JSON ────────────────────────────────────
        specs = _build_specifications(row)
        # ── Owner (optional — must be NULL when blank) ─────────────
        owner_id_raw = (row.get("owner_id") or "").strip()
        owner_id = None
        if owner_id_raw:
            try:
                owner_id = int(owner_id_raw)
            except (ValueError, TypeError):
                errors.append({"row": i, "errors": [f"Invalid owner_id: {owner_id_raw}"]})
                continue

        # ── Assemble validated row ─────────────────────────────────
        valid_rows.append({
            "resource_id": row["resource_id"].strip(),
            "category": row["category"].strip(),
            "type": row["type"].strip(),
            "name": row["name"].strip(),
            "description": (row.get("description") or "").strip(),
            "organization_id": org.id,
            "department_id": dept.id,
            "owner_id": owner_id,
            "condition": condition,
            "availability": availability,
            "utilization": utilization,
            "status": "active",
            "location": (row.get("location") or "").strip(),
            "building": (row.get("building") or "").strip(),
            "room": (row.get("room") or "").strip(),
            "purchase_date": purchase_date.isoformat() if purchase_date else None,
            "remaining_useful_life_months": remaining_months,
            "specifications": specs,
            "share_scope": (row.get("share_scope") or "organization").strip() or "organization",
            "original_cost": _safe_float(row.get("original_cost")),
            "estimated_current_value": _safe_float(row.get("estimated_current_value")),
        })

    return {
        "total_rows": len(rows),
        "valid_rows": len(valid_rows),
        "invalid_rows": len(rows) - len(valid_rows),
        "errors": errors,
        "preview_data": valid_rows[:5],
        "_all_valid": valid_rows,
    }


def _safe_float(raw) -> Optional[float]:
    raw = (raw or "").strip() if isinstance(raw, str) else raw
    if not raw:
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Commit validated rows to the database
# ---------------------------------------------------------------------------

def commit_import(db: Session, validated_data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert validated rows inside a transaction.

    If any row fails, the entire batch is rolled back and the error is
    reported so the caller can fix the CSV and retry.
    """
    rows = validated_data.get("_all_valid", [])
    if not rows:
        return {"created": 0, "skipped": 0, "errors": ["No valid rows to import"]}

    created = 0
    skipped = 0
    batch_errors: List[str] = []

    try:
        for row in rows:
            # Duplicate check
            existing = (
                db.query(Resource)
                .filter(
                    Resource.resource_id == row["resource_id"],
                    Resource.organization_id == row["organization_id"],
                )
                .first()
            )
            if existing:
                skipped += 1
                continue

            # Convert ISO date strings back to datetime (JSON storage loses type)
            pd = row.get("purchase_date")
            if isinstance(pd, str) and pd:
                try:
                    row["purchase_date"] = datetime.fromisoformat(pd)
                except (ValueError, TypeError):
                    row["purchase_date"] = None

            db.add(Resource(**row))
            created += 1

        db.commit()

    except IntegrityError as exc:
        db.rollback()
        msg = str(exc.orig) if exc.orig else str(exc)
        batch_errors.append(f"Database integrity error — rolled back entire import: {msg}")
        created = 0

    except Exception as exc:
        db.rollback()
        batch_errors.append(f"Unexpected error — rolled back entire import: {exc}")
        created = 0

    return {
        "created": created,
        "skipped": skipped,
        "errors": batch_errors,
    }
