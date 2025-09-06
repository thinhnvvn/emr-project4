from sqlalchemy import inspect

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Patient

import os
print("📦 patients.py loaded from:", os.path.abspath(__file__))

router = APIRouter(tags=["patients"])

@router.get("/api/patients")
def get_all_patients(db: Session = Depends(get_db)):
    results = db.query(Patient).all()

    print("📋 Tổng số bệnh nhân:", len(results))
    for p in results:
        print("👤", p.patient_id, p.full_name)
        
    return [
        {
            "patient_id": p.patient_id,
            "full_name": p.full_name,
            "gender": p.gender or "",
            "birth_date": str(p.birth_date) if p.birth_date else "",
            "phone": p.phone or "",
            "insurance_id": p.insurance_id or ""
        }
        for p in results
    ]


