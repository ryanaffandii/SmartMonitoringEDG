import pandas as pd
import numpy as np
import streamlit as st

def load_css():
    """
    Returns the custom CSS string for the application.
    Defines styles for Dark Mode, Cards, and general UI/UX.
    """
    return """
    <style>
        /* General Settings */
        .stApp {
            background-color: #0E1117;
            font-family: 'Inter', sans-serif;
        }
        
        /* Remove top padding */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Card Styling */
        .metric-card {
            background-color: #262730;
            border: 1px solid #3d3d3d;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            margin-bottom: 1rem;
        }
        
        .metric-value {
            font-size: 28px;
            font-weight: bold;
            color: #ffffff;
            margin: 0;
        }
        
        .metric-label {
            font-size: 14px;
            color: #a0a0a0;
            margin-bottom: 5px;
        }
        
        /* Status Cards */
        .status-card {
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 20px;
            border-left: 6px solid;
            color: white;
            position: relative;
            overflow: hidden;
        }
        
        .status-normal {
            background-color: rgba(0, 204, 150, 0.1);
            border-color: #00CC96;
        }
        
        .status-warning {
            background-color: rgba(255, 189, 69, 0.1);
            border-color: #FFBD45;
        }
        
        .status-critical {
            background-color: rgba(255, 75, 75, 0.1);
            border-color: #FF4B4B;
        }

        .status-title {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .status-desc {
            font-size: 16px;
            opacity: 0.9;
        }
        
        /* Upload Area */
        .upload-area {
            border: 2px dashed #4b4b4b;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            background-color: #262730;
        }

        /* Sidebar Styling Fix */
        [data-testid="stSidebar"] {
            background-color: #161a24;
            border-right: 1px solid #2b303b;
        }
    </style>
    """

