import base64
import html
import re
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Se deja desactivado el componente de clic directo para que el cursor sea limpio.
# La interacción principal de la línea será por hover y el análisis se controla con el selector.
PLOTLY_EVENTS_AVAILABLE = False
plotly_events = None


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Visualizador de cambios",
    layout="wide",
    initial_sidebar_state="expanded"
)

PALETA = {
    "azul_auteco": "#003A70",
    "azul_medio": "#0E67A9",
    "azul_claro": "#18A7D7",
    "rojo_auteco": "#E30613",
    "gris": "#8A8C8E",
    "gris_claro": "#E6E8EB",
    "gris_fondo": "#F7F9FC",
    "negro": "#222222",
    "verde": "#00C83A",
    "verde_suave": "#E1F4E8",
    "blanco": "#FFFFFF",
    "amarillo_suave": "#FFF4CC",
    "gris_texto": "#5D6677"
}


# ============================================================
# HTML / CSS
# ============================================================

def render_html(markup: str):
    st.markdown(textwrap.dedent(markup).strip(), unsafe_allow_html=True)


render_html(
    """
    <style>
    .block-container {
        padding-top: 2.0rem;
        padding-bottom: 2rem;
        max-width: 1640px;
    }

    [data-testid="stSidebar"] {
        background: #F5F7FA;
        border-right: 1px solid #E6E8EB;
    }

    .header-card {
        display: flex;
        align-items: center;
        gap: 24px;
        background: #FFFFFF;
        border: 1px solid #E6E8EB;
        border-radius: 20px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0px 3px 14px rgba(0,0,0,0.05);
        overflow: visible;
    }

    .header-logo {
        max-width: 150px;
        max-height: 78px;
        object-fit: contain;
        flex-shrink: 0;
    }

    .hero-title {
        font-size: 2.05rem;
        font-weight: 850;
        color: #1D2A44;
        line-height: 1.20;
        margin: 0 0 0.30rem 0;
        overflow: visible;
    }

    .hero-subtitle {
        color: #6A6F7A;
        font-size: 1.00rem;
        margin: 0;
        line-height: 1.35;
    }

    .instruction-box {
        background: #F7F9FC;
        border: 1px solid #E6E8EB;
        border-radius: 16px;
        padding: 14px 18px;
        margin: 8px 0 18px 0;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.03);
    }

    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E6E8EB;
        border-radius: 18px;
        padding: 16px 14px;
        text-align: center;
        box-shadow: 0px 3px 14px rgba(0,0,0,0.06);
        min-height: 96px;
    }

    .kpi-label {
        font-size: 0.83rem;
        color: #6A6F7A;
        margin-bottom: 7px;
    }

    .kpi-value {
        font-size: 1.55rem;
        font-weight: 800;
        color: #003A70;
    }

    .section-card {
        background: #FFFFFF;
        border: 1px solid #E6E8EB;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0px 3px 14px rgba(0,0,0,0.05);
        margin-bottom: 14px;
    }

    .mini-card {
        background: #F7F9FC;
        border: 1px solid #E6E8EB;
        border-radius: 16px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }

    .change-card {
        background: #FFFFFF;
        border-left: 6px solid #0E67A9;
        border-radius: 16px;
        padding: 14px 16px;
        margin-bottom: 10px;
        box-shadow: 0px 3px 12px rgba(0,0,0,0.05);
    }

    .change-card-red { border-left: 6px solid #E30613; }
    .change-card-green { border-left: 6px solid #2E7D32; }
    .change-card-gray { border-left: 6px solid #8A8C8E; }

    .change-title {
        font-size: 1rem;
        font-weight: 800;
        color: #003A70;
        margin-bottom: 5px;
    }

    .change-desc {
        font-size: 0.90rem;
        color: #2E3440;
        margin-bottom: 8px;
        line-height: 1.35;
    }

    .tag {
        display: inline-block;
        background: #E6E8EB;
        color: #222222;
        border-radius: 20px;
        padding: 4px 10px;
        font-size: 0.78rem;
        margin-right: 5px;
        margin-top: 4px;
        white-space: nowrap;
    }

    .tag-blue { background: #D9ECFA; color: #003A70; }
    .tag-red { background: #FDE1E3; color: #A4000B; }
    .tag-green { background: #E1F4E8; color: #1B5E20; }
    .tag-gray { background: #ECEFF1; color: #455A64; }
    .tag-yellow { background: #FFF4CC; color: #7A5200; }

    .small-title {
        font-size: 0.95rem;
        font-weight: 800;
        color: #003A70;
        margin-bottom: 6px;
    }

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        padding: 12px 14px;
        border: 1px solid #E6E8EB;
        border-radius: 16px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.04);
    }

    div[data-testid="stSelectbox"] label,
    div[data-testid="stMultiSelect"] label,
    div[data-testid="stTextInput"] label {
        font-weight: 700;
        color: #1D2A44;
    }

    /* Ajuste de indicadores: evita textos gigantes y recortados */
    div[data-testid="stMetric"] {
        min-height: 96px;
        overflow: visible;
    }

    div[data-testid="stMetric"] label {
        font-size: 0.86rem !important;
        color: #4B5563 !important;
        line-height: 1.15 !important;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.30rem !important;
        line-height: 1.25 !important;
        color: #1D2A44 !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }

    div[data-testid="stMetricValue"] > div {
        font-size: 1.30rem !important;
        line-height: 1.25 !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }

    </style>
    """
)


# ============================================================
# UTILIDADES GENERALES
# ============================================================

def find_asset(candidates):
    folder = Path(".")
    for name in candidates:
        path = folder / name
        if path.exists():
            return path
    return None


def image_to_data_uri(path):
    suffix = path.suffix.lower()
    mime = "image/png"
    if suffix in [".jpg", ".jpeg"]:
        mime = "image/jpeg"
    elif suffix == ".svg":
        mime = "image/svg+xml"

    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}"


def cargar_logo():
    return find_asset([
        "auteco_logo.png",
        "auteco_logo.jpg",
        "auteco_logo.jpeg",
        "logo_auteco.png",
        "logo.png"
    ])


def extraer_numero_estacion(estacion_id):
    texto = str(estacion_id).upper().strip()
    match = re.search(r"(\d+)", texto)
    if match:
        return int(match.group(1))
    return 999


def custom_station_order(estacion_id):
    est = str(estacion_id).upper().strip()

    if est in ["SEC", "SUB", "SUBENSAMBLE"]:
        return (0, 0, est)
    if est == "1RH":
        return (1, 1, est)
    if est == "1LH":
        return (2, 1, est)

    n = extraer_numero_estacion(est)

    if est.endswith("LH"):
        return (3, n, 0)
    if est.endswith("RH"):
        return (3, n, 1)

    return (9, n, est)


def ordenar_estaciones(lista_estaciones):
    return sorted([str(x) for x in lista_estaciones], key=custom_station_order)


