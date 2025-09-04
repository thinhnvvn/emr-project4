from sqlalchemy import Column, Integer, String, Date, Float
from backend.base import Base  # Import Base từ base.py

class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = {'schema': 'public'}  # Thay 'public' bằng schema thực tế nếu khác
    # patient_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, primary_key=True, index=True)

    full_name = Column(String)
    gender = Column(String)
    birth_date = Column(String)
    phone = Column(String)
    insurance_id = Column(String)
    
class Observation(Base):
    __tablename__ = "observation"

    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    type = Column(String)
    value = Column(String)
    date = Column(Date)
    
print("MODEL FILE:", __file__)