"""
Сервис для интеграции с LLM (Large Language Models)
Поддерживает OpenAI, Anthropic и другие провайдеры
"""
import httpx
import json
from typing import Dict, Any, Optional, List
from app.core.config import settings
from loguru import logger
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential


class LLMService:
    """Сервис для работы с LLM"""
    
    def __init__(self):
        self.base_url = settings.llm_base_url
        self.timeout = 30.0
        self.max_retries = 3
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение HTTP запроса к LLM сервису"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/{endpoint}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error(f"LLM request timeout for {endpoint}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM request failed with status {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"LLM request error: {e}")
            raise
    
    async def analyze_data_structure(self, data_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ структуры данных с помощью LLM"""
        prompt = f"""
        Проанализируй следующую структуру данных и предоставь рекомендации:
        
        Количество строк: {data_profile.get('rows', 0)}
        Колонки: {json.dumps(data_profile.get('columns', []), ensure_ascii=False, indent=2)}
        Временной ряд: {data_profile.get('is_time_series', False)}
        
        Пожалуйста, предоставь:
        1. Анализ качества данных
        2. Рекомендации по оптимизации схемы
        3. Предложения по индексации
        4. Оценку пригодности для различных типов запросов
        """
        
        payload = {
            "prompt": prompt,
            "max_tokens": 1000,
            "temperature": 0.3
        }
        
        try:
            result = await self._make_request("analyze", payload)
            return {
                "analysis": result.get("response", ""),
                "confidence": result.get("confidence", 0.8),
                "recommendations": self._extract_recommendations(result.get("response", ""))
            }
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {
                "analysis": "Анализ недоступен",
                "confidence": 0.0,
                "recommendations": []
            }
    
    async def generate_ddl_recommendations(self, table_info: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация рекомендаций по DDL с помощью LLM"""
        prompt = f"""
        Создай оптимальную схему базы данных для следующих данных:
        
        Таблица: {table_info.get('table_name', 'unknown')}
        СУБД: {table_info.get('target_system', 'postgres')}
        Колонки: {json.dumps(table_info.get('columns', []), ensure_ascii=False, indent=2)}
        
        Учти:
        1. Производительность запросов
        2. Эффективность хранения
        3. Масштабируемость
        4. Лучшие практики для {table_info.get('target_system', 'postgres')}
        
        Предоставь DDL с комментариями и объяснениями.
        """
        
        payload = {
            "prompt": prompt,
            "max_tokens": 1500,
            "temperature": 0.2
        }
        
        try:
            result = await self._make_request("generate_ddl", payload)
            return {
                "ddl": result.get("response", ""),
                "explanations": self._extract_explanations(result.get("response", "")),
                "optimization_tips": self._extract_optimization_tips(result.get("response", ""))
            }
        except Exception as e:
            logger.error(f"LLM DDL generation failed: {e}")
            return {
                "ddl": "-- LLM недоступен",
                "explanations": [],
                "optimization_tips": []
            }
    
    async def recommend_storage_strategy(self, workload_info: Dict[str, Any]) -> Dict[str, Any]:
        """Рекомендации по стратегии хранения данных"""
        prompt = f"""
        Рекомендуй оптимальную стратегию хранения для следующих требований:
        
        Тип нагрузки: {workload_info.get('workload', 'analytical')}
        SLA задержки: {workload_info.get('latency_sla_seconds', 'не указано')} секунд
        Объем данных: {workload_info.get('data_volume', 'не указано')}
        Частота обновления: {workload_info.get('update_frequency', 'не указано')}
        
        Рассмотри варианты:
        1. PostgreSQL для оперативных данных
        2. ClickHouse для аналитики
        3. HDFS для больших данных
        4. Гибридные решения
        
        Предоставь обоснование выбора.
        """
        
        payload = {
            "prompt": prompt,
            "max_tokens": 1200,
            "temperature": 0.4
        }
        
        try:
            result = await self._make_request("recommend_storage", payload)
            return {
                "recommendation": result.get("response", ""),
                "storage_type": self._extract_storage_type(result.get("response", "")),
                "rationale": self._extract_rationale(result.get("response", ""))
            }
        except Exception as e:
            logger.error(f"LLM storage recommendation failed: {e}")
            return {
                "recommendation": "Рекомендация недоступна",
                "storage_type": "postgres",
                "rationale": "Fallback решение"
            }
    
    async def generate_pipeline_code(self, pipeline_info: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация кода пайплайна с помощью LLM"""
        prompt = f"""
        Создай код ETL пайплайна для следующих требований:
        
        Источник: {pipeline_info.get('source', {})}
        Назначение: {pipeline_info.get('destination', {})}
        Расписание: {pipeline_info.get('schedule', '0 * * * *')}
        Трансформации: {pipeline_info.get('transformations', [])}
        
        Используй Airflow и Python. Включи:
        1. Обработку ошибок
        2. Логирование
        3. Мониторинг
        4. Валидацию данных
        """
        
        payload = {
            "prompt": prompt,
            "max_tokens": 2000,
            "temperature": 0.3
        }
        
        try:
            result = await self._make_request("generate_pipeline", payload)
            return {
                "code": result.get("response", ""),
                "dependencies": self._extract_dependencies(result.get("response", "")),
                "configuration": self._extract_configuration(result.get("response", ""))
            }
        except Exception as e:
            logger.error(f"LLM pipeline generation failed: {e}")
            return {
                "code": "# LLM недоступен",
                "dependencies": [],
                "configuration": {}
            }
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Извлечение рекомендаций из текста LLM"""
        recommendations = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['рекоменд', 'совет', 'следует', 'лучше']):
                recommendations.append(line.strip())
        return recommendations[:5]  # Максимум 5 рекомендаций
    
    def _extract_explanations(self, text: str) -> List[str]:
        """Извлечение объяснений из текста LLM"""
        explanations = []
        lines = text.split('\n')
        for line in lines:
            if line.strip().startswith('--') or line.strip().startswith('#'):
                explanations.append(line.strip())
        return explanations
    
    def _extract_optimization_tips(self, text: str) -> List[str]:
        """Извлечение советов по оптимизации"""
        tips = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['оптимиз', 'производитель', 'индекс', 'партиц']):
                tips.append(line.strip())
        return tips[:3]
    
    def _extract_storage_type(self, text: str) -> str:
        """Извлечение типа хранилища из рекомендации"""
        text_lower = text.lower()
        if 'clickhouse' in text_lower:
            return 'clickhouse'
        elif 'postgres' in text_lower:
            return 'postgres'
        elif 'hdfs' in text_lower:
            return 'hdfs'
        else:
            return 'postgres'
    
    def _extract_rationale(self, text: str) -> str:
        """Извлечение обоснования выбора"""
        # Простое извлечение - берем первые 200 символов
        return text[:200] + "..." if len(text) > 200 else text
    
    def _extract_dependencies(self, code: str) -> List[str]:
        """Извлечение зависимостей из кода"""
        dependencies = []
        lines = code.split('\n')
        for line in lines:
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                dependencies.append(line.strip())
        return dependencies[:10]  # Максимум 10 зависимостей
    
    def _extract_configuration(self, code: str) -> Dict[str, Any]:
        """Извлечение конфигурации из кода"""
        config = {}
        lines = code.split('\n')
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                try:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"\'')
                except:
                    pass
        return config


# Глобальный экземпляр сервиса
llm_service = LLMService()
