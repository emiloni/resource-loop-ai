"""Impact Service."""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models.impact import ImpactRecord

ASSUMPTIONS = {
    "co2_per_kg_electronics": 15.0, "co2_per_kg_furniture": 5.0, "co2_per_kg_general": 3.0,
    "avg_waste_per_item_kg": 12.0, "avg_cost_new_computer": 1200.0, "avg_cost_new_furniture": 400.0,
    "avg_cost_new_equipment": 800.0, "repair_cost_fraction": 0.20,
}

def _category_cost(cat):
    return {"Electronics": 1200, "Furniture": 400, "Laboratory Equipment": 800, "Office Equipment": 800, "Books": 50}.get(cat, 800)

def _category_co2(cat):
    return {"Electronics": 240, "Furniture": 100, "Laboratory Equipment": 120, "Office Equipment": 30, "Books": 2}.get(cat, 30)


def get_impact_summary(db: Session, organization_id: int = 1) -> Dict[str, Any]:
    agg = db.query(
        func.coalesce(func.sum(ImpactRecord.resources_reused), 0),
        func.coalesce(func.sum(ImpactRecord.resources_repaired), 0),
        func.coalesce(func.sum(ImpactRecord.resources_redistributed), 0),
        func.coalesce(func.sum(ImpactRecord.resources_recycled), 0),
        func.coalesce(func.sum(ImpactRecord.purchases_avoided), 0),
        func.coalesce(func.sum(ImpactRecord.cost_avoided), 0),
        func.coalesce(func.sum(ImpactRecord.waste_avoided_kg), 0),
        func.coalesce(func.sum(ImpactRecord.co2_saved_kg), 0),
    ).filter(ImpactRecord.organization_id == organization_id).first()

    summary = {"resources_reused": int(agg[0]), "resources_repaired": int(agg[1]),
               "resources_redistributed": int(agg[2]), "resources_recycled": int(agg[3]),
               "purchases_avoided": int(agg[4]), "cost_avoided": float(agg[5]),
               "waste_avoided_kg": float(agg[6]), "co2_saved_kg": float(agg[7]), "assumptions": ASSUMPTIONS}

    trends = []
    now = datetime.utcnow()
    for i in range(11, -1, -1):
        ms = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0)
        me = (ms + timedelta(days=32)).replace(day=1)
        md = db.query(func.coalesce(func.sum(ImpactRecord.purchases_avoided), 0),
                       func.coalesce(func.sum(ImpactRecord.cost_avoided), 0),
                       func.coalesce(func.sum(ImpactRecord.co2_saved_kg), 0)).filter(
            ImpactRecord.organization_id == organization_id, ImpactRecord.period_start >= ms, ImpactRecord.period_start < me).first()
        trends.append({"period": ms.strftime("%Y-%m"), "purchases_avoided": int(md[0]), "cost_avoided": float(md[1]), "co2_saved_kg": float(md[2])})

    env = {"waste_diverted_from_landfill_kg": float(agg[6]), "co2_emissions_prevented_kg": float(agg[7]),
           "trees_equivalent": round(float(agg[7]) / 21.77, 1), "car_km_equivalent": round(float(agg[7]) / 0.21, 0),
           "methodology": "Environmental estimates are based on industry-average emission factors."}
    fin = {"total_cost_avoided": float(agg[5]),
           "avg_savings_per_resource": round(float(agg[5]) / max(int(agg[4]), 1), 2),
           "methodology": "Cost avoidance estimates based on average replacement costs by category."}
    sdg = {"SDG 12": "Responsible Consumption and Production", "SDG 9": "Industry, Innovation and Infrastructure",
           "SDG 11": "Sustainable Cities and Communities (future)"}

    return {"summary": summary, "trends": trends, "environmental_details": env, "financial_details": fin, "sdg_alignment": sdg}
