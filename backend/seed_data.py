"""Seed database with realistic demo data for ResourceLoop AI."""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
import random

from app.database.connection import engine, SessionLocal, Base
from app.models.organization import Organization
from app.models.department import Department
from app.models.user import User
from app.models.resource import Resource
from app.models.impact import ImpactRecord
from app.models.document import Document, DocumentChunk
from app.services.auth_service import hash_password


def seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("🌱 Seeding database...")

    # ── Organizations ──────────────────────────────────────────────
    orgs = [
        Organization(name="ITER", code="ITER", description="Institute of Technology and Engineering Research", address="Barcelona, Spain", share_scope="locality"),
        Organization(name="Local School", code="SCHOOL", description="Local secondary school", address="Barcelona, Spain", share_scope="locality"),
        Organization(name="Community Hospital", code="HOSPITAL", description="Community health center", address="Barcelona, Spain", share_scope="locality"),
        Organization(name="Green NGO", code="NGO", description="Environmental non-profit organization", address="Barcelona, Spain", share_scope="locality"),
        Organization(name="Tech Startup", code="STARTUP", description="AI and robotics startup", address="Barcelona, Spain", share_scope="locality"),
    ]
    db.add_all(orgs)
    db.flush()

    # ── Departments (ITER) ─────────────────────────────────────────
    iter_id = orgs[0].id
    depts_iter = [
        Department(organization_id=iter_id, name="Computer Science", code="CS", head_name="Dr. Ana García"),
        Department(organization_id=iter_id, name="Electronics Lab", code="ELEC", head_name="Dr. Carlos Ruiz"),
        Department(organization_id=iter_id, name="Mechanical Engineering", code="MECH", head_name="Dr. Luis Fernández"),
        Department(organization_id=iter_id, name="Administration", code="ADMIN", head_name="Maria López"),
        Department(organization_id=iter_id, name="Storage", code="STORAGE", head_name="Pedro Martínez"),
        Department(organization_id=iter_id, name="Library", code="LIB", head_name="Sofia Torres"),
    ]
    # Other orgs
    depts_other = [
        Department(organization_id=orgs[1].id, name="Science Department", code="SCI", head_name="Mr. Johnson"),
        Department(organization_id=orgs[1].id, name="IT Department", code="IT", head_name="Ms. Smith"),
        Department(organization_id=orgs[2].id, name="Administration", code="ADM", head_name="Dr. Brown"),
        Department(organization_id=orgs[2].id, name="Lab", code="LAB", head_name="Dr. Wilson"),
        Department(organization_id=orgs[3].id, name="Operations", code="OPS", head_name="Emma Davis"),
        Department(organization_id=orgs[4].id, name="Engineering", code="ENG", head_name="Jake Lee"),
    ]
    all_depts = depts_iter + depts_other
    db.add_all(all_depts)
    db.flush()

    # ── Users ──────────────────────────────────────────────────────
    users = [
        User(email="admin@iter.org", username="admin", hashed_password=hash_password("admin123"),
             full_name="Admin User", role="admin", organization_id=iter_id, department_id=depts_iter[3].id),
        User(email="ana.garcia@iter.org", username="ana", hashed_password=hash_password("ana123"),
             full_name="Dr. Ana García", role="manager", organization_id=iter_id, department_id=depts_iter[0].id),
        User(email="carlos.ruiz@iter.org", username="carlos", hashed_password=hash_password("carlos123"),
             full_name="Dr. Carlos Ruiz", role="manager", organization_id=iter_id, department_id=depts_iter[1].id),
        User(email="maria@iter.org", username="maria", hashed_password=hash_password("maria123"),
             full_name="Maria López", role="user", organization_id=iter_id, department_id=depts_iter[3].id),
    ]
    db.add_all(users)
    db.flush()

    now = datetime.utcnow()
    random.seed(42)  # Reproducible demo data

    # ── Resources (ITER) ──────────────────────────────────────────
    iter_resources = []

    # Computers - CS Department (some underutilized)
    cs_dept = depts_iter[0].id
    elec_dept = depts_iter[1].id
    storage_dept = depts_iter[4].id
    admin_dept = depts_iter[3].id
    mech_dept = depts_iter[2].id
    lib_dept = depts_iter[5].id

    computer_specs_pool = [
        {"cpu": "Intel i7-10700", "ram": "16GB", "storage": "512GB SSD", "gpu": "NVIDIA GTX 1650"},
        {"cpu": "Intel i7-12700", "ram": "32GB", "storage": "1TB SSD", "gpu": "NVIDIA RTX 3060"},
        {"cpu": "Intel i5-11400", "ram": "16GB", "storage": "256GB SSD", "gpu": "Intel UHD 630"},
        {"cpu": "AMD Ryzen 7 5800X", "ram": "32GB", "storage": "1TB SSD", "gpu": "NVIDIA RTX 3070"},
        {"cpu": "Intel i7-9700", "ram": "16GB", "storage": "512GB SSD", "gpu": "NVIDIA GTX 1050"},
        {"cpu": "Intel i3-10100", "ram": "8GB", "storage": "256GB SSD", "gpu": "Intel UHD 630"},
        {"cpu": "AMD Ryzen 5 3600", "ram": "16GB", "storage": "512GB SSD", "gpu": "NVIDIA GTX 1660"},
        {"cpu": "Intel i5-10400", "ram": "8GB", "storage": "256GB SSD", "gpu": "Intel UHD 630"},
    ]

    for i in range(15):
        spec = random.choice(computer_specs_pool)
        conditions = ["Excellent", "Good", "Good", "Fair", "Good"]
        availabilities = ["available", "underutilized", "in_use", "available", "available"]
        c = random.choice(conditions)
        avail = random.choice(availabilities)
        util = random.randint(5, 25) if avail == "underutilized" else random.randint(30, 90) if avail == "in_use" else random.randint(0, 15)

        iter_resources.append(Resource(
            resource_id=f"ITER-EL-{1000 + i}",
            organization_id=iter_id,
            department_id=random.choice([cs_dept, elec_dept, storage_dept]),
            category="Electronics",
            type="Computer",
            name=f"Desktop PC #{i+1}",
            description=f"Desktop computer with {spec['cpu']}, {spec['ram']} RAM, {spec['storage']}",
            condition=c,
            availability=avail,
            utilization=util,
            location=f"Building A, Room {random.randint(101, 210)}",
            building="Building A",
            room=str(random.randint(101, 210)),
            purchase_date=now - timedelta(days=random.randint(30, 1200)),
            remaining_useful_life_months=random.randint(12, 48),
            specifications=spec,
            share_scope="locality" if random.random() > 0.6 else "organization",
            original_cost=random.choice([800, 1000, 1200, 1500, 2000]),
            estimated_current_value=random.choice([400, 600, 800, 1000, 1200]),
        ))

    # Monitors
    for i in range(8):
        avail = random.choice(["available", "underutilized", "in_use"])
        util = random.randint(5, 20) if avail == "available" else random.randint(25, 60) if avail == "underutilized" else random.randint(70, 95)
        iter_resources.append(Resource(
            resource_id=f"ITER-EL-{2000 + i}",
            organization_id=iter_id,
            department_id=random.choice([cs_dept, elec_dept]),
            category="Electronics",
            type="Monitor",
            name=f"Monitor #{i+1} - {random.choice(['Dell', 'HP', 'LG', 'Samsung'])} {random.choice(['24', '27', '32'])}\"",
            description=f"{random.choice([24, 27, 32])}-inch monitor, {random.choice(['1080p', '1440p', '4K'])} resolution",
            condition=random.choice(["Good", "Good", "Excellent", "Fair"]),
            availability=avail,
            utilization=util,
            location=f"Building A, Room {random.randint(101, 210)}",
            building="Building A",
            room=str(random.randint(101, 210)),
            purchase_date=now - timedelta(days=random.randint(60, 900)),
            remaining_useful_life_months=random.randint(18, 60),
            specifications={
                "brand": random.choice(["Dell", "HP", "LG", "Samsung"]),
                "screen_size": f"{random.choice([24, 27, 32])} inches",
                "resolution": random.choice(["1080p", "1440p", "4K"]),
            },
            share_scope="locality" if random.random() > 0.5 else "organization",
            original_cost=random.choice([200, 300, 450, 600]),
            estimated_current_value=random.choice([100, 150, 250, 350]),
        ))

    # Chairs (some damaged for circularity demo)
    for i in range(12):
        c = random.choice(["Excellent", "Good", "Good", "Fair", "Fair", "Poor"])
        avail_map = {"Excellent": "in_use", "Good": random.choice(["in_use", "available"]), "Fair": "available", "Poor": "available"}
        util_map = {"Excellent": 85, "Good": random.choice([65, 40, 15]), "Fair": random.choice([10, 20]), "Poor": 5}
        condition = c
        avail = avail_map[condition]
        util = util_map[condition]
        damage = ""
        if condition == "Fair":
            damage = random.choice(["Broken armrest", "Worn cushion", "Loose screws", "Scratched back"])
        elif condition == "Poor":
            damage = random.choice(["Broken armrest and base", "Torn fabric", "Missing wheels"])

        iter_resources.append(Resource(
            resource_id=f"ITER-FN-{3000 + i}",
            organization_id=iter_id,
            department_id=random.choice([cs_dept, elec_dept, admin_dept, mech_dept]),
            category="Furniture",
            type="Chair",
            name=f"Office Chair #{i+1}",
            description=f"Office chair, metal frame, fabric seat" + (f". Damage: {damage}." if damage else ""),
            condition=condition,
            availability=avail,
            utilization=util,
            location=f"Building {random.choice(['A', 'B'])}, Room {random.randint(101, 305)}",
            building=f"Building {random.choice(['A', 'B'])}",
            room=str(random.randint(101, 305)),
            purchase_date=now - timedelta(days=random.randint(180, 2000)),
            remaining_useful_life_months=random.choice([3, 12, 24, 36, 48]) if condition != "Poor" else 3,
            specifications={
                "material": "Metal + Fabric",
                "damage": damage if damage else "None",
                "repairability": "High" if condition in ("Fair", "Poor") else "N/A",
            },
            share_scope="locality" if random.random() > 0.7 else "organization",
            original_cost=random.choice([150, 200, 250, 350]),
            estimated_current_value=random.choice([30, 80, 120, 180]),
        ))

    # Desks
    for i in range(6):
        iter_resources.append(Resource(
            resource_id=f"ITER-FN-{4000 + i}",
            organization_id=iter_id,
            department_id=random.choice([cs_dept, admin_dept, mech_dept]),
            category="Furniture",
            type="Desk",
            name=f"Office Desk #{i+1}",
            description=f"Standard office desk, {random.choice(['wood', 'laminate'])} surface",
            condition=random.choice(["Good", "Good", "Excellent", "Fair"]),
            availability=random.choice(["in_use", "available"]),
            utilization=random.randint(10, 80),
            location=f"Building {random.choice(['A', 'B'])}, Room {random.randint(101, 305)}",
            building=f"Building {random.choice(['A', 'B'])}",
            room=str(random.randint(101, 305)),
            purchase_date=now - timedelta(days=random.randint(180, 1800)),
            remaining_useful_life_months=random.randint(12, 60),
            specifications={"material": random.choice(["Wood", "Laminate"]), "size": "120x60cm"},
            share_scope="organization",
            original_cost=random.choice([200, 300, 400]),
            estimated_current_value=random.choice([80, 150, 250]),
        ))

    # Projectors
    for i in range(4):
        avail = random.choice(["available", "underutilized", "in_use"])
        iter_resources.append(Resource(
            resource_id=f"ITER-EL-{5000 + i}",
            organization_id=iter_id,
            department_id=random.choice([cs_dept, admin_dept]),
            category="Electronics",
            type="Projector",
            name=f"Projector #{i+1} - {random.choice(['Epson', 'BenQ', 'Sony'])}",
            description=f"HD projector, {random.choice([3000, 4000, 5000])} lumens",
            condition=random.choice(["Good", "Excellent"]),
            availability=avail,
            utilization=random.randint(5, 70),
            location=f"Building A, Room {random.randint(101, 210)}",
            building="Building A",
            room=str(random.randint(101, 210)),
            purchase_date=now - timedelta(days=random.randint(90, 1200)),
            remaining_useful_life_months=random.randint(12, 36),
            specifications={
                "brand": random.choice(["Epson", "BenQ", "Sony"]),
                "resolution": random.choice(["1080p", "4K"]),
                "lumens": random.choice([3000, 4000, 5000]),
            },
            share_scope="locality",
            original_cost=random.choice([500, 800, 1200]),
            estimated_current_value=random.choice([250, 400, 600]),
        ))

    # Printers
    for i in range(3):
        iter_resources.append(Resource(
            resource_id=f"ITER-EL-{6000 + i}",
            organization_id=iter_id,
            department_id=random.choice([admin_dept, cs_dept]),
            category="Office Equipment",
            type="Printer",
            name=f"Printer #{i+1} - {random.choice(['HP LaserJet', 'Epson EcoTank', 'Brother'])}",
            description=f"{random.choice(['Laser', 'Inkjet'])} printer, {random.choice(['mono', 'color'])}",
            condition=random.choice(["Good", "Fair"]),
            availability=random.choice(["in_use", "available"]),
            utilization=random.randint(20, 75),
            location=f"Building A, Room {random.randint(101, 210)}",
            building="Building A",
            room=str(random.randint(101, 210)),
            purchase_date=now - timedelta(days=random.randint(120, 1000)),
            remaining_useful_life_months=random.randint(12, 30),
            specifications={"brand": random.choice(["HP", "Epson", "Brother"]), "type": random.choice(["Laser", "Inkjet"])},
            share_scope="organization",
            original_cost=random.choice([200, 400, 600]),
            estimated_current_value=random.choice([80, 150, 250]),
        ))

    # Lab equipment
    for i in range(5):
        iter_resources.append(Resource(
            resource_id=f"ITER-LB-{7000 + i}",
            organization_id=iter_id,
            department_id=elec_dept,
            category="Laboratory Equipment",
            type=random.choice(["Oscilloscope", "Multimeter", "Signal Generator", "Power Supply", "Spectrum Analyzer"]),
            name=f"Lab Instrument #{i+1}",
            description=f"Professional-grade {random.choice(['oscilloscope', 'multimeter', 'signal generator'])}",
            condition=random.choice(["Excellent", "Good"]),
            availability=random.choice(["available", "underutilized", "in_use"]),
            utilization=random.randint(10, 85),
            location=f"Building B, Lab {random.randint(1, 5)}",
            building="Building B",
            room=f"Lab {random.randint(1, 5)}",
            purchase_date=now - timedelta(days=random.randint(200, 1500)),
            remaining_useful_life_months=random.randint(24, 72),
            specifications={"brand": random.choice(["Keysight", "Tektronix", "Rigol"])},
            share_scope="organization",
            original_cost=random.choice([500, 1000, 2000, 3500]),
            estimated_current_value=random.choice([250, 500, 1200, 2000]),
        ))

    # Books
    for i in range(8):
        iter_resources.append(Resource(
            resource_id=f"ITER-BK-{8000 + i}",
            organization_id=iter_id,
            department_id=lib_dept,
            category="Books",
            type="Textbook",
            name=f"Textbook #{i+1}",
            description=random.choice([
                "Introduction to Machine Learning - 3rd Edition",
                "Database System Concepts - 7th Edition",
                "Operating Systems: Design and Implementation",
                "Computer Networks - 6th Edition",
                "Artificial Intelligence: A Modern Approach",
                "Pattern Recognition and Machine Learning",
                "Numerical Methods for Engineers",
                "Physics for Scientists and Engineers",
            ]),
            condition=random.choice(["Excellent", "Good", "Good", "Fair"]),
            availability=random.choice(["available", "available", "in_use"]),
            utilization=random.randint(0, 60),
            location="Library, Shelf A",
            building="Library",
            room="Shelf A",
            purchase_date=now - timedelta(days=random.randint(365, 3000)),
            remaining_useful_life_months=random.randint(12, 60),
            specifications={"pages": random.randint(400, 1200), "edition": random.choice(["3rd", "5th", "7th"])},
            share_scope="locality",
            original_cost=random.choice([40, 60, 80, 120]),
            estimated_current_value=random.choice([10, 20, 30, 50]),
        ))

    # Networking equipment
    for i in range(4):
        iter_resources.append(Resource(
            resource_id=f"ITER-NW-{9000 + i}",
            organization_id=iter_id,
            department_id=cs_dept,
            category="Electronics",
            type=random.choice(["Router", "Switch", "Access Point"]),
            name=f"Network Device #{i+1}",
            description=f"{random.choice(['Cisco', 'Ubiquiti', 'TP-Link'])} {random.choice(['router', 'switch', 'access point'])}",
            condition=random.choice(["Good", "Good", "Excellent"]),
            availability=random.choice(["in_use", "available"]),
            utilization=random.randint(15, 90),
            location=f"Building A, Server Room",
            building="Building A",
            room="Server Room",
            purchase_date=now - timedelta(days=random.randint(90, 800)),
            remaining_useful_life_months=random.randint(12, 48),
            specifications={"brand": random.choice(["Cisco", "Ubiquiti", "TP-Link"]), "ports": random.choice([8, 16, 24, 48])},
            share_scope="organization",
            original_cost=random.choice([100, 300, 500, 800]),
            estimated_current_value=random.choice([50, 150, 300, 500]),
        ))

    # ── Add ITER resources to DB ──
    db.add_all(iter_resources)

    # ── Resources from other organizations (for network demo) ──
    # Local School
    school_dept = depts_other[0].id
    for i in range(6):
        orgs[1].id
        db.add(Resource(
            resource_id=f"SCH-EL-{1000 + i}",
            organization_id=orgs[1].id,
            department_id=school_dept,
            category="Electronics",
            type="Computer",
            name=f"School Computer #{i+1}",
            description=f"Computer for science lab",
            condition=random.choice(["Good", "Fair"]),
            availability=random.choice(["available", "in_use"]),
            utilization=random.randint(10, 70),
            location="Science Lab",
            remaining_useful_life_months=random.randint(6, 24),
            specifications={"cpu": "Intel i5-8400", "ram": "8GB", "storage": "256GB SSD", "gpu": "Integrated"},
            share_scope="locality",
            original_cost=600,
            estimated_current_value=200,
        ))

    # Community Hospital
    hosp_dept = depts_other[2].id
    for i in range(4):
        db.add(Resource(
            resource_id=f"HOS-FN-{1000 + i}",
            organization_id=orgs[2].id,
            department_id=hosp_dept,
            category="Furniture",
            type="Chair",
            name=f"Hospital Chair #{i+1}",
            description="Waiting room chair",
            condition="Good",
            availability="available",
            utilization=20,
            location="Reception Area",
            remaining_useful_life_months=24,
            specifications={"material": "Metal + Vinyl", "damage": "None"},
            share_scope="locality",
            original_cost=150,
            estimated_current_value=60,
        ))

    # Green NGO
    ngo_dept = depts_other[4].id
    for i in range(5):
        db.add(Resource(
            resource_id=f"NGO-EL-{1000 + i}",
            organization_id=orgs[3].id,
            department_id=ngo_dept,
            category="Electronics",
            type=random.choice(["Monitor", "Printer"]),
            name=f"NGO Equipment #{i+1}",
            description=f"Office {random.choice(['monitor', 'printer'])}",
            condition=random.choice(["Good", "Fair"]),
            availability="available",
            utilization=15,
            location="Office",
            remaining_useful_life_months=18,
            specifications={"brand": random.choice(["Dell", "HP"])},
            share_scope="locality",
            original_cost=300,
            estimated_current_value=100,
        ))

    # Tech Startup
    startup_dept = depts_other[5].id
    for i in range(7):
        db.add(Resource(
            resource_id=f"STU-EL-{1000 + i}",
            organization_id=orgs[4].id,
            department_id=startup_dept,
            category="Electronics",
            type="Computer",
            name=f"Startup PC #{i+1}",
            description=f"Workstation for engineering team",
            condition="Good",
            availability=random.choice(["available", "in_use"]),
            utilization=random.randint(10, 80),
            location="Office Floor 2",
            remaining_useful_life_months=random.randint(12, 36),
            specifications={"cpu": "AMD Ryzen 7 5800X", "ram": "32GB", "storage": "1TB SSD", "gpu": "NVIDIA RTX 3060"},
            share_scope="locality",
            original_cost=1500,
            estimated_current_value=800,
        ))

    db.flush()

    # ── Impact Records (sample historical data) ──
    for month_offset in range(6):
        month_start = (now - timedelta(days=30 * month_offset)).replace(day=1)
        month_end = month_start + timedelta(days=30)
        
        db.add(ImpactRecord(
            organization_id=iter_id,
            resources_reused=random.randint(2, 8),
            resources_repaired=random.randint(1, 4),
            resources_redistributed=random.randint(1, 5),
            resources_recycled=random.randint(0, 3),
            purchases_avoided=random.randint(2, 6),
            cost_avoided=random.uniform(1000, 8000),
            waste_avoided_kg=random.uniform(50, 200),
            co2_saved_kg=random.uniform(100, 500),
            period="monthly",
            period_start=month_start,
            period_end=month_end,
            notes=f"Monthly impact record for {month_start.strftime('%B %Y')}",
        ))

    # ── Documents ──
    docs = [
        Document(
            organization_id=iter_id,
            name="Equipment Transfer Policy",
            filename="transfer_policy.pdf",
            file_type="pdf",
            category="policy",
            description="Policy for internal equipment transfers between departments",
            status="processed",
            chunk_count=3,
        ),
        Document(
            organization_id=iter_id,
            name="Procurement Guidelines",
            filename="procurement.pdf",
            file_type="pdf",
            category="policy",
            description="Guidelines for purchasing new equipment and resources",
            status="processed",
            chunk_count=2,
        ),
        Document(
            organization_id=iter_id,
            name="Maintenance Procedures",
            filename="maintenance.pdf",
            file_type="pdf",
            category="manual",
            description="Equipment maintenance and repair procedures",
            status="processed",
            chunk_count=2,
        ),
        Document(
            organization_id=iter_id,
            name="Sustainability Policy",
            filename="sustainability.pdf",
            file_type="pdf",
            category="policy",
            description="Organization sustainability and circular economy policy",
            status="processed",
            chunk_count=2,
        ),
    ]
    db.add_all(docs)
    db.flush()

    # Document chunks for RAG
    chunks = [
        DocumentChunk(document_id=docs[0].id, chunk_index=0,
            content="Section 3.1: Internal transfers between departments within the same organization are permitted when the originating department declares the equipment as surplus and the receiving department formally accepts responsibility for maintenance and usage costs.",
            chunk_metadata='{"section": "3.1", "page": 2}'),
        DocumentChunk(document_id=docs[0].id, chunk_index=1,
            content="Section 3.2: Cross-organization transfers require approval from both organization administrators. Equipment must be marked as 'locality-shareable' in the inventory system. A transfer agreement must be signed by authorized representatives of both organizations.",
            chunk_metadata='{"section": "3.2", "page": 2}'),
        DocumentChunk(document_id=docs[0].id, chunk_index=2,
            content="Section 4.1: Equipment condition must be assessed before transfer. Items in 'Poor' or 'Non-functional' condition must be repaired or recycled before transfer approval. The sending organization bears the cost of condition assessment.",
            chunk_metadata='{"section": "4.1", "page": 3}'),
        DocumentChunk(document_id=docs[1].id, chunk_index=0,
            content="Section 2.1: Before any new purchase exceeding €500, departments must search the internal resource inventory for available alternatives. If compatible resources exist within the organization, they must be considered first.",
            chunk_metadata='{"section": "2.1", "page": 1}'),
        DocumentChunk(document_id=docs[1].id, chunk_index=1,
            content="Section 2.2: Procurement requests that bypass the inventory search must include justification. The sustainability office may flag requests for review if available resources could satisfy the requirement.",
            chunk_metadata='{"section": "2.2", "page": 1}'),
        DocumentChunk(document_id=docs[2].id, chunk_index=0,
            content="Section 1.1: All electronic equipment must undergo preventive maintenance every 6 months. Maintenance records must be updated in the inventory system. Equipment with missed maintenance should be flagged for review.",
            chunk_metadata='{"section": "1.1", "page": 1}'),
        DocumentChunk(document_id=docs[2].id, chunk_index=1,
            content="Section 2.1: Repair priority is given to items with high repairability scores. When repair cost exceeds 50% of replacement value, recycling or repurposing should be considered instead.",
            chunk_metadata='{"section": "2.1", "page": 2}'),
        DocumentChunk(document_id=docs[3].id, chunk_index=0,
            content="Policy Statement: ITER is committed to responsible resource management aligned with UN SDG 12 - Responsible Consumption and Production. The organization targets a 30% reduction in unnecessary procurement through resource circularity by 2027.",
            chunk_metadata='{"section": "policy_statement", "page": 1}'),
        DocumentChunk(document_id=docs[3].id, chunk_index=1,
            content="Section 5.1: Resource circularity priorities: 1) Reuse within organization, 2) Redistribute to departments with higher need, 3) Repair and redeploy, 4) Donate to community partners, 5) Repurpose for alternative use, 6) Recycle materials, 7) Dispose only as last resort.",
            chunk_metadata='{"section": "5.1", "page": 3}'),
    ]
    db.add_all(chunks)

    db.commit()
    db.close()
    print("✅ Database seeded successfully!")
    print(f"   Organizations: 5")
    print(f"   Departments: {len(all_depts)}")
    print(f"   Users: {len(users)}")
    print(f"   Resources: ~80 across all organizations")
    print(f"   Impact records: 6 monthly")
    print(f"   Documents: {len(docs)}")
    print(f"   Document chunks: {len(chunks)}")


if __name__ == "__main__":
    seed()
