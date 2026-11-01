import streamlit as st

st.set_page_config(page_title="PARKU", layout="wide", page_icon="🐔",)



with st.sidebar:
    st.title("🐔 PARKU")
    st.caption("Prediksi Ayam Regresi Komponen Utama")
    st.divider()

beranda = st.Page("halaman/beranda.py", title="Beranda", default=True)
unggah = st.Page("halaman/unggah_Data.py", title="Unggah Data")
prediksi = st.Page("halaman/prediksi.py", title="Prediksi" )
informasi = st.Page("halaman/informasi.py", title="Informasi")

pg = st.navigation([beranda, unggah, prediksi, informasi], position="sidebar")
pg.run()