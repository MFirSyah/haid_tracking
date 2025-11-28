import streamlit as st
import os
from supabase import create_client, Client

# 1. Fungsi Helper Aman (Bisa baca Secrets Streamlit ATAU Environment Variable GitHub)
def get_secret(key_parent, key_child):
    # Coba ambil dari Streamlit Secrets (Priority 1)
    try:
        return st.secrets[key_parent][key_child]
    except (FileNotFoundError, KeyError, AttributeError):
        # Jika gagal, ambil dari OS Environment (Priority 2 - untuk GitHub Actions)
        env_key = f"{key_parent.upper()}_{key_child.upper()}"
        return os.environ.get(env_key)

# 2. Inisialisasi Koneksi (Cached)
# Kita gunakan try-except agar tidak error saat diimport
@st.cache_resource
def init_connection():
    try:
        url = get_secret("supabase", "url")
        key = get_secret("supabase", "key")
        
        if not url or not key:
            return None
            
        return create_client(url, key)
    except Exception as e:
        print(f"Init DB Error: {e}")
        return None

# 3. Buat Variable Global 'supabase'
# Logika: Coba pakai cache streamlit dulu, kalau gagal (misal di GitHub Actions), buat manual.
try:
    # Coba cara Streamlit
    supabase: Client = init_connection()
except:
    # Coba cara Script Python biasa (Fallback)
    try:
        _url = os.environ.get("SUPABASE_URL")
        _key = os.environ.get("SUPABASE_KEY")
        if _url and _key:
            supabase: Client = create_client(_url, _key)
        else:
            supabase = None
    except:
        supabase = None

# 4. FUNGSI TEST CONNECTION (Wajib Ada karena dipanggil main.py)
def test_connection():
    if supabase:
        try:
            # Coba query ringan (ambil 1 data user)
            supabase.table("users").select("id").limit(1).execute()
            return True, "Koneksi Berhasil! Database terhubung."
        except Exception as e:
            return False, f"Koneksi Gagal: {e}"
    else:
        return False, "Supabase Client belum terinisialisasi (Cek Secrets)."
