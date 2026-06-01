import sys
import time

# Importa as funções principais de cada etapa
from ingestion.load_raw import run as run_ingestion
from transformation.compute_kpi import run as run_transformation


def main():
    print("=" * 50)
    print("   OLIST KPI PIPELINE")
    print("=" * 50)

    start = time.time()

    # Etapa 1 — Ingestão
    print("\n[1/2] Ingestão — carregando CSVs no schema raw...\n")
    run_ingestion()

    # Etapa 2 — Transformação
    print("\n[2/2] Transformação — calculando KPIs no schema analytics...\n")
    run_transformation()

    elapsed = round(time.time() - start, 1)

    print("\n" + "=" * 50)
    print(f"   Pipeline concluído em {elapsed}s")
    print("   Execute: streamlit run dashboard/app.py")
    print("=" * 50)


if __name__ == "__main__":
    main()