def preprocess_data(df):
    """
    Cleans and maps columns from various logsheet formats (including the user's Indonesian format)
    to the standard English format required by the dashboard.
    """
    # Define mapping dictionary: {Standard_Name: [Possible_Matches]}
    column_mapping = {
        'Voltage': ['Tegangan Line to Line fase AB', 'Voltage', 'Tegangan Output'],
        'Frequency': ['Frequency', 'Frekuensi', 'Freq'],
        'Oil Pressure': ['Oil Pressure in KPa', 'Oil Pressure', 'Tekanan Oli'],
        'Oil Temp': ['Oil Temperature', 'Oil Temp', 'Suhu Oli', 'Coolant Right Temperature'], # Fallback for now if Oil Temp missing
        'Coolant Temp': ['Coolant Left Temperature', 'Coolant Temp', 'Suhu Pendingin'],
        'Vibration': ['Vibration', 'Vibrasi', 'Getaran'],
        'Battery Voltage': ['Tegangan Baterai Starter', 'Battery Voltage', 'Tegangan Accu']
    }
    
    # 1. Normalize Column Names
    
    # Create a copy to avoid SettingWithCopy warnings
    df_clean = df.copy()
    
    # Check for Date column
    date_cols = [c for c in df_clean.columns if 'date' in c.lower() or 'tanggal' in c.lower()]
    if date_cols:
        df_clean.rename(columns={date_cols[0]: 'Timestamp'}, inplace=True)
        try:
            df_clean['Timestamp'] = pd.to_datetime(df_clean['Timestamp'])
        except:
            # Fallback for weird date formats
            df_clean['Timestamp'] = pd.to_datetime(df_clean['Timestamp'], errors='coerce')
    else:
        # Create dummy timestamps if missing
        df_clean['Timestamp'] = pd.date_range(end=pd.Timestamp.now(), periods=len(df_clean), freq='h')

    # 2. Map Columns
    found_cols = []
    
    for standard, aliases in column_mapping.items():
        match = None
        for alias in aliases:
            # Case insensitive search
            matches = [c for c in df_clean.columns if alias.lower() in c.lower()]
            if matches:
                match = matches[0]
                break
        
        if match:
            df_clean.rename(columns={match: standard}, inplace=True)
            found_cols.append(standard)
        else:
            # If a required column is missing, fill with default/dummy values ONLY to prevent crash
            if standard not in df_clean.columns:
                if standard == 'Vibration':
                    df_clean[standard] = 1.2 # Default safe value
                elif standard == 'Oil Temp':
                    df_clean[standard] = 80 # Default safe value
                else:
                    df_clean[standard] = 0

    # Ensure all numeric columns are actually numeric
    numeric_cols = ['Voltage', 'Frequency', 'Oil Pressure', 'Oil Temp', 'Coolant Temp', 'Vibration', 'Battery Voltage']
    for col in numeric_cols:
        if col in df_clean.columns:
            # Clean non-numeric characters if any
            if df_clean[col].dtype == object:
                df_clean[col] = pd.to_numeric(df_clean[col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
            df_clean[col] = df_clean[col].fillna(0)
            
    return df_clean

def generate_mock_data():
    """
    Generates dummy data for the EDG Monitoring System.
    Includes scenarios for Normal, Warning (Low Oil Pressure), and Critical.
    """
    # Create a time range for 24 hours
    dates = pd.date_range(end=pd.Timestamp.now(), periods=24, freq='h')
    
    data = {
        'Timestamp': dates,
        'Voltage': np.random.normal(400, 2, 24).round(1),  # Normal ~400V
        'Frequency': np.random.normal(50, 0.1, 24).round(2), # Normal ~50Hz
        'Oil Pressure': np.concatenate([
            np.random.normal(460, 5, 20), 
            np.random.normal(440, 5, 4) # Last 4 hours drop below 450 (Warning)
        ]).round(1),
        'Oil Temp': np.random.normal(85, 2, 24).round(1),
        'Coolant Temp': np.random.normal(80, 2, 24).round(1),
        'Vibration': np.random.normal(1.5, 0.1, 24).round(2),
        'Battery Voltage': np.random.normal(27, 0.5, 24).round(1)
    }
    
    return pd.DataFrame(data)

def load_historical_data(filepath="data/2024-2026.csv"):
    """
    Loads and cleans the specific historical dataset provided by the user.
    Handles corrupted headers by skipping lines and mapping by index.
    """
    try:
        # Read with header=None since the header is messy
        # Skip the first 3 lines based on inspection (headers are on line 1, data starts line 3)
        df = pd.read_csv(filepath, skiprows=2, header=None, on_bad_lines='skip')
        
        # Manual Index Mapping based on 2024-2026.csv analysis
        # Index 1: Date (2024-08-12)
        # Index 8: Voltage (400)
        # Index 17: Frequency (0 or 50) -> Wait, Index mapping needs care.
        # Let's inspect line 4 (Index 3): "4","2024-08-26","EMDG Unit1","27","0.81","Normal","Normal","Normal","400"
        # 0: id, 1: Date, 2: Name, 3: ?, 4: ?, 5,6,7: Levels, 8: Volts AB, 9: Volts BC, 10: Volts CA
        # 11,12,13: Volts Neutral, 14,15: Amps/Power?, 16: KWH (22534), 17: Freq (50)
        # 18: RPM (1503), 19: Starts, 20: RunHours, 21: Oil Press (39!), 22: Coolant Left (29), 23: Coolant Right (27)
        # 24: Status text
        
        mapped_data = pd.DataFrame()
        mapped_data['Timestamp'] = pd.to_datetime(df[1], errors='coerce')
        mapped_data['Voltage'] = pd.to_numeric(df[8], errors='coerce') # V Line Phase AB 
        mapped_data['Frequency'] = pd.to_numeric(df[17], errors='coerce') 
        mapped_data['Oil Pressure'] = pd.to_numeric(df[21], errors='coerce')
        mapped_data['Oil Temp'] = pd.to_numeric(df[22], errors='coerce') # Assuming Coolant Left ~ Oil Temp proxy for now or similar
        mapped_data['Coolant Temp'] = pd.to_numeric(df[23], errors='coerce') # Coolant Right
        mapped_data['Vibration'] = 1.5 # Placeholder, not in CSV?
        mapped_data['Battery Voltage'] = 27.0 # Placeholder
        
        # Filter valid data
        mapped_data = mapped_data.dropna(subset=['Timestamp', 'Oil Pressure'])
        # Sort by date
        mapped_data = mapped_data.sort_values('Timestamp')
        
        return mapped_data
    except Exception as e:
        print(f"Error loading history: {e}")
        return pd.DataFrame() # Return empty on failure

def train_baseline_model(df):
    """
    Calculates statistical baseline (Mean & Std Dev) from historical data.
    Returns a dictionary of parameters for the Anomaly Detection model.
    """
    model = {}
    metrics = ['Oil Pressure', 'Coolant Temp', 'Voltage', 'Frequency']
    
    if df.empty:
        # Default fallbacks if no history
        return {
            'Oil Pressure': {'mean': 450, 'std': 50, 'low_limit': 400},
            'Coolant Temp': {'mean': 80, 'std': 10, 'high_limit': 95}
        }

    for m in metrics:
        if m in df.columns:
            mu = df[m].mean()
            sigma = df[m].std()
            
            # Sanity check for zero std dev
            if sigma == 0: sigma = 1 
            
            model[m] = {
                'mean': mu,
                'std': sigma,
                # Dynamic Thresholds: 2 Sigma (95% Confidence Interval)
                'low_limit': mu - (2 * sigma),
                'high_limit': mu + (2 * sigma)
            }
            
    return model

def analyze_status(df, model=None):
    """
    Analyzes status using Statistical Model (Z-Score) if available,
    otherwise falls back to hardcoded rules.
    """
    if df.empty:
        return {"status": "Unknown", "message": "No Data", "class": "grey", "confidence": 0, "latest_data": {}}

    latest = df.iloc[-1]
    
    status = "Normal"
    message = "Parameter operasi dalam rentang normal (Historical Baseline)."
    color_class = "status-normal"
    confidence = 98 
    
    # Metric Extraction
    oil_p = latest.get('Oil Pressure', 0)
    cool_t = latest.get('Coolant Temp', 0)
    
    # --- Logic Decision Tree ---
    
    # 1. Critical Hard Limits (Safety Interlocks) - Always take precedence
    if cool_t > 98 or oil_p < 200:
         status = "Critical"
         message = f"CRITICAL: Nilai berbahaya terdeteksi! (Oil: {oil_p}, Coolant: {cool_t})"
         color_class = "status-critical"
         confidence = 99
         return {"status": status, "message": message, "class": color_class, "confidence": confidence, "latest_data": latest}

    # 2. Statistical Anomaly Detection (if Model exists)
    if model:
        # Oil Pressure Check
        oil_stats = model.get('Oil Pressure')
        if oil_stats:
            z_score = (oil_p - oil_stats['mean']) / oil_stats['std']
            
            if oil_p < oil_stats['low_limit']: # Lower than 2 sigma
                status = "Warning (Anomaly)"
                message = f"Tekanan oli ({oil_p} kPa) rendah tidak wajar. (Avg: {oil_stats['mean']:.1f}, Limit: {oil_stats['low_limit']:.1f})"
                color_class = "status-warning"
                confidence = 95
                
        # Coolant Check
        cool_stats = model.get('Coolant Temp')
        if cool_stats and status == "Normal": # Only if not already warning
            if cool_t > cool_stats['high_limit']:
                status = "Warning (Overheat Trend)"
                message = f"Suhu pendingin ({cool_t}°C) naik diatas wajar. (Avg: {cool_stats['mean']:.1f})"
                color_class = "status-warning"
                
    # 3. Fallback Hardcoded Rules (if no model or model permissive)
    else:
        if cool_t > 95:
            status = "Critical"
            message = "Suhu tinggi > 95°C."
            color_class = "status-critical"
        elif oil_p < 450:
            status = "Warning"
            message = "Tekanan oli < 450 kPa."
            color_class = "status-warning"
        
    return {
        "status": status,
        "message": message,
        "class": color_class,
        "confidence": confidence,
        "latest_data": latest
    }

def generate_chat_response(query, df, model):
    """
    Generates a response for the AI Assistant based on data context.
    Uses pattern matching to handle date-specific queries (history lookup).
    """
    query = query.lower()
    
    if df.empty:
        return "Maaf, saya belum menerima data operasional. Silakan upload file logsheet terlebih dahulu."
        
    latest = df.iloc[-1]
    status = analyze_status(df, model)
    
    # 1. Handle Date-Specific Queries (e.g., "kondisi pada 2024-08-12" or "tanggal 12 agustus")
    import re
    # Try to extract year-month-day or day/month simple patterns
    # Very basic regex for demo: YYYY-MM-DD
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', query)
    
    if date_match:
        target_date = date_match.group(1)
        # Filter dataframe
        try:
            # Look for exact date match. 
            # Note: Timestamp column might have time, so we check date part.
            target_row = df[df['Timestamp'].dt.strftime('%Y-%m-%d') == target_date]
            
            if not target_row.empty:
                row = target_row.iloc[0]
                return f"**Data pada {target_date}:**\n- Tekanan Oli: {row.get('Oil Pressure', 'N/A')} kPa\n- Suhu Coolant: {row.get('Coolant Temp', 'N/A')}°C\n- Status (Data): {row.get(24, 'Tidak ada catatan status')}" # Column 24 was status text in raw CSV
            else:
                return f"Maaf, tidak ditemukan data untuk tanggal {target_date} di database riwayat."
        except Exception as e:
            return f"Terjadi kesalahan saat mencari tanggal: {e}"

    # 2. General Queries (Aggregation / High Level)
    if "kapan" in query and ("suhu" in query or "panas" in query):
        # Find dates where temp > 95
        high_temp = df[df['Coolant Temp'] > 95]
        if not high_temp.empty:
            dates = high_temp['Timestamp'].dt.strftime('%Y-%m-%d').tolist()
            return f"Suhu tinggi (>95°C) terdeteksi pada tanggal: {', '.join(dates[:5])}..."
        else:
            return "Tidak ada catatan suhu kritis (>95°C) dalam riwayat data."
            
    if "kapan" in query and ("oli" in query or "tekanan" in query):
        # Find dates where oil < 450
        low_oil = df[df['Oil Pressure'] < 450]
        if not low_oil.empty:
            dates = low_oil['Timestamp'].dt.strftime('%Y-%m-%d').tolist()
            return f"Tekanan oli rendah (<450 kPa) terdeteksi pada tanggal: {', '.join(dates[:5])}..."
        else:
             return "Tidak ada catatan tekanan oli kritis dalam riwayat data."

    # 3. Contextual Data (Current / Latest)
    oil_p = latest.get('Oil Pressure', 0)
    cool_t = latest.get('Coolant Temp', 0)
    
    if "status" in query or "kondisi" in query or "kesehatan" in query:
        return f"**Status Terakhir (Data Terbaru):** {status['status']}.\n\n{status['message']}\nConfidence Score model AI adalah {status['confidence']}%."
        
    elif "oli" in query or "oil" in query or "tekanan" in query:
        msg = f"Tekanan Oli terakhir adalah **{oil_p} kPa**."
        if model and 'Oil Pressure' in model:
            msg += f" (Baseline Normal: {model['Oil Pressure']['mean']:.1f} kPa)."
        if oil_p < 450:
            msg += " **Peringatan:** Tekanan ini di bawah batas normal!"
        return msg
        
    elif "suhu" in query or "temp" in query or "panas" in query:
        msg = f"Suhu Pendingin (Coolant): **{cool_t}°C**."
        if model and 'Coolant Temp' in model:
            msg += f" (Baseline Normal: {model['Coolant Temp']['mean']:.1f}°C)."
        if cool_t > 95:
            msg += " **BAHAYA:** Suhu ini terlalu tinggi!"
        return msg
    
    elif "rekomendasi" in query or "saran" in query or "tindakan" in query:
        if status['status'] == "Normal":
            return "Sistem berjalan optimal. Lakukan perawatan rutin sesuai jadwal (Ganti oli tiap 250 jam, cek filter)."
        elif "Warning" in status['status']:
            return "Saran: Periksa sensor terkait, cek level fluida (oli/coolant), dan pastikan tidak ada kebocoran. Pantau tren grafik."
        else:
            return "TINDAKAN SEGERA: Matikan mesin jika memungkinkan atau kurangi beban. Hubungi tim maintenance untuk inspeksi menyeluruh."
            
    elif "halo" in query or "hai" in query:
         return "Halo! Saya asisten cerdas EDG Monitoring. Anda bisa tanya 'Kapan suhu tinggi?' atau 'Kondisi pada 2024-08-12'."
        
    else:
        return "Maaf, saya hanya bisa menjawab terkait: Status, Tekanan Oli, Suhu, dan Rekomendasi Maintenance."

def create_pdf_report(df, selected_date_str, stats, recommendations):
    """
    Generates a PDF report for the EDG status.
    Uses FPDF library.
    """
    from fpdf import FPDF
    import tempfile
    
    class PDF(FPDF):
        def header(self):
            # Logo header (Assuming user has logos in assets/ or remove this part if no logo)
            # self.image('assets/pln_logo.png', 10, 8, 33) 
            self.set_font('Arial', 'B', 15)
            self.cell(80) # Move to right
            self.cell(30, 10, 'Laporan Monitoring EDG', 0, 0, 'C')
            self.ln(20)
            
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    
    # 1. Report Info
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'Periode Laporan: {selected_date_str}', 0, 1)
    pdf.ln(5)
    
    # 2. Executive Summary
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Executive Summary', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, f"Berdasarkan analisis data pada periode ini, performa EDG menunjukkan indikator: {stats.get('status', 'Unknown')}.")
    pdf.ln(5)
    
    # 3. Key Metrics Table
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Statistik Performa (Rata-rata)', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    col_width = 45 
    row_height = 10
    
    # Header
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(col_width, row_height, "Parameter", 1, 0, 'C', 1)
    pdf.cell(col_width, row_height, "Nilai Aktual", 1, 0, 'C', 1)
    pdf.cell(col_width, row_height, "Normal Baseline", 1, 0, 'C', 1)
    pdf.cell(col_width, row_height, "Deviasi", 1, 1, 'C', 1)
    
    # Data Rows
    metrics = [
        ("Oil Pressure", stats['oil_curr'], stats['oil_base'], stats['oil_delta']),
        ("Coolant Temp", stats['cool_curr'], stats['cool_base'], stats['cool_delta']),
        ("Frequency", stats['freq_curr'], stats['freq_base'], stats['freq_delta'])
    ]
    
    for label, curr, base, delta in metrics:
        pdf.cell(col_width, row_height, label, 1)
        pdf.cell(col_width, row_height, f"{curr:.1f}", 1)
        pdf.cell(col_width, row_height, f"{base:.1f}", 1)
        
        # Color deviation
        if abs(delta) > 5:
            pdf.set_text_color(255, 0, 0) # Red
        else:
             pdf.set_text_color(0, 100, 0) # Green
             
        pdf.cell(col_width, row_height, f"{delta:+.1f}%", 1, 1)
        pdf.set_text_color(0, 0, 0) # Reset
        
    pdf.ln(10)
    
    # 4. Recommendations
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Rekomendasi Teknis (AI Generated)', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    # Helper to clean text for FPDF (latin-1 only)
    def clean_text(text):
        replacements = {
            "✅": "[OK]",
            "❌": "[CRITICAL]",
            "⚠️": "[WARNING]",
            "“": '"', "”": '"', "’": "'"
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        # Encode to latin-1 and ignore errors to prevent crashing
        return text.encode('latin-1', 'replace').decode('latin-1')

    for rec in recommendations:
        # Simple bullet handling
        safe_rec = clean_text(str(rec))
        pdf.multi_cell(0, 10, f"{safe_rec}")
        
    # Output to temp file
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_file.name)
    return tmp_file.name
