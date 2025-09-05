from backend.routers.patients import router as patients_router
from backend.routers.observations import router as observations_router
from backend.models import Patient, Observation


from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import sys
import os
import pandas as pd
import statistics



print("Current sys.path:", sys.path)  # Debug sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.database import get_db, init_db
from backend.models import Patient
from backend.crud.patient import get_patients  # Import get_patients từ crud/patient.py
from fastapi.responses import JSONResponse

from backend.analysis import  analyze_observations, classify_risk
from collections import defaultdict
from fastapi.responses import FileResponse

import psycopg2
import logging

# =================================================================================
# cho Render
import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv("DATABASE_URL")
# =================================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


app = FastAPI()

from backend.routers import patients
app.include_router(patients.router)

'''
=================================================================================
# good for local

# Tính đường dẫn tuyệt đối tới thư mục www
static_path = os.path.abspath("D:/emr-project4/frontend/www")

# Kiểm tra tồn tại
if not os.path.exists(static_path):
    raise RuntimeError(f"❌ Thư mục static không tồn tại: {static_path}")

# Mount static files
app.mount("/static", StaticFiles(directory=static_path, html=True), name="static")

# print("📁 Static path:", static_path)
# print("📄 search.html exists:", os.path.exists(os.path.join(static_path, "search.html")))
'''
# ==================================================================================
# chạy được cả trên máy bạn và trên Render

# Tính đường dẫn tương đối tới thư mục frontend/www
static_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "www")
static_path = os.path.abspath(static_path)

# Kiểm tra tồn tại
if not os.path.exists(static_path):
    raise RuntimeError(f"❌ Thư mục static không tồn tại: {static_path}")

# Mount static files vào /static
app.mount("/static", StaticFiles(directory=static_path, html=True), name="static")
#  mount thêm để có thể truy cập index.html qua /
app.mount("/", StaticFiles(directory=static_path, html=True), name="frontend")


print("📁 Static path:", static_path)
print("📄 search.html exists:", os.path.exists(os.path.join(static_path, "search.html")))

# =================================================================================

# 2) Trả về search.html khi truy cập gốc
@app.get("/", include_in_schema=False)
def serve_search():
    # return FileResponse("static/search.html")
    return FileResponse(os.path.join(static_path, "search.html"))


# Include router
app.include_router(patients_router)
app.include_router(observations_router)

# Kiểm tra tồn tại
if not os.path.exists(static_path):
    raise RuntimeError(f"❌ Thư mục static không tồn tại: {static_path}")



@app.on_event("startup")
async def startup_event():
    init_db()  # Khởi tạo database khi app khởi động

