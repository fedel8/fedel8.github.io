import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Configuración de página de Streamlit
st.set_page_config(page_title="Modelo Langmuir-Polanyi", layout="wide")

st.title("📊 Simulador de Adsorción: Enfoque Langmuir-Polanyi (D-A)")
st.write(
    "Este simulador utiliza la **Teoría del Potencial de Polanyi (Dubinin-Astakhov)** "
    "para promediar y proyectar isotermas de adsorción a la temperatura del pozo a partir de datos base."
)

# ----------------------------------------------------
# Barra Lateral - Parámetros de Entrada
# ----------------------------------------------------
st.sidebar.header("🔧 Parámetros de Entrada")

# Temperaturas
T_lab = st.sidebar.number_input("Temperatura de Laboratorio (T_lab) [K]", min_value=100.0, max_value=500.0, value=298.15, step=5.0)
T_pozo = st.sidebar.number_input("Temperatura del Pozo (T_pozo) [K]", min_value=100.0, max_value=600.0, value=363.15, step=5.0)

# Parámetros del modelo
Vm_base = st.sidebar.number_input("Capacidad Máxima Vm_base [cm³/g]", min_value=0.1, max_value=100.0, value=5.0, step=0.5)
P_L_25 = st.sidebar.number_input("Presión de Langmuir a 25°C (298.15 K) [MPa]", min_value=0.01, max_value=50.0, value=3.5, step=0.5)
n_polanyi = st.sidebar.number_input("Exponente característico (n)", min_value=1.0, max_value=6.0, value=3.7, step=0.1)

# ----------------------------------------------------
# Ajuste de Visualización (Nuevo Slider de Font Size)
# ----------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🎨 Ajustes de Gráfico")
font_size_global = st.sidebar.slider("Tamaño de Fuente Global", min_value=10, max_value=28, value=14, step=1)

# Constantes Físicas del Metano (CH4) como referencia para el estado supercrítico
T_c = 190.56  # Temperatura crítica del metano en K
P_c = 4.599   # Presión crítica del metano en MPa
R = 8.3144    # Constante universal de los gases J/(mol*K)


# ----------------------------------------------------
# Funciones del Modelo Matemático
# ----------------------------------------------------
def calcular_presion_saturacion_virtual(T, n):
    """Calcula la presión de saturación virtual usando el exponente n de Polanyi."""
    if T > T_c:
        # Reemplazamos el exponente fijo 2 por el parámetro n (C22 en tu Excel)
        return P_c * ((T / T_c) ** n)
    return P_c

# --- Flujo de cálculos corregidos ---
# 1. Calculamos las presiones de saturación virtuales usando el exponente n
Ps_25 = calcular_presion_saturacion_virtual(298.15, n_polanyi)
Ps_lab = calcular_presion_saturacion_virtual(T_lab, n_polanyi)
Ps_pozo = calcular_presion_saturacion_virtual(T_pozo, n_polanyi)

 
epsilon_L_25 = R * 298.15 * np.log(Ps_25 / P_L_25)
#E_caracteristica = epsilon_L_25 
E_caracteristica = epsilon_L_25 / ((np.log(2)) ** (1 / n_polanyi))



def modelo_dubinin_astakhov(P_array, T, Ps, Vm, E, n):
    """Calcula el volumen adsorbido usando la ecuación D-A."""
    V_adsorbido = []
    for P in P_array:
        if P <= 0:
            V_adsorbido.append(0.0)
            continue
        epsilon = R * T * np.log(Ps / P)
        fraccion_llenado = np.exp(- (epsilon / E) ** n)
        V_adsorbido.append(Vm * fraccion_llenado)
    return np.array(V_adsorbido)

# ----------------------------------------------------
# Cálculos e Interfaz de Resultados
# ----------------------------------------------------
# Rango de presiones para graficar (0 a 40 MPa)
presiones = np.linspace(0.01, 40.0, 1000)

# Calcular curvas
V_lab = modelo_dubinin_astakhov(presiones, T_lab, Ps_lab, Vm_base, E_caracteristica, n_polanyi)
V_pozo = modelo_dubinin_astakhov(presiones, T_pozo, Ps_pozo, Vm_base, E_caracteristica, n_polanyi)

# Layout de columnas en Streamlit para mostrar métricas rápidas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Energía Característica (E)", value=f"{E_caracteristica:.1f} J/mol")
with col2:
    st.metric(label="P_sat Virtual Lab", value=f"{Ps_lab:.2f} MPa")
with col3:
    st.metric(label="P_sat Virtual Pozo", value=f"{Ps_pozo:.2f} MPa")

# ----------------------------------------------------
# Gráfico interactivo con Plotly
# ----------------------------------------------------
fig = go.Figure()

# Línea del Laboratorio
fig.add_trace(go.Scatter(
    x=presiones, y=V_lab,
    mode='lines',
    name=f'Condición Lab ({T_lab} K)',
    line=dict(color='#1f77b4', width=3)
))

# Línea del Pozo
fig.add_trace(go.Scatter(
    x=presiones, y=V_pozo,
    mode='lines',
    name=f'Condición Pozo ({T_pozo} K)',
    line=dict(color='#ff7f0e', width=3, dash='dash')
))

# Configuraciones del diseño del gráfico (Sintaxis corregida para Plotly moderno)
fig.update_layout(
    title=dict(
        text="Isotermas de Adsorción (Extrapolación por Potencial de Polanyi)",
        font=dict(size=font_size_global + 4) # El título queda un poco más grande
    ),
    xaxis=dict(
        title=dict(
            text="Presión del Gas (MPa)",
            font=dict(size=font_size_global) # Estructura correcta para la fuente del título
        ),
        tickfont=dict(size=font_size_global - 2) # Fuente de los números del eje
    ),
    yaxis=dict(
        title=dict(
            text="Volumen Adsorbido V(P) [cm³/g]",
            font=dict(size=font_size_global) # Estructura correcta para la fuente del título
        ),
        tickfont=dict(size=font_size_global - 2) # Fuente de los números del eje
    ),
    hovermode="x unified",
    legend=dict(
        yanchor="bottom", y=0.01, xanchor="right", x=0.99,
        font=dict(size=font_size_global - 2)
    ),
    margin=dict(l=50, r=40, t=60, b=50),
    template="plotly_white",
    font=dict(size=font_size_global) # Fuente global de respaldo
)

# Mantenemos theme=None para evitar que Streamlit pise los tamaños seteados
st.plotly_chart(fig, use_container_width=True, theme=None)


# Cuadro informativo explicativo
st.info(
    "💡 **Nota Técnica:** Observá cómo al aumentar la temperatura hacia la condición de pozo "
    "(línea naranja discontinua), la curva de adsorción se desplaza hacia abajo de forma automática. "
    "Esto representa el comportamiento exotérmico real del yacimiento sin necesidad de realizar "
    "múltiples experimentos de laboratorio térmicos."
)

