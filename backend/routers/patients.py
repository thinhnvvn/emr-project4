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
    # Lấy danh sách cột thực tế từ bảng patients
    inspector = inspect(db.bind)
    actual_columns = [col["name"] for col in inspector.get_columns("patients")]

    try:
        # Truy vấn tất cả bản ghi
        result = db.query(Patient).all()

        # Chuyển mỗi bản ghi thành dict chỉ chứa các cột hợp lệ
        patients_data = []
        for p in result:
            patient_dict = {
                col: getattr(p, col)
                for col in actual_columns
                if hasattr(p, col)
            }
            patients_data.append(patient_dict)

        return patients_data

    except Exception as e:
        print(f"❌ Error querying patients: {str(e)}")
        raise

@router.get("/api/patients/search-old")
def search_patients(
    query: str = Query(..., description="Search by patient ID or name"),
    db: Session = Depends(get_db)
):
    results = db.query(Patient).filter(
        (Patient.patient_id.ilike(f"%{query}%")) |
        (Patient.full_name.ilike(f"%{query}%"))
    ).all()

    return [
        {
            # "patient_id": p.patient_id,
            # "full_name": p.full_name,
            # "birth_date": p.birth_date,
            # "date_of_birth": p.date_of_birth,
            # "contact_number": p.contact_number
            
            "patient_id": p.patient_id,
            "full_name": p.full_name,
            "gender": p.gender or "",
            "birth_date": str(p.birth_date) if p.birth_date else "",
            "phone": p.phone or "",
            "insurance_id": p.insurance_id or ""
        }
        for p in results
    ]