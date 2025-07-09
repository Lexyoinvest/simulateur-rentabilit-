import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Simulateur de Rentabilité Immobilière", layout="wide")
st.title("Simulateur de Rentabilité Immobilière")

# --- Sélection du régime fiscal ---
st.sidebar.header("Choix du régime fiscal")
regime_fiscal = st.sidebar.selectbox("Régime fiscal", [
    "LMNP réel",
    "Micro-BIC",
    "LMP réel",
    "Location nue (micro-foncier)",
    "Location nue (réel)",
    "SCI à l'IS",
    "SCI à l'IR"
])

# --- Saisie des données principales ---
st.header("1. Informations sur le bien")
col1, col2 = st.columns(2)

with col1:
    prix_bien = st.number_input("Prix du bien (€)", min_value=0.0, step=1000.0)
with col2:
    travaux = st.number_input("Montant des travaux (€)", min_value=0.0, step=1000.0)
    
frais_tiers = st.number_input("Frais pris par des tiers (€)", min_value=0.0, step=100.0)
frais_agence = st.number_input("Frais d’agence (€)", min_value=0.0, step=100.0)
frais_dossier = st.number_input("Frais de dossier bancaire (€)", min_value=0.0, step=100.0)
caution = st.number_input("Caution bancaire (€)", min_value=0.0, step=100.0)
mobilier = st.number_input("Valeur du mobilier (€)", min_value=0.0, step=100.0)

apport = st.number_input("Apport personnel (€)", min_value=0.0, step=1000.0)
frais_notaire = round(0.08 * prix_bien)
st.write(f"**Frais de notaire estimés :** {frais_notaire} €")

montant_emprunt = prix_bien + travaux + frais_agence + frais_dossier + caution + frais_notaire + frais_tiers - apport 
st.write(f"**Montant total emprunté :** {montant_emprunt} €")

# --- Paramètres du prêt ---
st.header("2. Paramètres du prêt")
duree = st.number_input("Durée du prêt (années)", min_value=1, step=1)
taux = st.number_input("Taux d'intérêt (%)", min_value=0.0, step=0.1) / 100
taux_assurance = st.number_input("Taux assurance (%)", min_value=0.0, step=0.01) / 100

n_mois = int(duree * 12)
taux_mensuel = taux / 12
assurance_mensuelle = montant_emprunt * taux_assurance / 12

mensualite_hors_assurance = montant_emprunt * taux_mensuel / (1 - (1 + taux_mensuel) ** -n_mois)
mensualite_totale = mensualite_hors_assurance + assurance_mensuelle

st.write(f"**Mensualité hors assurance :** {mensualite_hors_assurance:.2f} €")
st.write(f"**Mensualité avec assurance :** {mensualite_totale:.2f} €")

# --- Tableau d'amortissement ---
st.header("3. Tableau d'amortissement")
def generer_tableau_amortissement(capital, taux_annuel, duree_annees, taux_assurance):
    taux_m = taux_annuel / 12
    duree_m = duree_annees * 12
    mensualite = capital * taux_m / (1 - (1 + taux_m) ** -duree_m)
    assurance = capital * taux_assurance / 12

    tableau = []
    capital_restant = capital

    for mois in range(1, int(duree_m) + 1):
        interets = capital_restant * taux_m
        principal = mensualite - interets
        capital_restant -= principal
        cout_total = mensualite + assurance

        tableau.append({
            "Mois": mois,
            "Mensualité": round(mensualite, 2),
            "Assurance": round(assurance, 2),
            "Intérêts": round(interets, 2),
            "Principal remboursé": round(principal, 2),
            "Capital restant dû": round(capital_restant, 2),
            "Total payé": round(cout_total, 2)
        })

    return pd.DataFrame(tableau)

tableau_amortissement = generer_tableau_amortissement(montant_emprunt, taux, duree, taux_assurance)
st.dataframe(tableau_amortissement, use_container_width=True)

# --- Amortissements LMNP réel ---
if regime_fiscal == "LMNP réel":
    st.header("4. Détails des amortissements")

    duree_amort_bat = st.number_input("Durée amortissement bâtiment (ans)", min_value=1, value=30)
    duree_amort_travaux = st.number_input("Durée amortissement travaux (ans)", min_value=1, value=10)
    mobilier = st.number_input("Achat mobilier (€)", min_value=0.0, step=100.0)
    duree_amort_mobilier = st.number_input("Durée amortissement mobilier (ans)", min_value=1, value=7)
    duree_amort_agence = st.number_input("Durée amortissement frais d'agence (ans)", min_value=1, value=5)
    duree_amort_dossier = st.number_input("Durée amortissement frais de dossier (ans)", min_value=1, value=5)

    valeur_terrain = 0.2 * prix_bien
    valeur_batiment = prix_bien - valeur_terrain

    amortissement_batiment = valeur_batiment / duree_amort_bat
    amortissement_travaux = travaux / duree_amort_travaux
    amortissement_mobilier = mobilier / duree_amort_mobilier
    amortissement_agence = frais_agence / duree_amort_agence
    amortissement_dossier = frais_dossier / duree_amort_dossier

    st.markdown(f"""
    **Amortissements annuels estimés :**
    - Bâtiment : {amortissement_batiment:.2f} €
    - Travaux : {amortissement_travaux:.2f} €
    - Mobilier : {amortissement_mobilier:.2f} €
    - Frais de dossier : {amortissement_dossier:.2f} €
    """)
