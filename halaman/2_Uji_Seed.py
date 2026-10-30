
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error,
)

from koneksi import supabase, kolom_x, kolom_y


st.set_page_config(page_title="Uji Random State", layout="wide")
st.title("Uji Random State (Train/Test Split)")
st.caption(
    "Menjalankan proses PCR, deteksi outlier menggunakan Cook's Distance, "
    "pemodelan akhir, dan evaluasi data test untuk berbagai random_state."
)


KOLOM_HASIL = [
    "seed",
    "komponen",
    "outlier",
    "R2",
    "MAE",
    "RMSE",
    "MAPE",
]


# =========================================================
# 1. AMBIL DATA DARI SUPABASE
# =========================================================
@st.cache_data(ttl=600, show_spinner="Mengambil data dari database...")
def ambil_data():
    semua = []
    mulai = 0
    ukuran = 1000

    while True:
        r = (
            supabase.table("harga_pangan")
            .select("*")
            .range(mulai, mulai + ukuran - 1)
            .execute()
        )

        semua.extend(r.data)

        if len(r.data) < ukuran:
            break

        mulai += ukuran

    data = pd.DataFrame(semua)

    if data.empty:
        return np.empty((0, len(kolom_x))), np.empty(0)

    data = data.dropna(subset=list(kolom_x) + [kolom_y])

    X = data[kolom_x].astype(float).to_numpy()
    Y = data[kolom_y].astype(float).to_numpy()

    valid = np.isfinite(X).all(axis=1) & np.isfinite(Y)

    return X[valid], Y[valid]


dataX, dataY = ambil_data()


# =========================================================
# 2. PEMODELAN PCR
# =========================================================
def pcr_fit(X, Y, pk):
    n, p = X.shape

    if n <= p + 1:
        raise ValueError("Jumlah data training terlalu sedikit.")

    if not 0 < pk <= 1:
        raise ValueError("Proporsi kumulatif harus lebih dari 0 dan maksimal 1.")

    men = X.mean(axis=0)
    sd = X.std(axis=0, ddof=1)

    if np.any(sd == 0) or not np.isfinite(sd).all():
        raise ValueError("Terdapat prediktor dengan standar deviasi nol.")

    Zr = (X - men) / sd

    matriks = (Zr.T @ Zr) / (n - 1)
    ev, V = np.linalg.eigh(matriks)

    idx = np.argsort(ev)[::-1]
    ev = ev[idx]
    V = V[:, idx]

    ev = np.maximum(ev, 0)

    if ev.sum() <= 0:
        raise ValueError("Total eigenvalue tidak valid.")

    cum = np.cumsum(ev / ev.sum())
    k = min(int(np.searchsorted(cum, pk)) + 1, p)

    VA = V[:, :k]

    menY = Y.mean()
    sdY = Y.std(ddof=1)

    if not np.isfinite(sdY) or sdY == 0:
        raise ValueError("Standar deviasi target tidak valid.")

    Zry = (Y - menY) / sdY

    W = Zr @ VA
    A = np.column_stack([np.ones(n), W])

    b = np.linalg.lstsq(A, Zry, rcond=None)[0]

    BZ = np.concatenate([[b[0]], VA @ b[1:]])

    return {
        "men": men,
        "sd": sd,
        "k": k,
        "menY": menY,
        "sdY": sdY,
        "Zr": Zr,
        "Zry": Zry,
        "BZ": BZ,
    }


