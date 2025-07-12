import streamlit as st
import pandas as pd
from typing import Dict, Any

# --- CONFIGURATION DE L'APPLICATION ---
st.set_page_config(page_title="Simulateur Lexyo", layout="wide")
st.title("🏡 Simulateur de rentabilité immobilière - Lexyo")

# --- INITIALISATION DES VARIABLES GLOBALES ---
regimes_fiscaux = [
    "LMNP Réel",
    "LMNP Micro-BIC",
    "LMP Réel",
    "Location nue (IR)",
    "SCI à l'IS",
    "SCI à l'IR",
    "SARL de famille",
    "Holding IS"
]

# --- BARRE LATÉRALE ---
st.sidebar.header("Paramètres généraux")
regime = st.sidebar.selectbox("Choisissez votre régime fiscal", regimes_fiscaux)

# --- FORMULAIRE DES DONNÉES D'ENTRÉE ---
st.header("🔢 Données d'entrée")
col1, col2, col3 = st.columns(3)

with col1:
    prix_bien = st.number_input("Prix du bien (€)", min_value=0, value=150000)
    frais_notaire = st.number_input("Frais de notaire (%)", min_value=0.0, value=7.5)
    travaux = st.number_input("Montant des travaux (€)", min_value=0, value=20000)

with col2:
    loyer_mensuel = st.number_input("Loyer mensuel (€)", min_value=0, value=750)
    charges_mensuelles = st.number_input("Charges mensuelles (€)", min_value=0, value=150)
    vacances_locatives = st.slider("Vacance locative (%)", 0, 20, 5)

with col3:
    apport = st.number_input("Apport (€)", min_value=0, value=20000)
    taux_credit = st.number_input("Taux d'intérêt (%)", min_value=0.0, value=3.0)
    duree_credit = st.number_input("Durée du crédit (années)", min_value=1, value=20)

# --- CALCULS COMMUNS ---
def calculs_communs(data: Dict[str, Any]) -> Dict[str, Any]:
    prix_total = data["prix_bien"] + data["prix_bien"] * data["frais_notaire"] / 100 + data["travaux"]
    loyer_annuel = data["loyer_mensuel"] * 12 * (1 - data["vacances_locatives"] / 100)
    charges_annuelles = data["charges_mensuelles"] * 12
    capital_emprunte = prix_total - data["apport"]
    mensualite = (capital_emprunte * (data["taux_credit"] / 100 / 12)) / (1 - (1 + data["taux_credit"] / 100 / 12) ** (-data["duree_credit"] * 12))
    annuite = mensualite * 12

    return {
        "prix_total": prix_total,
        "loyer_annuel": loyer_annuel,
        "charges_annuelles": charges_annuelles,
        "capital_emprunte": capital_emprunte,
        "mensualite": mensualite,
        "annuite": annuite
    }

# --- RÉCUPÉRATION DES DONNÉES ---
data = {
    "prix_bien": prix_bien,
    "frais_notaire": frais_notaire,
    "travaux": travaux,
    "loyer_mensuel": loyer_mensuel,
    "charges_mensuelles": charges_mensuelles,
    "vacances_locatives": vacances_locatives,
    "apport": apport,
    "taux_credit": taux_credit,
    "duree_credit": duree_credit,
}

calculs = calculs_communs(data)

# --- BLOC DE CALCUL DYNAMIQUE SELON LE RÉGIME ---
st.header("📊 Résultats selon le régime fiscal")

if regime == "LMNP Réel":
    # 👉 Tu colleras ici le code complet du LMNP Réel
    pass

elif regime == "SCI à l'IS":
    st.header("📘 Simulation SCI à l'IS")

st.markdown("### 📌 Prix d'acquisition du bien")
prix_bien = st.number_input("Prix du bien (€)", value=200000)
apport = st.number_input("Apport personnel (€)", value=20000)
frais_notaire = st.number_input("Frais de notaire (€)", value=15000)
frais_agence = st.number_input("Frais d'agence (payés par l'acquéreur) (€)", value=10000)
frais_dossier = st.number_input("Frais de dossier bancaire (€)", value=1000)
travaux = st.number_input("Montant des travaux (€)", value=30000)
frais_garantie = st.number_input("Frais de garantie bancaire (€)", value=2000)
frais_tiers = st.number_input("Frais tiers (courtier, diagnostic, etc.) (€)", value=1500)

montant_emprunt = prix_bien + frais_notaire + frais_agence + travaux + frais_dossier + frais_garantie + frais_tiers - apport
st.markdown(f"**Montant emprunté :** {montant_emprunt:,.0f} €")

