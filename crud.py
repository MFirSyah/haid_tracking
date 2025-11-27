import streamlit as st
import pandas as pd
from db_connect import supabase

# === BAGIAN 1: CYCLES (DATA HAID) ===

# CREATE: Tambah Data Siklus Baru
def create_cycle(user_id, start_date, end_date, symptoms, mood):
    try:
        data = {
            "user_id": user_id,
            "start_date": str(start_date),
            "end_date": str(end_date), # Sekarang wajib string, bukan None
            "symptoms": symptoms,
            "mood": mood
        }
        supabase.table("cycles").insert(data).execute()
        return True, "Data haid berhasil disimpan!"
    except Exception as e:
        return False, f"Gagal menyimpan: {e}"

# READ: Ambil Semua Riwayat Haid User
def get_user_cycles(user_id):
    try:
        response = supabase.table("cycles").select("*").eq("user_id", user_id).order("start_date", desc=True).execute()
        data = response.data
        if data:
            df = pd.DataFrame(data)
            df['start_date'] = pd.to_datetime(df['start_date'])
            df['end_date'] = pd.to_datetime(df['end_date'])
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error mengambil data: {e}")
        return pd.DataFrame()

# DELETE: Hapus Data Spesifik (Berdasarkan List ID yang dicentang)
def delete_cycles_bulk(cycle_ids):
    try:
        # Menghapus banyak ID sekaligus
        supabase.table("cycles").delete().in_("id", cycle_ids).execute()
        return True, f"{len(cycle_ids)} data berhasil dihapus."
    except Exception as e:
        return False, f"Gagal hapus: {e}"

# === BAGIAN 2: NOTIFICATION RULES (SUPPORT SYSTEM) ===

# CREATE: Tambah Aturan Notifikasi
def add_notification_rule(user_id, email, role, days_before, custom_msg):
    try:
        data = {
            "user_id": user_id,
            "recipient_email": email,
            "role": role,
            "days_before": days_before,
            "custom_message": custom_msg
        }
        supabase.table("notification_rules").insert(data).execute()
        return True, "Support System berhasil ditambahkan!"
    except Exception as e:
        return False, f"Error DB: {e}"

# READ: Ambil Data Notifikasi
def get_user_notifications(user_id):
    res = supabase.table("notification_rules").select("*").eq("user_id", user_id).execute()
    return res.data

# UPDATE: Edit Notifikasi (Misal ganti H- atau pesan)
def update_notification_rule(rule_id, new_role, new_days, new_msg):
    try:
        supabase.table("notification_rules").update({
            "role": new_role,
            "days_before": new_days,
            "custom_message": new_msg
        }).eq("id", rule_id).execute()
        return True, "Update berhasil."
    except Exception as e:
        return False, f"Gagal update: {e}"

# DELETE: Hapus Notifikasi
def delete_notification_rule(rule_id):
    try:
        supabase.table("notification_rules").delete().eq("id", rule_id).execute()
        return True, "Aturan dihapus."
    except Exception as e:
        return False, f"Gagal hapus: {e}"
