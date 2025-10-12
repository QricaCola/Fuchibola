import streamlit as st
from streamlit_autorefresh import st_autorefresh
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

# Nombre del archivo de Google Sheets (ya existente)
sheet_name = "Inscripciones Futbol"
sheet = client.open(sheet_name).sheet1

# ---------- CONFIG STREAMLIT ----------
st.title("Pichanga Miércoles ⚽")
st.write("Máximo 20 jugadores por partido")

# ---------- PANEL DE ADMIN ----------
password = st.sidebar.text_input("Admin", type="password")
if password == "#Mordecay123":
    if st.sidebar.button("Resetear lista"):
        sheet.clear()
        st.sidebar.success("Lista reseteada ✅")

    st.sidebar.markdown("---")
    nombre_borrar = st.sidebar.text_input("Nombre a borrar")
    if st.sidebar.button("Borrar jugador"):
        jugadores = [j.strip().lower() for j in sheet.col_values(1)]
        nombre_borrar_limpio = nombre_borrar.strip().lower()
        if nombre_borrar_limpio in jugadores:
            index = jugadores.index(nombre_borrar_limpio) + 1
            sheet.delete_rows(index)
            st.sidebar.success(f"'{nombre_borrar}' eliminado 🗑️")
        else:
            st.sidebar.warning("No se encontró ese jugador")

# ---------- HOJAS AUXILIARES ----------
sheet_jugadores = client.open(sheet_name).worksheet("Jugadores")
sheet_confirm = client.open(sheet_name).worksheet("Confirmaciones")
sheet_equipos = client.open(sheet_name).worksheet("Equipos")

# ---------- PANEL CAPITANES ----------
st.sidebar.markdown("---")
st.sidebar.subheader("⚽ Zona Capitanes")

capitanes = ["Capitán 1", "Capitán 2"]
contraseña_capitan = "clave123"

nombre_cap = st.sidebar.text_input("Nombre del capitán")
clave_cap = st.sidebar.text_input("Contraseña", type="password")

if st.sidebar.button("Ingresar como capitán"):
    if nombre_cap in capitanes and clave_cap == contraseña_capitan:
        st.session_state["capitan"] = nombre_cap
        st.sidebar.success(f"Bienvenido {nombre_cap} 👋")

        # Marcar confirmación
        if nombre_cap == "Capitán 1":
            sheet_confirm.update_acell("A2", "✅")
        else:
            sheet_confirm.update_acell("B2", "✅")
    else:
        st.sidebar.error("Nombre o contraseña incorrectos ❌")

# ---------- SINCRONIZACIÓN EN TIEMPO REAL ----------
confirm = sheet_confirm.get_all_values()
cap1_ok = confirm[1][0] == "✅"
cap2_ok = confirm[1][1] == "✅"

if not (cap1_ok and cap2_ok):
    st.sidebar.info("Esperando al otro capitán...")
    st_autorefresh(interval=5000, key="refresh_capitanes")  # recarga cada 5s
else:
    st.sidebar.success("✅ Ambos capitanes confirmados, inicia la elección!")
    st.session_state["eleccion_activa"] = True

# ---------- ELECCIÓN DE JUGADORES ----------
if st.session_state.get("eleccion_activa", False):
    st.subheader("🏆 Elección de jugadores")

    jugadores = [j[0] for j in sheet_jugadores.get_all_values()]
    if "seleccion_blanco" not in st.session_state:
        st.session_state["seleccion_blanco"] = []
    if "seleccion_azul" not in st.session_state:
        st.session_state["seleccion_azul"] = []

    st.write("**Jugadores disponibles:**", jugadores)
    st.write("**Equipo Blanco:**", st.session_state["seleccion_blanco"])
    st.write("**Equipo Azul:**", st.session_state["seleccion_azul"])

    turno = st.session_state.get("turno", 0)
    cap_turno = capitanes[turno % 2]
    st.write(f"Turno actual: **{cap_turno}**")

    nombre_elegido = st.text_input(f"{cap_turno}, elige jugador:")

    if st.button("Seleccionar jugador"):
        if nombre_elegido in jugadores:
            if cap_turno == "Capitán 1":
                st.session_state["seleccion_blanco"].append(nombre_elegido)
                sheet_equipos.update_cell(len(st.session_state["seleccion_blanco"])+1, 1, nombre_elegido)
            else:
                st.session_state["seleccion_azul"].append(nombre_elegido)
                sheet_equipos.update_cell(len(st.session_state["seleccion_azul"])+1, 2, nombre_elegido)

            jugadores.remove(nombre_elegido)
            st.session_state["turno"] = turno + 1

            sheet_jugadores.clear()
            if jugadores:
                sheet_jugadores.update("A1", [[j] for j in jugadores])
        else:
            st.warning("Ese jugador no está disponible ⚠️")

    if not jugadores:
        st.success("🎉 Elecciones finalizadas, buena suerte!")
        st.session_state["eleccion_activa"] = False

# ---------- REGISTRO DE JUGADORES ----------
try:
    jugadores = sheet.col_values(1)
except:
    jugadores = []

if len(jugadores) < 20:
    nombre = st.text_input("Ingresa tu nombre (puedes incluir tu posición)")
    if st.button("Anotarme"):
        if nombre.strip() == "":
            st.warning("Ingresa un nombre válido")
        elif nombre in jugadores:
            st.warning("Ya estás inscrito!")
        else:
            sheet.append_row([nombre, str(datetime.now())])
            st.success(f"{nombre} anotado ✅")
else:
    st.error("Se alcanzó el máximo de 20 jugadores")

if jugadores:
    st.subheader("Jugadores inscritos:")
    for i, j in enumerate(jugadores, start=1):
        st.write(f"{i}. {j}")
