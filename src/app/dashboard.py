import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
import mlflow
import os
from pathlib import Path

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Forecasting Eléctrico Europeo", page_icon="⚡", layout="wide")
st.title("⚡ Dashboard de Demanda Eléctrica Europea (ENTSO-E)")
st.markdown("Predicción de demanda horaria usando **CatBoost Global**, variables meteorológicas y **FastAPI**.")

COUNTRY_INFO = {
    'ES': {'lat': 40.46, 'lon': -3.75, 'name': 'España'},
    'FR': {'lat': 46.22, 'lon': 2.21, 'name': 'Francia'},
    'DE': {'lat': 51.16, 'lon': 10.45, 'name': 'Alemania'},
    'IT': {'lat': 41.87, 'lon': 12.56, 'name': 'Italia'}
}

# ==========================================
# 2. CARGA DE DATOS LOCALES (CACHE)
# ==========================================
@st.cache_data
def load_historical_data(full=False):
    path = "data/processed/features_clean.parquet"
    if os.path.exists(path):
        df = pd.read_parquet(path)
        if full: return df
        last_date = df['ds'].max()
        return df[df['ds'] >= (last_date - pd.Timedelta(days=7))]
    return None

@st.cache_data
def load_cv_data():
    path = "data/processed/cv_predictions.parquet"
    if os.path.exists(path):
        df_cv = pd.read_parquet(path)
        df_cv['ds'] = pd.to_datetime(df_cv['ds'])
        return df_cv
    return None

@st.cache_data
def load_train_preds(full=False):
    path = "data/processed/train_predictions.parquet"
    if os.path.exists(path):
        df_train = pd.read_parquet(path)
        df_train['ds'] = pd.to_datetime(df_train['ds'])
        if full: return df_train
        last_date = df_train['ds'].max()
        return df_train[df_train['ds'] >= (last_date - pd.Timedelta(days=7))]
    return None

df_hist = load_historical_data()
df_cv = load_cv_data()
df_train_preds = load_train_preds()

# ==========================================
# 3. PANEL LATERAL: CONTROLES Y MLFLOW (VERSIÓN ROBUSTA)
# ==========================================
st.sidebar.header("🌍 Filtros")

# Definir país fuera del try para evitar el NameError
paises_disponibles = list(COUNTRY_INFO.keys())
pais_seleccionado = st.sidebar.selectbox("Selecciona un país:", paises_disponibles)

st.sidebar.markdown("---")
st.sidebar.header("📊 Métricas del Modelo")

try:
    # Ajustamos la ruta para llegar a la raíz (ML_template)
    # IMPORTANTE: Revisa si necesitas 2 o 3 .parent según tu carpeta
    BASE_DIR = Path(__file__).resolve().parent.parent.parent 
    DB_PATH = f"sqlite:///{BASE_DIR.as_posix()}/mlflow.db"
    mlflow.set_tracking_uri(DB_PATH)

    # 1. Buscamos el experimento
    experiment = mlflow.get_experiment_by_name("Portfolio_Forecasting_Global")
    
    if experiment:
        # 2. Obtenemos el último run
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"],
            max_results=1
        )
        
        if not runs.empty:
            last_run = runs.iloc[0]
        

            # Intentamos obtener las métricas con los nombres exactos que usa MLflow
            mae = last_run.get("metrics.cv_mae")
            rmse = last_run.get("metrics.cv_rmse")
            
            # Solo mostramos si no son None, si son None ponemos "N/A" en lugar de 0
            if mae is not None:
                st.sidebar.metric("MAE (Error Medio)", f"{float(mae):.2f} MW")
            else:
                st.sidebar.metric("MAE (Error Medio)", "No hay datos")

            if rmse is not None:
                st.sidebar.metric("RMSE (Error Cuadrático)", f"{float(rmse):.2f} MW")
            else:
                st.sidebar.metric("RMSE (Error Cuadrático)", "No hay datos")
        else:
            st.sidebar.warning("No hay ejecuciones (runs) registradas.")
    else:
        st.sidebar.error("Experimento no encontrado en la DB.")

except Exception as e:
    st.sidebar.error(f"Error de conexión: {e}")
