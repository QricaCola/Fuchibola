import streamlit as st
import json
import os
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from gspread.exceptions import APIError, WorksheetNotFound

# ---------------- CONFIG (cambia si quieres) ----------------
SPREADSHEET_NAME = "Inscripciones Futbol"
ADMIN_PASSWORD = "#Mordecay123"   # contraseña admin
CAPTAIN_PASSWORD = "clave123"     # contraseña única para capitanes
MAX_PLAYERS = 20

# ---------------- Google Sheets - conexión segura ----------------
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_dict = json.loads(os.environ['GSPREAD_JSON'])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

def open_spreadsheet_safe(name, retries=3, delay=1):
    for i in range(retries):
        try:
            return client.open(name)
        except APIError as e:
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise

spreadsheet = open_spreadsheet_safe(SPREADSHEET_NAME)

def open_or_create(title, rows=50, cols=2):
    try:
        return spreadsheet.worksheet(title)
    except WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows=str(rows), cols=str(cols))

# Hojas usadas
sheet_players = open_or_create("Jugadores", rows=200, cols=2)   # A: nombre, B: timestamp
sheet_teams = open_or_create("Equipos", rows=200, cols=2)       # A: Azul, B: Blanco
sheet_turns = open_or_create("Turnos", rows=5, cols=2)         # A1: current turn ("Azul"/"Blanco")
sheet_config = open_or_create("Config", rows=10, cols=3)       # A1: cap_azul, B1: cap_blanco, C1: start

# Inicializar config / turns si vacío
if not sheet_config.get_all_values():
    sheet_config.update("A1:C1", [["", "", "Azul"]])
if not sheet_turns.get_all_values():
    sheet_turns.update("A1", "Azul")

# ---------------- helpers seguros ----------------
def rows(sheet):
    return sheet.get_all_values() or []

def player_list():
    filas = rows(sheet_players)
    return [r[0].strip() for r in filas if len(r) > 0 and r[0].strip()]

def write_players_list(lista):
    sheet_players.clear()
    if lista:
        sheet_players.update("A1", [[p] for p in lista])

def read_config():
    vals = rows(sheet_config)
    if vals and len(vals) >= 1:
        row = vals[0]
        cap_azul = row[0] if len(row) > 0 else ""
        cap_blanco = row[1] if len(row) > 1 else ""
        start = row[2] if len(row) > 2 else "Azul"
    else:
        cap_azul, cap_blanco, start = "", "", "Azul"
    return cap_azul, cap_blanco, start

def read_turn():
    vals = rows(sheet_turns)
    if vals and len(vals) >= 1 and vals[0]:
        return vals[0][0]
    # default
    return "Azul"

def set_turn(color):
    sheet_turns.update("A1", color)

def read_teams():
    vals = rows(sheet_teams)
    header = vals[0] if vals else ["Azul","Blanco"]
    filas = vals[1:] if len(vals) > 1 else []
    col_azul = [r[0] for r in filas if len(r) >= 1 and r[0].strip() != ""]
    col_blanco = [r[1] for r in filas if len(r) >= 2 and r[1].strip() != ""]
    return col_azul, col_blanco

def write_teams(azul, blanco):
    # escribe encabezado y filas combinadas
    sheet_teams.clear()
    sheet_teams.update("A1:B1", [["Azul", "Blanco"]])
    maxlen = max(len(azul), len(blanco))
    filas = []
    for i in range(maxlen):
        a = azul[i] if i < len(azul) else ""
        b = blanco[i] if i < len(blanco) else ""
        filas.append([a, b])
    if filas:
        sheet_teams.update("A2", filas)

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Pichanga - Elección", layout="wide")
st.title("Pichanga Miércoles ⚽")
st.write("Máximo de jugadores por partido:", MAX_PLAYERS)

