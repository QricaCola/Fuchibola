import streamlit as st
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ---------- CONFIG GOOGLE SHEETS ----------
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds_dict = json.loads(os.environ['GSPREAD_JSON'])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# ---------- SPREADSHEET ----------
sheet_name = "Inscripciones Futbol"
spreadsheet = client.open(sheet_name)

# Función para abrir o crear hoja
def open_or_create(title, rows="50", cols="2"):
    try:
        return spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)

sheet_jugadores = open_or_create("Jugadores", rows="50", cols="1")
sheet_confirm = open_or_create("Confirmaciones", rows="10", cols="2")
sheet_equipos = open_or_create("Equipos", rows="20", cols="2")

# ---------- CONFIG STREAMLIT ----------
st.title("Pichanga Miércoles ⚽")
st.write("Máximo 20 jugadores por partido")

# ---------- PANEL ADMIN ----------
password = st.sidebar.text_input("Admin", type="password")
admin_activo = False
if password == "#Mordecay123":
    admin_activo = True
    st.sidebar.success("Modo Admin activo ✅")

    # Resetear lista completa
    if st.sidebar.button("Resetear lista"):
        sheet_jugadores.clear()
        sheet_confirm.clear()
        sheet_confirm.update("A1:B1", [["Azul", "Blanco"]])
        sheet_confirm.update("A2:B2", [["❌","❌"]])
        sheet_equipos.clear()
        st.sidebar.success("Todas las hojas reseteadas!")

    st.sidebar.markdown("---")
    # Borrar jugador específico
    nombre_borrar = st.sidebar.text_input("Ingresar el nombre a borrar")
    if st.sidebar.button("Borrar jugador"):
        jugadores = [j.strip() for j in sheet_jugadores.col_values(1)]
        nombre_borrar_limpio = nombre_borrar.strip()
        if nombre_borrar_limpio in jugadores:
            index = jugadores.index(nombre_borrar_limpio) + 1
            sheet_jugadores.delete_rows(index)
            st.sidebar.success(f"Jugador '{nombre_borrar}' eliminado 🗑️")
        else:
            st.sidebar.warning(f"No se encontró '{nombre_borrar}'.")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Designar Capitanes")
    cap_azul = st.sidebar.text_input("Nombre Capitán Azul")
    cap_blanco = st.sidebar.text_input("Nombre Capitán Blanco")
    if st.sidebar.button("Guardar Capitanes"):
        sheet_confirm.update("A1:B1", [[cap_azul, cap_blanco]])
        sheet_confirm.update("A2:B2", [["❌","❌"]])
        st.sidebar.success("Capitanes asignados ✅")

# ---------- ELECCIÓN DE CAPITANES ----------
colores = ["Azul", "Blanco"]
color_inicio = st.selectbox("¿Qué equipo inicia la elección?", colores)

confirm_values = sheet_confirm.get_all_values()
if len(confirm_values) < 2:
    # Inicializar confirmaciones si vacío
    sheet_confirm.update("A1:B1", [["Azul", "Blanco"]])
    sheet_confirm.update("A2:B2", [["❌","❌"]])
    confirm_values = sheet_confirm.get_all_values()

cap_azul = confirm_values[0][0] if len(confirm_values) > 0 else ""
cap_blanco = confirm_values[0][1] if len(confirm_values) > 0 else ""

# ---------- LOGIN CAPITAN ----------
nombre_cap = st.text_input("Ingresa tu nombre de capitán")
clave_cap = st.text_input("Contraseña única de capitán", type="password")
if st.button("Ingresar como capitán"):
    if clave_cap == "#Mordecay123" and nombre_cap in [cap_azul, cap_blanco]:
        st.success(f"Bienvenido {nombre_cap}")
        st.session_state["capitan"] = nombre_cap

        # Actualizar confirmación
        if nombre_cap == cap_azul:
            sheet_confirm.update_acell("A2", "✅")
        else:
            sheet_confirm.update_acell("B2", "✅")

# ---------- ELECCIÓN DE JUGADORES ----------
if "capitan" in st.session_state:
    jugadores_disponibles = [j[0] for j in sheet_jugadores.get_all_values()] if sheet_jugadores.get_all_values() else []
    if "seleccion_azul" not in st.session_state:
        st.session_state["seleccion_azul"] = [cap_azul] if cap_azul else []
    if "seleccion_blanco" not in st.session_state:
        st.session_state["seleccion_blanco"] = [cap_blanco] if cap_blanco else []

    st.subheader("🏆 Elección de jugadores")
    st.write("Jugadores disponibles:", jugadores_disponibles)
    st.write("Equipo Azul:", st.session_state["seleccion_azul"])
    st.write("Equipo Blanco:", st.session_state["seleccion_blanco"])

    # Turno dinámico según color_inicio
    turno = st.session_state.get("turno", 0)
    cap_turno = cap_azul if (color_inicio == "Azul" and turno % 2 == 0) or (color_inicio == "Blanco" and turno % 2 == 1) else cap_blanco
    st.write(f"Turno de: {cap_turno}")

    nombre_elegido = st.text_input(f"{cap_turno}, escribe el nombre del jugador a elegir", key="input_eleccion")
    if st.button("Seleccionar jugador"):
        if nombre_elegido in jugadores_disponibles:
            if cap_turno == cap_azul:
                st.session_state["seleccion_azul"].append(nombre_elegido)
                sheet_equipos.update_cell(len(st.session_state["seleccion_azul"]),1,nombre_elegido)
            else:
                st.session_state["seleccion_blanco"].append(nombre_elegido)
                sheet_equipos.update_cell(len(st.session_state["seleccion_blanco"]),2,nombre_elegido)
            jugadores_disponibles.remove(nombre_elegido)
            st.session_state["turno"] = turno + 1

            # Actualizar hoja de jugadores
            valores = [[j] for j in jugadores_disponibles]
            sheet_jugadores.clear()
            if valores:
                sheet_jugadores.update("A1", valores)
        else:
            st.warning("Ese jugador no está disponible o fue escrito incorrectamente.")

# ---------- REGISTRO GENERAL ----------
if len(sheet_jugadores.get_all_values() or []) < 20:
    nombre = st.text_input("Ingresa tu nombre para anotarte")
    if st.button("Anotarme"):
        if nombre.strip() == "":
            st.warning("Ingresa un nombre válido")
        elif nombre in [j[0] for j in sheet_jugadores.get_all_values()]:
            st.warning("Ya estás inscrito!")
        else:
            sheet_jugadores.append_row([nombre, str(datetime.now())])
            st.success(f"{nombre} anotado")
else:
    st.error("Se alcanzó el máximo de 20 jugadores")

# ---------- MOSTRAR JUGADORES ----------
jugadores = [j[0] for j in sheet_jugadores.get_all_values()] if sheet_jugadores.get_all_values() else []
if jugadores:
    st.subheader("Jugadores inscritos:")
    for i,j in enumerate(jugadores,1):
        st.write(f"{i}. {j}")
