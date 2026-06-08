import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
APP_NAME = os.getenv("APP_NAME", "ระบบจัดการของครูเตอร์")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./storage/app.db")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "tjter")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "tjter08")
STRICT_CURRICULUM_MODE = os.getenv("STRICT_CURRICULUM_MODE", "true").lower() == "true"

STORAGE_DIR = BASE_DIR / "storage"
GENERATED_DIR = STORAGE_DIR / "generated"
CURRICULUM_DIR = STORAGE_DIR / "curriculums"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
CURRICULUM_DIR.mkdir(parents=True, exist_ok=True)
