import pandas as pd
import streamlit as st
import io

# Configuración de la página
st.set_page_config(
    page_title="Mexweld <-> Cadweld",
    page_icon="🔄",
    layout="wide"
)

# Estilos CSS personalizados para mejorar la apariencia
st.markdown("""
    <style>
    /* Forzamos el fondo oscuro general de la app */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Forzamos el color del texto general a blanco */
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #fafafa !important;
    }

    /* Estilo de tus tarjetas (Resultados) */
    .result-card {
        padding: 20px;
        border-radius: 15px;
        background-color: #262730; /* Fondo gris oscuro de la tarjeta */
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 10px;
        border: 1px solid #444;
    }
    
    .card-label {
        font-size: 0.85rem;
        color: #b0b0b0; /* Un gris clarito para el subtitulo */
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    
    .card-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
        color: #ffffff; /* Blanco puro para el valor */
    }
    
    /* Ajuste para los inputs para que no se vean raros */
    .stTextInput input {
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS DE EQUIVALENCIAS ---
# Diccionario maestro con los datos proporcionados.
# Se puede expandir fácilmente agregando más líneas.
DB_DATA = [
    {"descripcion": "Cable a Cable de Paso", "mexweld": "CCP", "cadweld": "SS"},
    {"descripcion": "Cable a Cable con Derivacion", "mexweld": "CCD", "cadweld": "PC"},
    {"descripcion": "Cable a Cable en 'T'", "mexweld": "CCT", "cadweld": "TA"},
    {"descripcion": "Cable a Cable en 'X' Cortando uno", "mexweld": "CCX", "cadweld": "XA"},
    {"descripcion": "Cable a Cable en 'X' Empalmados", "mexweld": "CCXE", "cadweld": "XB"},
    {"descripcion": "Cable a Cable de Paso y Paralelos", "mexweld": "CCPP", "cadweld": "PT"},
    {"descripcion": "Cable a Cable en Paralelo Vertical", "mexweld": "CCPPV", "cadweld": "PH"},
    {"descripcion": "Cable de Tope a Varilla", "mexweld": "CTV", "cadweld": "GR"},
    {"descripcion": "Cable de Paso a Varilla", "mexweld": "CPV", "cadweld": "GT"},
    {"descripcion": "Cable de Paso a Varilla de Paso", "mexweld": "CPVP", "cadweld": "GY"},
    {"descripcion": "Dos Cables de paso a Varilla de Tierra", "mexweld": "CVCCH", "cadweld": "ND"},
    {"descripcion": "Varilla a Varilla", "mexweld": "VV", "cadweld": "GB"},
    {"descripcion": "Cable Horizontal a Tubo Horizontal", "mexweld": "CHTH", "cadweld": "HA"},
    {"descripcion": "Cable Horizontal a Placa Horizontal", "mexweld": "CHPH", "cadweld": "HS"},
    {"descripcion": "Cable a 45\" a Tubo Vertical", "mexweld": "C45TV", "cadweld": "VS"},
    {"descripcion": "Cable a 45\" a Placa Vertical", "mexweld": "C45PV", "cadweld": "VS"},
    {"descripcion": "Cable de Paso Horizontal a Placa Horizontal", "mexweld": "CPHPH", "cadweld": "HT"},
    {"descripcion": "Cable de Paso Horizontal a Placa Vertical", "mexweld": "CPHPV", "cadweld": "VT"},
    {"descripcion": "Cable de Paso Vertical a Placa Vertical", "mexweld": "CPVPV", "cadweld": "VV"},
    {"descripcion": "Cable hacia abajo a Superficie Vertical", "mexweld": "CAPV", "cadweld": "VF"},
    {"descripcion": "Cable hacia arriba a Superficie Vertical", "mexweld": "CVAPV", "cadweld": "VB"},
    {"descripcion": "Cable a Zapata tipo 'Z'", "mexweld": "CZZ", "cadweld": "LA"},
    {"descripcion": "Cable a Zapata tipo 'L'", "mexweld": "CZL", "cadweld": "GL"},
    {"descripcion": "Cable a Barra de Tierra", "mexweld": "CBT", "cadweld": "LJ"},
    {"descripcion": "Cable Vertical de Paso a Barra Horizontal", "mexweld": "CBVT", "cadweld": "LQ"},
    {"descripcion": "Cable a Varilla Corrugada Horizontal", "mexweld": "CHVCH", "cadweld": "RR"},
    {"descripcion": "Cable de paso a Varilla Corrugada Vertical", "mexweld": "CVCXE", "cadweld": "RC"},
    {"descripcion": "Cable a Varilla Corrugada Vertical", "mexweld": "CHVCV", "cadweld": "RJ"},
    {"descripcion": "Cable a Varilla Corrugada Horizontal", "mexweld": "CHCXE", "cadweld": "RD"},
    {"descripcion": "Pinza Facil Cambio - Estandar", "mexweld": "M-PE", "cadweld": "L160"},
    {"descripcion": "Pinza Facil Cambio - Grande", "mexweld": "M-PG", "cadweld": "L159"},
    {"descripcion": "Chispero para Encendido Fulminante", "mexweld": "E-CEF", "cadweld": "T320"},
    {"descripcion": "Mexseal - Masilla para Sellado de Moldes", "mexweld": "M-MSM", "cadweld": "T317"},
    {"descripcion": "Cepillo de Alambre", "mexweld": "M-CA", "cadweld": "T313"},
    {"descripcion": "Cepillo de Alambre Doble", "mexweld": "M-CAD", "cadweld": "T314"},
    {"descripcion": "Cepillo Limpiador de Molde", "mexweld": "M-CLM", "cadweld": "T394"},
    {"descripcion": "Lima para Limpiar Molde", "mexweld": "M-LLC", "cadweld": "T329"},
    {"descripcion": "Sujetador para Cable", "mexweld": "M-SC", "cadweld": "B265"},
    {"descripcion": "Espatula para remover escoria (65 al 115)", "mexweld": "M-E65", "cadweld": "B136A"},
    {"descripcion": "Espatula para remover escoria (150 al 250)", "mexweld": "M-E150", "cadweld": "B136B"},
    {"descripcion": "Raspador de Acero Estructural", "mexweld": "M-RAE", "cadweld": "T321"},
    {"descripcion": "Disco Reten para Cargas 25 y 32", "mexweld": "M-DR1", "cadweld": "B117A"},
    {"descripcion": "Disco Reten para Cargas 45, 65, 90 y 115", "mexweld": "M-DR2", "cadweld": "B117B"},
    {"descripcion": "Disco Reten para Cargas 150, 200 y 250", "mexweld": "M-DR3", "cadweld": "B117C"},
]

# --- FUNCIONES AUXILIARES ---

def normalize(text):
    """Limpia el texto para comparaciones (mayúsculas, sin espacios)."""
    if not isinstance(text, str):
        return str(text) if text else ""
    return text.strip().upper().replace(" ", "")

@st.cache_data
def get_mappings():
    """Genera diccionarios de búsqueda rápida."""
    mex_to_cad = {}
    cad_to_mex = {}
    
    for item in DB_DATA:
        m_norm = normalize(item["mexweld"])
        c_norm = normalize(item["cadweld"])
        desc = item["descripcion"]
        
        if m_norm:
            mex_to_cad[m_norm] = {"equiv": item["cadweld"], "desc": desc}
        if c_norm:
            cad_to_mex[c_norm] = {"equiv": item["mexweld"], "desc": desc}
            
    return mex_to_cad, cad_to_mex

def find_equivalence(code, mapping, target_brand):
    """Busca un código en la dirección seleccionada."""
    norm_code = normalize(code)
    if not norm_code:
        return None
    
    if norm_code in mapping:
        data = mapping[norm_code]
        return {
            "original": code,
            "equivalente": data["equiv"],
            "marca_equivalente": target_brand,
            "descripcion": data["desc"],
            "encontrado": True
        }
        
    return {
        "original": code,
        "equivalente": "No encontrado",
        "marca_equivalente": "-",
        "descripcion": "Sin descripción",
        "encontrado": False
    }

# --- INTERFAZ DE USUARIO ---

st.title("Convertidor Mexweld ↔ Cadweld")
st.markdown("Herramienta rápida para consultar equivalencias de moldes y accesorios.")

mex_map, cad_map = get_mappings()

# Selector de dirección
direction = st.radio(
    "¿Qué desea hacer?",
    ["De Mexweld a Cadweld", "De Cadweld a Mexweld"],
    horizontal=True
)

# Configuración según selección
if direction == "De Mexweld a Cadweld":
    search_map = mex_map
    source_brand = "Mexweld"
    target_brand = "Cadweld"
else:
    search_map = cad_map
    source_brand = "Cadweld"
    target_brand = "Mexweld"

# Tabs para separar funcionalidad
tab_busqueda, tab_masiva, tab_lista = st.tabs(["🔍 Búsqueda Rápida", "📂 Carga Masiva (Excel)", "📋 Ver Catálogo Completo"])

with tab_busqueda:
    st.subheader("Consultar un código individual")
    col1, col2 = st.columns([2, 1])
    with col1:
        code_input = st.text_input(f"Ingrese el código ({source_brand}):", placeholder="Ej: CCP" if source_brand == "Mexweld" else "Ej: SS").strip()
    
    if code_input:
        res = find_equivalence(code_input, search_map, target_brand)
        
        if res and res["encontrado"]:
            st.success(f"✅ Código encontrado.")
            
            # Diseño de tarjeta para el resultado
            st.markdown(f"""
            <div class="result-card">
                <h3 style="margin: 0 0 15px 0; color: #ffff; font-size: 1.2rem; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                    {res['descripcion']}
                </h3>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div class="card-value" style="color: #329bfc;">{res['original'].upper()}</div>
                    </div>
                    <div style="padding: 0 15px; font-size: 2rem; color: #ffff;">➜</div>
                    <div style="flex: 1; text-align: right;">
                        <div class="card-label">{res['marca_equivalente']}</div>
                        <div class="card-value" style="color: #28a745;">{res['equivalente']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("❌ Código no encontrado en la base de datos.")
            st.info(f"Buscando en {source_brand}. Verifique la dirección seleccionada.")

with tab_masiva:
    st.subheader("Procesar lista de códigos")
    st.markdown("Suba un archivo Excel (.xlsx) con los códigos en la **primera columna**.")
    
    uploaded_file = st.file_uploader("Seleccionar archivo", type=["xlsx"])
    
    if uploaded_file:
        try:
            df_input = pd.read_excel(uploaded_file)
            if df_input.empty:
                st.warning("El archivo está vacío.")
            else:
                # Asumimos que los códigos están en la primera columna
                codes_col = df_input.columns[0]
                codes_list = df_input[codes_col].dropna().astype(str).tolist()
                
                st.write(f"Procesando {len(codes_list)} códigos...")
                
                results = []
                for c in codes_list:
                    m = find_equivalence(c, search_map, target_brand)
                    if m:
                        results.append({
                            "Código Ingresado": m["original"],
                            "Equivalente": m["equivalente"],
                            "Descripción": m["descripcion"]
                        })
                
                df_results = pd.DataFrame(results)
                st.dataframe(df_results, use_container_width=True)
                
                # Botón de descarga
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    df_results.to_excel(writer, index=False, sheet_name="Conversión")
                
                st.download_button(
                    label="📥 Descargar Resultados en Excel",
                    data=buffer.getvalue(),
                    file_name="resultados_conversion.xlsx",
                    mime="application/vnd.ms-excel"
                )
                
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

with tab_lista:
    st.subheader("Catálogo de Equivalencias")
    df_full = pd.DataFrame(DB_DATA)
    st.dataframe(df_full, use_container_width=True)
