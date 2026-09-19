"""Resource matching routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.matching import RequirementInput
from app.services.matching_service import parse_natural_language_requirements, match_resources, build_optimal_combination

router = APIRouter()


@router.post("/parse")
def parse_requirements(input: RequirementInput, db: Session = Depends(get_db)):
    return parse_natural_language_requirements(input.raw_query)


@router.post("/search")
def search_resources(input: RequirementInput, db: Session = Depends(get_db)):
    parsed = parse_natural_language_requirements(input.raw_query)
    matches = match_resources(db=db, requirements=parsed, organization_id=input.organization_id or 1, department_id=input.department_id)
    combination = build_optimal_combination(matches, parsed["quantity"])
    total = len(matches)
    if total >= parsed["quantity"]:
        msg = f"Found {total} potentially compatible {parsed['type']}(s). All {parsed['quantity']} required items can be sourced from existing resources. Potential purchase avoided."
    elif total > 0:
        msg = f"Found {total} potentially compatible {parsed['type']}(s). {parsed['quantity'] - total} additional items may need to be sourced externally."
    else:
        msg = f"No compatible {parsed['type']}(s) found matching your requirements."
    return {"parsed_requirements": {"category": parsed["category"], "type": parsed["type"], "quantity": parsed["quantity"],
                                     "specifications": parsed["specifications"], "raw_query": parsed["raw_query"]},
            "total_compatible": total, "recommended_combination": combination,
            "individual_matches": matches, "message": msg}
