import sqlite3
import pandas as pd

from config.settings import TABLES, DB_PATH, DB_STREAMLIT_PATH, LAYERS, LAYER_DIRS


class Repository:

    def __init__(self, db_path=DB_PATH, streamlit_db_path=DB_STREAMLIT_PATH, layer_dirs=None):
        self.db_path = db_path
        self.streamlit_db_path = streamlit_db_path
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

    def save(self, df, layer, name, save_to_streamlit=False, check_nulls=True):
        table = self._table_name(layer, name)
        if check_nulls:
            self._check_nulls(df, table)
        self._write_to_database(df, table)
        self._write_to_csv(df, layer, table)
        if save_to_streamlit:
            self._write_to_streamlit_database(df, table)

    def _write_to_database(self, df, table):
        with sqlite3.connect(self.db_path) as conn:
            df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"Successfully stored table '{table}' in DB.")

    def _write_to_csv(self, df, layer, table):
        csv_path = self._csv_path(layer, table)
        df.to_csv(csv_path, index=False)
        print(f"Successfully stored table '{table}' in {csv_path.parent}.")

    def _write_to_streamlit_database(self, df, table):
        with sqlite3.connect(self.streamlit_db_path) as conn:
            df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"Successfully stored table '{table}' in Streamlit DB.")

    def load_streamlit(self, layer, name):
        table = self._table_name(layer, name)
        with sqlite3.connect(self.streamlit_db_path) as conn:
            return pd.read_sql(f"SELECT * FROM {table}", conn)

    def _check_nulls(self, df, table):
        if df.isnull().values.any():
            null_cols = df.columns[df.isnull().any()].tolist()
            id_cols = [c for c in ['ticker', 'date'] if c in df.columns]
            bad_rows = df[df.isnull().any(axis=1)]
            print(f"Warning:found NULLs in table '{table}', columns: {null_cols}")
            if id_cols:
                print(bad_rows[id_cols + null_cols])
            else:
                print(bad_rows)