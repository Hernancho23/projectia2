import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import numpy as np
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Cementos Argos · Análisis Bursátil",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# ESTILOS CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

/* Variables de color */
:root {
    --argos-red:     #C0392B;
    --argos-dark:    #1A1A2E;
    --argos-gray:    #2D2D44;
    --argos-light:   #F5F0EB;
    --argos-gold:    #D4A843;
    --argos-teal:    #16A085;
    --argos-border:  rgba(212, 168, 67, 0.25);
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--argos-dark);
    color: var(--argos-light);
}

/* Header hero */
.hero-header {
    background: linear-gradient(135deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%);
    border: 1px solid var(--argos-border);
    border-radius: 16px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(192,57,43,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.6rem;
    color: var(--argos-light);
    margin: 0;
    line-height: 1.1;
}
.hero-title span {
    color: var(--argos-gold);
}
.hero-subtitle {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: rgba(245,240,235,0.5);
    margin-top: 0.5rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
.hero-ticker {
    font-family: 'DM Mono', monospace;
    font-size: 0.85rem;
    background: rgba(212,168,67,0.15);
    border: 1px solid var(--argos-border);
    border-radius: 6px;
    padding: 0.25rem 0.75rem;
    color: var(--argos-gold);
    display: inline-block;
    margin-top: 1rem;
}

/* Tarjetas de métricas */
.metric-card {
    background: linear-gradient(145deg, #2D2D44, #1f1f35);
    border: 1px solid var(--argos-border);
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.metric-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: rgba(245,240,235,0.55);
    font-family: 'DM Mono', monospace;
}
.metric-value {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    margin: 0.2rem 0;
}
.metric-delta-pos { color: var(--argos-teal); font-size: 0.82rem; }
.metric-delta-neg { color: var(--argos-red);  font-size: 0.82rem; }

/* Sección de gráfico */
.chart-section {
    background: #1f1f35;
    border: 1px solid var(--argos-border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}
.chart-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.25rem;
    color: var(--argos-light);
    margin-bottom: 0.2rem;
}
.chart-desc {
    font-size: 0.78rem;
    color: rgba(245,240,235,0.45);
    margin-bottom: 1rem;
    font-family: 'DM Mono', monospace;
}

/* Interpretación */
.interp-box {
    background: linear-gradient(135deg, rgba(22,160,133,0.12), rgba(22,160,133,0.05));
    border-left: 3px solid var(--argos-teal);
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.25rem;
    margin: 0.5rem 0;
    font-size: 0.88rem;
}
.interp-box.neg {
    background: linear-gradient(135deg, rgba(192,57,43,0.12), rgba(192,57,43,0.05));
    border-left-color: var(--argos-red);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #16213E !important;
    border-right: 1px solid var(--argos-border);
}
section[data-testid="stSidebar"] * {
    color: var(--argos-light) !important;
}

/* Divider */
hr { border-color: var(--argos-border); }

/* Streamlit metric override */
[data-testid="stMetricValue"] {
    font-family: 'DM Serif Display', serif !important;
    font-size: 1.9rem !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    opacity: 0.65;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data():
    end   = datetime.today()
    start = end - timedelta(days=185)  # ~6 meses + margen

    tickers = {
        "CEMARGOS": "CEMARGOS.CL",
        "ICOLCAP":  "ICOLCAP.CL",
        "TRM":      "COP=X",
    }

    raw = {}
    for key, tkr in tickers.items():
        df = yf.download(tkr, start=start, end=end, auto_adjust=True, progress=False)
        if not df.empty:
            raw[key] = df["Close"].rename(key)

    combined = pd.concat(raw.values(), axis=1)
    combined.index = pd.to_datetime(combined.index)
    combined.index = combined.index.tz_localize(None)
    combined = combined.dropna()
    combined = combined.sort_index()
    return combined


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏗️ Cementos Argos")
    st.markdown("**Análisis Bursátil · Dashboard**")
    st.markdown("---")

    st.markdown("#### 📅 Rango de fechas")

    df_full = load_data()

    min_date = df_full.index.min().date()
    max_date = df_full.index.max().date()

    date_range = st.date_input(
        "Selecciona el período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        help="Filtra los datos del dashboard en este rango.",
    )

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_sel, end_sel = date_range
    else:
        start_sel, end_sel = min_date, max_date

    st.markdown("---")
    st.markdown("#### ℹ️ Variables")
    st.markdown("""
    | Símbolo | Variable |
    |---|---|
    | `CEMARGOS.CL` | Cementos Argos (Y) |
    | `ICOLCAP.CL` | COLCAP ETF (X₁) |
    | `COP=X` | TRM USD/COP (X₂) |
    """)
    st.markdown("---")
    st.caption("Datos: Yahoo Finance · yfinance")
    st.caption("Entrega académica · Análisis de Regresión")


# ─────────────────────────────────────────────
# FILTRADO POR FECHA
# ─────────────────────────────────────────────
df = df_full[
    (df_full.index.date >= start_sel) &
    (df_full.index.date <= end_sel)
].copy()

n = len(df)


# ─────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="hero-header">
    <p class="hero-subtitle">Universidad · Análisis Cuantitativo de Acciones</p>
    <h1 class="hero-title">Cementos <span>Argos</span></h1>
    <p class="hero-subtitle" style="margin-top:0.6rem;">
        Regresión múltiple: COLCAP · TRM · Precio de cierre
    </p>
    <span class="hero-ticker">CEMARGOS.CL</span>
    <span class="hero-ticker" style="margin-left:0.5rem;">n = {n} observaciones</span>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# VALIDACIÓN DE DATOS
# ─────────────────────────────────────────────
if n < 10:
    st.error(f"⚠️ Solo hay {n} registros en el rango seleccionado. Amplía el período para ver los gráficos.")
    st.stop()

if n < 90:
    st.warning(f"⚠️ Se tienen {n} observaciones. Se recomiendan al menos 90 para mayor robustez estadística.")


# ─────────────────────────────────────────────
# CORRELACIONES Y MÉTRICAS
# ─────────────────────────────────────────────
corr_colcap, pval_colcap = stats.pearsonr(df["CEMARGOS"], df["ICOLCAP"])
corr_trm,    pval_trm    = stats.pearsonr(df["CEMARGOS"], df["TRM"])

ultimo_precio  = float(df["CEMARGOS"].iloc[-1])
penult_precio  = float(df["CEMARGOS"].iloc[-2]) if n > 1 else ultimo_precio
delta_precio   = ultimo_precio - penult_precio
pct_delta      = (delta_precio / penult_precio) * 100 if penult_precio else 0

# ── Fila de métricas ──
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Último cierre · CEMARGOS",
        value=f"${ultimo_precio:,.0f} COP",
        delta=f"{pct_delta:+.2f}% vs día anterior",
    )
with col2:
    st.metric(
        label="Correlación Pearson (vs COLCAP)",
        value=f"{corr_colcap:.4f}",
        delta="Positiva ↑" if corr_colcap > 0 else "Negativa ↓",
    )
with col3:
    st.metric(
        label="Correlación Pearson (vs TRM)",
        value=f"{corr_trm:.4f}",
        delta="Positiva ↑" if corr_trm > 0 else "Negativa ↓",
    )
with col4:
    st.metric(
        label="Observaciones en rango",
        value=f"{n}",
        delta="✓ Suficientes" if n >= 90 else "⚠ < 90",
    )

st.markdown("---")


# ─────────────────────────────────────────────
# HELPER: PLOTLY THEME
# ─────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="#1f1f35",
    plot_bgcolor="#1f1f35",
    font=dict(family="DM Sans, sans-serif", color="#F5F0EB"),
    xaxis=dict(gridcolor="rgba(212,168,67,0.1)", zerolinecolor="rgba(212,168,67,0.2)"),
    yaxis=dict(gridcolor="rgba(212,168,67,0.1)", zerolinecolor="rgba(212,168,67,0.2)"),
    margin=dict(l=40, r=20, t=50, b=40),
)


# ─────────────────────────────────────────────
# GRÁFICO 1: SERIE TEMPORAL
# ─────────────────────────────────────────────
st.markdown('<div class="chart-section">', unsafe_allow_html=True)
st.markdown('<p class="chart-title">📈 Precio histórico · Cementos Argos</p>', unsafe_allow_html=True)
st.markdown('<p class="chart-desc">Serie temporal del precio de cierre ajustado (COP)</p>', unsafe_allow_html=True)

fig_ts = go.Figure()
fig_ts.add_trace(go.Scatter(
    x=df.index, y=df["CEMARGOS"],
    mode="lines",
    name="CEMARGOS",
    line=dict(color="#D4A843", width=2),
    fill="tozeroy",
    fillcolor="rgba(212,168,67,0.08)",
))
fig_ts.add_trace(go.Scatter(
    x=df.index, y=df["CEMARGOS"].rolling(20).mean(),
    mode="lines",
    name="Media móvil 20d",
    line=dict(color="#C0392B", width=1.5, dash="dot"),
))
fig_ts.update_layout(
    **PLOTLY_LAYOUT,
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(212,168,67,0.2)"),
    hovermode="x unified",
    height=320,
)
st.plotly_chart(fig_ts, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# GRÁFICOS 2 & 3: DISPERSIÓN
# ─────────────────────────────────────────────
col_a, col_b = st.columns(2)

# ── Scatter: Argos vs COLCAP ──
with col_a:
    st.markdown('<div class="chart-section">', unsafe_allow_html=True)
    st.markdown('<p class="chart-title">🔵 Argos vs. COLCAP</p>', unsafe_allow_html=True)
    st.markdown('<p class="chart-desc">Dispersión con línea de tendencia OLS</p>', unsafe_allow_html=True)

    slope1, intercept1, r1, p1, se1 = stats.linregress(df["ICOLCAP"], df["CEMARGOS"])
    x_line1 = np.linspace(df["ICOLCAP"].min(), df["ICOLCAP"].max(), 100)
    y_line1  = slope1 * x_line1 + intercept1

    fig_sc1 = go.Figure()
    fig_sc1.add_trace(go.Scatter(
        x=df["ICOLCAP"], y=df["CEMARGOS"],
        mode="markers",
        name="Observaciones",
        marker=dict(color="#D4A843", size=6, opacity=0.7, line=dict(color="#1f1f35", width=0.5)),
    ))
    fig_sc1.add_trace(go.Scatter(
        x=x_line1, y=y_line1,
        mode="lines",
        name=f"Tendencia (r={r1:.3f})",
        line=dict(color="#16A085", width=2),
    ))
    fig_sc1.update_layout(
        **PLOTLY_LAYOUT,
        xaxis_title="ICOLCAP (COP)",
        yaxis_title="CEMARGOS (COP)",
        height=340,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_sc1, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Scatter: Argos vs TRM ──
with col_b:
    st.markdown('<div class="chart-section">', unsafe_allow_html=True)
    st.markdown('<p class="chart-title">🔴 Argos vs. TRM (USD/COP)</p>', unsafe_allow_html=True)
    st.markdown('<p class="chart-desc">Dispersión con línea de tendencia OLS</p>', unsafe_allow_html=True)

    slope2, intercept2, r2, p2, se2 = stats.linregress(df["TRM"], df["CEMARGOS"])
    x_line2 = np.linspace(df["TRM"].min(), df["TRM"].max(), 100)
    y_line2  = slope2 * x_line2 + intercept2

    fig_sc2 = go.Figure()
    fig_sc2.add_trace(go.Scatter(
        x=df["TRM"], y=df["CEMARGOS"],
        mode="markers",
        name="Observaciones",
        marker=dict(color="#C0392B", size=6, opacity=0.7, line=dict(color="#1f1f35", width=0.5)),
    ))
    fig_sc2.add_trace(go.Scatter(
        x=x_line2, y=y_line2,
        mode="lines",
        name=f"Tendencia (r={r2:.3f})",
        line=dict(color="#D4A843", width=2),
    ))
    fig_sc2.update_layout(
        **PLOTLY_LAYOUT,
        xaxis_title="TRM · USD/COP",
        yaxis_title="CEMARGOS (COP)",
        height=340,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_sc2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# GRÁFICO 4: DOBLE EJE TEMPORAL (ARGOS + TRM)
# ─────────────────────────────────────────────
st.markdown('<div class="chart-section">', unsafe_allow_html=True)
st.markdown('<p class="chart-title">📊 Argos vs. TRM · Evolución temporal</p>', unsafe_allow_html=True)
st.markdown('<p class="chart-desc">Comparación normalizada de ambas series en el tiempo</p>', unsafe_allow_html=True)

df_norm = (df[["CEMARGOS", "TRM"]] - df[["CEMARGOS", "TRM"]].mean()) / df[["CEMARGOS", "TRM"]].std()

fig_dual = go.Figure()
fig_dual.add_trace(go.Scatter(
    x=df.index, y=df_norm["CEMARGOS"],
    name="CEMARGOS (norm.)", mode="lines",
    line=dict(color="#D4A843", width=2),
))
fig_dual.add_trace(go.Scatter(
    x=df.index, y=df_norm["TRM"],
    name="TRM (norm.)", mode="lines",
    line=dict(color="#C0392B", width=2, dash="dash"),
))
fig_dual.update_layout(
    **PLOTLY_LAYOUT,
    hovermode="x unified",
    height=300,
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)
st.plotly_chart(fig_dual, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# INTERPRETACIÓN DE CORRELACIONES
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🧠 Interpretación de correlaciones")

col_i1, col_i2 = st.columns(2)

with col_i1:
    if corr_colcap > 0:
        sentiment = "positiva"
        box_class = "interp-box"
        icon = "📈"
        texto = (
            f"La correlación de Pearson con el COLCAP es **{corr_colcap:.4f}** ({sentiment}). "
            "Esto indica que cuando el índice bursátil colombiano sube, el precio de Argos "
            "tiende a subir también. Argos se mueve en la misma dirección que el mercado, "
            "lo que es esperable para una acción de alta capitalización incluida en el índice."
        )
    else:
        sentiment = "negativa"
        box_class = "interp-box neg"
        icon = "📉"
        texto = (
            f"La correlación de Pearson con el COLCAP es **{corr_colcap:.4f}** ({sentiment}). "
            "Esto indica que Argos se mueve en sentido contrario al mercado general, "
            "lo que podría señalar factores idiosincráticos o una dinámica sectorial particular."
        )
    st.markdown(f"**{icon} Argos vs. COLCAP (X₁)**")
    st.markdown(f'<div class="{box_class}">{texto}</div>', unsafe_allow_html=True)

with col_i2:
    if corr_trm > 0:
        sentiment = "positiva"
        box_class = "interp-box"
        icon = "💵"
        texto = (
            f"La correlación de Pearson con la TRM es **{corr_trm:.4f}** ({sentiment}). "
            "Un dólar más caro podría beneficiar a Argos si exporta cemento u obtiene "
            "ingresos en divisas, ya que sus ventas internacionales valen más en pesos."
        )
    else:
        sentiment = "negativa"
        box_class = "interp-box neg"
        icon = "💵"
        texto = (
            f"La correlación de Pearson con la TRM es **{corr_trm:.4f}** ({sentiment}). "
            "Un dólar más caro encarece los insumos importados (carbón, clinker) y "
            "la deuda en dólares, lo que presiona los costos de Argos y reduce su margen, "
            "reflejándose en un precio de acción más bajo."
        )
    st.markdown(f"**{icon} Argos vs. TRM (X₂)**")
    st.markdown(f'<div class="{box_class}">{texto}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TABLA DE DATOS
# ─────────────────────────────────────────────
with st.expander("🗃️ Ver tabla de datos completa"):
    df_show = df.copy()
    df_show.index = df_show.index.strftime("%Y-%m-%d")
    df_show.columns = ["CEMARGOS (COP)", "ICOLCAP (COP)", "TRM (USD/COP)"]
    st.dataframe(
        df_show.style.format("{:,.2f}"),
        use_container_width=True,
        height=300,
    )
    st.caption(f"Total: {n} observaciones · Fuente: Yahoo Finance")


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="text-align:center; font-family: DM Mono, monospace; font-size:0.72rem; '
    'opacity:0.4; color:#F5F0EB;">Cementos Argos · Dashboard Académico · '
    'Datos: Yahoo Finance · yfinance · Plotly · Streamlit</p>',
    unsafe_allow_html=True,
)
