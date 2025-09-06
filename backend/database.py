from sqlalchemy import inspect
from dotenv import load_dotenv
from pathlib import Path
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from backend.base import Base  # Import Base từ base.py
import sys

'''
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Thêm thư mục cha vào sys.path
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:1234@localhost:5432/fhir_data"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)  # Tạo bảng nếu chưa có

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    try:
        with engine.connect() as conn:
            print("✅ Database connected successfully.")
    except Exception as e:
        print("❌ Database connection failed:", e)
        
'''

# Tự động nhận biết môi trường Render
is_render = os.getenv("RENDER") == "true"

# ✅ Load .env khi chạy local
if not is_render:
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path)

# ✅ Fallback: dùng biến môi trường hoặc chuỗi local
DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://postgres:1234@localhost:5432/fhir_data"

# ✅ Kiểm tra cú pháp
if not DATABASE_URL.startswith("postgresql://"):
    raise RuntimeError(f"❌ DATABASE_URL không hợp lệ: {repr(DATABASE_URL)}")

# ✅ In ra để kiểm tra
print("📦 DATABASE_URL =", repr(DATABASE_URL))

# ✅ Tạo engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# ✅ Session và Base
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ✅ Hàm tạo bảng
def init_db():
    Base.metadata.create_all(bind=engine)

# ✅ Dependency cho FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Kiểm tra kết nối khi chạy trực tiếp
if __name__ == "__main__":
    try:
        with engine.connect() as conn:
            print("✅ Database connected successfully.")
    except Exception as e:
        print("❌ Database connection failed:", e)
