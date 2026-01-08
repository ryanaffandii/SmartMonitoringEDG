import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import utils

# 1. Page Configuration
st.set_page_config(
    page_title="Smart EDG Monitoring System",
    page_icon="assets/pnj_logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Custom CSS
st.markdown(utils.load_css(), unsafe_allow_html=True)

# 3. Sidebar Navigation
with st.sidebar:
    st.markdown("<h4 style='text-align: center; color: #a0a0a0;'>Project By Ryan Affandi</h4>", unsafe_allow_html=True)
    st.markdown("### EDG Monitor")
    
    selected = option_menu(
        menu_title="Navigasi",
        options=["Dashboard", "Analisa Lanjutan", "AI Assistant", "Input Data", "Riwayat", "Tentang"],
        icons=["speedometer2", "graph-up-arrow", "robot", "cloud-upload", "clock-history", "info-circle"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "orange", "font-size": "16px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#262730"},
            "nav-link-selected": {"background-color": "#262730", "border-left": "5px solid #00CC96"},
        }
    )
    
    # Logos at the bottom
    col_logo = st.columns(1)[0]
    with col_logo:
        st.image("assets/pnj_logo.png", width=180)
        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True) # Spacer
        st.image("assets/pln_logo.png", width=180)

# Initialize Session State for Data
if 'data' not in st.session_state:
    st.session_state['data'] = pd.DataFrame()

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Halo! Saya AI Monitoring EDG. Tanyakan saya tentang status mesin, tekanan oli, atau anomali data."}]

# Initialize Historical Data & AI Model
if 'historical_data' not in st.session_state:
    with st.spinner("Loading Historical Data & Training Model..."):
        history_df = utils.load_historical_data()
        st.session_state['historical_data'] = history_df
        
        # Train Baseline Model
        if not history_df.empty:
            st.session_state['ai_model'] = utils.train_baseline_model(history_df)
        else:
            st.session_state['ai_model'] = None

# Constants for Date Filtering
FILTER_SINGLE = "Single Date"
FILTER_RANGE = "Date Range"

