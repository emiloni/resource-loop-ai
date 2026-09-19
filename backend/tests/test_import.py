"""Tests for the CSV import / ingestion service."""
import sys
import os
import json
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base
from app.models.organization import Organization
from app.models.department import Department
from app.models.resource import Resource
from app.services.ingestion_service import (
    validate_and_normalize,
    commit_import,
    parse_csv,
    _parse_utilization,
    _parse_remaining_life_months,
)

# Use a dedicated in-memory SQLite database for tests — no shared state
TEST_ENGINE = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=TEST_ENGINE)


class TestImport(unittest.TestCase):
    """Test CSV import against a fresh in-memory SQLite database."""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=TEST_ENGINE)

    def setUp(self):
        self.db = TestSession()
        # Seed an ITER org + CSE Department
        org = Organization(name="ITER", code="ITER")
        self.db.add(org)
        self.db.flush()
        dept = Department(organization_id=org.id, name="CSE Department", code="CSE")
        self.db.add(dept)
        self.db.flush()
        self.org_id = org.id
        self.dept_id = dept.id

    def tearDown(self):
        self.db.rollback()
        self.db.query(Resource).delete()
        self.db.query(Department).delete()
        self.db.query(Organization).delete()
        self.db.commit()
        self.db.close()

    # ------------------------------------------------------------------
    # a) Valid organization + department → resolves to correct IDs
    # ------------------------------------------------------------------
    def test_valid_org_and_dept(self):
        rows = [
            {"resource_id": "T001", "category": "Electronics", "type": "PC",
             "name": "Test PC", "organization": "ITER", "department": "CSE Department"},
        ]
        result = validate_and_normalize(rows, list(rows[0].keys()), self.db)
        self.assertEqual(result["valid_rows"], 1, f"Errors: {result['errors']}")
        self.assertEqual(result["invalid_rows"], 0)
        vr = result["_all_valid"][0]
        self.assertEqual(vr["organization_id"], self.org_id)
        self.assertEqual(vr["department_id"], self.dept_id)

    # ------------------------------------------------------------------
    # b) Missing organization → creates it
    # ------------------------------------------------------------------
    def test_missing_org_creates_it(self):
        rows = [
            {"resource_id": "T002", "category": "Electronics", "type": "PC",
             "name": "Test PC", "organization": "NewOrg", "department": "NewDept"},
        ]
        result = validate_and_normalize(rows, list(rows[0].keys()), self.db)
        self.assertEqual(result["valid_rows"], 1, f"Errors: {result['errors']}")
        vr = result["_all_valid"][0]
        new_org = self.db.query(Organization).filter(Organization.id == vr["organization_id"]).first()
        self.assertIsNotNone(new_org)
        self.assertEqual(new_org.name, "NewOrg")

    # ------------------------------------------------------------------
    # c) Missing department → creates it under the correct org
    # ------------------------------------------------------------------
    def test_missing_dept_creates_it(self):
        rows = [
            {"resource_id": "T003", "category": "Electronics", "type": "PC",
             "name": "Test PC", "organization": "ITER", "department": "Physics Lab"},
        ]
        result = validate_and_normalize(rows, list(rows[0].keys()), self.db)
        self.assertEqual(result["valid_rows"], 1, f"Errors: {result['errors']}")
        vr = result["_all_valid"][0]
        new_dept = self.db.query(Department).filter(Department.id == vr["department_id"]).first()
        self.assertIsNotNone(new_dept)
        self.assertEqual(new_dept.name, "Physics Lab")
        self.assertEqual(new_dept.organization_id, self.org_id)

    # ------------------------------------------------------------------
    # d) Blank owner_id → owner_id is None, no FK error
    # ------------------------------------------------------------------
    def test_blank_owner_id(self):
        rows = [
            {"resource_id": "T004", "category": "Electronics", "type": "PC",
             "name": "Test PC", "organization": "ITER", "department": "CSE Department",
             "owner_id": ""},
        ]
        result = validate_and_normalize(rows, list(rows[0].keys()), self.db)
        self.assertEqual(result["valid_rows"], 1, f"Errors: {result['errors']}")
        self.assertIsNone(result["_all_valid"][0]["owner_id"])

        commit = commit_import(self.db, result)
        self.assertEqual(commit["created"], 1, f"Commit errors: {commit.get('errors')}")
        self.assertEqual(len(commit.get("errors", [])), 0)

    # ------------------------------------------------------------------
    # e) Invalid specifications JSON → row rejected with clear error
    # ------------------------------------------------------------------
    def test_invalid_specs_json(self):
        rows = [
            {"resource_id": "T005", "category": "Electronics", "type": "PC",
             "name": "Test PC", "organization": "ITER", "department": "CSE Department",
             "specifications": "not valid json {{{"},
        ]
        result = validate_and_normalize(rows, list(rows[0].keys()), self.db)
        self.assertEqual(result["valid_rows"], 0)
        self.assertEqual(result["invalid_rows"], 1)
        error_str = json.dumps(result["errors"])
        self.assertIn("specifications", error_str.lower())

    # ------------------------------------------------------------------
    # Utilization text parsing
    # ------------------------------------------------------------------
    def test_utilization_text_parsing(self):
        self.assertEqual(_parse_utilization("Underutilized"), 20)
        self.assertEqual(_parse_utilization("Unused"), 0)
        self.assertEqual(_parse_utilization("Fully Utilized"), 100)
        self.assertEqual(_parse_utilization("High"), 80)
        self.assertEqual(_parse_utilization("50"), 50)
        self.assertEqual(_parse_utilization(""), 0)

    # ------------------------------------------------------------------
    # Remaining life years → months
    # ------------------------------------------------------------------
    def test_remaining_life_years_to_months(self):
        self.assertEqual(_parse_remaining_life_months("3"), 36)
        self.assertEqual(_parse_remaining_life_months("0.5"), 6)
        self.assertEqual(_parse_remaining_life_months("24"), 24)
        self.assertEqual(_parse_remaining_life_months(""), 36)

    # ------------------------------------------------------------------
    # Duplicate resource_id skipped
    # ------------------------------------------------------------------
    def test_duplicate_resource_skipped(self):
        rows = [
            {"resource_id": "T006", "category": "Electronics", "type": "PC",
             "name": "First", "organization": "ITER", "department": "CSE Department"},
            {"resource_id": "T006", "category": "Electronics", "type": "PC",
             "name": "Duplicate", "organization": "ITER", "department": "CSE Department"},
        ]
        result = validate_and_normalize(rows, list(rows[0].keys()), self.db)
        self.assertEqual(result["valid_rows"], 2)
        commit = commit_import(self.db, result)
        self.assertEqual(commit["created"], 1)
        self.assertEqual(commit["skipped"], 1)

    # ------------------------------------------------------------------
    # Full end-to-end: parse CSV → validate → commit
    # ------------------------------------------------------------------
    def test_full_csv_roundtrip(self):
        csv_text = (
            "resource_id,category,type,name,organization,department,utilization,remaining_useful_life_years\n"
            "E001,Electronics,PC,End-to-End PC,ITER,CSE Department,Underutilized,2\n"
        )
        rows, headers = parse_csv(csv_text.encode("utf-8"))
        self.assertEqual(len(rows), 1)
        result = validate_and_normalize(rows, headers, self.db)
        self.assertEqual(result["valid_rows"], 1, f"Errors: {result['errors']}")
        vr = result["_all_valid"][0]
        self.assertEqual(vr["utilization"], 20)
        self.assertEqual(vr["remaining_useful_life_months"], 24)

        commit = commit_import(self.db, result)
        self.assertEqual(commit["created"], 1)
        self.assertEqual(len(commit.get("errors", [])), 0)


if __name__ == "__main__":
    unittest.main()
