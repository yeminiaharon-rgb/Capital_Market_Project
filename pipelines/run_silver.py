from repository.repository import Repository
from transforms.silver_transforms import (
    transform_valuation,
    transform_income,
    transform_balance,
    transform_cash,
    transform_dividends,
    transform_price,
    get_current_and_year_ago,
    get_period_column_y,
    get_period_column_d,
    merge_metric_from_table,
)


def run():
    repo = Repository()

    ### Start of transformation - quarterly tables

    df = repo.load("bronze", "valu")
    df = transform_valuation(df)
    df = get_current_and_year_ago(df)
    repo.save(df, "silver", "valu")

    df = repo.load("bronze", "income")
    df = transform_income(df)
    df = get_current_and_year_ago(df)
    repo.save(df, "silver", "income")

    df = repo.load("bronze", "balance")
    df = transform_balance(df)
    df = get_current_and_year_ago(df)
    repo.save(df, "silver", "balance")

    df = repo.load("bronze", "cash")
    df = transform_cash(df)
    df = get_current_and_year_ago(df)
    repo.save(df, "silver", "cash")

    #### Non-quarterly tables

    df = repo.load("bronze", "divi")
    df = transform_dividends(df)
    df = get_period_column_y(df)
    repo.save(df, "silver", "divi")

    df = repo.load("bronze", "pr")
    df = transform_price(df)
    df = get_period_column_d(df)
    repo.save(df, "silver", "pr")

    ######## Adding a calculated metric to income

    df_income = repo.load("silver", "income")
    df_balance = repo.load("silver", "balance")

    df_income = merge_metric_from_table(df_income, df_balance, 'Stockholders Equity')
    df_income["ROE_metric"] = (df_income["net_income_metric"] / df_income["Stockholders Equity"]).round(2)

    df_income = df_income.drop(columns='Stockholders Equity')
    df_balance = df_balance.drop(columns='Stockholders Equity')

    repo.save(df_income, "silver", "income")
    repo.save(df_balance, "silver", "balance")

    ######## Adding a calculated metric to dividends

    df_dividends = repo.load("silver", "divi")
    df_price = repo.load("silver", "pr")

    df_dividends = merge_metric_from_table(df_dividends, df_price, 'close')
    df_dividends["dividend_metric"] = (df_dividends["dividend_metric"] / df_dividends["close"]).round(2)
    df_dividends = df_dividends.drop(columns='close')

    repo.save(df_dividends, "silver", "divi")


if __name__ == "__main__":
    run()