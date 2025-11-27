import streamlit as st
import pandas as pd
from db_connect import supabase

# 1. CREATE: Tambah Data Siklus Baru
def create_cycle(user_id, start_date, end_date, symptoms, mood):
    try:
        # Siapkan data dictionary
        data = {
            "user_id": user_id,
            "start_date": str(start_date), # Convert tanggal ke string biar aman
            "end_date": str(end_date) if end_date else None,
            "symptoms": symptoms, # Ini sudah bentuk List/Array
            "mood": mood
        }
        
        # Kirim ke Supabase
        supabase.table("cycles").insert(data).execute()
        return True, "Data haid berhasil disimpan!"
    except Exception as e:
        return False, f"Gagal menyimpan: {e}"

# 2. READ: Ambil Semua Riwayat Haid User
def get_user_cycles(user_id):
    try:
        # Ambil data khusus punya user yang sedang login, urutkan dari tanggal terbaru
        response = supabase.table("cycles").select("*").eq("user_id", user_id).order("start_date", desc=True).execute()
        
        data = response.data
        
        if data:
            # Ubah jadi DataFrame Pandas biar gampang diolah visualisasi
            df = pd.DataFrame(data)
            # Pastikan kolom tanggal dibaca sebagai datetime
            df['start_date'] = pd.to_datetime(df['start_date'])
            if 'end_date' in df.columns:
                df['end_date'] = pd.to_datetime(df['end_date'])
            return df
        else:
            return pd.DataFrame() # Return tabel kosong kalau belum ada data
            
    except Exception as e:
        st.error(f"Error mengambil data: {e}")
        return pd.DataFrame()

# 3. DELETE: Hapus Data (Buat jaga-jaga kalau salah input)
def delete_cycle(cycle_id):
    try:
        supabase.table("cycles").delete().eq("id", cycle_id).execute()
        return True, "Data dihapus."
    except Exception as e:
        return False, f"Gagal hapus: {e}"