import streamlit as st
import pandas as pd
import io

# Sayfa Başlığı ve Ayarları
st.set_page_config(page_title="Excel Kategori Filtreleyici", layout="wide")
st.title("📊 Çalışan Sınıflandırma ve Excel Oluşturucu")

# Session State (Kuralları hafızada tutmak için)
if 'kurallar' not in st.session_state:
    st.session_state.kurallar = []

# 1. ADIM: Excel Yükleme
st.header("1. Excel Dosyasını Yükle")
uploaded_file = st.file_uploader("Excel dosyanızı buraya sürükleyin (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("Dosya başarıyla yüklendi!")
        
        with st.expander("Veri Önizlemesi (Tıklayıp Aç/Kapa)"):
            st.dataframe(df.head())

        # Sütun isimlerini al
        tum_sutunlar = df.columns.tolist()

        st.divider()

        # 2. ADIM: Kural Tanımlama
        st.header("2. Yeni Kategori ve Filtre Kuralı Ekle")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            kategori_adi = st.text_input("Kategori Adı (Örn: İleri Seviye)", key="cat_name")
        
        with col2:
            secilen_sutunlar = st.multiselect("Filtre uygulamak istediğiniz sütunları seçin", tum_sutunlar)

        filtreler = {}
        
        if secilen_sutunlar:
            st.info("Seçilen sütunlar için değer aralıklarını girin (Değerler dahildir):")
            cols = st.columns(len(secilen_sutunlar))
            
            for i, sutun in enumerate(secilen_sutunlar):
                with cols[i]:
                    st.markdown(f"**{sutun}**")
                    # Verideki min ve max değerleri referans olarak bulalım
                    min_val, max_val = 0.0, 100.0
                    if pd.api.types.is_numeric_dtype(df[sutun]):
                        min_val = float(df[sutun].min())
                        max_val = float(df[sutun].max())
                    
                    girilen_min = st.number_input(f"Min", value=min_val, key=f"min_{sutun}")
                    girilen_max = st.number_input(f"Max", value=max_val, key=f"max_{sutun}")
                    
                    filtreler[sutun] = (girilen_min, girilen_max)

        # Kuralı Listeye Ekleme Butonu
        if st.button("Bu Kuralı Listeye Ekle"):
            if kategori_adi and filtreler:
                yeni_kural = {
                    "kategori": kategori_adi,
                    "filtreler": filtreler
                }
                st.session_state.kurallar.append(yeni_kural)
                st.success(f"'{kategori_adi}' kategorisi eklendi!")
            else:
                st.error("Lütfen kategori adı girin ve en az bir sütun seçin.")

        st.divider()

        # 3. ADIM: Eklenen Kuralları Göster ve Excel Oluştur
        st.header("3. Oluşturulacak Sayfalar (Sheetler)")

        if len(st.session_state.kurallar) > 0:
            # Kuralları Listele
            for i, kural in enumerate(st.session_state.kurallar):
                with st.expander(f"📄 Sayfa Adı: {kural['kategori']}", expanded=True):
                    st.markdown("###### Uygulanacak Kriterler:")
                    
                    # --- GÜNCELLENEN KISIM BURASI ---
                    # Dictionary'yi yazdırmak yerine döngü ile cümle kuruyoruz
                    for sutun, (min_v, max_v) in kural['filtreler'].items():
                        # Sayı tam sayı ise virgüllü göstermesin (örn: 25.0 yerine 25 yazsın)
                        gosterilen_min = int(min_v) if min_v == int(min_v) else min_v
                        gosterilen_max = int(max_v) if max_v == int(max_v) else max_v
                        
                        st.markdown(f"- **{sutun}**: *{gosterilen_min}* ile *{gosterilen_max}* arasında olanlar.")
                    # --------------------------------
                    
                    st.write("") # Biraz boşluk
                    if st.button(f"❌ '{kural['kategori']}' kuralını sil", key=f"del_{i}"):
                        st.session_state.kurallar.pop(i)
                        st.rerun()

            st.divider()

            # Excel Oluşturma İşlemi
            st.subheader("✅ Sonuç Dosyasını İndir")
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                
                df.to_excel(writer, sheet_name='Tüm Veri', index=False)
                
                for kural in st.session_state.kurallar:
                    temp_df = df.copy()
                    
                    for sutun, (min_v, max_v) in kural['filtreler'].items():
                        if pd.api.types.is_numeric_dtype(temp_df[sutun]):
                            temp_df = temp_df[
                                (temp_df[sutun] >= min_v) & 
                                (temp_df[sutun] <= max_v)
                            ]
                    
                    sheet_name = kural['kategori'][:30] 
                    temp_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            output.seek(0)
            
            st.download_button(
                label="📥 Excel Dosyasını İndir",
                data=output,
                file_name="kategorize_edilmis_calisanlar.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary" 
            )
            
        else:
            st.info("Henüz hiç kural eklemediniz. Yukarıdan ekleyebilirsiniz.")

    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")

else:
    st.info("Lütfen başlamak için bir Excel dosyası yükleyin.")