# 4. Main Content Logic
if selected == "Analisa Lanjutan":
    st.title("Analisa Performa EDG (Custom Filter)")
    st.markdown("Analisis mendalam berdasarkan rentang waktu pilihan Anda.")
    
    hist_df = st.session_state.get('historical_data', pd.DataFrame())
    
    if not hist_df.empty:
        # --- Filter UI ---
        with st.container():
            st.markdown("### 📅 Filter Data")
            col_f1, col_f2, col_f3 = st.columns([1, 2, 1])
            
            with col_f1:
                filter_type = st.radio("Mode Filter", [FILTER_RANGE, FILTER_SINGLE])
                
            filtered_df = pd.DataFrame()
            
            with col_f2:
                min_date = hist_df['Timestamp'].min().date()
                max_date = hist_df['Timestamp'].max().date()
                
                if filter_type == FILTER_SINGLE:
                    target_date = st.date_input("Pilih Tanggal", value=max_date, min_value=min_date, max_value=max_date)
                    # Filter for that specific day
                    filtered_df = hist_df[hist_df['Timestamp'].dt.date == target_date]
                else:
                    date_range = st.date_input("Pilih Rentang Tanggal", value=(min_date, max_date), min_value=min_date, max_value=max_date)
                    if len(date_range) == 2:
                        start_d, end_d = date_range
                        filtered_df = hist_df[(hist_df['Timestamp'].dt.date >= start_d) & (hist_df['Timestamp'].dt.date <= end_d)]
                    else:
                        st.info("Pilih tanggal awal dan akhir.")
                        filtered_df = hist_df # Default full if incomplete
        
        # --- Analysis UI ---
        st.markdown("---")
        
        if not filtered_df.empty:
            # --- 1. Comparative Analysis (Period vs Baseline) ---
            st.markdown("### 🔍 Analisa Komparatif & Diagnosa")
            
            global_model = st.session_state.get('ai_model')
            
            # Helper for metrics
            def calc_metric_stats(col_name, label, baseline_key):
                current_mean = filtered_df[col_name].mean()
                if global_model and baseline_key in global_model:
                    base_mean = global_model[baseline_key]['mean']
                    delta = ((current_mean - base_mean) / base_mean) * 100
                    return current_mean, base_mean, delta
                return current_mean, 0, 0

            # Calculate Stats
            oil_curr, oil_base, oil_delta = calc_metric_stats('Oil Pressure', 'Tekanan Oli', 'Oil Pressure')
            cool_curr, cool_base, cool_delta = calc_metric_stats('Coolant Temp', 'Suhu Coolant', 'Coolant Temp')
            freq_curr, freq_base, freq_delta = calc_metric_stats('Frequency', 'Frekuensi', 'Frequency')
            
            # --- Layout: 2 Columns (Stats vs Recommendations) ---
            col_res1, col_res2 = st.columns([1, 1])
            
            with col_res1:
                st.markdown("#### 📊 Statistik Performa")
                st.markdown("Perbandingan rata-rata periode terpilih vs Baseline Keseluruhan (2024-2026).")
                
                stats_data = {
                    "Parameter": ["Tekanan Oli (kPa)", "Suhu Coolant (°C)", "Frekuensi (Hz)"],
                    "Periode Ini": [f"{oil_curr:.1f}", f"{cool_curr:.1f}", f"{freq_curr:.2f}"],
                    "Baseline Normal": [f"{oil_base:.1f}", f"{cool_base:.1f}", f"{freq_base:.2f}"],
                    "Deviasi": [f"{oil_delta:+.1f}%", f"{cool_delta:+.1f}%", f"{freq_delta:+.2f}%"]
                }
                st.dataframe(pd.DataFrame(stats_data), hide_index=True, use_container_width=True)
                
                # Deviation Indicator
                if abs(oil_delta) > 5:
                    st.warning(f"⚠️ Tekanan Oli menyimpang {oil_delta:+.1f}% dari standar!")
                if abs(cool_delta) > 5:
                    st.warning(f"⚠️ Suhu Coolant menyimpang {cool_delta:+.1f}% dari standar!")

            with col_res2:
                st.markdown("#### 🛠️ Rekomendasi Teknis Spesifik")
                recommendations = []
                
                # Logic for Recommendations
                # 1. Oil Pressure Analysis
                if oil_curr < 450:
                    recommendations.append("❌ **CRITICAL: Tekanan Oli Rendah (<450 kPa).**")
                    recommendations.append("- Segera periksa kondisi Lubricating Oil Pump.")
                    recommendations.append("- Cek kebuntuan pada Oil Filter.")
                    recommendations.append("- Pastikan viskositas oli sesuai spesifikasi.")
                elif oil_delta < -3: # Dropping but not critical
                    recommendations.append("⚠️ **Warning: Tren Penurunan Tekanan Oli.**")
                    recommendations.append("- Indikasi awal penyumbatan filter atau degradasi kualitas oli.")
                    recommendations.append("- Jadwalkan pengambilan sampel oli (Oil Analysis).")
                else:
                    recommendations.append("✅ Sistem pelumasan dalam kondisi optimal.")
                    
                st.markdown("---")
                
                # 2. Temperature Analysis
                if cool_curr > 95:
                    recommendations.append("❌ **CRITICAL: Potensi Overheat (>95°C).**")
                    recommendations.append("- Periksa sirkulasi air pendingin dan kondisi Radiator.")
                    recommendations.append("- Cek fungsi Thermostat Valve.")
                elif cool_delta > 3:
                     recommendations.append("⚠️ **Warning: Tren Kenaikan Suhu.**")
                     recommendations.append("- Periksa kebersihan sirip radiator (fouling).")
                     recommendations.append("- Cek ketegangan belt kipas pendingin.")
                else:
                    recommendations.append("✅ Sistem pendingin berfungsi normal.")

                # 3. Electrical/General
                if abs(freq_delta) > 1:
                     recommendations.append("⚠️ **Warning: Fluktuasi Frekuensi.**")
                     recommendations.append("- Periksa kinerja Governor / Speed Control.")
                     
                for rec in recommendations:
                    st.markdown(rec)
            
            st.markdown("---")
            st.markdown("### 📈 Deep Dive Charts")
            
            # Using Plotly
            fig = go.Figure()
            
            # Interactive Line Chart
            fig.add_trace(go.Scatter(
                x=filtered_df['Timestamp'], y=filtered_df['Oil Pressure'],
                name='Oil Pressure', mode='lines+markers', line=dict(color='#FFBD45')
            ))
            fig.add_trace(go.Scatter(
                x=filtered_df['Timestamp'], y=filtered_df['Coolant Temp'],
                name='Coolant Temp', mode='lines+markers', line=dict(color='#00CC96')
            ))
            
            # Add Baseline Reference Lines (Global Average)
            if global_model:
                fig.add_hline(y=global_model['Oil Pressure']['mean'], line_dash="dot", line_color="grey", annotation_text="Global Avg Oil")
            
            fig.update_layout(
                title=f"Detail Tren: {min_date} s/d {max_date}",
                xaxis_title="Waktu",
                yaxis_title="Nilai",
                paper_bgcolor="#1E2129", plot_bgcolor="#1E2129",
                font=dict(color="white"),
                height=400,
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed Data Table
            with st.expander("Lihat Raw Data & Export"):
                st.dataframe(filtered_df, use_container_width=True)
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Data (CSV)", csv, "data_export.csv", "text/csv")
                
        else:
            st.warning("Tidak ada data ditemukan untuk tanggal yang dipilih.")
            
    else:
        st.error("Data historis tidak tersedia. Mohon cek file data.")

elif selected == "AI Assistant":
    st.title("💬 EDG Smart Assistant")
    st.markdown("Ngobrol langsung dengan data operasional EDG Anda.")
    
    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Chat Input
    if prompt := st.chat_input("Tanya tentang kondisi EDG..."):
        # User message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Assistant Response
        with st.chat_message("assistant"):
            with st.spinner("Menganalisis data..."):
                response = utils.generate_chat_response(
                    prompt, 
                    st.session_state['data'], 
                    st.session_state.get('ai_model')
                )
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

elif selected == "Input Data":
    st.title("Input Logsheet Operasional")
    st.markdown("Upload file Excel atau CSV hasil ekspor logsheet harian.")
    
    # Custom Upload Area
    st.markdown('<div class="upload-area">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=['csv', 'xlsx'])
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Preprocess the data (Map columns from Indonesian -> English)
            df = utils.preprocess_data(df)
            
            st.session_state['data'] = df
            st.success(f"File '{uploaded_file.name}' berhasil diupload! Sistem telah mendeteksi dan memetakan kolom otomatis.")
            
            # Preview Data
            st.markdown("### Preview Data")
            st.dataframe(df.head(), use_container_width=True)
            
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")
            
    # Button to Load Mock Data
    st.markdown("---")
    if st.button("Load Dummy Data (Untuk Demo)"):
        st.session_state['data'] = utils.generate_mock_data()
        st.success("Dummy data berhasil dimuat! Silakan cek Dashboard.")

elif selected == "Dashboard":
    st.title("Panel Monitoring EDG")
    st.markdown("Analisis Real-time Kesehatan Emergency Diesel Generator.")
    
    # Check if data exists
    if st.session_state['data'].empty:
        # Auto-load mock data if empty for better UX as requested
        st.warning("Belum ada data diupload. Menggunakan **Dummy Data** untuk demonstrasi.")
        st.session_state['data'] = utils.generate_mock_data()
    
    df = st.session_state['data']
    
    # --- Dashboard Filter Section ---
    st.markdown("### 📅 Filter & Analisis Kondisi")
    
    # Defaults
    hist_df = st.session_state.get('historical_data', pd.DataFrame())
    dashboard_df = pd.DataFrame()
    
    if not hist_df.empty:
        col_d1, col_d2 = st.columns([1, 2])
        with col_d1:
            filter_mode = st.radio("Mode Tampilan:", ["Semua Data (2024-2026)", "Rentang Tanggal", "Pilih Tanggal Tunggal"], horizontal=True)
            
        with col_d2:
            min_d = hist_df['Timestamp'].min().date()
            max_d = hist_df['Timestamp'].max().date()
            
            if filter_mode == "Rentang Tanggal":
                d_range = st.date_input("Pilih Rentang:", value=(min_d, max_d), min_value=min_d, max_value=max_d)
                if len(d_range) == 2:
                    dashboard_df = hist_df[(hist_df['Timestamp'].dt.date >= d_range[0]) & (hist_df['Timestamp'].dt.date <= d_range[1])]
                else:
                    dashboard_df = hist_df
            elif filter_mode == "Pilih Tanggal Tunggal":
                s_date = st.date_input("Pilih Tanggal:", value=max_d, min_value=min_d, max_value=max_d)
                dashboard_df = hist_df[hist_df['Timestamp'].dt.date == s_date]
            else:
                dashboard_df = hist_df
    else:
        dashboard_df = df # Fallback
        
    if dashboard_df.empty:
        st.warning(f"Tidak ada data ditemukan untuk periode yang dipilih.")
        st.stop()
        
    # --- Update Analysis based on Filtered Data ---
    # We re-run the analysis logic on the filtered view to get the "Status" for this specific period
    current_analysis = utils.analyze_status(dashboard_df, model=st.session_state.get('ai_model'))
    
    # Override the top status card with this dynamic analysis
    status = current_analysis['status']
    message = current_analysis['message']
    color_class = current_analysis['class']
    confidence = current_analysis.get('confidence', 0)

    # --- Top Section: Status Card & Diagnostic ---
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="status-card {color_class}">
            <div class="status-title">{status}</div>
            <div class="status-desc">{message}</div>
            <div style="margin-top: 10px; font-size: 12px; opacity: 0.8;">
                AI Confidence Score: <b>{confidence}%</b> | Data Points: {len(dashboard_df)}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
             <div class="metric-label">System Health Score</div>
             <div class="metric-value" style="color: {color_class.split('-')[1] == 'normal' and '#00CC96' or '#FFBD45'}; font-size: 42px;">
                {confidence if status == 'Normal' else 100 - (100-confidence)*2}/100
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- PDF Report Generation (Moved to Dashboard) ---
    st.markdown("### 📄 Export Laporan")
    if st.button("Generate Laporan Resmi (PDF) untuk Periode Ini"):
        if not dashboard_df.empty:
            # 1. Calc Stats for PDF (Re-using logic)
            global_model = st.session_state.get('ai_model')
            
            def safe_stats(col, base_key):
                curr = dashboard_df[col].mean()
                base = 0
                delta = 0
                if global_model and base_key in global_model:
                     base = global_model[base_key]['mean']
                     if base != 0: delta = ((curr - base) / base) * 100
                return curr, base, delta
                
            oil_c, oil_b, oil_d = safe_stats('Oil Pressure', 'Oil Pressure')
            cool_c, cool_b, cool_d = safe_stats('Coolant Temp', 'Coolant Temp')
            freq_c, freq_b, freq_d = safe_stats('Frequency', 'Frequency')

            stats_pdf = {
                'status': status,
                'oil_curr': oil_c, 'oil_base': oil_b, 'oil_delta': oil_d,
                'cool_curr': cool_c, 'cool_base': cool_b, 'cool_delta': cool_d,
                'freq_curr': freq_c, 'freq_base': freq_b, 'freq_delta': freq_d,
            }
            
            # 2. Generate Simple Auto Recommendations
            recs_pdf = []
            if status != "Normal":
                 recs_pdf.append(f"⚠️ **Perhatian:** {message}")
                 if oil_c < 450: recs_pdf.append("- Cek sistem pelumasan.")
                 if cool_c > 95: recs_pdf.append("- Cek sistem pendingin.")
            else:
                 recs_pdf.append("✅ Sistem beroperasi normal.")
            
            pdf_path = utils.create_pdf_report(
                dashboard_df, 
                f"Laporan Dashboard ({len(dashboard_df)} data points)", 
                stats_pdf, 
                recs_pdf
            )
            
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download PDF Sekarang",
                    data=f.read(),
                    file_name="Laporan_Dashboard_EDG.pdf",
                    mime="application/pdf"
                )
        else:
            st.error("Tidak ada data untuk digenerate.")
    
    # --- Middle Section: Key Metrics ---
    st.markdown("### Key Metrics (Rata-rata Periode Terpilih)")
    
    # Calculate Averages from Filtered Data
    params_to_show = ['Voltage', 'Frequency', 'Oil Pressure', 'Coolant Temp', 'Oil Temp', 'Battery Voltage', 'Vibration']
    
    metrics_data = {}
    if not dashboard_df.empty:
        for p in params_to_show:
            if p in dashboard_df.columns:
                 metrics_data[p] = dashboard_df[p].mean()
            else:
                 metrics_data[p] = 0
    else:
         for p in params_to_show: metrics_data[p] = 0

    # Metrics Layout - Grid of 4 per row
    cols1 = st.columns(4)
    cols2 = st.columns(4)
    
    def metric_html(label, value, unit):
        color = "#ffffff"
        if label == "Oil Pressure" and value < 450: color = "#FFBD45"
        if label == "Coolant Temp" and value > 95: color = "#FF4B4B"
        
        return f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color: {color}">{value:.1f} <span style="font-size: 16px;">{unit}</span></div>
        </div>
        """
    
    # Row 1
    with cols1[0]: st.markdown(metric_html("Voltage", metrics_data['Voltage'], "V"), unsafe_allow_html=True)
    with cols1[1]: st.markdown(metric_html("Frequency", metrics_data['Frequency'], "Hz"), unsafe_allow_html=True)
    with cols1[2]: st.markdown(metric_html("Oil Pressure", metrics_data['Oil Pressure'], "kPa"), unsafe_allow_html=True)
    with cols1[3]: st.markdown(metric_html("Suhu Coolant", metrics_data['Coolant Temp'], "°C"), unsafe_allow_html=True)
    
    # Row 2
    with cols2[0]: st.markdown(metric_html("Suhu Oli", metrics_data['Oil Temp'], "°C"), unsafe_allow_html=True)
    with cols2[1]: st.markdown(metric_html("Battery Volt", metrics_data['Battery Voltage'], "V"), unsafe_allow_html=True)
    with cols2[2]: st.markdown(metric_html("Vibration", metrics_data['Vibration'], "mm/s"), unsafe_allow_html=True)
    
    # --- Bottom Section: Charts ---
    st.markdown("### Tren Analisis (Periode Terpilih)")
    
    # Use Filtered Data for Trends
    chart_df = dashboard_df
    
    # Dynamic tabs for all parameters
    tab_list = ["Tekanan", "Temperatur", "Kelistrikan", "Getaran"]
    tab1, tab2, tab3, tab4 = st.tabs(tab_list)
    
    # Helper to plot time series
    def plot_trend(y_col, name, color, unit, thresh=None):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=chart_df['Timestamp'], y=chart_df[y_col], name=name,
            mode='lines+markers', line=dict(color=color, width=2)
        ))
        if thresh:
             fig.add_hline(y=thresh, line_dash="dash", line_color="red", annotation_text=f"Limit ({thresh})")
             
        fig.update_layout(
            yaxis_title=f"{name} ({unit})",
            paper_bgcolor="#1E2129", plot_bgcolor="#1E2129",
            font=dict(color="white"),
            margin=dict(l=20, r=20, t=20, b=20),
            height=350,
            hovermode="x unified"
        )
        return fig
    
    with tab1:
        st.plotly_chart(plot_trend('Oil Pressure', 'Tekanan Oli', '#FFBD45', 'kPa', 450), use_container_width=True)
        
    with tab2:
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(x=chart_df['Timestamp'], y=chart_df['Coolant Temp'], name='Coolant', mode='lines+markers', line=dict(color='#00CC96')))
        fig_temp.add_trace(go.Scatter(x=chart_df['Timestamp'], y=chart_df['Oil Temp'], name='Oil Temp', mode='lines+markers', line=dict(color='#00AAFF')))
        fig_temp.update_layout(paper_bgcolor="#1E2129", plot_bgcolor="#1E2129", font=dict(color="white"), height=350, margin=dict(t=20, l=20, r=20, b=20), hovermode="x unified")
        st.plotly_chart(fig_temp, use_container_width=True)
        
    with tab3:
        fig_elec = go.Figure()
        fig_elec.add_trace(go.Scatter(x=chart_df['Timestamp'], y=chart_df['Voltage'], name='Voltage (V)', mode='lines+markers', line=dict(color='#E1E1E1')))
        fig_elec.add_trace(go.Scatter(x=chart_df['Timestamp'], y=chart_df['Battery Voltage'], name='Battery (V)', mode='lines+markers', line=dict(color='#FF5555')))
        fig_elec.add_trace(go.Scatter(x=chart_df['Timestamp'], y=chart_df['Frequency'], name='Freq (Hz)', mode='lines+markers', line=dict(color='#FFFF00'))) # Freq might be different scale, but okay for overview
        fig_elec.update_layout(paper_bgcolor="#1E2129", plot_bgcolor="#1E2129", font=dict(color="white"), height=350, margin=dict(t=20, l=20, r=20, b=20), hovermode="x unified")
        st.plotly_chart(fig_elec, use_container_width=True)

    with tab4:
        st.plotly_chart(plot_trend('Vibration', 'Vibrasi Mesin', '#9D4EDD', 'mm/s'), use_container_width=True)

elif selected == "Riwayat":
    st.title("Riwayat Data Operasional (2024-2026)")
    
    history_df = st.session_state.get('historical_data')
    
    if history_df is not None and not history_df.empty:
        # Metrics Summary of History
        col1, col2 = st.columns(2)
        with col1:
             st.markdown(f"**Total Data Points:** {len(history_df)}")
             st.markdown(f"**Rentang Waktu:** {history_df['Timestamp'].min().date()} s/d {history_df['Timestamp'].max().date()}")
        with col2:
             if 'ai_model' in st.session_state and st.session_state['ai_model']:
                 model = st.session_state['ai_model']
                 st.info(f"**AI Baseline (Normal):**\n- Oil Pressure: {model['Oil Pressure']['mean']:.1f} ± {model['Oil Pressure']['std']*2:.1f} kPa")

        st.dataframe(history_df, use_container_width=True)
        
        # Download Button
        csv = history_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Data CSV",
            csv,
            "edg_pembangkit_history.csv",
            "text/csv",
            key='download-csv'
        )
    else:
        st.warning("Data riwayat tidak ditemukan atau gagal dimuat.")
    
elif selected == "Tentang":
    st.markdown("### Smart EDG Monitoring System")
    st.markdown("""
    Dikembangkan untuk Skripsi Rancang Bangun Teknik Mesin.
    
    **Fitur Utama:**
    - Monitoring Parameter Kritis EDG
    - Deteksi Anomali Berbasis Aturan (Early AI Logic)
    - Visualisasi Data Real-time
    """)
