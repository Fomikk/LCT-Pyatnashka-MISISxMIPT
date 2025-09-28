# ml/main.py
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Tuple, List

import pandas as pd


# ---------- UTILS ----------

def read_csv_robust(path: str, nrows: int = 100) -> pd.DataFrame:
    """Читаем CSV, пробуя разные кодировки/движки."""
    for enc in ("utf-8", "utf-8-sig", "cp1251", "latin1", "utf-16"):
        try:
            return pd.read_csv(path, nrows=nrows, encoding=enc)
        except UnicodeDecodeError:
            continue
        except pd.errors.ParserError:
            continue
    # последняя попытка — максимально терпимая
    return pd.read_csv(path, nrows=nrows, engine="python", encoding_errors="replace")


def read_json_robust(path: str, nrows: int = 100) -> pd.DataFrame:
    """
    Поддержка:
      - JSON Lines (по одной записи в строке)
      - Массив JSON-объектов
    """
    # 1) попробовать как jsonl (lines=True)
    try:
        df = pd.read_json(path, lines=True)
        if len(df):
            return df.head(nrows)
    except Exception:
        pass

    # 2) обычный JSON-массив
    for enc in ("utf-8-sig", "utf-8", "cp1251", "latin1"):
        try:
            with open(path, "r", encoding=enc) as f:
                data = json.load(f)
            break
        except Exception:
            data = None
        if data is None:
            raise ValueError("Не удалось прочитать JSON с типичными кодировками")
    if isinstance(data, list):
        return pd.DataFrame(data).head(nrows)
    elif isinstance(data, dict):
        # если словарь верхнего уровня — попробуем взять первый «большой» список
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return pd.DataFrame(v).head(nrows)
        # иначе попробуем расплющить словарь в одну строку
        return pd.json_normalize(data)
    else:
        raise ValueError("Неподдерживаемая структура JSON")


def read_xml_as_table(path: str, item_xpath: str = None, nrows: int = 100) -> pd.DataFrame:
    """
    Превращает XML в таблицу. Ищет повторяющийся тег-элемент (row/item),
    либо использует заданный item_xpath (например, './/row' или './/item').
    """
    tree = ET.parse(path)
    root = tree.getroot()

    if item_xpath:
        items = root.findall(item_xpath)
    else:
        # эвристика: берём самый частый тег среди детей (row, item, record и т.п.)
        tags: List[str] = [child.tag for child in root.iter() if len(child) and all(len(list(g)) == 0 for g in child)]
        # если tags пустой, fallback на прямых детей root
        if not tags:
            tags = [child.tag for child in root]
        # самый частый тег
        if not tags:
            raise ValueError("Не удалось определить повторяющийся элемент XML")
        # простая мода
        from collections import Counter
        common_tag, _ = Counter(tags).most_common(1)[0]
        items = root.findall(f".//{common_tag}")

    rows = []
    for el in items[:nrows]:
        row = {}
        # берём текст из простых дочерних элементов <col>value</col>
        for child in list(el):
            if len(list(child)) == 0:
                row[child.tag] = (child.text or "").strip()
        # если элементов нет — возможно значения в атрибутах
        if not row:
            for k, v in el.attrib.items():
                row[k] = v
        if row:
            rows.append(row)

    if not rows:
        # попытаемся расплющить как один объект
        return pd.json_normalize(_xml_to_dict(root))
    return pd.DataFrame(rows)


def _xml_to_dict(elem: ET.Element) -> dict:
    """Вспомогательно: грубая конвертация XML в dict."""
    d = {elem.tag: {} if elem.attrib else None}
    children = list(elem)
    if children:
        dd = {}
        for dc in map(_xml_to_dict, children):
            for k, v in dc.items():
                if k in dd:
                    if not isinstance(dd[k], list):
                        dd[k] = [dd[k]]
                    dd[k].append(v)
                else:
                    dd[k] = v
        d = {elem.tag: dd}
    if elem.attrib:
        d[elem.tag].update(('@' + k, v) for k, v in elem.attrib.items())
    if elem.text:
        text = elem.text.strip()
        if children or elem.attrib:
            if text:
                d[elem.tag]['#text'] = text
        else:
            d[elem.tag] = text
    return d


def pandas_dtype_to_sql(dtype: pd.api.extensions.ExtensionDtype | str) -> str:
    s = str(dtype).lower()
    if "int" in s:
        return "INT"
    if "float" in s or "double" in s:
        return "FLOAT"
    if "bool" in s:
        return "BOOLEAN"
    # простая эвристика по названию
    if re.search(r"date|time", s):
        return "TIMESTAMP"
    return "TEXT"


