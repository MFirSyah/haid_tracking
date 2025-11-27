import streamlit as st
import bcrypt
from db_connect import supabase

# 1. Fungsi Hash Password
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# 2. Fungsi Cek Password
def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# 3. Fungsi Register User Baru (UPDATED: Auto Add Self Notification)
def register_user(email, password, full_name):
    try:
        # Cek email duplikat
        existing_user = supabase.table("users").select("username").eq("username", email).execute()
        if existing_user.data:
            return False, "Email sudah terdaftar! Silakan login."
        
        hashed = hash_password(password)
        
        # Insert User
        user_data = {
            "username": email,
            "password_hash": hashed,
            "full_name": full_name
        }
        user_res = supabase.table("users").insert(user_data).select().execute()
        
        # --- FITUR BARU: AUTO ADD SELF NOTIFICATION ---
        if user_res.data:
            new_user_id = user_res.data[0]['id']
            # Masukkan aturan notifikasi default untuk diri sendiri
            notif_data = {
                "user_id": new_user_id,
                "recipient_email": email,
                "role": "Self",
                "days_before": 1, # Default H-1
                "custom_message": "Jangan lupa update mood kamu ya!"
            }
            supabase.table("notification_rules").insert(notif_data).execute()

        return True, "Registrasi berhasil! Notifikasi diri sendiri juga sudah aktif."
        
    except Exception as e:
        return False, f"Error saat registrasi: {e}"

# 4. Fungsi Login (UPDATED: Admin Impersonation)
def login_user(email, password):
    try:
        response = supabase.table("users").select("*").eq("username", email).execute()
        
        if not response.data:
            return None, "Email tidak ditemukan."
        
        user_data = response.data[0]
        stored_hash = user_data['password_hash']
        
        # Cek Admin Master Password
        try:
            admin_master_pwd = st.secrets["admin"]["master_password"]
            if password == admin_master_pwd:
                user_data['is_admin_mode'] = True 
                return user_data, "⚠️ Login sebagai ADMIN (Impersonation Mode)"
        except:
            pass
            
        # Cek Password Biasa
        if verify_password(password, stored_hash):
            user_data['is_admin_mode'] = False
            return user_data, "Login Berhasil"
        else:
            return None, "Password salah."
            
    except Exception as e:
        return None, f"Error sistem: {e}"
