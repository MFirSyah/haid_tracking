import pandas as pd
import numpy as np
from datetime import timedelta

def calculate_prediction(df):
    """
    Mengembalikan prediksi haid berikutnya DAN masa subur.
    """
    
    # PERSIAPAN DATA
    if df.empty:
        return None
    
    df = df.sort_values('start_date', ascending=True)
    df['cycle_length'] = df['start_date'].diff().dt.days
    
    # Bersihkan data (Hapus baris pertama yg NaT)
    valid_cycles = df.dropna(subset=['cycle_length'])
    cycle_data = valid_cycles['cycle_length']
    last_period_date = df.iloc[-1]['start_date']
    
    # --- LOGIKA PREDIKSI SIKLUS (Sama seperti sebelumnya) ---
    if len(cycle_data) < 2:
        predicted_cycle_days = 28
        margin_error = 2
        method = "Medis Standar (Data Kurang)"
    else:
        # IQR Filter
        Q1 = cycle_data.quantile(0.25)
        Q3 = cycle_data.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        
        clean_data = cycle_data[(cycle_data >= lower) & (cycle_data <= upper)]
        if clean_data.empty: clean_data = cycle_data
            
        # EWMA
        predicted_cycle_days = clean_data.ewm(span=3).mean().iloc[-1]
        
        std_dev = clean_data.std()
        if np.isnan(std_dev): std_dev = 1.5
        margin_error = round(std_dev)
        method = "Smart Hybrid AI"

    # --- HASIL PREDIKSI TANGGAL HAID ---
    cycle_days_int = round(predicted_cycle_days)
    next_period_date = last_period_date + timedelta(days=cycle_days_int)
    
    # --- LOGIKA MASA SUBUR (OVULASI) ---
    # Ovulasi biasanya terjadi 14 hari SEBELUM haid berikutnya
    ovulation_date = next_period_date - timedelta(days=14)
    
    # Masa subur (Fertile Window) biasanya H-2 sampai H+2 dari Ovulasi
    fertile_start = ovulation_date - timedelta(days=2)
    fertile_end = ovulation_date + timedelta(days=2)
    
    return {
        "next_date": next_period_date.date(),
        "cycle_avg": cycle_days_int,
        "margin_error": margin_error,
        "method": method,
        # Data Baru: Masa Subur
        "ovulation_date": ovulation_date.date(),
        "fertile_window": f"{fertile_start.strftime('%d %b')} - {fertile_end.strftime('%d %b')}"
    }
