import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

def parse_latex(expr):
    replacements = {
        r'\sin': 'np.sin', r'\cos': 'np.cos', r'\tan': 'np.tan',
        r'\exp': 'np.exp', r'\sqrt': 'np.sqrt', r'\pi': 'np.pi',
        r'\log': 'np.log', '^': '**', '{': '(', '}': ')'
    }
    for old, new in replacements.items():
        expr = expr.replace(old, new)
    return expr

st.set_page_config(page_title="Generador Paramétrico 3D", layout="wide")

st.title("📊 Generador de Datos Paramétricos")

# --- Configuración Lateral ---
with st.sidebar:
    st.header("Configuración")
    t_min = st.number_input("t inicial", value=0.0)
    t_max = st.number_input("t final", value=10.0)
    n_points = st.number_input("Número de puntos", min_value=2, value=500)
    num_y = st.number_input("Número de columnas Y adicionales", min_value=1, value=2)

# --- Entrada de Ecuaciones ---
t = np.linspace(t_min, t_max, n_points)
data = {"t": t}

st.subheader("Ecuaciones")
col_x, _ = st.columns([1, 1])
with col_x:
    formula_x = st.text_input("Eje X: f(t)", value="np.cos(t)")

formulas_y = []
cols = st.columns(2)
for i in range(num_y):
    with cols[i % 2]:
        default_val = f"np.sin(t)" if i == 0 else f"t*0.1"
        f_y = st.text_input(f"Columna Y_{i+1}: f(t)", value=default_val, key=f"y{i}")
        formulas_y.append(f_y)

# --- Procesamiento ---
try:
    env = {"np": np, "t": t}
    data[formula_x] = np.array(eval(parse_latex(formula_x), env)).flatten()
    for f_y in formulas_y:
        data[f_y] = np.array(eval(parse_latex(f_y), env)).flatten()
    
    df = pd.DataFrame(data)
    all_columns = df.columns.tolist()

    # --- Lógica de Gráficos ---
    st.divider()
    
    # Opción 3D si hay suficientes columnas
    show_3d = False
    if len(all_columns) >= 3:
        st.subheader("Visualización Especial")
        show_3d = st.checkbox("¿Deseas generar un gráfico 3D de curva paramétrica?")
    
    if show_3d:
        c1, c2, c3 = st.columns(3)
        with c1: col_3dx = st.selectbox("Eje X (3D)", all_columns, index=1)
        with c2: col_3dy = st.selectbox("Eje Y (3D)", all_columns, index=2)
        with c3: col_3dz = st.selectbox("Eje Z (3D)", all_columns, index=0)
        
        fig_3d = go.Figure(data=[go.Scatter3d(
            x=df[col_3dx], y=df[col_3dy], z=df[col_3dz],
            mode='lines',
            line=dict(color='blue', width=4)
        )])
        fig_3d.update_layout(scene=dict(xaxis_title=col_3dx, yaxis_title=col_3dy, zaxis_title=col_3dz))
        st.plotly_chart(fig_3d, use_container_width=True)
    else:
        # Gráfico 2D estándar
        fig, ax = plt.subplots(figsize=(10, 4))
        for f_y in formulas_y:
            ax.plot(df[formula_x].values, df[f_y].values, label=f"${f_y}$")
        ax.set_xlabel(f"${formula_x}$")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

    # --- Tabla y Descarga ---
    st.divider()
    st.subheader("Vista Previa y Descarga")
    st.dataframe(df.head(10))
    st.download_button("💾 Descargar Datos.csv", df.to_csv(index=False).encode('utf-8'), "Datos.csv", "text/csv")

except Exception as e:
    st.error(f"Error: {e}")

