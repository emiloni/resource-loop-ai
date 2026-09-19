"""Resource Matching Engine Service."""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.resource import Resource
from app.models.department import Department

DEFAULT_WEIGHTS = {
    "technical_compatibility": 0.40,
    "condition": 0.20,
    "availability": 0.15,
    "underutilization": 0.10,
    "logistics": 0.10,
    "remaining_life": 0.05,
}


def parse_natural_language_requirements(text: str) -> Dict[str, Any]:
    """Parse natural language into structured requirements."""
    import re
    text_lower = text.lower()
    result = {"category": "Electronics", "type": "Computer", "quantity": 1, "specifications": {}, "raw_query": text}

    category_keywords = {
        "Computer": ("Electronics", "Computer"), "Laptop": ("Electronics", "Laptop"),
        "Monitor": ("Electronics", "Monitor"), "Projector": ("Electronics", "Projector"),
        "Printer": ("Electronics", "Printer"), "Chair": ("Furniture", "Chair"),
        "Desk": ("Furniture", "Desk"), "Server": ("Electronics", "Server"),
    }
    for keyword, (cat, typ) in category_keywords.items():
        if keyword.lower() in text_lower:
            result["category"], result["type"] = cat, typ
            break

    for pattern in [r"(\d+)\s*(?:computers?|laptops?|monitors?|chairs?|desks?|units?)", r"need\s+(\d+)", r"require\s+(\d+)"]:
        match = re.search(pattern, text_lower)
        if match:
            result["quantity"] = int(match.group(1))
            break

    specs = {}
    ram_match = re.search(r"(\d+)\s*gb\s*ram", text_lower)
    if ram_match:
        specs["ram_gb"] = {"minimum": int(ram_match.group(1))}
    storage_match = re.search(r"(\d+)\s*gb\s*(?:ssd|hdd|storage)", text_lower)
    if storage_match:
        specs["storage_gb"] = {"minimum": int(storage_match.group(1))}
    for cpu in ["i3", "i5", "i7", "i9", "ryzen 3", "ryzen 5", "ryzen 7", "ryzen 9", "xeon"]:
        if cpu in text_lower:
            specs["cpu"] = {"minimum": cpu}
            break
    for gpu in ["gpu", "graphics", "nvidia", "dedicated graphics"]:
        if gpu in text_lower:
            specs["gpu"] = {"required": True}
            break
    result["specifications"] = specs
    return result


def _check_spec_compatibility(resource_specs: Dict, requirements: Dict) -> Tuple[float, List[str]]:
    if not requirements:
        return 100.0, ["No specific technical requirements"]
    reasons = []
    total_checks = 0
    passed_checks = 0

    if "ram_gb" in requirements:
        total_checks += 1
        req_min = requirements["ram_gb"].get("minimum", 0)
        import re
        res_ram = float(re.search(r"(\d+)", str(resource_specs.get("ram", "0"))).group(1)) if re.search(r"(\d+)", str(resource_specs.get("ram", "0"))) else 0
        if res_ram >= req_min:
            passed_checks += 1
            reasons.append(f"✓ Meets RAM requirement ({res_ram}GB ≥ {req_min}GB)")
        else:
            reasons.append(f"✗ RAM below requirement ({res_ram}GB < {req_min}GB)")

    if "storage_gb" in requirements:
        total_checks += 1
        req_min = requirements["storage_gb"].get("minimum", 0)
        import re
        storage_str = str(resource_specs.get("storage", "0"))
        m = re.search(r"(\d+)", storage_str)
        res_storage = float(m.group(1)) if m else 0
        if "tb" in storage_str.lower():
            res_storage *= 1024
        if res_storage >= req_min:
            passed_checks += 1
            reasons.append(f"✓ Meets storage requirement ({res_storage}GB ≥ {req_min}GB)")
        else:
            reasons.append(f"✗ Storage below requirement ({res_storage}GB < {req_min}GB)")

    if "cpu" in requirements:
        total_checks += 1
        req_cpu = requirements["cpu"].get("minimum", "").lower()
        res_cpu = resource_specs.get("cpu", "").lower()
        hierarchy = {"i3": 1, "i5": 2, "i7": 3, "i9": 4, "ryzen 3": 1, "ryzen 5": 2, "ryzen 7": 3, "ryzen 9": 4, "xeon": 3}
        actual_level = max((v for k, v in hierarchy.items() if k in res_cpu), default=0)
        required_level = max((v for k, v in hierarchy.items() if k in req_cpu), default=0)
        if required_level == 0 or actual_level >= required_level:
            passed_checks += 1
            reasons.append(f"✓ Meets CPU requirement ({resource_specs.get('cpu', 'N/A')})")
        else:
            reasons.append(f"✗ CPU may not meet requirement ({resource_specs.get('cpu', 'N/A')})")

    if "gpu" in requirements:
        total_checks += 1
        res_gpu = resource_specs.get("gpu", "")
        if requirements["gpu"].get("required") and res_gpu and res_gpu.lower() not in ("none", "integrated", ""):
            passed_checks += 1
            reasons.append(f"✓ Dedicated GPU available ({res_gpu})")
        elif not requirements["gpu"].get("required"):
            passed_checks += 1
            reasons.append("✓ GPU not strictly required")
        else:
            reasons.append("✗ No dedicated GPU detected")

    return (passed_checks / total_checks * 100 if total_checks else 100.0), reasons


