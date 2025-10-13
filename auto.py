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

# Crear hojas si no existen
try:
    sheet_jugadores = client.open(sheet_name).worksheet("Jugadores")
except:
    sheet_jugadores = client.open(sheet_name).add_worksheet(title="Jugadores", rows="50", cols="1")

try:
    sheet_confirm = client.open(sheet_name).worksheet("Confirmaciones")
except:
    sheet_confirm = client.open(sheet_name).add_worksheet(title="Confirmaciones", rows="10", cols="2")
    sheet_confirm.update("A1:B1", [["Azul", "Blanco"]])
    sheet_confirm.update("A2:B2", [["❌", "❌"]])

try:
    sheet_equipos = client.open(sheet_name).worksheet("Equipos")
except:
    sheet_equipos = client.open(sheet_name).add_worksheet(title="Equipos", rows="20", cols="2")

# ---------- CONFIG STREAMLIT ----------
st.title("Pichanga Miércoles ⚽")
st.write("Máximo 20 jugadores por partido")

# ---------- PANEL ADMIN ----------
cap_azul = ""
cap_blanco = ""

password = st.sidebar.text_input("Admin", type="password")
if password == "#Mordecay123":
    st.sidebar.subheader("Panel Admin")
    
    # Leer jugadores actuales (si hay)
    jugadores_actuales = [j[0] for j in sheet_jugadores.get_all_values() if j]
    
    # Designar capitanes desde la web
    if jugadores_actuales:
        cap_azul = st.sidebar.selectbox("Elegir capitán Azul", [""] + jugadores_actuales)
        cap_blanco = st.sidebar.selectbox("Elegir capitán Blanco", [""] + jugadores_actuales)

    if st.sidebar.button("Resetear lista"):
        sheet_jugadores.clear()
        sheet_equipos.clear()
        sheet_confirm.update("A2:B2", [["❌", "❌"]])
        st.sidebar.success("Todo reseteado ✅")

# ---------- REGISTRO DE JUGADORES ----------
jugadores = [j[0] for j in sheet_jugadores.get_all_values() if j]
if len(jugadores) < 20:
    nombre = st.text_input("Ingresa tu nombre (y opcional posición)")
    if st.button("Anotarme"):
        nombre_limpio = nombre.strip()
        if not nombre_limpio:
            st.warning("Ingresa un nombre válido")
        elif nombre_limpio in jugadores:
            st.warning("Ya estás inscrito!")
        else:
            sheet_jugadores.append_row([nombre_limpio, str(datetime.now())])
            jugadores.append(nombre_limpio)
            st.success(f"{nombre_limpio} anotado ✅")
else:
    st.error("Se alcanzó el máximo de 20 jugadores")

# ---------- ELECCIÓN DE CAPITANES ----------
st.sidebar.markdown("---")
st.sidebar.subheader("Zona Capitanes")

# Solo mostrar input si los capitanes están definidos
if cap_azul and cap_blanco:
    color_inicio = st.sidebar.radio("¿Quién comienza la elección?", ["Azul", "Blanco"])
    capitan_actual = cap_azul if color_inicio == "Azul" else cap_blanco
    otro_capitan = cap_blanco if color_inicio == "Azul" else cap_azul
    
    nombre_cap = st.sidebar.text_input("Nombre del capitán")
    clave_cap = st.sidebar.text_input("Contraseña", type="password")
    
    # Contraseña única
    contraseña_capitan = "clave123"
    
    if st.sidebar.button("Ingresar como capitán"):
        if nombre_cap == capitan_actual and clave_cap == contraseña_capitan:
            st.session_state["capitan"] = nombre_cap
            st.sidebar.success(f"Bienvenido {nombre_cap}, es tu turno para elegir!")
        else:
            st.sidebar.error("Nombre o contraseña incorrectos ❌")
else:
    st.sidebar.info("Esperando que el admin seleccione los capitanes")

# ---------- ELECCIÓN DE JUGADORES ----------
if st.session_state.get("capitan"):
    st.subheader("🏆 Elección de jugadores")
    
    jugadores_disponibles = [j for j in jugadores if j not in [cap_azul, cap_blanco]]
    
    if "seleccion_azul" not in st.session_state:
        st.session_state["seleccion_azul"] = [cap_azul] if cap_azul else []
    if "seleccion_blanco" not in st.session_state:
        st.session_state["seleccion_blanco"] = [cap_blanco] if cap_blanco else []
    
    st.write("Jugadores disponibles:", jugadores_disponibles)
    st.write("Equipo Azul:", st.session_state["seleccion_azul"])
    st.write("Equipo Blanco:", st.session_state["seleccion_blanco"])
    
    # Determinar turno
    if "turno" not in st.session_state:
        st.session_state["turno"] = 0
    
    turno_actual = cap_azul if st.session_state["turno"] % 2 == 0 else cap_blanco
    st.write(f"Turno actual: {turno_actual}")
    
    nombre_elegido = st.text_input(f"{turno_actual}, escribe el nombre del jugador a elegir", key="eleccion_input")
    
    if st.button("Seleccionar jugador"):
        if nombre_elegido in jugadores_disponibles:
            if turno_actual == cap_azul:
                st.session_state["seleccion_azul"].append(nombre_elegido)
            else:
                st.session_state["seleccion_blanco"].append(nombre_elegido)
            
            jugadores_disponibles.remove(nombre_elegido)
            st.session_state["turno"] += 1
        else:
            st.warning("Ese jugador no está disponible o ya fue elegido")
    
    if not jugadores_disponibles:
        st.success("🎉 Elecciones finalizadas, buena suerte!")
