import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_plotly_events import plotly_events
import plotly.graph_objects as go
from koneksi import supabase, kolom_x, kolom_y


st.title("PARKU")
st.subheader("Prediksi Ayam dengan Regresi Komponen Utama")
st.write(
    "PARKU adalah aplikasi untuk memprediksi harga daging ayam berdasarkan harga "
    "beras, minyak goreng, gula pasir, daging sapi, dan telur ayam menggunakan "
    "metode Regresi Komponen Utama (RKU)."
)

if st.button("Mulai Prediksi"):
    st.switch_page("halaman/prediksi.py")

st.header("Berita")
kol1, kol2, kol3 = st.columns(3)
with kol1:
    with st.container(border=True, height="stretch",):
        st.image("assets/beras.jpeg", width=600)
        st.markdown("**Berita 1**")
        st.write("Harga Beras Bisa Tembus Rp 20.000/Kg Jika RI Terus-terusan Impor")
        st.markdown("[Baca Selengkapnya](https://finance.detik.com/berita-ekonomi-bisnis/d-8648335/harga-beras-bisa-tembus-rp-20-000-kg-jika-ri-terus-terusan-impor)")

with kol2:
    with st.container(border=True, height="stretch",):
        st.image("assets/minyakgoreng.webp", width=600)
        st.markdown("**Berita 2**")
        st.write("Berlaku Mulai Besok, Harga Minyak Goreng Rp 14.000 Per Liter")
        st.markdown("[Baca Selengkapnya](https://nasional.kontan.co.id/news/berlaku-mulai-besok-harga-minyak-goreng-rp-14000-per-liter)")

with kol3:
    with st.container(border=True, height="stretch",):
        st.image("assets/dagingsapi.jpeg", width=600)
        st.markdown("**Berita 3**")
        st.write("BPS Catat Harga Daging Sapi Tembus Rp200 Ribu per Kg Awal Agustus Ini")
        st.markdown("[Baca Selengkapnya](https://www.cnnindonesia.com/ekonomi/20260810115114-92-1390517/bps-catat-harga-daging-sapi-tembus-rp200-ribu-per-kg-awal-agustus-ini)")

st.divider()

kolom_matriks, kolom_grafik = st.columns([1, 1])

with kolom_matriks:
    st.header("Matriks Korelasi")
    st.write(
        "Klik nilai korelasi untuk melihat grafik perbandingan harga dua komoditas.")
# Mengambil seluruh data dari Supabase
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

# Memilih kolom prediktor dan target
kolom_plot = kolom_x + [kolom_y]
data_plot = data[kolom_plot].copy()


# Mengganti nama kolom agar mudah dibaca
nama_kolom = {
    kolom_x[0]: "Harga Beras",
    kolom_x[1]: "Harga Minyak Goreng",
    kolom_x[2]: "Harga Gula Pasir",
    kolom_x[3]: "Harga Daging Sapi",
    kolom_x[4]: "Harga Telur Ayam",
    kolom_y: "Harga Daging Ayam",
}

data_plot = data_plot.rename(columns=nama_kolom)

# Menghitung korelasi Pearson
matriks_korelasi = data_plot.corr(method="pearson")
nama_variabel = matriks_korelasi.columns.tolist()
jumlah = len(nama_variabel)

# Menyiapkan setiap sel matriks sebagai titik yang dapat dipilih
koordinat_x = []
koordinat_y = []
nilai_korelasi = []
pasangan = []

for i, nama_y in enumerate(nama_variabel):
    for j, nama_x in enumerate(nama_variabel):
        koordinat_x.append(j)
        koordinat_y.append(i)
        nilai = matriks_korelasi.loc[nama_y, nama_x]
        nilai_korelasi.append(nilai)
        pasangan.append((nama_y, nama_x))

# Membuat matriks korelasi yang responsif
fig = go.Figure(
    go.Scatter(
        x=koordinat_x,
        y=koordinat_y,
        mode="markers+text",
        text=[f"{v:.2f}" for v in nilai_korelasi],
        textposition="middle center",
        textfont=dict(size=11),
        customdata=[
            [y, x, v]
            for (y, x), v in zip(pasangan, nilai_korelasi)
        ],
        marker=dict(
            symbol="square",
            size=42,
            color=nilai_korelasi,
            colorscale="RdBu_r",
            cmin=-1,
            cmax=1,
            showscale=True,
            colorbar=dict(
                title=dict(text="Pearson", font=dict(size=10)),
                tickfont=dict(size=9),
                thickness=12,
                len=0.75,
            ),
            line=dict(width=1, color="white"),
        ),
        hovertemplate=(
            "%{customdata[0]} dan %{customdata[1]}"
            "<br>Korelasi: %{customdata[2]:.3f}"
            "<extra></extra>"
        ),
    )
)

fig.update_layout(
    autosize=True,
    height=460,
    clickmode="event+select",
    margin=dict(l=5, r=5, t=20, b=100),
    font=dict(size=10),
    xaxis=dict(
        title=None,
        tickmode="array",
        tickvals=list(range(jumlah)),
        ticktext=nama_variabel,
        range=[-0.5, jumlah - 0.5],
        side="bottom",
        tickangle=-45,
        tickfont=dict(size=9),
        fixedrange=True,
        constrain="domain",
    ),
    yaxis=dict(
        title=None,
        tickmode="array",
        tickvals=list(range(jumlah)),
        ticktext=nama_variabel,
        range=[jumlah - 0.5, -0.5],
        tickfont=dict(size=9),
        fixedrange=True,
        scaleanchor="x",
        scaleratio=1,
    ),
)
# Menampilkan matriks yang bisa diklik
with kolom_matriks:
    hasil = st.plotly_chart(
        fig,
        width="stretch",
        key="matriks_pearson_interaktif",
        on_select="rerun",
        selection_mode="points",
        config={
            "responsive": True,
            "displayModeBar": False,
        },
    )

# Membaca sel yang dipilih
with kolom_grafik:
    st.header("Grafik Komoditas")

    titik_dipilih = hasil.selection.points

    if titik_dipilih:
        titik = titik_dipilih[-1]
        indeks = titik.get("point_index")

        if indeks is not None and 0 <= indeks < len(pasangan):
            variabel_y, variabel_x = pasangan[indeks]

            if variabel_x == variabel_y:
                st.info(
                    "Kamu memilih diagonal matriks. "
                    "Silakan klik sel di luar diagonal untuk membandingkan dua komoditas."
                )
            else:
                pearson = matriks_korelasi.loc[
                    variabel_y, variabel_x
                ]

                st.write(
                    f"Grafik Garis: {variabel_x} dan {variabel_y}"
                )


                # Membuat grafik garis dari dua komoditas yang dipilih
                data_garis = data_plot[
                    [variabel_x, variabel_y]
                ].reset_index(drop=True)

                data_garis.index.name = "Urutan Observasi"

                fig_garis = px.line(
                    data_garis,
                    y=[variabel_x, variabel_y],
                    labels={
                        "index": "Urutan Observasi",
                        "value": "Harga (Rp/kg)",
                        "variable": "Komoditas",
                    },
                )

                fig_garis.update_layout(
                    legend_title_text="Komoditas",
                    hovermode="x unified",
                )

                st.plotly_chart(
                    fig_garis,
                    width="stretch",
                )
