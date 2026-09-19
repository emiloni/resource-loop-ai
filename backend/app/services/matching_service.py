"""Resource Matching Engine Service."""

from typing import Dict, Any, List, Tuple
import re

from sqlalchemy.orm import Session

from app.models.resource import Resource
from app.models.department import Department


# ============================================================
# MATCHING WEIGHTS
# ============================================================

DEFAULT_WEIGHTS = {
    "technical_compatibility": 0.40,
    "condition": 0.20,
    "availability": 0.15,
    "underutilization": 0.10,
    "logistics": 0.10,
    "remaining_life": 0.05,
}


# ============================================================
# NATURAL LANGUAGE REQUIREMENT PARSER
# ============================================================

def parse_natural_language_requirements(
    text: str,
) -> Dict[str, Any]:
    """
    Convert a natural-language resource request into
    structured requirements.

    Examples:

        "computer"
        -> Computer / Computer

        "laptop"
        -> Computer / Laptop

        "desktop computer"
        -> Computer / Desktop Computer

        "I need 5 laptops with 16GB RAM"
        -> Computer / Laptop
        -> quantity = 5
        -> RAM >= 16GB
    """

    text = text or ""
    text_lower = text.lower().strip()

    result = {
        "category": None,
        "type": None,
        "quantity": 1,
        "specifications": {},
        "raw_query": text,
    }

    # --------------------------------------------------------
    # CATEGORY / TYPE DETECTION
    # --------------------------------------------------------

    # IMPORTANT:
    # More specific terms must appear BEFORE generic terms.
    # Otherwise "desktop computer" could match "computer" first.

    category_keywords = [
        # Computers
        ("laptop", "Computer", "Laptop"),
        ("notebook", "Computer", "Laptop"),
        ("desktop computer", "Computer", "Desktop Computer"),
        ("desktop pc", "Computer", "Desktop Computer"),
        ("desktop", "Computer", "Desktop Computer"),
        ("computer", "Computer", "Computer"),
        ("computers", "Computer", "Computer"),

        # Electronics
        ("monitor", "Electronics", "Monitor"),
        ("display", "Electronics", "Monitor"),
        ("projector", "Electronics", "Projector"),
        ("printer", "Electronics", "Printer"),
        ("scanner", "Electronics", "Scanner"),
        ("server", "Electronics", "Server"),

        # Networking
        ("router", "Networking", "Router"),
        ("switch", "Networking", "Switch"),

        # Furniture
        ("office chair", "Furniture", "Office Chair"),
        ("visitor chair", "Furniture", "Visitor Chair"),
        ("chair", "Furniture", "Chair"),
        ("study desk", "Furniture", "Study Desk"),
        ("work desk", "Furniture", "Desk"),
        ("desk", "Furniture", "Desk"),
        ("table", "Furniture", "Table"),
    ]

    for keyword, category, resource_type in category_keywords:

        if keyword in text_lower:
            result["category"] = category
            result["type"] = resource_type
            break

    # --------------------------------------------------------
    # QUANTITY
    # --------------------------------------------------------

    quantity_patterns = [
        r"(\d+)\s*(?:computers?|laptops?|notebooks?|monitors?|chairs?|desks?|tables?|projectors?|printers?|routers?|servers?|units?)",
        r"need\s+(\d+)",
        r"require\s+(\d+)",
        r"want\s+(\d+)",
        r"looking\s+for\s+(\d+)",
    ]

    for pattern in quantity_patterns:

        match = re.search(
            pattern,
            text_lower,
        )

        if match:
            result["quantity"] = int(
                match.group(1)
            )
            break

    # --------------------------------------------------------
    # TECHNICAL SPECIFICATIONS
    # --------------------------------------------------------

    specs = {}

    # RAM
    ram_match = re.search(
        r"(\d+)\s*gb\s*(?:of\s*)?ram",
        text_lower,
    )

    if ram_match:

        specs["ram_gb"] = {
            "minimum": int(
                ram_match.group(1)
            )
        }

    # Storage
    storage_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(gb|tb)\s*(?:ssd|hdd|storage)",
        text_lower,
    )

    if storage_match:

        value = float(
            storage_match.group(1)
        )

        unit = storage_match.group(2).lower()

        if unit == "tb":
            value *= 1024

        specs["storage_gb"] = {
            "minimum": int(value)
        }

    # CPU
    cpu_options = [
        "ryzen 9",
        "ryzen 7",
        "ryzen 5",
        "ryzen 3",
        "core i9",
        "core i7",
        "core i5",
        "core i3",
        "i9",
        "i7",
        "i5",
        "i3",
        "xeon",
    ]

    for cpu in cpu_options:

        if cpu in text_lower:

            specs["cpu"] = {
                "minimum": cpu
            }

            break

    # GPU
    gpu_keywords = [
        "dedicated gpu",
        "dedicated graphics",
        "nvidia",
        "amd gpu",
        "graphics card",
        "gpu",
    ]

    for gpu_keyword in gpu_keywords:

        if gpu_keyword in text_lower:

            specs["gpu"] = {
                "required": True
            }

            break

    result["specifications"] = specs

    return result


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def _normalize(value: Any) -> str:

    return str(
        value or ""
    ).strip().lower()


