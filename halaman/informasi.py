
import streamlit as st

st.set_page_config(page_title="Informasi", layout="wide")

st.title("Informasi PARKU")

# IDENTITAS APLIKASI

col1 = st.columns(1)[0]

with col1:
    with st.container(border=True):
        st.image(
            "D:/SKRIPSI_/pythontest1/Web/assets/logountar.png",
            width=250
        )

        st.divider()

        st.markdown(
            """
            <h3>
            PREDIKSI HARGA DAGING AYAM BERDASARKAN HARGA SEMBAKO
            MENGGUNAKAN METODE REGRESI KOMPONEN UTAMA
            </h3>
            """,
            unsafe_allow_html=True
        )

        st.write(
            """
            PARKU (Prediksi Ayam dengan Regresi Komponen Utama)
            merupakan aplikasi yang digunakan untuk memperkirakan
            harga daging ayam berdasarkan harga beras, minyak goreng,
            gula pasir, daging sapi, dan telur ayam dengan menggunakan
            metode Regresi Komponen Utama (RKU).
            """
        )

        st.divider()

        # KEGUNAAN APLIKASI
        
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
        st.divider()
        st.subheader("Dikembangkan oleh")

        st.write("**Noel Liman**")
        st.write("NIM: 535230067")
        st.write("Program Studi: Teknik Informatika")
        st.write("Universitas Tarumanagara")

        st.divider()

        st.subheader("Dibimbing oleh")

        st.write("**Pembimbing 1:**")
        st.write("Prof. Dr. Ir. Dyah Erny Herwindiati, M.Si.")

        st.write("**Pembimbing 2:**")
        st.write("Novario Jaya Perdana, S.Kom., M.T.")
