import streamlit as st
import os
from supabase import create_client, Client

# Fungsi Helper untuk mengambil Secret (Support Streamlit & OS Env)
def get_secret(key_parent, key_child):
    # Coba ambil dari Streamlit Secrets (saat run lokal / streamlit cloud)
    try:
        return st.secrets[key_parent][key_child]
    except:
        # Jika gagal (berarti sedang jalan di GitHub Actions), ambil dari OS Environ
        # Nanti di GitHub kita set nama variablenya: SUPABASE_URL, SUPABASE_KEY, dsb.
        env_name = f"{key_parent.upper()}_{key_child.upper()}"
        return os.environ.get(env_name)

@st.cache_resource
def init_connection():
    try:
        url = get_secret("supabase", "url")
        key = get_secret("supabase", "key")
        
        if not url or not key:
            # Fallback manual jika cache bermasalah di script python biasa
            return create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
            
        return create_client(url, key)
    except Exception as e:
        # Jika dijalankan di luar Streamlit (Script murni), st.error akan gagal
        # Kita return None atau print error biasa
        print(f"Koneksi DB Init Error: {e}")
        return None

# Buat Client Global
# Perbaikan logika: Jika dijalankan via GitHub Actions, @st.cache_resource tidak jalan
# Jadi kita buat koneksi langsung
try:
    if st.runtime.exists():
        supabase: Client = init_connection()
    else:
        # Mode Script (GitHub Actions)
        _url = os.environ.get("SUPABASE_URL")
        _key = os.environ.get("SUPABASE_KEY")
        supabase: Client = create_client(_url, _key)
except:
    # Fallback terakhir
    try:
        _url = os.environ.get("SUPABASE_URL")
        _key = os.environ.get("SUPABASE_KEY")
        supabase: Client = create_client(_url, _key)
    except:
        supabase = None
