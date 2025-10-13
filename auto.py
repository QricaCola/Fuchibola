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

sheet_name = "Inscripciones Futbol"

# ---------- FUNCIONES AUXILIARES ----------
def obtener_hoja(nombre_hoja, filas=50, cols=2):
    try:
        hoja = client.open(sheet_name).worksheet(nombre_hoja)
    except gspread.exceptions.WorksheetNotFound:
        hoja = client.open(sheet_name).add_worksheet(title=nombre_hoja, rows=str(filas), cols=str(cols))
    return hoja

# ---------- HOJAS ----------
sheet_jugadores = obtener_hoja("Jugadores", filas=50, cols=2)
sheet_confirm = obtener_hoja("Confirmaciones", filas=10, cols=2)
sheet_equipos = obtener_hoja("Equipos", filas=20, cols=2)

# Inicializar confirmaciones si está vacía
if not sheet_confirm.get_all_values():
    sheet_confirm.update("A1:B1", [["Azul", "Blanco"]])
    sheet_confirm.update("A2:B2", [["❌", "❌"]])

# ---------- CONFIG STREAMLIT ----------
st.title("Pichanga ⚽")
st.write("Máximo 20 jugadores por partido")

# ---------- PANEL ADMIN ----------
st.sidebar.subheader("🛠 Admin")
password = st.sidebar.text_input("Contraseña admin", type="password")
if password == "#Mordecay123":
    st.sidebar.markdown("### Configuración de capitanes")
    capitán_azul = st.sidebar.text_input("Nombre capitán Azul")
    capitán_blanco = st.sidebar.text_input("Nombre capitán Blanco")
    if st.sidebar.button("Guardar capitanes"):
        st.session_state["capitan_azul"] = capitán_azul.strip()
        st.session_state["capitan_blanco"] = capitán_blanco.strip()
        st.sidebar.success("Capitanes guardados ✅")

    st.sidebar.markdown("---")
    if st.sidebar.button("Resetear lista de jugadores"):
        sheet_jugadores.clear()
        sheet_equipos.clear()
        sheet_confirm.update("A2:B2", [["❌", "❌"]])
        st.sidebar.success("Listas reseteadas ✅")

    nombre_borrar = st.sidebar.text_input("Borrar jugador específico")
    if st.sidebar.button("Borrar jugador"):
        jugadores_data = sheet_jugadores.get_all_values()
        jugadores = [j[0] for j in jugadores_data] if jugadores_data else []
        nombre_borrar_limpio = nombre_borrar.strip()
        if nombre_borrar_limpio in jugadores:
            index = jugadores.index(nombre_borrar_limpio) + 1
            sheet_jugadores.delete_rows(index)
            st.sidebar.success(f"Jugador '{nombre_borrar}' eliminado 🗑️")
        else:
            st.sidebar.warning(f"No se encontró el jugador '{nombre_borrar}'")

# ---------- SELECCIÓN DE COLOR DE CAPITÁN ----------
color_cap = st.sidebar.selectbox("¿Eres capitán Azul o Blanco?", ["Azul", "Blanco"])
capitan_actual = ""
if color_cap == "Azul":
    capitan_actual = st.session_state.get("capitan_azul", "")
else:
    capitan_actual = st.session_state.get("capitan_blanco", "")

if not capitan_actual:
    st.info("Admin aún no ha designado los capitanes de este partido")
    st.stop()

nombre_cap = st.text_input(f"Ingrese su nombre de capitán ({color_cap})")

# ---------- CONFIRMAR CAPITÁN ----------
if st.button("Ingresar como capitán"):
    if nombre_cap.strip() == capitan_actual:
        st.session_state[f"confirm_{color_cap}"] = True
        st.success(f"Bienvenido capitán {color_cap} ✅")
        # Guardar confirmación en Google Sheets
        if color_cap == "Azul":
            sheet_confirm.update_acell("A2", "✅")
        else:
            sheet_confirm.update_acell("B2", "✅")
    else:
        st.error("Nombre incorrecto ❌")

# ---------- VERIFICAR SI AMBOS CAPITANES HAN CONFIRMADO ----------
confirm_data = sheet_confirm.get_all_values()
eleccion_activa = False
if confirm_data and len(confirm_data) > 1:
    if confirm_data[1][0] == "✅" and confirm_data[1][1] == "✅":
        eleccion_activa = True

# ---------- ELECCIÓN DE JUGADORES ----------
if eleccion_activa:
    st.subheader("🏆 Elección de jugadores")

    # Obtener jugadores disponibles
    jugadores_data = sheet_jugadores.get_all_values()
    jugadores = [j[0] for j in jugadores_data] if jugadores_data else []

    if "seleccion_azul" not in st.session_state:
        st.session_state["seleccion_azul"] = [st.session_state.get("capitan_azul", "")]
    if "seleccion_blanco" not in st.session_state:
        st.session_state["seleccion_blanco"] = [st.session_state.get("capitan_blanco", "")]

    st.write("Jugadores disponibles:", jugadores)
    st.write("Equipo Azul:", st.session_state["seleccion_azul"])
    st.write("Equipo Blanco:", st.session_state["seleccion_blanco"])

    # Turno
    turno = st.session_state.get("turno", 0)
    color_turno = "Azul" if turno % 2 == 0 else "Blanco"
    st.write(f"Turno: {color_turno}")

    jugador_elegido = st.text_input(f"{color_turno}, escribe el nombre del jugador a elegir", key="eleccion_input")
    if st.button("Seleccionar jugador"):
        if jugador_elegido.strip() in jugadores:
            if color_turno == "Azul":
                st.session_state["seleccion_azul"].append(jugador_elegido.strip())
                sheet_equipos.update_cell(len(st.session_state["seleccion_azul"]), 1, jugador_elegido.strip())
            else:
                st.session_state["seleccion_blanco"].append(jugador_elegido.strip())
                sheet_equipos.update_cell(len(st.session_state["seleccion_blanco"]), 2, jugador_elegido.strip())

            jugadores.remove(jugador_elegido.strip())
            st.session_state["turno"] = turno + 1

            # Actualizar hoja de jugadores
            sheet_jugadores.clear()
            for i, j in enumerate(jugadores, start=1):
                sheet_jugadores.update_cell(i, 1, j)
        else:
            st.warning("Ese jugador no está disponible, escribe de nuevo ✅")

    if not jugadores:
        st.success("🎉 Elecciones finalizadas, buena suerte!")

# ---------- REGISTRO DE JUGADORES ----------
jugadores_data = sheet_jugadores.get_all_values()
jugadores = [j[0] for j in jugadores_data] if jugadores_data else []

if len(jugadores) < 20:
    nombre = st.text_input("Ingresa tu nombre (y posición si deseas)")
    if st.button("Anotarme"):
        nombre = nombre.strip()
        if nombre == "":
            st.warning("Ingresa un nombre válido")
        elif nombre in jugadores:
            st.warning("Ya estás inscrito!")
        else:
            sheet_jugadores.append_row([nombre, str(datetime.now())])
            st.success(f"{nombre} anotado")
else:
    st.error("Se alcanzó el máximo de 20 jugadores")

# ---------- MOSTRAR JUGADORES ----------
if jugadores:
    st.subheader("Jugadores inscritos:")
    for i, j in enumerate(jugadores, start=1):
        st.write(f"{i}. {j}")
