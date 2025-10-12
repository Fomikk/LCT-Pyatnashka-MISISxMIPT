# ml/sources/loader.py
from __future__ import annotations
from pathlib import Path
from io import StringIO, BytesIO
from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET

def _jsonable_preview(df: pd.DataFrame, n=5):
    return df.replace([np.nan, np.inf, -np.inf], None).head(n).to_dict(orient="records")

def load_sample(source: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    source:
      {"type":"file","format":"csv|json|xml","path":"/abs/path"}
      {"type":"postgres","dsn":"...","query":"SELECT ... LIMIT 100"}
      {"type":"clickhouse","url":"http://...","query":"..."}
    """
    st = (source.get("type") or "").lower()
    if st == "file":
        path = Path(source["path"])
        fmt = (source.get("format") or path.suffix.lstrip(".")).lower()
        if fmt == "csv":
            # устойчивый CSV
            raw = path.read_bytes()
            for enc in ["utf-8-sig","utf-8","cp1251","windows-1251","latin1"]:
                try:
                    txt = raw.decode(enc, errors="ignore").replace("\x00", "")
                    buf = StringIO(txt)
                    try:
                        df = pd.read_csv(buf, sep=None, engine="python", on_bad_lines="skip")
                    except Exception:
                        buf.seek(0)
                        df = pd.read_csv(buf, sep=";", engine="python", on_bad_lines="skip")
                    return df, {"type":"file","format":"csv","name":path.name}
                except Exception:
                    continue
            raise ValueError("CSV read failed (encoding/separator)")
        elif fmt == "json":
            # JSON array / JSONL
            try:
                df = pd.read_json(path, lines=False)
            except ValueError:
                df = pd.read_json(path, lines=True)
            return df, {"type":"file","format":"json","name":path.name}
        elif fmt == "xml":
            # простая таблица из однотипных children
            root = ET.parse(path).getroot()
            rows = []
            for child in root:
                row = {elem.tag: elem.text for elem in child}
                rows.append(row)
            df = pd.DataFrame(rows)
            return df, {"type":"file","format":"xml","name":path.name}
        else:
            raise ValueError(f"Unsupported file format: {fmt}")

    elif st == "postgres":
        # интерфейс-заглушка для демо; реал коннект добьём позже
        # from sqlalchemy import create_engine; pd.read_sql(query, engine)
        return pd.DataFrame(), {"type":"postgres", "note":"not_implemented_in_mvp_loader"}

    elif st == "clickhouse":
        return pd.DataFrame(), {"type":"clickhouse", "note":"not_implemented_in_mvp_loader"}

    elif st == "hdfs":
        return pd.DataFrame(), {"type":"hdfs", "note":"not_implemented_in_mvp_loader"}

    else:
        raise ValueError(f"Unsupported source type: {st}")
