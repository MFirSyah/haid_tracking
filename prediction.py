import pandas as pd
import numpy as np
from datetime import timedelta, date

def calculate_prediction(df):
    """
    Menghitung prediksi haid, ovulasi, dan masa subur.
    Menangani kasus haid sedang berlangsung (end_date kosong).
    """
    if df.empty:
        return None
    
    # Sort data
    df = df.sort_values('start_date', ascending=True)
    
    # Ambil data siklus terakhir (Raw Data) untuk cek status hari ini
    last_record = df.iloc[-1]
    last_start_date = last_record['start_date']
    last_end_date = last_record['end_date'] # Bisa NaT (Not a Time) / None
    
    # Hitung durasi antar siklus (Cycle Length) untuk prediksi
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
    ovulation_date = next_date - timedelta(days=14)
    fertile_start = ovulation_date - timedelta(days=5)
    fertile_end = ovulation_date + timedelta(days=1)
    
    # --- CEK FASE HARI INI ---
    today_ts = pd.to_datetime("today")
    today = today_ts.date()
    
    next_date_d = next_date.date()
    fertile_start_d = fertile_start.date()
    fertile_end_d = fertile_end.date()
    last_start_d = last_start_date.date()
    
    # Handle end_date jika kosong (anggap belum selesai)
    is_ongoing = pd.isnull(last_end_date)
    
    current_phase = "Fase Folikuler (Normal)"
    message = "Tubuhmu sedang bersiap untuk siklus baru."
    
    # LOGIKA BARU: Tentukan Tanggal Selesai untuk Visualisasi Chart
    # Jika user sudah input tanggal selesai, pakai itu.
    # Jika belum (ongoing), pakai estimasi (misal Start + 5 hari) untuk visualisasi sementara.
    if is_ongoing:
        visual_last_end = last_start_date + timedelta(days=5)
    else:
        visual_last_end = last_end_date

    # 1. Cek apakah sedang haid (Ongoing atau dalam range tanggal)
    is_menstruating = False
    
    if is_ongoing:
        # Jika end_date kosong, cek apakah start_date baru saja terjadi (misal < 10 hari lalu)
        days_since_start = (today_ts - last_start_date).days
        if 0 <= days_since_start <= 14: # Diperlebar jadi 14 hari jaga-jaga haid panjang
            current_phase = "Sedang Haid (Menstruasi) 🩸"
            message = "Jangan lupa update tanggal selesai jika haid sudah berhenti ya!"
            is_menstruating = True
    else:
        # Jika end_date ada, cek apakah hari ini masih di antara start dan end
        last_end_d = last_end_date.date()
        if last_start_d <= today <= last_end_d:
            current_phase = "Sedang Haid (Menstruasi) 🩸"
            message = "Istirahat yang cukup dan minum air putih."
            is_menstruating = True

    # 2. Jika TIDAK haid, baru cek fase lain
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
        elif today < fertile_start_d and today > last_start_d:
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
            "last_end": visual_last_end, # INI YANG DIPERBAIKI (Pakai data real)
            "fertile_start": fertile_start,
            "fertile_end": fertile_end,
            "ovulation": ovulation_date,
            "next_start": next_date
        }
    }
