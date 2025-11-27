import streamlit as st
import pandas as pd
from datetime import date, timedelta
from db_connect import supabase
from prediction import calculate_prediction
from email_service import get_email_content, send_email_notification

def run_daily_automation():
    # 1. CEK KAPAN TERAKHIR JALAN
    try:
        log_res = supabase.table("system_logs").select("*").order("id", desc=True).limit(1).execute()
        if log_res.data:
            last_run = pd.to_datetime(log_res.data[0]['last_run_date']).date()
            if last_run == date.today():
                return "SUDAH_JALAN", "Tugas hari ini sudah selesai. Tidak perlu kirim ulang."
    except Exception as e:
        return "ERROR", f"Gagal cek log: {e}"

    # 2. MULAI PROSES OTOMASI
    logs_report = []
    
    # Ambil semua user
    users = supabase.table("users").select("id, full_name").execute().data
    
    for u in users:
        u_id = u['id']
        u_name = u['full_name']
        
        # Ambil data siklus user ini
        cycles = supabase.table("cycles").select("*").eq("user_id", u_id).order("start_date", desc=True).execute().data
        
        if not cycles:
            continue # Skip user yang belum pernah input data
            
        # Hitung Prediksi
        df = pd.DataFrame(cycles)
        df['start_date'] = pd.to_datetime(df['start_date'])
        
        pred_result = calculate_prediction(df)
        if not pred_result:
            continue
            
        next_haid = pred_result['next_date']
        today = date.today()
        selisih_hari = (next_haid - today).days
        
        # Ambil Aturan Notifikasi User Ini
        rules = supabase.table("notification_rules").select("*").eq("user_id", u_id).execute().data
        
        for rule in rules:
            target_days = rule['days_before'] # Misal user minta H-3
            
            # LOGIKA PENTING: Apakah hari ini adalah H-3?
            if selisih_hari == target_days:
                # Siapkan Email
                subject, body = get_email_content(rule['role'], u_name, selisih_hari, rule['custom_message'])
                
                # Kirim!
                success, msg = send_email_notification(rule['recipient_email'], subject, body)
                
                status = "BERHASIL" if success else "GAGAL"
                logs_report.append(f"User: {u_name} | Role: {rule['role']} | Status: {status}")

    # 3. CATAT LOG & UPDATE TANGGAL
    final_log = "; ".join(logs_report) if logs_report else "Tidak ada jadwal notifikasi hari ini."
    
    supabase.table("system_logs").insert({
        "last_run_date": str(date.today()),
        "logs": final_log
    }).execute()
    
    return "SUKSES", f"Otomasi selesai. {len(logs_report)} email diproses."