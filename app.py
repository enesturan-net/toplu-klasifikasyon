import streamlit as st
import pandas as pd
import io
import json
import plotly.express as px
import plotly.io as pio
from datetime import datetime

# Sayfa Ayarları
st.set_page_config(page_title="İK Analiz Pro & Raporlama", layout="wide", page_icon="📊")
st.title("🚀 RobotİK - Analiz ve Otomatik Raporlama")

# Session State
if 'kurallar' not in st.session_state:
    st.session_state.kurallar = []

# --- HTML RAPOR OLUŞTURMA FONKSİYONU ---
def create_html_report(df, rules):
    # 1. İstatistikleri Hesapla
    toplam_kisi = len(df)
    rapor_tarihi = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    kategori_verileri = []
    kategori_isimleri = []
    kategori_sayilari = []
    
    for kural in rules:
        temp_df = df.copy()
        # Sayısal Filtre
        for s, (mn, mx) in kural['filtreler']['sayisal'].items():
            if s in temp_df.columns:
                temp_df = temp_df[(temp_df[s] >= mn) & (temp_df[s] <= mx)]
        # Kategorik Filtre
        for s, v in kural['filtreler']['kategorik'].items():
            if s in temp_df.columns:
                temp_df = temp_df[temp_df[s].isin(v)]
        
        count = len(temp_df)
        yuzde = (count / toplam_kisi * 100) if toplam_kisi > 0 else 0
        
        kategori_verileri.append({
            "isim": kural['kategori'],
            "sayi": count,
            "yuzde": yuzde,
            "kriterler_sayisal": kural['filtreler']['sayisal'],
            "kriterler_kategorik": kural['filtreler']['kategorik']
        })
        kategori_isimleri.append(kural['kategori'])
        kategori_sayilari.append(count)

    # 2. Pasta Grafiği Oluştur (Genel Dağılım)
    fig_pie = px.pie(
        names=kategori_isimleri, 
        values=kategori_sayilari, 
        title="Kategorilere Göre Çalışan Dağılımı",
        hole=0.4
    )
    fig_pie.update_layout(title_x=0.5) # Başlığı ortala
    chart_html = pio.to_html(fig_pie, full_html=False)

    # 3. HTML İçeriğini Hazırla (CSS Tasarımı)
    html_string = f"""
    <html>
    <head>
        <title>Analiz Raporu</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; background-color: #f9f9f9; padding: 20px; }}
            .container {{ max_width: 900px; margin: 0 auto; background: white; padding: 40px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); border-radius: 10px; }}
            h1 {{ color: #2c3e50; text-align: center; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            .meta {{ text-align: center; color: #7f8c8d; margin-bottom: 30px; font-size: 0.9em; }}
            .summary-box {{ display: flex; justify-content: space-around; background: #ecf0f1; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
            .stat {{ text-align: center; }}
            .stat-num {{ font-size: 24px; font-weight: bold; color: #2980b9; }}
            .stat-desc {{ font-size: 14px; color: #555; }}
            .category-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 20px; border-left: 5px solid #3498db; }}
            .cat-title {{ font-size: 18px; font-weight: bold; color: #2c3e50; display: flex; justify-content: space-between; }}
            .cat-stats {{ color: #e67e22; font-weight: bold; }}
            .criteria-list {{ margin-top: 10px; font-size: 14px; color: #555; }}
            .footer {{ text-align: center; margin-top: 50px; color: #aaa; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Yönetici Özeti ve Analiz Raporu</h1>
            <div class="meta">Oluşturulma Tarihi: {rapor_tarihi}</div>

            <div class="summary-box">
                <div class="stat">
                    <div class="stat-num">{toplam_kisi}</div>
                    <div class="stat-desc">Toplam Çalışan</div>
                </div>
                <div class="stat">
                    <div class="stat-num">{len(rules)}</div>
                    <div class="stat-desc">Oluşturulan Grup</div>
                </div>
                <div class="stat">
                    <div class="stat-num">{sum(kategori_sayilari)}</div>
                    <div class="stat-desc">Kategorize Edilen</div>
                </div>
            </div>

            <div style="margin-bottom: 40px;">
                {chart_html}
            </div>

            <h2>📁 Grup Detayları ve Kriterler</h2>
    """

    for kat in kategori_verileri:
        kriter_text = "<ul>"
        # Sayısal kriterleri yaz
        for k, v in kat['kriterler_sayisal'].items():
            kriter_text += f"<li><b>{k}:</b> {int(v[0])} - {int(v[1])} (Dahil)</li>"
        # Kategorik kriterleri yaz
        for k, v in kat['kriterler_kategorik'].items():
            vals = ", ".join(v)
            kriter_text += f"<li><b>{k}:</b> {vals}</li>"
        kriter_text += "</ul>"

        html_string += f"""
            <div class="category-card">
                <div class="cat-title">
                    {kat['isim']}
                    <span class="cat-stats">{kat['sayi']} Kişi (%{kat['yuzde']:.1f})</span>
                </div>
                <div class="criteria-list">
                    <strong>Uygulanan Filtreler:</strong>
                    {kriter_text}
                </div>
            </div>
        """

    html_string += """
            <div class="footer">Bu rapor RobotİK tarafından otomatik olarak oluşturulmuştur.</div>
        </div>
    </body>
    </html>
    """
    return html_string

