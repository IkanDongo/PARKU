import plotly.graph_objects as go
import streamlit as st

WARNA = {
    "harga_beras": "#6F8A5E",
    "harga_minyak_goreng": "#C2A24D",
    "harga_gula_pasir": "#8E7BA8",
    "harga_daging_sapi": "#A66A5B",
    "harga_telur_ayam": "#6E93A8",
    "harga_ayam": "#B8744A",
}

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
         "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html { font-size: 15px; }
.stApp { font-family: 'Plus Jakarta Sans', system-ui, sans-serif; }
h1, h2, h3, h4 {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
    letter-spacing: -0.01em;
}
h2 { font-size: 1.4rem !important; }
h3 { font-size: 1.12rem !important; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1280px; }
#MainMenu, footer { visibility: hidden; }

.stButton > button, .stDownloadButton > button {
    border-radius: 12px;
    font-weight: 600;
}

div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E4DBC8;
    border-radius: 16px;
    padding: 0.9rem 1.1rem;
    box-shadow: 0 2px 10px rgba(90, 80, 60, 0.08);
    /* tinggi kartu angka dibuat sama, walaupun ada yang punya baris delta */
    min-height: 6.4rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

div[data-testid="stMetricValue"] { font-size: 1.05rem; }
div[data-testid="stMetricLabel"] { font-size: 0.75rem; }
div[data-testid="stMetricDelta"] { font-size: 0.72rem; }
/* angka tidak dipotong jadi "...", kalau panjang turun ke baris berikutnya */
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] > div,
div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] *,
div[data-testid="stMetricDelta"],
div[data-testid="stMetricDelta"] * {
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    overflow-wrap: anywhere;
}

/* hero */
.hero {
    background: linear-gradient(135deg, #BF7D52 0%, #CF9467 55%, #DDAE82 100%);
    color: #FFFFFF;
    padding: 2.2rem 2.4rem;
    border-radius: 22px;
    margin-bottom: 1.2rem;
    box-shadow: 0 10px 28px rgba(191, 125, 82, 0.25);
}
.hero-kecil { padding: 1.5rem 2rem; }
.hero-label {
    display: inline-block;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 999px;
    padding: 0.2rem 0.8rem;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 0.7rem;
}
.hero-judul { font-size: 2rem; font-weight: 800; line-height: 1.1; }
.hero-kecil .hero-judul { font-size: 1.5rem; }
.hero-sub { font-size: 0.95rem; font-weight: 600; opacity: 0.95; margin-top: 0.3rem; }
.hero-isi { font-size: 0.88rem; opacity: 0.9; margin-top: 0.7rem; max-width: 760px; line-height: 1.55; }

/* kartu hasil prediksi */
.hasil-kartu {
    background: linear-gradient(135deg, #F1ECDF 0%, #E6DEC9 100%);
    border: 1px solid #D8CDB2;
    border-radius: 18px;
    padding: 1.3rem 1.5rem;
    margin-bottom: 0.8rem;
}
.hasil-label { font-size: 0.85rem; font-weight: 600; color: #000000; }
.hasil-nilai { font-size: 1.8rem; font-weight: 800; color: #000000; line-height: 1.2; }
.hasil-delta { font-size: 0.82rem; font-weight: 600; color: #000000; margin-top: 0.2rem; }
.hasil-kosong .hasil-nilai { color: #000000; }

.sidebar-brand { font-size: 1.25rem; font-weight: 800; color: #000000; }
.sidebar-sub { font-size: 0.8rem; color: #000000; opacity: 0.8; }

.chip {
    display: inline-block;
    background: #EFE8DC;
    border: 1px solid #E4DBC8;
    color: #000000;
    border-radius: 999px;
    padding: 0.15rem 0.7rem;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 0 0.3rem 0.3rem 0;
}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(judul, subjudul, isi="", label="", kecil=False):
    kelas = "hero hero-kecil" if kecil else "hero"
    html = f'<div class="{kelas}">'
    if label:
        html += f'<div class="hero-label">{label}</div><br>'
    html += f'<div class="hero-judul">{judul}</div>'
    html += f'<div class="hero-sub">{subjudul}</div>'
    if isi:
        html += f'<div class="hero-isi">{isi}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def rupiah(x, desimal=0):
    teks = f"{x:,.{desimal}f}"
    teks = teks.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"Rp {teks}"


def tanggal_id(ts, hari=True):
    if hari:
        return f"{ts.day} {BULAN[ts.month - 1]} {ts.year}"
    return f"{BULAN[ts.month - 1]} {ts.year}"


def ringkasan(df, kolom):
    d = df.sort_values("tanggal")[kolom].dropna()
    return {
        "terakhir": d.iloc[-1],
        "rata": d.mean(),
        "maks": d.max(),
        "min": d.min(),
    }


def grafik_fluktuasi(df, kolom, label, tinggi=360, kompak=False,
                     garis=None, nama_garis="Input Anda"):
    """Grafik garis fluktuasi harga satu komoditas + rata-rata bergerak 30 hari."""
    d = df[["tanggal", kolom]].dropna().sort_values("tanggal")
    warna = WARNA.get(kolom, "#B8744A")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=d["tanggal"],
            y=d[kolom],
            mode="lines",
            name=f"Harga {label}",
            line=dict(color=warna, width=2),
            hovertemplate="Rp %{y:,.0f}<extra>Harga harian</extra>",
        )
    )

    if not kompak and len(d) >= 30:
        rata = d[kolom].rolling(30, min_periods=1).mean()
        fig.add_trace(
            go.Scatter(
                x=d["tanggal"],
                y=rata,
                mode="lines",
                name="Rata-rata 30 hari",
                line=dict(color="#7A7364", width=1.6, dash="dash"),
                hovertemplate="Rp %{y:,.0f}<extra>Rata-rata 30 hari</extra>",
            )
        )

    if garis is not None and garis > 0:
        fig.add_hline(
            y=garis,
            line_dash="dot",
            line_color="#3D3A35",
            annotation_text=f"{nama_garis}: {rupiah(garis)}",
            annotation_position="top left",
            annotation_font=dict(size=11, color="#3D3A35"),
        )

    fig.update_layout(
        height=tinggi,
        separators=",.",
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30 if kompak else 10, b=10),
        font=dict(family="Plus Jakarta Sans, sans-serif", size=12),
        showlegend=not kompak,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0),
        yaxis=dict(title="Rp/kg", tickformat=",.0f", gridcolor="#E9E2D2",
                   zeroline=False),
        xaxis=dict(gridcolor="#F1EBDD", tickformat="%b %Y"),
    )

    if kompak:
        fig.update_layout(title=dict(text=f"<b>{label}</b>", x=0.01,
                                     font=dict(size=14)))

    return fig
