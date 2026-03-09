import streamlit as st
import pandas as pd

# 1. Configuración de Acceso (Diccionario de Usuarios)
# Puedes asignar la misma clave a todos o una diferente para cada uno
USUARIOS_PERMITIDOS = {
    "ggomez@rasa.com.uy": "neumaticos2026",
    "gciompi@rasa.com.uy": "neumaticos2026",
    "gviera@rasa.com.uy": "neumaticos2026",
    "dpereira@rasa.com.uy": "neumaticos2026",
    "admin": "admin123" # Opcional: mantener un admin
}

# URL de Google Sheets (Publicado como CSV)
URL_GSHEETS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQChb978H20pHIVMAwBBVGP4pJ99vWVLMLpsZOreAXg9dlSN5kUjrZ2s66_F2mi2Rq-BMviPqh8MVRX/pub?output=csv"

st.set_page_config(page_title="Stock RASA", page_icon="ico.ico", layout="wide")

# --- Función de Autenticación ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔑 Acceso al Sistema")
        col1, _ = st.columns([1, 1])
        with col1:
            usuario = st.text_input("Correo electrónico").lower().strip()
            clave = st.text_input("Contraseña", type="password")
            
            if st.button("Entrar"):
                # Verificamos si el usuario está en el diccionario y la clave coincide
                if usuario in USUARIOS_PERMITIDOS and USUARIOS_PERMITIDOS[usuario] == clave:
                    st.session_state.authenticated = True
                    st.session_state.user_email = usuario # Guardamos quién entró
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
        return False
    return True

# --- Función de Carga y Limpieza de Datos ---
@st.cache_data(ttl=600)
def cargar_datos():
    try:
        df = pd.read_csv(URL_GSHEETS)
        df.columns = df.columns.str.strip()
        
        # Columnas requeridas
        columnas_filtro = ['Código', 'Descripción', 'Precio USD', 'Stock Total']
        df = df[columnas_filtro]
        
        # Limpieza numérica
        columnas_numericas = ['Precio USD', 'Stock Total']
        for col in columnas_numericas:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Error al conectar o procesar los datos: {e}")
        return None

# --- Función de Estilo para Filas ---
def resaltar_filas(row):
    if row['Stock Total'] > 0:
        color = 'background-color: #025315; color: white;' # Verde oscuro
    else:
        color = 'background-color: #63000a; color: white;' # Rojo oscuro
    return [color] * len(row)

# --- Lógica Principal ---
if check_password():
    # Barra lateral
    st.sidebar.title("Opciones")
    st.sidebar.write(f"Usuario: **{st.session_state.user_email}**") # Muestra el usuario logueado
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.rerun()

    st.title("Buscador de Neumáticos")
    
    with st.spinner('Actualizando inventario...'):
        df_inventario = cargar_datos()

    if df_inventario is not None:
        busqueda = st.text_input("🔍 Buscar por Código o Descripción (ej: 215/75 o ONYX):").strip().upper()

        if busqueda:
            mask = (
                df_inventario['Código'].astype(str).str.contains(busqueda, case=False, na=False) |
                df_inventario['Descripción'].astype(str).str.contains(busqueda, case=False, na=False)
            )
            resultados = df_inventario[mask]

            if not resultados.empty:
                st.write(f"Se encontraron **{len(resultados)}** productos:")
                st.dataframe(
                    resultados.style.apply(resaltar_filas, axis=1)
                    .format({'Precio USD': '$ {:.2f}', 'Stock Total': '{:.0f}'}),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("No se encontraron resultados.")
        else:
            st.info("💡 Tip: Puedes buscar por medida, marca o código.")
            
            st.subheader("Últimos ingresos / Vista rápida:")
            st.dataframe(
                df_inventario.head(10).style.apply(resaltar_filas, axis=1)
                .format({'Precio USD': '$ {:.2f}', 'Stock Total': '{:.0f}'}),
                use_container_width=True, 
                hide_index=True
            )