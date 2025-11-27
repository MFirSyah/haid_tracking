import streamlit as st
import pandas as pd
from db_connect import supabase

# --- CYCLE CRUD ---

def create_cycle(user_id, start_date, end_date, symptoms, mood):
    try:
        data = {
            "user_id": user_id,
            "start_date": str(start_date),
            "end_date": str(end_date) if end_date else None, # Handle None
            "symptoms": symptoms,
            "mood": mood
        }
        supabase.table("cycles").insert(data).execute()
        return True, "Data haid berhasil disimpan!"
    except Exception as e:
        return False, f"Gagal menyimpan: {e}"

def get_user_cycles(user_id):
    try:
        response = supabase.table("cycles").select("*").eq("user_id", user_id).order("start_date", desc=True).execute()
        data = response.data
        if data:
            df = pd.DataFrame(data)
            df['start_date'] = pd.to_datetime(df['start_date'])
            df['end_date'] = pd.to_datetime(df['end_date'])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error mengambil data: {e}")
        return pd.DataFrame()

# FITUR BARU: Update Data (Edit Table)
def update_cycle_safe(cycle_id, start_date, end_date, mood, symptoms):
    try:
        data = {
            "start_date": str(start_date),
            "end_date": str(end_date) if not pd.isnull(end_date) else None,
            "mood": mood,
            "symptoms": symptoms
        }
        supabase.table("cycles").update(data).eq("id", cycle_id).execute()
        return True
    except Exception as e:
        return False

# FITUR BARU: Hapus Banyak Data Sekaligus
def delete_cycles_bulk(list_of_ids):
    try:
        # Menghapus data dimana ID ada di dalam list_of_ids
        supabase.table("cycles").delete().in_("id", list_of_ids).execute()
        return True, f"{len(list_of_ids)} data berhasil dihapus."
    except Exception as e:
        return False, f"Gagal hapus: {e}"

# --- NOTIFICATION CRUD ---

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
        return True, "Kontak berhasil ditambahkan!"
    except Exception as e:
        return False, f"Error DB: {e}"

def get_user_notifications(user_id):
    res = supabase.table("notification_rules").select("*").eq("user_id", user_id).order("id", desc=True).execute()
    return res.data

def update_notification_rule(rule_id, role, days_before, custom_msg):
    try:
        data = {
            "role": role,
            "days_before": days_before,
            "custom_message": custom_msg
        }
        supabase.table("notification_rules").update(data).eq("id", rule_id).execute()
        return True
    except Exception as e:
        return False

def delete_notification_rule(rule_id):
    try:
        supabase.table("notification_rules").delete().eq("id", rule_id).execute()
        return True, "Kontak dihapus."
    except Exception as e:
        return False, f"Gagal hapus: {e}"
