import streamlit as st
import pandas as pd
import numpy as np
import statsmodels.api as sm

from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error,
    r2_score
)

from koneksi import supabase, kolom_x, kolom_y


st.set_page_config(page_title="Prediksi", layout="wide")
st.title("Prediksi Harga Daging Ayam")


#ambil data dri supabase
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

    semua_data = semua_data + respon.data

    if len(respon.data) < ukuran:
        break

    mulai = mulai + ukuran

data = pd.DataFrame(semua_data)

dataX = data[kolom_x].astype(float).values
dataY = data[kolom_y].astype(float).values.reshape(-1, 1)


#bagi data split train test 8020

X_train_raw, Xtest, Y_train_raw, Ytest = train_test_split(
    dataX,
    dataY,
    test_size=0.2,
    random_state=8264
)

#pcr 

X = X_train_raw
Y = Y_train_raw

n, p = X.shape

men = X.mean(axis=0)

Z = np.zeros((n, p))

for i in range(n):
    kurang = X[i, :] - men
    Z[i, :] = kurang

S = np.zeros((p, p))

for j in range(p):
    for k in range(p):
        sum_cov = 0
        for i in range(n):
            sum_cov = sum_cov + Z[i, j] * Z[i, k]

        S[j, k] = sum_cov / (n - 1)

Zr = np.zeros((n, p))

for i in range(n):
    for j in range(p):
        Zr[i, j] = Z[i, j] / np.sqrt(S[j, j])

Zcov = np.zeros((p, p))

for j in range(p):
    for k in range(p):
        sum_cov = 0

        for i in range(n):
            sum_cov = sum_cov + Zr[i, j] * Zr[i, k]

        Zcov[j, k] = sum_cov / (n - 1)

D, V = np.linalg.eigh(Zcov)

DA_urut = np.zeros((p, p))
VA_urut = np.zeros((p, p))

m = 0

for i in range(p - 1, -1, -1):
    DA_urut[m, m] = D[i]
    VA_urut[:, m] = V[:, i]
    m = m + 1

eValue = np.zeros((p, 1))

for i in range(p):
    eValue[i, 0] = DA_urut[i, i]

Total = eValue.sum()

PK = 0
komponen = 0

for j in range(p):
    proporsiValue = eValue[j, 0] / Total

    if PK < 0.95:
        PK = PK + proporsiValue
        komponen = komponen + 1

VA_Komponen = VA_urut[:, 0:komponen]

W = Zr @ VA_Komponen

menY = Y.mean()
sdY = np.std(Y, ddof=1)

Zy = np.zeros((n, 1))

for i in range(n):
    kurang = Y[i, 0] - menY
    Zy[i, 0] = kurang

Zry = np.zeros((n, 1))

for i in range(n):
    Zry[i, 0] = Zy[i, 0] / sdY

w0 = np.ones((n, 1))
wModel1 = np.hstack([w0, W])

b = np.linalg.inv(wModel1.T @ wModel1) @ (wModel1.T @ Zry)

Bw0 = b[0, 0]
Bw = b[1:, :]

BdiZ = VA_Komponen @ Bw

BZ = np.vstack([
    np.array([[Bw0]]),
    BdiZ
])

z0 = np.ones((n, 1))
Zmodel1 = np.hstack([z0, Zr])

YhatZ = Zmodel1 @ BZ

error = Zry - YhatZ

ssReg = (
    BZ.T @ (Zmodel1.T @ Zry)
)[0, 0] - n * (Zry.mean()) ** 2

ssRes = (
    Zry.T @ Zry
)[0, 0] - (
    BZ.T @ (Zmodel1.T @ Zry)
)[0, 0]

nx, px = Zmodel1.shape

dfRes = nx - px
msRes = ssRes / dfRes


#hat matriks dan cookdistance
H = (
    Zmodel1
    @ np.linalg.inv(Zmodel1.T @ Zmodel1)
    @ Zmodel1.T
)

Hii = np.zeros((n, 1))

for i in range(n):
    Hii[i, 0] = H[i, i]

Eii = error ** 2

