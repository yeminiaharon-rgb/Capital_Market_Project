import pandas as pd
from functools import reduce
from transformation import load, save

def build_metrics_table(layer_name, table_names):
    metric_dfs = []

    

    for name in table_names:
        df = load(layer_name, name)   # משתמש ישירות ב-load שכבר קיימת בקובץ

        metric_cols = [c for c in df.columns if c.endswith("_metric")]
        if not metric_cols:
            print(f"Warning: no '_metric' columns found in table '{name}', skipping.")
            continue

        metric_dfs.append(df[["ticker", "period"] + metric_cols])

    if not metric_dfs:
        raise ValueError("No metric columns found in any of the given tables.")

    metrics_table = reduce(
        lambda left, right: pd.merge(left, right, on=["ticker", "period"], how="outer"),
        metric_dfs,
    )

    return metrics_table

metrics_table = build_metrics_table("silver", ["income", "balance", "price", "dividends"])
save(metrics_table, "silver", "metrics")