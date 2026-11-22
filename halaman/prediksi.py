import streamlit as st

from gaya import hero, rupiah, tanggal_id, ringkasan, grafik_fluktuasi
from koneksi import ambil_data, kolom_x, kolom_y, label_kolom
from model import latih_model, prediksi_harga


hero(
    "Prediksi Harga Daging Ayam",
    "Masukkan harga lima komoditas pangan, lalu lihat estimasinya",
    kecil=True,
)

# font halaman ini dikecilkan (khusus halaman Prediksi)
st.markdown(
    """
    <style>
    div[data-testid="stNumberInput"] label p { font-size: 0.8rem; }
    div[data-testid="stNumberInput"] input { font-size: 0.85rem; }
    div[data-testid="stButton"] button p { font-size: 0.8rem; }
    div[data-testid="stCaptionContainer"] { font-size: 0.75rem; }
    .mini {
        background: #FFFFFF;
        border: 1px solid #E4DBC8;
        border-radius: 12px;
        padding: 0.5rem 0.75rem;
    }
    .mini-label { font-size: 0.7rem; font-weight: 600; color: #7A7364; }
    .mini-nilai {
        font-size: 0.95rem;
        font-weight: 700;
        color: #3D3A35;
        white-space: nowrap;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def kartu_kecil(label, nilai):
    return (
        f'<div class="mini"><div class="mini-label">{label}</div>'
        f'<div class="mini-nilai">{nilai}</div></div>'
    )


data = ambil_data()

if data.empty or len(data) < 30:
    st.info("Data di database belum cukup untuk membangun model. Hubungi admin.")
    st.stop()

model = latih_model(data)

urut = data.sort_values("tanggal")
harga_terakhir = urut.iloc[-1]

# kolom grafik yang sedang ditampilkan (default: harga daging ayam)
if "grafik_aktif" not in st.session_state:
    st.session_state.grafik_aktif = kolom_y

if "hasil_prediksi" not in st.session_state:
    st.session_state.hasil_prediksi = None


def pilih_grafik(kolom):
    st.session_state.grafik_aktif = kolom


kiri, kanan = st.columns([5, 6], gap="large")

# ---------------- kiri: input harga ----------------
with kiri:
    with st.container(border=True):
        st.subheader("Input Harga Komoditas")
        st.caption(
            "Isi harga setiap komoditas. Tekan tombol 📈 di samping kolom "
            "untuk melihat grafik fluktuasi harganya."
        )

        for kolom in kolom_x:
            nama = label_kolom[kolom]

            st.number_input(
                f"Harga {nama} (Rp/kg)",
                min_value=0,
                step=100,
                key=f"input_{kolom}",
                help=f"Harga terakhir di data: {rupiah(harga_terakhir[kolom])}",
            )

            # tombol fluktuasi tepat di bawah input
            aktif = st.session_state.grafik_aktif == kolom
            st.button(
                f"Fluktuasi Harga {nama}",
                key=f"tombol_{kolom}",
                type="primary" if aktif else "secondary",
                width="stretch",
                on_click=pilih_grafik,
                args=(kolom,),
            )

        if st.button("Prediksi Harga", type="primary", width="stretch"):
            input_baru = [st.session_state[f"input_{k}"] for k in kolom_x]

            if any(v == 0 for v in input_baru):
                st.session_state.hasil_prediksi = {"error": True}
            else:
                st.session_state.hasil_prediksi = {
                    "error": False,
                    "nilai": prediksi_harga(model, input_baru),
                }

#bagian kanan
hasil = st.session_state.hasil_prediksi

with kanan:
    with st.container():
        st.subheader("Hasil Prediksi")

        if hasil is None or hasil["error"]:
            if hasil is not None and hasil["error"]:
                st.warning(
                    "Prediksi tidak dapat dilakukan. "
                    "Pastikan seluruh harga komoditas telah diisi "
                    "dengan nilai lebih dari 0."
                )

            st.markdown(
                '<div class="hasil-kartu hasil-kosong">'
                '<div class="hasil-label">Prediksi Harga Daging Ayam</div>'
                '<div class="hasil-nilai">Rp -</div>'
                '<div class="hasil-delta">Isi form lalu tekan "Prediksi Harga"</div>'
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            nilai = hasil["nilai"]
            selisih = nilai - harga_terakhir[kolom_y]
            panah = "▲" if selisih >= 0 else "▼"

            st.markdown(
                '<div class="hasil-kartu">'
                '<div class="hasil-label">Prediksi Harga Daging Ayam</div>'
                f'<div class="hasil-nilai">{rupiah(nilai, 2)} /Kg</div>'
                f'<div class="hasil-delta">{panah} {rupiah(abs(selisih))} '
                f"dibanding harga terakhir di data "
                f"({tanggal_id(harga_terakhir['tanggal'])}: "
                f"{rupiah(harga_terakhir[kolom_y])})</div>"
                "</div>",
                unsafe_allow_html=True,
            )

        st.caption(
            "Hasil prediksi merupakan estimasi berdasarkan data historis, "
            "bukan kepastian harga."
        )

    st.write("")

    with st.container():
        kolom_grafik = st.session_state.grafik_aktif
        nama_grafik = label_kolom[kolom_grafik]

        st.subheader(f"Fluktuasi Harga {nama_grafik}")

        # garis putus-putus hanya untuk hasil prediksi harga ayam
        garis = None
        nama_garis = "Prediksi"

        if kolom_grafik == kolom_y:
            if hasil is not None and not hasil["error"]:
                garis = hasil["nilai"]

        st.plotly_chart(
            grafik_fluktuasi(data, kolom_grafik, nama_grafik,
                                garis=garis, nama_garis=nama_garis),
            width="stretch",
        )

        r = ringkasan(data, kolom_grafik)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Terakhir", rupiah(r["terakhir"]))
        m2.metric("Rata-rata", rupiah(r["rata"]))
        m3.metric("Tertinggi", rupiah(r["maks"]))
        m4.metric("Terendah", rupiah(r["min"]))

        if kolom_grafik != kolom_y:
            st.button(
                "↺ Tampilkan harga daging ayam",
                on_click=pilih_grafik,
                args=(kolom_y,),
            )
