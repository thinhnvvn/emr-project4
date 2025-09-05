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

sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Thêm thư mục cha vào sys.path

# DATABASE_URL = os.getenv("DATABASE_URL")
# if not DATABASE_URL:
#     raise ValueError("❌ DATABASE_URL is missing. Check your .env file!")  # Sửa ValueValue thành ValueError

# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine)

# ============== Good for local =========
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:1234@localhost:5432/fhir_data"

# engine = create_engine(SQLALCHEMY_DATABASE_URL)
# ================================================================

# ============= local và Render ==================
# ✅ Khai báo biến trước khi dùng
DATABASE_URL = os.getenv("DATABASE_URL")

# Tự động nhận biết môi trường
is_render = os.getenv("RENDER") == "true"

# Chỉ load .env khi chạy local
if not is_render:
    load_dotenv()

# Lấy DATABASE_URL từ môi trường
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL không được thiết lập")
print("📦 DATABASE_URL =", repr(DATABASE_URL))  # Thêm dòng này để kiểm tra

# Tạo engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# ==================================================


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