def _condition_score(c):
    return {"excellent": 100, "good": 80, "fair": 55, "poor": 30, "non-functional": 0}.get(c.lower(), 50) if c else 50

def _availability_score(a):
    return {"available": 100, "underutilized": 90, "in_use": 30, "reserved": 10, "maintenance": 0}.get(a.lower(), 50) if a else 50

def _underutilization_score(u):
    if u is None: return 50
    if u < 20: return 100
    if u < 50: return 75
    if u < 80: return 40
    return 10

def _remaining_life_score(m):
    if m is None: return 50
    if m >= 36: return 100
    if m >= 24: return 80
    if m >= 12: return 50
    return 25


def match_resources(db: Session, requirements: Dict, organization_id: int = 1, department_id=None, weights=None):
    if weights is None:
        weights = DEFAULT_WEIGHTS

    query = db.query(Resource).filter(
        Resource.organization_id == organization_id,
        Resource.status == "active",
        Resource.availability.in_(["available", "underutilized", "in_use"]),
    )
    if requirements.get("category"):
        query = query.filter(Resource.category == requirements["category"])
    if requirements.get("type"):
        query = query.filter(Resource.type == requirements["type"])

    resources = query.all()
    matches = []

    for resource in resources:
        if resource.share_scope == "private" and resource.department_id != department_id:
            continue

        tech_score, tech_reasons = _check_spec_compatibility(resource.specifications or {}, requirements.get("specifications", {}))
        cond_score = _condition_score(resource.condition)
        avail_score = _availability_score(resource.availability)
        underutil_score = _underutilization_score(resource.utilization)
        life_score = _remaining_life_score(resource.remaining_useful_life_months)
        logistics_s = 100 if department_id and resource.department_id == department_id else 70

        if tech_score < 50:
            continue

        overall = (tech_score * weights["technical_compatibility"] + cond_score * weights["condition"] +
                   avail_score * weights["availability"] + underutil_score * weights["underutilization"] +
                   logistics_s * weights["logistics"] + life_score * weights["remaining_life"])

        explanation_parts = []
        if underutil_score >= 75: explanation_parts.append("Currently underutilized")
        if cond_score >= 80: explanation_parts.append("Good condition")
        if avail_score >= 80: explanation_parts.append("Available for reallocation")

        explanation = "Recommended because: " + "; ".join(tech_reasons)
        if explanation_parts:
            explanation += ". Also: " + "; ".join(explanation_parts)

        dept = db.query(Department).filter(Department.id == resource.department_id).first()
        matches.append({
            "resource_id": resource.id, "resource_name": resource.name, "resource_code": resource.resource_id,
            "category": resource.category, "type": resource.type,
            "department_name": dept.name if dept else "Unknown", "location": resource.location,
            "condition": resource.condition, "utilization": resource.utilization or 0,
            "remaining_life_months": resource.remaining_useful_life_months or 0, "availability": resource.availability,
            "compatibility_score": round(tech_score, 1), "overall_score": round(overall, 1),
            "explanation": explanation,
            "match_details": {"technical_compatibility": round(tech_score, 1), "condition": round(cond_score, 1),
                              "availability": round(avail_score, 1), "underutilization": round(underutil_score, 1),
                              "logistics": round(logistics_s, 1), "remaining_life": round(life_score, 1),
                              "technical_reasons": tech_reasons},
        })

    matches.sort(key=lambda x: x["overall_score"], reverse=True)
    return matches


def build_optimal_combination(matches, required_quantity):
    if not matches:
        return {"sources": [], "total_quantity": 0, "combined_score": 0, "explanation": "No compatible resources found."}
    selected, remaining = [], required_quantity
    total_score = 0
    for m in matches:
        if remaining <= 0: break
        selected.append(m)
        remaining -= 1
        total_score += m["overall_score"]
    combined_score = total_score / len(selected) if selected else 0
    if remaining > 0:
        explanation = f"Found {len(selected)} of {required_quantity} required. {remaining} additional needed externally."
    else:
        depts = set(s["department_name"] for s in selected)
        explanation = f"All {required_quantity} resources found across {len(depts)} department(s): {', '.join(depts)}."
    return {"sources": selected, "total_quantity": len(selected), "combined_score": round(combined_score, 1), "explanation": explanation}
