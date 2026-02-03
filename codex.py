import streamlit as st
import pandas as pd
from datetime import datetime

# --- AYARLAR ---
st.set_page_config(page_title="CODEX Şantiye v2.0", layout="wide", page_icon="🏗️")

# --- HAFIZA (SESSION STATE) ---
if 'sozlesme' not in st.session_state:
    st.session_state['sozlesme'] = pd.DataFrame(columns=["İş Kodu", "Tanım", "Birim", "Birim Fiyat"])

if 'imalatlar' not in st.session_state:
    st.session_state['imalatlar'] = pd.DataFrame(columns=["Tarih", "Taşeron", "İş Kodu", "Miktar", "Fotoğraf", "Durum"])

if 'gecmis_odemeler' not in st.session_state:
    st.session_state['gecmis_odemeler'] = pd.DataFrame(columns=["Ödeme Tarihi", "Ödenen Tutar", "Açıklama"])

if 'kesintiler' not in st.session_state:
    st.session_state['kesintiler'] = {"Avans": 0.0, "Yemek": 0.0, "Konaklama": 0.0}

# --- YAN MENÜ ---
st.sidebar.title("🏗️ CODEX V2.0")
rol = st.sidebar.radio("Rol Seçiniz:", ["Proje Müdürü", "Taşeron (Usta)", "Saha Mühendisi", "Patron / Muhasebe"])
st.sidebar.info("Muhasebe Onayı Eklendi ✅")

# --- ROL 1: PROJE MÜDÜRÜ ---
if rol == "Proje Müdürü":
    st.title("📋 Sözleşme Yönetimi")
    col1, col2, col3, col4 = st.columns(4)
    with col1: is_kodu = st.text_input("İş Kodu (Örn: CP-01)")
    with col2: tanim = st.text_input("İş Tanımı")
    with col3: birim = st.selectbox("Birim", ["m2", "m3", "adet", "mt"])
    with col4: fiyat = st.number_input("Birim Fiyat (TL)", min_value=0.0)

    if st.button("Sözleşmeye Ekle"):
        if is_kodu and tanim and fiyat > 0:
            yeni = pd.DataFrame({"İş Kodu": [is_kodu], "Tanım": [tanim], "Birim": [birim], "Birim Fiyat": [fiyat]})
            st.session_state['sozlesme'] = pd.concat([st.session_state['sozlesme'], yeni], ignore_index=True)
            st.success("Eklendi")

    st.dataframe(st.session_state['sozlesme'], use_container_width=True)

# --- ROL 2: TAŞERON ---
elif rol == "Taşeron (Usta)":
    st.title("🧱 İmalat Bildirimi")
    if not st.session_state['sozlesme'].empty:
        sozlesme_listesi = st.session_state['sozlesme']['İş Kodu'].tolist()
        secilen = st.selectbox("İş Kalemi", sozlesme_listesi)
        taseron = st.text_input("Taşeron Adı")
        miktar = st.number_input("Miktar", min_value=1.0)
        
        if st.button("Onaya Gönder"):
            yeni_is = pd.DataFrame({
                "Tarih": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                "Taşeron": [taseron],
                "İş Kodu": [secilen],
                "Miktar": [miktar],
                "Fotoğraf": ["Görsel Var ✅"],
                "Durum": ["ONAY BEKLİYOR"]
            })
            st.session_state['imalatlar'] = pd.concat([st.session_state['imalatlar'], yeni_is], ignore_index=True)
            st.success("Gönderildi!")
    else:
        st.warning("Sözleşme yok.")

# --- ROL 3: SAHA MÜHENDİSİ ---
elif rol == "Saha Mühendisi":
    st.title("👷‍♂️ Saha Kontrol")
    
    # Sadece ONAY BEKLEYENLERİ göster
    bekleyenler = st.session_state['imalatlar'][st.session_state['imalatlar']['Durum'] == "ONAY BEKLİYOR"]
    
    if not bekleyenler.empty:
        for i, row in bekleyenler.iterrows():
            with st.expander(f"{row['Taşeron']} - {row['İş Kodu']} ({row['Miktar']})"):
                c1, c2 = st.columns(2)
                if c1.button("✅ KABUL", key=f"k_{i}"):
                    st.session_state['imalatlar'].at[i, 'Durum'] = "ONAYLANDI"
                    st.rerun()
                if c2.button("❌ RED", key=f"r_{i}"):
                    st.session_state['imalatlar'].at[i, 'Durum'] = "REDDEDİLDİ"
                    st.rerun()
    else:
        st.info("Onay bekleyen iş yok.")
    
    st.divider()
    st.caption("Tüm Liste")
    st.dataframe(st.session_state['imalatlar'])

