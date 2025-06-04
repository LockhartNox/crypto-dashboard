import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt
from datetime import timedelta
from statsmodels.tsa.statespace.sarimax import SARIMAX

# --- PAGE CONFIG ---
st.set_page_config(page_title="Crypto Dashboard", layout="wide")

# --- DARK THEME CSS ---
def inject_dark_theme():
    st.markdown(""" <style>
    .stApp {
    background-color: #121212;
    color: #FFFFFF;
    }
    h1, h2, h3, h4, h5, h6 {
    color: #00FFC6;
    }
    .stTabs [role="tablist"] {
    background-color: #121212;
    border-bottom: 1px solid #333;
    }
    .stTabs [role="tab"] {
    color: #FFFFFF;
    }
    .stTabs [aria-selected="true"] {
    color: #00FFC6;
    border-bottom: 2px solid #00FFC6;
    }
    ::-webkit-scrollbar {
    width: 8px;
    }
    ::-webkit-scrollbar-thumb {
    background: #333;
    border-radius: 10px;
    }
    .custom-metric-box {
    background-color: #333333 !important;
    border: 2px solid #00FFC6;
    border-radius: 10px;
    padding: 15px;
    text-align: center;
    color: #FFFFFF;
    font-weight: bold;
    } </style>
    """, unsafe_allow_html=True)

inject_dark_theme()

# --- HEADER ---
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.title("Crypto Predictor")
with header_col2:
    col_currency = st.selectbox("Mata Uang:", ["USD", "IDR", "EUR"])

st.write("Dashboard Prediksi Harga Crypto")
st.markdown("---")

# --- DICTIONARIES ---x`
crypto_dict = {
    "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "BNB": "BNB-USD",
    "Cardano": "ADA-USD", "Solana": "SOL-USD", "XRP": "XRP-USD",
    "Dogecoin": "DOGE-USD", "Polkadot": "DOT-USD", "Litecoin": "LTC-USD",
    "Chainlink": "LINK-USD", "Tether": "USDT-USD", "Pepe": "PEPE24478-USD",
    "Shiba Inu": "SHIB-USD"
}

crypto_colors = {
    "Bitcoin": "#F7931A", "Ethereum": "#3C3C3D", "BNB": "#F3BA2F",
    "Cardano": "#0033AD", "Solana": "#00FFA3", "XRP": "#25A768",
    "Dogecoin": "#C2A633", "Polkadot": "#E6007A", "Litecoin": "#BEBEBE",
    "Chainlink": "#2A5ADA", "Tether": "#26A17B", "Pepe": "#78C850",
    "Shiba Inu": "#F05A24"
}

logo_dict = {
    "BTC-USD": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
    "ETH-USD": "https://assets.coingecko.com/coins/images/279/large/ethereum.png",
    "BNB-USD": "https://assets.coingecko.com/coins/images/825/large/binance-coin-logo.png",
    "ADA-USD": "https://assets.coingecko.com/coins/images/975/large/cardano.png",
    "SOL-USD": "https://assets.coingecko.com/coins/images/4128/large/solana.png",
    "XRP-USD": "https://assets.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png",
    "DOGE-USD": "https://assets.coingecko.com/coins/images/5/large/dogecoin.png",
    "DOT-USD": "https://assets.coingecko.com/coins/images/12171/large/polkadot.png",
    "LTC-USD": "https://assets.coingecko.com/coins/images/2/large/litecoin.png",
    "LINK-USD": "https://assets.coingecko.com/coins/images/877/large/chainlink-new-logo.png",
    "USDT-USD": "https://assets.coingecko.com/coins/images/325/large/Tether-logo.png",
    "PEPE24478-USD": "https://assets.coingecko.com/coins/images/29850/large/pepe-token.jpeg",
    "SHIB-USD": "https://assets.coingecko.com/coins/images/11939/large/shiba.png"
}

currency_rates = {"USD": 1, "IDR": 16000, "EUR": 0.92}
currency_symbol = {"USD": "$", "IDR": "Rp", "EUR": "€"}

selected_rate = currency_rates[col_currency]
selected_symbol = currency_symbol[col_currency]

