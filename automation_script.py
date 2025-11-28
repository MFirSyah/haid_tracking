import pandas as pd
from datetime import date
import os
# Import dari modul kita yang sudah dimodifikasi
from db_connect import supabase
from prediction import calculate_prediction
from email_service import get_email_content, send_email_notification

def run_job():
    print("🤖 MEMULAI TUGAS ROBOT HARIAN...")
    
    # 1. CEK LOG SYSTEM
    try:
        log_res = supabase.table("system_logs").select("*").order("id", desc=True).limit(1).execute()
        if log_res.data:
            last_run = pd.to_datetime(log_res.data[0]['last_run_date']).date()
            if last_run == date.today():
                print("✅ Tugas hari ini sudah dijalankan sebelumnya. Keluar.")
                return
    except Exception as e:
        print(f"⚠️ Gagal cek log, lanjut paksa: {e}")

    # 2. PROSES UTAMA
    logs_report = []
    users = supabase.table("users").select("id, full_name").execute().data
    
    if not users:
        print("Tidak ada user.")
        return

    for u in users:
        u_id = u['id']
        u_name = u['full_name']
        print(f"Memproses User: {u_name}...")
        
        cycles = supabase.table("cycles").select("*").eq("user_id", u_id).order("start_date", desc=True).execute().data
        
        if not cycles: continue
            
        df = pd.DataFrame(cycles)
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['end_date'] = pd.to_datetime(df['end_date']) # Handle end_date safe
        
        pred = calculate_prediction(df)
        if not pred: continue
            
        next_haid = pred['next_date'].date() # Convert timestamp to date
        today = date.today()
        selisih_hari = (next_haid - today).days
        
        print(f"  -> Prediksi Haid: {next_haid} (H-{selisih_hari})")
        
        rules = supabase.table("notification_rules").select("*").eq("user_id", u_id).execute().data
        
        for rule in rules:
            target_days = rule['days_before']
            
            # Kirim jika hari ini pas H-X
            if selisih_hari == target_days:
                subject, body = get_email_content(rule['role'], u_name, selisih_hari, rule['custom_message'])
                success, msg = send_email_notification(rule['recipient_email'], subject, body)
                status = "TERKIRIM" if success else "GAGAL"
                log_msg = f"User: {u_name} -> {rule['recipient_email']} ({status})"
                logs_report.append(log_msg)
                print(f"  -> {log_msg}")

    # 3. SIMPAN LOG
    final_log = "; ".join(logs_report) if logs_report else "No emails sent today."
    supabase.table("system_logs").insert({
        "last_run_date": str(date.today()),
        "logs": final_log
    }).execute()
    print("✅ OTOMASI SELESAI.")

if __name__ == "__main__":
    run_job()
