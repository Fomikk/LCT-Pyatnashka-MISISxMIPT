from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator

# Пример DAG для тестирования
with DAG(
    dag_id='example_etl_dag',
    schedule='0 * * * *',  # каждый час
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['etl-ai-assistant', 'example']
):
    start = EmptyOperator(task_id='start')
    extract = EmptyOperator(task_id='extract')
    transform = EmptyOperator(task_id='transform')
    load = EmptyOperator(task_id='load')
    end = EmptyOperator(task_id='end')

    start >> extract >> transform >> load >> end
