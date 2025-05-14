
# ------------------------------
# Funciones de valoración
# ------------------------------
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Análisis de Acciones NYSE", layout="wide")
st.title("📊 Analizador de Acciones con Dividendos – NYSE / S&P 500")

@st.cache_data
def cargar_sp500():
    table = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
    return table[['Symbol', 'Security', 'GICS Sector']]

@st.cache_data
def obtener_datos_financieros(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="5y")
    
    try:
        rev_growth = ((info.get("totalRevenue", 0) - info.get("revenuePerShare", 0)) / info.get("revenuePerShare", 1)) * 100
    except:
        rev_growth = None

    return {
        "Ticker": ticker,
        "Price": info.get("currentPrice", None),
        "EPS": info.get("trailingEps", None),
        "Market Cap": info.get("marketCap", None),
        "ROA": info.get("returnOnAssets", 0) * 100 if info.get("returnOnAssets") else None,
        "PER": info.get("trailingPE", None),
        "Quick Ratio": info.get("quickRatio", None),
        "Debt Ratio": info.get("debtToEquity", None),
        "Revenue Growth": rev_growth,
        "Analyst Opinion": info.get("recommendationKey", "N/A"),
        "Book Value": info.get("bookValue", None),
        "Dividend": info.get("dividendRate", 0)
    }

def modelo_graham(eps, bvps):
    try:
        return round(np.sqrt(22.5 * eps * bvps), 2)
    except:
        return None

def modelo_dcf(eps, growth, discount, years=5):
    try:
        cashflows = [eps * (1 + growth) ** i for i in range(1, years + 1)]
        discounted = [cf / (1 + discount) ** i for i, cf in enumerate(cashflows, 1)]
        return round(sum(discounted), 2)
    except:
        return None

st.markdown("Se filtran automáticamente acciones con ROA > 15%, PER 10-20, Quick Ratio > 1, Deuda < 1, crecimiento ingresos > 10%")

df_sp500 = cargar_sp500()
tickers = df_sp500['Symbol'].tolist()
sectores = df_sp500['GICS Sector'].unique()

data_filtrada = []

progress = st.progress(0)
for i, ticker in enumerate(tickers[:100]):  # Limitar a 100 por velocidad
    datos = obtener_datos_financieros(ticker)
    if all([
        datos["ROA"] and datos["ROA"] > 15,
        datos["PER"] and 10 <= datos["PER"] <= 20,
        datos["Quick Ratio"] and datos["Quick Ratio"] > 1,
        datos["Debt Ratio"] is not None and datos["Debt Ratio"] < 1,
        datos["Revenue Growth"] and datos["Revenue Growth"] > 10,
    ]):
        sector = df_sp500[df_sp500["Symbol"] == ticker]["GICS Sector"].values[0]
        graham = modelo_graham(datos["EPS"], datos["Book Value"])
        dcf = modelo_dcf(datos["EPS"], 0.10, 0.08)
        data_filtrada.append([
            sector, ticker, datos["Market Cap"], datos["ROA"], datos["PER"], datos["Quick Ratio"],
            datos["Debt Ratio"], datos["Revenue Growth"], datos["Analyst Opinion"], datos["Price"],
            datos["EPS"], graham, dcf
        ])
    progress.progress(i / 100)

cols = [
    "Sector", "Ticker", "Market Cap (USD)", "ROA (%)", "PER", "Quick Ratio", "Debt Ratio",
    "Revenue Growth (%)", "Analyst Opinion", "Price (USD)", "EPS (USD)", "Graham Valuation (USD)", "DCF Valuation (USD)"
]

df_final = pd.DataFrame(data_filtrada, columns=cols)

# Agregar fila vacía para ingresar manualmente
df_final.loc[len(df_final)] = ["Add your own"] + [""] * (len(cols) - 1)

# Calcular promedios sectoriales
df_sector_avg = df_final.groupby("Sector").mean(numeric_only=True)
for sector in df_sector_avg.index:
    row = ["Sector Avg"] + [""] + [df_sector_avg.loc[sector][col] if col in df_sector_avg.columns else "" for col in cols[2:]]
    df_final.loc[len(df_final)] = row

# Mostrar tabla
st.dataframe(df_final, use_container_width=True)

# Exportar a Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Análisis')
    return output.getvalue()

excel_data = to_excel(df_final)
st.download_button("📥 Descargar Excel", data=excel_data, file_name="analisis_empresas_nyse.xlsx")

st.markdown("---")
st.caption("Datos obtenidos con Yahoo Finance. Modelo educativo - no constituye asesoramiento financiero.")
