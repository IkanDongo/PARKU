import numpy as np
import streamlit as st

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error,
    r2_score
)

from koneksi import kolom_x, kolom_y


# Model RKU dihitung sekali lalu disimpan di cache,
# supaya halaman Prediksi dan Admin tidak menghitung ulang setiap interaksi.
# Cache otomatis diperbarui kalau data di database berubah (setelah unggah data).
@st.cache_data(show_spinner="Melatih model RKU...")
def latih_model(data):

    dataX = data[kolom_x].astype(float).values
    dataY = data[kolom_y].astype(float).values.reshape(-1, 1)

    #bagi data split train test 8020

    X_train_raw, Xtest, Y_train_raw, Ytest = train_test_split(
        dataX,
        dataY,
        test_size=0.2,
        random_state=9707
    )

    #pcr

    X = X_train_raw
    Y = Y_train_raw

    n, p = X.shape
    n_awal = n

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

    dfTot = nx - 1
    Fhit = msReg / msRes


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

    # semua hasil dikumpulkan supaya bisa dipakai di halaman lain
    return {
        "men": men,
        "sd": np.sqrt(S.diagonal()),
        "VA_Komponen": VA_Komponen,
        "BZ": BZ,
        "menY": menY,
        "sdY": sdY,
        "komponen": komponen,
        "n_awal": n_awal,
        "n_bersih": n,
        "n_test": nTest,
        "jumlah_outlier": jumlah_outlier,
        "eigen": eValue[:, 0],
        "proporsi": proporsi,
        "proporsi_kumulatif": proporsi_kumulatif,
        "ssReg": ssReg,
        "ssRes": ssRes,
        "ssTot": ssTot,
        "dfReg": dfReg,
        "dfRes": dfRes,
        "dfTot": dfTot,
        "msReg": msReg,
        "msRes": msRes,
        "Fhit": Fhit,
        "r2": r2_test,
        "mae": mae,
        "mse": mse,
        "rmse": rmse,
        "mape": mape,
        "y_test": Ytest[:, 0],
        "y_hat": YhatAsli[:, 0],
    }


def prediksi_harga(model, input_baru):
    """Prediksi harga ayam dari 5 harga komoditas (urutan sesuai kolom_x)."""
    input_baru = np.array(input_baru, dtype=float)

    VA_Komponen = model["VA_Komponen"]

    Z_baru = input_baru - model["men"]
    Zr_baru = Z_baru / model["sd"]

    W_baru = Zr_baru @ VA_Komponen
    Z_bintang_baru = W_baru @ VA_Komponen.T

    Z_model_baru = np.hstack([
        np.ones((1, 1)),
        Z_bintang_baru.reshape(1, -1)
    ])

    Y_prediksi_Z = Z_model_baru @ model["BZ"]

    return Y_prediksi_Z[0, 0] * model["sdY"] + model["menY"]