# ==========================================
# 🚀 PESTAÑAS (TABS)
# ==========================================
tab1, tab2 = st.tabs(["🌍 Situación y Predicción", "🧠 Evaluación del Modelo (In-Sample)"])

# ---------------------------------------------------------
# TABA 1: EL DASHBOARD PRINCIPAL (Mapa y Predicción Futura)
# ---------------------------------------------------------
with tab1:
    st.subheader("🗺️ Evolución Meteorológica y Demanda")
    if df_hist is not None and not df_hist.empty:
        min_time = df_hist['ds'].min().to_pydatetime()
        max_time = df_hist['ds'].max().to_pydatetime()
        selected_time = st.slider("Desplaza el slider para viajar en el tiempo (Últimos 7 días):", 
                                  min_value=min_time, max_value=max_time, value=max_time, 
                                  step=pd.Timedelta(hours=1), format="YYYY-MM-DD HH:mm")

        df_mapa = df_hist[df_hist['ds'] == selected_time].copy()
        if not df_mapa.empty:
            df_mapa['País'] = df_mapa['unique_id'].map(lambda x: COUNTRY_INFO[x]['name'])
            df_mapa['lat'] = df_mapa['unique_id'].map(lambda x: COUNTRY_INFO[x]['lat'])
            df_mapa['lon'] = df_mapa['unique_id'].map(lambda x: COUNTRY_INFO[x]['lon'])
            df_mapa['hover_text'] = (df_mapa['País'] + "<br>Demanda: " + df_mapa['y'].round(0).astype(str) + " MW<br>" +
                                     "Temperatura: " + df_mapa['temperature'].round(1).astype(str) + " °C")

            temp_min_global = df_hist['temperature'].min()
            temp_max_global = df_hist['temperature'].max()

            fig_map = px.scatter_geo(
                df_mapa, lat="lat", lon="lon", size="y", color="temperature",
                hover_name="País", hover_data={"lat": False, "lon": False, "y": True, "temperature": True},
                color_continuous_scale="inferno", range_color=[temp_min_global, temp_max_global], size_max=40,
                title=f"Situación Europea: {selected_time.strftime('%Y-%m-%d %H:00')}", scope="europe"
            )
            fig_map.update_traces(text=df_mapa['hover_text'], hoverinfo="text")
            fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=400)
            st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("---")
    st.subheader(f"🔮 Predicción Futura: {COUNTRY_INFO[pais_seleccionado]['name']}")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        horizonte = st.slider("Horizonte (Horas)", min_value=12, max_value=168, value=24, step=12)
        btn_predict = st.button("Lanzar Predicción", type="primary", use_container_width=True)
    
    def create_base_figure(country, df_h, df_cv, df_tr):
        fig = go.Figure()
        h_c = df_h[df_h['unique_id'] == country] if df_h is not None else None
        tr_c = df_tr[df_tr['unique_id'] == country] if df_tr is not None else None
        cv_c = df_cv[df_cv['unique_id'] == country] if df_cv is not None else None

        if h_c is not None and not h_c.empty:
            fig.add_trace(go.Scatter(x=h_c['ds'], y=h_c['y'], mode='lines', name='Demanda Real', line=dict(color='gray', width=2)))
        if tr_c is not None and not tr_c.empty:
            fig.add_trace(go.Scatter(x=tr_c['ds'], y=tr_c['CatBoost'], mode='lines', name='Ajuste Modelo', line=dict(color='green', width=1.5, dash='dash')))
        if cv_c is not None and not cv_c.empty:
            fig.add_trace(go.Scatter(x=cv_c['ds'], y=cv_c['CatBoost'], mode='lines', name='Backtesting (CV)', line=dict(color='orange', width=2, dash='dot')))
        return fig

    with col2:
        if btn_predict:
            with st.spinner("Consultando a FastAPI..."):
                try:
                    response = requests.post("http://127.0.0.1:8000/predict", json={"horizon": horizonte, "country": pais_seleccionado})
                    if response.status_code == 200:
                        df_pred = pd.DataFrame(response.json()["data"])
                        df_pred['ds'] = pd.to_datetime(df_pred['ds'])
                        
                        fig = create_base_figure(pais_seleccionado, df_hist, df_cv, df_train_preds)
                        fig.add_trace(go.Scatter(x=df_pred['ds'], y=df_pred['CatBoost'], mode='lines', name='Predicción Futura', line=dict(color='blue', width=3)))

                        for level, opacity in zip([95, 80], [0.1, 0.25]):
                            hi, lo = f'CatBoost-hi-{level}', f'CatBoost-lo-{level}'
                            if hi in df_pred.columns and lo in df_pred.columns:
                                fig.add_trace(go.Scatter(x=df_pred['ds'], y=df_pred[hi], mode='lines', line=dict(width=0), showlegend=False))
                                fig.add_trace(go.Scatter(x=df_pred['ds'], y=df_pred[lo], mode='lines', fill='tonexty', fillcolor=f'rgba(0, 0, 255, {opacity})', line=dict(width=0), name=f'Confianza ({level}%)'))

                        fig.update_layout(title="Predicción a Futuro", xaxis_title="Fecha", yaxis_title="Demanda (MW)", hovermode="x unified", template="plotly_white")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error(f"Error de la API: {response.text}")
                except Exception:
                    st.error("🚨 No se pudo conectar a FastAPI (puerto 8000).")
        else:
            fig_base = create_base_figure(pais_seleccionado, df_hist, df_cv, df_train_preds)
            fig_base.update_layout(title="Histórico Reciente", xaxis_title="Fecha", yaxis_title="Demanda (MW)", hovermode="x unified", template="plotly_white")
            st.plotly_chart(fig_base, use_container_width=True)

