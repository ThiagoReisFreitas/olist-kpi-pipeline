import os
import sys
import pandas as pd
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db_connection import get_engine

# Caminho para a pasta data/ relativo à raiz do projeto
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def get_table_name(filename):
    """
    Transforma o nome do arquivo em nome de tabela limpo.

    Exemplos:
        olist_orders_dataset.csv                  → orders
        olist_order_items_dataset.csv             → order_items
        product_category_name_translation.csv     → product_category_name_translation
    """
    name = filename.replace(".csv", "")
    name = name.replace("olist_", "")
    name = name.replace("_dataset", "")
    return name


def load_csv_to_db(engine, filepath, table_name):
    """
    Lê um CSV e insere no schema raw sem nenhuma alteração.

    Princípio ELT: raw é espelho fiel da fonte.
    Regras de negócio ficam na camada transformation/.
    """
    print(f"  Lendo {os.path.basename(filepath)}...")
    df = pd.read_csv(filepath)

    print(f"  Inserindo {len(df):,} linhas em raw.{table_name}...")
    df.to_sql(
        name=table_name,
        con=engine,
        schema="raw",
        if_exists="replace",  # recria a tabela a cada execução
        index=False,
    )
    print(f"  ✅ raw.{table_name} carregada.\n")


def run():
    engine = get_engine()

    # Garante que o schema raw existe antes de qualquer inserção
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        conn.commit()

    # Descobre automaticamente todos os CSVs na pasta data/
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

    if not csv_files:
        print("⚠️  Nenhum arquivo CSV encontrado em data/")
        print(f"   Caminho verificado: {os.path.abspath(DATA_DIR)}")
        return

    print(f"=== {len(csv_files)} arquivo(s) encontrado(s) ===\n")

    for filename in sorted(csv_files):
        table_name = get_table_name(filename)
        filepath = os.path.join(DATA_DIR, filename)
        load_csv_to_db(engine, filepath, table_name)

    print("=== Ingestão concluída ===")
    print(f"    {len(csv_files)} tabelas carregadas no schema raw.")


if __name__ == "__main__":
    run()