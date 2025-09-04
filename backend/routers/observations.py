from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Observation

router = APIRouter(tags=["observations"])

@router.get("/api/observations/{patient_id}")
def get_observations_by_patient(patient_id: str, db: Session = Depends(get_db)):
    observations = db.query(Observation).filter(Observation.patient_id == patient_id).order_by(Observation.date.desc()).all()
    return [
        {
            "id": o.id,
            "patient_id": o.patient_id,
            "type": o.type,
            "value": o.value,
            "date": o.date.strftime("%Y-%m-%d")
        }
        for o in observations
    ]
