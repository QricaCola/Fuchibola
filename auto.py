import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Configuración de conexión
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file("credenciales.json", scopes=SCOPE)
client = gspread.authorize(creds)

sheet_name = "Fuchibola"
spreadsheet = client.open(sheet_name)

# --- Función segura para leer hoja ---
def safe_get_all_values(sheet):
    try:
        values = sheet.get_all_values()
        return values if values else []
    except Exception:
        return []

# --- Obtener o crear hojas ---
def get_or_create_worksheet(name, rows=50, cols=5):
    try:
        return spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=name, rows=str(rows), cols=str(cols))

sheet_jugadores = get_or_create_worksheet("Jugadores", 50, 1)
sheet_config = get_or_create_worksheet("Config", 10, 2)

# --- Inicializar configuración si está vacía ---
if not safe_get_all_values(sheet_config):
    sheet_config.update("A1:B1", [["Capitán ⚪", "Capitán 🔵"]])
    sheet_config.update("A2:B2", [["", ""]])

# --- Interfaz Streamlit ---
st.title("⚽ Fuchibola - Sistema de Inscripción y Equipos")

modo_admin = st.sidebar.checkbox("🔑 Modo administrador")

if modo_admin:
    st.subheader("Panel de administración")
    capitan_blanco = st.text_input("Capitán ⚪ (nombre exacto)")
    capitan_azul = st.text_input("Capitán 🔵 (nombre exacto)")

    if st.button("Guardar capitanes"):
        sheet_config.update("A2:B2", [[capitan_blanco, capitan_azul]])
        st.success(f"Capitanes actualizados: ⚪ {capitan_blanco or '-'} | 🔵 {capitan_azul or '-'}")

    st.write("Capitanes actuales:")
    config_values = safe_get_all_values(sheet_config)
    if len(config_values) >= 2:
        st.write(f"⚪ {config_values[1][0] or '-'} | 🔵 {config_values[1][1] or '-'}")

else:
    st.subheader("Inscripción de jugadores")
    nombre = st.text_input("Escribe tu nombre para inscribirte")

    if st.button("Inscribirme"):
        jugadores = safe_get_all_values(sheet_jugadores)
        jugadores_existentes = [fila[0] for fila in jugadores if fila]

        if nombre.strip() == "":
            st.warning("Por favor ingresa un nombre válido.")
        elif nombre in jugadores_existentes:
            st.error("Este nombre ya está inscrito ❌")
        else:
            sheet_jugadores.append_row([nombre])
            st.success(f"✅ {nombre} fue inscrito correctamente.")

    # Mostrar lista actualizada
    jugadores = safe_get_all_values(sheet_jugadores)
    if jugadores:
        st.write("**Jugadores inscritos:**")
        for j in jugadores:
            st.write(f"• {j[0]}")
    else:
        st.info("Aún no hay jugadores inscritos 🕓")
