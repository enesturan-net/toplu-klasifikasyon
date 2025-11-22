import streamlit as st
import pandas as pd
import io
import json
import plotly.express as px

# Sayfa Başlığı ve Ayarları
st.set_page_config(page_title="İK Analiz Pro - v2.0", layout="wide")
st.title("🚀 İK Analiz ve Sınıflandırma Robotu v2.0")

# Session State Tanımlamaları
if 'kurallar' not in st.session_state:
    st.session_state.kurallar = []

# --- YAN MENÜ: AYARLARI KAYDET / YÜKLE ---
with st.sidebar:
    st.header("💾 Ayar Yönetimi")
    st.info("Oluşturduğunuz kuralları kaydedip sonra tekrar kullanabilirsiniz.")
    
    # 1. Ayarları İndir
    if st.session_state.kurallar:
        json_string = json.dumps(st.session_state.kurallar)
        st.download_button(
            label="Ayarları Dosya Olarak İndir",
            file_name="kural_ayarlari.json",
            mime="application/json",
            data=json_string
        )
    
    # 2. Ayarları Yükle
    uploaded_settings = st.file_uploader("Ayar Dosyası Yükle (.json)", type=["json"])
    if uploaded_settings is not None:
        try:
            data = json.load(uploaded_settings)
            if isinstance(data, list):
                st.session_state.kurallar = data
                st.success("Ayarlar başarıyla yüklendi!")
            else:
                st.error("Hatalı dosya formatı.")
        except Exception as e:
            st.error(f"Yükleme hatası: {e}")

# --- ANA EKRAN ---