def mostrar_kpi_card(label, value):
    render_html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{html.escape(str(label))}</div>
            <div class="kpi-value">{html.escape(str(value))}</div>
        </div>
        """
    )


def truncar_texto(texto, limite=160):
    texto = str(texto)
    if len(texto) <= limite:
        return texto
    return texto[:limite].rstrip() + "..."


def texto_cambio(valor, unidad="", dec=2):
    """Devuelve Aumentó, Disminuyó o Sin cambio sin mostrar signos negativos."""
    try:
        valor = float(valor)
    except Exception:
        return "Sin dato"

    if abs(valor) < 1e-9:
        return "Sin cambio"

    palabra = "Aumentó" if valor > 0 else "Disminuyó"
    magnitud = abs(valor)

    if unidad:
        return f"{palabra} {magnitud:.{dec}f} {unidad}"
    return f"{palabra} {magnitud:.{dec}f}"


def texto_cambio_metric(valor, unidad="", dec=2):
    """Versión compacta para indicadores st.metric."""
    try:
        valor = float(valor)
    except Exception:
        return "Sin dato"

    if abs(valor) < 1e-9:
        return "Sin cambio"

    palabra = "Aumentó" if valor > 0 else "Disminuyó"
    magnitud = abs(valor)

    if unidad:
        return f"{palabra} {magnitud:.{dec}f} {unidad}"
    return f"{palabra} {magnitud:.{dec}f}"


# ============================================================
# CARGA DE DATOS
# ============================================================

@st.cache_data
def cargar_archivo_interfaz(archivo):
    datos = {}
    xls = pd.ExcelFile(archivo)
    for hoja in xls.sheet_names:
        datos[hoja] = pd.read_excel(archivo, sheet_name=hoja)
    return datos


def preparar_datos(datos_actual, datos_mejora):
    actividades_actual = datos_actual["actividades"].copy()
    estaciones_actual = datos_actual["estaciones"].copy()

    actividades_mejora = datos_mejora["actividades"].copy()
    estaciones_mejora = datos_mejora["estaciones"].copy()

    actividades = pd.concat([actividades_actual, actividades_mejora], ignore_index=True)
    estaciones = pd.concat([estaciones_actual, estaciones_mejora], ignore_index=True)

    actividades["escenario"] = actividades["escenario"].astype(str).str.upper().str.strip()
    estaciones["escenario"] = estaciones["escenario"].astype(str).str.upper().str.strip()

    actividades["actividad_id"] = actividades["actividad_id"].astype(str).str.strip()
    actividades["estacion_id"] = actividades["estacion_id"].astype(str).str.strip()
    estaciones["estacion_id"] = estaciones["estacion_id"].astype(str).str.strip()

    if "descripcion" not in actividades.columns:
        actividades["descripcion"] = actividades["actividad_id"]

    actividades["tiempo_seg"] = pd.to_numeric(actividades["tiempo_seg"], errors="coerce")
    if "esfuerzo" not in actividades.columns:
        actividades["esfuerzo"] = 0
    actividades["esfuerzo"] = pd.to_numeric(actividades["esfuerzo"], errors="coerce").fillna(0).fillna(0)

    # Misma actividad = mismo tiempo y mismo esfuerzo.
    tiempos_actuales = (
        actividades[actividades["escenario"] == "ANTES"]
        .drop_duplicates("actividad_id")
        .set_index("actividad_id")["tiempo_seg"]
        .to_dict()
    )

    esfuerzos_actuales = (
        actividades[actividades["escenario"] == "ANTES"]
        .drop_duplicates("actividad_id")
        .set_index("actividad_id")["esfuerzo"]
        .to_dict()
    )

    actividades["tiempo_seg"] = actividades["actividad_id"].map(tiempos_actuales)
    actividades["esfuerzo"] = actividades["actividad_id"].map(esfuerzos_actuales)

    actividades["tiempo_seg"] = pd.to_numeric(actividades["tiempo_seg"], errors="coerce")
    actividades["esfuerzo"] = pd.to_numeric(actividades["esfuerzo"], errors="coerce").fillna(0)

    resumen_estaciones_calc = (
        actividades
        .groupby(["escenario", "estacion_id"], as_index=False)
        .agg(
            tiempo_total_seg=("tiempo_seg", "sum"),
            num_actividades=("actividad_id", "count"),
            esfuerzo_total=("esfuerzo", "sum"),
            tiempo_max_actividad=("tiempo_seg", "max")
        )
    )

    estaciones_base = estaciones.drop(
        columns=[
            "num_actividades",
            "carga_total_seg",
            "tiempo_total_seg",
            "esfuerzo_total",
            "actividades_sin_esfuerzo",
            "tiempo_max_actividad"
        ],
        errors="ignore"
    ).copy()

    estaciones_viz = estaciones_base.merge(
        resumen_estaciones_calc,
        on=["escenario", "estacion_id"],
        how="left"
    )

    estaciones_viz["tiempo_total_seg"] = estaciones_viz["tiempo_total_seg"].fillna(0)
    estaciones_viz["num_actividades"] = estaciones_viz["num_actividades"].fillna(0).astype(int)
    estaciones_viz["esfuerzo_total"] = estaciones_viz["esfuerzo_total"].fillna(0)
    estaciones_viz["tiempo_max_actividad"] = estaciones_viz["tiempo_max_actividad"].fillna(0)

    if "orden" not in estaciones_viz.columns:
        estaciones_viz["orden"] = estaciones_viz["estacion_id"].apply(extraer_numero_estacion)

    if "lado" not in estaciones_viz.columns:
        estaciones_viz["lado"] = estaciones_viz["estacion_id"].apply(
            lambda x: "LH" if str(x).upper().endswith("LH") else ("RH" if str(x).upper().endswith("RH") else "ESPECIAL")
        )

    estaciones_viz["orden"] = pd.to_numeric(estaciones_viz["orden"], errors="coerce")

    return actividades, estaciones, estaciones_viz


# ============================================================
# KPIS Y COMPARACIONES
# ============================================================

def calcular_kpis(estaciones_viz, actividades, escenario):
    carga = estaciones_viz[estaciones_viz["escenario"] == escenario].copy()
    acts = actividades[actividades["escenario"] == escenario].copy()

    tiempo_ciclo = carga["tiempo_total_seg"].max()
    contenido_trabajo = acts["tiempo_seg"].sum()
    num_estaciones = carga["estacion_id"].nunique()
    num_actividades = acts["actividad_id"].nunique()

    estacion_critica = "-"
    if not carga.empty and carga["tiempo_total_seg"].notna().any():
        idx = carga["tiempo_total_seg"].idxmax()
        estacion_critica = str(carga.loc[idx, "estacion_id"])

    return {
        "tiempo_ciclo": tiempo_ciclo,
        "contenido_trabajo": contenido_trabajo,
        "num_estaciones": num_estaciones,
        "num_actividades": num_actividades,
        "estacion_critica": estacion_critica
    }


def comparar_actividades(actividades):
    antes = actividades[actividades["escenario"] == "ANTES"].copy()
    despues = actividades[actividades["escenario"] == "DESPUES"].copy()

    antes = antes[[
        "actividad_id",
        "descripcion",
        "estacion_id",
        "tiempo_seg"
    ]].rename(columns={
        "estacion_id": "estacion_antes",
        "tiempo_seg": "tiempo"
    })

    despues = despues[[
        "actividad_id",
        "descripcion",
        "estacion_id"
    ]].rename(columns={
        "descripcion": "descripcion_despues",
        "estacion_id": "estacion_despues"
    })

    comp = antes.merge(despues, on="actividad_id", how="outer")
    comp["descripcion"] = comp["descripcion"].fillna(comp["descripcion_despues"])

    def clasificar(row):
        if pd.isna(row["estacion_antes"]):
            return "Nueva"
        elif pd.isna(row["estacion_despues"]):
            return "Eliminada"
        elif row["estacion_antes"] != row["estacion_despues"]:
            return "Movida"
        else:
            return "Sin cambio"

    comp["estado_cambio"] = comp.apply(clasificar, axis=1)

    return comp[[
        "actividad_id",
        "descripcion",
        "estacion_antes",
        "estacion_despues",
        "tiempo",
        "estado_cambio"
    ]]


def crear_comparacion_estaciones(estaciones_viz):
    resumen = estaciones_viz[[
        "escenario",
        "estacion_id",
        "orden",
        "lado",
        "tiempo_total_seg",
        "num_actividades",
        "esfuerzo_total"
    ]].copy()

    antes = resumen[resumen["escenario"] == "ANTES"].rename(columns={
        "tiempo_total_seg": "tiempo_antes",
        "num_actividades": "actividades_antes",
        "esfuerzo_total": "esfuerzo_antes"
    })

    despues = resumen[resumen["escenario"] == "DESPUES"].rename(columns={
        "tiempo_total_seg": "tiempo_despues",
        "num_actividades": "actividades_despues",
        "esfuerzo_total": "esfuerzo_despues"
    })

    comp = antes.merge(
        despues[[
            "estacion_id",
            "tiempo_despues",
            "actividades_despues",
            "esfuerzo_despues"
        ]],
        on="estacion_id",
        how="outer"
    )

    comp["tiempo_antes"] = comp["tiempo_antes"].fillna(0)
    comp["tiempo_despues"] = comp["tiempo_despues"].fillna(0)
    comp["actividades_antes"] = comp["actividades_antes"].fillna(0)
    comp["actividades_despues"] = comp["actividades_despues"].fillna(0)
    comp["esfuerzo_antes"] = comp["esfuerzo_antes"].fillna(0)
    comp["esfuerzo_despues"] = comp["esfuerzo_despues"].fillna(0)

    comp["delta_tiempo"] = comp["tiempo_despues"] - comp["tiempo_antes"]
    comp["delta_actividades"] = comp["actividades_despues"] - comp["actividades_antes"]
    comp["delta_esfuerzo"] = comp["esfuerzo_despues"] - comp["esfuerzo_antes"]
    comp["orden_custom"] = comp["estacion_id"].apply(custom_station_order)

    return comp.sort_values("orden_custom")


# ============================================================
# VISUAL DE LÍNEA SIN IMAGEN
# ============================================================

def posiciones_esquema(estacion_id):
    est = str(estacion_id).upper().strip()

    if est in ["SEC", "SUB", "SUBENSAMBLE"]:
        return 13, 14
    if est == "1RH":
        return 13, 28
    if est == "1LH":
        return 28, 62

    n = extraer_numero_estacion(est)

    if est.endswith("LH"):
        return 28 + (n - 1) * 6.2, 62
    if est.endswith("RH"):
        return 28 + (n - 1) * 6.2, 28

    return 18, 45


def graficar_linea_esquematica(estaciones_viz, escenario, estacion_sel=None):
    df = estaciones_viz[estaciones_viz["escenario"] == escenario].copy()
    df["estacion_id"] = df["estacion_id"].astype(str).str.upper().str.strip()

    fig = go.Figure()

    # Banda principal más "real"
    banda_x0, banda_x1 = 24, 150
    banda_y0, banda_y1 = 42, 49
    banda_yc = (banda_y0 + banda_y1) / 2

    fig.add_shape(
        type="rect",
        x0=banda_x0, y0=banda_y0,
        x1=banda_x1, y1=banda_y1,
        line=dict(color="#3A3A3A", width=1.4),
        fillcolor="#D9DEE5",
        layer="below"
    )
    fig.add_shape(
        type="rect",
        x0=banda_x0, y0=banda_y0 + 1.1,
        x1=banda_x1, y1=banda_y1 - 1.1,
        line=dict(color="rgba(0,0,0,0)", width=0),
        fillcolor="#EEF1F5",
        layer="below"
    )

    # Rodillos
    for x in np.linspace(banda_x0 + 4, banda_x1 - 4, 28):
        fig.add_shape(
            type="line",
            x0=x, y0=banda_y0,
            x1=x, y1=banda_y1,
            line=dict(color="#B5BCC7", width=0.8),
            layer="below"
        )

    # Línea de flujo y flecha
    fig.add_shape(
        type="line",
        x0=banda_x0, y0=banda_yc,
        x1=banda_x1, y1=banda_yc,
        line=dict(color=PALETA["verde"], width=2.8),
        layer="below"
    )

    fig.add_annotation(
        x=banda_x0, y=banda_yc,
        ax=banda_x0 - 12, ay=banda_yc,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=2.1,
        arrowwidth=3,
        arrowcolor=PALETA["verde"]
    )

    # Flujo SEC -> 1RH -> banda
    fig.add_annotation(
        x=12, y=24,
        ax=12, ay=18,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.3,
        arrowwidth=2,
        arrowcolor=PALETA["gris"]
    )
    fig.add_shape(
        type="line",
        x0=19, y0=28,
        x1=banda_x0 - 3, y1=28,
        line=dict(color=PALETA["gris"], width=2),
    )
    fig.add_shape(
        type="line",
        x0=banda_x0 - 3, y0=28,
        x1=banda_x0 - 3, y1=banda_yc,
        line=dict(color=PALETA["gris"], width=2),
    )
    fig.add_annotation(
        x=banda_x0, y=banda_yc,
        ax=banda_x0 - 3, ay=banda_yc,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.3,
        arrowwidth=2,
        arrowcolor=PALETA["gris"]
    )

    # Conexiones LH/RH a banda
    for _, row in df.iterrows():
        est = row["estacion_id"]
        if est in ["SEC", "SUB", "SUBENSAMBLE", "1RH"]:
            continue

        x, y = posiciones_esquema(est)
        if est.endswith("LH"):
            fig.add_shape(type="line", x0=x, y0=59, x1=x, y1=banda_y1, line=dict(color="#AFAFAF", width=1))
        elif est.endswith("RH"):
            fig.add_shape(type="line", x0=x, y0=31, x1=x, y1=banda_y0, line=dict(color="#AFAFAF", width=1))

    # Estaciones en scatter clickeable
    xs, ys, labels, sizes, colors, line_colors, text_colors, customdata, hovers = [], [], [], [], [], [], [], [], []

    for _, row in df.sort_values("estacion_id").iterrows():
        est = str(row["estacion_id"]).upper().strip()
        x, y = posiciones_esquema(est)

        xs.append(x)
        ys.append(y)
        customdata.append(est)

        selected = est == str(estacion_sel).upper().strip()

        if est in ["SEC", "SUB", "SUBENSAMBLE"]:
            labels.append("SEC<br>SUBENSAMBLE")
            sizes.append(95)
            colors.append(PALETA["amarillo_suave"] if selected else PALETA["blanco"])
            line_colors.append(PALETA["rojo_auteco"] if selected else PALETA["negro"])
            text_colors.append(PALETA["negro"])
        elif est == "1RH":
            labels.append("1RH<br>MARCACIÓN")
            sizes.append(95)
            colors.append(PALETA["amarillo_suave"] if selected else PALETA["blanco"])
            line_colors.append(PALETA["rojo_auteco"] if selected else PALETA["negro"])
            text_colors.append(PALETA["negro"])
        else:
            labels.append(est)
            sizes.append(38 if selected else 34)
            colors.append(PALETA["amarillo_suave"] if selected else PALETA["azul_medio"])
            line_colors.append(PALETA["rojo_auteco"] if selected else PALETA["azul_auteco"])
            text_colors.append(PALETA["negro"] if selected else PALETA["blanco"])

        hovers.append(
            f"<b>{est}</b><br>"
            f"Tiempo total: {row['tiempo_total_seg']:.2f} s<br>"
            f"Esfuerzo total: {row['esfuerzo_total']:.1f}<br>"
            f"Actividades: {int(row['num_actividades'])}<extra></extra>"
        )

    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            marker=dict(
                symbol="square",
                size=sizes,
                color=colors,
                line=dict(color=line_colors, width=2),
                opacity=0.97
            ),
            text=labels,
            textposition="middle center",
            textfont=dict(size=9, color=text_colors),
            customdata=customdata,
            hovertemplate=hovers,
            showlegend=False,
            name="estaciones"
        )
    )

    fig.update_layout(
        height=610,
        margin=dict(l=5, r=5, t=10, b=5),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(range=[0, 156], visible=False, fixedrange=True),
        yaxis=dict(range=[0, 74], visible=False, fixedrange=True),
        hovermode="closest",
        dragmode=False,
        showlegend=False
    )

    return fig


# ============================================================
# GRÁFICAS
# ============================================================

def grafico_balance_comparativo(estaciones_viz):
    carga = estaciones_viz.copy()
    orden = ordenar_estaciones(carga["estacion_id"].dropna().astype(str).unique())

    fig = go.Figure()

    for escenario, color, nombre in [
        ("ANTES", PALETA["gris"], "Actual"),
        ("DESPUES", PALETA["azul_medio"], "Mejora")
    ]:
        df = carga[carga["escenario"] == escenario].copy()
        df["estacion_id"] = pd.Categorical(df["estacion_id"], categories=orden, ordered=True)
        df = df.sort_values("estacion_id")

        fig.add_trace(
            go.Bar(
                x=df["estacion_id"].astype(str),
                y=df["tiempo_total_seg"],
                name=nombre,
                marker=dict(color=color),
                hovertemplate="<b>%{x}</b><br>Tiempo total: %{y:.2f} s<extra></extra>"
            )
        )

    fig.update_layout(
        title="Carga total por estación",
        xaxis_title="Estación",
        yaxis_title="Tiempo total por estación (s)",
        barmode="group",
        height=470,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=65, b=100),
        legend=dict(orientation="h", y=1.10)
    )
    fig.update_xaxes(tickangle=-90)
    return fig


def grafico_top_cambios(comparacion_estaciones, top_n=12):
    df = comparacion_estaciones.copy()
    df["abs_delta"] = df["delta_tiempo"].abs()
    df = df.sort_values("abs_delta", ascending=False).head(top_n).copy()
    df = df.sort_values("delta_tiempo")

    colores = [PALETA["rojo_auteco"] if x < 0 else PALETA["azul_medio"] for x in df["delta_tiempo"]]

    fig = go.Figure(
        go.Bar(
            x=df["delta_tiempo"],
            y=df["estacion_id"],
            orientation="h",
            marker=dict(color=colores),
            text=df["delta_tiempo"].round(1),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Cambio: %{x:.2f} s<extra></extra>"
        )
    )

    fig.add_shape(
        type="line",
        x0=0, x1=0,
        y0=-0.5, y1=len(df) - 0.5,
        line=dict(color=PALETA["negro"], width=1.1)
    )

    fig.update_layout(
        title="Estaciones con mayor cambio de carga",
        xaxis_title="Cambio de tiempo (s)",
        yaxis_title="Estación",
        height=430,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=65, b=40),
        showlegend=False
    )

    return fig


def grafico_movimientos_por_estacion(comparacion_actividades):
    mov = comparacion_actividades[comparacion_actividades["estado_cambio"] == "Movida"].copy()

    salen = (
        mov.groupby("estacion_antes")
        .size()
        .reset_index(name="Salen")
        .rename(columns={"estacion_antes": "estacion_id"})
    )

    entran = (
        mov.groupby("estacion_despues")
        .size()
        .reset_index(name="Entran")
        .rename(columns={"estacion_despues": "estacion_id"})
    )

    df = salen.merge(entran, on="estacion_id", how="outer").fillna(0)
    df["orden_custom"] = df["estacion_id"].apply(custom_station_order)
    df = df.sort_values("orden_custom")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["estacion_id"],
            y=df["Entran"],
            name="Entran",
            marker=dict(color=PALETA["azul_medio"]),
            hovertemplate="<b>%{x}</b><br>Entran: %{y}<extra></extra>"
        )
    )
    fig.add_trace(
        go.Bar(
            x=df["estacion_id"],
            y=-df["Salen"],
            name="Salen",
            marker=dict(color=PALETA["rojo_auteco"]),
            hovertemplate="<b>%{x}</b><br>Salen: %{customdata}<extra></extra>",
            customdata=df["Salen"]
        )
    )

    fig.add_shape(
        type="line",
        x0=-0.5, x1=len(df["estacion_id"]) - 0.5,
        y0=0, y1=0,
        line=dict(color=PALETA["negro"], width=1.1)
    )

    fig.update_layout(
        title="Entrada y salida de actividades por estación",
        xaxis_title="Estación",
        yaxis_title="Cantidad de actividades",
        barmode="relative",
        height=440,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=65, b=100),
        legend=dict(orientation="h", y=1.10)
    )
    fig.update_xaxes(tickangle=-90)
    return fig


def grafico_resumen_cambios(comparacion_actividades):
    df = comparacion_actividades["estado_cambio"].value_counts().reset_index()
    df.columns = ["tipo", "cantidad"]
    orden = ["Movida", "Sin cambio", "Nueva", "Eliminada"]
    df["tipo"] = pd.Categorical(df["tipo"], categories=orden, ordered=True)
    df = df.sort_values("tipo")

    color_map = {
        "Movida": PALETA["azul_medio"],
        "Sin cambio": PALETA["gris"],
        "Nueva": "#2E7D32",
        "Eliminada": PALETA["rojo_auteco"]
    }

    fig = go.Figure(
        go.Bar(
            x=df["cantidad"],
            y=df["tipo"].astype(str),
            orientation="h",
            marker=dict(color=[color_map.get(x, PALETA["gris"]) for x in df["tipo"].astype(str)]),
            text=df["cantidad"],
            textposition="outside"
        )
    )

    fig.update_layout(
        title="Resumen de cambios de actividades",
        xaxis_title="Cantidad",
        yaxis_title="Tipo de cambio",
        height=330,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=65, b=40),
        showlegend=False
    )

    return fig


def grafico_flujo_desde_estacion(actividades, estacion_sel):
    antes = actividades[actividades["escenario"] == "ANTES"].copy()
    despues = actividades[actividades["escenario"] == "DESPUES"].copy()

    base = antes[antes["estacion_id"].astype(str) == estacion_sel][["actividad_id"]].copy()
    if base.empty:
        return None, pd.DataFrame()

    destinos = base.merge(despues[["actividad_id", "estacion_id"]], on="actividad_id", how="left")
    destinos = destinos.rename(columns={"estacion_id": "destino"})
    destinos["destino"] = destinos["destino"].fillna("Eliminada")
    total = len(destinos)

    resumen = destinos.groupby("destino").size().reset_index(name="cantidad")
    resumen["porcentaje"] = resumen["cantidad"] / total * 100
    resumen["orden_custom"] = resumen["destino"].apply(
        lambda x: (99, 0, str(x)) if str(x) == "Eliminada" else custom_station_order(x)
    )
    resumen = resumen.sort_values("orden_custom")

    colores = [
        PALETA["rojo_auteco"] if x == "Eliminada"
        else (PALETA["gris"] if x == estacion_sel else PALETA["azul_medio"])
        for x in resumen["destino"]
    ]

    resumen["texto"] = resumen.apply(
        lambda r: f"{r['porcentaje']:.1f}% | {int(r['cantidad'])} act.",
        axis=1
    )

    max_x = max(100, resumen["porcentaje"].max() * 1.25)

    fig = go.Figure(
        go.Bar(
            x=resumen["porcentaje"],
            y=resumen["destino"],
            orientation="h",
            marker=dict(color=colores),
            text=resumen["texto"],
            textposition="outside",
            cliponaxis=False,
            customdata=resumen["cantidad"],
            hovertemplate="<b>%{y}</b><br>Porcentaje: %{x:.1f}%<br>Actividades: %{customdata}<extra></extra>"
        )
    )

    fig.update_layout(
        title=f"Destino de las actividades que estaban en {estacion_sel}",
        xaxis_title="Porcentaje del total original de la estación",
        yaxis_title="Destino en la mejora",
        height=max(420, 115 + 52 * len(resumen)),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=70, r=135, t=70, b=55),
        showlegend=False
    )

    fig.update_xaxes(range=[0, max_x], ticksuffix="%")
    fig.update_yaxes(automargin=True)

    return fig, resumen

def grafico_sankey_estacion(actividades, estacion_sel):
    """Sankey profesional con etiquetas externas legibles y hover detallado de actividades."""
    antes = actividades[actividades["escenario"] == "ANTES"].copy()
    despues = actividades[actividades["escenario"] == "DESPUES"].copy()

    base = antes[
        antes["estacion_id"].astype(str) == str(estacion_sel)
    ][["actividad_id", "descripcion", "tiempo_seg", "esfuerzo"]].copy()

    if base.empty:
        return None

    destinos = base.merge(
        despues[["actividad_id", "estacion_id"]],
        on="actividad_id",
        how="left"
    ).rename(columns={"estacion_id": "destino"})

    destinos["destino"] = destinos["destino"].fillna("Eliminada")

    resumen = (
        destinos
        .groupby("destino")
        .agg(
            cantidad=("actividad_id", "count"),
            actividades=("actividad_id", lambda x: ", ".join(x.astype(str))),
            descripciones=("descripcion", lambda x: "<br>".join(
                [f"• {truncar_texto(v, 95)}" for v in x.astype(str).tolist()[:8]]
            )),
            tiempo_total=("tiempo_seg", "sum")
        )
        .reset_index()
    )

    total = resumen["cantidad"].sum()
    resumen["porcentaje"] = resumen["cantidad"] / total * 100
    resumen["orden_custom"] = resumen["destino"].apply(
        lambda x: (99, 0, str(x)) if str(x) == "Eliminada" else custom_station_order(x)
    )
    resumen = resumen.sort_values("orden_custom").reset_index(drop=True)

    n_destinos = len(resumen)

    # Posiciones fijas para que las etiquetas externas queden alineadas y legibles.
    if n_destinos == 1:
        y_targets = [0.50]
    else:
        y_targets = np.linspace(0.08, 0.88, n_destinos).tolist()

    node_x = [0.03] + [0.88] * n_destinos
    node_y = [0.45] + y_targets

    # Dejamos los labels internos vacíos y usamos anotaciones externas.
    # Esto evita el texto gris montado sobre los flujos.
    nodos_visuales = [" "] * (n_destinos + 1)

    hover_links = []
    for _, r in resumen.iterrows():
        hover_links.append(
            f"<b>Origen:</b> {estacion_sel}<br>"
            f"<b>Destino:</b> {r['destino']}<br>"
            f"<b>Cantidad:</b> {int(r['cantidad'])} actividades<br>"
            f"<b>Porcentaje:</b> {r['porcentaje']:.1f}%<br>"
            f"<b>Tiempo total:</b> {r['tiempo_total']:.2f} s<br>"
            f"<b>Códigos:</b> {r['actividades']}<br>"
            f"<b>Descripciones:</b><br>{r['descripciones']}"
        )

    node_colors = [PALETA["azul_auteco"]] + [
        PALETA["rojo_auteco"] if d == "Eliminada"
        else (PALETA["gris"] if str(d) == str(estacion_sel) else PALETA["azul_medio"])
        for d in resumen["destino"]
    ]

    link_colors = [
        "rgba(227,6,19,0.28)" if d == "Eliminada"
        else ("rgba(138,140,142,0.28)" if str(d) == str(estacion_sel) else "rgba(14,103,169,0.30)")
        for d in resumen["destino"]
    ]

    fig = go.Figure(
        go.Sankey(
            arrangement="fixed",
            node=dict(
                pad=34,
                thickness=24,
                line=dict(color="rgba(0,0,0,0.30)", width=0.8),
                label=nodos_visuales,
                x=node_x,
                y=node_y,
                color=node_colors,
                hovertemplate="<extra></extra>"
            ),
            link=dict(
                source=[0] * n_destinos,
                target=list(range(1, n_destinos + 1)),
                value=resumen["cantidad"],
                color=link_colors,
                customdata=hover_links,
                hovertemplate="%{customdata}<extra></extra>"
            )
        )
    )

    # Etiqueta de origen con fondo blanco.
    fig.add_annotation(
        x=0.01,
        y=0.50,
        xref="paper",
        yref="paper",
        text=f"<b>Origen</b><br>{estacion_sel}",
        showarrow=False,
        align="left",
        font=dict(size=15, color=PALETA["azul_auteco"]),
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor=PALETA["azul_auteco"],
        borderwidth=1,
        borderpad=5
    )

    # Etiquetas de destino, porcentaje y cantidad.
    for i, r in resumen.iterrows():
        destino = str(r["destino"])
        color_borde = PALETA["rojo_auteco"] if destino == "Eliminada" else PALETA["azul_medio"]

        fig.add_annotation(
            x=0.965,
            y=y_targets[i] + 0.03,
            xref="paper",
            yref="paper",
            # Solo se muestra la estación para no romper la alineación.
            # El porcentaje, cantidad, códigos y descripciones quedan en el hover.
            text=f"<b>{destino}</b>",
            showarrow=False,
            align="center",
            font=dict(size=15, color="#1D2A44"),
            bgcolor="rgba(255,255,255,0.96)",
            bordercolor=color_borde,
            borderwidth=1,
            borderpad=6
        )

    fig.update_layout(
        title=f"Movimiento específico desde {estacion_sel}",
        height=max(560, 140 + 70 * n_destinos),
        margin=dict(l=35, r=85, t=80, b=45),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(size=14, color="#1D2A44"),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#003A70",
            font=dict(size=13, color="#1D2A44")
        )
    )

    return fig

def grafico_composicion_estacion(actividades, estacion_sel):
    antes_est = actividades[(actividades["escenario"] == "ANTES") & (actividades["estacion_id"].astype(str) == estacion_sel)].copy()
    despues_est = actividades[(actividades["escenario"] == "DESPUES") & (actividades["estacion_id"].astype(str) == estacion_sel)].copy()

    antes_ids = set(antes_est["actividad_id"])
    despues_ids = set(despues_est["actividad_id"])

    labels = ["Permanece", "Sale", "Entra"]
    values = [len(antes_ids & despues_ids), len(antes_ids - despues_ids), len(despues_ids - antes_ids)]
    colors = [PALETA["gris"], PALETA["rojo_auteco"], "#2E7D32"]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.58,
            marker=dict(colors=colors),
            textinfo="label+percent"
        )
    )

    fig.update_layout(
        title=f"Composición de cambios en {estacion_sel}",
        height=360,
        margin=dict(l=20, r=20, t=65, b=20),
        paper_bgcolor="white"
    )

    return fig


# ============================================================
# TARJETAS
# ============================================================

def mostrar_resumen_cambios_metricas(comparacion_actividades):
    resumen = comparacion_actividades["estado_cambio"].value_counts().to_dict()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Movidas", resumen.get("Movida", 0))
    with c2:
        st.metric("Sin cambio", resumen.get("Sin cambio", 0))
    with c3:
        st.metric("Nuevas", resumen.get("Nueva", 0))
    with c4:
        st.metric("Eliminadas", resumen.get("Eliminada", 0))


def etiqueta_estado(estado):
    if estado in ["Sale", "Eliminada"]:
        return "🔴 " + str(estado)
    if estado in ["Entra", "Nueva"]:
        return "🟢 " + str(estado)
    if estado == "Movida":
        return "🔵 Movida"
    return "⚪ " + str(estado)


def card_actividad(row, estado=None, estacion_antes=None, estacion_despues=None):
    """Tarjeta 100% Streamlit. No usa etiquetas HTML internas para evitar que aparezcan <span>."""
    estado = estado or row.get("estado_cambio", "Sin cambio")

    actividad = str(row.get("actividad_id", ""))
    descripcion = truncar_texto(row.get("descripcion", ""), 260)

    estacion_antes = estacion_antes if estacion_antes is not None else row.get("estacion_antes", "")
    estacion_despues = estacion_despues if estacion_despues is not None else row.get("estacion_despues", "")

    tiempo = row.get("tiempo", row.get("tiempo_seg", 0))
    try:
        tiempo = float(tiempo)
    except Exception:
        tiempo = 0.0

    with st.container(border=True):
        st.markdown(f"**{actividad}**")
        st.write(descripcion)

        linea = f"{etiqueta_estado(estado)} · Tiempo: {tiempo:.2f} s"

        if str(estacion_antes).strip() or str(estacion_despues).strip():
            linea += f" · Antes: {estacion_antes} · Después: {estacion_despues}"

        st.caption(linea)


def obtener_actividades_por_destino(actividades, estacion_origen, destino):
    """Actividades que en ANTES estaban en estacion_origen y en DESPUÉS terminan en destino."""
    antes = actividades[actividades["escenario"] == "ANTES"].copy()
    despues = actividades[actividades["escenario"] == "DESPUES"].copy()

    base = antes[
        antes["estacion_id"].astype(str) == str(estacion_origen)
    ][["actividad_id", "descripcion", "tiempo_seg", "esfuerzo", "estacion_id"]].copy()

    base = base.rename(columns={"estacion_id": "estacion_antes"})

    mov = base.merge(
        despues[["actividad_id", "estacion_id"]],
        on="actividad_id",
        how="left"
    ).rename(columns={"estacion_id": "estacion_despues"})

    mov["estacion_despues"] = mov["estacion_despues"].fillna("Eliminada")

    return mov[mov["estacion_despues"].astype(str) == str(destino)].copy()


def mostrar_actividades_destino(actividades, estacion_sel, destinos_disponibles):
    if len(destinos_disponibles) == 0:
        return

    destino_sel = st.selectbox(
        "Selecciona un destino para ver las actividades movidas",
        destinos_disponibles,
        key=f"destino_{estacion_sel}"
    )

    df_destino = obtener_actividades_por_destino(
        actividades,
        estacion_sel,
        destino_sel
    )

    st.caption(
        f"Actividades que estaban en {estacion_sel} y en la mejora quedaron en {destino_sel}: {len(df_destino)}"
    )

    if df_destino.empty:
        st.info("No hay actividades para este destino.")
        return

    for _, row in df_destino.sort_values("actividad_id").iterrows():
        estado = "Permanece" if str(destino_sel) == str(estacion_sel) else "Movida"
        card_actividad(
            row,
            estado=estado,
            estacion_antes=row.get("estacion_antes", estacion_sel),
            estacion_despues=row.get("estacion_despues", destino_sel)
        )


def mostrar_cards_limitadas(df, limite=24):
    if df.empty:
        st.info("No hay actividades para mostrar con los filtros seleccionados.")
        return
    for _, row in df.head(limite).iterrows():
        card_actividad(row)
    if len(df) > limite:
        st.caption(f"Mostrando {limite} de {len(df)} actividades. Usa filtros para acotar la búsqueda.")


def obtener_resumen_estacion(actividades, estacion_sel):
    antes_est = actividades[(actividades["escenario"] == "ANTES") & (actividades["estacion_id"].astype(str) == estacion_sel)].copy()
    despues_est = actividades[(actividades["escenario"] == "DESPUES") & (actividades["estacion_id"].astype(str) == estacion_sel)].copy()

    antes_ids = set(antes_est["actividad_id"])
    despues_ids = set(despues_est["actividad_id"])

    return {
        "antes_est": antes_est,
        "despues_est": despues_est,
        "permanecen": antes_ids & despues_ids,
        "salen": antes_ids - despues_ids,
        "entran": despues_ids - antes_ids,
        "tiempo_antes": antes_est["tiempo_seg"].sum(),
        "tiempo_despues": despues_est["tiempo_seg"].sum()
    }

def mostrar_detalle_estacion(actividades, comparacion_actividades, estacion_sel):
    info = obtener_resumen_estacion(actividades, estacion_sel)

    delta_tiempo = info["tiempo_despues"] - info["tiempo_antes"]

    render_html(
        f"""
        <div class="instruction-box">
        <b>Lectura de la estación {html.escape(str(estacion_sel))}:</b>
        compara tiempo, actividades que permanecen, actividades que salen y actividades que entran.
        </div>
        """
    )

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Cambio en tiempo", texto_cambio_metric(delta_tiempo, "s", dec=2))
    with m2:
        st.metric("Actividades entran", len(info["entran"]))
    with m3:
        st.metric("Actividades salen", len(info["salen"]))

    c_left, c_right = st.columns([1.05, 1.45])

    with c_left:
        render_html(
            f"""
            <div class="section-card">
                <div class="small-title">Comparación general</div>
                <span class="tag tag-blue">Tiempo actual: {info['tiempo_antes']:.2f} s</span>
                <span class="tag tag-blue">Tiempo mejora: {info['tiempo_despues']:.2f} s</span>
                <span class="tag tag-yellow">Tiempo: {html.escape(texto_cambio(delta_tiempo, "s", dec=2))}</span><br>
                <span class="tag tag-gray">Permanecen: {len(info['permanecen'])}</span>
                <span class="tag tag-green">Entran: {len(info['entran'])}</span>
                <span class="tag tag-red">Salen: {len(info['salen'])}</span>
            </div>
            """
        )

        st.plotly_chart(
            grafico_composicion_estacion(actividades, estacion_sel),
            use_container_width=True,
            config={"displayModeBar": False}
        )

        fig_dest, tabla_dest = grafico_flujo_desde_estacion(actividades, estacion_sel)
        if fig_dest is not None:
            st.plotly_chart(
                fig_dest,
                use_container_width=True,
                config={"displayModeBar": False}
            )

    with c_right:
        tab_perm, tab_entran, tab_salen, tab_actual, tab_mejora, tab_especificos = st.tabs([
            "Permanecen",
            "Entran",
            "Salen",
            "Actual",
            "Mejora",
            "Cambios específicos"
        ])

        with tab_perm:
            df = info["despues_est"][info["despues_est"]["actividad_id"].isin(info["permanecen"])].copy()
            if df.empty:
                st.info("No hay actividades que permanezcan en esta estación.")
            else:
                for _, row in df.sort_values("actividad_id").iterrows():
                    card_actividad(row, estado="Permanece")

        with tab_entran:
            df = info["despues_est"][info["despues_est"]["actividad_id"].isin(info["entran"])].copy()
            if df.empty:
                st.success("No entran actividades nuevas a esta estación.")
            else:
                for _, row in df.sort_values("actividad_id").iterrows():
                    card_actividad(row, estado="Entra")

        with tab_salen:
            df = info["antes_est"][info["antes_est"]["actividad_id"].isin(info["salen"])].copy()
            if df.empty:
                st.success("No salen actividades de esta estación.")
            else:
                for _, row in df.sort_values("actividad_id").iterrows():
                    card_actividad(row, estado="Sale")

        with tab_actual:
            for _, row in info["antes_est"].sort_values("actividad_id").iterrows():
                estado = "Permanece" if row["actividad_id"] in info["permanecen"] else "Sale"
                card_actividad(row, estado=estado)

        with tab_mejora:
            for _, row in info["despues_est"].sort_values("actividad_id").iterrows():
                estado = "Permanece" if row["actividad_id"] in info["permanecen"] else "Entra"
                card_actividad(row, estado=estado)

        with tab_especificos:
            dfc = comparacion_actividades[
                (comparacion_actividades["estacion_antes"].astype(str) == estacion_sel) |
                (comparacion_actividades["estacion_despues"].astype(str) == estacion_sel)
            ].copy()

            if dfc.empty:
                st.info("No se encontraron cambios específicos para esta estación.")
            else:
                for _, row in dfc.sort_values(["estado_cambio", "actividad_id"]).iterrows():
                    card_actividad(
                        row,
                        estado=row["estado_cambio"],
                        estacion_antes=row["estacion_antes"],
                        estacion_despues=row["estacion_despues"]
                    )

    # Vista grande del gráfico de movimientos.
    st.markdown("### Movimiento específico en vista grande")
    st.caption("Este gráfico ocupa todo el ancho para que los destinos y flujos se lean con claridad.")

    fig_sankey = grafico_sankey_estacion(actividades, estacion_sel)
    if fig_sankey is not None:
        st.plotly_chart(
            fig_sankey,
            use_container_width=True,
            config={
                "displayModeBar": True,
                "toImageButtonOptions": {
                    "format": "png",
                    "filename": f"movimiento_{estacion_sel}",
                    "height": 900,
                    "width": 1600,
                    "scale": 2
                }
            }
        )

# ============================================================
# ENCABEZADO
# ============================================================

logo_path = cargar_logo()
logo_html = ""

if logo_path:
    logo_html = f'<img class="header-logo" src="{image_to_data_uri(logo_path)}" alt="Auteco">'

render_html(
    f"""
    <div class="header-card">
        {logo_html}
        <div>
            <div class="hero-title">Visualizador de cambios</div>
            <div class="hero-subtitle">
                Representación visual ANTES vs DESPUÉS de la redistribución de actividades en la línea de ensamble.
            </div>
        </div>
    </div>
    """
)

render_html(
    """
    <div class="instruction-box">
    <b>Guía rápida:</b> 1) carga ambos archivos, 2) elige el escenario visible, 3) toca o selecciona una estación,
    4) revisa abajo la comparación completa: tiempo, esfuerzo, actividades y redistribución porcentual.
    </div>
    """
)

# ============================================================
# CONTROL PRINCIPAL DE ESCENARIO
# ============================================================

if "escenario" not in st.session_state:
    st.session_state["escenario"] = "ANTES"

render_html("<div class='small-title'>Escenario visible</div>")

esc_btn_1, esc_btn_2, esc_help = st.columns([1, 1, 4])

with esc_btn_1:
    if st.button(
        "ANTES",
        use_container_width=True,
        type="primary" if st.session_state["escenario"] == "ANTES" else "secondary"
    ):
        st.session_state["escenario"] = "ANTES"

with esc_btn_2:
    if st.button(
        "DESPUÉS",
        use_container_width=True,
        type="primary" if st.session_state["escenario"] == "DESPUES" else "secondary"
    ):
        st.session_state["escenario"] = "DESPUES"

with esc_help:
    render_html(
        """
        <div class="mini-card">
        Selecciona el escenario que quieres ver en la línea. Luego haz clic sobre una estación o usa el selector manual.
        </div>
        """
    )



# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("Carga de archivos")

    archivo_actual = st.file_uploader(
        "Excel escenario actual / ANTES",
        type=["xlsx"]
    )

    archivo_mejora = st.file_uploader(
        "Excel escenario mejora / DESPUÉS",
        type=["xlsx"]
    )

    st.markdown("---")
    st.caption("Carga los archivos y usa los botones superiores para cambiar el escenario visible.")


if archivo_actual is None or archivo_mejora is None:
    st.info("Carga los dos archivos Excel para iniciar.")
    st.stop()


# ============================================================
# PROCESAMIENTO
# ============================================================

datos_actual = cargar_archivo_interfaz(archivo_actual)
datos_mejora = cargar_archivo_interfaz(archivo_mejora)

actividades, estaciones, estaciones_viz = preparar_datos(datos_actual, datos_mejora)
comparacion_actividades = comparar_actividades(actividades)
comparacion_estaciones = crear_comparacion_estaciones(estaciones_viz)
escenario = st.session_state["escenario"]
kpis = calcular_kpis(estaciones_viz, actividades, escenario)

# Selector libre: conserva el orden en que las estaciones aparecen en el Excel.
# No fuerza una secuencia específica de lectura.
estaciones_disponibles = (
    actividades["estacion_id"]
    .dropna()
    .astype(str)
    .drop_duplicates()
    .tolist()
)

if "estacion_sel" not in st.session_state or st.session_state["estacion_sel"] not in estaciones_disponibles:
    st.session_state["estacion_sel"] = estaciones_disponibles[0]


# ============================================================
# KPIS PRINCIPALES
# ============================================================

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    mostrar_kpi_card("Tiempo ciclo", f"{kpis['tiempo_ciclo']:.1f} s")
with k2:
    mostrar_kpi_card("Contenido trabajo", f"{kpis['contenido_trabajo']:.1f} s")
with k3:
    mostrar_kpi_card("Estaciones", f"{kpis['num_estaciones']}")
with k4:
    mostrar_kpi_card("Actividades", f"{kpis['num_actividades']}")
with k5:
    mostrar_kpi_card("Estación crítica", f"{kpis['estacion_critica']}")


# ============================================================
# REPRESENTACIÓN DE LA LÍNEA
# ============================================================

st.markdown("### Representación esquemática de la línea")
st.caption("Vista sin imagen de fondo. Pasa el cursor sobre una estación para ver su información; usa el selector para analizarla.")

sel_col1, sel_col2 = st.columns([1.2, 2.2])
with sel_col1:
    estacion_select = st.selectbox(
        "Selecciona cualquier estación",
        options=estaciones_disponibles,
        index=estaciones_disponibles.index(st.session_state["estacion_sel"])
    )
    st.session_state["estacion_sel"] = estacion_select

with sel_col2:
    st.empty()

fig_linea = graficar_linea_esquematica(estaciones_viz, escenario, estacion_sel=st.session_state["estacion_sel"])

st.plotly_chart(
    fig_linea,
    use_container_width=True,
    config={
        "displayModeBar": False,
        "scrollZoom": False,
        "doubleClick": False,
        "staticPlot": False
    }
)


st.markdown("---")


# ============================================================
# DETALLE DE ESTACIÓN
# ============================================================

st.markdown("### Comparación detallada por estación")
mostrar_detalle_estacion(actividades, comparacion_actividades, st.session_state["estacion_sel"])

st.markdown("---")


# ============================================================
# ANÁLISIS VISUAL
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "Resumen visual",
    "Carga por estación",
    "Movimientos de actividades",
    "Datos de apoyo"
])

with tab1:
    st.subheader("Resumen visual de la redistribución")
    st.caption("Vista global para entender magnitud de cambios y estaciones más afectadas.")

    mostrar_resumen_cambios_metricas(comparacion_actividades)

    g1, g2 = st.columns([1, 1])
    with g1:
        st.plotly_chart(grafico_resumen_cambios(comparacion_actividades), use_container_width=True)
    with g2:
        st.plotly_chart(grafico_top_cambios(comparacion_estaciones, top_n=12), use_container_width=True)

with tab2:
    st.subheader("Carga por estación")
    st.caption("Comparación del tiempo total asignado a cada estación en el estado actual y en la mejora.")
    st.plotly_chart(grafico_balance_comparativo(estaciones_viz), use_container_width=True)

with tab3:
    st.subheader("Movimientos de actividades")
    st.caption("Azul: actividades que entran a la estación. Rojo: actividades que salen de la estación.")

    st.plotly_chart(grafico_movimientos_por_estacion(comparacion_actividades), use_container_width=True)

    st.markdown("#### Buscar movimientos específicos")
    f1, f2, f3 = st.columns([1, 1, 2])

    with f1:
        tipo_cambio = st.multiselect(
            "Tipo de cambio",
            options=comparacion_actividades["estado_cambio"].unique().tolist(),
            default=["Movida"]
        )

    with f2:
        estacion_origen = st.selectbox(
            "Estación origen",
            ["Todas"] + ordenar_estaciones(comparacion_actividades["estacion_antes"].dropna().astype(str).unique())
        )

    with f3:
        buscar = st.text_input("Buscar actividad o palabra clave")

    tabla_filtrada = comparacion_actividades[
        comparacion_actividades["estado_cambio"].isin(tipo_cambio)
    ].copy()

    if estacion_origen != "Todas":
        tabla_filtrada = tabla_filtrada[tabla_filtrada["estacion_antes"].astype(str) == estacion_origen]

    if buscar.strip():
        texto = buscar.strip().lower()
        tabla_filtrada = tabla_filtrada[
            tabla_filtrada["actividad_id"].astype(str).str.lower().str.contains(texto, na=False) |
            tabla_filtrada["descripcion"].astype(str).str.lower().str.contains(texto, na=False)
        ]

    mostrar_cards_limitadas(tabla_filtrada, limite=24)

with tab4:
    st.subheader("Datos de apoyo")
    st.caption("Tablas disponibles solo para revisión detallada o auditoría del contenido.")

    with st.expander("Tabla de cambios de actividades"):
        st.dataframe(
            comparacion_actividades.sort_values(["estado_cambio", "estacion_antes", "actividad_id"]),
            use_container_width=True,
            hide_index=True,
            column_config={
                "actividad_id": "Actividad",
                "descripcion": "Descripción",
                "estacion_antes": "Estación antes",
                "estacion_despues": "Estación después",
                "tiempo": st.column_config.NumberColumn("Tiempo", format="%.2f s"),
                "estado_cambio": "Cambio"
            }
        )

    with st.expander("Comparación por estación"):
        vista = comparacion_estaciones.drop(columns=["orden_custom", "esfuerzo_antes", "esfuerzo_despues", "delta_esfuerzo"], errors="ignore").copy()
        st.dataframe(
            vista,
            use_container_width=True,
            hide_index=True,
            column_config={
                "tiempo_antes": st.column_config.NumberColumn("Tiempo actual", format="%.2f s"),
                "tiempo_despues": st.column_config.NumberColumn("Tiempo mejora", format="%.2f s"),
                "delta_tiempo": st.column_config.NumberColumn("Δ tiempo", format="%.2f s"),
                "actividades_antes": "Act. actual",
                "actividades_despues": "Act. mejora",
                "delta_actividades": "Δ actividades",
            }
        )