# --- Sidebar: Admin + Capitanes (todo en sidebar) ---
with st.sidebar:
    st.header("Panel lateral")

    # ---- Admin ----
    st.subheader("🔧 Admin")
    admin_pass = st.text_input("Contraseña Admin", type="password", key="admin_pass")
    admin_mode = (admin_pass == ADMIN_PASSWORD)
    if admin_mode:
        st.success("Admin activo")
        # Mostrar capitanes actuales
        cap_azul_cfg, cap_blanco_cfg, start_cfg = read_config()
        st.markdown("**Capitán Azul:** " + (cap_azul_cfg or "_no asignado_"))
        st.markdown("**Capitán Blanco:** " + (cap_blanco_cfg or "_no asignado_"))
        st.markdown("**Equipo que inicia:** " + (start_cfg or "Azul"))
        st.markdown("---")

        # Asignar capitanes (select si hay jugadores, o texto si no hay)
        jugadores_disp = player_list()
        if jugadores_disp:
            sel_azul = st.selectbox("Seleccionar Capitán Azul", [""] + jugadores_disp, key="sel_azul")
            sel_blanco = st.selectbox("Seleccionar Capitán Blanco", [""] + jugadores_disp, key="sel_blanco")
        else:
            sel_azul = st.text_input("Capitán Azul (escribe nombre)", key="txt_azul")
            sel_blanco = st.text_input("Capitán Blanco (escribe nombre)", key="txt_blanco")
        start_choice = st.selectbox("Equipo que inicia", ["Azul", "Blanco"], index=0 if start_cfg!="Blanco" else 1)
        if st.button("Guardar configuración"):
            # decidir nombres reales
            new_azul = sel_azul if jugadores_disp else sel_azul or ""
            new_blanco = sel_blanco if jugadores_disp else sel_blanco or ""
            # si ambos estaban vacíos, no sobreescribir si campos vacíos
            sheet_config.clear()
            sheet_config.update("A1:C1", [[new_azul, new_blanco, start_choice]])
            # set initial turn
            set_turn(start_choice)
            st.success("Configuración guardada")
            cap_azul_cfg, cap_blanco_cfg, start_cfg = read_config()
        st.markdown("---")
        # Reset y borrados
        if st.button("Resetear todo (borrar listas y equipos)"):
            sheet_players = sheet_players = sheet_players = None  # no-op visual safety
            sheet_players = open_or_create("Jugadores", rows="200", cols="2")
            sheet_players.clear()
            sheet_teams.clear()
            sheet_config.clear()
            sheet_config.update("A1:C1", [["", "", "Azul"]])
            set_turn("Azul")
            st.success("Reseteado completado")
        # Borrar jugador
        borrar_nombre = st.text_input("Borrar jugador por nombre", key="del_name")
        if st.button("Borrar jugador seleccionado"):
            jugadores_now = player_list()
            if borrar_nombre.strip() in jugadores_now:
                idx = jugadores_now.index(borrar_nombre.strip()) + 1
                sheet_players.delete_rows(idx)
                st.success(f"Jugador '{borrar_nombre.strip()}' borrado")
            else:
                st.warning("Nombre no encontrado")

    else:
        st.info("Introduce contraseña admin para ver opciones")

    st.markdown("---")

    # ---- Capitanes ----
    st.subheader("⚽ Capitanes (ingreso)")
    cap_name = st.text_input("Tu nombre (capitán)", key="sidebar_cap_name")
    cap_pass = st.text_input("Contraseña capitanes", type="password", key="sidebar_cap_pass")
    if st.button("Ingresar como capitán"):
        cfg_az, cfg_blanco, cfg_start = read_config()
        if cap_pass == CAPTAIN_PASSWORD and cap_name.strip() in [cfg_az, cfg_blanco]:
            # login ok
            st.success(f"Bienvenido {cap_name.strip()}")
            st.session_state["capitan_logged"] = True
            st.session_state["capitan_name"] = cap_name.strip()
            # determine color
            if cap_name.strip() == cfg_az:
                st.session_state["capitan_color"] = "Azul"
            else:
                st.session_state["capitan_color"] = "Blanco"
        else:
            st.error("Credenciales incorrectas o no eres capitán asignado")

    st.markdown("---")
    st.info("Usuarios normales: anotarse abajo (en la página principal)")

# ---------------- Main columns: left teams / right actions ----------------
col_left, col_right = st.columns([2, 1])

# Left: mostrar equipos y lista inscritos (visible para admin & captains; players see only list)
with col_left:
    st.subheader("Equipos")
    azul_team, blanco_team = read_teams()
    st.markdown("**Equipo Azul 🔵**")
    if azul_team:
        for i, p in enumerate(azul_team, start=1):
            st.write(f"{i}. {p}")
    else:
        st.write("_Vacío_")

    st.markdown("**Equipo Blanco ⚪**")
    if blanco_team:
        for i, p in enumerate(blanco_team, start=1):
            st.write(f"{i}. {p}")
    else:
        st.write("_Vacío_")

    st.write("---")
    # Mostrar lista general de inscritos para todos
    st.subheader("Jugadores inscritos")
    jugadores_now = player_list()
    if jugadores_now:
        for i, p in enumerate(jugadores_now, start=1):
            st.write(f"{i}. {p}")
    else:
        st.write("_No hay jugadores todavía_")

