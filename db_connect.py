import streamlit as st
from supabase import create_client, Client

# Fungsi untuk inisialisasi koneksi
# Menggunakan @st.cache_resource agar koneksi tidak dibuat ulang tiap kali user klik tombol (biar cepat)
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Gagal koneksi ke database: {e}")
        return None

# Variabel global client
supabase: Client = init_connection()

# Fungsi Test Sederhana (Hanya untuk debugging awal)
def test_connection():
    try:
        # Coba ambil data dari tabel 'users' (walaupun masih kosong)
        response = supabase.table("users").select("*").execute()
        return True, "Koneksi Berhasil! Database merespon."
    except Exception as e:
        return False, f"Error: {e}"