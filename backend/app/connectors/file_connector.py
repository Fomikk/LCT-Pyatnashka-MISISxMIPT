import pandas as pd
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from pathlib import Path
import io
import numpy as np
from loguru import logger
import asyncio
import aiofiles


class FileConnector:
    """Коннектор для работы с файловыми источниками данных"""
    
    @staticmethod
    async def read_csv(file_path: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        """Чтение CSV файла с расширенным анализом"""
        try:
            # Параметры подключения
            sep = connection.get("separator", ",")
            encoding = connection.get("encoding", "utf-8")
            header = connection.get("header", 0)
            
            # Чтение файла
            df = pd.read_csv(file_path, sep=sep, encoding=encoding, header=header)
            
            # Анализ структуры с дополнительной статистикой
            columns = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                nullable = df[col].isnull().any()
                example = df[col].iloc[0] if len(df) > 0 else None
                
                # Дополнительная статистика
                unique_count = df[col].nunique()
                null_count = df[col].isnull().sum()
                
                # Статистика для числовых колонок
                numeric_stats = {}
                if pd.api.types.is_numeric_dtype(df[col]):
                    numeric_stats = {
                        "min": float(df[col].min()) if not df[col].isnull().all() else None,
                        "max": float(df[col].max()) if not df[col].isnull().all() else None,
                        "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                        "std": float(df[col].std()) if not df[col].isnull().all() else None
                    }
                
                columns.append({
                    "name": col,
                    "dtype": dtype,
                    "nullable": nullable,
                    "example": example,
                    "unique_count": int(unique_count),
                    "null_count": int(null_count),
                    "null_percentage": float(null_count / len(df) * 100) if len(df) > 0 else 0.0,
                    "numeric_stats": numeric_stats
                })
            
            return {
                "rows": len(df),
                "columns": columns,
                "sample_data": df.head(5).to_dict("records"),
                "file_size": Path(file_path).stat().st_size
            }
        except Exception as e:
            logger.error(f"Error reading CSV {file_path}: {e}")
            raise
    
    @staticmethod
    async def read_json(file_path: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        """Чтение JSON файла с расширенным анализом"""
        try:
            encoding = connection.get("encoding", "utf-8")
            
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
            
            # Анализ структуры JSON
            if isinstance(data, list) and len(data) > 0:
                # Массив объектов
                sample = data[0]
                columns = []
                
                # Анализируем все объекты для получения полной статистики
                all_keys = set()
                for item in data:
                    if isinstance(item, dict):
                        all_keys.update(item.keys())
                
                for key in all_keys:
                    # Собираем все значения для этого ключа
                    values = [item.get(key) for item in data if isinstance(item, dict)]
                    non_null_values = [v for v in values if v is not None]
                    
                    # Определяем тип на основе всех значений
                    if non_null_values:
                        dtype = type(non_null_values[0]).__name__
                        # Если есть разные типы, используем 'mixed'
                        if len(set(type(v).__name__ for v in non_null_values)) > 1:
                            dtype = 'mixed'
                    else:
                        dtype = 'null'
                    
                    # Статистика
                    null_count = sum(1 for v in values if v is None)
                    unique_count = len(set(str(v) for v in non_null_values)) if non_null_values else 0
                    
                    columns.append({
                        "name": key,
                        "dtype": dtype,
                        "nullable": null_count > 0,
                        "example": non_null_values[0] if non_null_values else None,
                        "unique_count": int(unique_count),
                        "null_count": int(null_count),
                        "null_percentage": float(null_count / len(values) * 100) if values else 0.0
                    })
                
                return {
                    "rows": len(data),
                    "columns": columns,
                    "sample_data": data[:5],
                    "file_size": Path(file_path).stat().st_size
                }
            else:
                # Одиночный объект
                columns = []
                for key, value in data.items():
                    dtype = type(value).__name__
                    columns.append({
                        "name": key,
                        "dtype": dtype,
                        "nullable": value is None,
                        "example": value,
                        "unique_count": 1,
                        "null_count": 1 if value is None else 0,
                        "null_percentage": 100.0 if value is None else 0.0
                    })
                
                return {
                    "rows": 1,
                    "columns": columns,
                    "sample_data": [data],
                    "file_size": Path(file_path).stat().st_size
                }
        except Exception as e:
            logger.error(f"Error reading JSON {file_path}: {e}")
            raise
    
    @staticmethod
    async def read_xml(file_path: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        """Чтение XML файла"""
        try:
            encoding = connection.get("encoding", "utf-8")
            root_element = connection.get("root_element", None)
            
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Если указан корневой элемент, ищем его
            if root_element:
                elements = root.findall(f".//{root_element}")
            else:
                # Пытаемся найти повторяющиеся элементы
                elements = []
                for child in root:
                    if len(child) > 0:  # Элемент с дочерними элементами
                        elements.append(child)
                        break
            
            if not elements:
                # Если не нашли повторяющиеся элементы, используем корень
                elements = [root]
            
            # Анализ структуры первого элемента
            sample = elements[0]
            columns = []
            
            def extract_attributes_and_text(element, prefix=""):
                attrs = []
                for key, value in element.attrib.items():
                    attrs.append({
                        "name": f"{prefix}@{key}" if prefix else key,
                        "dtype": "string",
                        "nullable": value is None,
                        "example": value
                    })
                
                if element.text and element.text.strip():
                    attrs.append({
                        "name": f"{prefix}@text" if prefix else "text",
                        "dtype": "string",
                        "nullable": False,
                        "example": element.text.strip()
                    })
                
                for child in element:
                    attrs.extend(extract_attributes_and_text(child, f"{prefix}{child.tag}."))
                
                return attrs
            
            columns = extract_attributes_and_text(sample)
            
            # Создаем примеры данных
            sample_data = []
            for elem in elements[:5]:
                def element_to_dict(element, prefix=""):
                    result = {}
                    for key, value in element.attrib.items():
                        result[f"{prefix}@{key}" if prefix else key] = value
                    
                    if element.text and element.text.strip():
                        result[f"{prefix}@text" if prefix else "text"] = element.text.strip()
                    
                    for child in element:
                        result.update(element_to_dict(child, f"{prefix}{child.tag}."))
                    
                    return result
                
                sample_data.append(element_to_dict(elem))
            
            return {
                "rows": len(elements),
                "columns": columns,
                "sample_data": sample_data
            }
        except Exception as e:
            logger.error(f"Error reading XML {file_path}: {e}")
            raise
    
    @staticmethod
    async def read_excel(file_path: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        """Чтение Excel файла"""
        try:
            sheet_name = connection.get("sheet_name", 0)
            header = connection.get("header", 0)
            
            # Читаем Excel файл
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=header)
            
            # Анализ структуры
            columns = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                nullable = df[col].isnull().any()
                example = df[col].iloc[0] if len(df) > 0 else None
                
                # Дополнительная статистика
                unique_count = df[col].nunique()
                null_count = df[col].isnull().sum()
                
                columns.append({
                    "name": col,
                    "dtype": dtype,
                    "nullable": nullable,
                    "example": example,
                    "unique_count": int(unique_count),
                    "null_count": int(null_count),
                    "null_percentage": float(null_count / len(df) * 100) if len(df) > 0 else 0.0
                })
            
            return {
                "rows": len(df),
                "columns": columns,
                "sample_data": df.head(5).to_dict("records"),
                "file_size": Path(file_path).stat().st_size
            }
        except Exception as e:
            logger.error(f"Error reading Excel {file_path}: {e}")
            raise

    @staticmethod
    async def read_parquet(file_path: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        """Чтение Parquet файла"""
        try:
            # Читаем Parquet файл
            df = pd.read_parquet(file_path)
            
            # Анализ структуры
            columns = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                nullable = df[col].isnull().any()
                example = df[col].iloc[0] if len(df) > 0 else None
                
                # Дополнительная статистика
                unique_count = df[col].nunique()
                null_count = df[col].isnull().sum()
                
                columns.append({
                    "name": col,
                    "dtype": dtype,
                    "nullable": nullable,
                    "example": example,
                    "unique_count": int(unique_count),
                    "null_count": int(null_count),
                    "null_percentage": float(null_count / len(df) * 100) if len(df) > 0 else 0.0
                })
            
            return {
                "rows": len(df),
                "columns": columns,
                "sample_data": df.head(5).to_dict("records"),
                "file_size": Path(file_path).stat().st_size
            }
        except Exception as e:
            logger.error(f"Error reading Parquet {file_path}: {e}")
            raise

    @staticmethod
    async def detect_file_type(file_path: str) -> str:
        """Автоматическое определение типа файла"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        type_mapping = {
            '.csv': 'csv',
            '.json': 'json',
            '.xml': 'xml',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.parquet': 'parquet',
            '.pq': 'parquet'
        }
        
        return type_mapping.get(suffix, 'unknown')

    @staticmethod
    async def get_file_metadata(file_path: str) -> Dict[str, Any]:
        """Получение метаданных файла"""
        try:
            path = Path(file_path)
            stat = path.stat()
            
            return {
                "file_name": path.name,
                "file_size": stat.st_size,
                "file_extension": path.suffix.lower(),
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "is_readable": path.is_file() and path.stat().st_mode & 0o444
            }
        except Exception as e:
            logger.error(f"Error getting file metadata {file_path}: {e}")
            return {}

    @staticmethod
    async def analyze_file(file_path: str, file_type: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ файла по типу с расширенной информацией"""
        try:
            # Получаем метаданные файла
            metadata = await FileConnector.get_file_metadata(file_path)
            
            # Автоопределение типа если не указан
            if file_type.lower() == "auto":
                file_type = await FileConnector.detect_file_type(file_path)
            
            # Читаем данные в зависимости от типа
            if file_type.lower() == "csv":
                data = await FileConnector.read_csv(file_path, connection)
            elif file_type.lower() == "json":
                data = await FileConnector.read_json(file_path, connection)
            elif file_type.lower() == "xml":
                data = await FileConnector.read_xml(file_path, connection)
            elif file_type.lower() in ["excel", "xlsx", "xls"]:
                data = await FileConnector.read_excel(file_path, connection)
            elif file_type.lower() in ["parquet", "pq"]:
                data = await FileConnector.read_parquet(file_path, connection)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Добавляем метаданные
            data.update(metadata)
            
            # Дополнительный анализ качества данных
            data["data_quality"] = await FileConnector._analyze_data_quality(data)
            
            return data
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            raise

    @staticmethod
    async def _analyze_data_quality(data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ качества данных"""
        try:
            columns = data.get("columns", [])
            total_rows = data.get("rows", 0)
            
            quality_metrics = {
                "completeness_score": 0.0,
                "consistency_score": 0.0,
                "uniqueness_score": 0.0,
                "issues": []
            }
            
            if total_rows == 0:
                quality_metrics["issues"].append("Файл пустой")
                return quality_metrics
            
            # Анализ полноты данных
            null_percentages = [col.get("null_percentage", 0) for col in columns]
            avg_null_percentage = sum(null_percentages) / len(null_percentages) if null_percentages else 0
            quality_metrics["completeness_score"] = max(0, 100 - avg_null_percentage)
            
            # Анализ уникальности
            unique_ratios = []
            for col in columns:
                unique_count = col.get("unique_count", 0)
                if total_rows > 0:
                    unique_ratio = unique_count / total_rows
                    unique_ratios.append(unique_ratio)
            
            if unique_ratios:
                avg_unique_ratio = sum(unique_ratios) / len(unique_ratios)
                quality_metrics["uniqueness_score"] = min(100, avg_unique_ratio * 100)
            
            # Поиск потенциальных проблем
            for col in columns:
                null_pct = col.get("null_percentage", 0)
                if null_pct > 50:
                    quality_metrics["issues"].append(f"Колонка '{col['name']}' содержит {null_pct:.1f}% пустых значений")
                
                if col.get("unique_count", 0) == total_rows and total_rows > 1:
                    quality_metrics["issues"].append(f"Колонка '{col['name']}' содержит только уникальные значения (возможно ID)")
            
            # Общая оценка консистентности
            if len(quality_metrics["issues"]) == 0:
                quality_metrics["consistency_score"] = 100.0
            else:
                quality_metrics["consistency_score"] = max(0, 100 - len(quality_metrics["issues"]) * 10)
            
            return quality_metrics
        except Exception as e:
            logger.error(f"Error analyzing data quality: {e}")
            return {"completeness_score": 0, "consistency_score": 0, "uniqueness_score": 0, "issues": ["Ошибка анализа качества данных"]}
