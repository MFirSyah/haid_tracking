import streamlit as st
import pandas as pd
import time
import altair as alt 
from datetime import datetime, timedelta
from db_connect import test_connection
from auth import login_user, register_user
from crud import create_cycle, get_user_cycles, delete_cycles_bulk, update_cycle_safe, add_notification_rule, get_user_notifications, update_notification_rule, delete_notification_rule
from prediction import calculate_prediction
from scheduler import run_daily_automation

st.set_page_config(page_title="Period Tracker & Support", page_icon="🩸", layout="centered")

# === SESSION TIMEOUT & SCHEDULER ===
TIMEOUT_SECONDS = 5 * 60 

if 'last_active' not in st.session_state: st.session_state['last_active'] = time.time()
current_time = time.time()
if st.session_state.get('logged_in'):
    if (current_time - st.session_state['last_active']) > TIMEOUT_SECONDS:
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = None
        st.error("Sesi habis (5 menit inaktif). Silakan login ulang.")
        st.stop()
    else:
        st.session_state['last_active'] = current_time

query_params = st.query_params
if "task" in query_params and query_params["task"] == "run_daily":
    st.write("🤖 Scheduler Aktif...")
    status, pesan = run_daily_automation()
    st.write(f"{status}: {pesan}")
    st.stop()

# --- HELPER FUNCTION: TABLE RIWAYAT EDITABLE ---
def render_history_table(df, key_prefix="dash"):
    st.subheader("📝 Riwayat & Edit Data")
    st.caption("Ubah tanggal di tabel ini lalu klik 'Simpan' untuk memperbarui grafik prediksi.")
    
    if df.empty:
        st.info("Belum ada data.")
        return

    df_display = df.copy()
    df_display['Pilih'] = False 
    
    edited_df = st.data_editor(
        df_display[['Pilih', 'id', 'start_date', 'end_date', 'mood', 'symptoms']],
        column_config={
            "id": None, 
            "Pilih": st.column_config.CheckboxColumn("Hapus?", default=False),
            "start_date": st.column_config.DateColumn("Mulai", format="DD/MM/YYYY"),
            "end_date": st.column_config.DateColumn("Selesai", format="DD/MM/YYYY"),
            "mood": st.column_config.SelectboxColumn("Mood", options=["Biasa", "Senang", "Sedih", "Marah/Sensitif", "Cemas"]),
            "symptoms": st.column_config.ListColumn("Gejala")
        },
        use_container_width=True,
        hide_index=True,
        key=f"{key_prefix}_editor"
    )

    col_btn1, col_btn2 = st.columns([1, 1])

    with col_btn1:
        if st.button("💾 Simpan Perubahan Tabel", key=f"{key_prefix}_save"):
            updated_count = 0
            for index, row in edited_df.iterrows():
                original_row = df[df['id'] == row['id']].iloc[0]
                
                new_start = row['start_date'].date() if hasattr(row['start_date'], 'date') else row['start_date']
                old_start = original_row['start_date'].date() if hasattr(original_row['start_date'], 'date') else original_row['start_date']
                
                new_end = row['end_date']
                if pd.notnull(new_end) and hasattr(new_end, 'date'): new_end = new_end.date()
                
                old_end = original_row['end_date']
                if pd.notnull(old_end) and hasattr(old_end, 'date'): old_end = old_end.date()
                
                is_changed = (new_start != old_start) or \
                             (pd.isna(new_end) != pd.isna(old_end)) or \
                             (pd.notnull(new_end) and pd.notnull(old_end) and new_end != old_end) or \
                             (row['mood'] != original_row['mood']) or \
                             (row['symptoms'] != original_row['symptoms'])

                if is_changed:
                    update_cycle_safe(row['id'], row['start_date'], row['end_date'], row['mood'], row['symptoms'])
                    updated_count += 1
            
            if updated_count > 0:
                st.success(f"{updated_count} data diperbarui! Grafik sedang dihitung ulang...")
                time.sleep(1)
                st.rerun() 
            else:
                st.info("Tidak ada perubahan data.")

    with col_btn2:
        if st.button("🗑 Hapus Data Dicentang", key=f"{key_prefix}_del"):
            rows_to_delete = edited_df[edited_df['Pilih'] == True]
            if not rows_to_delete.empty:
                ids = rows_to_delete['id'].tolist()
                success, msg = delete_cycles_bulk(ids)
                if success:
                    st.success(msg)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Centang dulu data yang mau dihapus.")

