import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from gaya import hero, rupiah, tanggal_id
from koneksi import ambil_data, kolom_x, kolom_y, label_kolom


hero(
    "PARKU",
    "Prediksi Ayam dengan Regresi Komponen Utama",
    "Aplikasi untuk memprediksi harga daging ayam berdasarkan harga beras, "
    "minyak goreng, gula pasir, daging sapi, dan telur ayam menggunakan "
    "metode Regresi Komponen Utama (RKU).",
    label="🐔 Prediksi Harga Pangan",
)

if st.button("Mulai Prediksi →", type="primary"):
    st.switch_page("halaman/prediksi.py")

# Mengambil seluruh data dari Supabase
data = ambil_data()

if data.empty:
    st.info("Belum ada data di database. Admin dapat mengunggah data terlebih dahulu.")
    st.stop()

# Ringkasan data
urut = data.sort_values("tanggal")
terakhir = urut.iloc[-1]
acuan = urut[urut["tanggal"] <= terakhir["tanggal"] - pd.Timedelta(days=30)]

if acuan.empty:
    delta = None
else:
    selisih = terakhir[kolom_y] - acuan.iloc[-1][kolom_y]
    tanda = "+" if selisih >= 0 else "-"
    delta = f"{tanda}{rupiah(abs(selisih))} / 30 hari"

k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "Harga Daging Ayam Terbaru",
    rupiah(terakhir[kolom_y]),
    delta=delta,
    delta_color="inverse",
)
k2.metric("Rata-rata Harga Ayam", rupiah(urut[kolom_y].mean()))
k3.metric("Jumlah Data", f"{len(urut):,} hari".replace(",", "."))
k4.metric(
    "Periode Data",
    f"{tanggal_id(urut['tanggal'].min(), hari=False)} - "
    f"{tanggal_id(urut['tanggal'].max(), hari=False)}",
)

st.write("")

# Memilih kolom prediktor dan target
kolom_plot = kolom_x + [kolom_y]
data_plot = data[kolom_plot].copy()
data_tanggal = data["tanggal"].copy()

# Mengganti nama kolom agar mudah dibaca
nama_kolom = {k: "Harga " + label_kolom[k] for k in kolom_plot}
data_plot = data_plot.rename(columns=nama_kolom)

# Menghitung korelasi Pearson
matriks_korelasi = data_plot.corr(method="pearson")
nama_variabel = matriks_korelasi.columns.tolist()
jumlah = len(nama_variabel)

# Nama singkat untuk label sumbu
nama_pendek = [n.replace("Harga ", "") for n in nama_variabel]

# Titik transparan di atas setiap sel, supaya sel bisa diklik
koordinat_x = []
koordinat_y = []
pasangan = []
info_sel = []

for i, nama_y in enumerate(nama_variabel):
    for j, nama_x in enumerate(nama_variabel):
        koordinat_x.append(j)
        koordinat_y.append(i)
        pasangan.append((nama_y, nama_x))
        info_sel.append([nama_pendek[i], nama_pendek[j],
                         matriks_korelasi.loc[nama_y, nama_x]])

nilai = matriks_korelasi.values
teks = [[f"{v:.2f}" for v in b] for b in nilai]

fig = go.Figure()

# tampilan matriks (heatmap, tanpa garis tepi)
fig.add_trace(
    go.Heatmap(
        z=nilai,
        x=list(range(jumlah)),
        y=list(range(jumlah)),
        zmin=-1,
        zmax=1,
        colorscale=[[0, "#6E93A8"], [0.5, "#F5F0E4"], [1, "#B8744A"]],
        text=teks,
        texttemplate="%{text}",
        textfont=dict(size=11, color="#3D3A35"),
        hoverinfo="skip",
        colorbar=dict(
            thickness=10,
            len=0.8,
            tickfont=dict(size=10),
            outlinewidth=0,
        ),
    )
)

# lapisan klik (tidak terlihat)
fig.add_trace(
    go.Scatter(
        x=koordinat_x,
        y=koordinat_y,
        mode="markers",
        marker=dict(symbol="square", size=52, color="rgba(0,0,0,0)"),
        customdata=info_sel,
        hovertemplate=(
            "%{customdata[0]} dan %{customdata[1]}"
            "<br>Korelasi: %{customdata[2]:.3f}"
            "<extra></extra>"
        ),
        showlegend=False,
    )
)