# ============================================================
# RESOURCE TYPE MATCHING
# ============================================================

def _resource_matches_requested_type(
    resource: Resource,
    requested_category: str,
    requested_type: str,
) -> bool:
    """
    Flexible category/type matching.

    This intentionally does NOT require an exact database
    category/type combination.

    Example:

        Requested:
            category = Computer
            type = Computer

        Database:
            category = Computer
            type = Laptop

        Result:
            MATCH
    """

    db_category = _normalize(
        resource.category
    )

    db_type = _normalize(
        resource.type
    )

    db_name = _normalize(
        resource.name
    )

    # No category/type requirement
    if (
        not requested_category
        and not requested_type
    ):
        return True

    # Exact type match
    if (
        requested_type
        and requested_type == db_type
    ):
        return True

    # --------------------------------------------------------
    # LAPTOP
    # --------------------------------------------------------

    if requested_type in {
        "laptop",
        "notebook",
    }:

        return (
            db_type in {
                "laptop",
                "notebook",
            }
            or "laptop" in db_name
            or "notebook" in db_name
        )

    # --------------------------------------------------------
    # DESKTOP
    # --------------------------------------------------------

    if requested_type in {
        "desktop",
        "desktop computer",
        "desktop pc",
    }:

        return (
            db_type in {
                "desktop",
                "desktop computer",
                "desktop pc",
            }
            or "desktop" in db_type
            or "desktop" in db_name
        )

    # --------------------------------------------------------
    # GENERIC COMPUTER
    # --------------------------------------------------------

    if requested_type in {
        "computer",
        "computers",
    }:

        return (
            db_category == "computer"
            or db_type in {
                "computer",
                "computers",
                "laptop",
                "notebook",
                "desktop",
                "desktop computer",
                "desktop pc",
            }
            or "computer" in db_name
            or "laptop" in db_name
            or "desktop" in db_name
        )

    # --------------------------------------------------------
    # MONITOR
    # --------------------------------------------------------

    if requested_type in {
        "monitor",
        "display",
    }:

        return (
            db_type in {
                "monitor",
                "display",
            }
            or "monitor" in db_name
            or "display" in db_name
        )

    # --------------------------------------------------------
    # CHAIRS
    # --------------------------------------------------------

    if requested_type in {
        "chair",
        "office chair",
        "visitor chair",
    }:

        return (
            "chair" in db_type
            or "chair" in db_name
        )

    # --------------------------------------------------------
    # DESKS
    # --------------------------------------------------------

    if requested_type in {
        "desk",
        "study desk",
        "work desk",
    }:

        return (
            "desk" in db_type
            or "desk" in db_name
        )

    # --------------------------------------------------------
    # GENERIC TYPE MATCH
    # --------------------------------------------------------

    if requested_type:

        if requested_type in db_type:
            return True

        if requested_type in db_name:
            return True

    # --------------------------------------------------------
    # CATEGORY MATCH
    # --------------------------------------------------------

    if requested_category:

        if db_category == requested_category:
            return True

        if requested_category in db_category:
            return True

        if requested_category in db_type:
            return True

        if requested_category in db_name:
            return True

    return False


# ============================================================
# TECHNICAL COMPATIBILITY
# ============================================================

