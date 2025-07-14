import streamlit as st
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

st.set_page_config(page_title="Lexyo Simulateur de Rentabilité Immobilière", layout="wide")
st.title("Lexyo Simulateur de rentabilité immobilière")

# Menu à gauche
regime = st.sidebar.selectbox("Choisissez le régime fiscal :", ["LMNP réel", "SCI à l'IS"])

# --------------------------------------------------------------------------------
# CLASSE LMNP RÉEL
# --------------------------------------------------------------------------------
if regime == "LMNP réel":
   @dataclass
class LMNPReel:
    # Données achat
    prix_bien: float
    part_terrain: float
    apport: float
    frais_dossier: float
    frais_agence: float
    montant_travaux: float
    frais_garantie: float
    frais_tiers: float
    mobilier: float
    frais_notaire_pct: float = 8.0

    # Emprunt
    duree_annees: int
    taux_interet: float
    taux_assurance: float
    differe_mois: int

    # Charges annuelles
    charges_copro: float
    assurance_habitation: float
    assurance_gli: float
    taxe_fonciere: float
    frais_entretien: float
    frais_compta: float
    frais_bancaires: float
    gestion_locative: float = 0.0
    taxe_habitation: float = 0.0

    # Revenus
    loyer_mensuel_hc: float
    vacance_locative_mois: int

    # Fiscalité
    tmi: float
    duree_amort_bati: int = 30
    duree_amort_mobilier: int = 7

    # Internes
    montant_emprunt: float = field(init=False)
    deficits_reportables: list = field(default_factory=lambda: [0] * 10)

    def __post_init__(self):
        frais_notaire = self.prix_bien * self.frais_notaire_pct / 100
        total_frais = (
            self.prix_bien + frais_notaire + self.frais_agence +
            self.frais_dossier + self.montant_travaux +
            self.frais_garantie + self.frais_tiers
        )
        self.montant_emprunt = max(0, total_frais - self.apport)

    def mensualite_emprunt(self):
        taux_mensuel = self.taux_interet / 100 / 12
        taux_assurance_mens = self.taux_assurance / 100 / 12
        capital = self.montant_emprunt

        capital_differe = capital
        for _ in range(self.differe_mois):
            capital_differe += capital_differe * taux_mensuel

        nb_mensualites = self.duree_annees * 12 - self.differe_mois
        if nb_mensualites <= 0:
            raise ValueError("Durée trop courte ou différé trop long")

        mensualite = capital_differe * taux_mensuel / (1 - (1 + taux_mensuel) ** -nb_mensualites)
        return mensualite + capital * taux_assurance_mens

    def tableau_amortissement(self):
        taux_mensuel = self.taux_interet / 100 / 12
        capital = self.montant_emprunt
        capital_rest = capital
        mensualite = None
        rows = []

        for mois in range(1, self.duree_annees * 12 + 1):
            if mois <= self.differe_mois:
                interets = capital_rest * taux_mensuel
                principal = 0
                capital_rest += interets
            else:
                if mensualite is None:
                    mensualite = self.mensualite_emprunt() - capital * self.taux_assurance / 100 / 12
                interets = capital_rest * taux_mensuel
                principal = mensualite - interets
                capital_rest -= principal
                if capital_rest < 0:
                    principal += capital_rest
                    capital_rest = 0
            rows.append({
                'Mois': mois,
                'Capital restant dû': capital_rest,
                'Intérêts': interets,
                'Principal remboursé': principal
            })

        df = pd.DataFrame(rows)
        df['Année'] = ((df['Mois'] - 1) // 12) + 1
        return df

    def amortissements(self):
        valeur_bati = self.prix_bien * (1 - self.part_terrain / 100)
        amort_bati_annuel = valeur_bati / self.duree_amort_bati
        amort_mobilier_annuel = self.mobilier / self.duree_amort_mobilier

        amortissements = []
        for annee in range(1, 11):
            bati = amort_bati_annuel if annee <= self.duree_amort_bati else 0
            mobilier = amort_mobilier_annuel if annee <= self.duree_amort_mobilier else 0
            total = bati + mobilier
            amortissements.append({
                'Année': annee,
                'Amortissement Bâti': bati,
                'Amortissement Mobilier': mobilier,
                'Total Amortissement': total
            })

        return pd.DataFrame(amortissements)

    def resultat_fiscal_annuel(self):
        amort_df = self.amortissements()
        amortissement_dict = amort_df.set_index('Année')['Total Amortissement'].to_dict()
        amort_table = self.tableau_amortissement()
        interets_annuels = amort_table.groupby('Année')['Intérêts'].sum()

        resultats = []
        deficits_reportables = self.deficits_reportables.copy()
        mensualite = self.mensualite_emprunt()

        for annee in range(1, 11):
            revenus = self.loyer_mensuel_hc * (12 - self.vacance_locative_mois)

            charges = (
                self.charges_copro + self.assurance_habitation + self.assurance_gli +
                self.taxe_fonciere + self.frais_entretien + self.frais_compta +
                self.frais_bancaires + self.gestion_locative + self.taxe_habitation
            )

            interets = interets_annuels.get(annee, 0)
            amort = amortissement_dict.get(annee, 0)
            resultat = revenus - charges - interets - amort

            if resultat < 0:
                deficits_reportables[annee - 1] = -resultat
                resultat_fiscal = 0
            else:
                resultat_fiscal = resultat
                for i in range(annee):
                    if deficits_reportables[i] > 0:
                        if resultat_fiscal >= deficits_reportables[i]:
                            resultat_fiscal -= deficits_reportables[i]
                            deficits_reportables[i] = 0
                        else:
                            deficits_reportables[i] -= resultat_fiscal
                            resultat_fiscal = 0
                            break

            impot = resultat_fiscal * self.tmi / 100

            charges_recup = 0.8 * self.charges_copro
            cashflow_mensuel = (revenus - charges - mensualite * 12 + charges_recup) / 12

            resultats.append({
                'Année': annee,
                'Revenus nets vacance': revenus,
                'Charges': charges,
                'Intérêts Emprunt': interets,
                'Amortissement': amort,
                'Résultat fiscal imposable': resultat_fiscal,
                'Impôt': impot,
                'Cashflow mensuel': round(cashflow_mensuel, 2),
                'Déficits reportables': sum(deficits_reportables)
            })

        return pd.DataFrame(resultats)

# Tu veux aussi la partie SCI à l'IS complète ?
# --------------------------------------------------------------------------------
# CLASSE SCI À L'IS
# --------------------------------------------------------------------------------
elif regime == "SCI à l'IS":

    @dataclass
    class SCIaIS:
        prix_bien: float
        part_terrain: float
        apport: float
        frais_dossier: float
        frais_agence: float
        montant_travaux: float
        frais_garantie: float
        frais_tiers: float
        mobilier: float

        duree_annees: int
        taux_interet: float
        taux_assurance: float
        differe_mois: int

        charges_copro: float
        assurance: float
        taxe_fonciere: float
        frais_entretien: float
        frais_compta: float
        frais_bancaires: float
        loyer_mensuel_hc: float
        vacance_locative_mois: int

        duree_amort_bati: int
        duree_amort_travaux: int
        duree_amort_mobilier: int
        duree_amort_frais: int

        gestion_locative: float = 0.0
        frais_notaire_pct: float = 8.0

        montant_emprunt: float = field(init=False)
        frais_notaire: float = field(init=False)

        def __post_init__(self):
            self.frais_notaire = self.prix_bien * self.frais_notaire_pct / 100
            total_a_financer = (
                self.prix_bien + self.frais_notaire + self.frais_agence +
                self.frais_dossier + self.frais_garantie +
                self.frais_tiers + self.montant_travaux
            )
            self.montant_emprunt = max(0, total_a_financer - self.apport)

        def mensualite_emprunt(self):
            taux_mensuel = self.taux_interet / 100 / 12
            taux_assurance = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt

            capital_differe = capital
            for _ in range(self.differe_mois):
                capital_differe += capital_differe * taux_mensuel

            nb_mensualites = self.duree_annees * 12 - self.differe_mois
            if nb_mensualites <= 0:
                raise ValueError("Durée ou différé incohérents")

            mensualite_hors_assurance = capital_differe * taux_mensuel / (1 - (1 + taux_mensuel) ** -nb_mensualites)
            mensualite_totale = mensualite_hors_assurance + capital * taux_assurance
            return mensualite_totale

        def tableau_amortissement_emprunt(self):
            taux_mensuel = self.taux_interet / 100 / 12
            capital = self.montant_emprunt
            capital_rest = capital
            mensualite_hors_assurance = None
            rows = []

            for mois in range(1, self.duree_annees * 12 + 1):
                if mois <= self.differe_mois:
                    interets = capital_rest * taux_mensuel
                    principal = 0
                    capital_rest += interets
                else:
                    if mensualite_hors_assurance is None:
                        mensualite_hors_assurance = self.mensualite_emprunt() - capital * (self.taux_assurance / 100 / 12)
                    interets = capital_rest * taux_mensuel
                    principal = mensualite_hors_assurance - interets
                    capital_rest -= principal
                    if capital_rest < 0:
                        principal += capital_rest
                        capital_rest = 0
                rows.append({
                    'Mois': mois,
                    'Année': (mois - 1) // 12 + 1,
                    'Intérêts': interets,
                    'Principal': principal,
                    'Capital restant dû': capital_rest
                })

            return pd.DataFrame(rows)

        def amortissements(self):
            valeur_bati = self.prix_bien * (1 - self.part_terrain / 100)
            amortissements = []

            for annee in range(1, 11):
                bati = valeur_bati / self.duree_amort_bati if annee <= self.duree_amort_bati else 0
                mobilier = self.mobilier / self.duree_amort_mobilier if annee <= self.duree_amort_mobilier else 0
                travaux = self.montant_travaux / self.duree_amort_travaux if annee <= self.duree_amort_travaux else 0
                frais = (
                    (self.frais_dossier + self.frais_agence + self.frais_garantie + self.frais_tiers)
                    / self.duree_amort_frais if annee <= self.duree_amort_frais else 0
                )
                total = bati + mobilier + travaux + frais
                amortissements.append({
                    'Année': annee,
                    'Amortissement Bâti': bati,
                    'Amortissement Mobilier': mobilier,
                    'Amortissement Travaux': travaux,
                    'Amortissement Frais': frais,
                    'Total Amortissement': total
                })

            return pd.DataFrame(amortissements)

        def resultat_fiscal_annuel(self):
            amort = self.amortissements().set_index('Année')['Total Amortissement'].to_dict()
            interets = self.tableau_amortissement_emprunt().groupby('Année')['Intérêts'].sum().to_dict()

            mensualite = self.mensualite_emprunt()
            resultats = []

            deficit_reportable = 0.0

            for annee in range(1, 11):
                revenus = self.loyer_mensuel_hc * (12 - self.vacance_locative_mois)
                charges_reelles = (
                    self.charges_copro + self.assurance + self.taxe_fonciere +
                    self.frais_entretien + self.frais_compta + self.frais_bancaires +
                    self.gestion_locative
                )
                charges_repercutees = self.charges_copro * 0.8
                charges_fiscales = charges_reelles - charges_repercutees

                interet = interets.get(annee, 0.0)
                dotation = amort.get(annee, 0.0)

                resultat_fiscal_brut = revenus - charges_fiscales - interet - dotation
                resultat_fiscal_net = resultat_fiscal_brut + deficit_reportable

                if resultat_fiscal_net < 0:
                    impot = 0.0
                    deficit_reportable = resultat_fiscal_net  # cumul du déficit (négatif)
                else:
                    if resultat_fiscal_net <= 42500:
                        impot = resultat_fiscal_net * 0.15
                    else:
                        impot = 42500 * 0.15 + (resultat_fiscal_net - 42500) * 0.25
                    deficit_reportable = 0.0

                cashflow_mensuel = (
                    (revenus - charges_reelles - impot - mensualite * 12) / 12 +
                    charges_repercutees / 12
                )

                resultats.append({
                    'Année': annee,
                    'Revenus nets': round(revenus, 2),
                    'Charges réelles': round(charges_reelles, 2),
                    'Charges récupérées': round(charges_repercutees, 2),
                    'Intérêts': round(interet, 2),
                    'Amortissements': round(dotation, 2),
                    'Résultat fiscal (avant déficit)': round(resultat_fiscal_brut, 2),
                    'Résultat fiscal net': round(resultat_fiscal_net, 2),
                    'Déficit reportable': round(deficit_reportable, 2) if deficit_reportable < 0 else 0.0,
                    'IS': round(impot, 2),
                    'Cashflow mensuel (€)': round(cashflow_mensuel, 2)
                })

            return pd.DataFrame(resultats)



    # Interface utilisateur SCI
    st.header("Simulation SCI à l'IS")

    prix_bien = st.number_input("Prix du bien (€)", value=200000)
    part_terrain = st.number_input("Part du terrain (%)", value=15)
    apport = st.number_input("Apport (€)", value=20000)
    frais_agence = st.number_input("Frais d'agence (€)", value=5000)
    frais_dossier = st.number_input("Frais de dossier (€)", value=1000)
    montant_travaux = st.number_input("Montant des travaux (€)", value=10000)
    frais_garantie = st.number_input("Frais de garantie (€)", value=1000)
    frais_tiers = st.number_input("Frais tiers (€)", value=500)
    mobilier = st.number_input("Montant du mobilier (€)", value=3000)

    duree_amort_bati = st.slider("Durée d'amortissement bâti (ans)", 20, 50, 30)
    duree_amort_travaux = st.slider("Durée d'amortissement travaux (ans)", 1, 30, 10)
    duree_amort_mobilier = st.slider("Durée d'amortissement mobilier (ans)", 1, 30, 7)
    duree_amort_frais = st.slider("Durée d'amortissement frais (ans)", 1, 30, 5)

    duree_annees = st.slider("Durée du prêt (années)", 5, 30, 20)
    taux_interet = st.number_input("Taux d'intérêt (%)", value=2.0)
    taux_assurance = st.number_input("Taux assurance emprunteur (%)", value=0.3)
    differe_mois = st.slider("Différé de remboursement (mois)", 0, 24, 0)

    charges_copro = st.number_input("Charges de copropriété (€)", value=1000)
    assurance = st.number_input("Assurance (€)", value=200)
    taxe_fonciere = st.number_input("Taxe foncière (€)", value=800)
    frais_entretien = st.number_input("Frais d'entretien (€)", value=400)
    frais_compta = st.number_input("Frais de comptabilité (€)", value=500)
    frais_bancaires = st.number_input("Frais bancaires (€)", value=100)
    gestion_locative = st.number_input("Frais de gestion locative (€)", value=0)

    loyer_mensuel_hc = st.number_input("Loyer mensuel HC (€)", value=850)
    vacance_locative_mois = st.slider("Mois de vacance locative", 0, 12, 1)

    if st.button("Lancer la simulation"):
        sci = SCIaIS(
            prix_bien, part_terrain, apport, frais_dossier, frais_agence, montant_travaux,
            frais_garantie, frais_tiers, mobilier,
            duree_annees, taux_interet, taux_assurance, differe_mois,
            charges_copro, assurance, taxe_fonciere, frais_entretien,
            frais_compta, frais_bancaires, loyer_mensuel_hc, vacance_locative_mois,
            duree_amort_bati, duree_amort_travaux, duree_amort_mobilier, duree_amort_frais,
            gestion_locative
        )

        st.subheader("Frais de notaire calculés :")
        st.write(f"{sci.frais_notaire:,.0f} €")

        st.subheader("Montant de l'emprunt calculé :")
        st.write(f"{sci.montant_emprunt:,.0f} €")

        st.subheader("Résultats sur 10 ans")
        st.dataframe(sci.resultat_fiscal_annuel())
        st.subheader("Amortissements")
        st.dataframe(sci.amortissements())
        st.subheader("Tableau d'amortissement de l'emprunt")
        st.dataframe(sci.tableau_amortissement_emprunt())
