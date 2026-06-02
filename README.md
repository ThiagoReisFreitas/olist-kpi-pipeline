# Olist KPI Pipeline

Pipeline ELT de KPIs logísticos construído sobre o dataset público da Olist (Kaggle).  
Dados brutos em CSV → PostgreSQL → KPIs calculados em SQL → Dashboard Streamlit.

---

## Índice

1. [O que o projeto faz](#o-que-o-projeto-faz)
2. [Fluxo da aplicação](#fluxo-da-aplicação)
3. [KPIs calculados](#kpis-calculados)
4. [Estrutura de arquivos](#estrutura-de-arquivos)
5. [Pré-requisitos](#pré-requisitos)
6. [Como executar](#como-executar)
7. [Testes](#testes)
8. [Detalhes técnicos](#detalhes-técnicos)

---

## O que o projeto faz

A Olist é um marketplace brasileiro. O dataset público deles tem ~100 mil pedidos com informações de entrega, pagamento, avaliações e produtos.

O projeto usa esse dataset pra responder perguntas logísticas:

- Qual estado tem a maior taxa de entrega no prazo?
- Onde o frete come mais do valor do produto?
- Quanto um atraso de 3 dias afeta a nota do cliente?
- Qual etapa do processo (aprovação, despacho, trânsito) é o gargalo de cada estado?

---

## Fluxo da aplicação

```
data/*.csv
     │
     │  1. Ingestão (ingestion/load_raw.py)
     │     Lê cada CSV com pandas e insere no PostgreSQL
     │     sem alterações — cópia direta da fonte.
     ▼
raw.orders
raw.customers          ← schema "raw" no PostgreSQL
raw.order_items
raw.order_reviews
raw.order_payments
raw.products
raw.sellers
raw.geolocation
raw.product_category_name_translation
     │
     │  2. Transformação (transformation/compute_kpi.py)
     │     Executa os SQLs de KPI e salva no schema analytics.
     │     O schema raw nunca é alterado.
     ▼
analytics.otd                    ← On-Time Delivery por estado
analytics.lead_time              ← Tempo médio compra→entrega
analytics.perfect_order          ← Entregue no prazo + nota ≥ 4
analytics.freight_cost           ← Frete médio e proporção frete/produto
analytics.delay_vs_satisfaction  ← Nota média por faixa de atraso
analytics.volume_temporal        ← Pedidos e receita por mês
analytics.categorias             ← Top 20 categorias por receita
analytics.pagamentos             ← Distribuição e comportamento por meio de pagamento
     │
     │  3. Dashboard (dashboard/app.py)
     │     Streamlit lê do schema analytics e
     │     renderiza os gráficos com Plotly.
     ▼
http://localhost:8501
```

**Por que ELT e não ETL?**  
Os dados são transformados depois de estarem no banco. O schema `raw` preserva a fonte original — se uma regra de negócio mudar, basta reescrever o SQL e rodar a transformação de novo, sem reingerir os CSVs.

---

## KPIs calculados

### On-Time Delivery (OTD)

Percentual de pedidos entregues até ou antes da data estimada, agrupado por estado.  
Campos: `total_pedidos`, `pedidos_no_prazo`, `pedidos_atrasados`, `otd_pct`, `atraso_medio_dias`, `pior_atraso_dias`.

### Lead Time de Entrega

Tempo total da compra até a entrega ao cliente, decomposto em três etapas:

- **Aprovação** — compra → aprovação do pagamento (horas)
- **Despacho** — aprovação → entregue ao transportador (dias)
- **Trânsito** — transportador → cliente (dias)

A coluna `pct_tempo_despacho` aponta qual etapa é o gargalo de cada estado.

### Perfect Order Rate

Pedido perfeito = entregue no prazo **e** avaliação ≥ 4 estrelas. Combina eficiência logística com satisfação do cliente num único número.

### Custo de Frete

Frete médio, frete mediano e proporção frete/preço do produto por estado. A proporção mostra onde o custo logístico compromete mais a experiência de compra.

### Atraso × Satisfação

Nota média de avaliação agrupada por faixa de atraso:

- No prazo
- Atraso leve (1–3 dias)
- Atraso moderado (4–7 dias)
- Atraso grave (8+ dias)

Traduz em números o impacto de cada dia de atraso na percepção do cliente.

### Tendência Temporal

Volume de pedidos e receita agrupados por mês (jan/2017 a ago/2018). Útil pra identificar sazonalidade e crescimento do marketplace.  
Campos: `mes`, `total_pedidos`, `receita_total`, `ticket_medio`.

### Categorias de Produto

Top 20 categorias por receita em pedidos entregues. Inclui ticket médio e proporção do frete sobre o valor do produto por categoria.  
Campos: `categoria`, `total_pedidos`, `receita_total`, `ticket_medio`, `proporcao_frete_pct`.

### Meios de Pagamento

Distribuição de transações por método de pagamento (cartão de crédito, boleto, voucher, débito). Inclui parcelamento médio e proporção de pedidos parcelados.  
Campos: `tipo_pagamento`, `total_transacoes`, `ticket_medio`, `parcelas_medias`, `pct_parcelado`.

---

## Estrutura de arquivos

```
olist-kpi-pipeline/
├── data/                          # CSVs da Olist (não versionados)
│   ├── olist_orders_dataset.csv
│   ├── olist_customers_dataset.csv
│   ├── olist_order_items_dataset.csv
│   ├── olist_order_reviews_dataset.csv
│   ├── olist_order_payments_dataset.csv
│   ├── olist_products_dataset.csv
│   ├── olist_sellers_dataset.csv
│   ├── olist_geolocation_dataset.csv
│   └── product_category_name_translation.csv
│
├── docker/
│   └── init.sql                   # Cria os schemas raw e analytics na primeira vez
│
├── ingestion/
│   └── load_raw.py                # Lê os CSVs e carrega no schema raw
│
├── transformation/
│   ├── compute_kpi.py             # Orquestra a execução dos SQLs de KPI
│   └── sql/
│       ├── otd.sql
│       ├── lead_time.sql
│       ├── perfect_order.sql
│       ├── freight_cost.sql
│       ├── delay_vs_satisfaction.sql
│       ├── volume_temporal.sql
│       ├── categorias.sql
│       └── pagamentos.sql
│
├── dashboard/
│   └── app.py                     # Dashboard Streamlit com Plotly (9 páginas)
│
├── tests/
│   ├── conftest.py                # Setup do pytest (sys.path + mock do Streamlit)
│   ├── test_ingestion.py          # Testa get_table_name de load_raw.py
│   ├── test_compute_kpi.py        # Testa leitura e integridade dos SQLs de KPI
│   ├── test_db_connection.py      # Testa montagem da URL de conexão
│   └── test_dashboard_helpers.py  # Testa helpers HTML (kpi, header, section)
│
├── db_connection.py               # Fábrica de engine SQLAlchemy (lê o .env)
├── run_pipeline.py                # Ponto de entrada: roda ingestão + transformação
├── docker-compose.yml             # Sobe o PostgreSQL em container
├── .env.example                   # Template das variáveis de ambiente
└── .gitignore
```

---

## Pré-requisitos

| Ferramenta | Versão mínima | Para que serve |
|---|---|---|
| Python | 3.10+ | Executar o pipeline e o dashboard |
| Docker + Docker Compose | qualquer versão atual | Subir o PostgreSQL |
| pip | — | Instalar as dependências Python |

**Dependências Python** (instale com `pip install` abaixo):

```
pandas
sqlalchemy
psycopg2-binary
python-dotenv
streamlit
plotly
pytest
```

---

## Como executar

### 1. Clone o repositório e baixe os dados

```bash
git clone <url-do-repositorio>
cd olist-kpi-pipeline
```

Baixe o dataset da Olist no Kaggle:  
`https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce`

Extraia os CSVs dentro da pasta `data/`. A estrutura esperada está descrita em [Estrutura de arquivos](#estrutura-de-arquivos).

### 2. Configure o ambiente Python

```bash
pip install pandas sqlalchemy psycopg2-binary python-dotenv streamlit plotly
```

### 3. Configure as variáveis de ambiente

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp .env.example .env
```

Edite o `.env`:

```env
DB_USER=olist
DB_PASSWORD=sua_senha_aqui
DB_HOST=localhost
DB_PORT=5433
DB_NAME=olist_db
```

> **Por que porta 5433?**  
> O `docker-compose.yml` mapeia a porta interna 5432 do container para 5433 na sua máquina. Isso evita conflito caso você já tenha um PostgreSQL local rodando na 5432 padrão.

### 4. Suba o banco de dados

```bash
docker compose up -d
```

Isso inicia um container PostgreSQL 16. Na primeira vez, o arquivo `docker/init.sql` é executado automaticamente e cria os schemas `raw` e `analytics`.

Verifique se o banco subiu corretamente:

```bash
docker compose ps
```

O status deve ser `healthy`. Se quiser confirmar a conexão pelo Python:

```bash
python db_connection.py
```

### 5. Execute o pipeline

```bash
python run_pipeline.py
```

O script roda duas etapas em sequência:

1. **Ingestão** — lê todos os CSVs da pasta `data/` e carrega no schema `raw`. Cada arquivo vira uma tabela com o mesmo nome sem os prefixos `olist_` e `_dataset`.
2. **Transformação** — executa os 8 SQLs de KPI e salva os resultados no schema `analytics`.

Saída esperada:

```
==================================================
   OLIST KPI PIPELINE
==================================================
[1/2] Ingestão — carregando CSVs no schema raw...
=== 9 arquivo(s) encontrado(s) ===
  Lendo olist_customers_dataset.csv...
  Inserindo 99.441 linhas em raw.customers...
  ✅ raw.customers carregada.
  ...
[2/2] Transformação — calculando KPIs no schema analytics...
  Calculando analytics.otd...
  ✅ analytics.otd — 27 linhas salvas.
  ...
==================================================
   Pipeline concluído em 42.3s
   Execute: streamlit run dashboard/app.py
==================================================
```

### 6. Abra o dashboard

```bash
streamlit run dashboard/app.py
```

Acesse `http://localhost:8501` no navegador. O dashboard tem 9 páginas navegáveis pela barra lateral:

| Página | O que mostra |
|---|---|
| Visão Geral | Cards nacionais + mapa OTD + ranking lead time |
| On-Time Delivery | Mapa, barras por estado, atraso médio |
| Lead Time | Decomposição despacho/trânsito por estado |
| Perfect Order | Taxa combinada prazo + satisfação |
| Custo de Frete | Frete médio, proporção frete/produto, scatter ticket vs frete |
| Atraso × Satisfação | Queda da nota conforme a faixa de atraso |
| Tendência Temporal | Volume de pedidos e receita por mês |
| Categorias | Top 20 categorias — treemap, ticket médio, proporção frete |
| Meios de Pagamento | Distribuição de transações, parcelamento, ticket por método |

---

## Testes

Os testes cobrem a lógica pura do pipeline, sem precisar de banco de dados ou Streamlit rodando.

```bash
pytest tests/ -v
```

| Arquivo de teste | O que verifica |
|---|---|
| `test_ingestion.py` | `get_table_name()` — conversão correta de nome de arquivo para nome de tabela |
| `test_compute_kpi.py` | Existência, leitura e integridade dos 8 arquivos SQL de KPI |
| `test_db_connection.py` | Montagem correta da URL de conexão a partir das variáveis de ambiente |
| `test_dashboard_helpers.py` | Geração de HTML dos helpers `kpi()`, `header()` e `section()` |

O Streamlit é mockado no `conftest.py` para permitir importar `dashboard/app.py` sem um servidor ativo.

---

## Detalhes técnicos

### Por que o pipeline recria as tabelas a cada execução?

Tanto na ingestão (`raw`) quanto na transformação (`analytics`), as tabelas são recriadas com `if_exists="replace"`. Isso garante idempotência: rodar o pipeline duas vezes produz o mesmo resultado que rodar uma vez. Não há risco de dados duplicados.

### Como adicionar um novo KPI

1. Crie um arquivo `.sql` em `transformation/sql/` com a query que lê do schema `raw`.
2. Registre o arquivo em `KPI_JOBS` dentro de `transformation/compute_kpi.py`:
   ```python
   KPI_JOBS = {
       ...
       "meu_kpi.sql": "meu_kpi",   # arquivo → nome da tabela no analytics
   }
   ```
3. Rode `python run_pipeline.py` — a nova tabela `analytics.meu_kpi` será criada automaticamente.
4. Adicione a página no dashboard em `dashboard/app.py` usando `load_table("meu_kpi")`.

### Parar e remover o banco

```bash
# Para o container sem apagar os dados
docker compose stop

# Para e remove o container e o volume (apaga tudo)
docker compose down -v
```