def _check_spec_compatibility(
    resource_specs: Dict,
    requirements: Dict,
) -> Tuple[float, List[str]]:
    """
    Compare resource specifications against requested
    technical specifications.
    """

    if not requirements:

        return (
            100.0,
            ["No specific technical requirements"],
        )

    resource_specs = resource_specs or {}
    requirements = requirements or {}

    reasons = []

    total_checks = 0
    passed_checks = 0

    # --------------------------------------------------------
    # RAM
    # --------------------------------------------------------

    if "ram_gb" in requirements:

        total_checks += 1

        req_min = requirements[
            "ram_gb"
        ].get(
            "minimum",
            0,
        )

        ram_text = str(
            resource_specs.get(
                "ram",
                "0",
            )
        )

        ram_match = re.search(
            r"(\d+(?:\.\d+)?)",
            ram_text,
        )

        res_ram = (
            float(ram_match.group(1))
            if ram_match
            else 0
        )

        if res_ram >= req_min:

            passed_checks += 1

            reasons.append(
                f"✓ Meets RAM requirement "
                f"({res_ram:g}GB ≥ {req_min}GB)"
            )

        else:

            reasons.append(
                f"✗ RAM below requirement "
                f"({res_ram:g}GB < {req_min}GB)"
            )

    # --------------------------------------------------------
    # STORAGE
    # --------------------------------------------------------

    if "storage_gb" in requirements:

        total_checks += 1

        req_min = requirements[
            "storage_gb"
        ].get(
            "minimum",
            0,
        )

        storage_text = str(
            resource_specs.get(
                "storage",
                "0",
            )
        )

        storage_match = re.search(
            r"(\d+(?:\.\d+)?)",
            storage_text,
        )

        res_storage = (
            float(storage_match.group(1))
            if storage_match
            else 0
        )

        if "tb" in storage_text.lower():

            res_storage *= 1024

        if res_storage >= req_min:

            passed_checks += 1

            reasons.append(
                f"✓ Meets storage requirement "
                f"({res_storage:g}GB ≥ {req_min}GB)"
            )

        else:

            reasons.append(
                f"✗ Storage below requirement "
                f"({res_storage:g}GB < {req_min}GB)"
            )

    # --------------------------------------------------------
    # CPU
    # --------------------------------------------------------

    if "cpu" in requirements:

        total_checks += 1

        req_cpu = _normalize(
            requirements[
                "cpu"
            ].get(
                "minimum",
                "",
            )
        )

        res_cpu = _normalize(
            resource_specs.get(
                "cpu",
                "",
            )
        )

        hierarchy = {
            "i3": 1,
            "core i3": 1,
            "i5": 2,
            "core i5": 2,
            "i7": 3,
            "core i7": 3,
            "i9": 4,
            "core i9": 4,

            "ryzen 3": 1,
            "ryzen 5": 2,
            "ryzen 7": 3,
            "ryzen 9": 4,

            "xeon": 3,
        }

        actual_level = max(
            (
                level
                for cpu_name, level
                in hierarchy.items()
                if cpu_name in res_cpu
            ),
            default=0,
        )

        required_level = max(
            (
                level
                for cpu_name, level
                in hierarchy.items()
                if cpu_name in req_cpu
            ),
            default=0,
        )

        if (
            required_level == 0
            or actual_level >= required_level
        ):

            passed_checks += 1

            reasons.append(
                "✓ Meets CPU requirement "
                f"({resource_specs.get('cpu', 'N/A')})"
            )

        else:

            reasons.append(
                "✗ CPU may not meet requirement "
                f"({resource_specs.get('cpu', 'N/A')})"
            )

    # --------------------------------------------------------
    # GPU
    # --------------------------------------------------------

    if "gpu" in requirements:

        total_checks += 1

        gpu_required = requirements[
            "gpu"
        ].get(
            "required",
            False,
        )

        res_gpu = str(
            resource_specs.get(
                "gpu",
                "",
            )
        ).strip()

        if not gpu_required:

            passed_checks += 1

            reasons.append(
                "✓ GPU not strictly required"
            )

        elif res_gpu and res_gpu.lower() not in {
            "none",
            "integrated",
            "integrated graphics",
            "",
        }:

            passed_checks += 1

            reasons.append(
                "✓ Dedicated GPU available "
                f"({res_gpu})"
            )

        else:

            reasons.append(
                "✗ No dedicated GPU detected"
            )

    # --------------------------------------------------------
    # FINAL TECHNICAL SCORE
    # --------------------------------------------------------

    if total_checks == 0:

        return (
            100.0,
            ["No specific technical requirements"],
        )

    score = (
        passed_checks
        / total_checks
        * 100
    )

    return (
        score,
        reasons,
    )


# ============================================================
# CONDITION SCORE
# ============================================================

def _condition_score(
    condition,
):

    if not condition:
        return 50

    return {
        "excellent": 100,
        "good": 80,
        "fair": 55,
        "poor": 30,
        "non-functional": 0,
    }.get(
        _normalize(condition),
        50,
    )


