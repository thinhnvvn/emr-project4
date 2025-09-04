from sqlalchemy.orm import Session
# from ..models import Patient
from backend.models import Patient
from sqlalchemy import inspect




def get_patients(db: Session):
    inspector = inspect(db.bind)
    actual_columns = [col["name"] for col in inspector.get_columns("patients")]

    try:
        result = db.query(Patient).all()
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
