import streamlit as st

st.set_page_config(page_title="PARKU", layout="wide", page_icon="🐔")

# status login disimpan di session_state
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

with st.sidebar:
    st.title("🐔 PARKU")
    st.caption("Prediksi Ayam Regresi Komponen Utama")
    st.divider()

beranda = st.Page("halaman/beranda.py", title="Beranda", default=True)
prediksi = st.Page("halaman/prediksi.py", title="Prediksi")
informasi = st.Page("halaman/informasi.py", title="Informasi")
unggah = st.Page("halaman/unggah_Data.py", title="Unggah Data")

# menu menyesuaikan peran
if st.session_state.is_admin:
    daftar_halaman = [beranda, unggah, prediksi, informasi]
else:
    daftar_halaman = [beranda, prediksi, informasi]

pg = st.navigation(daftar_halaman, position="sidebar")

# form login / logout di sidebar
with st.sidebar:

    if st.session_state.is_admin:
        st.success("Login sebagai Admin")
        if st.button("Logout", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()
    else:
        with st.expander("Login Admin"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login", use_container_width=True):
                if (
                    username == st.secrets["admin"]["username"]
                    and password == st.secrets["admin"]["password"]
                ):
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("Username atau password salah.")

pg.run()