st.markdown("### 📌 Emprunt")
duree_emprunt = st.number_input("Durée de l'emprunt (années)", value=20)
taux_interet = st.number_input("Taux d'intérêt (%)", value=2.5) / 100
taux_assurance = st.number_input("Taux assurance (%)", value=0.36) / 100

mensualite = np.pmt(taux_interet / 12, duree_emprunt * 12, -montant_emprunt)
mensualite_assurance = montant_emprunt * taux_assurance / 12
total_mensualite = mensualite + mensualite_assurance
st.markdown(f"**Mensualité avec assurance :** {total_mensualite:,.2f} €")

st.markdown("### 📌 Charges annuelles")
charges_copro = st.number_input("Charges de copropriété (€ / an)", value=1200)
assurance_habitation = st.number_input("Assurance habitation (€ / an)", value=200)
gli = st.number_input("Assurance loyer impayé GLI (€ / an)", value=300)
taxe_fonciere = st.number_input("Taxe foncière (€ / an)", value=1000)
frais_entretien = st.number_input("Frais d'entretien (€ / an)", value=500)
comptabilite = st.number_input("Comptabilité (€ / an)", value=900)
frais_bancaires = st.number_input("Frais bancaires (€ / an)", value=300)

charges_annuelles = sum([charges_copro, assurance_habitation, gli, taxe_fonciere, frais_entretien, comptabilite, frais_bancaires])

st.markdown("### 📌 Revenu locatif")
loyer_mensuel = st.number_input("Loyer mensuel HC (€)", value=1000)
revenu_annuel = loyer_mensuel * 12

st.markdown("### 📌 Amortissements")
amortissement_bien = st.number_input("Durée amortissement bien (ans)", value=30)
amortissement_travaux = st.number_input("Durée amortissement travaux (ans)", value=15)
amortissement_frais = st.number_input("Durée amortissement frais d'acquisition (ans)", value=5)

am_bien = prix_bien / amortissement_bien
am_travaux = travaux / amortissement_travaux
am_frais = (frais_notaire + frais_agence + frais_dossier + frais_tiers + frais_garantie) / amortissement_frais

amortissement_total_annuel = am_bien + am_travaux + am_frais

# Projection sur 10 ans
resultats = []
interets_restants = montant_emprunt
annee = 0
report_deficit = 0

for annee in range(1, 11):
    interets_annuels = np.ipmt(taux_interet / 12, annee * 12, duree_emprunt * 12, -montant_emprunt) * 12
    depenses = total_mensualite * 12 + charges_annuelles + comptabilite
    resultat_fiscal = revenu_annuel - charges_annuelles - interets_annuels - amortissement_total_annuel
    if resultat_fiscal < 0:
        report_deficit += abs(resultat_fiscal)
        impot_is = 0
    else:
        resultat_fiscal -= min(report_deficit, resultat_fiscal)
        report_deficit -= min(report_deficit, resultat_fiscal)
        impot_is = resultat_fiscal * 0.15 if resultat_fiscal < 38120 else (38120 * 0.15 + (resultat_fiscal - 38120) * 0.25)

    cashflow = revenu_annuel - depenses - impot_is
    resultats.append({
        "Année": annee,
        "Résultat fiscal (€)": resultat_fiscal,
        "Impôt sur les sociétés (€)": impot_is,
        "Cashflow net (€)": cashflow
    })

# Affichage tableau et graphiques
resultats_df = pd.DataFrame(resultats)
st.dataframe(resultats_df.style.format("{:.0f}"))

fig, ax = plt.subplots(3, 1, figsize=(8, 10))

ax[0].plot(resultats_df["Année"], resultats_df["Résultat fiscal (€)"], marker='o', color='orange')
ax[0].set_title("Résultat fiscal annuel")
ax[0].set_ylabel("€")

ax[1].plot(resultats_df["Année"], resultats_df["Impôt sur les sociétés (€)"], marker='o', color='red')
ax[1].set_title("Impôt sur les sociétés annuel")
ax[1].set_ylabel("€")

ax[2].plot(resultats_df["Année"], resultats_df["Cashflow net (€)"], marker='o', color='green')
ax[2].set_title("Cashflow net annuel")
ax[2].set_ylabel("€")
ax[2].set_xlabel("Année")

plt.tight_layout()
st.pyplot(fig)

elif regime == "Location nue (IR)":
    # 👉 Tu colleras ici le code complet de la location nue IR
    pass

# etc. pour tous les régimes

# --- AFFICHAGE DES CALCULS COMMUNS POUR VÉRIFICATION ---
st.subheader("🧮 Détails des calculs communs")
st.write(calculs)

# --- FIN DU MODULE DE BASE ---
