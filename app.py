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
            st.info("Değer aralıklarını girin (Sadece tam sayı):")
            cols = st.columns(len(secilen_sutunlar))
            
            for i, sutun in enumerate(secilen_sutunlar):
                with cols[i]:
                    st.markdown(f"**{sutun}**")
                    # Varsayılan min-max değerlerini bul (Tam sayıya çevirerek)
                    min_val, max_val = 0, 100
                    if pd.api.types.is_numeric_dtype(df[sutun]):
                        # int() fonksiyonu ile küsüratları atıyoruz
                        min_val = int(df[sutun].min())
                        max_val = int(df[sutun].max())
                    
                    # step=1 ve format="%d" ile sadece tam sayı girişine izin veriyoruz
                    girilen_min = st.number_input(f"Min Değer", value=min_val, step=1, format="%d", key=f"min_{sutun}")
                    girilen_max = st.number_input(f"Max Değer", value=max_val, step=1, format="%d", key=f"max_{sutun}")
                    
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
                    
                    for sutun, (min_v, max_v) in kural['filtreler'].items():
                        # Ekrana yazarken de tam sayı olarak gösteriyoruz
                        st.markdown(f"- **{sutun}**: **{int(min_v)}** ile **{int(max_v)}** arası *(Başlangıç ve bitiş değerleri dahildir)*")
                    
                    st.write("") 
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