# --- AMBIL DATA ---
@st.cache_data
def ambil_data(tickers):
    start_date = "2015-01-01"
    end_date = pd.Timestamp.today().strftime('%Y-%m-%d')
    data = yf.download(tickers, start=start_date, end=end_date)["Close"]
    for col in data.columns:
        first_valid = data[col].first_valid_index()
        if first_valid:
            data.loc[:first_valid, col] = 0
        else:
            data[col] = 0
    return data.fillna(0)

with st.spinner("Mengambil data dari Yahoo Finance..."):
    data_harga_all = ambil_data(list(crypto_dict.values()))

if data_harga_all.empty:
    st.warning("Data tidak tersedia.")
    st.stop()

# --- RANKING CRYPTO DENGAN FILTER WAKTU ---
st.header("📈 Ranking Crypto Berdasarkan Kenaikan Persentase")

# Dropdown untuk memilih periode perubahan
periode = st.selectbox("Pilih Periode Perubahan:", ["Hari", "Minggu", "Bulan"])

# Ambil harga terakhir dan harga sebelumnya berdasarkan pilihan
last_price = data_harga_all.iloc[-1]

if periode == "Hari":
    prev_price = data_harga_all.iloc[-2]
    label = "Harian (%)"
elif periode == "Minggu":
    prev_price = data_harga_all.shift(7).iloc[-1]
    label = "Mingguan (%)"
else:  # "Bulan"
    prev_price = data_harga_all.shift(30).iloc[-1]
    label = "Bulanan (%)"

# Hitung persentase perubahan
persentase = ((last_price - prev_price) / prev_price) * 100

# Siapkan DataFrame ranking
ranking_df = pd.DataFrame({
    "Ticker": persentase.index,
    "Nama": [k for t in persentase.index for k, v in crypto_dict.items() if v == t],
    "Logo": [logo_dict.get(t, "") for t in persentase.index],
    "Harga Sekarang": (last_price * selected_rate).values,
    "Perubahan (%)": persentase.values
})

# Urutkan berdasarkan perubahan terbesar
ranking_df = ranking_df.sort_values("Perubahan (%)", ascending=False).reset_index(drop=True)

# Tambahkan header kolom
col1, col2, col3, col4, col5 = st.columns([1, 1.5, 3, 2.5, 3])
with col1:
    st.markdown("**#**")
with col2:
    st.markdown("**Logo**")
with col3:
    st.markdown("**Nama (Ticker)**")
with col4:
    st.markdown(f"**Perubahan {label}**")
with col5:
    st.markdown("**Harga Sekarang**")

