import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()


def get_engine():
    """
    Cria e retorna uma engine de conexão com o PostgreSQL.

    A engine é o objeto central do SQLAlchemy — ela gerencia
    o pool de conexões com o banco de forma eficiente.
    Todos os outros scripts do projeto importam essa função.
    """

    # Lê as credenciais do .env — nunca escreva senhas direto no código
    db_user     = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host     = os.getenv("DB_HOST", "localhost")  # padrão: localhost
    db_port     = os.getenv("DB_PORT", "5433")        # padrão: porta do PostgreSQL
    db_name     = os.getenv("DB_NAME")

    # Monta a URL de conexão no formato que o SQLAlchemy espera
    connection_url = (
        f"postgresql+psycopg2://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

    engine = create_engine(
        connection_url,
        echo=False   # mude para True se quiser ver o SQL gerado no terminal
    )

    return engine


def test_connection():
    """
    Testa se a conexão com o banco está funcionando.
    Rode esse arquivo diretamente para verificar o ambiente:

        python ingestion/db_connection.py
    """
    try:
        engine = get_engine()

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]

        print("✅ Conexão bem-sucedida!")
        print(f"   PostgreSQL: {version}")

    except Exception as e:
        print("❌ Falha na conexão.")
        print(f"   Erro: {e}")
        print("\n   Verifique seu arquivo .env:")
        print("   DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME")


# Permite testar a conexão rodando esse arquivo diretamente
if __name__ == "__main__":
    test_connection()