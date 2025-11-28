import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
import os
from db_connect import supabase

# Helper Secret
def get_secret(key_parent, key_child):
    try:
        return st.secrets[key_parent][key_child]
    except:
        return os.environ.get(f"{key_parent.upper()}_{key_child.upper()}")

# ... (Fungsi get_email_content TETAP SAMA, tidak perlu diubah) ...
# Copy paste fungsi get_email_content dari kode sebelumnya disini
def get_email_content(role, user_name, days_left, custom_msg=""):
    subject = ""
    body = ""
    if role == "Self":
        subject = f"🔔 Reminder Haid: {days_left} Hari Lagi"
        body = f"Hai {user_name},\n\nPrediksi haidmu {days_left} hari lagi.\n- Period Tracker Bot"
    elif role == "Pacar":
        subject = f"⚠️ PMS Alert: {user_name} H-{days_left}"
        body = f"Halo Bro,\n\n{user_name} diprediksi haid {days_left} hari lagi.\nMsg: {custom_msg}\n- Support Bot"
    elif role == "Teman":
        subject = f"Info Bestie: {user_name}"
        body = f"Hi Bestie,\n\n{user_name} haid {days_left} hari lagi.\nCheers!"
    return subject, body

def send_email_notification(to_email, subject, html_body):
    # Ambil credentials secara dinamis
    sender_email = get_secret("email", "sender_email")
    sender_password = get_secret("email", "sender_password")
    
    if not sender_email or not sender_password:
        return False, "Kredensial Email tidak ditemukan di Secrets/Env"

    msg = MIMEMultipart()
    msg['From'] = f"Period Tracker Bot <{sender_email}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        return True, "Terkirim"
    except Exception as e:
        return False, str(e)

# ... (Fungsi add/get notification TETAP SAMA) ...
def add_notification_rule(user_id, email, role, days_before, custom_msg):
    try:
        data = {"user_id": user_id, "recipient_email": email, "role": role, "days_before": days_before, "custom_message": custom_msg}
        supabase.table("notification_rules").insert(data).execute()
        return True, "OK"
    except Exception as e: return False, str(e)

def get_user_notifications(user_id):
    res = supabase.table("notification_rules").select("*").eq("user_id", user_id).execute()
    return res.data

def update_notification_rule(rid, role, days, msg):
    try:
        supabase.table("notification_rules").update({"role":role, "days_before":days, "custom_message":msg}).eq("id", rid).execute()
        return True
    except: return False

def delete_notification_rule(rid):
    try:
        supabase.table("notification_rules").delete().eq("id", rid).execute()
        return True, "OK"
    except: return False, "Error"
