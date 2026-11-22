import streamlit as st

from gaya import hero

hero(
    "Informasi PARKU",
    "Prediksi Harga Daging Ayam Berdasarkan Harga Sembako "
    "Menggunakan Metode Regresi Komponen Utama",
    kecil=True,
)

#informasi ttg aplkasi
with st.container(border=True):
    kol_logo, kol_teks = st.columns([1, 4], vertical_alignment="center")

    with kol_logo:
        st.image("assets/logountar.png")

    with kol_teks:
        st.subheader("Tentang PARKU")
        st.write(
            """
            PARKU (Prediksi Ayam dengan Regresi Komponen Utama)
            merupakan aplikasi yang digunakan untuk memperkirakan
            harga daging ayam berdasarkan harga beras, minyak goreng,
            gula pasir, daging sapi, dan telur ayam dengan menggunakan
            metode Regresi Komponen Utama (RKU).
            """
        )

# kegunaan aplikasi
with st.container(border=True):
    st.subheader("Kegunaan Aplikasi")

    st.write(
        """
        Perubahan harga bahan pangan dapat menimbulkan pertanyaan
        mengenai kemungkinan perubahan harga komoditas pangan lainnya,
        termasuk daging ayam. PARKU dikembangkan untuk membantu pengguna
        memperoleh estimasi harga daging ayam berdasarkan harga beberapa
        komoditas pangan yang dimasukkan ke dalam aplikasi.
        """
    )

    st.markdown(
        """
        Melalui aplikasi ini, pengguna dapat:
        - **Memperkirakan harga daging ayam** berdasarkan harga
        komoditas pangan yang dimasukkan.
        - **Mengetahui estimasi harga daging ayam** ketika terdapat
        perubahan harga pada komoditas prediktor.
        - **Melihat fluktuasi harga** setiap komoditas pada halaman Prediksi.
        """
    )

    st.info(
        """
        Hasil prediksi merupakan estimasi berdasarkan model RKU
        yang dibangun dari data historis, bukan kepastian bahwa
        harga daging ayam akan naik atau turun. Harga aktual juga
        dapat dipengaruhi oleh faktor lain, seperti permintaan,
        pasokan, biaya produksi, dan distribusi.
        """
    )

kiri, kanan = st.columns(2, gap="large")

with kiri:
    with st.container(border=True, height="stretch"):
        st.subheader("Dikembangkan oleh")

        st.write("**Noel Liman**")
        st.write("NIM: 535230067")
        st.write("Program Studi: Teknik Informatika")
        st.write("Universitas Tarumanagara")

with kanan:
    with st.container(border=True, height="stretch"):
        st.subheader("Dibimbing oleh")

        st.write("**Pembimbing 1:**")
        st.write("Prof. Dr. Ir. Dyah Erny Herwindiati, M.Si.")

        st.write("**Pembimbing 2:**")
        st.write("Novario Jaya Perdana, S.Kom., M.T.")

with st.container(border=True):
    st.subheader("Manual Book")

    st.write(
        "Unduh manual book untuk melihat panduan penggunaan "
        "aplikasi PARKU."
    )

    with open("assets/535230067_Manual_Book_Parku.pdf", "rb") as file:
        st.download_button(
            label="📥 Download Manual Book",
            data=file,
            file_name="User_Manual_Book_PARKU.pdf",
            mime="application/pdf",
            width="stretch",
        )