# =========================================================
# 3. MENJALANKAN SATU RANDOM STATE
# =========================================================
def jalankan(seed, dataX, dataY, test_size, pk1, pk2):
    Xtr, Xte, Ytr, Yte = train_test_split(
        dataX,
        dataY,
        test_size=test_size,
        random_state=seed,
    )

    # Tahap 1: deteksi outlier menggunakan Cook's Distance
    m1 = pcr_fit(Xtr, Ytr, pk1)

    n = len(Ytr)
    Zm = np.column_stack([np.ones(n), m1["Zr"]])

    err = m1["Zry"] - Zm @ m1["BZ"]

    px = Zm.shape[1]
    df_res = n - px

    if df_res <= 0:
        raise ValueError("Derajat bebas residual tidak mencukupi.")

    msRes = np.sum(err ** 2) / df_res

    if not np.isfinite(msRes) or msRes <= 0:
        raise ValueError("Mean square residual tidak valid.")

    Hii = np.einsum(
        "ij,jk,ik->i",
        Zm,
        np.linalg.pinv(Zm.T @ Zm),
        Zm,
    )

    penyebut = np.maximum(1 - Hii, np.finfo(float).eps)

    di = (err ** 2 / (px * msRes)) * (Hii / penyebut ** 2)

    batas = 3 * di.mean()
    bersih = di <= batas

    if bersih.sum() <= len(kolom_x) + 1:
        raise ValueError(
            "Data training bersih terlalu sedikit setelah menghapus outlier."
        )

    # Tahap 2: model PCR pada data training bersih
    Xbersih = Xtr[bersih]
    Ybersih = Ytr[bersih]

    m2 = pcr_fit(Xbersih, Ybersih, pk2)

    Zr2 = m2["Zr"]
    Zry2 = m2["Zry"]

    n2 = len(Ybersih)

    # R2 training bersih berdasarkan prediksi model PCR
    Zm2 = np.column_stack([np.ones(n2), Zr2])
    Yhat_train_z = Zm2 @ m2["BZ"]

    ssRes = np.sum((Zry2 - Yhat_train_z) ** 2)
    ssTot = np.sum((Zry2 - Zry2.mean()) ** 2)

    if ssTot <= 0:
        raise ValueError("Total sum of squares tidak valid.")

    r2 = (1 - ssRes / ssTot) * 100

    # Evaluasi pada data test yang tidak digunakan untuk fitting
    Zte = (Xte - m2["men"]) / m2["sd"]

    Yhat = (
        np.column_stack([np.ones(len(Zte)), Zte]) @ m2["BZ"]
    ) * m2["sdY"] + m2["menY"]

    mse = mean_squared_error(Yte, Yhat)

    return {
        "seed": int(seed),
        "komponen": int(m2["k"]),
        "outlier": int((~bersih).sum()),
        "R2": float(r2),
        "MAE": float(mean_absolute_error(Yte, Yhat)),
        "RMSE": float(np.sqrt(mse)),
        "MAPE": float(mean_absolute_percentage_error(Yte, Yhat) * 100),
    }


# =========================================================
# 4. MENJALANKAN SEMUA RANDOM STATE
# =========================================================
@st.cache_data(show_spinner=False)
def jalankan_semua(dataX, dataY, seed_awal, seed_akhir, test_size, pk1, pk2):
    baris = []
    gagal = []

    total = seed_akhir - seed_awal + 1

    bar = st.progress(0.0, text="Menjalankan uji seed...")

    for i, s in enumerate(range(seed_awal, seed_akhir + 1), start=1):
        try:
            hasil_seed = jalankan(s, dataX, dataY, test_size, pk1, pk2)
            baris.append(hasil_seed)

        except (np.linalg.LinAlgError, ValueError, ZeroDivisionError) as e:
            gagal.append({
                "seed": s,
                "penyebab": str(e),
            })

        bar.progress(
            i / total,
            text=f"Seed {s} dari {seed_akhir}",
        )

    bar.empty()

    hasil = pd.DataFrame(baris, columns=KOLOM_HASIL)

    return hasil, pd.DataFrame(gagal)


# =========================================================
# 5. PENGATURAN
# =========================================================
st.info(
    f"Data dari database: {dataX.shape[0]} baris, "
    f"{dataX.shape[1]} prediktor."
)

if len(dataX) < 5:
    st.error("Data tidak mencukupi untuk menjalankan uji random state.")
    st.stop()

