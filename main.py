import streamlit as st
import time
import pandas as pd
from datetime import date

# Import modul buatan sendiri
from auth import login_user, register_user
from db_connect import supabase
from crud import create_cycle, get_user_cycles, delete_cycle
from prediction import calculate_prediction 
from email_service import add_notification_rule, get_user_notifications, send_email_notification
from scheduler import run_daily_automation 

# --- 1. KONFIGURASI HALAMAN (WAJIB PALING ATAS) ---
st.set_page_config(page_title="Period Tracker & Support", page_icon="🩸", layout="centered")

# --- 2. PINTU RAHASIA UNTUK ROBOT (UPTIMEROBOT) ---
# Kita cek apakah ada parameter '?task=run_daily' di URL
query_params = st.query_params

# Cara akses query params di Streamlit terbaru
task_param = query_params.get("task", None)

if task_param == "run_daily":
    st.write("🤖 Memulai Tugas Harian Robot...")
    
    status, pesan = run_daily_automation()
    
    if status == "SUKSES":
        st.success(pesan)
    elif status == "SUDAH_JALAN":
        st.info(pesan)
    else:
        st.error(pesan)
        
    st.stop() # PENTING: Berhenti disini, jangan load tampilan UI

# --- 3. JUDUL APLIKASI ---
st.title("🩸 Period Tracker System")
st.caption("Tracking Siklus Haid & Support System Otomatis")

# --- 4. MANAJEMEN SESI (SESSION STATE) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# --- 5. LOGIKA TAMPILAN (LOGIN vs DASHBOARD) ---

if not st.session_state['logged_in']:
    # === TAMPILAN BELUM LOGIN ===
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    # --- TAB LOGIN ---
    with tab1:
        st.subheader("Masuk ke Akun")
        l_email = st.text_input("Email", key="l_email")
        l_pass = st.text_input("Password", type="password", key="l_pass")
        
        if st.button("Login Masuk"):
            if l_email and l_pass:
                user, msg = login_user(l_email, l_pass)
                if user:
                    st.success(f"Selamat datang, {user['full_name']}!")
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = user
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Harap isi email dan password.")

    # --- TAB REGISTER ---
    with tab2:
        st.subheader("Daftar Akun Baru")
        r_name = st.text_input("Nama Panggilan", key="r_name")
        r_email = st.text_input("Email", key="r_email")
        r_pass = st.text_input("Password", type="password", key="r_pass")
        
        if st.button("Daftar Sekarang"):
            if r_name and r_email and r_pass:
                success, msg = register_user(r_email, r_pass, r_name)
                if success:
                    st.success(msg)
                    st.info("Silakan pindah ke Tab Login untuk masuk.")
                else:
                    st.error(msg)
            else:
                st.warning("Semua kolom wajib diisi.")

