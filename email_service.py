import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

# 1. TEMPLATE EMAIL BERDASARKAN ROLE
def get_email_content(role, user_name, days_left, custom_msg=""):
    subject = ""
    body = ""
    
    if role == "Self":
        subject = f"🔔 Reminder Haid: {days_left} Hari Lagi"
        body = f"""
        Hai {user_name},
        
        Ini reminder otomatis. Siklus haidmu diprediksi mulai {days_left} hari lagi.
        Jangan lupa siapkan kebutuhanmu & update mood di aplikasi.
        
        Semangat!
        - Period Tracker Bot
        """
        
    elif role == "Pacar":
        subject = f"⚠️ PMS Alert: {user_name} H-{days_left}"
        body = f"""
        Halo Bro,
        
        Bot mau kasih tau, pasanganmu ({user_name}) diprediksi haid {days_left} hari lagi.
        
        Tips:
        - Sabar kalau dia badmood.
        - Siapkan cokelat/makanan enak.
        
        Pesan dari {user_name}:
        "{custom_msg if custom_msg else 'Mohon pengertiannya ya!'}"
        
        Good luck!
        - Support System Bot
        """
        
    elif role == "Teman":
        subject = f"Info Bestie: {user_name} mau Haid"
        body = f"""
        Hi Bestie,
        
        Reminder nih, {user_name} kayaknya bakal haid {days_left} hari lagi.
        Ingetin dia bawa 'persiapan' kalau kalian mau hangout.
        
        Cheers!
        """
        
    return subject, body

# 2. FUNGSI KIRIM EMAIL UTAMA
def send_email_notification(to_email, subject, html_body):
    try:
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        
        msg = MIMEMultipart()
        msg['From'] = f"Period Tracker Bot <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'plain')) 

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        return True, "Terkirim"
    except Exception as e:
        return False, str(e)
