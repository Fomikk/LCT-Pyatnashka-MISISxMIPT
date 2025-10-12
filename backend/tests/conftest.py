# backend/tests/conftest.py
import sys
from pathlib import Path
import types
import pytest
from fastapi.testclient import TestClient
from fastapi import APIRouter

# Пути
BACKEND_ROOT = Path(__file__).resolve().parents[1]     # .../backend
PROJECT_ROOT = BACKEND_ROOT.parent                     # корень репозитория

# Добавляем в sys.path и backend, и корень проекта (чтобы импортировался ml)
for p in (str(BACKEND_ROOT), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Пытаемся импортировать приложение; если не найден 'ml', создаём мягкую заглушку
try:
    from app.main import app  # noqa: E402
except ModuleNotFoundError as e:
    if e.name == "ml" or e.name.startswith("ml."):
        # Заглушка модулей ml.api.service с пустым роутером
        ml_mod = types.ModuleType("ml")
        ml_api_mod = types.ModuleType("ml.api")
        ml_service_mod = types.ModuleType("ml.api.service")
        stub_router = APIRouter(prefix="/ml")
        setattr(ml_service_mod, "router", stub_router)

        sys.modules["ml"] = ml_mod
        sys.modules["ml.api"] = ml_api_mod
        sys.modules["ml.api.service"] = ml_service_mod

        from app.main import app  # noqa: E402
    else:
        raise


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def SAMPLE_PROFILE():
    return {
        "rows": 3,
        "columns": [
            {"name": "id", "dtype": "int64", "nullable": False},
            {"name": "name", "dtype": "object", "nullable": True},
        ],
        "is_time_series": False,
        "sample_data": [{"id": 1, "name": "Alex"}],
        "data_quality": {
            "completeness_score": 100.0,
            "consistency_score": 90.0,
            "uniqueness_score": 80.0,
            "issues": [],
        },
        "file_metadata": {
            "file_name": "example.csv",
            "file_size": 106,
            "file_extension": ".csv",
            "created_at": "2025-10-02T00:00:00",
            "modified_at": "2025-10-02T00:00:00",
        },
    }
