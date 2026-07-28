import sqlite3
import pandas as pd

from config.settings import TABLES, DB_PATH, LAYERS, LAYER_DIRS


class Repository:

    def __init__(self, db_path=DB_PATH, layer_dirs=None):
        self.db_path = db_path
        self.layer_dirs = layer_dirs or LAYER_DIRS
        for path in self.layer_dirs.values():
            path.mkdir(parents=True, exist_ok=True)

    def _table_name(self, layer, name):
        if name not in TABLES or layer not in LAYERS:
            raise ValueError(f"Unknown table or layer: table={name}, layer={layer}")
        return f"{layer}_{TABLES[name]}"

    def _csv_path(self, layer, table_name):
        return self.layer_dirs[layer] / f"{table_name}.csv"

    def load(self, layer, name):
        table = self._table_name(layer, name)
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql(f"SELECT * FROM {table}", conn)

    def save(self, df, layer, name):
        table = self._table_name(layer, name)
        self._write_to_database(df, table)
        self._write_to_csv(df, layer, table)

    def _write_to_database(self, df, table):
        with sqlite3.connect(self.db_path) as conn:
            df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"Successfully stored table '{table}' in DB.")

    def _write_to_csv(self, df, layer, table):
        csv_path = self._csv_path(layer, table)
        df.to_csv(csv_path, index=False)
        print(f"Successfully stored table '{table}' in {csv_path.parent}.")