# backend/app/connectors/file_connector.py
from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import asyncio
import math
import pandas as pd
from loguru import logger

# chardet опционален — но очень желателен; без него падаем на utf-8
try:
    import chardet  # type: ignore
except Exception:  # pragma: no cover
    chardet = None


# --------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---------

def _detect_encoding(path: Path, sample_size: int = 200_000) -> str:
    if chardet is None:
        return "utf-8"
    try:
        with open(path, "rb") as f:
            raw = f.read(sample_size)
        det = chardet.detect(raw or b"")
        enc = (det.get("encoding") or "utf-8").lower()
        return "utf-8" if enc in {"ascii", "none"} else enc
    except Exception:
        return "utf-8"


def _detect_delimiter(text_sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(text_sample, delimiters=";,|\t,")
        return dialect.delimiter
    except Exception:
        # простая эвристика: выбираем самый частый из популярных
        candidates = [",", ";", "\t", "|"]
        counts = {d: text_sample.count(d) for d in candidates}
        # если все нули — по умолчанию запятая
        return max(counts, key=counts.get) if any(counts.values()) else ","


def _file_times_iso(stat) -> Dict[str, str]:
    try:
        created = getattr(stat, "st_ctime", stat.st_mtime)
        modified = stat.st_mtime
        return {
            "created_at": datetime.fromtimestamp(created).isoformat(),
            "modified_at": datetime.fromtimestamp(modified).isoformat(),
        }
    except Exception:
        now = datetime.now().isoformat()
        return {"created_at": now, "modified_at": now}


# --------- ОСНОВНОЙ КЛАСС КОННЕКТОРА ---------

class FileConnector:
    """Коннектор для работы с файловыми источниками данных (устойчивый)"""

    # ================== ПУБЛИЧНЫЕ МЕТОДЫ ==================

    @staticmethod
    async def read_csv(file_path: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Чтение CSV/TSV с авто-детектом encoding/sep (если не указаны).
        Параметры в connection:
          - separator (str | 'auto') — разделитель
          - encoding (str | 'auto')  — кодировка
          - header (int | None)      — номер строки заголовка (по умолчанию 0)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {path}")

        sep_cfg = (connection or {}).get("separator", "auto")
        enc_cfg = (connection or {}).get("encoding", "auto")
        header = (connection or {}).get("header", 0)

        encoding = _detect_encoding(path) if enc_cfg in (None, "", "auto") else enc_cfg

        # для детекции разделителя читаем небольшой сэмпл
        try:
            with open(path, "r", encoding=encoding, errors="replace") as f:
                sample = f.read(50_000)
        except UnicodeError:
            # если не получилось с выбранной кодировкой — падаем на utf-8
            encoding = "utf-8"
            with open(path, "r", encoding=encoding, errors="replace") as f:
                sample = f.read(50_000)

        sep = _detect_delimiter(sample) if sep_cfg in (None, "", "auto") else sep_cfg

        def _read() -> pd.DataFrame:
            return pd.read_csv(path, sep=sep, encoding=encoding, engine="python", header=header)

        df = await asyncio.to_thread(_read)
        return _dataframe_to_meta(path, df)

    @staticmethod
    async def read_json(file_path: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Чтение JSON (массив объектов, одиночный объект или JSON Lines).
        Параметры: encoding
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {path}")

        enc_cfg = (connection or {}).get("encoding", "auto")
        encoding = _detect_encoding(path) if enc_cfg in (None, "", "auto") else enc_cfg

        def _read() -> pd.DataFrame:
            # Пытаемся JSON Lines
            try:
                return pd.read_json(path, lines=True, encoding=encoding)
            except Exception:
                pass
            # Пытаемся обычный JSON (массив/объект)
            obj = json.loads(path.read_text(encoding=encoding, errors="replace"))
            if isinstance(obj, list):
                return pd.json_normalize(obj)
            elif isinstance(obj, dict):
                return pd.json_normalize([obj])
            else:
                raise ValueError("Поддерживаются JSON-объект или массив объектов, либо JSON Lines")

        df = await asyncio.to_thread(_read)
        return _dataframe_to_meta(path, df)

    @staticmethod
    async def read_xml(file_path: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Простой XML → таблица: берём самый часто повторяющийся не-корневой тег.
        Параметры: encoding (опционально), root_element (опционально)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {path}")

        enc_cfg = (connection or {}).get("encoding", "auto")
        root_element = (connection or {}).get("root_element")
        encoding = _detect_encoding(path) if enc_cfg in (None, "", "auto") else enc_cfg

        def _read() -> pd.DataFrame:
            text = path.read_text(encoding=encoding, errors="replace")
            root = ET.fromstring(text)

            # если явно задан root_element — берём его повторы
            if root_element:
                elems = list(root.iter(root_element))
            else:
                # считаем частоты тегов и берём самый частый не-корневой
                counts: Dict[str, int] = {}
                for el in root.iter():
                    counts[el.tag] = counts.get(el.tag, 0) + 1
                tag = max((t for t in counts if t != root.tag), key=lambda t: counts[t], default=None)
                elems = list(root.iter(tag)) if tag else [root]

            rows: List[Dict[str, Any]] = []
            for e in elems:
                row: Dict[str, Any] = {}
                # атрибуты
                for k, v in e.attrib.items():
                    row[f"@{k}"] = v
                # текст
                if e.text and e.text.strip():
                    row["#text"] = e.text.strip()
                # дочерние элементы (плоско)
                for ch in e:
                    key = ch.tag
                    val = (ch.text or "").strip() if (ch.text and ch.text.strip()) else None
                    # если повторяются — нумеруем
                    if key in row:
                        i = 2
                        while f"{key}_{i}" in row:
                            i += 1
                        key = f"{key}_{i}"
                    row[key] = val
                rows.append(row)
            return pd.DataFrame(rows)

        df = await asyncio.to_thread(_read)
        return _dataframe_to_meta(path, df)

    @staticmethod
    async def read_excel(file_path: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Чтение Excel (требует openpyxl).
        Параметры: sheet_name (по умолчанию 0), header (по умолчанию 0)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {path}")

        sheet_name = (connection or {}).get("sheet_name", 0)
        header = (connection or {}).get("header", 0)

        def _read() -> pd.DataFrame:
            return pd.read_excel(path, sheet_name=sheet_name, header=header, engine="openpyxl")

        df = await asyncio.to_thread(_read)
        return _dataframe_to_meta(path, df)

    @staticmethod
    async def read_parquet(file_path: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        """Чтение Parquet (pyarrow/fastparquet)."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {path}")

        def _read() -> pd.DataFrame:
            return pd.read_parquet(path)

        df = await asyncio.to_thread(_read)
        return _dataframe_to_meta(path, df)

    @staticmethod
    async def detect_file_type(file_path: str) -> str:
        """Автоматическое определение типа файла по расширению."""
        suffix = Path(file_path).suffix.lower()
        return {
            ".csv": "csv",
            ".tsv": "csv",
            ".json": "json",
            ".xml": "xml",
            ".xlsx": "excel",
            ".xls": "excel",
            ".parquet": "parquet",
            ".pq": "parquet",
        }.get(suffix, "unknown")

    @staticmethod
    async def get_file_metadata(file_path: str) -> Dict[str, Any]:
        """Метаданные файла с ISO-временем."""
        try:
            p = Path(file_path)
            st = p.stat()
            times = _file_times_iso(st)
            meta = {
                "file_name": p.name,
                "file_size": st.st_size,
                "file_extension": p.suffix.lower(),
                **times,
                "is_readable": p.is_file(),
            }
            return meta
        except Exception as e:
            logger.error(f"Error getting file metadata {file_path}: {e}")
            now = datetime.now().isoformat()
            return {
                "file_name": Path(file_path).name,
                "file_size": 0,
                "file_extension": Path(file_path).suffix.lower(),
                "created_at": now,
                "modified_at": now,
                "is_readable": False,
            }

    @staticmethod
    async def analyze_file(file_path: str, file_type: str, connection: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Унифицированная точка входа.
        Возвращает структуру:
          rows, columns, sample_data, data_quality,
          file_name, file_size, file_extension, created_at, modified_at,
          file_metadata (dict с теми же полями)
        """
        try:
            connection = connection or {}
            meta = await FileConnector.get_file_metadata(file_path)
            ft = (file_type or "auto").lower()

            if ft == "auto" or ft == "unknown":
                ft = await FileConnector.detect_file_type(file_path)

            if ft == "csv":
                data = await FileConnector.read_csv(file_path, connection)
            elif ft == "json":
                data = await FileConnector.read_json(file_path, connection)
            elif ft == "xml":
                data = await FileConnector.read_xml(file_path, connection)
            elif ft in {"excel", "xlsx", "xls"}:
                data = await FileConnector.read_excel(file_path, connection)
            elif ft in {"parquet", "pq"}:
                data = await FileConnector.read_parquet(file_path, connection)
            else:
                raise ValueError(f"Unsupported file type: {ft}")

            # дополним плоскими метаданными (для совместимости с analysis_service)
            data.update({
                "file_name": meta.get("file_name"),
                "file_size": meta.get("file_size"),
                "file_extension": meta.get("file_extension"),
                "created_at": meta.get("created_at"),
                "modified_at": meta.get("modified_at"),
                "file_metadata": meta,
            })

            # базовая оценка качества
            data["data_quality"] = await FileConnector._analyze_data_quality(data)
            return data

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            raise

    # ================== ВНУТРЕННЕЕ КАЧЕСТВО ДАННЫХ ==================

    @staticmethod
    async def _analyze_data_quality(data: Dict[str, Any]) -> Dict[str, Any]:
        """Простая оценка качества данных по null-ам и уникальности."""
        try:
            columns = data.get("columns", [])
            total_rows = int(data.get("rows", 0))

            if total_rows <= 0 or not columns:
                return {
                    "completeness_score": 0.0,
                    "consistency_score": 0.0,
                    "uniqueness_score": 0.0,
                    "issues": ["Файл пустой или не распознан"],
                }

            null_pcts = [float(c.get("null_percentage", 0.0) or 0.0) for c in columns]
            avg_null = sum(null_pcts) / max(len(null_pcts), 1)
            completeness = max(0.0, 100.0 - avg_null)

            uniq_scores: List[float] = []
            for c in columns:
                uc = int(c.get("unique_count", 0) or 0)
                uniq_scores.append(min(100.0, (uc / total_rows) * 100.0) if total_rows else 0.0)
            uniqueness = sum(uniq_scores) / max(len(uniq_scores), 1)

            issues: List[str] = []
            for c in columns:
                null_pct = float(c.get("null_percentage", 0.0) or 0.0)
                if null_pct > 50.0:
                    issues.append(f"Колонка '{c.get('name')}' содержит {null_pct:.1f}% пустых значений")
                if int(c.get("unique_count", 0) or 0) == total_rows and total_rows > 1:
                    issues.append(f"Колонка '{c.get('name')}' содержит только уникальные значения (возможно ID)")

            consistency = 100.0 if not issues else max(0.0, 100.0 - len(issues) * 10.0)

            return {
                "completeness_score": completeness,
                "consistency_score": consistency,
                "uniqueness_score": uniqueness,
                "issues": issues,
            }
        except Exception as e:
            logger.error(f"Error analyzing data quality: {e}")
            return {
                "completeness_score": 0.0,
                "consistency_score": 0.0,
                "uniqueness_score": 0.0,
                "issues": ["Ошибка анализа качества данных"],
            }


# --------- ПРИВАТНЫЕ ПОМОЩНИКИ ---------

def _dataframe_to_meta(path: Path, df: pd.DataFrame) -> Dict[str, Any]:
    """Преобразовать DataFrame в структуру meta, ожидаемую сервисом анализа."""
    rows = int(len(df))
    cols: List[Dict[str, Any]] = []

    for col in df.columns:
        s = df[col]
        dtype = str(s.dtype)
        null_count = int(s.isna().sum())
        unique_count = int(s.nunique(dropna=True))
        # пример значения
        example = None
        for v in s.head(10):
            if pd.notna(v):
                example = v
                break

        numeric_stats = None
        if pd.api.types.is_numeric_dtype(s):
            desc = s.describe(percentiles=[0.25, 0.5, 0.75])
            numeric_stats = {
                "min": _to_num(desc.get("min")),
                "max": _to_num(desc.get("max")),
                "mean": _to_num(desc.get("mean")),
                "p25": _to_num(desc.get("25%")),
                "p50": _to_num(desc.get("50%")),
                "p75": _to_num(desc.get("75%")),
            }

        cols.append({
            "name": str(col),
            "dtype": dtype,
            "nullable": bool(null_count > 0),
            "example": None if pd.isna(example) else example,
            "unique_count": unique_count,
            "null_count": null_count,
            "null_percentage": float(null_count) / rows * 100 if rows else 0.0,
            "numeric_stats": numeric_stats,
        })

    sample_head = df.head(5).where(pd.notna(df.head(5)), None)
    sample_data = sample_head.to_dict(orient="records")
    return {
        "rows": rows,
        "columns": cols,
        "sample_data": sample_data,
        "file_size": path.stat().st_size if path.exists() else 0,
    }


def _to_num(x):
    try:
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except Exception:
        return None
