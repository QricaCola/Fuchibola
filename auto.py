import streamlit as st
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ---------- AUTOREFRESH ----------
st_autorefresh(interval=2000, key="fuchibola_refresh")  # refresca cada 2 seg

# ---------- CONFIG GOOGLE SHEETS ----------
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds_dict = json.loads(os.environ['GSPREAD_JSON'])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

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
        st.sidebar.success("Lista reseteada!")
    st.sidebar.markdown("---")
    nombre_borrar = st.sidebar.text_input("Ingresar el nombre a borrar")
    if st.sidebar.button("Borrar jugador"):
        jugadores = [j.strip().lower() for j in sheet.col_values(1)]
        nombre_borrar_limpio = nombre_borrar.strip().lower()
        if nombre_borrar_limpio in jugadores:
            index = jugadores.index(nombre_borrar_limpio) + 1
            sheet.delete_rows(index)
            st.sidebar.success(f"Jugador '{nombre_borrar}' eliminado correctamente 🗑️")
        else:
            st.sidebar.warning(f"No se encontró el jugador '{nombre_borrar}'.")

# ---------- PANEL CAPITANES ----------
st.sidebar.markdown("---")
st.sidebar.subheader("⚽ Zona Capitanes")

capitanes = ["Capitán 1", "Capitán 2"]
contraseña_capitan = "clave123"

nombre_cap = st.sidebar.text_input("Nombre del capitán")
clave_cap = st.sidebar.text_input("Contraseña", type="password")

# ---------- HOJAS DE GOOGLE SHEETS ----------
sheet_jugadores = client.open(sheet_name).worksheet("Jugadores")
sheet_confirm = client.open(sheet_name).worksheet("Confirmaciones")
sheet_equipos = client.open(sheet_name).worksheet("Equipos")

if st.sidebar.button("Ingresar como capitán"):
    if nombre_cap in capitanes and clave_cap == contraseña_capitan:
        st.session_state["capitan"] = nombre_cap
        st.sidebar.success(f"Bienvenido {nombre_cap}, esperando al otro capitán...")

        # Confirmación del capitán
        if nombre_cap == "Capitán 1":
            sheet_confirm.update_acell("A2", "✅")
        else:
            sheet_confirm.update_acell("B2", "✅")

        confirm = sheet_confirm.get_all_values()
        if confirm[1][0] == "✅" and confirm[1][1] == "✅":
            st.sidebar.success("✅ Ambos capitanes confirmados, inicia la elección!")
            st.session_state["eleccion_activa"] = True
        else:
            st.sidebar.info("Esperando al otro capitán...")
    else:
        st.sidebar.error("Nombre o contraseña incorrectos ❌")

# ---------- ELECCIÓN DE JUGADORES ----------
if st.session_state.get("eleccion_activa", False):
    st.subheader("🏆 Elección de jugadores")

    # Obtener jugadores disponibles
    jugadores = [j[0] for j in sheet_jugadores.get_all_values()]
    if "seleccion_blanco" not in st.session_state:
        st.session_state["seleccion_blanco"] = []
    if "seleccion_azul" not in st.session_state:
        st.session_state["seleccion_azul"] = []

    st.write("Jugadores disponibles:", jugadores)
    st.write("Equipo Blanco:", st.session_state["seleccion_blanco"])
    st.write("Equipo Azul:", st.session_state["seleccion_azul"])

    # Turnos
    turno = st.session_state.get("turno", 0)
    cap_turno = capitanes[turno % 2]
    st.write(f"Turno: {cap_turno}")

    nombre_elegido = st.text_input(f"{cap_turno}, escribe el nombre del jugador a elegir", key="eleccion_input")

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

            # Actualizar hoja de jugadores
            valores = [[j] for j in jugadores]
            sheet_jugadores.clear()
            if valores:
                sheet_jugadores.update("A1", valores)
        else:
            st.warning("Ese jugador no está disponible")

    if not jugadores:
        st.success("🎉 Elecciones finalizadas, buena suerte!")
        st.session_state["eleccion_activa"] = False

# ---------- REGISTRO DE JUGADORES ----------
if len(jugadores) < 20:
    nombre = st.text_input("Ingresa tu nombre y si deseas, añade la posición que te gusta")
    if st.button("Anotarme"):
        if nombre.strip() == "":
            st.warning("Ingresa un nombre válido")
        elif nombre in jugadores:
            st.warning("Ya estás inscrito!")
        else:
            sheet.append_row([nombre, str(datetime.now())])
            st.success(f"{nombre} anotado")
            jugadores.append(nombre)
else:
    st.error("Se alcanzó el máximo de 20 jugadores")

# ---------- MOSTRAR JUGADORES ----------
if jugadores:
    st.subheader("Jugadores inscritos:")
    for i, j in enumerate(jugadores, start=1):
        st.write(f"{i}. {j}")
