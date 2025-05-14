
import streamlit as st
import yfinance as yf
import numpy as np

# ------------------------------
# Funciones de valoración
# ------------------------------
def modelo_graham(eps, bvps):
    try:
        return round(np.sqrt(22.5 * eps * bvps), 2)
    except:
        return None

def modelo_ddm(dividend, growth_rate, discount_rate):
    try:
        return round(dividend * (1 + growth_rate) / (discount_rate - growth_rate), 2)
    except:
        return None

def modelo_dcf(eps, growth_rate, discount_rate, years=5):
    try:
        future_cashflows = [eps * (1 + growth_rate) ** i for i in range(1, years + 1)]
        discounted = [cf / (1 + discount_rate) ** i for i, cf in enumerate(future_cashflows, 1)]
        return round(sum(discounted), 2)
    except:
        return None

# ------------------------------
# Interfaz Streamlit
# ------------------------------
st.set_page_config(page_title="Analizador de Acciones NYSE", layout="wide")
st.title("📊 Analizador de Acciones que Pagan Dividendos (NYSE)")

st.markdown("""
Esta app calcula el valor intrínseco de acciones mediante tres modelos:
- 📘 **Graham**
- 💸 **Dividend Discount Model (DDM)**
- 📉 **Discounted Cash Flow (DCF)**

Muestra una alerta si el precio actual está por debajo del promedio de estos valores.
""")

# Lista de prueba de empresas NYSE
empresas = {
    "Coca-Cola (KO)": "KO",
    "Johnson & Johnson (JNJ)": "JNJ",
    "Procter & Gamble (PG)": "PG",
    "PepsiCo (PEP)": "PEP",
    "Apple (AAPL)": "AAPL"
}

opcion = st.selectbox("Selecciona una empresa para analizar:", list(empresas.keys()))
ticker = empresas[opcion]

# Obtener datos
data = yf.Ticker(ticker).info

st.subheader(f"📈 Datos de {data.get('shortName', ticker)}")
precio_actual = data.get("regularMarketPrice")
eps = data.get("trailingEps")
bvps = data.get("bookValue")
dividendo = data.get("dividendRate") or 0

yield_div = data.get("dividendYield")
pe_ratio = data.get("trailingPE")

st.write(f"**Precio actual:** ${precio_actual}")
st.write(f"**EPS:** {eps}")
st.write(f"**Valor libros por acción:** {bvps}")
st.write(f"**Dividend Yield:** {round(yield_div*100, 2) if yield_div else 0}%")
st.write(f"**P/E Ratio:** {pe_ratio}")

# Parámetros
st.markdown("---")
st.subheader("🧮 Parámetros para estimación")
col1, col2, col3 = st.columns(3)
with col1:
    growth = st.number_input("Crecimiento estimado (% anual)", value=6.0) / 100
with col2:
    discount = st.number_input("Tasa de descuento (%)", value=8.0) / 100
with col3:
    years = st.number_input("Años a proyectar (DCF)", value=5, step=1)

# Calcular valores
val_graham = modelo_graham(eps, bvps)
val_dcf = modelo_dcf(eps, growth, discount, years)
val_ddm = modelo_ddm(dividendo, growth, discount)

valores = [v for v in [val_graham, val_dcf, val_ddm] if v is not None]
promedio_intrinseco = round(sum(valores) / len(valores), 2) if valores else None

# Mostrar resultados
st.markdown("---")
st.subheader("📌 Valoraciones")

st.write(f"**Modelo Graham:** ${val_graham}")
st.write(f"**Modelo DCF:** ${val_dcf}")
st.write(f"**Modelo DDM:** ${val_ddm}")

if promedio_intrinseco:
    st.write(f"**Valor intrínseco promedio:** ${promedio_intrinseco}")
    descuento = round((promedio_intrinseco - precio_actual) / promedio_intrinseco * 100, 2)
    if descuento > 0:
        st.success(f"🔔 La acción está subvaluada aproximadamente un {descuento}%")
    else:
        st.warning(f"⚠️ La acción no está subvaluada actualmente.")
else:
    st.error("No se pudo calcular el valor intrínseco con los datos actuales.")

st.markdown("---")
st.caption("Datos obtenidos con Yahoo Finance. Modelo educativo - no constituye asesoramiento financiero.")