di = (
    Eii / (px * msRes)
) * (
    Hii / (1 - Hii) ** 2
)

di_rata = di.mean()
cutoff = 3 * di_rata

#hapus oultier dari training data
dataTrain = np.hstack([
    X_train_raw,
    Y_train_raw
])

outlier = []
data_bersih80 = []

for i in range(n):

    if di[i, 0] > cutoff:
        outlier.append(i + 1)

    else:
        data_bersih80.append(dataTrain[i, :])

data_bersih80 = np.array(data_bersih80)

jumlah_outlier = len(outlier)


# pcr lagi dengan data bersih
X = data_bersih80[:, 0:p]
Y = data_bersih80[:, p].reshape(-1, 1)

n = X.shape[0]

men = X.mean(axis=0)

Z = np.zeros((n, p))

for i in range(n):
    kurang = X[i, :] - men
    Z[i, :] = kurang

S = np.zeros((p, p))

for j in range(p):
    for k in range(p):
        sum_cov = 0

        for i in range(n):
            sum_cov = sum_cov + Z[i, j] * Z[i, k]

        S[j, k] = sum_cov / (n - 1)

Zr = np.zeros((n, p))

for i in range(n):
    for j in range(p):
        Zr[i, j] = Z[i, j] / np.sqrt(S[j, j])

Zcov = np.zeros((p, p))

for j in range(p):
    for k in range(p):
        sum_cov = 0

        for i in range(n):
            sum_cov = sum_cov + Zr[i, j] * Zr[i, k]

        Zcov[j, k] = sum_cov / (n - 1)

D, V = np.linalg.eigh(Zcov)

DA_urut = np.zeros((p, p))
VA_urut = np.zeros((p, p))

m = 0

for i in range(p - 1, -1, -1):
    DA_urut[m, m] = D[i]
    VA_urut[:, m] = V[:, i]
    m = m + 1

eValue = np.zeros((p, 1))

for i in range(p):
    eValue[i, 0] = DA_urut[i, i]

Total = eValue.sum()

PK = 0
komponen = 0

proporsi = np.zeros(p)

for j in range(p):

    proporsi[j] = eValue[j, 0] / Total

    if PK < 0.90:
        PK = PK + proporsi[j]
        komponen = komponen + 1

proporsi_kumulatif = np.cumsum(proporsi)

VA_Komponen = VA_urut[:, 0:komponen]

W = Zr @ VA_Komponen

menY = Y.mean()
sdY = np.std(Y, ddof=1)

Zy = np.zeros((n, 1))

for i in range(n):
    kurang = Y[i, 0] - menY
    Zy[i, 0] = kurang

Zry = np.zeros((n, 1))

for i in range(n):
    Zry[i, 0] = Zy[i, 0] / sdY

w0 = np.ones((n, 1))
wModel1 = np.hstack([w0, W])

b = np.linalg.inv(wModel1.T @ wModel1) @ (wModel1.T @ Zry)

Bw0 = b[0, 0]
Bw = b[1:, :]

BdiZ = VA_Komponen @ Bw

BZ = np.vstack([
    np.array([[Bw0]]),
    BdiZ
])

z0 = np.ones((n, 1))
Zmodel1 = np.hstack([z0, Zr])

YhatZ = Zmodel1 @ BZ

error = Zry - YhatZ


#tabel anova
ssReg = (
    BZ.T @ (Zmodel1.T @ Zry)
)[0, 0] - n * (Zry.mean()) ** 2

ssRes = (
    Zry.T @ Zry
)[0, 0] - (
    BZ.T @ (Zmodel1.T @ Zry)
)[0, 0]

ssTot = (
    Zry.T @ Zry
)[0, 0] - n * (Zry.mean()) ** 2

nx, px = Zmodel1.shape

dfReg = px - 1
msReg = ssReg / dfReg

dfRes = nx - px
msRes = ssRes / dfRes



#evaluasi data testing
nTest = Xtest.shape[0]

Ztest = np.zeros((nTest, p))

for i in range(nTest):
    for j in range(p):
        Ztest[i, j] = Xtest[i, j] - men[j]

Zrtest = np.zeros((nTest, p))