# ============================================================
# AVAILABILITY SCORE
# ============================================================

def _availability_score(
    availability,
):

    if not availability:
        return 50

    return {
        "available": 100,
        "underutilized": 90,
        "in_use": 30,
        "reserved": 10,
        "maintenance": 0,
    }.get(
        _normalize(availability),
        50,
    )


# ============================================================
# UNDERUTILIZATION SCORE
# ============================================================

def _underutilization_score(
    utilization,
):

    if utilization is None:
        return 50

    if utilization < 20:
        return 100

    if utilization < 50:
        return 75

    if utilization < 80:
        return 40

    return 10


# ============================================================
# REMAINING LIFE SCORE
# ============================================================

def _remaining_life_score(
    months,
):

    if months is None:
        return 50

    if months >= 36:
        return 100

    if months >= 24:
        return 80

    if months >= 12:
        return 50

    return 25


# ============================================================
# MAIN MATCHING FUNCTION
# ============================================================

def match_resources(
    db: Session,
    requirements: Dict,
    organization_id: int = 1,
    department_id=None,
    weights=None,
):
    """
    Find and rank resources matching the user's requirements.
    """

    if weights is None:
        weights = DEFAULT_WEIGHTS

    # --------------------------------------------------------
    # DATABASE FILTER
    # --------------------------------------------------------
    #
    # Keep the DB filter broad.
    #
    # We intentionally DO NOT filter category/type here,
    # because Computer -> Laptop/Desktop needs flexible
    # matching.
    #

    query = db.query(Resource).filter(
        Resource.organization_id
        == organization_id,

        Resource.status
        == "active",

        Resource.availability.in_(
            [
                "available",
                "underutilized",
                "in_use",
            ]
        ),
    )

    resources = query.all()

    # --------------------------------------------------------
    # DEBUG INFORMATION
    # --------------------------------------------------------

    print(
        "\n========== MATCHING DEBUG =========="
    )

    print(
        "Organization ID:",
        organization_id,
    )

    print(
        "Requested requirements:",
        requirements,
    )

    print(
        "Total resources after DB filter:",
        len(resources),
    )

    for resource in resources:

        print(
            "RESOURCE:",
            resource.resource_id,
            "| name:",
            resource.name,
            "| category:",
            resource.category,
            "| type:",
            resource.type,
            "| status:",
            resource.status,
            "| availability:",
            resource.availability,
            "| org:",
            resource.organization_id,
        )

    print(
        "====================================\n"
    )

    # --------------------------------------------------------
    # REQUESTED CATEGORY / TYPE
    # --------------------------------------------------------

    requested_category = _normalize(
        requirements.get(
            "category"
        )
    )

    requested_type = _normalize(
        requirements.get(
            "type"
        )
    )

    # --------------------------------------------------------
    # FLEXIBLE CATEGORY / TYPE FILTER
    # --------------------------------------------------------

    resources = [
        resource

        for resource in resources

        if _resource_matches_requested_type(
            resource,
            requested_category,
            requested_type,
        )
    ]

    print(
        "Resources after category/type matching:",
        len(resources),
    )

    # --------------------------------------------------------
    # BUILD MATCH RESULTS
    # --------------------------------------------------------

    matches = []

    for resource in resources:

        # ----------------------------------------------------
        # PRIVATE RESOURCE VISIBILITY
        # ----------------------------------------------------

        if (
            resource.share_scope
            == "private"

            and resource.department_id
            != department_id
        ):
            continue

        # ----------------------------------------------------
        # TECHNICAL COMPATIBILITY
        # ----------------------------------------------------

        tech_score, tech_reasons = (
            _check_spec_compatibility(
                resource.specifications or {},
                requirements.get(
                    "specifications",
                    {},
                ),
            )
        )

        # ----------------------------------------------------
        # TECHNICAL REJECTION
        # ----------------------------------------------------

        if tech_score < 50:

            print(
                "REJECTED TECHNICALLY:",
                resource.resource_id,
                tech_score,
            )

            continue

        # ----------------------------------------------------
        # OTHER SCORES
        # ----------------------------------------------------

        cond_score = _condition_score(
            resource.condition
        )

        avail_score = _availability_score(
            resource.availability
        )

        underutil_score = (
            _underutilization_score(
                resource.utilization
            )
        )

        life_score = _remaining_life_score(
            resource.remaining_useful_life_months
        )

        # ----------------------------------------------------
        # LOGISTICS SCORE
        # ----------------------------------------------------

        logistics_score = (
            100
            if (
                department_id
                and resource.department_id
                == department_id
            )
            else 70
        )

        # ----------------------------------------------------
        # OVERALL SCORE
        # ----------------------------------------------------

        overall = (
            tech_score
            * weights[
                "technical_compatibility"
            ]

            + cond_score
            * weights["condition"]

            + avail_score
            * weights["availability"]

            + underutil_score
            * weights["underutilization"]

            + logistics_score
            * weights["logistics"]

            + life_score
            * weights["remaining_life"]
        )

        # ----------------------------------------------------
        # EXPLANATION
        # ----------------------------------------------------

        explanation_parts = []

        if underutil_score >= 75:

            explanation_parts.append(
                "Currently underutilized"
            )

        if cond_score >= 80:

            explanation_parts.append(
                "Good condition"
            )

        if avail_score >= 80:

            explanation_parts.append(
                "Available for reallocation"
            )

        explanation = (
            "Recommended because: "
            + "; ".join(
                tech_reasons
            )
        )

        if explanation_parts:

            explanation += (
                ". Also: "
                + "; ".join(
                    explanation_parts
                )
            )

        # ----------------------------------------------------
        # DEPARTMENT
        # ----------------------------------------------------

        dept = (
            db.query(Department)
            .filter(
                Department.id
                == resource.department_id
            )
            .first()
        )

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        matches.append(
            {
                "resource_id": resource.id,

                "resource_name": resource.name,

                "resource_code": resource.resource_id,

                "category": resource.category,

                "type": resource.type,

                "department_name": (
                    dept.name
                    if dept
                    else "Unknown"
                ),

                "location": resource.location,

                "condition": resource.condition,

                "utilization": (
                    resource.utilization
                    or 0
                ),

                "remaining_life_months": (
                    resource.remaining_useful_life_months
                    or 0
                ),

                "availability": (
                    resource.availability
                ),

                "compatibility_score": round(
                    tech_score,
                    1,
                ),

                "overall_score": round(
                    overall,
                    1,
                ),

                "explanation": explanation,

                "match_details": {
                    "technical_compatibility": round(
                        tech_score,
                        1,
                    ),

                    "condition": round(
                        cond_score,
                        1,
                    ),

                    "availability": round(
                        avail_score,
                        1,
                    ),

                    "underutilization": round(
                        underutil_score,
                        1,
                    ),

                    "logistics": round(
                        logistics_score,
                        1,
                    ),

                    "remaining_life": round(
                        life_score,
                        1,
                    ),

                    "technical_reasons": (
                        tech_reasons
                    ),
                },
            }
        )

    # --------------------------------------------------------
    # SORT BY OVERALL SCORE
    # --------------------------------------------------------

    matches.sort(
        key=lambda x: x["overall_score"],
        reverse=True,
    )

    print(
        "Final matches:",
        len(matches),
    )

    return matches


