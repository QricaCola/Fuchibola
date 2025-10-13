import streamlit as st
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ---------------- CONFIG GOOGLE SHEETS ----------------
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# Leer credenciales desde variable de entorno (Streamlit Cloud)
creds_dict = json.loads(os.environ['GSPREAD_JSON'])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Nombre del spreadsheet (cámbialo si tu archivo en Drive tiene otro nombre)
SPREADSHEET_NAME = "Inscripciones Futbol"

# Función utilitaria: abrir o crear worksheet
def abrir_o_crear_worksheet(spreadsheet, titulo, rows=100, cols=2):
    try:
        return client.open(spreadsheet).worksheet(titulo)
    except gspread.SpreadsheetNotFound:
        st.error(f"No existe el spreadsheet '{spreadsheet}'. Crea uno con ese nombre y comparte con la service account.")
        st.stop()
    except gspread.WorksheetNotFound:
        ss = client.open(spreadsheet)
        return ss.add_worksheet(title=titulo, rows=str(rows), cols=str(cols))

# Inicializar/abrir hojas necesarias
# Hoja principal de inscripciones (podría ser la primera pestaña o "Jugadores" — aquí abrimos/creamos pestañas específicas)
# Jugadores: columna A (nombre)
sheet_jugadores = abrir_o_crear_worksheet(SPREADSHEET_NAME, "Jugadores", rows=200, cols=1)
# Equipos: columnas A=Blanco, B=Azul (fila1 encabezados)
sheet_equipos = abrir_o_crear_worksheet(SPREADSHEET_NAME, "Equipos", rows=200, cols=2)
# Turno: celda A1 guarda "Blanco" o "Azul"
sheet_turno = abrir_o_crear_worksheet(SPREADSHEET_NAME, "Turno", rows=5, cols=2)

# Asegurar cabeceras estándar (no sobrescribe jugadores/equipos ya existentes)
try:
    head = sheet_equipos.row_values(1)
    if not head or head[0] != "Blanco" or (len(head) < 2 or head[1] != "Azul"):
        sheet_equipos.update("A1:B1", [["Blanco", "Azul"]])
except Exception:
    sheet_equipos.update("A1:B1", [["Blanco", "Azul"]])

try:
    turno_val = sheet_turno.acell("A1").value
except Exception:
    turno_val = None

# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="Pichanga Miércoles", layout="centered")
st.title("Pichanga Miércoles ⚽")
st.write("Máximo 20 jugadores por partido")

# ---------- PANEL ADMIN ----------
st.sidebar.header("🔧 Panel Admin")
admin_pass = st.sidebar.text_input("Contraseña admin", type="password")
if admin_pass == "#Mordecay123":  # Cambia por tu contraseña segura
    if st.sidebar.button("Resetear todo (nuevo partido)"):
        # Limpiar Jugadores, Equipos, Turno
        sheet_jugadores.clear()
        sheet_equipos.clear()
        sheet_equipos.update("A1:B1", [["Blanco", "Azul"]])
        sheet_turno.clear()
        st.sidebar.success("✅ Todo reseteado. Crea la nueva inscripción.")
    st.sidebar.markdown("---")
    nombre_borrar = st.sidebar.text_input("Nombre a borrar (admin)")
    if st.sidebar.button("Borrar jugador (admin)"):
        # borrar en hoja Jugadores (insensitive)
        jgs = [r[0].strip() for r in sheet_jugadores.get_all_values() if r]
        target = nombre_borrar.strip().lower()
        found = False
        for i, val in enumerate(jgs, start=1):
            if val.lower() == target:
                sheet_jugadores.delete_rows(i)
                st.sidebar.success(f"'{nombre_borrar}' eliminado de Jugadores.")
                found = True
                break
        if not found:
            st.sidebar.warning("No encontrado en Jugadores.")

# ---------- REGISTRO DE JUGADORES (pública) ----------
st.header("📝 Inscripción")
# Cargar lista actual desde sheet Jugadores
try:
    jugadores_lista = [r[0] for r in sheet_jugadores.get_all_values() if r]
except Exception as e:
    st.error("Error leyendo la hoja 'Jugadores'. Revisa permisos y nombre del spreadsheet.")
    st.stop()

