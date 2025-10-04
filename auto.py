import streamlit as st
import time

st.set_page_config(page_title="Proyecto", page_icon="🛹")

# --- Estilo personalizado ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #e3f2fd, #fce4ec);
        text-align: center;
    }
    h1 {
        color: #1e88e5;
    }
    .result {
        font-size: 1.3em;
        color: #2e7d32;
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Contenido principal ---
st.title("🔤 Contador de Letras")

palabra = st.text_input("✏️ Escribe una palabra:", "")

if st.button("Contar letras"):
    if palabra.strip() == "":
        st.warning("⚠️ Por favor, escribe una palabra primero.")
    else:
        st.info("Procesando tu palabra...")
        progreso = st.progress(0)

        for i in range(100):
            time.sleep(0.02)
            progreso.progress(i + 1)

        st.balloons()
        st.markdown(
            f"<div class='result'>La palabra <b>{palabra}</b> tiene <b>{len(palabra)}</b> letras. 🎉</div>",
            unsafe_allow_html=True
        )
