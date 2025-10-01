import pandas as pd
import numpy as np

def profile_dataframe(df: pd.DataFrame, source_meta: dict) -> dict:
    # заменяем NaN/Inf в предпросмотре
    preview = df.replace([np.nan, np.inf, -np.inf], None).head(5).to_dict(orient="records")

    schema = []
    for col in df.columns:
        s = df[col]
        nulls = int(s.isna().sum())
        uniques = int(s.nunique(dropna=True))
        schema.append({
            "column": str(col),
            "dtype": str(s.dtype),
            "nulls": nulls,
            "uniques": uniques,
        })

    checks = {
        "has_time": any("date" in str(c).lower() or "time" in str(c).lower() for c in df.columns),
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
    }

    return {
        "source": source_meta,
        "preview": preview,
        "schema": schema,
        "checks": checks,
    }
