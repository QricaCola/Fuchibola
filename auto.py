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
sheet = client.open(sheet_name).worksheet("Jugadores")  # Hoja de jugadores

# ---------- CONFIG STREAMLIT ----------
st.title("Pichanga Miércoles ⚽")
st.write("Máximo 20 jugadores por partido")

# Leer jugadores actuales
try:
    jugadores = sheet.col_values(1)
except:
    jugadores = []

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
