import pytest
from unittest.mock import patch
from db_connection import get_engine


def test_get_engine_uses_env_vars():
    env = {
        "DB_USER": "testuser",
        "DB_PASSWORD": "testpass",
        "DB_HOST": "testhost",
        "DB_PORT": "5433",
        "DB_NAME": "testdb",
    }
    with patch.dict("os.environ", env, clear=False):
        engine = get_engine()
        url = engine.url
        assert url.username == "testuser"
        assert url.host == "testhost"
        assert str(url.port) == "5433"
        assert url.database == "testdb"


def test_get_engine_default_host_and_port():
    env = {
        "DB_USER": "u",
        "DB_PASSWORD": "p",
        "DB_NAME": "db",
    }
    with patch.dict("os.environ", env, clear=False):
        # Remove valores anteriores para testar o default
        import os
        os.environ.pop("DB_HOST", None)
        os.environ.pop("DB_PORT", None)
        engine = get_engine()
        url = engine.url
        assert url.host == "localhost"
        assert str(url.port) == "5433"


def test_get_engine_uses_psycopg2_driver():
    env = {
        "DB_USER": "u", "DB_PASSWORD": "p",
        "DB_HOST": "h", "DB_PORT": "5432", "DB_NAME": "db",
    }
    with patch.dict("os.environ", env, clear=False):
        engine = get_engine()
        assert "psycopg2" in engine.url.drivername
