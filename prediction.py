import pandas as pd
import numpy as np
from datetime import timedelta, date

def calculate_prediction(df):
    """
    Menghitung prediksi haid, ovulasi, dan masa subur.
    Prioritas Visualisasi: Gunakan data aktual user jika ada, baru estimasi jika kosong.
    """
    if df.empty:
        return None
    
    # 1. Pastikan urutan data benar (Start Date terlama ke terbaru)
    df = df.sort_values('start_date', ascending=True)
    
    # Ambil data siklus terakhir
    last_record = df.iloc[-1]
    last_start_date = last_record['start_date']
    last_end_date = last_record['end_date'] # Bisa NaT (Not a Time) / None
    
    # Hitung durasi antar siklus (Cycle Length) untuk prediksi bulan depan
    # Logika: Siklus dihitung dari Start ke Start.
    df['cycle_length'] = df['start_date'].diff().dt.days
    valid_cycles = df.dropna(subset=['cycle_length'])
    cycle_data = valid_cycles['cycle_length']
    
    # --- LOGIKA HYBRID (PREDIKSI ANGKA) ---
    if len(cycle_data) < 2:
        predicted_days = 28
        margin_error = 2
        method = "Medis Standar"
    else:
        # IQR Filter & EWMA Logic
        Q1 = cycle_data.quantile(0.25)
        Q3 = cycle_data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        clean_data = cycle_data[(cycle_data >= lower_bound) & (cycle_data <= upper_bound)]
        if clean_data.empty: clean_data = cycle_data
            
        predicted_days = clean_data.ewm(span=3).mean().iloc[-1]
        std_dev = clean_data.std()
        if np.isnan(std_dev): std_dev = 1.5
        margin_error = round(std_dev)
        method = "Smart Hybrid AI"

    # --- HASIL UTAMA ---
    avg_cycle = round(predicted_days)
    next_date = last_start_date + timedelta(days=avg_cycle)
    
    # --- HASIL MASA SUBUR (FERTILE WINDOW) ---
    # Ovulasi terjadi 14 hari SEBELUM haid berikutnya
    ovulation_date = next_date - timedelta(days=14)
    fertile_start = ovulation_date - timedelta(days=5)
    fertile_end = ovulation_date + timedelta(days=1)
    
    # --- LOGIKA VISUALISASI (PERBAIKAN DISINI) ---
    # Cek apakah End Date valid (tidak NaT/None)
    is_end_date_valid = pd.notnull(last_end_date)
    
    if is_end_date_valid:
        # KASUS 1: User sudah input/edit tanggal selesai
        visual_last_end = last_end_date
        is_ongoing = False 
    else:
        # KASUS 2: Belum input tanggal selesai (Masih haid/lupa input)
        # Estimasi default 5 hari visualisasi
        visual_last_end = last_start_date + timedelta(days=5)
        is_ongoing = True

    # --- CEK FASE HARI INI ---
    today_ts = pd.to_datetime("today")
    today = today_ts.date()
    
    next_date_d = next_date.date()
    fertile_start_d = fertile_start.date()
    fertile_end_d = fertile_end.date()
    last_start_d = last_start_date.date()
    visual_last_end_d = visual_last_end.date()

    current_phase = "Fase Folikuler (Normal)"
    message = "Tubuhmu sedang bersiap untuk siklus baru."
    
    is_menstruating = False
    
    # Logika status teks
    if is_ongoing:
        # Jika belum ada end date, cek durasi hari berjalan
        days_since_start = (today_ts - last_start_date).days
        if 0 <= days_since_start <= 14:
            current_phase = "Sedang Haid (Menstruasi) 🩸"
            message = "Jangan lupa update tanggal selesai di tabel riwayat ya!"
            is_menstruating = True
    else:
        # Jika sudah ada end date, cek range tanggal
        if last_start_d <= today <= visual_last_end_d:
            current_phase = "Sedang Haid (Menstruasi) 🩸"
            message = "Istirahat yang cukup dan minum air putih."
            is_menstruating = True

    if not is_menstruating:
        if fertile_start_d <= today <= fertile_end_d:
            current_phase = "Masa Subur 🌸"
            message = "Peluang hamil tinggi. Kamu mungkin merasa lebih energik!"
            if today == ovulation_date.date():
                current_phase = "PUNCAK OVULASI 🥚"
                message = "Hari ini puncak kesuburan! Mood biasanya sangat bagus."
        elif today >= next_date_d - timedelta(days=3):
            current_phase = "Fase Luteal (PMS) ⚠️"
            message = "Mood mungkin agak berantakan menjelang haid."
        elif today < fertile_start_d and today > visual_last_end_d:
            current_phase = "Fase Folikuler 🌱"
            message = "Energi mulai naik setelah haid selesai."

    return {
        "next_date": next_date, 
        "cycle_avg": avg_cycle,
        "margin_error": margin_error,
        "method": method,
        "ovulation_date": ovulation_date,
        "fertile_window": f"{fertile_start.strftime('%d %b')} - {fertile_end.strftime('%d %b')}",
        "current_phase": current_phase,
        "daily_message": message,
        "chart_data": {
            "last_start": last_start_date,
            "last_end": visual_last_end, # Ini sekarang pasti mengikuti inputan user jika ada
            "fertile_start": fertile_start,
            "fertile_end": fertile_end,
            "ovulation": ovulation_date,
            "next_start": next_date
        }
    }
