import streamlit as st
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ---------- CONFIG GOOGLE SHEETS ----------
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Leer credenciales desde variable de entorno de Streamlit Cloud
creds_dict = json.loads(os.environ['GSPREAD_JSON'])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Abrir hoja de Google Sheets
sheet_name = "Inscripciones Futbol"  # Asegúrate de que esta hoja exista en Google Sheets
sheet = client.open(sheet_name).sheet1

# ---------- CONFIG STREAMLIT ----------
st.title("Pichanga Miércoles ⚽")
st.write("Máximo 14 jugadores por partido")

# Leer jugadores actuales desde Google Sheets
try:
    jugadores = sheet.col_values(1)
except:
    jugadores = []

# ---------- PANEL DE ADMIN (RESET) ----------
password = st.sidebar.text_input("Admin", type="password")
if password == "#Mordecay123":  # Cambia esto a algo seguro
    if st.sidebar.button("Resetear lista"):
        sheet.clear()
        st.sidebar.success("Lista reseteada!")
    st.sidebar.markdown("---")

# ---------- REGISTRO DE JUGADORES ----------
if len(jugadores) < 14:
    nombre = st.text_input("Ingresa tu nombre y si deseas, añade la posición en la que te gusta jugar entre paréntesis")
    if st.button("Anotarme"):
        if nombre.strip() == "":
            st.warning("Ingresa un nombre válido")
        elif nombre in jugadores:
            st.warning("Ya estás inscrito!")
        else:
            # Guardar en Google Sheets
            sheet.append_row([nombre, str(datetime.now())])
            st.success(f"{nombre} anotado")
            jugadores.append(nombre)
else:
    st.error("Se alcanzó el máximo de 14 jugadores broder")

# ---------- MOSTRAR JUGADORES ----------
if jugadores:
    st.subheader("Jugadores inscritos:")
    for i, j in enumerate(jugadores, start=1):
        st.write(f"{i}. {j}")
