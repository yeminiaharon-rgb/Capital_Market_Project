from functools import reduce
import pandas as pd


def build_metrics_table(named_dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:

    metric_dfs = []

    for name, df in named_dfs.items():
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


def compute_metric_scores(
    metrics_table: pd.DataFrame,
    metrics_config: dict,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:

    current = metrics_table[metrics_table["period"] == "current"].set_index("ticker")
    year_ago = metrics_table[metrics_table["period"] == "year_ago"].set_index("ticker")

    scores = pd.DataFrame(index=current.index)

    for key, cfg in metrics_config.items():
        col = cfg["column"]
        if col not in metrics_table.columns:
            print(f"Warning: column '{col}' for metric '{key}' not found in metrics_table, skipping.")
            continue

        delta = current[col] - year_ago[col]

        min_change = delta.min()
        max_change = delta.max()

        if max_change == min_change:
      
            score = pd.Series(5.0, index=delta.index)
        elif cfg["higher_is_better"]:
            score = (delta - min_change) / (max_change - min_change) * 10
        else:
            score = (max_change - delta) / (max_change - min_change) * 10

        scores[f"{key}_score"] = score

    score_cols = [c for c in scores.columns if c.endswith("_score")]
    if not score_cols:
        raise ValueError("No metric columns available to score.")

    if weights is None:
        weight_map = {c: 1.0 for c in score_cols}
    else:
        weight_map = {f"{key}_score": w for key, w in weights.items()}

    weights_series = pd.Series(weight_map)
    weighted_scores = scores[score_cols].multiply(weights_series, axis=1)
    valid_weights = scores[score_cols].notna().multiply(weights_series, axis=1).sum(axis=1)

    scores["final_score"] = (weighted_scores.sum(axis=1) / valid_weights).round(2)

    return scores.reset_index()