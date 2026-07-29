from config.settings import TABLES, METRICS_CONFIG
from repository.repository import Repository
from transforms.gold_transforms import build_metrics_table, compute_metric_scores


def run():
    repo = Repository()


    source_keys = [name for name in TABLES if name not in ("metrics", "scores")]

    named_dfs = {name: repo.load("silver", name) for name in source_keys}

    metrics_table = build_metrics_table(named_dfs)
    repo.save(metrics_table, "gold", "metrics", True)


    scores_table = compute_metric_scores(metrics_table, METRICS_CONFIG, weights=None)
    repo.save(scores_table,"gold", "scores")

    print("Gold metrics and scores tables built and saved successfully.")


if __name__ == "__main__":
    run()