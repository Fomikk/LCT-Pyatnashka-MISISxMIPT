import os, json
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from ml.generators.ddl import generate_ddl

# 1) подхватим .env
load_dotenv()

# 2) наш профайлер (важно: через ml.profiling)
from ml.profiling.profiler import profile_dataframe

# 3) оркестратор рекомендаций
from ml.recommend.orchestrator import make_recommendation

def ensure_sample_csv(path: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        df = pd.DataFrame(
            [{"id": 1, "name": "apple", "price": 10},
             {"id": 2, "name": "orange", "price": 20}]
        )
        df.to_csv(p, index=False)

def main():
    csv_path = "./ml/data/samples/csv_example.csv"
    ensure_sample_csv(csv_path)

    df = pd.read_csv(csv_path)
    profile = profile_dataframe(df, {"type": "file", "format": "csv", "name": os.path.basename(csv_path)})

    prefs = {
        "mode": "olap",
        "latency_sla": "day",
        "primary_key": "id",
        "table_name": "items"
    }

    rec = make_recommendation(profile, prefs, use_llm=True)
    sql = generate_ddl(rec["target_store"], profile, rec["ddl_hints"])
    print("\n-- DDL:\n", sql)
    print(json.dumps(rec, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
