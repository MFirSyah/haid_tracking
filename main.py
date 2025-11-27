import streamlit as st
import pandas as pd
import time
import altair as alt # Untuk visualisasi chart timeline
from datetime import datetime, timedelta
from db_connect import test_connection
from auth import login_user, register_user
from crud import create_cycle, get_user_cycles, delete_cycles_bulk, add_notification_rule, get_user_notifications, update_notification_rule, delete_notification_rule
from prediction import calculate_prediction
from scheduler import run_daily_automation

st.set_page_config(page_title="Period Tracker & Support", page_icon="🩸", layout="centered")

# === 1. FITUR SESSION TIMEOUT (5 MENIT) ===
TIMEOUT_SECONDS = 5 * 60 # 5 Menit

if 'last_active' not in st.session_state:
    st.session_state['last_active'] = time.time()

# Cek durasi inaktivitas
current_time = time.time()
if st.session_state.get('logged_in'):
    if (current_time - st.session_state['last_active']) > TIMEOUT_SECONDS:
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = None
        st.error("Sesi habis karena tidak aktif selama 5 menit. Silakan login ulang.")
        st.stop()
    else:
        # Update waktu aktif jika user melakukan sesuatu
        st.session_state['last_active'] = current_time

# === 2. PINTU RAHASIA SCHEDULER ===
query_params = st.query_params
if "task" in query_params and query_params["task"] == "run_daily":
    st.write("🤖 Robot Scheduler Aktif...")
    status, pesan = run_daily_automation()
    st.write(f"Status: {status} | {pesan}")
    st.stop()

# --- INISIALISASI SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_info' not in st.session_state: st.session_state['user_info'] = None

st.title("🩸 Period Tracker System")

# === LOGIKA TAMPILAN ===
if not st.session_state['logged_in']:
    # TAMPILAN LOGIN / REGISTER
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        l_email = st.text_input("Email", key="l_email")
        l_pass = st.text_input("Password", type="password", key="l_pass")
        if st.button("Login Masuk"):
            if l_email and l_pass:
                user, msg = login_user(l_email, l_pass)
                if user:
                    st.success(f"Welcome, {user['full_name']}!")
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = user
                    st.session_state['last_active'] = time.time() # Reset timer
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Isi semua kolom.")

    with tab2:
        r_name = st.text_input("Nama Panggilan")
        r_email = st.text_input("Email Pendaftaran")
        r_pass = st.text_input("Buat Password", type="password")
        if st.button("Daftar Sekarang"):
            if r_name and r_email and r_pass:
                success, msg = register_user(r_email, r_pass, r_name)
                if success:
                    st.success(msg)
                    st.info("Email kamu juga sudah otomatis didaftarkan sebagai penerima notifikasi.")
                else:
                    st.error(msg)
            else:
                st.warning("Wajib diisi semua.")

