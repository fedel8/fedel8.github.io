import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import io
import base64

st.set_page_config(page_title="LaTeX Pizarra Avanzada", layout="wide") 
st.title("Editor LaTeX con Pizarra Personalizable y Portapapeles")

# --- CONFIGURACIÓN DE MATPLOTLIB PARA LATEX ACADÉMICO ---
plt.rcParams.update({
    "text.usetex": False,
    "mathtext.fontset": "cm",
    "font.family": "serif",
})

if "canvas_key" not in st.session_state:
    st.session_state.canvas_key = 0

# 1. Parámetros en la barra lateral
with st.sidebar:
    st.header("Estilo de Ecuación")
    f_size = st.slider("Tamaño de fuente LaTeX", 20, 80, 40)
    f_color = st.color_picker("Color de letra LaTeX", "#000000")
    f_alpha = st.slider("Opacidad de la ecuación (Alpha)", 0.0, 1.0, 1.0, 0.1)
    
    st.header("Fondo del Lienzo")
    bg_transparent = st.checkbox("Fondo Transparente (Sin color)", value=False)
    # Selector de color dinámico para el fondo (se deshabilita si es transparente)
    bg_color = st.color_picker("Color de Fondo", "#FFFFFF", disabled=bg_transparent)
    
    st.header("Herramientas de Dibujo")
    stroke_width = st.slider("Grosor del pincel", 1, 15, 4)
    stroke_color = st.color_picker("Color del pincel", "#FF0000")
    drawing_mode = st.selectbox("Herramienta", ("freedraw", "line", "rect"))

# 2. Entrada de texto
latex_input = st.text_area("Código LaTeX:", r"f(x) = \int_{a}^{b} \sqrt{x^2 + 1} \, dx")

# Función optimizada para generar el lienzo con colores personalizados
def latex_to_image_custom(latex_str, font_size, color_hex, alpha, is_transparent, bg_hex):
    fig, ax = plt.subplots(figsize=(10, 3.2), dpi=150)
    fig.patch.set_alpha(0.0)
    ax.set_facecolor((0,0,0,0))
    
    ax.text(0.5, 0.5, f"${latex_str}$", 
            fontsize=font_size, 
            color=color_hex,
            alpha=alpha,
            ha='center', va='center')
    
    ax.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.4, transparent=True)
    buf.seek(0)
    plt.close(fig)
    
    latex_img = Image.open(buf).convert("RGBA")
    target_width, target_height = 1000, 320
    
    # Manejo del fondo según la elección del usuario
    if is_transparent:
        # Si es transparente, dibujamos una cuadrícula guía tenue de asistencia
        base_img = Image.new("RGBA", (target_width, target_height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(base_img)
        square_size = 12
        for y in range(0, target_height, square_size):
            for x in range(0, target_width, square_size):
                if (x // square_size + y // square_size) % 2 == 0:
                    draw.rectangle([x, y, x + square_size, y + square_size], fill=(245, 245, 245, 255))
                else:
                    draw.rectangle([x, y, x + square_size, y + square_size], fill=(255, 255, 255, 255))
    else:
        # Convertir el color HEX del widget a tupla RGB para el fondo sólido
        bg_rgb = tuple(int(bg_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        base_img = Image.new("RGBA", (target_width, target_height), bg_rgb + (255,))
                    
    offset_x = (target_width - latex_img.width) // 2
    offset_y = (target_height - latex_img.height) // 2
    base_img.paste(latex_img, (offset_x, offset_y), latex_img)
    return base_img

# 3. Renderizado y Lienzo de Dibujo
if latex_input:
    st.subheader("Pizarra Interactiva:")
    
    try:
        bg_image = latex_to_image_custom(latex_input, f_size, f_color, f_alpha, bg_transparent, bg_color)
        
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.2)",
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_image=bg_image,
            update_streamlit=True,
            height=320,  
            width=1000,  
            drawing_mode=drawing_mode,
            return_image_data=True,
            key=f"canvas_interactive_{st.session_state.canvas_key}",
        )
    except Exception as e:
        st.error(f"Error en la generación matemática: {e}")

    # --- DISEÑO DE BOTONES INFERIORES ---
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧼 Limpiar Trazos", use_container_width=True):
            st.session_state.canvas_key += 1
            st.rerun()
            
    with col2:
        # Preparar la imagen de exportación final de fondo (con color o transparente pura sin cuadrícula)
        if bg_transparent:
            export_img = Image.new("RGBA", (1000, 320), (0, 0, 0, 0))
            math_layer = latex_to_image_custom(latex_input, f_size, f_color, f_alpha, is_transparent=False, bg_hex="#FFFFFF")
            # Extraer solo la ecuación (sin el blanco de base)
            fig, ax = plt.subplots(figsize=(10, 3.2), dpi=150)
            fig.patch.set_alpha(0.0)
            ax.set_facecolor((0,0,0,0))
            ax.text(0.5, 0.5, f"${latex_input}$", fontsize=f_size, color=f_color, alpha=f_alpha, ha='center', va='center')
            ax.axis('off')
            b = io.BytesIO()
            plt.savefig(b, format='png', bbox_inches='tight', pad_inches=0.4, transparent=True)
            b.seek(0)
            plt.close(fig)
            pure_math = Image.open(b).convert("RGBA")
            ox = (1000 - pure_math.width) // 2
            oy = (320 - pure_math.height) // 2
            export_img.paste(pure_math, (ox, oy), pure_math)
        else:
            bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            export_img = Image.new("RGBA", (1000, 320), bg_rgb + (255,))
            math_layer = latex_to_image_custom(latex_input, f_size, f_color, f_alpha, is_transparent=False, bg_hex=bg_color)
            export_img.paste(math_layer, (0,0), math_layer)

        # Si el usuario dibujó algo, superponer los trazos
        if canvas_result is not None and canvas_result.image_data is not None:
            draw_data = canvas_result.image_data
            draw_img = Image.fromarray(draw_data.astype('uint8'), 'RGBA')
            export_img.alpha_composite(draw_img)
        
        # Procesar a Base64 para pasarle la info al botón JavaScript
        img_buffer = io.BytesIO()
        export_img.save(img_buffer, format="PNG")
        b64_image = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        # BOTÓN SIEMPRE VISIBLE MEDIANTE HTML/JS COPIER
        st.components.v1.html(f"""
            <button id="copy-btn" style="
                width: 100%; 
                height: 42px; 
                background-color: #2e7d32; 
                color: white; 
                border: none; 
                border-radius: .25rem; 
                cursor: pointer;
                font-size: 16px;
                font-weight: 500;
                box-shadow: 0 2px 4px rgba(0,0,0,0.15);">
                📋 Copiar al Portapapeles
            </button>
            <script>
                document.getElementById('copy-btn').onclick = async () => {{
                    try {{
                        const base64Data = "{b64_image}";
                        const byteCharacters = atob(base64Data);
                        const byteNumbers = new Array(byteCharacters.length);
                        for (let i = 0; i < byteCharacters.length; i++) {{
                            byteNumbers[i] = byteCharacters.charCodeAt(i);
                        }}
                        const byteArray = new Uint8Array(byteNumbers);
                        const blob = new Blob([byteArray], {{ type: 'image/png' }});
                        
                        const item = new ClipboardItem({{ "image/png": blob }});
                        await navigator.clipboard.write([item]);
                        alert("¡Imagen copiada al portapapeles! Ya podés pegarla con Ctrl+V.");
                    }} catch (err) {{
                        alert("Error de permisos del navegador al copiar: " + err);
                    }}
                }};
            </script>
        """, height=55)