# 1. ADIM: Excel Yükleme
st.header("1. Veri Setini Yükle")
uploaded_file = st.file_uploader("Excel dosyanızı buraya sürükleyin (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("✅ Dosya yüklendi.")
        
        with st.expander("Veri Önizlemesi (Görmek için tıkla)"):
            st.dataframe(df.head())

        # Sütunları Tiplerine Göre Ayır
        tum_sutunlar = df.columns.tolist()
        sayisal_sutunlar = df.select_dtypes(include=['number']).columns.tolist()
        kategorik_sutunlar = df.select_dtypes(exclude=['number']).columns.tolist()

        st.divider()

        # 2. ADIM: Kural Tanımlama
        st.header("2. Kategori Oluşturma")
        
        # Kategori İsmi
        kategori_adi = st.text_input("Kategori Adı (Örn: Yüksek Potansiyel Satış)", key="cat_name")
        
        col_secim1, col_secim2 = st.columns(2)
        
        with col_secim1:
            secilen_sayisal = st.multiselect("Puan/Sayı Bazlı Filtreler", sayisal_sutunlar)
        with col_secim2:
            secilen_kategorik = st.multiselect("Metin Bazlı Filtreler (Departman vb.)", kategorik_sutunlar)

        filtreler = {"sayisal": {}, "kategorik": {}}
        
        # --- SAYISAL FİLTRELER VE GRAFİKLER ---
        if secilen_sayisal:
            st.subheader("🔢 Puan Aralıklarını Belirle")
            # Her 2 sütunu yan yana gösterelim
            cols_num = st.columns(2)
            
            for i, sutun in enumerate(secilen_sayisal):
                col_idx = i % 2
                with cols_num[col_idx]:
                    st.markdown(f"### 📌 {sutun}")
                    
                    # GRAFİK: Kullanıcı karar vermeden önce dağılımı görsün
                    fig = px.histogram(df, x=sutun, nbins=20, title=f"{sutun} Dağılımı", height=250)
                    fig.update_layout(margin=dict(l=20, r=20, t=30, b=20))
                    st.plotly_chart(fig, use_container_width=True)

                    # MİN-MAX GİRİŞİ
                    min_val = int(df[sutun].min())
                    max_val = int(df[sutun].max())
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        g_min = st.number_input(f"Min ({sutun})", value=min_val, step=1, format="%d", key=f"min_{sutun}")
                    with c2:
                        g_max = st.number_input(f"Max ({sutun})", value=max_val, step=1, format="%d", key=f"max_{sutun}")
                    
                    filtreler["sayisal"][sutun] = (g_min, g_max)

        # --- KATEGORİK FİLTRELER ---
        if secilen_kategorik:
            st.subheader("🔤 Metin Bazlı Kısıtlamalar")
            for sutun in secilen_kategorik:
                # O sütundaki benzersiz değerleri bul
                benzersiz_degerler = df[sutun].dropna().unique().tolist()
                secilenler = st.multiselect(
                    f"'{sutun}' sütununda sadece şunlar olsun:", 
                    benzersiz_degerler,
                    key=f"cat_filter_{sutun}"
                )
                if secilenler:
                    filtreler["kategorik"][sutun] = secilenler

        # Ekle Butonu
        if st.button("Listeye Ekle ➕", type="primary"):
            if kategori_adi and (filtreler["sayisal"] or filtreler["kategorik"]):
                yeni_kural = {
                    "kategori": kategori_adi,
                    "filtreler": filtreler
                }
                st.session_state.kurallar.append(yeni_kural)
                st.success(f"✅ '{kategori_adi}' başarıyla eklendi!")
            else:
                st.warning("Lütfen bir isim girin ve en az bir filtre seçin.")

        st.divider()

        # 3. ADIM: Özet Tablo ve Rapor
        st.header("3. Analiz Özeti ve İndirme")

        if len(st.session_state.kurallar) > 0:
            
            # Özet İstatistikleri Hesapla
            ozet_veri = []
            
            for kural in st.session_state.kurallar:
                temp_df = df.copy()
                
                # Sayısal Filtreleme
                for sutun, (min_v, max_v) in kural['filtreler']['sayisal'].items():
                    if sutun in temp_df.columns:
                        temp_df = temp_df[
                            (temp_df[sutun] >= min_v) & (temp_df[sutun] <= max_v)
                        ]
                
                # Kategorik Filtreleme
                for sutun, secilenler in kural['filtreler']['kategorik'].items():
                    if sutun in temp_df.columns:
                        temp_df = temp_df[temp_df[sutun].isin(secilenler)]
                
                kisi_sayisi = len(temp_df)
                toplam_kisi = len(df)
                yuzde = (kisi_sayisi / toplam_kisi) * 100
                
                ozet_veri.append({
                    "Kategori Adı": kural['kategori'],
                    "Kişi Sayısı": kisi_sayisi,
                    "Oran (%)": f"%{yuzde:.1f}"
                })

            # Özeti Tablo Olarak Göster
            col_ozet1, col_ozet2 = st.columns([2, 1])
            with col_ozet1:
                st.subheader("📊 Kategorilere Göre Dağılım")
                st.table(pd.DataFrame(ozet_veri))

            with col_ozet2:
                st.subheader("📋 Eklenen Kurallar")
                for i, kural in enumerate(st.session_state.kurallar):
                    with st.expander(f"{i+1}. {kural['kategori']}"):
                        # Sayısal Açıklama
                        for s, (mn, mx) in kural['filtreler']['sayisal'].items():
                            st.write(f"• **{s}**: {int(mn)} - {int(mx)} (Dahil)")
                        # Kategorik Açıklama
                        for s, vals in kural['filtreler']['kategorik'].items():
                            st.write(f"• **{s}**: {', '.join(vals)}")
                        
                        if st.button("Sil", key=f"del_{i}"):
                            st.session_state.kurallar.pop(i)
                            st.rerun()

            # Excel Oluşturma
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Tüm Veri', index=False)
                
                for kural in st.session_state.kurallar:
                    # Filtreleme Mantığının Aynısı (Excel İçin)
                    t_df = df.copy()
                    for sutun, (min_v, max_v) in kural['filtreler']['sayisal'].items():
                        if sutun in t_df.columns:
                            t_df = t_df[(t_df[sutun] >= min_v) & (t_df[sutun] <= max_v)]
                    
                    for sutun, secilenler in kural['filtreler']['kategorik'].items():
                        if sutun in t_df.columns:
                            t_df = t_df[t_df[sutun].isin(secilenler)]
                            
                    safe_name = kural['kategori'][:30].replace(":", "").replace("/", "")
                    t_df.to_excel(writer, sheet_name=safe_name, index=False)
            
            output.seek(0)
            st.download_button(
                label="📥 Sonuç Excel Dosyasını İndir",
                data=output,
                file_name="analiz_sonuclari.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

        else:
            st.info("Henüz kural eklenmedi.")

    except Exception as e:
        st.error(f"Hata oluştu: {e}")
