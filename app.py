import io
import re
from pathlib import Path

import pandas as pd
import streamlit as st


DATA_FILE = Path(__file__).with_name("equivalencias.csv")
DISPLAY_COLUMNS = ["mexweld", "cadweld", "descripcion"]


# Configuración de la página
st.set_page_config(
    page_title="Mexweld <-> Cadweld",
    page_icon="🔄",
    layout="wide",
)

# Estilos CSS personalizados para mejorar la apariencia
st.markdown(
    """
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
        background-color: #262730;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 10px;
        border: 1px solid #444;
    }

    .card-label {
        font-size: 0.85rem;
        color: #b0b0b0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }

    .card-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
        color: #ffffff;
    }

    .stTextInput input {
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def normalize_code(text):
    """Normaliza un código para búsquedas case-insensitive y sin espacios."""
    if pd.isna(text):
        return ""
    return re.sub(r"\s+", "", str(text)).upper()


def split_catalog_code(code):
    """
    Separa un código en familia base y sufijo físico.

    Patrón observado en los PDFs:
    - El sufijo físico es la parte útil del código después del primer guion.
    - Mexweld a veces inserta una clave numérica interna antes de ese guion
      (por ejemplo, CPVP5-5/8-4 o VV6-5/8R). Esa clave no forma parte del
      sufijo físico y se elimina para poder comparar ambas marcas.
    - Con esta normalización, CPVP5-5/8-4 y CPVP-5/8-4 apuntan a la misma fila.
    """
    norm_code = normalize_code(code)
    if not norm_code:
        return "", ""

    if "-" not in norm_code:
        return norm_code, ""

    prefix, rest = norm_code.split("-", 1)

    # Accesorios como M-PE o E-CEF no usan sufijo físico.
    if rest and rest[0].isalpha():
        return norm_code, ""

    base = re.sub(r"\d+$", "", prefix) or prefix
    return base, f"-{rest}"


@st.cache_data
def load_equivalences():
    """Carga y prepara las equivalencias desde equivalencias.csv."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"No existe {DATA_FILE.name}")

    df = pd.read_csv(DATA_FILE, dtype=str).fillna("")

    missing_columns = [column for column in DISPLAY_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(
            "equivalencias.csv no tiene las columnas requeridas: "
            + ", ".join(missing_columns)
        )

    df = df[DISPLAY_COLUMNS].copy()
    for column in DISPLAY_COLUMNS:
        df[column] = df[column].astype(str).str.strip()

    df = df[(df["mexweld"] != "") & (df["cadweld"] != "")]

    for brand in ("mexweld", "cadweld"):
        parsed = df[brand].map(split_catalog_code)
        df[f"{brand}_norm"] = df[brand].map(normalize_code)
        df[f"{brand}_base"] = parsed.map(lambda item: item[0])
        df[f"{brand}_suffix"] = parsed.map(lambda item: item[1])

    return df


def format_matches(matches_df, target_col, base_only=False):
    """Convierte coincidencias a una lista compacta para la interfaz."""
    if base_only:
        target_field = f"{target_col}_base"
    else:
        target_field = target_col

    compact = (
        matches_df[[target_field, "descripcion"]]
        .drop_duplicates()
        .rename(columns={target_field: "equivalente"})
        .sort_values(["equivalente", "descripcion"])
    )

    return compact.to_dict("records")


def find_equivalence(code, df_equivalences, source_col, target_col, target_brand):
    """Busca equivalencias exactas, por familia+sufijo y por familia base."""
    norm_code = normalize_code(code)
    if not norm_code:
        return None

    matches = df_equivalences[df_equivalences[f"{source_col}_norm"] == norm_code]
    base_only = False

    if matches.empty:
        base, suffix = split_catalog_code(norm_code)

        if suffix:
            matches = df_equivalences[
                (df_equivalences[f"{source_col}_base"] == base)
                & (df_equivalences[f"{source_col}_suffix"] == suffix)
            ]

        if matches.empty and base:
            matches = df_equivalences[df_equivalences[f"{source_col}_base"] == base]
            base_only = True

    if matches.empty:
        return {
            "original": code,
            "equivalente": "No encontrado",
            "marca_equivalente": "-",
            "descripcion": "Sin descripción",
            "encontrado": False,
            "multiple": False,
            "matches": [],
        }

    formatted_matches = format_matches(matches, target_col, base_only=base_only)
    multiple = len(formatted_matches) > 1
    first_match = formatted_matches[0]

    return {
        "original": code,
        "equivalente": (
            first_match["equivalente"] if not multiple else "Múltiples opciones"
        ),
        "marca_equivalente": target_brand,
        "descripcion": (
            first_match["descripcion"] if not multiple else "Coincidencias múltiples"
        ),
        "encontrado": True,
        "multiple": multiple,
        "matches": formatted_matches,
    }


try:
    df_equivalences = load_equivalences()
except Exception as exc:
    st.error(f"No se pudo cargar la base de equivalencias: {exc}")
    st.stop()


# --- INTERFAZ DE USUARIO ---

st.title("Convertidor Mexweld ↔ Cadweld")
st.markdown(
    "Herramienta rápida para consultar equivalencias de moldes y accesorios"
)

# Selector de dirección
direction = st.radio(
    "¿Qué desea hacer?",
    ["De Mexweld a Cadweld", "De Cadweld a Mexweld"],
    horizontal=True,
)

# Configuración según selección
if direction == "De Mexweld a Cadweld":
    source_col = "mexweld"
    target_col = "cadweld"
    source_brand = "Mexweld"
    target_brand = "Cadweld"
    example_code = "Ej: CCP-6"
else:
    source_col = "cadweld"
    target_col = "mexweld"
    source_brand = "Cadweld"
    target_brand = "Mexweld"
    example_code = "Ej: SS-6"

# Tabs para separar funcionalidad
tab_busqueda, tab_masiva, tab_lista = st.tabs(
    ["🔍 Búsqueda Rápida", "📂 Carga Masiva (Excel)", "📋 Ver Catálogo Completo"]
)

with tab_busqueda:
    st.subheader("Consultar un código individual")
    col1, col2 = st.columns([2, 1])
    with col1:
        code_input = st.text_input(
            f"Ingrese el código ({source_brand}):",
            placeholder=example_code,
        ).strip()

    if code_input:
        res = find_equivalence(
            code_input,
            df_equivalences,
            source_col=source_col,
            target_col=target_col,
            target_brand=target_brand,
        )

        if res and res["encontrado"]:
            if res["multiple"]:
                st.warning("Se encontraron varias equivalencias posibles.")
                st.dataframe(pd.DataFrame(res["matches"]), use_container_width=True)
            else:
                st.success("✅ Código encontrado.")
                st.markdown(
                    f"""
                    <div class="result-card">
                        <h3 style="margin: 0 0 15px 0; color: #ffff; font-size: 1.2rem; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                            {res['descripcion']}
                        </h3>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1;">
                                <div class="card-value" style="color: #329bfc;">{normalize_code(res['original'])}</div>
                            </div>
                            <div style="padding: 0 15px; font-size: 2rem; color: #ffff;">➜</div>
                            <div style="flex: 1; text-align: right;">
                                <div class="card-label">{res['marca_equivalente']}</div>
                                <div class="card-value" style="color: #28a745;">{res['equivalente']}</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
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
                codes_col = df_input.columns[0]
                codes_list = df_input[codes_col].dropna().astype(str).tolist()

                st.write(f"Procesando {len(codes_list)} códigos...")

                results = []
                for code in codes_list:
                    match = find_equivalence(
                        code,
                        df_equivalences,
                        source_col=source_col,
                        target_col=target_col,
                        target_brand=target_brand,
                    )

                    if match and match["encontrado"]:
                        equivalents = " | ".join(
                            item["equivalente"] for item in match["matches"]
                        )
                        descriptions = " | ".join(
                            dict.fromkeys(item["descripcion"] for item in match["matches"])
                        )
                    else:
                        equivalents = "No encontrado"
                        descriptions = "Sin descripción"

                    results.append(
                        {
                            "Código Ingresado": code,
                            "Equivalente": equivalents,
                            "Descripción": descriptions,
                        }
                    )

                df_results = pd.DataFrame(results)
                st.dataframe(df_results, use_container_width=True)

                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    df_results.to_excel(writer, index=False, sheet_name="Conversión")

                st.download_button(
                    label="📥 Descargar Resultados en Excel",
                    data=buffer.getvalue(),
                    file_name="resultados_conversion.xlsx",
                    mime="application/vnd.ms-excel",
                )

        except Exception as exc:
            st.error(f"Error al procesar el archivo: {exc}")

with tab_lista:
    st.subheader("Catálogo de Equivalencias")
    st.dataframe(
        df_equivalences[DISPLAY_COLUMNS].sort_values(DISPLAY_COLUMNS),
        use_container_width=True,
    )