else:
    # === TAMPILAN SUDAH LOGIN (DASHBOARD) ===
    user = st.session_state['user_info']
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.header(f"Halo, {user['full_name']}!")
        st.write("---")
        nav = st.radio("Menu", ["Dashboard", "Input Haid", "Settings"])
        
        st.write("---")
        if st.button("Logout", type="primary"):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = None
            st.rerun()
            
    # --- HALAMAN 1: DASHBOARD ---
    if nav == "Dashboard":
        st.header("📊 Dashboard & Prediksi")
        
        # Ambil data user
        df = get_user_cycles(user['id'])
        
        if not df.empty:
            # --- PANGGIL FUNGSI PREDIKSI DISINI ---
            prediction = calculate_prediction(df)
            
            # Tampilkan Card Prediksi Utama
            st.markdown("### 🔮 Prediksi Haid Berikutnya")
            
            # Kita bagi jadi 3 kolom metrik
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                tanggal_indo = prediction['next_date'].strftime("%d %B %Y")
                st.metric(label="Tanggal Prediksi", value=tanggal_indo)
                
            with col_b:
                margin = prediction['margin_error']
                delta_color = "normal" if margin < 3 else "inverse"
                st.metric(label="Rentang Akurasi", value=f"± {margin} Hari", delta="Stabil" if margin < 3 else "Tidak Stabil", delta_color=delta_color)
                
            with col_c:
                st.metric(label="Rata-rata Siklus", value=f"{prediction['cycle_avg']} Hari", help="Dihitung menggunakan metode EWMA")

            st.caption(f"ℹ️ Metode Kalkulasi: *{prediction['method']}*")
            st.divider()

            # --- BAGIAN BAWAH: DATA HISTORIS ---
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Tren Durasi Siklus")
                df_sorted = df.sort_values('start_date', ascending=True).copy()
                df_sorted['cycle_length'] = df_sorted['start_date'].diff().dt.days
                st.line_chart(df_sorted.set_index('start_date')['cycle_length'])

            with col2:
                st.subheader("Riwayat Input")
                st.dataframe(df[['start_date', 'mood']], use_container_width=True, height=300)
                
                if st.button("Hapus Data Teratas"):
                    cycle_id_to_delete = df.iloc[0]['id']
                    success, msg = delete_cycle(cycle_id_to_delete)
                    if success:
                        st.success(msg)
                        st.rerun()

        else:
            st.info("👋 Halo! Data kamu masih kosong. Silakan ke menu 'Input Haid' untuk mulai tracking.")
            
    # --- HALAMAN 2: INPUT DATA ---
    elif nav == "Input Haid":
        st.header("📝 Catat Haid Baru")
        
        with st.form("form_haid"):
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Tanggal Mulai")
            with col2:
                end_date = st.date_input("Tanggal Selesai (Opsional)", value=None)
            
            symptoms = st.multiselect("Gejala yang dirasakan", 
                ["Kram Perut", "Pusing", "Jerawat", "Nyeri Payudara", "Lelah", "Mual", "Sakit Punggung"])
            
            mood = st.selectbox("Mood Dominan", 
                ["Senang/Biasa", "Sensitif/Mudah Marah", "Sedih/Melow", "Cemas", "Energik"])
            
            submit = st.form_submit_button("Simpan Data")
            
            if submit:
                success, msg = create_cycle(user['id'], start_date, end_date, symptoms, mood)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

    # --- HALAMAN 3: SETTINGS (SUPPORT SYSTEM) ---
    elif nav == "Settings":
        st.header("❤️ Support System & Notifikasi")
        st.write("Daftarkan orang-orang terdekatmu agar mereka tahu kapan harus support kamu.")
        
        # --- TABEL DAFTAR PENERIMA ---
        st.subheader("Daftar Penerima Aktif")
        my_rules = get_user_notifications(user['id'])
        
        if my_rules:
            clean_data = []
            for item in my_rules:
                clean_data.append({
                    "Email Penerima": item['recipient_email'],
                    "Sebagai": item['role'],
                    "Dikirim H-": f"{item['days_before']} Hari",
                    "Pesan Custom": item['custom_message']
                })
            st.table(clean_data)
        else:
            st.info("Belum ada support system.")

        st.divider()

        # --- FORM TAMBAH BARU ---
        st.subheader("Tambah Kontak Baru")
        with st.form("add_notif_form"):
            col1, col2 = st.columns(2)
            with col1:
                rec_email = st.text_input("Email Penerima")
                rec_role = st.selectbox("Sebagai Siapa?", ["Self", "Pacar", "Teman"])
            with col2:
                rec_days = st.number_input("Kirim Notifikasi H- Berapa?", min_value=0, max_value=7, value=3)
                rec_msg = st.text_input("Pesan Tambahan (Opsional)")
            
            if st.form_submit_button("Simpan Kontak"):
                if rec_email:
                    success, msg = add_notification_rule(user['id'], rec_email, rec_role, rec_days, rec_msg)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Email wajib diisi.")

        st.divider()
        with st.expander("🛠 Test Kirim Email (Untuk Debugging)"):
            test_email = st.text_input("Masukkan email tujuan test")
            if st.button("Kirim Test Email"):
                sukses, info = send_email_notification(test_email, "Test Dari Bot", "Halo! Ini tes email period tracker.")
                if sukses:
                    st.success("Email berhasil terkirim! Cek inbox/spam.")
                else:
                    st.error(f"Gagal: {info}")