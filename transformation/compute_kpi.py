import os
import sys
import pandas as pd
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db_connection import get_engine

SQL_DIR = os.path.join(os.path.dirname(__file__), "sql")

KPI_JOBS = {
    "otd.sql":                   "otd",
    "lead_time.sql":             "lead_time",
    "perfect_order.sql":         "perfect_order",
    "freight_cost.sql":          "freight_cost",
    "delay_vs_satisfaction.sql": "delay_vs_satisfaction",
    "volume_temporal.sql":       "volume_temporal",
    "categorias.sql":            "categorias",
    "pagamentos.sql":            "pagamentos",
}


def read_sql(filename):
    filepath = os.path.join(SQL_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def run():
    engine = get_engine()

    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics;"))
        conn.commit()

    print("=== Iniciando transformação ===\n")

    sucessos = 0
    falhas = []

    for sql_file, table_name in KPI_JOBS.items():
        print(f"  Calculando analytics.{table_name}...")

        try:
            query = read_sql(sql_file)

            with engine.connect() as conn:
                # text() garante compatibilidade com SQLAlchemy 2.x
                result = conn.execute(text(query))
                df = pd.DataFrame(result.fetchall(), columns=result.keys())

            with engine.connect() as conn:
                df.to_sql(
                    name=table_name,
                    con=conn,
                    schema="analytics",
                    if_exists="replace",
                    index=False,
                )
                conn.commit()

            print(f"  ✅ analytics.{table_name} — {len(df)} linhas salvas.\n")
            sucessos += 1

        except Exception as e:
            print(f"  ❌ Erro em {sql_file}: {e}\n")
            falhas.append(sql_file)

    print("=== Transformação concluída ===")
    print(f"    {sucessos} KPI(s) calculados com sucesso.")

    if falhas:
        print(f"    {len(falhas)} com erro: {', '.join(falhas)}")


if __name__ == "__main__":
    run()