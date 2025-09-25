import pandas as pd
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from pathlib import Path
import io
from loguru import logger


class FileConnector:
    """Коннектор для работы с файловыми источниками данных"""
    
    @staticmethod
    async def read_csv(file_path: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        """Чтение CSV файла"""
        try:
            # Параметры подключения
            sep = connection.get("separator", ",")
            encoding = connection.get("encoding", "utf-8")
            header = connection.get("header", 0)
            
            # Чтение файла
            df = pd.read_csv(file_path, sep=sep, encoding=encoding, header=header)
            
            # Анализ структуры
            columns = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                nullable = df[col].isnull().any()
                example = df[col].iloc[0] if len(df) > 0 else None
                
                columns.append({
                    "name": col,
                    "dtype": dtype,
                    "nullable": nullable,
                    "example": example
                })
            
            return {
                "rows": len(df),
                "columns": columns,
                "sample_data": df.head(5).to_dict("records")
            }
        except Exception as e:
            logger.error(f"Error reading CSV {file_path}: {e}")
            raise
    
    @staticmethod
    async def read_json(file_path: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        """Чтение JSON файла"""
        try:
            encoding = connection.get("encoding", "utf-8")
            
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
            
            # Анализ структуры JSON
            if isinstance(data, list) and len(data) > 0:
                # Массив объектов
                sample = data[0]
                columns = []
                for key, value in sample.items():
                    dtype = type(value).__name__
                    columns.append({
                        "name": key,
                        "dtype": dtype,
                        "nullable": value is None,
                        "example": value
                    })
                
                return {
                    "rows": len(data),
                    "columns": columns,
                    "sample_data": data[:5]
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
                        "example": value
                    })
                
                return {
                    "rows": 1,
                    "columns": columns,
                    "sample_data": [data]
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
    async def analyze_file(file_path: str, file_type: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ файла по типу"""
        if file_type.lower() == "csv":
            return await FileConnector.read_csv(file_path, connection)
        elif file_type.lower() == "json":
            return await FileConnector.read_json(file_path, connection)
        elif file_type.lower() == "xml":
            return await FileConnector.read_xml(file_path, connection)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
