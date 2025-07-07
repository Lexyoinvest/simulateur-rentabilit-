import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Simulateur Rentabilité Lexyo", layout="centered")
st.title("Simulateur de rentabilité immobilière - Lexyo")
st.markdown("Choisissez votre **régime fiscal** ci-dessous :")

# --- Choix du régime fiscal ---
regimes = [
    "LMNP Réel", "Micro BIC", "LMP Réel", "Location nue réel", "Micro foncier",
    "SCI à l'IS", "SCI à l'IR", "SARL de famille", "Holding à l'IS"
]
régime = st.radio("Régime fiscal :", regimes, horizontal=True)

# --- Variables communes à presque tous les régimes ---
with st.expander("⚡ Couts d'acquisition"):
    apport = st.number_input("Montant de l'apport", value=20000)
    prix_bien = st.number_input("Prix du bien", value=100000)
    frais_agence = st.number_input("Frais d'agence (si payés par l'acquéreur)", value=5000)
    notaire = st.number_input("Frais de notaire", value=8000)
    travaux = st.number_input("Montant des travaux", value=15000)
    mobilier = st.number_input("Achat de mobilier (meublé)", value=3000)

with st.expander("💸 Charges"):
    copro = st.number_input("Charges de copropriété", value=1000)
    pno = st.number_input("Assurance habitation (PNO)", value=150)
    gli = st.number_input("Assurance GLI", value=200)
    fonciere = st.number_input("Taxe foncière", value=800)
    entretien = st.number_input("Frais d'entretien", value=300)
    gestion = st.number_input("Frais de gestion (agence)", value=600)
    bancaire = st.number_input("Frais bancaires", value=120)
    compta = st.number_input("Frais de comptabilité", value=600)

with st.expander("💰 Revenus locatifs"):
    loyer_hc = st.number_input("Loyer mensuel hors charges", value=700)
    loyer_cc = st.number_input("Loyer mensuel charges comprises", value=800)

with st.expander("⛏ Amortissements (automatiques si valides)"):
    amort_bien = st.slider("Durée amortissement bien (années)", 10, 40, 25)
    amort_notaire = st.slider("Durée amortissement frais de notaire", 5, 20, 10)
    amort_mobilier = st.slider("Durée amortissement mobilier", 5, 10, 7)
    amort_travaux = st.slider("Durée amortissement travaux", 5, 20, 15)

# --- Revenus fiscaux ---
with st.expander("📅 Informations fiscales"):
    revenu_annuel = st.number_input("Revenu imposable du foyer", value=30000)
    parts = st.slider("Nombre de parts fiscales", 1.0, 3.0, 1.0, 0.5)

# --- Calculs génériques ---
loyer_annuel = loyer_hc * 12
charges_total = copro + pno + gli + fonciere + entretien + gestion + bancaire + compta

amortissement_total = 0
if régime in ["LMNP Réel", "LMP Réel"]:
    amortissement_total += prix_bien / amort_bien
    amortissement_total += notaire / amort_notaire
    amortissement_total += mobilier / amort_mobilier
    amortissement_total += travaux / amort_travaux

# --- Régime spécifique ---
if régime == "Micro BIC":
    resultat = loyer_annuel * 0.5
    impot = resultat * 0.3

elif régime == "Micro foncier":
    resultat = loyer_annuel * 0.7
    impot = resultat * 0.3

elif régime in ["LMNP Réel", "LMP Réel"]:
    resultat = loyer_annuel - charges_total - amortissement_total
    impot = 0 if resultat < 0 else resultat * 0.3

elif régime == "Location nue réel":
    abattement_foncier = 0
    resultat = loyer_annuel - charges_total
    impot = 0 if resultat < 0 else resultat * 0.3

elif régime == "SCI à l'IS":
    resultat = loyer_annuel - charges_total - amortissement_total
    impot = max(0, resultat) * 0.15

else:
    resultat = loyer_annuel - charges_total
    impot = max(0, resultat) * 0.3

cashflow = loyer_annuel - charges_total - impot

# --- Affichage ---
st.subheader("📊 Résultats")
col1, col2 = st.columns(2)
col1.metric("Cashflow annuel estimé", f"{cashflow:.0f} €")
col2.metric("Impôt annuel estimé", f"{impot:.0f} €")

# --- Projection sur 10 ans ---
st.subheader("🔢 Projection sur 10 ans")
annees = list(range(1, 11))
cashflows = [cashflow for _ in annees]
impots = [impot for _ in annees]
resultats = [resultat for _ in annees]

df = pd.DataFrame({
    "Année": annees,
    "Cashflow": cashflows,
    "Impôts": impots,
    "Résultat fiscal": resultats
})

st.line_chart(df.set_index("Année"))
