import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
from db_connect import supabase
from datetime import date, timedelta

# 1. TEMPLATE EMAIL BERDASARKAN ROLE
def get_email_content(role, user_name, days_left, custom_msg=""):
    subject = ""
    body = ""
    
    if role == "Self":
        subject = f"🔔 Reminder Haid: {days_left} Hari Lagi"
        body = f"""
        Hai {user_name},
        
        Berdasarkan prediksi kami, siklus haidmu akan dimulai {days_left} hari lagi.
        Jangan lupa siapkan kebutuhanmu ya!
        
        Semangat!
        - Period Tracker Bot
        """
        
    elif role == "Pacar":
        subject = f"⚠️ PMS Alert: Pasanganmu ({user_name}) H-{days_left}"
        body = f"""
        Halo Bro,
        
        Ini adalah pesan otomatis. Pasanganmu, {user_name}, diprediksi akan haid dalam {days_left} hari kedepan.
        
        Tips Survival:
        - Harap maklum jika mood berubah.
        - Siapkan cokelat atau makanan kesukaannya.
        - Hindari debat yang tidak perlu.
        
        Pesan Tambahan dari {user_name}:
        "{custom_msg if custom_msg else 'Harap bersabar ya!'}"
        
        Good luck!
        - Support System Bot
        """
        
    elif role == "Teman":
        subject = f"Info Bestie: {user_name} mau Haid"
        body = f"""
        Hi Bestie,
        
        Cuma mau ngingetin, {user_name} sepertinya bakal haid {days_left} hari lagi.
        Kalau kalian mau jalan bareng, ingetin dia bawa 'persiapan' ya.
        
        Cheers!
        """
        
    return subject, body

# 2. FUNGSI KIRIM EMAIL UTAMA
def send_email_notification(to_email, subject, html_body):
    sender_email = st.secrets["email"]["sender_email"]
    sender_password = st.secrets["email"]["sender_password"]
    
    msg = MIMEMultipart()
    msg['From'] = f"Period Tracker Bot <{sender_email}>" # Trik Display Name
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(html_body, 'plain')) # Bisa diganti 'html' kalau mau desain bagus

    try:
        # Koneksi ke Server Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        return True, "Terkirim"
    except Exception as e:
        return False, str(e)

# 3. FUNGSI TAMBAH ATURAN NOTIFIKASI KE DB
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

# 4. FUNGSI AMBIL DAFTAR NOTIFIKASI USER
def get_user_notifications(user_id):
    res = supabase.table("notification_rules").select("*").eq("user_id", user_id).execute()
    return res.data