import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- Conexión con Google Sheets ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file("credenciales.json", scopes=SCOPE)
client = gspread.authorize(creds)

sheet_name = "Fuchibola"
spreadsheet = client.open(sheet_name)

# --- Función para acceder a una hoja o crearla ---
def get_or_create_worksheet(name, rows=50, cols=5):
    try:
        return spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=name, rows=str(rows), cols=str(cols))

# --- Función segura para leer datos ---
def safe_get_all_values(sheet):
    try:
        values = sheet.get_all_values()
        return values if values else []
    except Exception:
        return []

# --- Obtener hojas necesarias ---
sheet_jugadores = get_or_create_worksheet("Jugadores", 50, 1)
sheet_config = get_or_create_worksheet("Config", 10, 2)
sheet_equipos = get_or_create_worksheet("Equipos", 50, 2)

# --- Inicializar configuración si está vacía ---
if not safe_get_all_values(sheet_config):
    sheet_config.update("A1:B1", [["Capitán ⚪", "Capitán 🔵"]])
    sheet_config.update("A2:B2", [["", ""]])
    sheet_config.update("A4", [["Turno actual: ⚪"]])

# --- Interfaz Streamlit ---
st.title("⚽ Fuchibola - Sistema de Equipos")

modo_admin = st.sidebar.checkbox("🔑 Modo administrador")

# --- Panel admin ---
if modo_admin:
    st.subheader("Panel de administración")

    capitan_blanco = st.text_input("Capitán ⚪ (nombre exacto)")
    capitan_azul = st.text_input("Capitán 🔵 (nombre exacto)")

    if st.button("Guardar capitanes"):
        sheet_config.update("A2:B2", [[capitan_blanco, capitan_azul]])
        sheet_config.update("A4", [["Turno actual: ⚪"]])
        st.success("Capitanes y turno inicial configurados ✅")

    config_values = safe_get_all_values(sheet_config)
    if len(config_values) >= 2:
        st.write(f"**Capitanes actuales:** ⚪ {config_values[1][0] or '-'} | 🔵 {config_values[1][1] or '-'}")

    if st.button("Reiniciar equipos"):
        sheet_equipos.clear()
        sheet_equipos.update("A1:B1", [["Equipo ⚪", "Equipo 🔵"]])
        sheet_config.update("A4", [["Turno actual: ⚪"]])
        st.warning("Se reiniciaron los equipos y el turno 🔁")

# --- Inscripción de jugadores ---
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

    jugadores = safe_get_all_values(sheet_jugadores)
    if jugadores:
        st.write("**Jugadores inscritos:**")
        for j in jugadores:
            st.write(f"• {j[0]}")
    else:
        st.info("Aún no hay jugadores inscritos 🕓")

# --- Sistema de elección por turnos ---
st.divider()
st.subheader("⚙️ Elección por turnos")

config = safe_get_all_values(sheet_config)
equipos = safe_get_all_values(sheet_equipos)
jugadores = [fila[0] for fila in safe_get_all_values(sheet_jugadores) if fila]

if len(config) >= 2:
    capitan_blanco, capitan_azul = config[1][0], config[1][1]
    turno_actual = "⚪" if "⚪" in config[3][0] else "🔵"

    st.write(f"**Turno actual:** {turno_actual}")
    nombre_turno = capitan_blanco if turno_actual == "⚪" else capitan_azul
    st.info(f"Es el turno de **{nombre_turno or '---'}** ({turno_actual}) para elegir un jugador.")

    jugador_elegido = st.text_input("Jugador elegido (nombre exacto)")
    if st.button("Elegir jugador"):
        if jugador_elegido not in jugadores:
            st.error("❌ Ese jugador no está inscrito o ya fue elegido.")
        else:
            # Registrar jugador en su equipo
            col = 1 if turno_actual == "⚪" else 2
            sheet_equipos.append_row([jugador_elegido] if col == 1 else ["", jugador_elegido])

            # Eliminar jugador de lista principal
            all_vals = safe_get_all_values(sheet_jugadores)
            nuevos_jugadores = [j for j in all_vals if j and j[0] != jugador_elegido]
            sheet_jugadores.clear()
            if nuevos_jugadores:
                sheet_jugadores.update("A1", nuevos_jugadores)

            # Cambiar turno
            nuevo_turno = "🔵" if turno_actual == "⚪" else "⚪"
            sheet_config.update("A4", [[f"Turno actual: {nuevo_turno}"]])

            st.success(f"✅ {jugador_elegido} fue elegido para el equipo {turno_actual}")
            st.rerun()

# --- Mostrar equipos ---
st.divider()
st.subheader("📋 Equipos formados")

equipos = safe_get_all_values(sheet_equipos)
if len(equipos) > 1:
    eq_blancos = [fila[0] for fila in equipos[1:] if fila and fila[0]]
    eq_azules = [fila[1] for fila in equipos[1:] if len(fila) > 1 and fila[1]]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ⚪ Equipo Blanco")
        if eq_blancos:
            for j in eq_blancos:
                st.write(f"• {j}")
        else:
            st.info("Sin jugadores aún")

    with col2:
        st.markdown("### 🔵 Equipo Azul")
        if eq_azules:
            for j in eq_azules:
                st.write(f"• {j}")
        else:
            st.info("Sin jugadores aún")
else:
    st.info("Aún no hay equipos creados.")