# Tampilkan sebagai ranking baris per baris
for idx, row in ranking_df.iterrows():
    col1, col2, col3, col4, col5 = st.columns([1, 1.5, 3, 2.5, 3])
    with col1:
        st.markdown(f"*#{idx+1}*")
    with col2:
        if row["Logo"].startswith("http"):
            st.image(row["Logo"], width=32)
    with col3:
        st.markdown(f"**{row['Nama']} ({row['Ticker'].replace('-USD','')})**")
    with col4:
        warna = "#00FF88" if row["Perubahan (%)"] >= 0 else "#FF4444"
        st.markdown(f"<span style='color:{warna}'>{row['Perubahan (%)']:.2f}%</span>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"{selected_symbol}{row['Harga Sekarang']:,.2f}")


# Info tambahan
st.markdown("---")
st.markdown(f"📊 Menampilkan perubahan persentase berdasarkan periode: **{periode}**")



# --- PILIHAN ---
col1, col2 = st.columns([3, 1])
with col1:
    pilihan = st.multiselect("Pilih Crypto:", list(crypto_dict.keys()))

if pilihan:
    tickers = [crypto_dict[p] for p in pilihan]
    data_harga = data_harga_all[tickers]

    # --- TABS --- 
    tab2, tab1 = st.tabs(["Harga Terakhir", "Prediksi"])

    with tab2:
        st.subheader(f"Harga Terakhir ({col_currency})")
        last_prices = data_harga.iloc[-1] * selected_rate
        max_per_row = 5
        for i in range(0, len(tickers), max_per_row):
            row_tickers = tickers[i:i+max_per_row]
            cols = st.columns(len(row_tickers))
            for j, t in enumerate(row_tickers):
                with cols[j]:
                    st.markdown(f"""<div class="custom-metric-box">
                    {t.replace("-USD", "")}<br><span style='font-size: 1.5em;'>{selected_symbol}{last_prices[t]:,.2f}</span>
                    </div>""", unsafe_allow_html=True)

    with tab1:
        jumlah_hari = st.slider("Prediksi Hari ke Depan", 1, 30, 1)
        st.markdown(f"Data historis dari *{data_harga.index.min().date()}* sampai *{data_harga.index.max().date()}*")

        tanggal_akhir_prediksi = pd.Timestamp.today() + timedelta(days=jumlah_hari)
    

        prediksi_df = pd.DataFrame()
        harga_prediksi_akhir = {}
        for t in tickers:
            df_ts = data_harga[t].reset_index().rename(columns={t: "Close"}).set_index('Date').asfreq('D').ffill().bfill()
            try:
                model_full = SARIMAX(df_ts['Close'], order=(1,1,1), seasonal_order=(1,0,1,7)).fit(disp=False)
                future_pred = model_full.forecast(steps=jumlah_hari)
                future_dates = pd.date_range(start=df_ts.index[-1] + timedelta(days=1), periods=jumlah_hari, freq='D')
                future_pred = np.where(future_pred < 0, 0, future_pred)
                prediksi_df[t] = pd.Series(future_pred, index=future_dates)

                # Ambil harga prediksi hari terakhir
                harga_prediksi_akhir[t] = future_pred[-1] * selected_rate

            except Exception as e:
                st.warning(f"Gagal membuat prediksi untuk {t}: {e}")
                harga_prediksi_akhir[t] = np.nan

        # Tampilkan harga prediksi hari terakhir di bawah slider
        st.subheader(f"Harga Prediksi Hari ke-{jumlah_hari} ({tanggal_akhir_prediksi.date()})")
        cols_pred = st.columns(len(tickers))
        for i, t in enumerate(tickers):
            with cols_pred[i]:
                nama = [k for k,v in crypto_dict.items() if v==t][0]
                harga = harga_prediksi_akhir.get(t, np.nan)
                if np.isnan(harga):
                    st.markdown(f"**{nama}**\n\n:warning: Gagal prediksi")
                else:
                    st.markdown(f"**{nama}**\n\n{selected_symbol}{harga:,.2f}")

        df_hist = data_harga.reset_index().melt(id_vars="Date", var_name="Crypto", value_name="Close")
        df_hist["Type"] = "Historis"

        df_pred = prediksi_df.reset_index().melt(id_vars="index", var_name="Crypto", value_name="Close").rename(columns={"index": "Date"})
        df_pred["Type"] = "Prediksi"

        df_all = pd.concat([df_hist, df_pred])
        df_all["CryptoName"] = df_all["Crypto"].map(lambda x: [k for k,v in crypto_dict.items() if v==x][0])

        color_scale = alt.Scale(domain=list(pilihan), range=[crypto_colors[c] for c in pilihan])

        chart = alt.Chart(df_all[df_all["Crypto"].isin(tickers)]).mark_line(size=3).encode(
            x=alt.X("Date:T", title="Waktu"),
            y=alt.Y("Close:Q", title=f"Harga ({col_currency})"),
            color=alt.Color("CryptoName:N", scale=color_scale, legend=alt.Legend(title="Crypto")),
            tooltip=["Date:T", "CryptoName:N", "Close:Q", "Type:N"]
        ).properties(
            width=1000,
            height=400,
            background="#121212"
        ).configure_axis(
            labelColor="#FFFFFF",
            titleColor="#FFFFFF"
        ).configure_legend(
            labelColor="#FFFFFF",
            titleColor="#FFFFFF"
        ).interactive()

        st.altair_chart(chart, use_container_width=True)

else:
    st.info("🔍 Silakan pilih minimal satu crypto untuk menampilkan prediksi atau grafik harga.")

# --- FOOTER ---
st.markdown("---")
st.caption("Dibuat dengan Streamlit · Prediksi menggunakan SARIMAX · Data dari Yahoo Finance")