st.write(f"Jugadores inscritos actualmente: {len(jugadores_lista)}")
if len(jugadores_lista) < 20:
    nombre_nuevo = st.text_input("Ingresa tu nombre (opcional: posición entre paréntesis)")
    if st.button("Anotarme"):
        n = nombre_nuevo.strip()
        if not n:
            st.warning("Ingresa un nombre válido.")
        else:
            # prevenir duplicados (ignorar mayúsculas/minúsculas y espacios extra)
            clean = [x.strip().lower() for x in jugadores_lista]
            if n.strip().lower() in clean:
                st.warning("Ya estás inscrito.")
            else:
                sheet_jugadores.append_row([n, str(datetime.now())])
                st.success(f"{n} anotado ✅")
                # actualizar la lista local para que aparezca en la misma sesión
                jugadores_lista.append(n)
else:
    st.error("Se alcanzó el máximo de 20 jugadores.")

# Mostrar la lista
if jugadores_lista:
    st.subheader("Lista de inscritos")
    for i, j in enumerate(jugadores_lista, start=1):
        st.write(f"{i}. {j}")

st.write("---")

# ---------- ZONA CAPITANES Y ELECCIÓN POR TURNOS ----------
st.header("⚽ Elección por capitanes (Blanco / Azul)")

# Configuración: contraseña común (puedes cambiarla en el código)
CONTRASEÑA_CAPITAN = "clave123"

# Login / selección de color del capitán
col1, col2 = st.columns(2)
with col1:
    nombre_cap = st.text_input("Nombre del capitán (usa tu nombre real)", key="cap_nombre")
with col2:
    color_cap = st.selectbox("Elige tu color", ["Blanco", "Azul"], key="cap_color")

clave_input = st.text_input("Contraseña de capitán", type="password", key="cap_pass")
if st.button("Entrar como capitán"):
    if clave_input == CONTRASEÑA_CAPITAN and nombre_cap.strip() != "":
        st.success(f"Bienvenido {nombre_cap} — eres el capitán del equipo {color_cap}")
        st.session_state["cap_nombre"] = nombre_cap.strip()
        st.session_state["cap_color"] = color_cap
        # Colocar al capitán al inicio del equipo si no está ya
        try:
            equipos = sheet_equipos.get_all_values()
            # asegurar header
            if not equipos or equipos[0][:2] != ["Blanco", "Azul"]:
                sheet_equipos.update("A1:B1", [["Blanco", "Azul"]])
                equipos = sheet_equipos.get_all_values()
            # obtener columnas actuales (sin header)
            col_blanco = [r[0] for r in equipos[1:] if len(r) >= 1 and r[0].strip() != ""]
            col_azul = [r[1] for r in equipos[1:] if len(r) >= 2 and r[1].strip() != ""]
            # marca de capitán
            cap_tag = f"{nombre_cap.strip()} (CAPITÁN)"
            if color_cap == "Blanco":
                if cap_tag not in col_blanco:
                    # insertar en la cima: reconstruir lista con capitán primero
                    nueva = [cap_tag] + [p for p in col_blanco if p != cap_tag]
                    # escribir todo de nuevo: limpiar y actualizar
                    sheet_equipos.clear()
                    sheet_equipos.update("A1:B1", [["Blanco", "Azul"]])
                    # preparar filas
                    filas = []
                    max_len = max(len(nueva), len(col_azul))
                    for i in range(max_len):
                        a = nueva[i] if i < len(nueva) else ""
                        b = col_azul[i] if i < len(col_azul) else ""
                        filas.append([a, b])
                    if filas:
                        sheet_equipos.update("A2", filas)
            else:  # Azul
                if cap_tag not in col_azul:
                    nueva = [cap_tag] + [p for p in col_azul if p != cap_tag]
                    sheet_equipos.clear()
                    sheet_equipos.update("A1:B1", [["Blanco", "Azul"]])
                    filas = []
                    max_len = max(len(col_blanco), len(nueva))
                    for i in range(max_len):
                        a = col_blanco[i] if i < len(col_blanco) else ""
                        b = nueva[i] if i < len(nueva) else ""
                        filas.append([a, b])
                    if filas:
                        sheet_equipos.update("A2", filas)
        except Exception as e:
            st.error("Error actualizando equipos (comprueba permisos del service account).")
    else:
        st.error("Contraseña incorrecta o nombre vacío.")

st.markdown("**Inicio de la elección**")
# Allow admin or captain to set which team starts
col_start1, col_start2 = st.columns([2,3])
with col_start1:
    quien_parte = st.selectbox("¿Qué equipo parte primero?", ["Blanco", "Azul"], key="quien_parte")
with col_start2:
    if st.button("Fijar turno inicial"):
        sheet_turno.update_acell("A1", quien_parte)
        st.success(f"Turno inicial fijado: {quien_parte}")

