from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import Vital

router = APIRouter(prefix="/api/vitals", tags=["vitals"])

# Dependency để lấy session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API: Lấy danh sách chỉ số sinh tồn của bệnh nhân
@router.get("/{patient_id}")
def get_vitals(patient_id: str, db: Session = Depends(get_db)):
    records = (
        db.query(Vital)
        .filter(Vital.patient_id == patient_id)
        .order_by(Vital.date.desc())
        .all()
    )
    return [
        {
            "date": v.date.strftime("%Y-%m-%d"),
            "temperature": v.temperature,
            "heart_rate": v.heart_rate,
            "blood_pressure": v.blood_pressure,
            "spo2": v.spo2,
            "glucose": v.glucose,
            "respiratory_rate": v.respiratory_rate,
        }
        for v in records
    ]
