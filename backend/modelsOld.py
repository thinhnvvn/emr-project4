from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import sys
import os

print("Current sys.path:", sys.path)  # Debug sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.database import get_db, init_db
from backend.models import Patient
from backend.crud.patient import get_patients

app = FastAPI()

app.mount("/app", StaticFiles(directory="frontend/www", html=True), name="frontend")

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/api/patients")
def get_all_patients(db: Session = Depends(get_db)):
    try:
        patients = get_patients(db)
        return [
            {
                "patient_id": p.patient_id,
                "full_name": p.full_name,
                "gender": p.gender,
                "birth_date": p.birth_date.strftime("%Y-%m-%d") if p.birth_date else None,
                "phone": p.phone,
                "insurance_id": p.insurance_id
            }
            for p in patients
        ]
    except Exception as e:
        print(f"Error in get_all_patients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/api")
def read_api():
    return {"message": "✅ EMR backend is running!"}

@app.on_event("startup")
def show_routes():
    for route in app.routes:
        print("→", route.path, "-", route.name)