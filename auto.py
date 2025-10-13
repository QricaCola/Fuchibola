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

# Nombre del spreadsheet
sheet_name = "Inscripciones Futbol"

# ---------- CREAR HOJAS SI NO EXISTEN ----------
def crear_hoja(nombre_hoja, filas=50, cols=2):
    try:
        return client.open(sheet_name).worksheet(nombre_hoja)
    except:
        return client.open(sheet_name).add_worksheet(title=nombre_hoja, rows=str(filas), cols=str(cols))

sheet_jugadores = crear_hoja("Jugadores", 50, 1)
sheet_confirm = crear_hoja("Confirmaciones", 10, 2)
sheet_equipos = crear_hoja("Equipos", 20, 2)

# Inicializar confirmaciones si está vacío
if not sheet_confirm.get_all_values():
    sheet_confirm.update("A1:B1", [["Azul", "Blanco"]])
    sheet_confirm.update("A2:B2", [["❌", "❌"]])

# ---------- CONFIG STREAMLIT ----------
st.title("Pichanga Miércoles ⚽")
st.write("Máximo 20 jugadores por partido")

# ---------- PANEL DE ADMIN ----------
password = st.sidebar.text_input("Admin", type="password")
if password == "#Mordecay123":
    st.sidebar.subheader("Panel Admin")
    
    # Designar capitanes
    jugadores_actuales = [j[0] for j in sheet_jugadores.get_all_values() if j]
    cap_azul = st.sidebar.selectbox("Elegir capitán Azul", jugadores_actuales)
    cap_blanco = st.sidebar.selectbox("Elegir capitán Blanco", jugadores_actuales)
    
    # Resetear elecciones
    if st.sidebar.button("Resetear elecciones"):
        sheet_equipos.clear()
        sheet_confirm.update("A2:B2", [["❌", "❌"]])
        st.sidebar.success("Elecciones reseteadas!")

# ---------- PANEL CAPITANES ----------
st.sidebar.markdown("---")
st.sidebar.subheader("⚽ Zona Capitanes")

contraseña_capitan = st.sidebar.text_input("Contraseña de capitanes", type="password")

color_inicio = st.sidebar.radio("¿Qué color inicia la elección?", ["Azul", "Blanco"])
capitan_actual = cap_azul if color_inicio == "Azul" else cap_blanco
otro_capitan = cap_blanco if color_inicio == "Azul" else cap_azul

nombre_cap = st.sidebar.text_input("Nombre del capitán")

if st.sidebar.button("Ingresar como capitán"):
    if nombre_cap in [cap_azul, cap_blanco] and contraseña_capitan == "#Capitan123":
        st.session_state["capitan"] = nombre_cap
        st.sidebar.success(f"Bienvenido {nombre_cap}, esperando a que el turno sea tuyo...")
    else:
        st.sidebar.error("Nombre o contraseña incorrectos ❌")

# ---------- ELECCIÓN DE JUGADORES ----------
if "capitan" in st.session_state:
    st.subheader("🏆 Elección de jugadores")
    
    jugadores_disponibles = [j[0] for j in sheet_jugadores.get_all_values() if j]
    
    if "seleccion_azul" not in st.session_state:
        st.session_state["seleccion_azul"] = [cap_azul]
    if "seleccion_blanco" not in st.session_state:
        st.session_state["seleccion_blanco"] = [cap_blanco]
    if "turno" not in st.session_state:
        st.session_state["turno"] = 0  # 0 = inicia color elegido
    
    st.write("Jugadores disponibles:", jugadores_disponibles)
    st.write("Equipo Azul:", st.session_state["seleccion_azul"])
    st.write("Equipo Blanco:", st.session_state["seleccion_blanco"])
    
    # Turno
    turno_actual = color_inicio if st.session_state["turno"] % 2 == 0 else ("Blanco" if color_inicio=="Azul" else "Azul")
    st.write(f"Turno: {turno_actual}")
    
    # Solo el capitán del turno puede elegir
    if (turno_actual == "Azul" and st.session_state["capitan"] == cap_azul) or \
       (turno_actual == "Blanco" and st.session_state["capitan"] == cap_blanco):
        
        nombre_elegido = st.text_input(f"{turno_actual}, escribe el nombre del jugador a elegir", key="eleccion_input")
        
        if st.button("Seleccionar jugador"):
            if nombre_elegido in jugadores_disponibles:
                if turno_actual == "Azul":
                    st.session_state["seleccion_azul"].append(nombre_elegido)
                    sheet_equipos.update_cell(len(st.session_state["seleccion_azul"]), 1, nombre_elegido)
                else:
                    st.session_state["seleccion_blanco"].append(nombre_elegido)
                    sheet_equipos.update_cell(len(st.session_state["seleccion_blanco"]), 2, nombre_elegido)
                
                jugadores_disponibles.remove(nombre_elegido)
                st.session_state["turno"] += 1
                
                # Actualizar hoja de jugadores
                sheet_jugadores.clear()
                if jugadores_disponibles:
                    sheet_jugadores.update("A1", [[j] for j in jugadores_disponibles])
            else:
                st.warning("Ese jugador no está disponible")
    else:
        st.info("Esperando que el otro capitán haga su elección...")

# ---------- REGISTRO DE JUGADORES ----------
if "capitan" not in st.session_state:
    if len([j[0] for j in sheet_jugadores.get_all_values() if j]) < 20:
        nombre = st.text_input("Ingresa tu nombre y si deseas posición")
        if st.button("Anotarme"):
            if nombre.strip() == "":
                st.warning("Ingresa un nombre válido")
            else:
                sheet_jugadores.append_row([nombre, str(datetime.now())])
                st.success(f"{nombre} anotado")
    else:
        st.error("Se alcanzó el máximo de 20 jugadores")
