import streamlit as st
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ---------- CONFIG GOOGLE SHEETS ----------
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_dict = json.loads(os.environ['GSPREAD_JSON'])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

sheet_name = "Inscripciones Futbol"

# ---------- FUNCIONES DE HOJAS ----------
def get_or_create_sheet(spreadsheet, title, rows=50, cols=2):
    try:
        return spreadsheet.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)
        return ws

# Abrir o crear Google Sheet
spreadsheet = client.open(sheet_name)
sheet_jugadores = get_or_create_sheet(spreadsheet, "Jugadores", rows=50, cols=1)
sheet_confirm = get_or_create_sheet(spreadsheet, "Confirmaciones", rows=10, cols=2)
sheet_equipos = get_or_create_sheet(spreadsheet, "Equipos", rows=20, cols=2)

# Inicializar confirmaciones si están vacías
if not sheet_confirm.get_all_values():
    sheet_confirm.update("A1:B1", [["Azul", "Blanco"]])
    sheet_confirm.update("A2:B2", [["❌", "❌"]])

# ---------- CONFIG STREAMLIT ----------
st.title("Pichanga Miércoles ⚽")
st.write("Máximo 20 jugadores por partido")

# ---------- PANEL ADMIN ----------
password = st.sidebar.text_input("Admin", type="password")
admin = False
if password == "#Mordecay123":
    admin = True
    st.sidebar.success("Admin activo ✅")
    
    # Reset completo
    if st.sidebar.button("Resetear lista y equipos"):
        sheet_jugadores.clear()
        sheet_equipos.clear()
        sheet_confirm.update("A2:B2", [["❌", "❌"]])
        st.sidebar.success("Listas reseteadas!")
    
    st.sidebar.markdown("---")
    
    # Borrar jugador específico
    nombre_borrar = st.sidebar.text_input("Borrar jugador")
    if st.sidebar.button("Eliminar jugador"):
        jugadores_actuales = [j[0] for j in sheet_jugadores.get_all_values()]
        if nombre_borrar in jugadores_actuales:
            idx = jugadores_actuales.index(nombre_borrar) + 1
            sheet_jugadores.delete_rows(idx)
            st.sidebar.success(f"Jugador '{nombre_borrar}' eliminado 🗑️")
        else:
            st.sidebar.warning("Jugador no encontrado")

    st.sidebar.markdown("---")
    # Designar capitanes
    jugadores_totales = [j[0] for j in sheet_jugadores.get_all_values()]
    if jugadores_totales:
        azul = st.sidebar.selectbox("Elegir capitán Azul", jugadores_totales)
        blanco = st.sidebar.selectbox("Elegir capitán Blanco", jugadores_totales)
        if st.sidebar.button("Asignar capitanes"):
            sheet_confirm.update("A2", "✅")  # azul confirmado
            sheet_confirm.update("B2", "✅")  # blanco confirmado
            sheet_equipos.update("A1", [azul])
            sheet_equipos.update("B1", [blanco])
            st.sidebar.success("Capitanes asignados!")

# ---------- PANEL CAPITANES ----------
st.sidebar.markdown("---")
st.sidebar.subheader("Zona Capitanes")

# Contraseña única
contraseña_capitan = "clave123"

nombre_cap = st.sidebar.text_input("Nombre del capitán")
clave_cap = st.sidebar.text_input("Contraseña", type="password")

cap_color = None
jugadores_disponibles = [j[0] for j in sheet_jugadores.get_all_values()]
if st.sidebar.button("Ingresar como capitán"):
    confirm_values = sheet_confirm.get_all_values()
    if nombre_cap in jugadores_disponibles and clave_cap == contraseña_capitan:
        if confirm_values[1][0] == "✅" and nombre_cap == sheet_equipos.acell("A1").value:
            cap_color = "Azul"
        elif confirm_values[1][1] == "✅" and nombre_cap == sheet_equipos.acell("B1").value:
            cap_color = "Blanco"
        if cap_color:
            st.session_state["capitan_color"] = cap_color
            st.sidebar.success(f"Bienvenido capitán {cap_color} ✅")
        else:
            st.sidebar.error("No eres el capitán asignado o aún no se asigna capitán.")
    else:
        st.sidebar.error("Nombre o contraseña incorrectos ❌")

# ---------- ELECCIÓN DE JUGADORES ----------
if "capitan_color" in st.session_state:
    st.subheader(f"Elección de jugadores - {st.session_state['capitan_color']}")
    
    # Inicializar equipos
    if "seleccion_azul" not in st.session_state:
        azul_name = sheet_equipos.acell("A1").value
        st.session_state["seleccion_azul"] = [azul_name] if azul_name else []
    if "seleccion_blanco" not in st.session_state:
        blanco_name = sheet_equipos.acell("B1").value
        st.session_state["seleccion_blanco"] = [blanco_name] if blanco_name else []
    
    st.write("Jugadores disponibles:", jugadores_disponibles)
    st.write("Equipo Azul:", st.session_state["seleccion_azul"])
    st.write("Equipo Blanco:", st.session_state["seleccion_blanco"])
    
    # Turno
    turno_color = st.radio("¿Quién empieza?", ["Azul", "Blanco"], key="turno_color")    
    nombre_elegido = st.text_input(f"{st.session_state['capitan_color']}, escribe el nombre del jugador a elegir", key="input_jugador")
    
    if st.button("Seleccionar jugador"):
        if nombre_elegido in jugadores_disponibles:
            if st.session_state["capitan_color"] == "Azul":
                st.session_state["seleccion_azul"].append(nombre_elegido)
                sheet_equipos.update_cell(len(st.session_state["seleccion_azul"]), 1, nombre_elegido)
            else:
                st.session_state["seleccion_blanco"].append(nombre_elegido)
                sheet_equipos.update_cell(len(st.session_state["seleccion_blanco"]), 2, nombre_elegido)
            jugadores_disponibles.remove(nombre_elegido)
            sheet_jugadores.clear()
            if jugadores_disponibles:
                sheet_jugadores.update("A1", [[j] for j in jugadores_disponibles])
        else:
            st.warning("Ese jugador no está disponible o fue escrito mal.")

# ---------- REGISTRO DE JUGADORES ----------
if admin or "capitan_color" not in st.session_state:
    if len(jugadores_disponibles) < 20:
        nombre = st.text_input("Ingresa tu nombre y posición opcional")
        if st.button("Anotarme"):
            if nombre.strip() == "":
                st.warning("Ingresa un nombre válido")
            elif nombre in jugadores_disponibles:
                st.warning("Ya estás inscrito!")
            else:
                sheet_jugadores.append_row([nombre, str(datetime.now())])
                jugadores_disponibles.append(nombre)
                st.success(f"{nombre} anotado")
    else:
        st.error("Se alcanzó el máximo de 20 jugadores")

# ---------- MOSTRAR JUGADORES ----------
if admin or "capitan_color" in st.session_state:
    st.subheader("Jugadores inscritos:")
    for i, j in enumerate(jugadores_disponibles, start=1):
        st.write(f"{i}. {j}")
