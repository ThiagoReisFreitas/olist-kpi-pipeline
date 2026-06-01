import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db_connection import get_engine

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Olist KPI Pipeline",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilo customizado ────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0f1117; }
    [data-testid="stSidebar"] * { color: #e0e0e0 !important; }
    .metric-card {
        background: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #4ecca3; }
    .metric-label { font-size: 0.8rem; color: #888; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
    h1, h2, h3 { color: #f0f0f0; }
</style>
""", unsafe_allow_html=True)

# ── Conexão e cache ───────────────────────────────────────────────────────────
# Colunas que devem permanecer como texto
TEXT_COLS = {"estado", "faixa_atraso", "estado_nome"}

@st.cache_data
def load_table(table_name):
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(f"SELECT * FROM analytics.{table_name}", con=conn)
    # Converte todas as colunas numéricas — PostgreSQL NUMERIC vira string no pandas 2.x
    for col in df.columns:
        if col not in TEXT_COLS:
            try:
                df[col] = df[col].astype(float)
            except (ValueError, TypeError):
                pass
    return df

# Mapa: sigla → nome completo do estado
ESTADO_NOME = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
    "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina",
    "SE": "Sergipe", "SP": "São Paulo", "TO": "Tocantins",
}

TEAL   = "#4ecca3"
CORAL  = "#ff6b6b"
BLUE   = "#4d9de0"
AMBER  = "#f7c948"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📦 Olist KPI")
    st.markdown("---")
    page = st.radio(
        "Navegação",
        [
            "🏠  Visão Geral",
            "📦  On-Time Delivery",
            "⏱️  Lead Time",
            "⭐  Perfect Order",
            "💰  Custo de Frete",
            "😤  Atraso × Satisfação",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Projeto 1 — Olist KPI Pipeline\nDados: Kaggle · Olist Dataset")


# ═══════════════════════════════════════════════════════════════
# PÁGINA 1 — VISÃO GERAL
# ═══════════════════════════════════════════════════════════════
if page == "🏠  Visão Geral":
    st.title("📦 Olist KPI Pipeline")
    st.markdown("Dashboard de KPIs logísticos construído sobre o dataset público da Olist.")
    st.markdown("---")

    otd = load_table("otd")
    lt  = load_table("lead_time")
    po  = load_table("perfect_order")
    fc  = load_table("freight_cost")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{float(otd['otd_pct'].mean()):.1f}%</div>
            <div class="metric-label">OTD médio nacional</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{float(lt['lead_time_total_dias'].mean()):.1f}d</div>
            <div class="metric-label">Lead time médio</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{float(po['perfect_order_pct'].mean()):.1f}%</div>
            <div class="metric-label">Perfect Order Rate</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">R${float(fc['frete_medio'].mean()):.0f}</div>
            <div class="metric-label">Frete médio nacional</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("OTD por estado")
        fig = px.choropleth(
            otd,
            geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
            locations="estado",
            featureidkey="properties.sigla",
            color="otd_pct",
            color_continuous_scale=["#ff6b6b", "#f7c948", "#4ecca3"],
            range_color=[float(otd["otd_pct"].min()), 100],
            labels={"otd_pct": "OTD %"},
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    geo=dict(bgcolor="rgba(0,0,0,0)"),  # ← isso remove o fundo branco
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Lead time médio por estado (dias)")
        lt_sorted = lt.sort_values("lead_time_total_dias", ascending=True).tail(15)
        fig2 = px.bar(
            lt_sorted, x="lead_time_total_dias", y="estado", orientation="h",
            color="lead_time_total_dias",
            color_continuous_scale=["#4ecca3", "#f7c948", "#ff6b6b"],
            labels={"lead_time_total_dias": "Dias", "estado": "Estado"},
        )
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# PÁGINA 2 — ON-TIME DELIVERY
# ═══════════════════════════════════════════════════════════════
elif page == "📦  On-Time Delivery":
    st.title("📦 On-Time Delivery")
    st.markdown("Percentual de pedidos entregues até ou antes da data estimada, por estado.")
    st.markdown("---")

    df = load_table("otd")
    df["estado_nome"] = df["estado"].map(ESTADO_NOME)

    col1, col2, col3 = st.columns(3)
    melhor = df.loc[df["otd_pct"].idxmax()]
    pior   = df.loc[df["otd_pct"].idxmin()]
    with col1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{float(melhor['otd_pct']):.1f}%</div>
            <div class="metric-label">Melhor OTD — {melhor['estado']}</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#ff6b6b">{float(pior['otd_pct']):.1f}%</div>
            <div class="metric-label">Pior OTD — {pior['estado']}</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{float(df['atraso_medio_dias'].mean()):.1f}d</div>
            <div class="metric-label">Atraso médio nacional</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Mapa — OTD % por estado")
    fig = px.choropleth(
        df,
        geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
        locations="estado",
        featureidkey="properties.sigla",
        color="otd_pct",
        color_continuous_scale=["#ff6b6b", "#f7c948", "#4ecca3"],
        range_color=[float(df["otd_pct"].min()), 100],
        hover_name="estado_nome",
        hover_data={"estado": False, "otd_pct": True, "pedidos_atrasados": True},
        labels={"otd_pct": "OTD %", "pedidos_atrasados": "Atrasados"},
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    geo=dict(bgcolor="rgba(0,0,0,0)"),  # ← isso remove o fundo branco
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("OTD % por estado")
        fig2 = px.bar(
            df.sort_values("otd_pct"), x="otd_pct", y="estado", orientation="h",
            color="otd_pct",
            color_continuous_scale=["#ff6b6b", "#f7c948", "#4ecca3"],
            labels={"otd_pct": "OTD %", "estado": ""},
        )
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.subheader("Atraso médio por estado (dias)")
        fig3 = px.bar(
            df.sort_values("atraso_medio_dias", ascending=False).head(15),
            x="estado", y="atraso_medio_dias",
            color="atraso_medio_dias",
            color_continuous_scale=["#f7c948", "#ff6b6b"],
            labels={"atraso_medio_dias": "Dias de atraso", "estado": ""},
        )
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Dados completos")
    st.dataframe(df.sort_values("otd_pct", ascending=False), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# PÁGINA 3 — LEAD TIME
# ═══════════════════════════════════════════════════════════════
elif page == "⏱️  Lead Time":
    st.title("⏱️ Lead Time de Entrega")
    st.markdown("Tempo médio entre a compra e a entrega, decomposto em 3 etapas do processo.")
    st.markdown("---")

    df = load_table("lead_time")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{float(df['tempo_aprovacao_horas'].mean()):.1f}h</div>
            <div class="metric-label">Aprovação média</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{float(df['tempo_despacho_dias'].mean()):.1f}d</div>
            <div class="metric-label">Despacho médio</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{float(df['tempo_transito_dias'].mean()):.1f}d</div>
            <div class="metric-label">Trânsito médio</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Decomposição do lead time por estado (dias)")
    df_sorted = df.sort_values("lead_time_total_dias", ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Despacho", x=df_sorted["estado"], y=df_sorted["tempo_despacho_dias"], marker_color=CORAL))
    fig.add_trace(go.Bar(name="Trânsito", x=df_sorted["estado"], y=df_sorted["tempo_transito_dias"], marker_color=TEAL))
    fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    geo=dict(bgcolor="rgba(0,0,0,0)"),  # ← isso remove o fundo branco
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Lead time total vs mediana")
        df_s = df.sort_values("lead_time_total_dias", ascending=False)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Média", x=df_s["estado"], y=df_s["lead_time_total_dias"], marker_color=BLUE))
        fig2.add_trace(go.Scatter(name="Mediana", x=df_s["estado"], y=df_s["lead_time_mediana_dias"], mode="lines+markers", line=dict(color=AMBER, width=2)))
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(tickangle=-45))
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.subheader("% do tempo gasto no despacho por estado")
        fig3 = px.bar(
            df.sort_values("pct_tempo_despacho", ascending=False),
            x="estado", y="pct_tempo_despacho",
            color="pct_tempo_despacho",
            color_continuous_scale=["#4ecca3", "#ff6b6b"],
            labels={"pct_tempo_despacho": "% no despacho", "estado": ""},
        )
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Dados completos")
    st.dataframe(df.sort_values("lead_time_total_dias", ascending=False), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# PÁGINA 4 — PERFECT ORDER
# ═══════════════════════════════════════════════════════════════
elif page == "⭐  Perfect Order":
    st.title("⭐ Perfect Order Rate")
    st.markdown("Pedidos entregues no prazo **e** com avaliação ≥ 4 estrelas.")
    st.markdown("---")

    df = load_table("perfect_order")
    df["estado_nome"] = df["estado"].map(ESTADO_NOME)

    total_pos = float(df["avaliacoes_positivas"].sum())
    total_all = float(df[["avaliacoes_positivas","avaliacoes_neutras","avaliacoes_negativas"]].sum(axis=1).sum())

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{float(df['perfect_order_pct'].mean()):.1f}%</div>
            <div class="metric-label">Perfect Order Rate nacional</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{float(df['nota_media'].mean()):.2f}</div>
            <div class="metric-label">Nota média nacional</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{total_pos/total_all*100:.1f}%</div>
            <div class="metric-label">% avaliações positivas</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Perfect Order Rate por estado")
        fig = px.bar(
            df.sort_values("perfect_order_pct"), x="perfect_order_pct", y="estado", orientation="h",
            color="perfect_order_pct",
            color_continuous_scale=["#ff6b6b", "#f7c948", "#4ecca3"],
            labels={"perfect_order_pct": "Perfect Order %", "estado": ""},
        )
        fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    geo=dict(bgcolor="rgba(0,0,0,0)"),  # ← isso remove o fundo branco
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Nota média: no prazo vs atrasado por estado")
        df_s = df.sort_values("nota_media_no_prazo", ascending=False).head(15)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="No prazo", x=df_s["estado"], y=df_s["nota_media_no_prazo"], marker_color=TEAL))
        fig2.add_trace(go.Bar(name="Atrasado", x=df_s["estado"], y=df_s["nota_media_atrasado"], marker_color=CORAL))
        fig2.update_layout(
            barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(range=[0, 5.5], title="Nota"), legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Distribuição de avaliações por estado (top 10)")
    df_top = df.sort_values("total_pedidos", ascending=False).head(10)
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Positivas (≥4)", x=df_top["estado"], y=df_top["avaliacoes_positivas"], marker_color=TEAL))
    fig3.add_trace(go.Bar(name="Neutras (3)",    x=df_top["estado"], y=df_top["avaliacoes_neutras"],   marker_color=AMBER))
    fig3.add_trace(go.Bar(name="Negativas (≤2)", x=df_top["estado"], y=df_top["avaliacoes_negativas"], marker_color=CORAL))
    fig3.update_layout(
        barmode="stack", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.05),
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Dados completos")
    st.dataframe(df.sort_values("perfect_order_pct", ascending=False), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# PÁGINA 5 — CUSTO DE FRETE
# ═══════════════════════════════════════════════════════════════
elif page == "💰  Custo de Frete":
    st.title("💰 Custo de Frete")
    st.markdown("Análise do custo logístico por estado — frete médio, ticket e proporção frete/produto.")
    st.markdown("---")

    df = load_table("freight_cost")
    df["estado_nome"] = df["estado"].map(ESTADO_NOME)
    mais_caro = df.loc[df["frete_medio"].idxmax()]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">R${float(df['frete_medio'].mean()):.2f}</div>
            <div class="metric-label">Frete médio nacional</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{float(df['proporcao_frete_pct'].mean()):.1f}%</div>
            <div class="metric-label">Frete / produto médio</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#ff6b6b">R${float(mais_caro['frete_medio']):.2f}</div>
            <div class="metric-label">Maior frete médio — {mais_caro['estado']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Mapa — Frete médio por estado")
    fig = px.choropleth(
        df,
        geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
        locations="estado",
        featureidkey="properties.sigla",
        color="frete_medio",
        color_continuous_scale=["#4ecca3", "#f7c948", "#ff6b6b"],
        hover_name="estado_nome",
        hover_data={"estado": False, "frete_medio": True, "proporcao_frete_pct": True},
        labels={"frete_medio": "Frete médio (R$)", "proporcao_frete_pct": "% do produto"},
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    geo=dict(bgcolor="rgba(0,0,0,0)"),  # ← isso remove o fundo branco
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Frete médio vs ticket médio por estado")
        fig2 = px.scatter(
            df, x="ticket_medio", y="frete_medio", text="estado",
            color="proporcao_frete_pct",
            color_continuous_scale=["#4ecca3", "#ff6b6b"],
            size="total_pedidos",
            labels={"ticket_medio": "Ticket médio (R$)", "frete_medio": "Frete médio (R$)", "proporcao_frete_pct": "% frete"},
        )
        fig2.update_traces(textposition="top center", textfont_size=9)
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.subheader("Proporção frete / produto por estado (%)")
        fig3 = px.bar(
            df.sort_values("proporcao_frete_pct", ascending=False),
            x="estado", y="proporcao_frete_pct",
            color="proporcao_frete_pct",
            color_continuous_scale=["#4ecca3", "#f7c948", "#ff6b6b"],
            labels={"proporcao_frete_pct": "% frete/produto", "estado": ""},
        )
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Dados completos")
    st.dataframe(df.sort_values("frete_medio", ascending=False), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# PÁGINA 6 — ATRASO × SATISFAÇÃO
# ═══════════════════════════════════════════════════════════════
elif page == "😤  Atraso × Satisfação":
    st.title("😤 Atraso × Satisfação")
    st.markdown("Como o atraso na entrega impacta a nota de avaliação do cliente.")
    st.markdown("---")

    df = load_table("delay_vs_satisfaction")
    ordem = ["No prazo", "Atraso leve (1-3 dias)", "Atraso moderado (4-7 dias)", "Atraso grave (8+ dias)"]
    df["faixa_atraso"] = pd.Categorical(df["faixa_atraso"], categories=ordem, ordered=True)
    df = df.sort_values("faixa_atraso")

    no_prazo = df[df["faixa_atraso"] == "No prazo"].iloc[0]
    grave    = df[df["faixa_atraso"] == "Atraso grave (8+ dias)"].iloc[0]
    queda    = float(no_prazo["nota_media"]) - float(grave["nota_media"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{float(no_prazo['nota_media']):.2f}</div>
            <div class="metric-label">Nota média — no prazo</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#ff6b6b">{float(grave['nota_media']):.2f}</div>
            <div class="metric-label">Nota média — atraso grave</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#f7c948">-{queda:.2f}</div>
            <div class="metric-label">Queda na nota (prazo → grave)</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Nota média por faixa de atraso")
        fig = px.line(
            df, x="faixa_atraso", y="nota_media", markers=True,
            labels={"faixa_atraso": "", "nota_media": "Nota média"},
            color_discrete_sequence=[TEAL],
        )
        fig.update_traces(line=dict(width=3), marker=dict(size=10))
        fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    geo=dict(bgcolor="rgba(0,0,0,0)"),  # ← isso remove o fundo branco
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("% de avaliações negativas por faixa")
        fig2 = px.bar(
            df, x="faixa_atraso", y="pct_negativas",
            color="pct_negativas",
            color_continuous_scale=["#4ecca3", "#f7c948", "#ff6b6b"],
            labels={"faixa_atraso": "", "pct_negativas": "% negativas"},
        )
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Distribuição completa de notas por faixa")
    notas = df[["faixa_atraso","nota_5","nota_4","nota_3","nota_2","nota_1"]].melt(
        id_vars="faixa_atraso", var_name="nota", value_name="quantidade"
    )
    fig3 = px.bar(
        notas, x="faixa_atraso", y="quantidade", color="nota",
        color_discrete_map={"nota_5": TEAL, "nota_4": BLUE, "nota_3": AMBER, "nota_2": CORAL, "nota_1": "#c0392b"},
        labels={"faixa_atraso": "", "quantidade": "Pedidos", "nota": "Nota"},
        barmode="group",
    )
    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Dados completos")
    st.dataframe(df, use_container_width=True, hide_index=True)