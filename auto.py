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

# ---------- HOJA PRINCIPAL ----------
sheet_name = "Inscripciones Futbol"
try:
    sheet = client.open(sheet_name).sheet1
except gspread.SpreadsheetNotFound:
    sheet = client.create(sheet_name).sheet1

# ---------- HOJAS AUXILIARES ----------
def crear_hoja(nombre):
    try:
        return client.open(sheet_name).worksheet(nombre)
    except gspread.WorksheetNotFound:
        hoja = client.open(sheet_name).add_worksheet(title=nombre, rows="50", cols="2")
        return hoja

sheet_jugadores = crear_hoja("Jugadores")
sheet_confirm = crear_hoja("Confirmaciones")
sheet_equipos = crear_hoja("Equipos")

# ---------- STREAMLIT ----------
st.title("Pichanga Miércoles ⚽")
st.write("Máximo 20 jugadores por partido")

# ---------- PANEL ADMIN ----------
st.sidebar.subheader("🔧 Panel Admin")
admin_pass = st.sidebar.text_input("Contraseña Admin", type="password")
if admin_pass == "#Mordecay123":
    st.sidebar.markdown("**Designar Capitanes**")
    cap_azul = st.sidebar.text_input("Nombre Capitán Azul")
    cap_blanco = st.sidebar.text_input("Nombre Capitán Blanco")
    if st.sidebar.button("Guardar Capitanes"):
        st.session_state["cap_azul"] = cap_azul.strip()
        st.session_state["cap_blanco"] = cap_blanco.strip()
        st.sidebar.success("Capitanes actualizados ✅")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Resetear lista completa"):
        sheet_jugadores.clear()
        sheet_equipos.clear()
        st.sidebar.success("Listas reseteadas! 🗑️")
    
    nombre_borrar = st.sidebar.text_input("Borrar jugador específico")
    if st.sidebar.button("Borrar jugador"):
        jugadores = [j[0] for j in sheet_jugadores.get_all_values()]
        nombre_borrar_limpio = nombre_borrar.strip()
        if nombre_borrar_limpio in jugadores:
            idx = jugadores.index(nombre_borrar_limpio) + 1
            sheet_jugadores.delete_rows(idx)
            st.sidebar.success(f"Jugador '{nombre_borrar_limpio}' eliminado 🗑️")
        else:
            st.sidebar.warning(f"No se encontró '{nombre_borrar_limpio}'")

# ---------- PANEL CAPITANES ----------
st.sidebar.markdown("---")
st.sidebar.subheader("⚽ Zona Capitanes")

cap_pass = st.sidebar.text_input("Contraseña Capitanes", type="password")
cap_name = st.sidebar.text_input("Tu nombre de capitán")
if st.sidebar.button("Ingresar"):
    if cap_pass == "clave123":
        azul = st.session_state.get("cap_azul", "")
        blanco = st.session_state.get("cap_blanco", "")
        if cap_name == azul:
            st.session_state["color"] = "Azul"
            st.session_state["capitan"] = cap_name
            st.sidebar.success(f"Bienvenido {cap_name} (Azul)")
        elif cap_name == blanco:
            st.session_state["color"] = "Blanco"
            st.session_state["capitan"] = cap_name
            st.sidebar.success(f"Bienvenido {cap_name} (Blanco)")
        else:
            st.sidebar.error("No eres un capitán asignado ❌")
    else:
        st.sidebar.error("Contraseña incorrecta ❌")

# ---------- ELECCIÓN DE JUGADORES ----------
if st.session_state.get("capitan"):
    st.subheader("🏆 Elección de jugadores")
    
    # Lista disponible
    jugadores = [j[0] for j in sheet_jugadores.get_all_values()]
    if "equipo_azul" not in st.session_state:
        st.session_state["equipo_azul"] = []
    if "equipo_blanco" not in st.session_state:
        st.session_state["equipo_blanco"] = []
    
    st.write("Jugadores disponibles:", jugadores)
    st.write("Equipo Azul:", st.session_state["equipo_azul"])
    st.write("Equipo Blanco:", st.session_state["equipo_blanco"])
    
    # Turno por color
    turno = st.session_state.get("turno", "Azul")  # empieza Azul por defecto
    st.write(f"Turno: {turno}")
    
    nombre_elegido = st.text_input(f"{turno}, escribe el nombre del jugador a elegir", key="eleccion_input")
    if st.button("Seleccionar jugador"):
        if nombre_elegido in jugadores:
            if turno == "Azul":
                st.session_state["equipo_azul"].append(nombre_elegido)
                sheet_equipos.update_cell(len(st.session_state["equipo_azul"])+1, 1, nombre_elegido)
                turno = "Blanco"
            else:
                st.session_state["equipo_blanco"].append(nombre_elegido)
                sheet_equipos.update_cell(len(st.session_state["equipo_blanco"])+1, 2, nombre_elegido)
                turno = "Azul"
            jugadores.remove(nombre_elegido)
            st.session_state["turno"] = turno
            # actualizar hoja jugadores
            sheet_jugadores.clear()
            if jugadores:
                sheet_jugadores.update("A1", [[j] for j in jugadores])
        else:
            st.warning("Ese jugador no está disponible, escribe otro nombre")
    
    if not jugadores:
        st.success("🎉 Elecciones finalizadas, buena suerte!")
        st.session_state["turno"] = None

# ---------- REGISTRO DE JUGADORES ----------
if len([j[0] for j in sheet_jugadores.get_all_values()]) < 20:
    nombre = st.text_input("Ingresa tu nombre (y posición si deseas)")
    if st.button("Anotarme"):
        nombre = nombre.strip()
        if nombre == "":
            st.warning("Ingresa un nombre válido")
        else:
            jugadores = [j[0] for j in sheet_jugadores.get_all_values()]
            if nombre in jugadores:
                st.warning("Ya estás inscrito!")
            else:
                sheet_jugadores.append_row([nombre, str(datetime.now())])
                st.success(f"{nombre} anotado")
else:
    st.error("Se alcanzó el máximo de 20 jugadores")

# ---------- MOSTRAR JUGADORES ----------
jugadores = [j[0] for j in sheet_jugadores.get_all_values()]
if jugadores:
    st.subheader("Jugadores inscritos:")
    for i, j in enumerate(jugadores, start=1):
        st.write(f"{i}. {j}")