for i in range(nTest):
    for j in range(p):
        Zrtest[i, j] = Ztest[i, j] / np.sqrt(S[j, j])

Wtest = Zrtest @ VA_Komponen

ZBintangTest = Wtest @ VA_Komponen.T

Zytest = np.zeros((nTest, 1))

for i in range(nTest):
    kurang = Ytest[i, 0] - menY
    Zytest[i, 0] = kurang

Zrytest = np.zeros((nTest, 1))

for i in range(nTest):
    Zrytest[i, 0] = Zytest[i, 0] / sdY

z0test = np.ones((nTest, 1))

ZmodelTest = np.hstack([
    z0test,
    ZBintangTest
])

YhatZTest = ZmodelTest @ BZ

errorZtest = Zrytest - YhatZTest


#kembaliin ke skala asli
YhatAsli = YhatZTest * sdY + menY


#eval model

r2_test = r2_score(Ytest, YhatAsli) * 100

mae = mean_absolute_error(Ytest, YhatAsli)

mse = mean_squared_error(Ytest, YhatAsli)

rmse = np.sqrt(mse)

mape = mean_absolute_percentage_error(
    Ytest,
    YhatAsli
) * 100


#tampilan aplikasi
kiri, kanan = st.columns(2)

with kiri:

    st.subheader("Input Harga Komoditas")

    with st.form("form_prediksi"):

        beras = st.number_input(
            "Harga Beras (Rp/kg)",
            min_value=0,
            step=100
        )

        minyak = st.number_input(
            "Harga Minyak Goreng (Rp/kg)",
            min_value=0,
            step=100
        )

        gula = st.number_input(
            "Harga Gula Pasir (Rp/kg)",
            min_value=0,
            step=100
        )

        sapi = st.number_input(
            "Harga Daging Sapi (Rp/kg)",
            min_value=0,
            step=100
        )

        telur = st.number_input(
            "Harga Telur Ayam (Rp/kg)",
            min_value=0,
            step=100
        )

        tombol = st.form_submit_button(
            "Prediksi Harga",
            use_container_width=True
        )


with kanan:

    st.subheader("Hasil Prediksi")

    if tombol:

        input_baru = np.array([
            beras,
            minyak,
            gula,
            sapi,
            telur
        ], dtype=float)

        # Validasi input tidak boleh 0
        if np.any(input_baru == 0):

            st.warning(
                "Prediksi tidak dapat dilakukan. "
                "Pastikan seluruh harga komoditas telah diisi "
                "dengan nilai lebih dari 0."
            )

        else:

            Z_baru = input_baru - men

            Zr_baru = Z_baru / np.sqrt(S.diagonal())

            W_baru = Zr_baru @ VA_Komponen

            Z_bintang_baru = W_baru @ VA_Komponen.T

            Z_model_baru = np.hstack([
                np.ones((1, 1)),
                Z_bintang_baru.reshape(1, -1)
            ])

            Y_prediksi_Z = Z_model_baru @ BZ

            hasil_prediksi = (
                Y_prediksi_Z[0, 0] * sdY + menY
            )

            st.metric(
                "Prediksi Harga Daging Ayam",
                f"Rp {hasil_prediksi:,.2f} /Kg"
            )

    else:

        st.metric(
            "Prediksi Harga Daging Ayam",
            "Rp 0.00 /Kg"
        )

    # Hasil evaluasi model
    if tombol and all(
        nilai > 0
        for nilai in [beras, minyak, gula, sapi, telur]
    ):

        st.subheader("Hasil Evaluasi Model")

        e1, e2 = st.columns(2)

        e1.metric(
            "R²",
            f"{r2_test:.2f}%"
        )

        e2.metric(
            "MAPE",
            f"{mape:.2f}%"
        )

        st.divider()

        e3, e4, e5 = st.columns(3)

        e3.metric(
            "MAE",
            f"Rp {mae:,.2f}"
        )

        e4.metric(
            "RMSE",
            f"Rp {rmse:,.2f}"
        )

        e5.metric(
            "MSE",
            f"{mse:,.2f}"
        )