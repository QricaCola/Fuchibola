import streamlit as st
import json
import os
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from gspread.exceptions import APIError, WorksheetNotFound

# ---------------- CONFIG ----------------
SPREADSHEET_NAME = "Inscripciones Futbol"
ADMIN_PASSWORD = "#Mordecay123"
MAX_PLAYERS = 20

# ---------------- Google Sheets ----------------
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_dict = json.loads(os.environ['GSPREAD_JSON'])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

def open_spreadsheet_safe(name, retries=3, delay=1):
    """Abre la hoja de cálculo con reintentos automáticos para evitar caídas por límite de API"""
    for i in range(retries):
        try:
            return client.open(name)
        except APIError:
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise

spreadsheet = open_spreadsheet_safe(SPREADSHEET_NAME)

def open_or_create(title, rows=50, cols=2):
    """Abre o crea una hoja si no existe"""
    try:
        return spreadsheet.worksheet(title)
    except WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows=str(rows), cols=str(cols))

# Hojas
sheet_players = open_or_create("Jugadores", rows=200, cols=2)

# ---------------- Helpers ----------------
def get_players():
    values = sheet_players.get_all_values()
    return [v[0].strip() for v in values if len(v) > 0 and v[0].strip()]

def write_players(players):
    sheet_players.clear()
    if players:
        sheet_players.update("A1", [[p] for p in players])

# ---------------- UI ----------------
st.set_page_config(page_title="Pichanga ⚽", layout="wide")
st.title("Inscripción Pichanga ⚽")
st.write(f"Máximo de jugadores: {MAX_PLAYERS}")

# ---- PANEL ADMIN ----
with st.sidebar:
    st.header("🔧 Panel Admin")
    admin_pass = st.text_input("Contraseña Admin", type="password")

    if admin_pass == ADMIN_PASSWORD:
        st.success("Modo admin activado ✅")

        jugadores = get_players()
        st.subheader("Jugadores actuales:")
        for i, j in enumerate(jugadores, start=1):
            st.write(f"{i}. {j}")

        # Reset total
        if st.button("🧹 Resetear lista completa"):
            sheet_players.clear()
            st.success("Lista de jugadores borrada completamente.")

        # Borrar jugador individual
        nombre_borrar = st.text_input("Nombre a borrar")
        if st.button("Borrar jugador seleccionado"):
            jugadores = get_players()
            if nombre_borrar.strip() in jugadores:
                jugadores.remove(nombre_borrar.strip())
                write_players(jugadores)
                st.success(f"Jugador '{nombre_borrar.strip()}' eliminado.")
            else:
                st.warning("Nombre no encontrado en la lista.")
    else:
        st.info("Ingresa la contraseña de admin para administrar jugadores.")

# ---- REGISTRO ----
st.subheader("📝 Registro de jugadores")
jugadores = get_players()

with st.form("form_registro"):
    nombre = st.text_input("Tu nombre (y posición opcional)")
    submit = st.form_submit_button("Anotarme")

    if submit:
        nombre = nombre.strip()
        if not nombre:
            st.warning("Por favor, ingresa un nombre válido.")
        elif nombre in jugadores:
            st.warning("Ese nombre ya está inscrito.")
        elif len(jugadores) >= MAX_PLAYERS:
            st.error("Se alcanzó el máximo de jugadores.")
        else:
            sheet_players.append_row([nombre, str(datetime.now())])
            st.success(f"{nombre} inscrito correctamente ✅")

# ---- LISTA FINAL ----
st.subheader("📋 Jugadores inscritos actualmente:")
jugadores = get_players()

if jugadores:
    for i, j in enumerate(jugadores, start=1):
        st.write(f"{i}. {j}")
else:
    st.write("_Aún no hay jugadores inscritos_")