# --- ROL 4: PATRON / MUHASEBE (YENİLENEN KISIM) ---
elif rol == "Patron / Muhasebe":
    st.title("💰 Muhasebe ve Ödeme Ekranı")
    st.markdown("Bu ekran sadece **Mühendis Onayı** almış ama henüz **Parası Ödenmemiş** işleri gösterir.")

    # Sadece ONAYLANDI olanları (Ödenmemişleri) çek
    odenecekler = st.session_state['imalatlar'][st.session_state['imalatlar']['Durum'] == "ONAYLANDI"]

    if not odenecekler.empty:
        # Hesaplama Yap
        tablo = pd.merge(odenecekler, st.session_state['sozlesme'], on="İş Kodu", how="left")
        tablo["Tutar"] = tablo["Miktar"] * tablo["Birim Fiyat"]
        toplam_hakedis = tablo["Tutar"].sum()

        # Kesintiler
        st.subheader("1. Kesintileri Girin")
        col_k1, col_k2, col_k3 = st.columns(3)
        avans = col_k1.number_input("Avans", value=st.session_state['kesintiler']['Avans'])
        yemek = col_k2.number_input("Yemek", value=st.session_state['kesintiler']['Yemek'])
        konak = col_k3.number_input("Konaklama", value=st.session_state['kesintiler']['Konaklama'])
        
        st.session_state['kesintiler'] = {"Avans": avans, "Yemek": yemek, "Konaklama": konak}
        toplam_kesinti = avans + yemek + konak

        net_odeme = toplam_hakedis - toplam_kesinti

        # Özet Gösterge
        st.info(f"💵 ÖDENECEK NET TUTAR: **{net_odeme:,.2f} TL**")
        st.dataframe(tablo[["Tarih", "Taşeron", "Tanım", "Miktar", "Tutar"]])

        # --- KRİTİK BUTON: MUHASEBE ONAYI ---
        st.markdown("---")
        st.subheader("2. İşlemi Tamamla")
        
        if st.button("✅ Ödemeyi Onayla ve Kayıtlara İşle"):
            # 1. Ödemeyi Geçmişe Kaydet
            yeni_odeme = pd.DataFrame({
                "Ödeme Tarihi": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                "Ödenen Tutar": [net_odeme],
                "Açıklama": [f"{len(tablo)} kalem iş ödemesi yapıldı."]
            })
            st.session_state['gecmis_odemeler'] = pd.concat([st.session_state['gecmis_odemeler'], yeni_odeme], ignore_index=True)

            # 2. Ödenen İşlerin Durumunu Değiştir (Listeden düşsün)
            for index, row in odenecekler.iterrows():
                st.session_state['imalatlar'].at[index, 'Durum'] = "ÖDENDİ (KAPANDI)"
            
            # 3. Kesintileri Sıfırla (Yeni ay için)
            st.session_state['kesintiler'] = {"Avans": 0.0, "Yemek": 0.0, "Konaklama": 0.0}
            
            st.success("Ödeme başarıyla kaydedildi! Liste temizlendi.")
            st.rerun()

    else:
        st.success("Şu an ödeme bekleyen onaylı bir iş yok. Her şey ödendi.")

    # --- GEÇMİŞ ÖDEMELER TABLOSU ---
    st.divider()
    st.subheader("📂 Geçmiş Ödemeler (Arşiv)")
    if not st.session_state['gecmis_odemeler'].empty:
        st.dataframe(st.session_state['gecmis_odemeler'])
    else:
        st.caption("Henüz yapılmış bir ödeme yok.")