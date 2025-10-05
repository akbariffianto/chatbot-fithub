# fitbot_project/app.py

import streamlit as st
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

from agent_logic import create_fitbot_agent
from database import init_db

# Muat variabel lingkungan dari file .env
load_dotenv()

# --- Inisialisasi Aplikasi ---
# Panggil sekali untuk memastikan database dan tabel sudah ada
init_db()

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(page_title="FitBot - AI Fitness Assistant", page_icon="💪")
st.title("💪 FitBot - Your AI Fitness Assistant")
st.caption("Didukung oleh Google Gemini, LangChain, dan Streamlit")

# --- Manajemen State (State Management) ---
# Inisialisasi agen dan riwayat obrolan dalam session state Streamlit
if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = create_fitbot_agent()

if "messages" not in st.session_state:
    st.session_state.messages = [
        AIMessage(content="Halo! Saya FitBot, asisten kebugaran Anda. Apa yang bisa saya bantu hari ini? Anda bisa meminta rencana latihan, mencatat progres, atau bertanya tentang riwayat latihan Anda.")
    ]

# --- Antarmuka Obrolan (Chat Interface) ---

# Tampilkan pesan-pesan sebelumnya
for msg in st.session_state.messages:
    if isinstance(msg, AIMessage):
        st.chat_message("assistant").write(msg.content)
    elif isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)

# Dapatkan input dari pengguna
if prompt := st.chat_input("Tanyakan sesuatu pada FitBot..."):
    # Pastikan API key ada
    if not os.getenv("GOOGLE_API_KEY"):
        st.info("Harap atur GOOGLE_API_KEY Anda di file .env")
        st.stop()
    
    # Tambahkan pesan pengguna ke riwayat dan tampilkan
    st.session_state.messages.append(HumanMessage(content=prompt))
    st.chat_message("user").write(prompt)

    # Dapatkan respons dari agen
    with st.spinner("FitBot sedang berpikir..."):
        # Kita perlu mengirim seluruh riwayat obrolan agar agen memiliki konteks
        response = st.session_state.agent_executor.invoke({
            "messages": st.session_state.messages
        })
    
    # Ambil konten pesan terakhir dari output agen
    ai_response_content = response['messages'][-1].content
    
    # Tambahkan respons AI ke riwayat dan tampilkan
    st.session_state.messages.append(AIMessage(content=ai_response_content))
    st.chat_message("assistant").write(ai_response_content)