fig.update_layout(
    autosize=True,
    height=400,
    clickmode="event+select",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=10, b=10),
    font=dict(size=11, family="Plus Jakarta Sans, sans-serif"),
    xaxis=dict(
        title=None,
        tickmode="array",
        tickvals=list(range(jumlah)),
        ticktext=nama_pendek,
        range=[-0.5, jumlah - 0.5],
        tickangle=-40,
        tickfont=dict(size=10),
        fixedrange=True,
        showgrid=False,
        zeroline=False,
        showline=False,
        automargin=True,
    ),
    yaxis=dict(
        title=None,
        tickmode="array",
        tickvals=list(range(jumlah)),
        ticktext=nama_pendek,
        range=[jumlah - 0.5, -0.5],
        tickfont=dict(size=10),
        fixedrange=True,
        showgrid=False,
        zeroline=False,
        showline=False,
        automargin=True,
    ),
)

kiri, kanan = st.columns([4, 6], gap="large")

# Menampilkan matriks yang bisa diklik
with kiri:
    with st.container():
        st.subheader("Matriks Korelasi")
        st.caption(
            "Klik nilai korelasi untuk melihat grafik perbandingan harga dua komoditas."
        )
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
with kanan:
    with st.container():
        st.subheader("Grafik Komoditas")

        titik_dipilih = hasil.selection.points

        if not titik_dipilih:
            st.info("Pilih salah satu sel pada matriks korelasi untuk menampilkan grafik.")
        else:
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
                    pearson = matriks_korelasi.loc[variabel_y, variabel_x]

                    st.caption(
                        f"{variabel_x} dan {variabel_y} "
                        f"(korelasi Pearson: {pearson:.3f})"
                    )

                    # Membuat grafik garis dari dua komoditas yang dipilih
                    data_garis = data_plot[[variabel_x, variabel_y]].copy()
                    data_garis.insert(0, "tanggal", data_tanggal)
                    data_garis = data_garis.sort_values("tanggal")

                    fig_garis = px.line(
                        data_garis,
                        x="tanggal",
                        y=[variabel_x, variabel_y],
                        labels={
                            "tanggal": "Tanggal",
                            "value": "Harga (Rp/kg)",
                            "variable": "Komoditas",
                        },
                        color_discrete_sequence=["#B8744A", "#6E93A8"],
                    )

                    fig_garis.update_layout(
                        height=440,
                        separators=",.",
                        hovermode="x unified",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=10, r=10, t=10, b=10),
                        legend=dict(
                            title_text="",
                            orientation="h",
                            yanchor="top",
                            y=-0.2,
                            xanchor="center",
                            x=0.5,
                        ),
                        xaxis=dict(
                            tickformat="%b %Y",
                            tickangle=-45,
                            gridcolor="#F1EBDD",
                        ),
                        yaxis=dict(
                            tickformat=",.0f",
                            gridcolor="#E9E2D2",
                        ),
                    )

                    st.plotly_chart(fig_garis, width="stretch")

st.write("")
st.header("Berita")
kol1, kol2, kol3 = st.columns(3)

with kol1:
    with st.container(border=True, height="stretch"):
        st.image("assets/beras.jpeg", width=600)
        st.markdown("**Berita 1**")
        st.write("Harga Beras Bisa Tembus Rp 20.000/Kg Jika RI Terus-terusan Impor")
        st.markdown("[Baca Selengkapnya](https://finance.detik.com/berita-ekonomi-bisnis/d-8648335/harga-beras-bisa-tembus-rp-20-000-kg-jika-ri-terus-terusan-impor)")

with kol2:
    with st.container(border=True, height="stretch"):
        st.image("assets/minyakgoreng.webp", width=600)
        st.markdown("**Berita 2**")
        st.write("Berlaku Mulai Besok, Harga Minyak Goreng Rp 14.000 Per Liter")
        st.markdown("[Baca Selengkapnya](https://nasional.kontan.co.id/news/berlaku-mulai-besok-harga-minyak-goreng-rp-14000-per-liter)")

with kol3:
    with st.container(border=True, height="stretch"):
        st.image("assets/dagingsapi.jpeg", width=600)
        st.markdown("**Berita 3**")
        st.write("BPS Catat Harga Daging Sapi Tembus Rp200 Ribu per Kg Awal Agustus Ini")
        st.markdown("[Baca Selengkapnya](https://www.cnnindonesia.com/ekonomi/20260810115114-92-1390517/bps-catat-harga-daging-sapi-tembus-rp200-ribu-per-kg-awal-agustus-ini)")