# --- Rentabilité sur 10 ans ---
st.header("5. Rentabilité sur 10 ans")
loyer_mensuel = st.number_input("Loyer mensuel brut (€)", min_value=0.0, step=10.0)
revenu_annuel = loyer_mensuel * 12
tf = st.number_input("Taxe foncière annuelle (€)", min_value=0.0, step=100.0)

# Charges diverses
charges_copro = st.number_input("Charges de copropriété annuelles (€)", min_value=0.0, step=100.0)
comptabilite = st.number_input("Frais de comptabilité annuels (€)", min_value=0.0, step=100.0)
assurance_pno = st.number_input("Assurance PNO annuelle (€)", min_value=0.0, step=100.0)
assurance_gli = st.number_input("Assurance GLI annuelle (€)", min_value=0.0, step=100.0)
entretien = st.number_input("Frais d'entretien annuels (€)", min_value=0.0, step=100.0)
frais_bancaires = st.number_input("Frais bancaires annuels (€)", min_value=0.0, step=100.0)
frais_agence_location = st.number_input("Frais de gestion locative annuels (€)", min_value=0.0, step=100.0)

charges_total_annuelles = sum([charges_copro, comptabilite, assurance_pno, assurance_gli, entretien, frais_bancaires, frais_agence_location])

# Choix du TMI et des prélèvements sociaux
col_ir, col_ps = st.columns(2)
with col_ir:
    taux_ir = st.number_input("Taux marginal d'imposition (IR) %", min_value=0.0, max_value=100.0, value=30.0, step=0.1) / 100
with col_ps:
    taux_ps = st.number_input("Taux des prélèvements sociaux %", min_value=0.0, max_value=100.0, value=17.2, step=0.1) / 100

# Placeholder : traitement fiscal simplifié uniquement LMNP réel pour l’instant
if regime_fiscal == "LMNP réel":
    deficit_reportable = 0
    tableau_renta = []

    for annee in range(1, 11):
        interets_annuels = tableau_amortissement["Intérêts"][(annee - 1) * 12:annee * 12].sum()
        assurance_annuelle = tableau_amortissement["Assurance"][(annee - 1) * 12:annee * 12].sum()

        amortissement_total = amortissement_batiment + amortissement_travaux + amortissement_mobilier + amortissement_agence + amortissement_dossier

        resultat_fiscal = revenu_annuel - interets_annuels - assurance_annuelle - tf - charges_total_annuelles

        amorti_possible = max(0, resultat_fiscal)
        if amortissement_total > amorti_possible:
            amortissement_utilise = amorti_possible
            deficit_reportable += amortissement_total - amorti_possible
        else:
            amortissement_utilise = amortissement_total

        resultat_fiscal -= amortissement_utilise

        if resultat_fiscal < 0:
            deficit_reportable += abs(resultat_fiscal)
            resultat_fiscal = 0
        else:
            if deficit_reportable > 0:
                if resultat_fiscal > deficit_reportable:
                    resultat_fiscal -= deficit_reportable
                    deficit_reportable = 0
                else:
                    deficit_reportable -= resultat_fiscal
                    resultat_fiscal = 0

        impot_ir = resultat_fiscal * taux_ir
        ps = resultat_fiscal * taux_ps

        cashflow_mensuel = (revenu_annuel - mensualite_totale * 12 - tf - charges_total_annuelles - impot_ir - ps) / 12

        tableau_renta.append({
            "Année": annee,
            "Résultat fiscal": round(resultat_fiscal, 2),
            "IR": round(impot_ir, 2),
            "Prélèvements sociaux": round(ps, 2),
            "Cashflow net mensuel": round(cashflow_mensuel, 2),
            "Déficit reportable": round(deficit_reportable, 2)
        })

    tableau_rentabilite = pd.DataFrame(tableau_renta)
    st.dataframe(tableau_rentabilite, use_container_width=True)
else:
    st.warning(f"⚠️ Le calcul pour le régime {regime_fiscal} n'est pas encore implémenté.")

st.markdown("""
---
📌 *Note : Ce simulateur est en cours de développement. Les régimes fiscaux autres que LMNP réel seront ajoutés prochainement avec leur logique propre.*
""")
