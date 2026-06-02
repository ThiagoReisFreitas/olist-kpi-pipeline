import pytest
from transformation.compute_kpi import read_sql, KPI_JOBS


def test_kpi_jobs_has_all_expected_tables():
    expected_tables = {
        "otd", "lead_time", "perfect_order", "freight_cost",
        "delay_vs_satisfaction", "volume_temporal", "categorias", "pagamentos",
    }
    assert set(KPI_JOBS.values()) == expected_tables


def test_all_sql_files_exist_and_are_readable():
    for sql_file in KPI_JOBS:
        content = read_sql(sql_file)
        assert len(content) > 0, f"{sql_file} está vazio"


def test_all_sql_files_contain_select():
    for sql_file in KPI_JOBS:
        content = read_sql(sql_file)
        assert "SELECT" in content.upper(), f"{sql_file} não contém SELECT"


def test_all_sql_files_reference_raw_schema():
    for sql_file in KPI_JOBS:
        content = read_sql(sql_file)
        assert "raw." in content.lower(), (
            f"{sql_file} não referencia o schema raw — as queries devem ler de raw.*"
        )


def test_kpi_jobs_sql_files_match_dict_keys():
    for sql_file in KPI_JOBS:
        assert sql_file.endswith(".sql"), f"Chave inválida em KPI_JOBS: {sql_file}"
