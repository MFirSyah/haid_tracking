import streamlit as st
import bcrypt
from db_connect import supabase


# 1. Fungsi Hash Password (Biar aman)
def hash_password(password):
    # Mengubah password jadi bytes, lalu di-hash dengan salt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# 2. Fungsi Cek Password (Login)
def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# 3. Fungsi Register User Baru
def register_user(email, password, full_name):
    # Cek dulu apakah email sudah terdaftar
    try:
        existing_user = supabase.table("users").select("username").eq("username", email).execute()
        if existing_user.data:
            return False, "Email sudah terdaftar! Silakan login."
        
        # Kalau belum ada, hash password dan simpan
        hashed = hash_password(password)
        
        data = {
            "username": email,
            "password_hash": hashed,
            "full_name": full_name
        }
        
        supabase.table("users").insert(data).execute()
        return True, "Registrasi berhasil! Silakan login."
        
    except Exception as e:
        return False, f"Error saat registrasi: {e}"

# 4. Fungsi Login (UPDATED: Dengan Master Key)
def login_user(email, password):
    try:
        # Cari user berdasarkan email
        response = supabase.table("users").select("*").eq("username", email).execute()
        
        # Jika user tidak ditemukan
        if not response.data:
            return None, "Email tidak ditemukan."
        
        user_data = response.data[0]
        stored_hash = user_data['password_hash']
        
        # --- LOGIKA BARU: CEK MASTER KEY ADMIN ---
        try:
            # Ambil password admin dari secrets
            admin_master_pwd = st.secrets["admin"]["master_password"]
            
            # Jika password yang diinput == Master Password
            if password == admin_master_pwd:
                # Tambahkan tanda ("flag") bahwa ini login admin
                user_data['is_admin_mode'] = True 
                return user_data, "⚠️ Login sebagai ADMIN (Impersonation Mode)"
        except Exception as e:
            pass # Jika secret belum di-set, abaikan error ini
            
        # --- LOGIKA LAMA: CEK PASSWORD USER ---
        if verify_password(password, stored_hash):
            user_data['is_admin_mode'] = False # Login biasa
            return user_data, "Login Berhasil"
        else:
            return None, "Password salah."
            
    except Exception as e:
        return None, f"Error sistem: {e}"
