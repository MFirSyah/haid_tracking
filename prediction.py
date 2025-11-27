import pandas as pd
import numpy as np
from datetime import timedelta

def calculate_prediction(df):
    """
    Menerima DataFrame history haid user.
    Mengembalikan dictionary berisi tanggal prediksi, margin error, dan status.
    """
    
    # 1. PERSIAPAN DATA
    # Pastikan data ada minimal 1 record
    if df.empty:
        return None
    
    # Urutkan dari tanggal terlama ke terbaru
    df = df.sort_values('start_date', ascending=True)
    
    # Hitung selisih hari antar haid (Cycle Length)
    df['cycle_length'] = df['start_date'].diff().dt.days
    
    # Hapus baris pertama karena pasti NaN
    valid_cycles = df.dropna(subset=['cycle_length'])
    
    cycle_data = valid_cycles['cycle_length']
    last_period_date = df.iloc[-1]['start_date']
    
    # --- LOGIKA 1: COLD START (DATA SEDIKIT) ---
    if len(cycle_data) < 2:
        predicted_days = 28
        margin_error = 2 
        method = "Medis Standar (Data Kurang)"
        
    else:
        # --- LOGIKA 2: HYBRID MODEL (DATA CUKUP) ---
        
        # A. IQR FILTER 
        Q1 = cycle_data.quantile(0.25)
        Q3 = cycle_data.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        clean_data = cycle_data[(cycle_data >= lower_bound) & (cycle_data <= upper_bound)]
        
        if clean_data.empty:
            clean_data = cycle_data
            
        # B. EWMA 
        predicted_days = clean_data.ewm(span=3).mean().iloc[-1]
        
        # C. STANDARD DEVIATION
        std_dev = clean_data.std()
        if np.isnan(std_dev): std_dev = 1.5
        
        margin_error = round(std_dev)
        method = "Smart Hybrid AI"

    # --- HASIL AKHIR ---
    next_date = last_period_date + timedelta(days=round(predicted_days))
    
    return {
        "next_date": next_date.date(),
        "cycle_avg": round(predicted_days),
        "margin_error": margin_error,
        "method": method
    }