def infer_schema(df: pd.DataFrame) -> Dict[str, str]:
    """
    Инференс SQL-типов по значениям.
    Порядок: datetime -> numeric(int/float) -> boolean(по словам) -> TEXT.
    Порог распознавания — 0.8 (80% ненулевых значений).
    """
    schema: Dict[str, str] = {}

    def frac_ok(series: pd.Series) -> float:
        series = series.dropna()
        return 0.0 if series.empty else float(series.notna().mean())

    for col in df.columns:
        s = df[col]

        # не object — маппим напрямую
        if s.dtype != object:
            schema[col] = pandas_dtype_to_sql(s.dtype)
            continue

        # нормализация строк
        s_str = s.astype(str).str.strip()
        s_str = s_str.replace({"": None, "None": None, "nan": None})
        s_norm = s_str.str.replace(",", ".", regex=False)

        # 1) datetime (без устаревшего infer_datetime_format)
        # --- datetime распознавание ---
        # --- datetime распознавание ---
        sample = s_norm.dropna().astype(str).head(200)

        iso_ratio = sample.str.match(
            r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)?$"
        ).mean() if len(sample) else 0

        # русский формат: DD.MM.YYYY (с optional временем)
        dot_ratio = sample.str.match(
            r"^\d{2}\.\d{2}\.\d{4}(?: \d{2}:\d{2}:\d{2})?$"
        ).mean() if len(sample) else 0

        if iso_ratio >= 0.8:
            # ISO YYYY-MM-DD
            s_dt = pd.to_datetime(s_norm, errors="coerce", utc=False, format="%Y-%m-%d")
        elif dot_ratio >= 0.8:
            # Русский формат DD.MM.YYYY
            s_dt = pd.to_datetime(s_norm, errors="coerce", utc=False, format="%d.%m.%Y")
        else:
            # Смешанные форматы
            s_dt = pd.to_datetime(s_norm, errors="coerce", utc=False, format="mixed")

        if s_dt.notna().mean() >= 0.8:
            schema[col] = "TIMESTAMP"
            continue


        # 2) numeric: сначала пытаемся распарсить как число
        s_num = pd.to_numeric(s_norm, errors="coerce")
        if s_num.notna().mean() >= 0.8:
            # если все распарсенные — целые, то INT, иначе FLOAT
            if ((s_num.dropna() % 1) == 0).all():
                schema[col] = "INT"
            else:
                schema[col] = "FLOAT"
            continue

        # 3) boolean — ТОЛЬКО текстовые формы (не 0/1)
        bool_map = {
            "true": True, "false": False,
            "yes": True, "no": False,
            "y": True, "n": False
        }
        s_bool = s_norm.str.lower().map(bool_map)
        if frac_ok(s_bool) >= 0.8:
            schema[col] = "BOOLEAN"
            continue

        # 4) по умолчанию
        schema[col] = "TEXT"

    return schema


def generate_ddl(schema: Dict[str, str], table_name: str = "my_table") -> str:
    cols = ",\n  ".join(f"{name} {typ}" for name, typ in schema.items())
    return f"CREATE TABLE {table_name} (\n  {cols}\n);"


def recommend_storage(df: pd.DataFrame) -> str:
    """
    Простейшая рекомендация:
      - много строк/числовых колонок → ClickHouse,
      - иначе → PostgreSQL.
    """
    rows = len(df)
    num_cols = sum(pd.api.types.is_numeric_dtype(t) for t in df.dtypes)
    if rows > 1_000_000 or num_cols >= max(2, len(df.columns) // 2):
        return "ClickHouse"
    return "PostgreSQL"


# ---------- MAIN FLOWS ----------

def analyze_path(path: str, xml_xpath: str = None) -> Tuple[str, str]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    ext = p.suffix.lower()
    if ext == ".csv":
        df = read_csv_robust(path)
    elif ext in (".json", ".jsonl"):
        df = read_json_robust(path)
    elif ext == ".xml":
        df = read_xml_as_table(path, item_xpath=xml_xpath)
    else:
        raise ValueError(f"Неизвестное расширение: {ext}")

    schema = infer_schema(df)
    ddl = generate_ddl(schema, table_name=p.stem)
    storage = recommend_storage(df)
    return storage, ddl


def main():
    parser = argparse.ArgumentParser(
        description="Анализ входного файла (CSV/JSON/XML) → рекомендация хранилища + DDL"
    )
    parser.add_argument(
        "command",
        choices=["analyze"],
        help="Команда: analyze — проанализировать файл и вывести рекомендацию + DDL",
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Путь к входному файлу (CSV/JSON/JSONL/XML)",
    )
    parser.add_argument(
        "--xml-xpath",
        default=None,
        help="Опционально: XPath повторяющегося элемента для XML (например, .//row или .//item)",
    )
    args = parser.parse_args()

    if args.command == "analyze":
        try:
            storage, ddl = analyze_path(args.path, xml_xpath=args.xml_xpath)
        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)

        print(f"Рекомендуемое хранилище: {storage}")
        print("DDL:\n", ddl)


if __name__ == "__main__":
    main()