# Right: acciones (registro o elección según rol)
with col_right:
    # ---------------- Registro general (jugadores) ----------------
    st.subheader("Inscripción")
    filas = rows(sheet_players)
    jugadores_now = [r[0].strip() for r in filas if len(r) > 0 and r[0].strip()]
    # usar formulario para evitar problemas
    with st.form("form_registro"):
        nombre_new = st.text_input("Tu nombre (y posición opcional)", key="form_name")
        submitted = st.form_submit_button("Anotarme")
        if submitted:
            nombre_clean = nombre_new.strip()
            if not nombre_clean:
                st.warning("Ingresa un nombre válido")
            elif nombre_clean in jugadores_now:
                st.warning("Ese nombre ya está inscrito")
            elif len(jugadores_now) >= MAX_PLAYERS:
                st.error("Se alcanzó el máximo de jugadores")
            else:
                sheet_players.append_row([nombre_clean, str(datetime.now())])
                st.success(f"{nombre_clean} anotado ✅")
                jugadores_now.append(nombre_clean)

    st.markdown("---")

    # ---------------- Elección por capitanes (si están logueados) ----------------
    cap_logged = st.session_state.get("capitan_logged", False)
    cap_name_logged = st.session_state.get("capitan_name", "")
    cap_color_logged = st.session_state.get("capitan_color", "")

    # Mostrar turno actual (desde sheet_turns)
    turno_actual = read_turn()
    st.markdown(f"**Turno actual:** {turno_actual if turno_actual else 'Azul'}")

    # Solo admin o capitan logueado pueden elegir
    if admin_mode or cap_logged:
        st.subheader("Elección (solo admin/capitán)")
        # refrescar variables
        jugadores_now = player_list()
        azul_team, blanco_team = read_teams()
        cfg_az, cfg_bl, cfg_start = read_config()

        # mostrar capitanes asignados en panel principal
        st.markdown(f"**Capitán Azul:** {cfg_az or '_no asignado_'}")
        st.markdown(f"**Capitán Blanco:** {cfg_bl or '_no asignado_'}")
        st.markdown("---")

        # Si admin -> puede forzar cambiar turno o asignar capitanes desde aquí también
        if admin_mode:
            if st.button("Forzar siguiente turno"):
                nxt = "Blanco" if turno_actual == "Azul" else "Azul"
                set_turn(nxt)
                st.info(f"Turno forzado a {nxt}")

        # Si el usuario es capitán: comprobar si es su turno
        if cap_logged:
            # Denegar si el nombre no coincide con config (por seguridad)
            if cap_name_logged not in [cfg_az, cfg_bl]:
                st.error("Tu nombre ya no coincide con los capitanes asignados.")
            else:
                # ¿es su turno?
                if cap_color_logged != turno_actual and not admin_mode:
                    st.info("No es tu turno. Espera a que el otro capitán elija o recarga la página.")
                else:
                    # elección del jugador
                    with st.form("form_eleccion"):
                        st.write("Jugadores disponibles:")
                        if jugadores_now:
                            for p in jugadores_now:
                                st.write("- " + p)
                        else:
                            st.write("_No hay jugadores disponibles_")

                        pick = st.text_input("Escribe exactamente el nombre del jugador que eliges")
                        pick_submit = st.form_submit_button("Seleccionar jugador")
                        if pick_submit:
                            pick_clean = pick.strip()
                            if not pick_clean:
                                st.warning("Escribe un nombre válido")
                            elif pick_clean not in jugadores_now:
                                st.warning("Ese jugador no está disponible")
                            else:
                                # agregar a equipo correcto
                                if cap_color_logged == "Azul":
                                    azul_team.append(pick_clean)
                                else:
                                    blanco_team.append(pick_clean)
                                write_teams(azul_team, blanco_team)
                                # remover jugador de lista
                                jugadores_now.remove(pick_clean)
                                write_players_list(jugadores_now)
                                # cambiar turno
                                nxt = "Blanco" if turno_actual == "Azul" else "Azul"
                                set_turn(nxt)
                                st.success(f"{pick_clean} agregado a {cap_color_logged}")
                                st.info(f"Turno cambiado a {nxt}")

    else:
        st.info("Solo capitanes y admin pueden ver/gestionar la elección de equipos.")

# ---------------- Footer: mensaje final si no quedan jugadores ----------------
remaining = player_list()
if not remaining:
    # si ya hay jugadores en equipos, significa eleccion terminada
    azul_team, blanco_team = read_teams()
    if azul_team or blanco_team:
        st.success("🎉 Elecciones finalizadas, buena suerte!")
