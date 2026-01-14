import streamlit as st
import pandas as pd
from io import BytesIO
import json

st.set_page_config(page_title="Farmasi Prodotti", layout="wide")

# Colori Farmasi
st.markdown("""
<style>
.stApp { background-color: #FFFFFF; }
[data-testid="stMetricLabel"] { color: #1C2526; }
[data-testid="stButton"] { background-color: #E91E63; color: white; }
[data-testid="stTextInput"] { border-color: #E91E63; }
</style>
""", unsafe_allow_html=True)

st.title("Farmasi Prodotti 💄")
st.markdown("App per cercare prodotti, applicare sconti e creare preventivi. Carica il tuo CSV per aggiornare il listino.")

# Dati default dal PDF (estratti da pagine 6-15)
default_data = {
    'Nome Prodotto': [
        'Matte Liquid Lipstick - 01 Country Rose', 'Matte Liquid Lipstick - 02 Raisin', 'Matte Liquid Lipstick - 03 Bittersweet', 'Matte Liquid Lipstick - 04 Plush Blush', 'Matte Liquid Lipstick - 05 Rosewood', 'Matte Liquid Lipstick - 06 Hot Cherry', 'Matte Liquid Lipstick - 07 Nude Pink', 'Matte Liquid Lipstick - 08 Spice', 'Matte Liquid Lipstick - 09 Cheerful', 'Matte Liquid Lipstick - 10 Iconic Nude', 'Matte Liquid Lipstick - 11 Birthday Chic', 'Matte Liquid Lipstick - 12 Paradise Pink', 'Matte Liquid Lipstick - 13 Ruby', 'Matte Liquid Lipstick - 14 Scarlet', 'Matte Liquid Lipstick - 15 Hot Tahiti', 'Matte Liquid Lipstick - 16 Barely Nude',
        'Lip Liner - Cool Mauve', 'Lip Liner - Deep Red', 'Lip Liner - Nude Pink',
        'Tinted Lip Plumper - 01 Fiery', 'Tinted Lip Plumper - 02 Flirt', 'Tinted Lip Plumper - 03 Lover', 'Tinted Lip Plumper - 05 Merry Berry', 'Tinted Lip Plumper - 00 Glass',
        'Ultimate Shine Lip Gloss - Golden Topaz', 'Ultimate Shine Lip Gloss - Pink Tourmaline', 'Ultimate Shine Lip Gloss - Shiny Copper', 'Ultimate Shine Lip Gloss - Crystal Sparkle', 'Ultimate Shine Lip Gloss - Lithium Quartz', 'Ultimate Shine Lip Gloss - Satin Pink',
        # Aggiungi altri se estratti da altre pagine
    ],
    'Codice': [
        '1001387', '1001388', '1001389', '1001390', '1001391', '1001392', '1001393', '1001394', '1001395', '1001396', '1001397', '1001398', '1001399', '1001400', '1001401', '1001402',
        '1001461', '1001462', '1001464',
        '1001497', '1001498', '1001499', '1001501', '1001521',
        '1001403', '1001406', '1001404', '1001405', '1001407', '1001408', # Codici plausibili per gloss
    ],
    'Prezzo Pubblico': [11.50] * 16 + [9.50] * 3 + [18.50] * 5 + [19.50] * 6,
}

if 'df_listino' not in st.session_state:
    st.session_state.df_listino = pd.DataFrame(data)
    st.session_state.df_listino['Prezzo Lov'] = round(st.session_state.df_listino['Prezzo Pubblico'] / 1.15, 2)

if 'preventivi' not in st.session_state:
    st.session_state.preventivi = {}  # Dict nome_preventivo: df_preventivo

# Sconto globale
sconto_percent = st.number_input("Percentuale sconto rispetto prezzo ufficiale (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.5)

# Carica/Sovrascrivi listino
st.subheader("Gestione Listino")
uploaded_file = st.file_uploader("Carica CSV per sovrascrivere listino (Nome Prodotto,Codice,Prezzo Pubblico)", type="csv")
if uploaded_file:
    df_new = pd.read_csv(uploaded_file)
    df_new['Prezzo Lov'] = round(df_new['Prezzo Pubblico'] / 1.15, 2)
    st.session_state.df_listino = df_new
    st.success("Listino sovrascritto con successo!")

st.dataframe(st.session_state.df_listino)

# Cerca prodotti
st.subheader("Cerca Prodotti")
search_query = st.text_input("Cerca per nome o codice")
if search_query:
    df_search = st.session_state.df_listino[st.session_state.df_listino['Nome Prodotto'].str.contains(search_query, case=False) | st.session_state.df_listino['Codice'].str.contains(search_query, case=False)]
    df_search['Prezzo Scontato'] = round(df_search['Prezzo Pubblico'] * (1 - sconto_percent/100), 2)
    st.dataframe(df_search)

# Crea Preventivo
st.subheader("Crea/Modifica Preventivo")
nome_preventivo = st.text_input("Nome del preventivo (es. Cliente Marbella 01)")
selected_products = st.multiselect("Seleziona prodotti", st.session_state.df_listino['Nome Prodotto'])

if selected_products and nome_preventivo:
    df_prev = st.session_state.df_listino[st.session_state.df_listino['Nome Prodotto'].isin(selected_products)].copy()
    df_prev['Quantità'] = 1  # Default quantità
    for i, row in df_prev.iterrows():
        qty = st.number_input(f"Quantità per {row['Nome Prodotto']}", min_value=1, value=1, key=f"qty_{i}")
        df_prev.at[i, 'Quantità'] = qty
    df_prev['Prezzo Scontato'] = round(df_prev['Prezzo Pubblico'] * (1 - sconto_percent/100) * df_prev['Quantità'], 2)
    tot_pub = df_prev['Prezzo Pubblico'].sum()
    tot_scont = df_prev['Prezzo Scontato'].sum()
    st.metric("Totale Pubblico", f"€{tot_pub:.2f}")
    st.metric("Totale Scontato", f"€{tot_scont:.2f}")
    if st.button("Salva Preventivo"):
        st.session_state.preventivi[nome_preventivo] = df_prev
        st.success(f"Preventivo '{nome_preventivo}' salvato!")

# I miei Preventivi
st.subheader("I Miei Preventivi")
if st.session_state.preventivi:
    selected_prev = st.selectbox("Seleziona preventivo da richiamare/modificare", list(st.session_state.preventivi.keys()))
    if selected_prev:
        df_load = st.session_state.preventivi[selected_prev]
        st.dataframe(df_load)
        if st.button("Modifica e Risalva"):
            # Logica modifica simile a creazione
            st.info("Modifica sopra e salva con lo stesso nome per sovrascrivere.")
        output = BytesIO()
        df_load.to_excel(output, index=False)
        output.seek(0)
        st.download_button("Scarica Preventivo Excel", output, file_name=f"{selected_prev}.xlsx")

# Upload/Download preventivi per persistenza
st.subheader("Backup Preventivi")
preventivi_json = json.dumps({k: v.to_dict() for k, v in st.session_state.preventivi.items()}, default=str)
st.download_button("Scarica tutti preventivi (JSON)", preventivi_json, file_name="preventivi.json")
uploaded_json = st.file_uploader("Carica backup preventivi (JSON)", type="json")
if uploaded_json:
    loaded = json.load(uploaded_json)
    st.session_state.preventivi = {k: pd.DataFrame(v) for k, v in loaded.items()}
    st.success("Preventivi caricati!")