with st.form("form_uji"):
    c1, c2, c3 = st.columns(3)

    seed_awal = c1.number_input(
        "Seed awal",
        min_value=0,
        value=1,
        step=1,
    )

    seed_akhir = c2.number_input(
        "Seed akhir",
        min_value=1,
        value=123,
        step=1,
    )

    seed_app = c3.number_input(
        "Seed yang dipakai di aplikasi",
        min_value=0,
        value=1,
        step=1,
    )

    c4, c5, c6 = st.columns(3)

    test_size = c4.slider(
        "Proporsi data test",
        0.1,
        0.5,
        0.2,
        0.05,
    )

    pk1 = c5.slider(
        "Proporsi kumulatif tahap 1 (outlier)",
        0.5,
        1.0,
        0.95,
        0.01,
    )

    pk2 = c6.slider(
        "Proporsi kumulatif tahap 2 (model)",
        0.5,
        1.0,
        0.95,
        0.01,
    )

    tombol = st.form_submit_button(
        "Jalankan Uji",
        use_container_width=True,
    )

if not tombol:
    st.stop()

if seed_akhir < seed_awal:
    st.error("Seed akhir harus lebih besar atau sama dengan seed awal.")
    st.stop()


# =========================================================
# 6. HASIL
# =========================================================
hasil, gagal = jalankan_semua(
    dataX,
    dataY,
    int(seed_awal),
    int(seed_akhir),
    test_size,
    pk1,
    pk2,
)

if not gagal.empty:
    with st.expander(f"Seed yang gagal ({len(gagal)})"):
        st.dataframe(gagal, use_container_width=True, hide_index=True)

if hasil.empty or "R2" not in hasil.columns:
    st.error("Tidak ada seed yang berhasil menghasilkan evaluasi.")
    st.stop()

st.success(
    f"{len(hasil)} seed berhasil dari "
    f"{int(seed_akhir) - int(seed_awal) + 1} seed yang diuji."
)

# Ringkasan seluruh seed
st.subheader("Ringkasan seluruh seed")

ringkas = (
    hasil.drop(columns="seed")
    .describe()
    .loc[["mean", "std", "min", "50%", "max"]]
    .rename(index={"50%": "median"})
    .round(3)
)

st.dataframe(ringkas, use_container_width=True)

# Posisi seed aplikasi
st.subheader(f"Posisi seed {int(seed_app)} (dipakai di aplikasi)")

baris_app = hasil[hasil["seed"] == int(seed_app)]

if baris_app.empty:
    st.warning(
        "Seed aplikasi tidak termasuk dalam seed yang berhasil diuji. "
        "Pastikan seed berada dalam rentang pengujian."
    )
else:
    st.dataframe(
        baris_app.round(3),
        use_container_width=True,
        hide_index=True,
    )

    m1c, m2c, m3c = st.columns(3)

    for kol, wadah in zip(
        ["R2", "MAPE", "RMSE"],
        [m1c, m2c, m3c],
    ):
        nilai = baris_app[kol].iloc[0]
        persentil = (hasil[kol] <= nilai).mean() * 100

        wadah.metric(
            kol,
            f"{nilai:,.3f}",
            f"persentil {persentil:.0f}",
            delta_color="off",
        )

    st.caption(
        "Persentil R² tinggi menunjukkan nilai R² lebih tinggi dibandingkan "
        "banyak seed lain. Untuk MAPE dan RMSE, persentil rendah lebih baik. "
        "R² dihitung dari data training bersih, sedangkan MAE, RMSE, dan "
        "MAPE dihitung dari data test."
    )

# Grafik sebaran
st.subheader("Sebaran per seed")

g1, g2 = st.columns(2)

with g1:
    st.caption("R² (%) per seed")
    st.line_chart(hasil.set_index("seed")["R2"])

with g2:
    st.caption("MAPE (%) per seed")
    st.line_chart(hasil.set_index("seed")["MAPE"])

# Jumlah komponen
st.subheader("Jumlah komponen yang terpilih")

st.dataframe(
    hasil["komponen"]
    .value_counts()
    .sort_index()
    .rename("jumlah seed")
    .to_frame(),
    use_container_width=True,
)

# Tabel lengkap
st.subheader("Hasil lengkap")

st.dataframe(
    hasil.round(3),
    use_container_width=True,
    hide_index=True,
)

# Unduh CSV
st.download_button(
    "Unduh hasil (CSV)",
    hasil.to_csv(index=False).encode("utf-8"),
    file_name="hasil_uji_seed.csv",
    mime="text/csv",
)
