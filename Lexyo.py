import streamlit as st

st.title("Simulateur fiscal")

regime = st.selectbox("Régime fiscal", [
    "LMNP réel", "Micro BIC", "LMP réel",
    "Location nue réel", "Micro foncier",
    "SCI à l’IS", "SCI à l’IR", "SARL de famille", "Holding à l’IS"
])

st.write(f"Tu as sélectionné : **{regime}**")