# --- YAN MENÜ ---
with st.sidebar:
    st.header("💾 Ayar Yönetimi")
    
    if st.session_state.kurallar:
        json_string = json.dumps(st.session_state.kurallar)
        st.download_button("Ayarları İndir (.json)", json_string, "robotik_ayarlari.json", "application/json")
    
    st.divider()
    uploaded_settings = st.file_uploader("Ayar Dosyası Yükle", type=["json"])
    if uploaded_settings:
        if st.button("Ayarları Yükle"):
            try:
                st.session_state.kurallar = json.load(uploaded_settings)
                st.success("Yüklendi!")
                st.rerun()
            except: st.error("Hata")

# --- ANA EKRAN ---
st.header("1. Veri Setini Yükle")
uploaded_file = st.file_uploader("Excel dosyanızı buraya sürükleyin (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("Dosya yüklendi.")
        
        with st.expander("Veri Önizlemesi"):
            st.dataframe(df.head())

        tum_sutunlar = df.columns.tolist()
        sayisal = df.select_dtypes(include=['number']).columns.tolist()
        kategorik = df.select_dtypes(exclude=['number']).columns.tolist()

        st.divider()
        st.header("2. Kategori Oluşturma")
        
        col_m1, col_m2 = st.columns([1, 3])
        kategori_adi = col_m1.text_input("Kategori Adı", key="cat_name")
        
        c1, c2 = st.columns(2)
        sec_sayisal = c1.multiselect("Puan Filtreleri", sayisal)
        sec_kategorik = c2.multiselect("Metin Filtreleri", kategorik)

        filtreler = {"sayisal": {}, "kategorik": {}}
        
        if sec_sayisal:
            st.subheader("Puan Aralıkları")
            cols = st.columns(2)
            for i, s in enumerate(sec_sayisal):
                with cols[i%2]:
                    fig = px.histogram(df, x=s, title=s, height=200)
                    fig.update_layout(margin=dict(l=20,r=20,t=30,b=20))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    mn, mx = int(df[s].min()), int(df[s].max())
                    c_a, c_b = st.columns(2)
                    g_mn = c_a.number_input(f"Min", value=mn, step=1, format="%d", key=f"min_{s}")
                    g_mx = c_b.number_input(f"Max", value=mx, step=1, format="%d", key=f"max_{s}")
                    filtreler["sayisal"][s] = (g_mn, g_mx)

        if sec_kategorik:
            for s in sec_kategorik:
                vals = df[s].dropna().unique().tolist()
                sel = st.multiselect(f"'{s}' İçin:", vals, key=f"k_{s}")
                if sel: filtreler["kategorik"][s] = sel

        if st.button("Listeye Ekle ➕", type="primary"):
            if kategori_adi and (filtreler["sayisal"] or filtreler["kategorik"]):
                st.session_state.kurallar.append({"kategori": kategori_adi, "filtreler": filtreler})
                st.success(f"'{kategori_adi}' eklendi!")

        st.divider()
        st.header("3. Sonuçlar ve Raporlama")

        if st.session_state.kurallar:
            # Özet Tablo Gösterimi (Ekranda)
            ozet_data = []
            for k in st.session_state.kurallar:
                t_df = df.copy()
                for s, (mn, mx) in k['filtreler']['sayisal'].items():
                    if s in t_df: t_df = t_df[(t_df[s]>=mn) & (t_df[s]<=mx)]
                for s, v in k['filtreler']['kategorik'].items():
                    if s in t_df: t_df = t_df[t_df[s].isin(v)]
                
                ozet_data.append({
                    "Kategori": k['kategori'], 
                    "Kişi": len(t_df), 
                    "Oran": f"%{(len(t_df)/len(df)*100):.1f}"
                })
            
            col_res1, col_res2 = st.columns([2,1])
            col_res1.table(pd.DataFrame(ozet_data))
            
            with col_res2:
                st.write("Eklenen Gruplar:")
                for i, k in enumerate(st.session_state.kurallar):
                    if st.button(f"Sil: {k['kategori']}", key=f"del_{i}"):
                        st.session_state.kurallar.pop(i)
                        st.rerun()

            st.divider()
            st.subheader("📥 İndirme Seçenekleri")
            
            col_down1, col_down2 = st.columns(2)
            
            # 1. EXCEL İNDİRME
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Tüm Veri', index=False)
                for k in st.session_state.kurallar:
                    t_df = df.copy()
                    for s, (mn, mx) in k['filtreler']['sayisal'].items():
                        if s in t_df: t_df = t_df[(t_df[s]>=mn) & (t_df[s]<=mx)]
                    for s, v in k['filtreler']['kategorik'].items():
                        if s in t_df: t_df = t_df[t_df[s].isin(v)]
                    safe_name = k['kategori'][:30].replace(":", "")
                    t_df.to_excel(writer, sheet_name=safe_name, index=False)
            
            col_down1.download_button(
                "📊 Excel Verilerini İndir", 
                output_excel.getvalue(), 
                "analiz_sonuclari.xlsx", 
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            # 2. HTML RAPOR İNDİRME
            html_report = create_html_report(df, st.session_state.kurallar)
            col_down2.download_button(
                "📄 Görsel Raporu İndir (HTML)", 
                html_report, 
                "yonetici_ozeti.html", 
                "text/html",
                type="primary",
                use_container_width=True
            )

        else:
            st.info("Rapor oluşturmak için yukarıdan en az bir grup kuralı ekleyin.")

    except Exception as e:
        st.error(f"Hata: {e}")
