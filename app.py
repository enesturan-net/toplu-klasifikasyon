import streamlit as st
import pandas as pd
import io
import json
import plotly.express as px
import plotly.io as pio
from datetime import datetime

# Sayfa Ayarları
st.set_page_config(page_title="RobotİK - Pro Analiz", layout="wide", page_icon="🚀")
st.title("🚀 RobotİK - İnteraktif Analiz ve Raporlama Paneli")

# Stil özelleştirmeleri
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px 5px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #ff4b4b; color: white; }
</style>""", unsafe_allow_html=True)

if 'kurallar' not in st.session_state:
    st.session_state.kurallar = []

# --- GELİŞMİŞ HTML RAPOR OLUŞTURUCU ---
def create_html_report(df, rules):
    toplam_kisi = len(df)
    rapor_tarihi = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    kategori_verileri = []
    
    for kural in rules:
        temp_df = df.copy()
        for s, (mn, mx) in kural['filtreler']['sayisal'].items():
            if s in temp_df: temp_df = temp_df[(temp_df[s] >= mn) & (temp_df[s] <= mx)]
        for s, v in kural['filtreler']['kategorik'].items():
            if s in temp_df: temp_df = temp_df[temp_df[s].isin(v)]
        
        count = len(temp_df)
        kategori_verileri.append({
            "Kategori": kural['kategori'],
            "Sayı": count,
            "Yüzde": (count / toplam_kisi * 100) if toplam_kisi > 0 else 0,
            "Kriterler_Sayisal": kural['filtreler']['sayisal'],
            "Kriterler_Kategorik": kural['filtreler']['kategorik']
        })

    # Grafik 1: Renkli Pasta Grafiği
    fig_pie = px.pie(kategori_verileri, values='Sayı', names='Kategori', hole=0.4, 
                     color_discrete_sequence=px.colors.qualitative.Set3, title="Grup Dağılımı")
    
    # Grafik 2: Karşılaştırmalı Bar Grafiği
    fig_bar = px.bar(kategori_verileri, x='Kategori', y='Sayı', color='Kategori', 
                     text='Sayı', title="Grup Mevcutları Karşılaştırması",
                     color_discrete_sequence=px.colors.qualitative.Set3)
    
    html_pie = pio.to_html(fig_pie, full_html=False)
    html_bar = pio.to_html(fig_bar, full_html=False)

    # HTML Şablonu
    html_string = f"""
    <html>
    <head>
        <title>RobotİK Raporu</title>
        <style>
            body {{ font-family: 'Helvetica', sans-serif; background: #f4f4f9; color: #333; padding: 20px; }}
            .container {{ max_width: 1000px; margin: auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }}
            h1 {{ text-align: center; color: #4a4a4a; }}
            .charts {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin-top: 30px; }}
            .card {{ background: #fff; border-left: 6px solid #6c5ce7; padding: 15px; margin-bottom: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
            .badge {{ background: #6c5ce7; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }}
            ul {{ margin: 5px 0; padding-left: 20px; font-size: 14px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 RobotİK Analiz Raporu</h1>
            <p style="text-align:center; color:#888;">{rapor_tarihi}</p>
            
            <div class="charts">
                <div style="width: 48%; min-width:300px;">{html_pie}</div>
                <div style="width: 48%; min-width:300px;">{html_bar}</div>
            </div>

            <h2>📂 Grup Detayları</h2>
    """
    
    for veri in kategori_verileri:
        filters_html = "<ul>"
        for k, v in veri['Kriterler_Sayisal'].items():
            filters_html += f"<li><b>{k}:</b> {int(v[0])} - {int(v[1])}</li>"
        for k, v in veri['Kriterler_Kategorik'].items():
            filters_html += f"<li><b>{k}:</b> {', '.join(v)}</li>"
        filters_html += "</ul>"
        
        html_string += f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;">{veri['Kategori']}</h3>
                    <span class="badge">{veri['Sayı']} Kişi (%{veri['Yüzde']:.1f})</span>
                </div>
                {filters_html}
            </div>
        """
    
    html_string += "</div></body></html>"
    return html_string

# --- YAN MENÜ ---
with st.sidebar:
    st.header("💾 Ayar Merkezi")
    if st.session_state.kurallar:
        st.download_button("Ayarları İndir (.json)", json.dumps(st.session_state.kurallar), "ayarlar.json", "application/json")
        
        if st.button("Tüm Kuralları Temizle 🗑️"):
            st.session_state.kurallar = []
            st.rerun()
    
    st.divider()
    uploaded_settings = st.file_uploader("Ayar Yükle", type=["json"])
    if uploaded_settings and st.button("Yükle"):
        try:
            st.session_state.kurallar = json.load(uploaded_settings)
            st.success("Yüklendi!"); st.rerun()
        except: st.error("Hata")

# --- ANA AKIŞ ---
st.subheader("1. Veri Yükleme")
uploaded_file = st.file_uploader("Excel dosyanı buraya bırak", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        col_stat1.metric("Toplam Kişi", len(df))
        col_stat1.info("✅ Veri Başarıyla Okundu")

        tum_cols = df.columns.tolist()
        sayisal = df.select_dtypes(include=['number']).columns.tolist()
        kategorik = df.select_dtypes(exclude=['number']).columns.tolist()

        st.divider()
        
        # --- KURAL OLUŞTURMA ---
        st.subheader("2. Grupları Oluştur")
        col_i1, col_i2 = st.columns([1, 2])
        kat_adi = col_i1.text_input("Grup Adı (Örn: Yıldızlar)", key="new_cat")
        
        s_sec = st.multiselect("Puan Sütunları", sayisal)
        k_sec = st.multiselect("Metin Sütunları", kategorik)
        
        filtreler = {"sayisal": {}, "kategorik": {}}
        
        if s_sec:
            cols = st.columns(len(s_sec)) if len(s_sec) < 4 else st.columns(3)
            for i, s in enumerate(s_sec):
                with cols[i % 3]:
                    fig = px.histogram(df, x=s, title=s, color_discrete_sequence=['#6c5ce7'], height=150)
                    fig.update_layout(margin=dict(l=0,r=0,t=25,b=0), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    mn, mx = int(df[s].min()), int(df[s].max())
                    c1, c2 = st.columns(2)
                    v1 = c1.number_input(f"Min", value=mn, step=1, format="%d", key=f"min_{s}")
                    v2 = c2.number_input(f"Max", value=mx, step=1, format="%d", key=f"max_{s}")
                    filtreler["sayisal"][s] = (v1, v2)
        
        if k_sec:
            for s in k_sec:
                sel = st.multiselect(f"{s} değerleri:", df[s].dropna().unique(), key=f"k_{s}")
                if sel: filtreler["kategorik"][s] = sel

        # --- GÜNCELLENEN EKLEME BUTONU ---
        if st.button("Grubu Ekle / Güncelle ➕", type="primary"):
            if kat_adi and (filtreler["sayisal"] or filtreler["kategorik"]):
                
                yeni_kural = {"kategori": kat_adi, "filtreler": filtreler}
                
                # KONTROL: Aynı isimde grup var mı?
                guncellendi = False
                for i, kural in enumerate(st.session_state.kurallar):
                    if kural['kategori'] == kat_adi:
                        st.session_state.kurallar[i] = yeni_kural # Eskisini ez
                        guncellendi = True
                        break
                
                if not guncellendi:
                    st.session_state.kurallar.append(yeni_kural)
                    st.success(f"✅ '{kat_adi}' yeni grup olarak eklendi!")
                else:
                    st.warning(f"⚠️ '{kat_adi}' grubunun kriterleri GÜNCELLENDİ! (Eski hali silindi)")
                    
            else: st.warning("İsim ve en az bir kriter girin.")

        # --- SONUÇ EKRANI ---
        if st.session_state.kurallar:
            st.divider()
            st.header("3. 🔍 İnteraktif Keşif ve Sonuçlar")

            grup_verileri = {} 
            summary_data = []
            
            for kural in st.session_state.kurallar:
                t_df = df.copy()
                for s, (mn, mx) in kural['filtreler']['sayisal'].items():
                    if s in t_df: t_df = t_df[(t_df[s]>=mn) & (t_df[s]<=mx)]
                for s, v in kural['filtreler']['kategorik'].items():
                    if s in t_df: t_df = t_df[t_df[s].isin(v)]
                
                grup_verileri[kural['kategori']] = t_df
                summary_data.append({"Grup": kural['kategori'], "Kişi": len(t_df)})

            # Treemap
            col_g1, col_g2 = st.columns([2, 1])
            with col_g1:
                st.markdown("##### Genel Bakış")
                if summary_data:
                    fig_tree = px.treemap(pd.DataFrame(summary_data), path=['Grup'], values='Kişi', 
                                          color='Grup', color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig_tree, use_container_width=True)
            
            with col_g2:
                st.markdown("##### İndirme Merkezi")
                # Excel
                out_ex = io.BytesIO()
                with pd.ExcelWriter(out_ex, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Tüm Veri', index=False)
                    for name, data in grup_verileri.items():
                        safe_n = name[:30].replace(":", "")
                        data.to_excel(writer, sheet_name=safe_n, index=False)
                st.download_button("📥 Excel İndir", out_ex.getvalue(), "sonuc.xlsx", 
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                
                # HTML
                st.download_button("📄 Rapor İndir (HTML)", create_html_report(df, st.session_state.kurallar), 
                                   "rapor.html", "text/html", type="primary", use_container_width=True)

            st.divider()
            st.subheader("4. 🕵️‍♀️ Grupları İncele")

            tab_names = list(grup_verileri.keys())
            if tab_names:
                tabs = st.tabs(tab_names)
                
                for i, tab_name in enumerate(tab_names):
                    with tabs[i]:
                        active_df = grup_verileri[tab_name]
                        
                        col_search, col_info = st.columns([3, 1])
                        with col_search:
                            search_term = st.text_input(f"🔍 '{tab_name}' içinde ara:", key=f"search_{i}")
                        with col_info:
                            st.markdown(f"### {len(active_df)} Kişi")
                        
                        display_df = active_df
                        if search_term:
                            mask = display_df.apply(lambda x: x.astype(str).str.contains(search_term, case=False, na=False)).any(axis=1)
                            display_df = display_df[mask]
                        
                        st.dataframe(display_df, use_container_width=True)
                        
                        if st.button(f"🗑️ '{tab_name}' Grubunu Sil", key=f"del_tab_{i}"):
                            st.session_state.kurallar.pop(i)
                            st.rerun()

    except Exception as e:
        st.error(f"Hata: {e}")
