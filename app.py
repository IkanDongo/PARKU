import streamlit as st

from gaya import inject_css

st.set_page_config(page_title="PARKU", layout="wide", page_icon="🐔")
inject_css()

# status login disimpan di session_state
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">🐔 PARKU</div>'
        '<div class="sidebar-sub">Prediksi Ayam Regresi Komponen Utama</div>',
        unsafe_allow_html=True,
    )
    st.divider()

beranda = st.Page("halaman/beranda.py", title="Beranda", default=True)
prediksi = st.Page("halaman/prediksi.py", title="Prediksi")
informasi = st.Page("halaman/informasi.py", title="Informasi")
admin = st.Page("halaman/admin.py", title="Admin")

# menu menyesuaikan peran (halaman Admin hanya muncul setelah login)
if st.session_state.is_admin:
    daftar_halaman = [beranda, prediksi, informasi, admin]
else:
    daftar_halaman = [beranda, prediksi, informasi]

pg = st.navigation(daftar_halaman, position="sidebar")

# form login / logout di sidebar
with st.sidebar:


    if st.session_state.is_admin:
        st.success("Login sebagai Admin")
        if st.button("Logout", width="stretch"):
            st.session_state.is_admin = False
            st.rerun()
    else:
        with st.expander("Login Admin"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login", width="stretch", type="primary"):
                if (
                    username == st.secrets["admin"]["username"]
                    and password == st.secrets["admin"]["password"]
                ):
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("Username atau password salah.")

pg.run()
