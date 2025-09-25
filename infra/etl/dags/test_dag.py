from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def hello_world():
    print("Airflow работает!")

with DAG(
    dag_id="test_dag",
    start_date=datetime(2025, 9, 25),
    schedule_interval="@once",
    catchup=False
) as dag:
    task = PythonOperator(
        task_id="hello",
        python_callable=hello_world
    )