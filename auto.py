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
st.write("Máximo 20 jugadores por partido")

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
    # --- Borrar jugador específico ---
    nombre_borrar = st.sidebar.text_input("Ingresar el nombre a borrar")
    
    if st.sidebar.button("Borrar jugador"):
        jugadores = [j.strip().lower() for j in sheet.col_values(1)]  # limpia espacios y minúsculas
        nombre_borrar_limpio = nombre_borrar.strip().lower()
    
        if nombre_borrar_limpio in jugadores:
            index = jugadores.index(nombre_borrar_limpio) + 1  # +1 porque las hojas comienzan en 1
            sheet.delete_rows(index)
            st.sidebar.success(f"Jugador '{nombre_borrar}' eliminado correctamente 🗑️")
        else:
            st.sidebar.warning(f"No se encontró el jugador '{nombre_borrar}' en la lista. Revisa que esté bien escrito.")

# ---------- PANEL DE CAPITANES ----------
st.sidebar.markdown("---")
st.sidebar.subheader("⚽ Zona de Capitanes")

# Diccionario con capitanes y sus contraseñas
capitanes = {
    "Capitán 1": "clave1",
    "Capitán 2": "clave2"
}

nombre_capitan = st.sidebar.text_input("Nombre del capitán")
clave_capitan = st.sidebar.text_input("Contraseña del capitán", type="password")

if st.sidebar.button("Ingresar como capitán"):
    if nombre_capitan in capitanes and clave_capitan == capitanes[nombre_capitan]:
        st.session_state["capitan"] = nombre_capitan
        st.sidebar.success(f"Bienvenido, {nombre_capitan} 👋 Esperando al otro capitán...")

        # ---------- Confirmaciones en Google Sheets ----------
        try:
            hoja_confirmaciones = client.open("Fuchibola").worksheet("Confirmaciones")
        except:
            hoja_confirmaciones = client.open("Fuchibola").add_worksheet(title="Confirmaciones", rows="10", cols="2")
            hoja_confirmaciones.update("A1:B1", [["Capitán 1", "Capitán 2"]])
            hoja_confirmaciones.update("A2:B2", [["❌", "❌"]])

        confirmaciones = hoja_confirmaciones.get_all_values()
        if nombre_capitan == "Capitán 1":
            hoja_confirmaciones.update_acell("A2", "✅")
        elif nombre_capitan == "Capitán 2":
            hoja_confirmaciones.update_acell("B2", "✅")

        confirmaciones = hoja_confirmaciones.get_all_values()

        # Si ambos confirmaron, mostrar mensaje
        if len(confirmaciones) > 1 and confirmaciones[1][0] == "✅" and confirmaciones[1][1] == "✅":
            st.sidebar.success("✅ Ambos capitanes han confirmado. ¡Comienza la elección de jugadores!")
            st.session_state["eleccion_activa"] = True
        else:
            st.sidebar.info("Esperando al otro capitán...")

    else:
        st.sidebar.error("Nombre o contraseña incorrectos ❌")
# ---------- REGISTRO DE JUGADORES ----------
if len(jugadores) < 20:
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
    st.error("Se alcanzó el máximo de 20 jugadores broder")

# ---------- MOSTRAR JUGADORES ----------
if jugadores:
    st.subheader("Jugadores inscritos:")
    for i, j in enumerate(jugadores, start=1):
        st.write(f"{i}. {j}")
