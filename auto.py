import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Configuración Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
client = gspread.authorize(creds)

# Abrir la hoja
sheet = client.open("Inscripciones Futbol").sheet1

# --- Inicializar estado si no existe ---
# Celda A1 = "Estado" | A2 = "Cerrada"
try:
    estado = sheet.acell("A2").value
except:
    sheet.update("A1", "Estado")
    sheet.update("A2", "Cerrada")
    estado = "Cerrada"

# --- Leer datos existentes ---
data = sheet.get_all_records()
df = pd.DataFrame(data)

st.title("⚽ Inscripción pichanga ⚽")
st.write(f"Cupo máximo: 14 jugadores")
st.write(f"Jugadores inscritos: {len(df)}")
st.write(f"Estado de la lista: {estado}")

# -------------------------
# Panel de control de admin
# -------------------------
admin_password = "#Mordecay123"  # Cambia esto a tu contraseña

st.sidebar.title("Panel de administrador 🔒")
password = st.sidebar.text_input("Ingresa contraseña", type="password")

if password == admin_password:
    st.sidebar.subheader("Control de lista")
    
    if st.sidebar.button("Resetear lista"):
        sheet.clear()
        sheet.append_row(["Nombre"])  # encabezado
        sheet.update("A1", "Estado")
        sheet.update("A2", "Cerrada")
        st.success("✅ Lista reseteada correctamente")
        df = pd.DataFrame(columns=["Nombre"])  # vacía localmente
        estado = "Cerrada"
        
    if st.sidebar.button("Abrir lista"):
        sheet.update("A2", "Abierta")
        st.success("✅ Lista abierta para inscripciones")
        estado = "Abierta"

elif password != "" and password != admin_password:
    st.sidebar.error("Contraseña incorrecta ❌")

# -------------------------
# Registro de jugadores
# -------------------------
nombre = st.text_input("Ingresa tu nombre")

if st.button("Registrarme"):
    if estado != "Abierta":
        st.warning("❌ Las inscripciones aún no están abiertas ❌")
    elif len(df) >= 14:
        st.error("⚠️ Cupo completo, la lista ya está cerrada ⚠️")
        sheet.update("A2", "Cerrada")
        estado = "Cerrada"
    elif nombre.strip() == "":
        st.warning("Ingresa un nombre válido")
    elif nombre in df['Nombre'].values:
        st.warning("Ya estás inscrito broder")
    else:
        sheet.append_row([nombre])
        st.success(f"{nombre} inscrito correctamente ✅")
        df = pd.concat([df, pd.DataFrame({"Nombre":[nombre]})], ignore_index=True)
        # Cierre automático al llegar a 14 jugadores
        if len(df) >= 14:
            st.warning("⚠️ Se alcanzó el cupo máximo, la lista se cerrará automáticamente")
            sheet.update("A2", "Cerrada")
            estado = "Cerrada"

# Mostrar jugadores
st.subheader("Jugadores inscritos")
st.table(df)