# --- MAIN APP ---

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_info' not in st.session_state: st.session_state['user_info'] = None

if not st.session_state['logged_in']:
    st.title("🩸 Period Tracker System")
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        l_email = st.text_input("Email", key="l")
        l_pass = st.text_input("Password", type="password", key="lp")
        if st.button("Login"):
            user, msg = login_user(l_email, l_pass)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['user_info'] = user
                st.session_state['last_active'] = time.time()
                st.rerun()
            else: st.error(msg)
    with tab2:
        r_n = st.text_input("Nama")
        r_e = st.text_input("Email")
        r_p = st.text_input("Password", type="password")
        if st.button("Daftar"):
            s, m = register_user(r_e, r_p, r_n)
            if s: st.success(m)
            else: st.error(m)

else:
    user = st.session_state['user_info']
    if user.get('is_admin_mode', False): st.warning("⚠️ ADMIN MODE")
    
    with st.sidebar:
        st.write(f"Halo, **{user['full_name']}**")
        nav = st.radio("Menu", ["Dashboard", "Input Haid", "Settings"])
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- 1. DASHBOARD ---
    if nav == "Dashboard":
        st.header("📊 Dashboard")
        
        # Ambil data terbaru dari DB
        df = get_user_cycles(user['id'])
        
        if not df.empty:
            # Hitung prediksi berdasarkan data terbaru
            pred = calculate_prediction(df)
            
            st.info(f"**Status:** {pred['current_phase']} | {pred['daily_message']}")
            
            chart_data = pred['chart_data']
            
            # --- LOGIKA CHART YANG LEBIH CERDAS ---
            # Menggunakan visual_last_end yang sudah diperbaiki di prediction.py
            mens_start = chart_data['last_start']
            mens_end = chart_data['last_end']
            
            # Bar Biru (Folikuler) dimulai tepat setelah Bar Merah selesai
            fol_start = mens_end
            fol_end = chart_data['fertile_start']
            
            # Validasi visual: Folikuler hanya muncul jika ada celah antara Haid dan Masa Subur
            show_follicular = fol_end > fol_start
            
            timeline_data = [
                {"Task": "Haid Terakhir", "Start": mens_start, "End": mens_end, "Color": "Menstruasi (Merah)"},
                {"Task": "Fase Folikuler", "Start": fol_start, "End": fol_end, "Color": "Folikuler (Biru)"} if show_follicular else None,
                {"Task": "Masa Subur", "Start": chart_data['fertile_start'], "End": chart_data['fertile_end'], "Color": "Subur (Hijau)"},
                {"Task": "Ovulasi", "Start": chart_data['ovulation'], "End": chart_data['ovulation'] + timedelta(hours=23), "Color": "Puncak Ovulasi (Emas)"},
                {"Task": "Prediksi Haid", "Start": chart_data['next_start'], "End": chart_data['next_start'] + timedelta(days=5), "Color": "Prediksi (Merah Pudar)"}
            ]
            
            # Bersihkan None
            timeline_data = [item for item in timeline_data if item is not None]
            
            # Render Chart
            c = alt.Chart(pd.DataFrame(timeline_data)).mark_bar().encode(
                x=alt.X('Start', axis=alt.Axis(grid=True, title="Tanggal")), 
                x2='End',
                y=alt.Y('Task', sort=None, axis=alt.Axis(grid=True)),
                color=alt.Color('Color', scale=alt.Scale(domain=['Menstruasi (Merah)', 'Folikuler (Biru)', 'Subur (Hijau)', 'Puncak Ovulasi (Emas)', 'Prediksi (Merah Pudar)'], range=['#e74c3c', '#3498db', '#2ecc71', '#f1c40f', '#fab1a0'])),
                tooltip=['Task', 'Start', 'End']
            ).properties(height=250)
            st.altair_chart(c, use_container_width=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("Prediksi Haid", pred['next_date'].strftime("%d %b"))
            c2.metric("Ovulasi", pred['ovulation_date'].strftime("%d %b"))
            c3.metric("Masa Subur", pred['fertile_window'])
            
            st.divider()
            
            # Table Editor (Untuk mengubah tanggal jika salah input)
            render_history_table(df, key_prefix="dash_hist")
            
        else:
            st.info("Data kosong. Silakan input data haid pertama Anda.")

    # --- 2. INPUT HAID ---
    elif nav == "Input Haid":
        st.header("📝 Catat Siklus Baru")
        
        with st.form("form_haid"):
            c1, c2 = st.columns(2)
            start_date = st.date_input("Tanggal Mulai *", value=None)
            end_date = st.date_input("Tanggal Selesai (Kosongkan jika masih haid)", value=None)
            
            symptoms = st.multiselect("Gejala", ["Kram", "Pusing", "Jerawat", "Mual", "Lelah"])
            mood = st.selectbox("Mood", ["Biasa", "Senang", "Sedih", "Marah/Sensitif"])
            
            if st.form_submit_button("Simpan Data Baru"):
                if start_date:
                    if end_date and end_date < start_date:
                        st.error("Tanggal selesai tidak boleh sebelum tanggal mulai.")
                    else:
                        success, msg = create_cycle(user['id'], start_date, end_date, symptoms, mood)
                        if success: 
                            st.success(msg)
                            time.sleep(1)
                            st.rerun()
                        else: st.error(msg)
                else:
                    st.error("Tanggal Mulai wajib diisi!")

        st.divider()
        # Tabel Riwayat juga ada disini biar user bisa revisi langsung
        df_fresh = get_user_cycles(user['id'])
        render_history_table(df_fresh, key_prefix="input_hist")

    # --- 3. SETTINGS ---
    elif nav == "Settings":
        st.header("⚙️ Support System")
        rules = get_user_notifications(user['id'])
        
        if rules:
            df_rules = pd.DataFrame(rules)
            edited_rules = st.data_editor(
                df_rules[['id', 'recipient_email', 'role', 'days_before', 'custom_message']],
                column_config={
                    "id": None,
                    "recipient_email": "Email (Read Only)",
                    "role": st.column_config.SelectboxColumn("Role", options=["Self", "Pacar", "Teman"]),
                    "days_before": st.column_config.NumberColumn("H-", min_value=0, max_value=14)
                },
                disabled=["recipient_email"],
                hide_index=True,
                use_container_width=True,
                key="rules_edit"
            )
            
            c1, c2 = st.columns(2)
            if c1.button("Simpan Perubahan Notif"):
                for i, row in edited_rules.iterrows():
                    update_notification_rule(row['id'], row['role'], row['days_before'], row['custom_message'])
                st.success("Tersimpan!")
                time.sleep(1)
                st.rerun()
                
            with c2:
                with st.popover("Hapus"):
                    sel = st.selectbox("Hapus Email", df_rules['recipient_email'])
                    if st.button("Konfirmasi Hapus"):
                        rid = df_rules[df_rules['recipient_email']==sel].iloc[0]['id']
                        delete_notification_rule(rid)
                        st.rerun()

        st.divider()
        with st.form("new_notif"):
            st.subheader("Tambah Kontak")
            ne = st.text_input("Email")
            nr = st.selectbox("Role", ["Self", "Pacar", "Teman"])
            nd = st.number_input("H-", 1)
            nm = st.text_input("Pesan")
            if st.form_submit_button("Tambah"):
                if ne: 
                    add_notification_rule(user['id'], ne, nr, nd, nm)
                    st.rerun()
