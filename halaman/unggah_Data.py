import streamlit as st
import pandas as pd
from koneksi import supabase, semua_kolom

st.set_page_config(page_title="Unggah Data", layout="wide")

st.title("Unggah Data")

st.write(
    "Unggah satu file Excel atau CSV berisi data harga pangan. "
    "Data akan dipraproses sebelum disimpan ke database."
)

file = st.file_uploader(
    "Pilih file Excel atau CSV",
    type=["xlsx", "csv"]
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

#proses simpen data

if st.button("Upload Data"):
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

            st.success(
                f"{len(records)} baris berhasil diproses "
                "dan disimpan ke database."
            )

        except Exception as e:
            st.error(
                f"Terjadi kesalahan saat memproses "
                f"atau menyimpan data: {e}"
            )


st.divider()
st.subheader("Data di Database")

try:
    semua_data = []
    mulai = 0

    while True:
        hasil = (
            supabase.table("harga_pangan")
            .select("*")
            .order("tanggal", desc=True)
            .range(mulai, mulai + 999)
            .execute()
        )

        semua_data.extend(hasil.data)

        if len(hasil.data) < 1000:
            break

        mulai += 1000

#streamlit funsgi untuk pagination

    if semua_data:
        df = pd.DataFrame(semua_data)
        rows_per_page = 100
        total_pages = (len(df) + rows_per_page - 1) // rows_per_page

        dataframe_slot = st.empty()

        with st.container(horizontal_alignment="right"):
            page = st.pagination(num_pages=total_pages)

        start_idx = (page - 1) * rows_per_page
        end_idx = start_idx + rows_per_page

        dataframe_slot.dataframe(df.iloc[start_idx:end_idx],
        )

        st.caption(
            f"Menampilkan data {start_idx + 1}-"
            f"{min(end_idx, len(df))} dari {len(df)} baris"
        )

    else:
        st.info("Belum ada data di database.")

except Exception as e:
    st.error(f"Gagal membaca database: {e}")


    