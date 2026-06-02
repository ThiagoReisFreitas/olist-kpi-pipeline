import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db_connection import get_engine

st.set_page_config(
    page_title="Olist KPI Pipeline",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Reset Streamlit defaults ── */
  #MainMenu, footer, [data-testid="stStatusWidget"],
  [data-testid="stToolbar"], .stDeployButton { display: none !important; }

  /* ── App background ── */
  html, body, .stApp,
  [data-testid="stAppViewContainer"] { background-color: #080910 !important; }
  section.main > div { padding-top: 1.5rem; padding-bottom: 2rem; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: #0c0d14 !important;
    border-right: 1px solid #181b28 !important;
  }
  [data-testid="stSidebar"] > div:first-child { padding: 1.25rem 0.75rem !important; }

  /* ── Sidebar nav (radio) ── */
  [data-testid="stRadio"] > label { display: none !important; }
  [data-testid="stRadio"] > div   { gap: 0 !important; }
  [data-testid="stRadio"] label {
    display: flex !important;
    align-items: center;
    width: 100% !important;
    padding: 9px 12px !important;
    border-radius: 8px !important;
    margin: 2px 0 !important;
    font-size: 0.875rem !important;
    color: #a8b2c0 !important;
    transition: background 0.15s, color 0.15s !important;
    cursor: pointer !important;
  }
  [data-testid="stRadio"] label p,
  [data-testid="stRadio"] label span,
  [data-testid="stRadio"] label div {
    color: #a8b2c0 !important;
    font-size: 0.875rem !important;
  }
  [data-testid="stRadio"] label:hover,
  [data-testid="stRadio"] label:hover p,
  [data-testid="stRadio"] label:hover span,
  [data-testid="stRadio"] label:hover div {
    background: rgba(255,255,255,0.07) !important;
    color: #e2e8f0 !important;
  }
  /* hide radio circle (first child div) and the raw input, NOT the text div after input */
  [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child { display: none !important; }
  [data-testid="stRadio"] label[data-baseweb="radio"] > input { display: none !important; }

  /* ── KPI Cards ── */
  .kpi-card {
    background: #10111a;
    border: 1px solid #181b28;
    border-left: 3px solid #4ecca3;
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    height: 100%;
  }
  .kpi-icon  { font-size: 1.1rem; opacity: 0.65; margin-bottom: 0.45rem; }
  .kpi-value {
    font-size: 1.8rem; font-weight: 700;
    color: #4ecca3; line-height: 1.1; margin-bottom: 0.3rem;
  }
  .kpi-label {
    font-size: 0.67rem; text-transform: uppercase;
    letter-spacing: 0.1em; color: #636b7a;
  }

  /* ── Page header ── */
  .page-header { margin-bottom: 0.75rem; }
  .page-title  {
    font-size: 1.45rem !important; font-weight: 700 !important;
    color: #e2e8f0 !important; margin: 0 !important; padding: 0 !important;
  }
  .page-subtitle { font-size: 0.82rem; color: #636b7a; margin: 3px 0 0 !important; }

  /* ── Section label ── */
  .section-label {
    font-size: 0.68rem; text-transform: uppercase;
    letter-spacing: 0.12em; color: #3a4255;
    margin: 1.25rem 0 0.4rem !important;
    display: flex; align-items: center; gap: 8px;
  }
  .section-label::after {
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, #181b28, transparent);
  }

  /* ── Misc ── */
  hr { border-color: #181b28 !important; margin: 1rem 0 !important; }
  h1, h2, h3, h4 { color: #e2e8f0 !important; }
  [data-testid="stDataFrame"] {
    border: 1px solid #181b28; border-radius: 8px; overflow: hidden;
  }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
TEXT_COLS = {"estado", "faixa_atraso", "estado_nome", "categoria",
             "tipo_pagamento", "mes"}

TEAL   = "#4ecca3"
CORAL  = "#ff6b6b"
BLUE   = "#4d9de0"
AMBER  = "#f7c948"
PURPLE = "#9b72ff"

ESTADO_NOME = {
    "AC": "Acre",            "AL": "Alagoas",          "AM": "Amazonas",
    "AP": "Amapá",           "BA": "Bahia",             "CE": "Ceará",
    "DF": "Distrito Federal","ES": "Espírito Santo",    "GO": "Goiás",
    "MA": "Maranhão",        "MG": "Minas Gerais",      "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso",     "PA": "Pará",              "PB": "Paraíba",
    "PE": "Pernambuco",      "PI": "Piauí",             "PR": "Paraná",
    "RJ": "Rio de Janeiro",  "RN": "Rio Grande do Norte","RO": "Rondônia",
    "RR": "Roraima",         "RS": "Rio Grande do Sul", "SC": "Santa Catarina",
    "SE": "Sergipe",         "SP": "São Paulo",         "TO": "Tocantins",
}

GEOJSON = ("https://raw.githubusercontent.com/codeforamerica/"
           "click_that_hood/master/public/data/brazil-states.geojson")

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_table(table_name):
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(f"SELECT * FROM analytics.{table_name}", con=conn)
    for col in df.columns:
        if col not in TEXT_COLS:
            try:
                df[col] = df[col].astype(float)
            except (ValueError, TypeError):
                pass
    return df

def try_load(table_name):
    """Load table without raising — returns None if unavailable."""
    try:
        return load_table(table_name)
    except Exception:
        return None

# ── UI helpers ────────────────────────────────────────────────────────────────
def kpi(value, label, icon="", color=TEAL):
    return f"""<div class="kpi-card" style="border-left-color:{color}">
  <div class="kpi-icon">{icon}</div>
  <div class="kpi-value" style="color:{color}">{value}</div>
  <div class="kpi-label">{label}</div>
</div>"""

def header(title, subtitle=""):
    sub = f'<p class="page-subtitle">{subtitle}</p>' if subtitle else ""
    return f'<div class="page-header"><p class="page-title">{title}</p>{sub}</div>'

def section(text):
    return f'<div class="section-label">{text}</div>'

# ── Chart helpers ─────────────────────────────────────────────────────────────
_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="system-ui,-apple-system,sans-serif", color="#636b7a", size=11),
    margin=dict(l=5, r=5, t=30, b=5),
    xaxis=dict(gridcolor="#12141e", linecolor="#181b28", zerolinecolor="#181b28"),
    yaxis=dict(gridcolor="#12141e", linecolor="#181b28", zerolinecolor="#181b28"),
    legend=dict(
        bgcolor="rgba(16,17,26,0.85)", bordercolor="#181b28", borderwidth=1,
        font=dict(color="#8892a4"),
    ),
    hoverlabel=dict(
        bgcolor="#12141e", bordercolor="#1e2235",
        font=dict(color="#e2e8f0", size=12),
    ),
    coloraxis=dict(colorbar=dict(
        tickfont=dict(color="#636b7a"),
        title_font=dict(color="#636b7a"),
        bgcolor="rgba(0,0,0,0)",
        bordercolor="#181b28",
    )),
)

def themed(fig, height=None, title=None):
    upd = dict(_BASE)
    if height:
        upd["height"] = height
    if title:
        upd["title"] = dict(text=title, font=dict(color="#c8d0de", size=13), x=0.01)
    fig.update_layout(**upd)
    return fig

def geo(fig):
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis=dict(colorbar=dict(
            tickfont=dict(color="#636b7a"),
            title_font=dict(color="#636b7a"),
        )),
    )
    return fig

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="padding:.5rem .25rem 1.1rem">
  <div style="font-size:1.25rem;font-weight:700;color:#4ecca3;letter-spacing:-.01em">
    📦 Olist KPI
  </div>
  <div style="font-size:.65rem;text-transform:uppercase;letter-spacing:.12em;
              color:#3a4255;margin-top:4px">
    Pipeline Dashboard
  </div>
</div>
<hr style="border-color:#181b28;margin:0 0 .6rem!important">
""", unsafe_allow_html=True)

    page = st.radio("", [
        "🏠  Visão Geral",
        "📦  On-Time Delivery",
        "⏱️  Lead Time",
        "⭐  Perfect Order",
        "💰  Custo de Frete",
        "😤  Atraso × Satisfação",
        "📈  Tendência Temporal",
        "🏷️  Categorias",
        "💳  Meios de Pagamento",
    ], label_visibility="collapsed")

    st.markdown("""
<hr style="border-color:#181b28;margin:.6rem 0 0!important">
<div style="font-size:.65rem;color:#636b7a;padding:.7rem .25rem 0;line-height:1.7">
  Fonte: Kaggle · Olist Dataset<br>
  2016 – 2018 · ~100 k pedidos
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# PÁGINA 1 — VISÃO GERAL
# ════════════════════════════════════════════════════════════════
if page == "🏠  Visão Geral":
    st.markdown(header("Visão Geral",
        "KPIs logísticos do marketplace Olist — 2016 a 2018"),
        unsafe_allow_html=True)

    otd = load_table("otd")
    lt  = load_table("lead_time")
    po  = load_table("perfect_order")
    fc  = load_table("freight_cost")

    total_pedidos  = int(otd["total_pedidos"].sum())
    receita_total  = float(fc["receita_total"].sum())

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.markdown(kpi(f"{total_pedidos:,}",                      "Total de pedidos",   "🛒", TEAL),   unsafe_allow_html=True)
    with c2: st.markdown(kpi(f"R${receita_total/1e6:.1f}M",             "Receita total",      "💵", BLUE),   unsafe_allow_html=True)
    with c3: st.markdown(kpi(f"{float(otd['otd_pct'].mean()):.1f}%",    "OTD médio",          "🎯", TEAL),   unsafe_allow_html=True)
    with c4: st.markdown(kpi(f"{float(lt['lead_time_total_dias'].mean()):.1f}d", "Lead time médio", "⏱️", AMBER), unsafe_allow_html=True)
    with c5: st.markdown(kpi(f"{float(po['perfect_order_pct'].mean()):.1f}%", "Perfect Order", "⭐", PURPLE), unsafe_allow_html=True)
    with c6: st.markdown(kpi(f"R${float(fc['frete_medio'].mean()):.0f}", "Frete médio",       "🚚", CORAL),  unsafe_allow_html=True)

    st.markdown("---")

    # Tendência temporal (disponível após rodar o pipeline com os novos SQLs)
    vt = try_load("volume_temporal")
    if vt is not None:
        st.markdown(section("Evolução de pedidos"), unsafe_allow_html=True)
        vt["mes"] = pd.to_datetime(vt["mes"])
        fig_trend = go.Figure(go.Scatter(
            x=vt["mes"], y=vt["total_pedidos"],
            mode="lines+markers",
            line=dict(color=TEAL, width=2.5),
            marker=dict(size=5, color=TEAL),
            fill="tozeroy",
            fillcolor="rgba(78,204,163,0.07)",
        ))
        st.plotly_chart(themed(fig_trend, height=190), use_container_width=True)
        st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(section("OTD por estado"), unsafe_allow_html=True)
        fig = px.choropleth(
            otd, geojson=GEOJSON,
            locations="estado", featureidkey="properties.sigla",
            color="otd_pct",
            color_continuous_scale=["#ff6b6b", "#f7c948", "#4ecca3"],
            range_color=[float(otd["otd_pct"].min()), 100],
            labels={"otd_pct": "OTD %"},
        )
        st.plotly_chart(geo(fig), use_container_width=True)

    with col_b:
        st.markdown(section("Lead time médio por estado — top 15 (dias)"), unsafe_allow_html=True)
        lt_s = lt.sort_values("lead_time_total_dias", ascending=True).tail(15)
        fig2 = px.bar(
            lt_s, x="lead_time_total_dias", y="estado", orientation="h",
            color="lead_time_total_dias",
            color_continuous_scale=["#4ecca3", "#f7c948", "#ff6b6b"],
            labels={"lead_time_total_dias": "Dias", "estado": ""},
        )
        st.plotly_chart(themed(fig2), use_container_width=True)


# ════════════════════════════════════════════════════════════════
# PÁGINA 2 — ON-TIME DELIVERY
# ════════════════════════════════════════════════════════════════
elif page == "📦  On-Time Delivery":
    df = load_table("otd")
    df["estado_nome"] = df["estado"].map(ESTADO_NOME)
    melhor = df.loc[df["otd_pct"].idxmax()]
    pior   = df.loc[df["otd_pct"].idxmin()]

    st.markdown(header("On-Time Delivery",
        "Percentual de pedidos entregues até ou antes da data estimada, por estado"),
        unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi(f"{float(melhor['otd_pct']):.1f}%", f"Melhor OTD — {melhor['estado']}", "🥇", TEAL),  unsafe_allow_html=True)
    with c2: st.markdown(kpi(f"{float(pior['otd_pct']):.1f}%",   f"Pior OTD — {pior['estado']}",    "⚠️", CORAL), unsafe_allow_html=True)
    with c3: st.markdown(kpi(f"{float(df['atraso_medio_dias'].mean()):.1f}d", "Atraso médio nacional", "📅", AMBER), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(section("Mapa OTD % por estado"), unsafe_allow_html=True)
    fig = px.choropleth(
        df, geojson=GEOJSON,
        locations="estado", featureidkey="properties.sigla",
        color="otd_pct",
        color_continuous_scale=["#ff6b6b", "#f7c948", "#4ecca3"],
        range_color=[float(df["otd_pct"].min()), 100],
        hover_name="estado_nome",
        hover_data={"estado": False, "otd_pct": True, "pedidos_atrasados": True},
        labels={"otd_pct": "OTD %", "pedidos_atrasados": "Atrasados"},
    )
    st.plotly_chart(geo(fig), use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(section("OTD % por estado"), unsafe_allow_html=True)
        fig2 = px.bar(
            df.sort_values("otd_pct"), x="otd_pct", y="estado", orientation="h",
            color="otd_pct",
            color_continuous_scale=["#ff6b6b", "#f7c948", "#4ecca3"],
            labels={"otd_pct": "OTD %", "estado": ""},
        )
        st.plotly_chart(themed(fig2), use_container_width=True)

    with col_b:
        st.markdown(section("Atraso médio por estado — top 15 (dias)"), unsafe_allow_html=True)
        fig3 = px.bar(
            df.sort_values("atraso_medio_dias", ascending=False).head(15),
            x="estado", y="atraso_medio_dias",
            color="atraso_medio_dias",
            color_continuous_scale=["#f7c948", "#ff6b6b"],
            labels={"atraso_medio_dias": "Dias de atraso", "estado": ""},
        )
        st.plotly_chart(themed(fig3), use_container_width=True)

    st.markdown(section("Dados completos"), unsafe_allow_html=True)
    st.dataframe(df.sort_values("otd_pct", ascending=False),
                 use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
# PÁGINA 3 — LEAD TIME
# ════════════════════════════════════════════════════════════════
elif page == "⏱️  Lead Time":
    df = load_table("lead_time")

    st.markdown(header("Lead Time de Entrega",
        "Tempo médio entre a compra e a entrega, decomposto em 3 etapas do processo"),
        unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi(f"{float(df['tempo_aprovacao_horas'].mean()):.1f}h", "Aprovação média", "🏦", BLUE),  unsafe_allow_html=True)
    with c2: st.markdown(kpi(f"{float(df['tempo_despacho_dias'].mean()):.1f}d",   "Despacho médio",  "📦", AMBER), unsafe_allow_html=True)
    with c3: st.markdown(kpi(f"{float(df['tempo_transito_dias'].mean()):.1f}d",   "Trânsito médio",  "🚚", CORAL), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(section("Decomposição despacho + trânsito por estado (dias)"), unsafe_allow_html=True)
    df_s = df.sort_values("lead_time_total_dias", ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Despacho", x=df_s["estado"], y=df_s["tempo_despacho_dias"], marker_color=CORAL))
    fig.add_trace(go.Bar(name="Trânsito", x=df_s["estado"], y=df_s["tempo_transito_dias"], marker_color=TEAL))
    fig.update_layout(barmode="stack")
    st.plotly_chart(themed(fig, height=320), use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(section("Média vs mediana por estado"), unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Média",   x=df_s["estado"], y=df_s["lead_time_total_dias"],  marker_color=BLUE))
        fig2.add_trace(go.Scatter(name="Mediana", x=df_s["estado"], y=df_s["lead_time_mediana_dias"],
                                  mode="lines+markers", line=dict(color=AMBER, width=2)))
        st.plotly_chart(themed(fig2), use_container_width=True)

    with col_b:
        st.markdown(section("% do tempo gasto no despacho por estado"), unsafe_allow_html=True)
        fig3 = px.bar(
            df.sort_values("pct_tempo_despacho", ascending=False),
            x="estado", y="pct_tempo_despacho",
            color="pct_tempo_despacho",
            color_continuous_scale=["#4ecca3", "#ff6b6b"],
            labels={"pct_tempo_despacho": "% no despacho", "estado": ""},
        )
        st.plotly_chart(themed(fig3), use_container_width=True)

    st.markdown(section("Dados completos"), unsafe_allow_html=True)
    st.dataframe(df.sort_values("lead_time_total_dias", ascending=False),
                 use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
# PÁGINA 4 — PERFECT ORDER
# ════════════════════════════════════════════════════════════════
elif page == "⭐  Perfect Order":
    df = load_table("perfect_order")
    df["estado_nome"] = df["estado"].map(ESTADO_NOME)
    total_pos = float(df["avaliacoes_positivas"].sum())
    total_all = float(df[["avaliacoes_positivas","avaliacoes_neutras","avaliacoes_negativas"]].sum(axis=1).sum())

    st.markdown(header("Perfect Order Rate",
        "Pedidos entregues no prazo e com avaliação ≥ 4 estrelas"),
        unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi(f"{float(df['perfect_order_pct'].mean()):.1f}%", "Perfect Order Rate nacional", "⭐", TEAL),   unsafe_allow_html=True)
    with c2: st.markdown(kpi(f"{float(df['nota_media'].mean()):.2f}",         "Nota média nacional",         "📊", PURPLE), unsafe_allow_html=True)
    with c3: st.markdown(kpi(f"{total_pos/total_all*100:.1f}%",               "Avaliações positivas",        "👍", BLUE),   unsafe_allow_html=True)

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(section("Perfect Order Rate por estado"), unsafe_allow_html=True)
        fig = px.bar(
            df.sort_values("perfect_order_pct"), x="perfect_order_pct", y="estado", orientation="h",
            color="perfect_order_pct",
            color_continuous_scale=["#ff6b6b", "#f7c948", "#4ecca3"],
            labels={"perfect_order_pct": "Perfect Order %", "estado": ""},
        )
        st.plotly_chart(themed(fig), use_container_width=True)

    with col_b:
        st.markdown(section("Nota média: no prazo vs atrasado — top 15"), unsafe_allow_html=True)
        df_s = df.sort_values("nota_media_no_prazo", ascending=False).head(15)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="No prazo", x=df_s["estado"], y=df_s["nota_media_no_prazo"], marker_color=TEAL))
        fig2.add_trace(go.Bar(name="Atrasado", x=df_s["estado"], y=df_s["nota_media_atrasado"], marker_color=CORAL))
        fig2.update_layout(barmode="group", yaxis=dict(range=[0, 5.5]))
        st.plotly_chart(themed(fig2), use_container_width=True)

    st.markdown(section("Distribuição de avaliações — top 10 estados por volume"), unsafe_allow_html=True)
    df_top = df.sort_values("total_pedidos", ascending=False).head(10)
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Positivas (≥4)", x=df_top["estado"], y=df_top["avaliacoes_positivas"], marker_color=TEAL))
    fig3.add_trace(go.Bar(name="Neutras (3)",    x=df_top["estado"], y=df_top["avaliacoes_neutras"],   marker_color=AMBER))
    fig3.add_trace(go.Bar(name="Negativas (≤2)", x=df_top["estado"], y=df_top["avaliacoes_negativas"], marker_color=CORAL))
    fig3.update_layout(barmode="stack")
    st.plotly_chart(themed(fig3, height=300), use_container_width=True)

    st.markdown(section("Dados completos"), unsafe_allow_html=True)
    st.dataframe(df.sort_values("perfect_order_pct", ascending=False),
                 use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
# PÁGINA 5 — CUSTO DE FRETE
# ════════════════════════════════════════════════════════════════
elif page == "💰  Custo de Frete":
    df = load_table("freight_cost")
    df["estado_nome"] = df["estado"].map(ESTADO_NOME)
    mais_caro = df.loc[df["frete_medio"].idxmax()]

    st.markdown(header("Custo de Frete",
        "Frete médio, ticket e proporção frete/produto por estado"),
        unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi(f"R${float(df['frete_medio'].mean()):.2f}",       "Frete médio nacional",            "🚚", TEAL),  unsafe_allow_html=True)
    with c2: st.markdown(kpi(f"{float(df['proporcao_frete_pct'].mean()):.1f}%","Frete / produto médio",           "📊", AMBER), unsafe_allow_html=True)
    with c3: st.markdown(kpi(f"R${float(mais_caro['frete_medio']):.2f}",       f"Maior frete — {mais_caro['estado']}", "⚠️", CORAL), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(section("Mapa — Frete médio por estado"), unsafe_allow_html=True)
    fig = px.choropleth(
        df, geojson=GEOJSON,
        locations="estado", featureidkey="properties.sigla",
        color="frete_medio",
        color_continuous_scale=["#4ecca3", "#f7c948", "#ff6b6b"],
        hover_name="estado_nome",
        hover_data={"estado": False, "frete_medio": True, "proporcao_frete_pct": True},
        labels={"frete_medio": "Frete médio (R$)", "proporcao_frete_pct": "% do produto"},
    )
    st.plotly_chart(geo(fig), use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(section("Frete médio vs ticket por estado"), unsafe_allow_html=True)
        fig2 = px.scatter(
            df, x="ticket_medio", y="frete_medio", text="estado",
            color="proporcao_frete_pct",
            color_continuous_scale=["#4ecca3", "#ff6b6b"],
            size="total_pedidos",
            labels={"ticket_medio": "Ticket médio (R$)", "frete_medio": "Frete médio (R$)",
                    "proporcao_frete_pct": "% frete"},
        )
        fig2.update_traces(textposition="top center", textfont_size=9)
        st.plotly_chart(themed(fig2), use_container_width=True)

    with col_b:
        st.markdown(section("Proporção frete / produto por estado (%)"), unsafe_allow_html=True)
        fig3 = px.bar(
            df.sort_values("proporcao_frete_pct", ascending=False),
            x="estado", y="proporcao_frete_pct",
            color="proporcao_frete_pct",
            color_continuous_scale=["#4ecca3", "#f7c948", "#ff6b6b"],
            labels={"proporcao_frete_pct": "% frete/produto", "estado": ""},
        )
        st.plotly_chart(themed(fig3), use_container_width=True)

    st.markdown(section("Dados completos"), unsafe_allow_html=True)
    st.dataframe(df.sort_values("frete_medio", ascending=False),
                 use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
# PÁGINA 6 — ATRASO × SATISFAÇÃO
# ════════════════════════════════════════════════════════════════
elif page == "😤  Atraso × Satisfação":
    df = load_table("delay_vs_satisfaction")
    ordem = ["No prazo", "Atraso leve (1-3 dias)",
             "Atraso moderado (4-7 dias)", "Atraso grave (8+ dias)"]
    df["faixa_atraso"] = pd.Categorical(df["faixa_atraso"], categories=ordem, ordered=True)
    df = df.sort_values("faixa_atraso")
    no_prazo = df[df["faixa_atraso"] == "No prazo"].iloc[0]
    grave    = df[df["faixa_atraso"] == "Atraso grave (8+ dias)"].iloc[0]
    queda    = float(no_prazo["nota_media"]) - float(grave["nota_media"])

    st.markdown(header("Atraso × Satisfação",
        "Impacto quantificado do atraso na nota de avaliação do cliente"),
        unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi(f"{float(no_prazo['nota_media']):.2f}", "Nota média — no prazo",      "✅", TEAL),  unsafe_allow_html=True)
    with c2: st.markdown(kpi(f"{float(grave['nota_media']):.2f}",    "Nota média — atraso grave",  "❌", CORAL), unsafe_allow_html=True)
    with c3: st.markdown(kpi(f"-{queda:.2f}",                        "Queda prazo → grave",        "📉", AMBER), unsafe_allow_html=True)

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(section("Nota média por faixa de atraso"), unsafe_allow_html=True)
        fig = px.line(df, x="faixa_atraso", y="nota_media", markers=True,
                      labels={"faixa_atraso": "", "nota_media": "Nota média"},
                      color_discrete_sequence=[TEAL])
        fig.update_traces(line=dict(width=3), marker=dict(size=10))
        st.plotly_chart(themed(fig), use_container_width=True)

    with col_b:
        st.markdown(section("% de avaliações negativas por faixa"), unsafe_allow_html=True)
        fig2 = px.bar(df, x="faixa_atraso", y="pct_negativas",
                      color="pct_negativas",
                      color_continuous_scale=["#4ecca3", "#f7c948", "#ff6b6b"],
                      labels={"faixa_atraso": "", "pct_negativas": "% negativas"})
        st.plotly_chart(themed(fig2), use_container_width=True)

    st.markdown(section("Distribuição completa de notas por faixa"), unsafe_allow_html=True)
    notas = df[["faixa_atraso","nota_5","nota_4","nota_3","nota_2","nota_1"]].melt(
        id_vars="faixa_atraso", var_name="nota", value_name="quantidade")
    fig3 = px.bar(
        notas, x="faixa_atraso", y="quantidade", color="nota", barmode="group",
        color_discrete_map={"nota_5": TEAL, "nota_4": BLUE, "nota_3": AMBER,
                            "nota_2": CORAL, "nota_1": "#c0392b"},
        labels={"faixa_atraso": "", "quantidade": "Pedidos", "nota": "Nota"},
    )
    st.plotly_chart(themed(fig3, height=320), use_container_width=True)

    st.markdown(section("Dados completos"), unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
# PÁGINA 7 — TENDÊNCIA TEMPORAL
# ════════════════════════════════════════════════════════════════
elif page == "📈  Tendência Temporal":
    df = load_table("volume_temporal")
    df["mes"] = pd.to_datetime(df["mes"])

    st.markdown(header("Tendência Temporal",
        "Evolução mensal de pedidos e receita — jan/2017 a ago/2018"),
        unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi(f"{int(df['total_pedidos'].sum()):,}", "Total de pedidos no período", "🛒", TEAL),  unsafe_allow_html=True)
    with c2: st.markdown(kpi(f"R${df['receita_total'].sum()/1e6:.1f}M", "Receita total no período", "💵", BLUE), unsafe_allow_html=True)
    with c3: st.markdown(kpi(f"R${float(df['ticket_medio'].mean()):.0f}", "Ticket médio por pedido", "🎫", AMBER), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(section("Volume de pedidos por mês"), unsafe_allow_html=True)
    fig = go.Figure(go.Scatter(
        x=df["mes"],
        y=df["total_pedidos"],
        mode="lines+markers",
        line=dict(color=TEAL, width=2.5),
        marker=dict(size=6, color=TEAL),
        fill="tozeroy",
        fillcolor="rgba(78,204,163,0.07)",
        name="Pedidos",
    ))
    st.plotly_chart(themed(fig, height=270), use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(section("Receita mensal (R$)"), unsafe_allow_html=True)
        fig2 = px.bar(df, x="mes", y="receita_total",
                      color_discrete_sequence=[BLUE],
                      labels={"mes": "", "receita_total": "Receita (R$)"})
        st.plotly_chart(themed(fig2, height=250), use_container_width=True)

    with col_b:
        st.markdown(section("Ticket médio por mês (R$)"), unsafe_allow_html=True)
        fig3 = px.line(df, x="mes", y="ticket_medio", markers=True,
                       color_discrete_sequence=[AMBER],
                       labels={"mes": "", "ticket_medio": "Ticket médio (R$)"})
        fig3.update_traces(line=dict(width=2.5), marker=dict(size=7))
        st.plotly_chart(themed(fig3, height=250), use_container_width=True)

    st.markdown(section("Dados completos"), unsafe_allow_html=True)
    df_disp = df.copy()
    df_disp["mes"] = df_disp["mes"].dt.strftime("%b/%Y")
    st.dataframe(df_disp, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
# PÁGINA 8 — CATEGORIAS
# ════════════════════════════════════════════════════════════════
elif page == "🏷️  Categorias":
    df = load_table("categorias")
    top1 = df.iloc[0]

    st.markdown(header("Categorias de Produto",
        "Top 20 categorias por receita em pedidos entregues"),
        unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi(top1["categoria"].replace("_"," ").title(), "Categoria top 1 em receita", "🏆", TEAL), unsafe_allow_html=True)
    with c2: st.markdown(kpi(f"R${df['receita_total'].sum()/1e6:.1f}M", "Receita total top 20",        "💰", BLUE), unsafe_allow_html=True)
    with c3: st.markdown(kpi(f"R${float(df['ticket_medio'].mean()):.0f}","Ticket médio geral",         "🎫", AMBER), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(section("Receita por categoria — área proporcional"), unsafe_allow_html=True)
    fig_tree = px.treemap(
        df, path=["categoria"], values="receita_total",
        color="ticket_medio",
        color_continuous_scale=["#1a1d2e", "#4d9de0", "#4ecca3"],
        labels={"receita_total": "Receita (R$)", "ticket_medio": "Ticket médio"},
        hover_data={"total_pedidos": True, "proporcao_frete_pct": True},
    )
    fig_tree.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=5, b=0),
        height=370,
        coloraxis=dict(colorbar=dict(tickfont=dict(color="#636b7a"), title_font=dict(color="#636b7a"))),
    )
    st.plotly_chart(fig_tree, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(section("Ticket médio por categoria"), unsafe_allow_html=True)
        fig2 = px.bar(
            df.sort_values("ticket_medio", ascending=True),
            x="ticket_medio", y="categoria", orientation="h",
            color="ticket_medio",
            color_continuous_scale=["#4ecca3", "#4d9de0"],
            labels={"ticket_medio": "Ticket médio (R$)", "categoria": ""},
        )
        st.plotly_chart(themed(fig2), use_container_width=True)

    with col_b:
        st.markdown(section("Proporção frete/produto por categoria (%)"), unsafe_allow_html=True)
        fig3 = px.bar(
            df.sort_values("proporcao_frete_pct", ascending=False),
            x="categoria", y="proporcao_frete_pct",
            color="proporcao_frete_pct",
            color_continuous_scale=["#4ecca3", "#f7c948", "#ff6b6b"],
            labels={"proporcao_frete_pct": "% frete/produto", "categoria": ""},
        )
        fig3.update_layout(xaxis=dict(tickangle=-40))
        st.plotly_chart(themed(fig3), use_container_width=True)

    st.markdown(section("Dados completos"), unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
# PÁGINA 9 — MEIOS DE PAGAMENTO
# ════════════════════════════════════════════════════════════════
elif page == "💳  Meios de Pagamento":
    df = load_table("pagamentos")
    cartao      = df[df["tipo_pagamento"] == "Cartão de Crédito"].iloc[0]
    total_trans = float(df["total_transacoes"].sum())

    st.markdown(header("Meios de Pagamento",
        "Distribuição e comportamento de pagamento no marketplace"),
        unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi(f"{float(cartao['total_transacoes'])/total_trans*100:.1f}%", "% transações no cartão",       "💳", TEAL),  unsafe_allow_html=True)
    with c2: st.markdown(kpi(f"{float(cartao['parcelas_medias']):.1f}x",                  "Parcelamento médio (crédito)", "📅", AMBER), unsafe_allow_html=True)
    with c3: st.markdown(kpi(f"R${float(df['ticket_medio'].mean()):.0f}",                 "Ticket médio geral",           "💵", BLUE),  unsafe_allow_html=True)

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(section("Distribuição de transações por método"), unsafe_allow_html=True)
        fig_pie = px.pie(
            df, names="tipo_pagamento", values="total_transacoes",
            hole=0.55,
            color_discrete_sequence=[TEAL, BLUE, AMBER, CORAL],
        )
        fig_pie.update_traces(
            textfont_color="#e2e8f0",
            marker=dict(line=dict(color="#080910", width=3)),
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(font=dict(color="#8892a4"), bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        st.markdown(section("Ticket médio por método (R$)"), unsafe_allow_html=True)
        fig2 = px.bar(
            df.sort_values("ticket_medio", ascending=True),
            x="ticket_medio", y="tipo_pagamento", orientation="h",
            color="ticket_medio",
            color_continuous_scale=["#4d9de0", "#4ecca3"],
            labels={"ticket_medio": "Ticket médio (R$)", "tipo_pagamento": ""},
        )
        st.plotly_chart(themed(fig2), use_container_width=True)

    st.markdown(section("% de transações parceladas por método"), unsafe_allow_html=True)
    df_sorted = df.sort_values("pct_parcelado", ascending=False)
    fig3 = px.bar(
        df_sorted, x="tipo_pagamento", y="pct_parcelado",
        color="pct_parcelado",
        color_continuous_scale=["#4ecca3", "#f7c948", "#ff6b6b"],
        text=df_sorted["pct_parcelado"].apply(lambda x: f"{x:.1f}%"),
        labels={"pct_parcelado": "% parcelado", "tipo_pagamento": ""},
    )
    fig3.update_traces(textfont_color="#e2e8f0", textposition="outside")
    st.plotly_chart(themed(fig3, height=260), use_container_width=True)

    st.markdown(section("Dados completos"), unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
