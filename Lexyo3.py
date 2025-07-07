import streamlit as st
import pandas as pd

# Définition des régimes fiscaux
REGIMES = [
    "LMNP Réel", "Micro BIC", "LMP Réel", "Location nue", "SCI IS", "SCI IR", "SARL de famille", "Holding IS"
]

# Champs par régime
CHAMPS_PAR_REGIME = {
    "LMNP Réel": ["Loyer annuel", "Charges locatives", "Amortissement bien", "Amortissement mobilier", "Frais de gestion", "Intérêts d’emprunt", "Taxe foncière", "Travaux déductibles"],
    "Micro BIC": ["Loyer annuel"],
    "LMP Réel": ["Loyer annuel", "Charges locatives", "Amortissement bien", "Amortissement mobilier", "Frais de gestion", "Intérêts d’emprunt", "Taxe foncière", "Travaux déductibles"],
    "Location nue": ["Loyer annuel", "Charges locatives", "Frais de gestion", "Intérêts d’emprunt", "Taxe foncière", "Travaux déductibles"],
    "SCI IS": ["Loyer annuel", "Charges locatives", "Amortissement bien", "Amortissement mobilier", "Frais de gestion", "Intérêts d’emprunt", "Taxe foncière", "Travaux déductibles"],
    "SCI IR": ["Loyer annuel", "Charges locatives", "Frais de gestion", "Intérêts d’emprunt", "Taxe foncière", "Travaux déductibles"],
    "SARL de famille": ["Loyer annuel", "Charges locatives", "Amortissement bien", "Amortissement mobilier", "Frais de gestion", "Intérêts d’emprunt", "Taxe foncière", "Travaux déductibles"],
    "Holding IS": ["Loyer annuel", "Charges locatives", "Amortissement bien", "Amortissement mobilier", "Frais de gestion", "Intérêts d’emprunt", "Taxe foncière", "Travaux déductibles"]
}

TAUX_ABATTEMENT = {
    "Micro BIC": 0.5
}

TAUX_IS = 0.25  # Impôt sur les sociétés

# Interface utilisateur
st.set_page_config(page_title="Simulateur de rentabilité Lexyo", layout="wide")
st.title("Simulateur de rentabilité immobilière - Lexyo")

regime = st.selectbox("Choisissez un régime fiscal", REGIMES)

st.subheader("Données d'entrée")

# Récupération des champs pertinents selon le régime
donnees = {}
for champ in CHAMPS_PAR_REGIME[regime]:
    donnees[champ] = st.number_input(champ, min_value=0.0, step=100.0)

# Fonctions de calcul par régime

def calcul_resultats(donnees, regime):
    loyer = donnees.get("Loyer annuel", 0)
    charges = donnees.get("Charges locatives", 0)
    frais = donnees.get("Frais de gestion", 0)
    interets = donnees.get("Intérêts d’emprunt", 0)
    tf = donnees.get("Taxe foncière", 0)
    travaux = donnees.get("Travaux déductibles", 0)
    amortissement_bien = donnees.get("Amortissement bien", 0)
    amortissement_mobilier = donnees.get("Amortissement mobilier", 0)

    if regime == "Micro BIC":
        revenu_net = loyer * (1 - TAUX_ABATTEMENT["Micro BIC"])
        impot_ir = revenu_net * 0.3  # Hypothèse d'un TMI à 30%
        cashflow = loyer - impot_ir

    elif regime in ["LMNP Réel", "LMP Réel", "SARL de famille"]:
        resultat_net = loyer - charges - frais - interets - tf - travaux - amortissement_bien - amortissement_mobilier
        impot_ir = max(0, resultat_net * 0.3)  # TMI à 30%
        cashflow = loyer - charges - frais - interets - tf - travaux - impot_ir

    elif regime == "Location nue":
        resultat_net = loyer - charges - frais - interets - tf - travaux
        impot_ir = max(0, resultat_net * 0.3)  # TMI à 30%
        cashflow = loyer - charges - frais - interets - tf - travaux - impot_ir

    elif regime == "SCI IS":
        resultat_net = loyer - charges - frais - interets - tf - travaux - amortissement_bien - amortissement_mobilier
        impot_is = max(0, resultat_net * TAUX_IS)
        cashflow = loyer - charges - frais - interets - tf - travaux - impot_is

    elif regime == "SCI IR":
        resultat_net = loyer - charges - frais - interets - tf - travaux
        impot_ir = max(0, resultat_net * 0.3)
        cashflow = loyer - charges - frais - interets - tf - travaux - impot_ir

    elif regime == "Holding IS":
        resultat_net = loyer - charges - frais - interets - tf - travaux - amortissement_bien - amortissement_mobilier
        impot_is = max(0, resultat_net * TAUX_IS)
        cashflow = loyer - charges - frais - interets - tf - travaux - impot_is

    else:
        resultat_net = 0
        impot_ir = 0
        cashflow = 0

    return {
        "Résultat net avant impôt": round(resultat_net, 2),
        "Impôt": round(impot_ir if 'impot_ir' in locals() else impot_is, 2),
        "Cashflow net annuel": round(cashflow, 2),
        "Rentabilité brute": round(loyer / (loyer + charges + frais + tf + interets) * 100, 2)
    }

# Résultats
st.subheader("Résultats")
if donnees:
    resultats = calcul_resultats(donnees, regime)
    for k, v in resultats.items():
        st.write(f"{k} : {v} €")