@app.get("/api/patients")
def read_patients(db: Session = Depends(get_db)):
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
        print(f"Error in read_patients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

print("📄 ĐANG CHẠY FILE:", __file__, flush=True)

# trả lại nhiều kết quả
@app.get("/api/patients/search")
def search_patients(query: str = Query(...), db: Session = Depends(get_db)):
    from backend.models import Patient

    query = query.strip()

    # Nếu query giống ID (bắt đầu bằng "P" và có số), thì tìm theo ID chính xác
    if query.upper().startswith("P") and query[1:].isdigit():
        results = db.query(Patient).filter(Patient.patient_id == query).all()
    else:
        # Ngược lại, tìm theo tên gần đúng
        results = db.query(Patient).filter(Patient.full_name.ilike(f"%{query}%")).all()

    response = []
    for p in results:
        response.append({
            "patient_id": p.patient_id,
            "full_name": p.full_name,
            "gender": p.gender or "",
            "birth_date": str(p.birth_date) if p.birth_date else "",
            "phone": p.phone or "",
            "insurance_id": p.insurance_id or ""
        })

    return response

# @app.get("/api/observations/{patient_id}")
# def get_observations(patient_id: str, db: Session = Depends(get_db)):
#     print("Kiểu db:", type(db))

#     try:
#         obs = db.query(Observation).filter(Observation.patient_id == patient_id).all()
#         return [{
#             "type": o.type,
#             "value": o.value,
#             "date": o.date.isoformat() if o.date else None
#         } for o in obs]
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Lỗi khi truy vấn: {str(e)}")

@app.get("/api/observations/{patient_id}/analyze")
def analyze_observations(patient_id: str, db: Session = Depends(get_db)):
    rows = db.query(Observation).filter(Observation.patient_id == patient_id).order_by(Observation.date.asc()).all()
    
    grouped = defaultdict(list)
    for obs in rows:
        try:
            val = float(str(obs.value).replace("°C", "").strip())
            grouped[obs.type].append(val)
        except Exception as e:
            print(f"Lỗi ép kiểu value: {obs.value} → {e}")
            continue

    result = {}
    for obs_type, values in grouped.items():
        values = values[-6:]
        try:
            trend = analyze_trend(values)
            mean = round(statistics.mean(values), 2) if values else None
            std_dev = round(statistics.stdev(values), 2) if len(values) > 1 else None
            rolling = round(statistics.mean(values[-3:]), 2) if len(values) >= 3 else None
        except Exception as e:
            print(f"Lỗi phân tích {obs_type}: {e}")
            trend, mean, std_dev, rolling = "Không thể phân tích", None, None, None

        result[obs_type] = {
            "trend": trend,
            "mean": mean,
            "std_dev": std_dev,
            "latest_rolling_mean": rolling,
            "data_points": len(values)
        }

    return result

@app.get("/api")
def read_api():
    return {"message": "✅ EMR backend is running!"}


from sqlalchemy import text

@app.on_event("startup")
# good
# def show_routes():
#     for route in app.routes:
#         print("→", route.path, "-", route.name)

# good
# def check_columns():
#     from backend.database import SessionLocal
#     db = SessionLocal()
#     result = db.execute(text("SELECT * FROM patients LIMIT 1"))
#     print("🧪 Columns:", result.keys())
    
def show_db_name():
    from backend.database import SessionLocal
    db = SessionLocal()
    db_name = db.execute(text("SELECT current_database()")).scalar()
    print("🧠 Connected to database:", db_name)
    
# ================================================================================================

# @app.get("/api/observations/{patient_id}/analyze")
# def analyze_patient_observations(patient_id: str, db: Session = Depends(get_db)):
#     try:
#         obs = db.query(Observation).filter(Observation.patient_id == patient_id).all()
#         if not obs:
#             raise HTTPException(status_code=404, detail="Không có dữ liệu quan sát")

#         result = analyze_observations(obs)
#         return result

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Lỗi phân tích: {str(e)}")


# @app.get("/api/patients/{patient_id}/risk")
# def get_patient_risk(patient_id: str, db: Session = Depends(get_db)):
#     try:
#         obs = db.query(Observation).filter(Observation.patient_id == patient_id).all()
#         if not obs:
#             raise HTTPException(status_code=404, detail="Không có dữ liệu quan sát")

#         risk = classify_risk(obs)
#         return {"patient_id": patient_id, "risk_level": risk}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Lỗi phân loại nguy cơ: {str(e)}")

# @app.get("/api/observations/{patient_id}/analyze")
# def analyze_patient_observations(patient_id: str, db: Session = Depends(get_db)):
#     from backend.analysis import analyze_observations

#     try:
#         obs = db.query(Observation).filter(Observation.patient_id == patient_id).all()
#         if not obs:
#             return JSONResponse(status_code=404, content={"detail": "Không có dữ liệu quan sát"})

#         result = analyze_observations(obs)
#         return JSONResponse(status_code=200, content=result)

#     except Exception as e:
#         return JSONResponse(status_code=500, content={"detail": f"Lỗi phân tích: {str(e)}"})


# @app.get("/api/patients/{patient_id}/risk")
# def get_patient_risk(patient_id: str, db: Session = Depends(get_db)):
#     from backend.analysis import classify_risk

#     try:
#         obs = db.query(Observation).filter(Observation.patient_id == patient_id).all()
#         if not obs:
#             raise HTTPException(status_code=404, detail="Không có dữ liệu quan sát")

#         risk = classify_risk(obs)
#         return {"patient_id": patient_id, "risk_level": risk}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Lỗi phân loại nguy cơ: {str(e)}")


@app.get("/api/observations/{patient_id}/analyze")
def analyze_patient_observations(patient_id: str, db: Session = Depends(get_db)):
    try:
        obs = db.query(Observation).filter(Observation.patient_id == patient_id).all()
        if not obs:
            return JSONResponse(status_code=404, content={"detail": "Không có dữ liệu quan sát"})

        result = analyze_observations(obs)
        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Lỗi phân tích: {str(e)}"})


@app.get("/api/patients/{patient_id}/risk")
def get_patient_risk(patient_id: str, db: Session = Depends(get_db)):
    try:
        obs = db.query(Observation).filter(Observation.patient_id == patient_id).all()
        if not obs:
            return JSONResponse(status_code=404, content={"detail": "Không có dữ liệu quan sát"})

        risk = classify_risk(obs)
        return JSONResponse(status_code=200, content={"patient_id": patient_id, "risk_level": risk})

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Lỗi phân loại nguy cơ: {str(e)}"})
    

def analyze_trend(values):
    if len(values) < 3:
        return "Không đủ dữ liệu"
    diffs = [values[i] - values[i - 1] for i in range(1, len(values))]
    avg_diff = sum(diffs) / len(diffs)
    max_diff = max(abs(d) for d in diffs)

    if abs(avg_diff) < 0.05 and max_diff < 0.2:
        return "Ổn định"
    elif avg_diff > 0.1 and max_diff > 0.3:
        return "Tăng rõ rệt"
    elif avg_diff < -0.1 and max_diff > 0.3:
        return "Giảm rõ rệt"
    elif avg_diff > 0.05:
        return "Tăng nhẹ"
    elif avg_diff < -0.05:
        return "Giảm nhẹ"
    else:
        return "Dao động"


# @app.get("/api/observations/{patient_id}/analyze")
# def analyze_observations(patient_id: str):
#     print("Gọi phân tích cho:", patient_id, type(patient_id))
#     try:
#         conn = psycopg2.connect(
#             host="localhost",
#             database="fhir_data",
#             user="postgres",
#             password="1234"
#         )
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT type, value, date
#             FROM observation
#             WHERE patient_id = %s
#             ORDER BY date ASC
#         """, (str(patient_id),))
#         rows = cursor.fetchall()
#         conn.close()
#     except Exception as e:
#         print("Lỗi phân tích:", e)
#         raise HTTPException(status_code=500, detail=f"Lỗi kết nối DB: {e}")

#     grouped = defaultdict(list)
#     for obs_type, value, date in rows:
#         try:
#             val = float(str(value).replace("°C", "").strip())
#             grouped[obs_type].append(val)
#         except Exception as e:
#             print(f"Lỗi ép kiểu value: {value} → {e}")
#             continue

#     result = {}
#     for obs_type, values in grouped.items():
#         values = values[-6:]  # lấy 6 giá trị gần nhất
#         try:
#             trend = analyze_trend(values)
#             mean = round(statistics.mean(values), 2) if values else None
#             std_dev = round(statistics.stdev(values), 2) if len(values) > 1 else None
#             rolling = round(statistics.mean(values[-3:]), 2) if len(values) >= 3 else None
#         except Exception as e:
#             print(f"Lỗi phân tích {obs_type}: {e}")
#             trend, mean, std_dev, rolling = "Không thể phân tích", None, None, None

#         result[obs_type] = {
#             "trend": trend,
#             "mean": mean,
#             "std_dev": std_dev,
#             "latest_rolling_mean": rolling,
#             "data_points": len(values)
#         }

#     return result

@app.get("/api/observations/{patient_id}/analyze")
def analyze_observations(patient_id: str):
    raw_list = get_observations(patient_id)  # list[Observation]
    grouped = defaultdict(list)

    for obs in raw_list:
        try:
            # Observation.value có thể đã là float hoặc string
            v = float(obs.value)
            grouped[obs.type].append(v)
        except Exception as e:
            print(f"Bad obs.value {obs.value}: {e}")
            continue

    # phần tính toán hoàn toàn giống A)
    result = {}
    for obs_type, vals in grouped.items():
        last6 = vals[-6:]
        try:
            trend = analyze_trend(last6)
            mean = round(statistics.mean(last6), 2)
            std_dev = round(statistics.stdev(last6), 2) if len(last6)>1 else None
            rolling = round(statistics.mean(last6[-3:]), 2) if len(last6)>=3 else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        result[obs_type] = {
            "trend": trend,
            "mean": mean,
            "std_dev": std_dev,
            "latest_rolling_mean": rolling,
            "data_points": len(last6)
        }

    return result


