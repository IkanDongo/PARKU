import pandas as pd
import streamlit as st

from gaya import hero, rupiah, tanggal_id, grafik_fluktuasi
from koneksi import (
    supabase,
    semua_kolom,
    kolom_x,
    kolom_y,
    label_kolom,
    ambil_data,
    bersihkan_cache,
)
from model import latih_model

# hanya admin yang boleh membuka halaman ini
if not st.session_state.get("is_admin", False):
    st.error("Halaman ini hanya bisa diakses oleh admin.")
    st.stop()

hero(
    "Panel Admin",
    "Kelola data, tinjau hasil model, dan pantau grafik harga",
    kecil=True,
    label="Akses Admin",
)


def proses_data(file):
    if file.name.lower().endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        df = pd.read_csv(file)

    df.columns = [str(col).strip() for col in df.columns]

    komoditas = [
        "Beras",
        "Minyak Goreng",
        "Gula Pasir",
        "Daging Ayam",
        "Daging Sapi",
        "Telur Ayam",
    ]

    if len(df.columns) < 3:
        raise ValueError("Format file tidak sesuai.")

    komoditas_col = df.columns[1]
    data = df[df[komoditas_col].isin(komoditas)].copy()

    tidak_ada = [
        k for k in komoditas
        if k not in data[komoditas_col].values
    ]

    if tidak_ada:
        raise ValueError(
            "Komoditas tidak ditemukan: " + ", ".join(tidak_ada)
        )

    data = data.drop(columns=data.columns[0])
    data = data.set_index(komoditas_col).T
    data.index.name = "Tgl"
    data = data.reset_index()

    data["Tgl"] = pd.to_datetime(
        data["Tgl"].astype(str).str.replace(" ", "", regex=False),
        dayfirst=True,
        errors="coerce"
    )

    for col in data.columns[1:]:
        data[col] = (
            data[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .replace("-", pd.NA)
            .replace("", pd.NA)
            .replace("nan", pd.NA)
        )

        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.sort_values("Tgl")
    data = data.dropna(subset=["Tgl"])
    data = data.drop_duplicates(subset="Tgl", keep="last")

    if data.empty:
        raise ValueError("Tidak ada tanggal yang valid.")

    data = data.set_index("Tgl")

    tanggal_lengkap = pd.date_range(
        start=data.index.min(),
        end=data.index.max(),
        freq="D"
    )

    data = data.reindex(tanggal_lengkap)
    data.index.name = "Tgl"
    data = data.ffill().reset_index()

    data["Tgl"] = data["Tgl"].dt.strftime("%Y-%m-%d")

    data = data.rename(columns={
        "Tgl": "tanggal",
        "Beras": "harga_beras",
        "Minyak Goreng": "harga_minyak_goreng",
        "Gula Pasir": "harga_gula_pasir",
        "Daging Sapi": "harga_daging_sapi",
        "Telur Ayam": "harga_telur_ayam",
        "Daging Ayam": "harga_ayam",
    })

    data = data[semua_kolom]

    sebelum = len(data)
    data = data.dropna()
    data = data.drop_duplicates(subset="tanggal", keep="last")
    dibuang = sebelum - len(data)

    if data.empty:
        raise ValueError("Tidak ada data valid untuk diunggah.")

    return data, dibuang


tab_unggah, tab_model, tab_grafik = st.tabs(
    ["Unggah Data", "Hasil Model", "Grafik Harga"]
)

#Unggah data
with tab_unggah:
    with st.container(border=True):
        st.subheader("Unggah Data")
        st.write(
            "Unggah satu file Excel atau CSV berisi data harga pangan. "
            "Data akan dipraproses sebelum disimpan ke database."
        )

        file = st.file_uploader(
            "Pilih file Excel atau CSV",
            type=["xlsx", "csv"]
        )

        #proses simpen data
        if st.button("Upload Data", type="primary"):
            if file is None:
                st.warning("Silakan pilih file terlebih dahulu atau file yang diunggah tidak sesuai dengan format.")
            else:
                try:
                    with st.spinner("Memproses dan menyimpan data..."):
                        # Prapemrosesan data
                        hasil, dibuang = proses_data(file)

                        # Simpan langsung ke Supabase
                        records = hasil.to_dict("records")

                        for i in range(0, len(records), 500):
                            (
                                supabase.table("harga_pangan")
                                .upsert(
                                    records[i:i + 500],
                                    on_conflict="tanggal"
                                )
                                .execute()
                            )

                        # supaya semua halaman memakai data terbaru
                        bersihkan_cache()

                    st.success(
                        f"{len(records)} baris berhasil diproses "
                        "dan disimpan ke database."
                    )

                except Exception as e:
                    st.error(
                        f"Terjadi kesalahan saat memproses "
                        f"atau menyimpan data: {e}"
                    )

    with st.container(border=True):
        st.subheader("Data di Database")

        try:
            df = ambil_data()

            if df.empty:
                st.info("Belum ada data di database.")
            else:
                df = df.sort_values("tanggal", ascending=False).reset_index(drop=True)
                df["tanggal"] = df["tanggal"].dt.strftime("%Y-%m-%d")

                rows_per_page = 100
                total_pages = (len(df) + rows_per_page - 1) // rows_per_page

                dataframe_slot = st.empty()

                #streamlit funsgi untuk pagination
                if hasattr(st, "pagination"):
                    with st.container(horizontal_alignment="right"):
                        page = st.pagination(num_pages=total_pages)
                else:
                    page = st.number_input("Halaman", 1, total_pages, 1)

                start_idx = (page - 1) * rows_per_page
                end_idx = start_idx + rows_per_page

                dataframe_slot.dataframe(
                    df.iloc[start_idx:end_idx],
                    width="stretch",
                )

                st.caption(
                    f"Menampilkan data {start_idx + 1}-"
                    f"{min(end_idx, len(df))} dari {len(df)} baris"
                )

        except Exception as e:
            st.error(f"Gagal membaca database: {e}")

# data terbaru untuk tab lain
data = ambil_data()

# Hasil model
with tab_model:
    if data.empty or len(data) < 30:
        st.info("Data di database belum cukup untuk membangun model.")
    else:
        model = latih_model(data)

        st.subheader("Evaluasi Model RKU")

        e1, e2, e3, e4, e5 = st.columns(5)
        e1.metric("R²", f"{model['r2']:.2f}%")
        e2.metric("MAPE", f"{model['mape']:.2f}%")
        e3.metric("MAE", rupiah(model["mae"]))
        e4.metric("RMSE", rupiah(model["rmse"]))
        e5.metric("MSE", f"{model['mse']:,.2f}")

        st.write("")
        

# Grafik harga
with tab_grafik:
    if data.empty:
        st.info("Belum ada data di database.")
    else:
        st.subheader("Grafik Harga Masing-masing Komoditas")

        tgl_min = data["tanggal"].min().date()
        tgl_maks = data["tanggal"].max().date()

        rentang = st.date_input(
            "Rentang tanggal",
            value=(tgl_min, tgl_maks),
            min_value=tgl_min,
            max_value=tgl_maks,
        )

        if isinstance(rentang, tuple) and len(rentang) == 2:
            awal, akhir = rentang
        else:
            awal, akhir = tgl_min, tgl_maks

        data_filter = data[
            (data["tanggal"].dt.date >= awal) & (data["tanggal"].dt.date <= akhir)
        ]

        if data_filter.empty:
            st.info("Tidak ada data pada rentang tanggal tersebut.")
        else:
            semua = [kolom_y] + kolom_x

            for baris in range(0, len(semua), 2):
                cols = st.columns(2, gap="large")

                for c, kolom in zip(cols, semua[baris:baris + 2]):
                    with c:
                        with st.container(border=True):
                            st.plotly_chart(
                                grafik_fluktuasi(
                                    data_filter, kolom, label_kolom[kolom],
                                    tinggi=300, kompak=True,
                                ),
                                width="stretch",
                                key=f"grafik_admin_{kolom}",
                            )
                            st.caption(
                                f"Terakhir {rupiah(data_filter.sort_values('tanggal').iloc[-1][kolom])} "
                                f"({tanggal_id(data_filter['tanggal'].max())})"
                            )
