import pandas as pd
import streamlit as st
from supabase import create_client

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

kolom_x = ["harga_beras", "harga_minyak_goreng", "harga_gula_pasir",
           "harga_daging_sapi", "harga_telur_ayam"]
kolom_y = "harga_ayam"
semua_kolom = ["tanggal"] + kolom_x + [kolom_y]

# nama komoditas yang ditampilkan di aplikasi
label_kolom = {
    "harga_beras": "Beras",
    "harga_minyak_goreng": "Minyak Goreng",
    "harga_gula_pasir": "Gula Pasir",
    "harga_daging_sapi": "Daging Sapi",
    "harga_telur_ayam": "Telur Ayam",
    "harga_ayam": "Daging Ayam",
}


@st.cache_data(ttl=600, show_spinner="Memuat data dari database...")
def ambil_data():
    """Mengambil seluruh data harga_pangan dari Supabase (di-cache 10 menit)."""
    semua_data = []
    mulai = 0
    ukuran = 1000

    while True:
        respon = (
            supabase.table("harga_pangan")
            .select("*")
            .range(mulai, mulai + ukuran - 1)
            .execute()
        )

        semua_data.extend(respon.data)

        if len(respon.data) < ukuran:
            break

        mulai += ukuran

    data = pd.DataFrame(semua_data)

    if not data.empty:
        data["tanggal"] = pd.to_datetime(data["tanggal"])

    return data


def bersihkan_cache():
    """Dipanggil setelah unggah data agar semua halaman memakai data terbaru."""
    st.cache_data.clear()