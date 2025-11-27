import pandas as pd
import numpy as np
from datetime import timedelta, date

def calculate_prediction(df):
    """
    Menghitung prediksi haid, ovulasi, dan masa subur.
    """
    if df.empty:
        return None
    
    # Sort data
    df = df.sort_values('start_date', ascending=True)
    df['cycle_length'] = df['start_date'].diff().dt.days
    valid_cycles = df.dropna(subset=['cycle_length'])
    cycle_data = valid_cycles['cycle_length']
    last_period_date = df.iloc[-1]['start_date']
    
    # --- LOGIKA HYBRID ---
    if len(cycle_data) < 2:
        predicted_days = 28
        margin_error = 2
        method = "Medis Standar"
    else:
        # IQR Filter
        Q1 = cycle_data.quantile(0.25)
        Q3 = cycle_data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        clean_data = cycle_data[(cycle_data >= lower_bound) & (cycle_data <= upper_bound)]
        if clean_data.empty: clean_data = cycle_data
            
        # EWMA
        predicted_days = clean_data.ewm(span=3).mean().iloc[-1]
        std_dev = clean_data.std()
        if np.isnan(std_dev): std_dev = 1.5
        margin_error = round(std_dev)
        method = "Smart Hybrid AI"

    # --- HASIL UTAMA ---
    avg_cycle = round(predicted_days)
    next_date = last_period_date + timedelta(days=avg_cycle)
    
    # --- HASIL MASA SUBUR (FERTILE WINDOW) ---
    # Ovulasi biasanya terjadi 14 hari SEBELUM haid berikutnya
    ovulation_date = next_date - timedelta(days=14)
    
    # Masa subur: 5 hari sebelum ovulasi sampai 1 hari setelahnya
    fertile_start = ovulation_date - timedelta(days=5)
    fertile_end = ovulation_date + timedelta(days=1)
    
    # Cek Fase Hari Ini
    today = pd.to_datetime("today").date() # Pastikan tipe date (bukan timestamp)
    
    # Konversi semua ke .date() untuk perbandingan aman
    next_date_d = next_date.date()
    ovulation_date_d = ovulation_date.date()
    fertile_start_d = fertile_start.date()
    fertile_end_d = fertile_end.date()
    last_period_d = last_period_date.date()
    
    current_phase = "Fase Folikuler (Normal)"
    message = "Tubuhmu sedang bersiap untuk siklus baru."
    
    if fertile_start_d <= today <= fertile_end_d:
        current_phase = "Masa Subur 🌸"
        message = "Peluang hamil tinggi. Kamu mungkin merasa lebih energik dan menarik!"
        if today == ovulation_date_d:
            current_phase = "PUNCAK OVULASI 🥚"
            message = "Hari ini adalah puncak kesuburanmu! Ceria banget dong hari ini!"
    elif today >= next_date_d - timedelta(days=3): # H-3 Haid
        current_phase = "Fase Luteal (PMS) ⚠️"
        message = "Siap-siap ya, mungkin mood agak berantakan menjelang haid."
    elif today < fertile_start_d and today > last_period_d:
        current_phase = "Fase Folikuler 🌱"
        message = "Energi mulai naik setelah haid selesai."
    
    return {
        "next_date": next_date, # Masih bentuk Timestamp untuk visualisasi
        "cycle_avg": avg_cycle,
        "margin_error": margin_error,
        "method": method,
        "ovulation_date": ovulation_date,
        "fertile_window": f"{fertile_start.strftime('%d %b')} - {fertile_end.strftime('%d %b')}",
        "current_phase": current_phase,
        "daily_message": message,
        # Data tanggal mentah untuk chart
        "chart_data": {
            "last_start": last_period_date,
            "fertile_start": fertile_start,
            "fertile_end": fertile_end,
            "ovulation": ovulation_date,
            "next_start": next_date
        }
    }