# ---------------------------------------------------------
# TAB 2: ANÁLISIS DEL MODELO (Todo el histórico In-Sample)
# ---------------------------------------------------------
with tab2:
    st.subheader(f"🔍 Análisis de Aprendizaje del Modelo: {COUNTRY_INFO[pais_seleccionado]['name']}")
    st.markdown("Aquí puedes evaluar cómo se ha comportado el modelo sobre el **100% de los datos históricos** que usó para entrenar (In-Sample).")
    
    # Cargamos TODO el dataset
    df_train_full = load_train_preds(full=True)
    df_hist_full = load_historical_data(full=True)

    if df_train_full is not None and df_hist_full is not None:
        # Filtrar por país
        df_tr_c = df_train_full[df_train_full['unique_id'] == pais_seleccionado]
        df_h_c = df_hist_full[df_hist_full['unique_id'] == pais_seleccionado]

        # Cruzar realidad vs predicción para comparar
        df_eval = pd.merge(df_h_c[['ds', 'y']], df_tr_c[['ds', 'CatBoost']], on='ds', how='inner')
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("**Realidad vs. Predicción (Scatter Plot)**")
            fig_scatter = px.scatter(
                df_eval, x='y', y='CatBoost', opacity=0.3,
                labels={'y': 'Demanda Real (MW)', 'CatBoost': 'Demanda Predicha (MW)'},
                title="Correlación del Entrenamiento"
            )
            # Línea ideal a 45 grados (Realidad = Predicción)
            min_val = min(df_eval['y'].min(), df_eval['CatBoost'].min())
            max_val = max(df_eval['y'].max(), df_eval['CatBoost'].max())
            fig_scatter.add_shape(type="line", x0=min_val, y0=min_val, x1=max_val, y1=max_val, line=dict(color="red", dash="dash"))
            fig_scatter.update_layout(template="plotly_white")
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with col_chart2:
            st.markdown("**Serie Temporal Completa (Navegable)**")
            fig_full_ts = go.Figure()
            fig_full_ts.add_trace(go.Scatter(x=df_eval['ds'], y=df_eval['y'], mode='lines', name='Real', line=dict(color='gray')))
            fig_full_ts.add_trace(go.Scatter(x=df_eval['ds'], y=df_eval['CatBoost'], mode='lines', name='Predicción', line=dict(color='green', dash='dot')))
            fig_full_ts.update_layout(template="plotly_white", xaxis=dict(rangeslider=dict(visible=True)), hovermode="x unified")
            st.plotly_chart(fig_full_ts, use_container_width=True)
            
    else:
        st.warning("⚠️ No se encontraron las predicciones de entrenamiento. Asegúrate de que `predict_in_sample` funcionó en el entrenamiento.")