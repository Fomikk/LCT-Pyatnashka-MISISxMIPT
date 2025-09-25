import pandas as pd

def analyze_csv(path: str):
    df = pd.read_csv(path, nrows=100)  # читаем первые строки
    info = df.dtypes.to_dict()

    # простая логика выбора БД
    if len(df) > 1_000_000:
        storage = "ClickHouse"
    else:
        storage = "PostgreSQL"

    # генерация DDL
    ddl = "CREATE TABLE my_table (\n"
    for col, dtype in info.items():
        if "int" in str(dtype):
            sql_type = "INT"
        elif "float" in str(dtype):
            sql_type = "FLOAT"
        elif "datetime" in str(dtype):
            sql_type = "TIMESTAMP"
        else:
            sql_type = "TEXT"
        ddl += f"  {col} {sql_type},\n"
    ddl = ddl.rstrip(",\n") + "\n);"

    return storage, ddl

if __name__ == "__main__":
    storage, ddl = analyze_csv("ml/data/example.csv")
    print("Рекомендуемое хранилище:", storage)
    print("DDL:\n", ddl)