# Leer estado actual de turno
try:
    turno_actual = sheet_turno.acell("A1").value
except Exception:
    turno_actual = None

st.write(f"**Turno actual:** {turno_actual if turno_actual else 'Sin turno fijado'}")

# Mostrar equipos en pantalla (leer sheet_equipos)
try:
    equipos_tabla = sheet_equipos.get_all_values()
    # convertir en columnas limpias
    header = equipos_tabla[0] if equipos_tabla else ["Blanco", "Azul"]
    filas = equipos_tabla[1:] if len(equipos_tabla) > 1 else []
    col_blanco = [r[0] for r in filas if len(r) >= 1 and r[0].strip() != ""]
    col_azul = [r[1] for r in filas if len(r) >= 2 and r[1].strip() != ""]
except Exception:
    col_blanco, col_azul = [], []

st.subheader("Equipo Blanco ⚪")
for i, p in enumerate(col_blanco, start=1):
    st.write(f"{i}. {p}")

st.subheader("Equipo Azul 🔵")
for i, p in enumerate(col_azul, start=1):
    st.write(f"{i}. {p}")

st.write("---")

# ---------- ELECCIÓN: sólo si capitán logueado y es su turno ----------
cap_nombre = st.session_state.get("cap_nombre")
cap_color = st.session_state.get("cap_color")

if cap_nombre and cap_color:
    # Mostrar si es su turno
    if turno_actual is None:
        st.info("Aún no se ha fijado el turno inicial. Usa 'Fijar turno inicial'.")
    else:
        if turno_actual != cap_color:
            st.info(f"No es tu turno. Es el turno de: {turno_actual}. Vuelve a cargar la página para ver cambios.")
        else:
            st.success("Es tu turno. Puedes seleccionar un jugador.")
            # Lista jugadores disponibles (leer desde Jugadores)
            jugadores_disp = [r[0] for r in sheet_jugadores.get_all_values() if r]
            st.write("Jugadores disponibles:", jugadores_disp)
            nombre_elegido = st.text_input("Escribe exactamente el nombre del jugador que eliges", key="elec_input")
            if st.button("Confirmar selección"):
                chosen = nombre_elegido.strip()
                if chosen == "":
                    st.warning("Escribe un nombre válido.")
                else:
                    # normalizar y buscar en Jugadores
                    clean = [x.strip() for x in jugadores_disp]
                    matches = [i for i, v in enumerate(clean, start=1) if v.lower() == chosen.lower()]
                    if not matches:
                        st.warning("Ese jugador no está disponible. Revisa escritura o recarga la página.")
                    else:
                        # tomar la primera coincidencia
                        row_index = matches[0]
                        # Append to team column (after existing)
                        try:
                            equipos_tabla = sheet_equipos.get_all_values()
                            filas = equipos_tabla[1:] if len(equipos_tabla) > 1 else []
                            col_b = [r[0] for r in filas if len(r) >=1]
                            col_a = [r[1] for r in filas if len(r) >=2]
                            # rebuild columns including new pick, preserving captain on top
                            if cap_color == "Blanco":
                                col_b.append(clean[row_index-1])
                            else:
                                col_a.append(clean[row_index-1])
                            # write back: header + rows
                            max_len = max(len(col_b), len(col_a))
                            rows_to_write = []
                            for i in range(max_len):
                                a = col_b[i] if i < len(col_b) else ""
                                b = col_a[i] if i < len(col_a) else ""
                                rows_to_write.append([a, b])
                            sheet_equipos.clear()
                            sheet_equipos.update("A1:B1", [["Blanco", "Azul"]])
                            if rows_to_write:
                                sheet_equipos.update("A2", rows_to_write)
                            # eliminar jugador de Jugadores (la hoja tiene items desde fila1)
                            sheet_jugadores.delete_rows(row_index)
                            st.success(f"{clean[row_index-1]} agregado a {cap_color} ✅")
                            # Cambiar turno en sheet Turno
                            nuevo_turno = "Azul" if cap_color == "Blanco" else "Blanco"
                            sheet_turno.update_acell("A1", nuevo_turno)
                            st.info(f"Turno cambiado a {nuevo_turno}.")
                        except Exception as e:
                            st.error("Error al procesar la elección. Revisa permisos y vuelve a intentar.")

# ---------- FINAL: mostrar mensaje si no quedan jugadores ----------
try:
    remaining = [r[0] for r in sheet_jugadores.get_all_values() if r]
except Exception:
    remaining = []

if not remaining:
    st.success("🎉 Elecciones finalizadas, buena suerte!")
