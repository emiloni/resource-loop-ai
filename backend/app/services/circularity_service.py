"""Circularity Assessment Engine — resource-specific decision logic.

Different inputs MUST produce different recommendations based on:
  category, type, condition, damage, material, repairability,
  remaining life, utilization, and structural integrity.

Key principles:
- Do NOT invent data. If unknown, say unknown.
- Suitability score = how suitable the recommended action is (NOT probability).
- why_factors must never be empty when factors exist.
- Image uploads produce real analysis, not generic defaults.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import re
from app.models.circularity import CircularityAssessment


# ── Action constants ──────────────────────────────────────────────
ACTIONS = ("reuse", "repair", "repurpose", "redistribute", "donate", "recycle", "dispose")

# ── Condition scores (0-100) ─────────────────────────────────────
CONDITION_SCORE = {
    "excellent": 95, "good": 80, "fair": 55, "poor": 25, "severely damaged": 5, "non-functional": 5,
}

# ── Repairability scores ──────────────────────────────────────────
REPAIRABILITY_SCORE = {"high": 85, "medium": 50, "low": 20}

# ── Structural integrity scores ───────────────────────────────────
INTEGRITY_SCORE = {"good": 90, "minor concerns": 65, "compromised": 25, "severely compromised": 5, "unknown": 40}


# ═══════════════════════════════════════════════════════════════════
# Image Vision Analysis
# ═══════════════════════════════════════════════════════════════════

def _analyze_image(image_data: str) -> Dict[str, Any]:
    """Analyze an image (base64 or URL) and return structured observations.

    This is a rule-based placeholder. In production, replace with a real
    vision model (e.g., OpenAI Vision, Google Cloud Vision, etc.).

    For now, we attempt basic analysis from any text context embedded
    in the image data (e.g., filename hints) and return observations
    that clearly mark confidence levels.
    """
    # Placeholder: cannot determine anything from raw image bytes
    # without a real vision model. Return structured "unknown" values
    # so the decision engine handles it correctly.
    return {
        "observed": {
            "object": None,
            "material": None,
            "condition": None,
            "damage_description": None,
            "structural_integrity": None,
        },
        "inferred": {
            "repairability": None,
        },
        "confidence": {
            "object": "low",
            "damage": "low",
            "material": "low",
            "structural_integrity": "low",
        },
        "remaining_life": None,  # Cannot determine from image alone
        "source": "image",
        "note": "Image uploaded but no vision model configured. Please describe the resource for accurate analysis.",
    }


# ═══════════════════════════════════════════════════════════════════
# Description parser — extracts features from free text
# ═══════════════════════════════════════════════════════════════════

def _assess_from_description(description: str) -> Dict[str, Any]:
    dl = description.lower()
    a: Dict[str, Any] = {
        "detected_object": "Unknown item",
        "detected_category": "Other",
        "detected_material": "Unknown",
        "detected_condition": None,  # None = not yet determined
        "detected_damage": None,
        "repairability": None,  # None = not yet determined
        "structural_integrity": None,  # None = not yet determined
        "estimated_remaining_life_months": None,  # None = unknown
        "_confidence": {},  # Per-field confidence tracking
    }

    # Object detection — order matters: more specific first
    objects = [
        ("laptop", ("Electronics", "Laptop")),
        ("desktop", ("Electronics", "Computer")),
        ("computer", ("Electronics", "Computer")),
        ("monitor", ("Electronics", "Monitor")),
        ("projector", ("Electronics", "Projector")),
        ("printer", ("Electronics", "Printer")),
        ("router", ("Electronics", "Router")),
        ("camera", ("Electronics", "Camera")),
        ("microscope", ("Laboratory Equipment", "Microscope")),
        ("centrifuge", ("Laboratory Equipment", "Centrifuge")),
        ("plastic chair", ("Furniture", "Plastic Chair")),
        ("office chair", ("Furniture", "Office Chair")),
        ("chair", ("Furniture", "Chair")),
        ("bookshelf", ("Furniture", "Bookshelf")),
        ("desk", ("Furniture", "Desk")),
        ("table", ("Furniture", "Table")),
        ("shelf", ("Furniture", "Shelf")),
    ]
    for kw, (cat, obj) in objects:
        if kw in dl:
            a["detected_category"] = cat
            a["detected_object"] = obj
            a["_confidence"]["object"] = "high"
            break
    if "object" not in a["_confidence"]:
        a["_confidence"]["object"] = "low"

    # Material detection
    materials = {"metal": "Metal", "steel": "Steel", "aluminum": "Aluminum",
                 "wood": "Wood", "plastic": "Plastic", "fabric": "Fabric",
                 "leather": "Leather", "glass": "Glass", "mesh": "Mesh"}
    detected_mat = [v for k, v in materials.items() if k in dl]
    if detected_mat:
        a["detected_material"] = " + ".join(detected_mat)
        a["_confidence"]["material"] = "high"
    else:
        a["_confidence"]["material"] = "low"

    # ── Damage detection — severity classification ────────────────
    severe_damage_keywords = {
        "non-functional": "Non-functional",
        "structural break": "Major structural break",
        "major break": "Major structural break",
        "collapsed": "Collapsed",
        "shattered": "Shattered",
        "destroyed": "Destroyed",
        "severely damaged": "Severely damaged",
        "severe damage": "Severely damaged",
        "motherboard failure": "Motherboard failure",
        "hardware failure": "Hardware failure",
        "burnt": "Burnt",
        "fried": "Electronically fried",
        "short circuit": "Short circuit",
        "dead": "Dead",
        "irreparable": "Irreparable damage",
    }
    moderate_damage_keywords = {
        "broken": "Broken",
        "crack": "Crack",
        "cracked": "Cracked",
        "dent": "Dent",
        "rust": "Rust",
        "rusted": "Rusted",
        "leak": "Leak",
        "leaking": "Leaking",
        "torn": "Torn fabric/covering",
        "faulty": "Faulty component",
        "malfunctioning": "Malfunctioning",
        "bent": "Bent",
        "split": "Split",
    }
    minor_damage_keywords = {
        "scratch": "Scratch",
        "worn": "Worn",
        "dirty": "Dirty",
        "stain": "Stain",
        "faded": "Faded",
        "cosmetic": "Cosmetic damage",
        "loose": "Loose component",
        "scuff": "Scuff mark",
    }

    severe_found = {k: v for k, v in severe_damage_keywords.items() if k in dl}
    moderate_found = {k: v for k, v in moderate_damage_keywords.items() if k in dl}
    minor_found = {k: v for k, v in minor_damage_keywords.items() if k in dl}

    all_damage = []
    if severe_found:
        all_damage.extend(severe_found.values())
    if moderate_found:
        all_damage.extend(moderate_found.values())
    if minor_found:
        all_damage.extend(minor_found.values())

    if all_damage:
        a["detected_damage"] = "; ".join(all_damage)
        a["_confidence"]["damage"] = "high" if severe_found or moderate_found else "medium"
    else:
        a["_confidence"]["damage"] = "medium"

    # ── Condition classification ───────────────────────────────────
    # Explicit condition overrides (text says it directly)
    condition_overrides = [
        (["severely damaged", "completely destroyed", "destroyed", "wrecked"], "severely damaged"),
        (["non-functional", "not working", "dead", "broken beyond repair", "irreparable"], "non-functional"),
        (["poor condition", "in poor shape", "poor"], "poor"),
        (["needs repair", "needs fixing", "needs work"], "fair"),
        (["good condition", "good shape", "working well", "functional", "decent", "operational"], "good"),
        (["excellent condition", "excellent", "pristine", "mint", "brand new", "like new", "perfect"], "excellent"),
    ]
    for keywords, cond in condition_overrides:
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', dl):
                a["detected_condition"] = cond
                a["_confidence"]["condition"] = "high"
                break
        if a["detected_condition"]:
            break

    # Infer condition from damage severity if not explicitly stated
    if a["detected_condition"] is None:
        if severe_found:
            a["detected_condition"] = "poor"
            a["_confidence"]["condition"] = "medium"
        elif moderate_found and len(moderate_found) >= 2:
            a["detected_condition"] = "fair"
            a["_confidence"]["condition"] = "medium"
        elif moderate_found:
            a["detected_condition"] = "fair"
            a["_confidence"]["condition"] = "medium"
        elif minor_found:
            a["detected_condition"] = "good"
            a["_confidence"]["condition"] = "medium"
        else:
            a["detected_condition"] = "fair"
            a["_confidence"]["condition"] = "low"

    # ── Structural integrity ───────────────────────────────────────
    integrity_keywords = {
        "compromised": ["structural break", "major break", "collapsed", "severely damaged",
                        "severe damage", "shattered", "destroyed", "bent frame", "wobbly",
                        "unstable", "large crack", "major crack"],
        "good": ["stable frame", "stable base", "solid structure", "structurally sound",
                 "sturdy", "firm", "solid"],
        "minor concerns": ["loose", "slight wobble", "minor crack", "surface wear"],
    }

    for level, keywords in integrity_keywords.items():
        for kw in keywords:
            if kw in dl:
                a["structural_integrity"] = level
                a["_confidence"]["structural_integrity"] = "high" if level in ("compromised", "good") else "medium"
                break
        if a["structural_integrity"]:
            break

    if a["structural_integrity"] is None:
        # Infer from damage severity
        if severe_found:
            a["structural_integrity"] = "compromised"
            a["_confidence"]["structural_integrity"] = "medium"
        elif moderate_found:
            a["structural_integrity"] = "minor concerns"
            a["_confidence"]["structural_integrity"] = "low"
        else:
            a["structural_integrity"] = "unknown"
            a["_confidence"]["structural_integrity"] = "low"

    # ── Repairability inference ────────────────────────────────────
    easy_repair = ["armrest", "screw", "bolt", "pad", "cushion", "wheel",
                   "caster", "hinge", "handle", "knob", "button", "key",
                   "cable", "cord", "battery", "tray", "cover", "lid",
                   "fabric", "upholstery", "seat cushion"]
    hard_repair = ["motherboard", "processor", "chip", "circuit", "lcd",
                   "screen", "hardwired", "soldered", "integrated",
                   "structural", "frame weld", "molded plastic"]

    easy_count = sum(1 for k in easy_repair if k in dl)
    hard_count = sum(1 for k in hard_repair if k in dl)

    # Also consider structural integrity for repairability
    if a["structural_integrity"] in ("compromised", "severely compromised"):
        hard_count += 2  # Structural damage makes repair harder

    if easy_count > hard_count + 1:
        a["repairability"] = "high"
    elif hard_count > easy_count:
        a["repairability"] = "low"
    else:
        a["repairability"] = "medium"

    a["_confidence"]["repairability"] = "medium"

    # ── Remaining life — DO NOT invent values ─────────────────────
    # Only set if explicitly mentioned or determinable
    life_match = re.search(r'(\d+)\s*(?:months?|mos?)\s*(?:remaining|left|useful life)', dl)
    if life_match:
        a["estimated_remaining_life_months"] = int(life_match.group(1))
    else:
        a["estimated_remaining_life_months"] = None  # Unknown

    return a


# ═══════════════════════════════════════════════════════════════════
# Resource-specific decision engine
# ═══════════════════════════════════════════════════════════════════

def _decide_recommendations(a: Dict[str, Any]) -> Dict[str, Any]:
    """Score every possible action based on the full feature set.

    Returns the primary recommendation, recommendation path,
    alternatives, suitability score, reasoning factors, and
    estimated life extension.
    """
    condition = a.get("detected_condition", "fair")
    repairability = a.get("repairability", "medium")
    remaining_life = a.get("estimated_remaining_life_months")  # None = unknown
    category = a.get("detected_category", "Other")
    obj = a.get("detected_object", "item")
    damage = a.get("detected_damage")
    integrity = a.get("structural_integrity", "unknown")
    utilization = a.get("utilization", 50)

    cond_score = CONDITION_SCORE.get(condition, 50)
    repair_score = REPAIRABILITY_SCORE.get(repairability, 50)
    integrity_score = INTEGRITY_SCORE.get(integrity, 40)

    # ── Score each action ──────────────────────────────────────────
    scores = {}
    reasons: Dict[str, List[str]] = {act: [] for act in ACTIONS}

    # REUSE — good condition, functional, enough remaining life
    reuse_score = 0
    if condition in ("excellent", "good"):
        reuse_score += 40
        reasons["reuse"].append("Good/excellent condition")
    if remaining_life is not None and remaining_life >= 24:
        reuse_score += 20
        reasons["reuse"].append(f"Significant remaining life ({remaining_life} months)")
    if utilization < 30:
        reuse_score += 15
        reasons["reuse"].append("Currently underutilized — available for reuse")
    if not damage:
        reuse_score += 15
        reasons["reuse"].append("No visible damage")
    if integrity in ("good",):
        reuse_score += 10
        reasons["reuse"].append("Structural integrity is good")
    scores["reuse"] = min(reuse_score, 100)

    # REPAIR — damage exists but is fixable
    repair_score_val = 0
    if damage:
        repair_score_val += 15
        reasons["repair"].append("Damage detected that may be repairable")
    if repairability == "high":
        repair_score_val += 35
        reasons["repair"].append("High repairability")
    elif repairability == "medium":
        repair_score_val += 15
        reasons["repair"].append("Medium repairability — repair may be feasible")
    if remaining_life is not None and remaining_life >= 12:
        repair_score_val += 20
        reasons["repair"].append(f"Remaining useful life justifies repair ({remaining_life} months)")
    if integrity == "good":
        repair_score_val += 15
        reasons["repair"].append("Structural frame is stable")
    elif integrity == "minor concerns":
        repair_score_val += 5
        reasons["repair"].append("Minor structural concerns — repair may restore integrity")
    if condition in ("fair",) and repairability in ("high", "medium"):
        repair_score_val += 10
        reasons["repair"].append(f"Condition is {condition} but repairable")
    # Penalty for compromised structure
    if integrity in ("compromised", "severely compromised"):
        repair_score_val -= 15
    scores["repair"] = max(0, min(repair_score_val, 100))

    # REPURPOSE — moderate damage, different use possible
    repurpose_score = 0
    if condition in ("fair", "poor"):
        repurpose_score += 25
        reasons["repurpose"].append("Condition allows alternative use")
    if damage and repairability == "low":
        repurpose_score += 20
        reasons["repurpose"].append("Original function impaired but materials/components usable")
    if remaining_life is not None and remaining_life >= 6:
        repurpose_score += 15
        reasons["repurpose"].append("Some useful life remains")
    if integrity in ("good", "minor concerns"):
        repurpose_score += 15
        reasons["repurpose"].append("Structure stable for repurposing")
    if integrity == "compromised":
        repurpose_score -= 10
    scores["repurpose"] = max(0, min(repurpose_score, 100))

    # REDISTRIBUTE — underutilized, good condition, available
    redist_score = 0
    if utilization < 30:
        redist_score += 30
        reasons["redistribute"].append("Low utilization — available for redistribution")
    if condition in ("excellent", "good"):
        redist_score += 25
        reasons["redistribute"].append("Good condition")
    if remaining_life is not None and remaining_life >= 24:
        redist_score += 15
        reasons["redistribute"].append("Sufficient remaining life")
    if not damage:
        redist_score += 15
        reasons["redistribute"].append("No damage")
    scores["redistribute"] = min(redist_score, 100)

    # DONATE — good enough to give away
    donate_score = 0
    if condition in ("excellent", "good", "fair"):
        donate_score += 30
        reasons["donate"].append("Condition suitable for donation")
    if remaining_life is not None and remaining_life >= 12:
        donate_score += 20
        reasons["donate"].append("Usable remaining life")
    if repairability in ("high", "medium"):
        donate_score += 10
        reasons["donate"].append("Can be maintained by receiving organization")
    scores["donate"] = min(donate_score, 100)

    # RECYCLE — poor/non-functional, or severe structural damage
    recycle_score = 0
    if condition in ("poor", "severely damaged", "non-functional"):
        recycle_score += 35
        reasons["recycle"].append(f"Condition is {condition}")
    if repairability == "low":
        recycle_score += 25
        reasons["recycle"].append("Low repairability")
    if remaining_life is not None and remaining_life <= 6:
        recycle_score += 20
        reasons["recycle"].append(f"Very limited remaining life ({remaining_life} months)")
    if category == "Electronics" and condition in ("poor", "non-functional"):
        recycle_score += 15
        reasons["recycle"].append("Electronic equipment should be properly recycled (e-waste)")
    if integrity in ("compromised", "severely compromised"):
        recycle_score += 20
        reasons["recycle"].append("Structural integrity compromised — continued use may be unsafe")
    scores["recycle"] = min(recycle_score, 100)

    # DISPOSE — absolute last resort
    dispose_score = 0
    if condition == "non-functional" and repairability == "low" and (remaining_life == 0 or remaining_life is None):
        dispose_score = 30
        reasons["dispose"].append("Non-functional, low repairability, no remaining life")
    elif condition in ("poor", "severely damaged") and repairability == "low" and integrity in ("compromised", "severely compromised"):
        dispose_score = 20
        reasons["dispose"].append("Very poor condition with no viable circular option")
    else:
        dispose_score = 5
        reasons["dispose"].append("Disposal not recommended when circular alternatives exist")
    scores["dispose"] = dispose_score

    # ── Pick primary recommendation ────────────────────────────────
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary = ranked[0][0]
    primary_score = ranked[0][1]

    # Build recommendation path
    path = [primary]
    if primary == "repair":
        path.append("reuse")
    elif primary == "redistribute":
        path.append("reuse")

    # Alternatives (next 2-3 actions with score > 10, excluding dispose)
    alternatives = [name for name, sc in ranked[1:4] if sc > 10 and name != "dispose"]

    # Why this recommendation — ALWAYS use the reasons for the primary action
    why_factors = reasons.get(primary, [])
    # Ensure at least one factor
    if not why_factors:
        why_factors = [f"Recommended based on {condition} condition assessment"]

    # ── Suitability score ──────────────────────────────────────────
    # This represents: "How suitable is the recommended action for this resource?"
    # It is NOT a probability. It is a suitability assessment.
    #
    # The score is the action's own score, NOT a generic condition score.
    # If the action scores high, it means the action is well-suited.
    suitability = primary_score

    # Life extension estimate — only when known
    if primary == "repair" and remaining_life is not None:
        life_ext = int(remaining_life * 0.7) if remaining_life else None
    elif primary in ("reuse", "redistribute") and remaining_life is not None:
        life_ext = remaining_life
    elif primary == "repurpose" and remaining_life is not None:
        life_ext = int(remaining_life * 0.5) if remaining_life else None
    else:
        life_ext = None  # Unknown

    # ── Generate explanation ───────────────────────────────────────
    explanation = _generate_explanation(primary, a, why_factors)

    return {
        "recommended_action": primary.upper(),
        "recommendation_path": [p.upper() for p in path],
        "suitability_score": suitability,
        "reason": explanation,
        "why_factors": why_factors,
        "alternatives": [act.upper() for act in alternatives],
        "alternative_scores": {act.upper(): scores[act] for act in alternatives},
        "estimated_life_extension_months": life_ext,
        "all_scores": {k.upper(): v for k, v in scores.items()},
    }


def _generate_explanation(action: str, a: Dict[str, Any], factors: List[str]) -> str:
    """Generate a contextual explanation from the actual assessment fields."""
    obj = a.get("detected_object", "item")
    condition = a.get("detected_condition", "fair")
    damage = a.get("detected_damage")
    integrity = a.get("structural_integrity", "unknown")
    repairability = a.get("repairability", "medium")

    if action == "recycle":
        parts = [f"The {obj} is in {condition} condition"]
        if damage:
            parts.append(f"with visible damage ({damage})")
        if integrity in ("compromised", "severely compromised"):
            parts.append("and its structural integrity appears compromised")
        if repairability == "low":
            parts.append("with low repairability")
        parts.append("— recycling is currently more suitable than direct reuse or repair.")
        return " ".join(parts) + " Material recovery is preferable to disposal."

    if action == "repair":
        parts = [f"The {obj} has damage ({damage or 'detected'})"]
        if repairability in ("high", "medium"):
            parts.append(f"but {repairability} repairability suggests repair is feasible")
        if integrity in ("good", "minor concerns"):
            parts.append("and the structure appears intact enough to support repair")
        parts.append("— repairing and reusing extends the resource's useful life.")
        return " ".join(parts) + "."

    if action == "reuse":
        parts = [f"The {obj} appears to be in {condition} condition"]
        if not damage:
            parts.append("with no visible damage")
        if integrity == "good":
            parts.append("and good structural integrity")
        parts.append("— it can likely be reused without significant intervention.")
        return " ".join(parts) + "."

    if action == "redistribute":
        parts = [f"The {obj} is functional but underutilized"]
        parts.append("— another department or organization could benefit from it.")
        return " ".join(parts) + "."

    if action == "repurpose":
        parts = [f"The {obj} in {condition} condition"]
        if damage:
            parts.append(f"with damage ({damage})")
        parts.append("could serve a different purpose with modification.")
        return " ".join(parts) + "."

    if action == "donate":
        return f"The {obj} in {condition} condition could be donated to extend its useful life."

    # Default
    return f"Based on {condition} condition, {repairability} repairability, and {integrity} structural integrity."


# ═══════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════

def analyze_circularity(
    db,
    description=None,
    image_url=None,
    resource_id=None,
    organization_id=1,
    assessed_by_id=None,
) -> Dict[str, Any]:
    """Full circularity analysis combining description + DB resource data + image."""
    a: Dict[str, Any] = {}
    input_type = "description"
    confidence_parts = {}

    # ── Step 1: Image analysis (if provided) ──────────────────────
    if image_url:
        input_type = "image"
        vision_result = _analyze_image(image_url)

        # Merge vision observations into assessment
        obs = vision_result.get("observed", {})
        if obs.get("object"):
            a["detected_object"] = obs["object"]
            confidence_parts["object"] = vision_result["confidence"].get("object", "low")
        if obs.get("material"):
            a["detected_material"] = obs["material"]
            confidence_parts["material"] = vision_result["confidence"].get("material", "low")
        if obs.get("condition"):
            a["detected_condition"] = obs["condition"]
            confidence_parts["condition"] = vision_result["confidence"].get("condition", "low")
        if obs.get("damage_description"):
            a["detected_damage"] = obs["damage_description"]
            confidence_parts["damage"] = vision_result["confidence"].get("damage", "low")
        if obs.get("structural_integrity"):
            a["structural_integrity"] = obs["structural_integrity"]
            confidence_parts["structural_integrity"] = vision_result["confidence"].get("structural_integrity", "low")

        inf = vision_result.get("inferred", {})
        if inf.get("repairability"):
            a["repairability"] = inf["repairability"]

        a["estimated_remaining_life_months"] = vision_result.get("remaining_life")  # None from image

    # ── Step 2: Database resource record ───────────────────────────
    if resource_id:
        from app.models.resource import Resource
        r = db.query(Resource).filter(Resource.id == resource_id).first()
        if r:
            a["detected_object"] = f"{r.type} - {r.name}"
            a["detected_category"] = r.category or "Other"
            a["detected_condition"] = (r.condition or "fair").lower()
            a["utilization"] = r.utilization or 0
            a["estimated_remaining_life_months"] = r.remaining_useful_life_months
            confidence_parts["object"] = "high"
            confidence_parts["condition"] = "high"
            if r.specifications:
                if r.specifications.get("material"):
                    a["detected_material"] = r.specifications["material"]
                    confidence_parts["material"] = "high"
                if r.specifications.get("damage") and r.specifications["damage"] != "None":
                    a["detected_damage"] = r.specifications["damage"]
                    confidence_parts["damage"] = "high"
                if r.specifications.get("repairability") and r.specifications["repairability"] != "N/A":
                    a["repairability"] = r.specifications["repairability"].lower()
                    confidence_parts["repairability"] = "high"

    # ── Step 3: Description parsing (overrides/supplements) ────────
    if description:
        desc_analysis = _assess_from_description(description)
        input_type = "description"
        # Description takes precedence for all fields it can determine
        for k, v in desc_analysis.items():
            if k == "_confidence":
                confidence_parts.update(v)
            elif v is not None:
                a[k] = v

    # ── Step 4: Apply defaults for any remaining None fields ───────
    a.setdefault("detected_object", "Unknown item")
    a.setdefault("detected_category", "Other")
    a.setdefault("detected_material", "Unknown")
    a.setdefault("detected_condition", "fair")
    a.setdefault("detected_damage", None)
    a.setdefault("repairability", "medium")
    a.setdefault("structural_integrity", "unknown")
    # CRITICAL: remaining_life stays None if unknown — do NOT default to 24
    a.setdefault("estimated_remaining_life_months", None)
    a.setdefault("utilization", 50)

    # ── Step 5: Decision engine ───────────────────────────────────
    decision = _decide_recommendations(a)

    # ── Step 6: Calculate overall confidence ───────────────────────
    confidence_values = {"high": 0.9, "medium": 0.6, "low": 0.3}
    if confidence_parts:
        overall_confidence = sum(confidence_values.get(v, 0.5) for v in confidence_parts.values()) / len(confidence_parts)
    else:
        overall_confidence = 0.5 if description else 0.3

    # ── Step 7: Build recommendation list ─────────────────────────
    recs = [{"action": decision["recommended_action"], "score": decision["suitability_score"],
             "explanation": decision["reason"]}]
    for alt in decision["alternatives"]:
        alt_score = decision["alternative_scores"].get(alt, 30)
        recs.append({"action": alt, "score": alt_score,
                      "explanation": f"Alternative action for this {a['detected_object']}."})
    if "DISPOSE" not in [r["action"] for r in recs]:
        recs.append({"action": "DISPOSE", "score": 5,
                      "explanation": "Disposal is not recommended when circular alternatives exist."})

    # ── Step 8: Persist assessment ────────────────────────────────
    assessment = CircularityAssessment(
        organization_id=organization_id, assessed_by_id=assessed_by_id,
        input_type=input_type,
        input_data=(description[:500] if description else ("image_upload" if image_url else f"resource_id:{resource_id}")),
        detected_object=a["detected_object"], detected_material=a["detected_material"],
        detected_condition=a["detected_condition"], detected_damage=a.get("detected_damage"),
        repairability=a["repairability"],
        estimated_remaining_life_months=a["estimated_remaining_life_months"],
        structural_integrity=a.get("structural_integrity"),
        recommendations=recs,
        recommended_action=decision["recommended_action"],
        recommended_explanation=decision["reason"],
        confidence=overall_confidence,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    # Build remaining_life display
    remaining_life_display = a["estimated_remaining_life_months"]
    note = None
    if remaining_life_display is None and image_url and not description:
        remaining_life_display = "Unable to determine from image"
        note = "Image uploaded but no vision model configured. Please describe the resource for accurate analysis."
    elif remaining_life_display is None:
        remaining_life_display = "Unknown"
        note = "Remaining useful life cannot be determined from the information provided."

    return {
        "id": assessment.id,
        "detected_object": a["detected_object"],
        "detected_category": a["detected_category"],
        "detected_material": a["detected_material"],
        "detected_condition": a["detected_condition"],
        "detected_damage": a.get("detected_damage"),
        "repairability": a["repairability"],
        "structural_integrity": a["structural_integrity"],
        "estimated_remaining_life_months": remaining_life_display,
        "recommendations": recs,
        "recommended_action": decision["recommended_action"],
        "recommendation_path": decision["recommendation_path"],
        "suitability_score": decision["suitability_score"],
        "reason": decision["reason"],
        "why_factors": decision["why_factors"],
        "alternatives": decision["alternatives"],
        "alternative_scores": decision["alternative_scores"],
        "estimated_life_extension_months": decision["estimated_life_extension_months"],
        "all_scores": decision["all_scores"],
        "recommended_explanation": decision["reason"],
        "confidence": round(overall_confidence, 2),
        "confidence_breakdown": confidence_parts,
        "note": note,
        "created_at": assessment.created_at,
    }
