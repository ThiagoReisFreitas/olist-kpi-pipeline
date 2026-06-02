import pytest
from ingestion.load_raw import get_table_name


@pytest.mark.parametrize("filename,expected", [
    ("olist_orders_dataset.csv",                  "orders"),
    ("olist_order_items_dataset.csv",             "order_items"),
    ("olist_order_payments_dataset.csv",          "order_payments"),
    ("olist_order_reviews_dataset.csv",           "order_reviews"),
    ("olist_customers_dataset.csv",               "customers"),
    ("olist_products_dataset.csv",                "products"),
    ("olist_sellers_dataset.csv",                 "sellers"),
    ("olist_geolocation_dataset.csv",             "geolocation"),
    ("product_category_name_translation.csv",     "product_category_name_translation"),
])
def test_get_table_name(filename, expected):
    assert get_table_name(filename) == expected


def test_get_table_name_strips_only_known_prefixes():
    # Arquivo sem prefixo olist_ não deve ser modificado além de remover .csv
    assert get_table_name("custom_file.csv") == "custom_file"