else:
    # TAMPILAN DASHBOARD (LOGGED IN)
    user = st.session_state['user_info']
    
    # Indikator Admin
    if user.get('is_admin_mode', False):
        st.warning(f"⚠️ ADMIN MODE: Mengakses akun {user['full_name']}")
    
    with st.sidebar:
        st.write(f"Halo, **{user['full_name']}** 👋")
        nav = st.radio("Menu", ["Dashboard", "Input Haid", "Settings"])
        st.write("---")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- MENU 1: DASHBOARD ---
    if nav == "Dashboard":
        st.header("📊 Statistik & Prediksi")
        df = get_user_cycles(user['id'])
        
        if not df.empty:
            pred = calculate_prediction(df)
            
            # 1. VISUALISASI FASE (KALENDER VISUAL)
            st.subheader(f"Status Hari Ini: {pred['current_phase']}")
            st.caption(f"💡 {pred['daily_message']}")
            
            # Persiapan data chart
            chart_data = pred['chart_data']
            timeline_data = [
                {"Task": "Haid Terakhir", "Start": chart_data['last_start'], "End": chart_data['last_start'] + timedelta(days=5), "Color": "Menstruasi (Merah)"},
                {"Task": "Fase Folikuler", "Start": chart_data['last_start'] + timedelta(days=5), "End": chart_data['fertile_start'], "Color": "Folikuler (Biru)"},
                {"Task": "Masa Subur", "Start": chart_data['fertile_start'], "End": chart_data['fertile_end'], "Color": "Subur (Hijau)"},
                {"Task": "Ovulasi", "Start": chart_data['ovulation'], "End": chart_data['ovulation'] + timedelta(hours=23), "Color": "Puncak Ovulasi (Emas)"},
                {"Task": "Prediksi Haid", "Start": chart_data['next_start'], "End": chart_data['next_start'] + timedelta(days=5), "Color": "Prediksi (Merah Pudar)"}
            ]
            df_timeline = pd.DataFrame(timeline_data)
            
            # Render Gantt Chart Sederhana pakai Altair
            c = alt.Chart(df_timeline).mark_bar().encode(
                x='Start',
                x2='End',
                y=alt.Y('Task', sort=None), # Agar urutan sesuai data
                color=alt.Color('Color', scale=alt.Scale(domain=['Menstruasi (Merah)', 'Folikuler (Biru)', 'Subur (Hijau)', 'Puncak Ovulasi (Emas)', 'Prediksi (Merah Pudar)'], range=['#e74c3c', '#3498db', '#2ecc71', '#f1c40f', '#fab1a0'])),
                tooltip=['Task', 'Start', 'End']
            ).properties(height=200)
            
            st.altair_chart(c, use_container_width=True)

            # 2. KARTU INFORMASI
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Prediksi Haid", pred['next_date'].strftime("%d %b %Y"))
            with col2:
                st.metric("Ovulasi", pred['ovulation_date'].strftime("%d %b"))
            with col3:
                st.metric("Masa Subur", pred['fertile_window'])
            
            st.divider()
            
            # 3. MANAJEMEN DATA (HAPUS PILIHAN)
            st.subheader("Riwayat Data & Edit")
            
            # Trik Hapus Data: Pakai Checkbox di Dataframe
            df_display = df.copy()
            df_display['Pilih'] = False # Kolom untuk checkbox
            
            edited_df = st.data_editor(
                df_display[['Pilih', 'start_date', 'end_date', 'mood', 'symptoms']],
                column_config={
                    "Pilih": st.column_config.CheckboxColumn("Hapus?", default=False),
                    "start_date": st.column_config.DateColumn("Mulai"),
                    "end_date": st.column_config.DateColumn("Selesai")
                },
                use_container_width=True,
                hide_index=True,
                key="data_editor"
            )
            
            # Tombol Eksekusi Hapus
            if st.button("🗑 Hapus Data Yang Dicentang"):
                # Cari baris yang dicentang di edited_df
                # Karena urutan sama, kita bisa ambil ID dari df asli berdasarkan index
                rows_to_delete = edited_df[edited_df['Pilih'] == True].index.tolist()
                
                if rows_to_delete:
                    ids_to_delete = df.iloc[rows_to_delete]['id'].tolist()
                    success, msg = delete_cycles_bulk(ids_to_delete)
                    if success:
                        st.success(msg)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Belum ada data yang dicentang.")
                    
        else:
            st.info("Belum ada data. Yuk input dulu!")

    # --- MENU 2: INPUT HAID ---
    elif nav == "Input Haid":
        st.header("📝 Catat Siklus Baru")
        with st.form("form_haid"):
            col1, col2 = st.columns(2)
            # Mandatory Input
            start_date = st.date_input("Tanggal Mulai *", value=None)
            end_date = st.date_input("Tanggal Selesai *", value=None)
            
            symptoms = st.multiselect("Gejala", ["Kram", "Pusing", "Jerawat", "Mual", "Lelah", "Nyeri Pinggang"])
            mood = st.selectbox("Mood", ["Biasa", "Senang", "Sedih", "Marah/Sensitif", "Cemas"])
            
            if st.form_submit_button("Simpan Data"):
                # Validasi Mandatory
                if start_date and end_date:
                    if end_date < start_date:
                        st.error("Tanggal Selesai tidak boleh sebelum Tanggal Mulai.")
                    else:
                        success, msg = create_cycle(user['id'], start_date, end_date, symptoms, mood)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                else:
                    st.error("⚠️ Tanggal Mulai dan Tanggal Selesai WAJIB diisi.")

    # --- MENU 3: SETTINGS (EDIT NOTIFIKASI) ---
    elif nav == "Settings":
        st.header("⚙️ Support System (Notifikasi)")
        
        # 1. TABEL DAFTAR & EDIT
        st.subheader("Kelola Daftar Penerima")
        rules = get_user_notifications(user['id'])
        
        if rules:
            df_rules = pd.DataFrame(rules)
            # Setup editor agar kolom tertentu bisa diedit
            edited_rules = st.data_editor(
                df_rules[['id', 'recipient_email', 'role', 'days_before', 'custom_message']],
                column_config={
                    "id": None, # Sembunyikan ID
                    "recipient_email": "Email Penerima (Read Only)",
                    "role": st.column_config.SelectboxColumn("Role", options=["Self", "Pacar", "Teman"]),
                    "days_before": st.column_config.NumberColumn("H- Berapa?", min_value=0, max_value=14),
                    "custom_message": "Pesan Custom"
                },
                disabled=["recipient_email"], # Email gabisa diedit, harus hapus bikin baru
                hide_index=True,
                use_container_width=True,
                key="rules_editor"
            )
            
            col_act1, col_act2 = st.columns(2)
            
            # Tombol Simpan Perubahan
            if col_act1.button("Simpan Perubahan Tabel"):
                # Kita loop untuk update (sederhana)
                errors = 0
                for index, row in edited_rules.iterrows():
                    res = update_notification_rule(row['id'], row['role'], row['days_before'], row['custom_message'])
                    if not res: errors += 1
                
                if errors == 0: st.success("Semua perubahan berhasil disimpan!")
                else: st.warning("Beberapa data gagal update.")
            
            # Tombol Hapus (Manual Input ID karena Data Editor delete row butuh callback kompleks)
            with col_act2:
                with st.popover("Hapus Kontak"):
                    rule_to_del = st.selectbox("Pilih Email untuk Dihapus", df_rules['recipient_email'])
                    if st.button("Konfirmasi Hapus"):
                        # Cari ID nya
                        id_del = df_rules[df_rules['recipient_email'] == rule_to_del].iloc[0]['id']
                        success, msg = delete_notification_rule(id_del)
                        if success:
                            st.rerun()
                            
        else:
            st.info("Belum ada kontak terdaftar.")

        st.divider()
        
        # 2. TAMBAH KONTAK BARU
        st.subheader("Tambah Kontak Baru")
        with st.form("add_contact"):
            c_email = st.text_input("Email")
            c_role = st.selectbox("Role", ["Self", "Pacar", "Teman"])
            c_days = st.number_input("H- Berapa?", 1)
            c_msg = st.text_input("Pesan")
            
            if st.form_submit_button("Tambah"):
                if c_email:
                    add_notification_rule(user['id'], c_email, c_role, c_days, c_msg)
                    st.rerun()