# ============================================================
# OPTIMAL COMBINATION
# ============================================================

def build_optimal_combination(
    matches,
    required_quantity,
):
    """
    Build a combination of matching resources
    to satisfy a requested quantity.
    """

    if not matches:

        return {
            "sources": [],

            "total_quantity": 0,

            "combined_score": 0,

            "explanation": (
                "No compatible resources found."
            ),
        }

    selected = []

    remaining = required_quantity

    total_score = 0

    # --------------------------------------------------------
    # SELECT BEST MATCHES
    # --------------------------------------------------------

    for match in matches:

        if remaining <= 0:
            break

        selected.append(
            match
        )

        remaining -= 1

        total_score += (
            match["overall_score"]
        )

    # --------------------------------------------------------
    # COMBINED SCORE
    # --------------------------------------------------------

    combined_score = (
        total_score
        / len(selected)
        if selected
        else 0
    )

    # --------------------------------------------------------
    # EXPLANATION
    # --------------------------------------------------------

    if remaining > 0:

        explanation = (
            f"Found {len(selected)} of "
            f"{required_quantity} required. "
            f"{remaining} additional needed "
            f"externally."
        )

    else:

        departments = set(
            resource[
                "department_name"
            ]
            for resource in selected
        )

        explanation = (
            f"All {required_quantity} "
            f"resources found across "
            f"{len(departments)} department(s): "
            f"{', '.join(departments)}."
        )

    return {
        "sources": selected,

        "total_quantity": len(
            selected
        ),

        "combined_score": round(
            combined_score,
            1,
        ),

        "explanation": explanation,
    }
