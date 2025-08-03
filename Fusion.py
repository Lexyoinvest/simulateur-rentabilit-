import streamlit as st
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

# 🔐 Interface de connexion stylisée
def login():
    try:
        credentials = pd.read_csv("credentials.csv")
    except FileNotFoundError:
        st.error("Fichier des identifiants manquant.")
        st.stop()

    # Branding Lexyo : logo + titre
    st.markdown("""
        <div style='text-align: left; padding-top: 40px; padding-bottom: 20px;'>
            <h1 style='color: #31333F; font-size: 42px;'>Se connecter à Lexyo</h1>
        </div>
    """, unsafe_allow_html=True)


    username = st.text_input("Identifiant")
    password = st.text_input("Mot de passe", type="password")

    login_btn = st.button("Se connecter", use_container_width=True)

    if login_btn:
        if ((credentials['username'] == username) & (credentials['password'] == password)).any():
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.rerun()  # Force le rafraîchissement
        else:
            st.error("Identifiant ou mot de passe incorrect.")

# ✅ Empêche d'accéder à l'app si non connecté
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.set_page_config(page_title="Connexion Lexyo", layout="centered")
    login()
    st.stop()
    
st.set_page_config(page_title="Lexyo Simulateur de Rentabilité Immobilière", layout="wide")

# 🌈 Custom CSS : Sliders + Titre aligné gauche + couleurs
st.markdown("""
    <style>
    /* Titre principal et sous-titre alignés à gauche */
    h1, h2 {
        text-align: left !important;
        padding-left: 1rem;
    }

    /* Titre Lexyo rose et Simulateur en dégradé */
    .main-title {
        font-size: 48px;
        font-weight: bold;
        padding-left: 1rem;
    }

    /* Sliders : fond rose pour la ligne active */
    [data-baseweb="slider"] > div > div > div:first-child {
        background-color: #ff00ff !important;
    }

    /* Sliders : couleur du thumb (point mobile) */
    [data-baseweb="slider"] span[role="slider"] {
        background-color: #ff00ff !important;
        border: 2px solid #ff00ff !important;
    }

    /* Sliders : valeurs min et max (fond blanc, texte noir) */
    [data-baseweb="slider"] > div > div > div > div {
        background-color: white !important;
        color: black !important;
        border: none !important;
        box-shadow: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# 🎨 Titre Lexyo (rose) + Simulateur (dégradé)
st.markdown("""
    <h1 class="main-title">
        <span style="color: #ff00ff;">Lexyo</span>
        <span style="
            background: linear-gradient(to right, #ff00ff, #000000);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        ">Simulateur</span> de rentabilité immobilière
    </h1>
""", unsafe_allow_html=True)


# Menu à gauche
regime = st.sidebar.selectbox("Choisissez le régime fiscal :", ["LMNP réel", "LMNP Micro-Bic", "LMP réel", "SCI à l'IS", "SCI à l'IR", "SARL de famille", "Holding à l'IS", "Location nue", "Micro foncier", "Réel foncier"])

# --------------------------------------------------------------------------------
# CLASSE LMNP RÉEL
# --------------------------------------------------------------------------------
if regime == "LMNP réel":

    @dataclass
    class LMNPReel:
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
        assurance_habitation: float
        assurance_gli: float
        taxe_fonciere: float
        frais_entretien: float
        frais_compta: float
        frais_bancaires: float
        gestion_locative: float
        taxe_habitation: float
        loyer_mensuel_hc: float
        vacance_locative_mois: int
        tmi: float
        frais_notaire_pct: float = 8.0
        duree_amort_bati: int = 30
        duree_amort_mobilier: int = 7
        montant_emprunt: float = field(init=False)
        deficits_reportables: list = field(default_factory=lambda: [0] * 10)

        def __post_init__(self):
            frais_notaire = self.prix_bien * self.frais_notaire_pct / 100
            total_frais = (self.prix_bien + frais_notaire + self.frais_agence +
                           self.frais_dossier + self.montant_travaux +
                           self.frais_garantie + self.frais_tiers)
            self.montant_emprunt = max(0, total_frais - self.apport)

        def mensualite_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            capital_differe = capital
            for _ in range(self.differe_mois):
                capital_differe += capital_differe * tm
            n = self.duree_annees * 12 - self.differe_mois
            mensualite_hors_assurance = capital_differe * tm / (1 - (1 + tm) ** -n)
            assurance = capital * ta
            return mensualite_hors_assurance + assurance

        def tableau_amortissement(self):
            tm = self.taux_interet / 100 / 12
            capital = self.montant_emprunt
            capital_rest = capital
            mensualite = None
            rows = []

            for mois in range(1, self.duree_annees * 12 + 1):
                if mois <= self.differe_mois:
                    interets = capital_rest * tm
                    principal = 0
                    capital_rest += interets
                else:
                    if mensualite is None:
                        mensualite = self.mensualite_emprunt() - (capital * self.taux_assurance / 100 / 12)
                    interets = capital_rest * tm
                    principal = mensualite - interets
                    capital_rest -= principal
                    if capital_rest < 0:
                        principal += capital_rest
                        capital_rest = 0
                rows.append({
                    'Mois': mois,
                    'Année': (mois - 1) // 12 + 1,
                    'Capital restant dû': capital_rest,
                    'Intérêts': interets,
                    'Principal remboursé': principal,
                    'Assurance': capital * self.taux_assurance / 100 / 12
                })
            return pd.DataFrame(rows)

        def amortissements(self):
            valeur_bati = self.prix_bien * (1 - self.part_terrain / 100)
            bati = valeur_bati / self.duree_amort_bati
            mobilier = self.mobilier / self.duree_amort_mobilier
            rows = []
            for annee in range(1, 11):
                if annee <= self.differe_mois // 12:
                    amort_bati = 0
                    amort_mobilier = 0
                else:
                    amort_bati = bati if annee <= self.duree_amort_bati else 0
                    amort_mobilier = mobilier if annee <= self.duree_amort_mobilier else 0
                total = amort_bati + amort_mobilier
                rows.append({
                    'Année': annee,
                    'Amortissement Bâti': amort_bati,
                    'Amortissement Mobilier': amort_mobilier,
                    'Total Amortissement': total
                })
            return pd.DataFrame(rows)

        def resultat_fiscal_annuel(self):
            amort = self.amortissements().set_index('Année')['Total Amortissement'].to_dict()
            interets = self.tableau_amortissement().groupby('Année')['Intérêts'].sum().to_dict()
            mensualite = self.mensualite_emprunt()
            resultats = []

            for annee in range(1, 11):
                revenus = self.loyer_mensuel_hc * (12 - self.vacance_locative_mois)
                charges = (self.charges_copro + self.assurance_habitation + self.assurance_gli +
                           self.taxe_fonciere + self.frais_entretien + self.frais_compta +
                           self.frais_bancaires + self.gestion_locative + self.taxe_habitation)
                charges_recup = self.charges_copro * 0.8
                interet = interets.get(annee, 0)
                amorti = amort.get(annee, 0)
                resultat = revenus - charges - interet - amorti

                if resultat < 0:
                    self.deficits_reportables[annee - 1] = -resultat
                    resultat_fiscal = 0
                else:
                    resultat_fiscal = resultat
                    for i in range(annee):
                        if self.deficits_reportables[i] > 0:
                            if resultat_fiscal >= self.deficits_reportables[i]:
                                resultat_fiscal -= self.deficits_reportables[i]
                                self.deficits_reportables[i] = 0
                            else:
                                self.deficits_reportables[i] -= resultat_fiscal
                                resultat_fiscal = 0
                                break

                impot = resultat_fiscal * self.tmi / 100
                cashflow_mensuel = (revenus - charges - impot - mensualite * 12 + charges_recup) / 12

                resultats.append({
                    'Année': annee,
                    'Revenus nets': revenus,
                    'Charges': charges,
                    'Charges récupérables': charges_recup,
                    'Intérêts': interet,
                    'Amortissements': amorti,
                    'Résultat fiscal': resultat_fiscal,
                    'Impôt': impot,
                    'Cashflow mensuel': round(cashflow_mensuel, 2)
                })
            return pd.DataFrame(resultats)

    # Interface utilisateur LMNP
    st.title("LMNP Réel")

    prix_bien = st.number_input("Prix du bien (€)", value=0)
    part_terrain = st.slider("Part du terrain (%)", 0, 100, 15)
    apport = st.number_input("Apport (€)", value=0)
    frais_dossier = st.number_input("Frais de dossier (€)", value=0)
    frais_agence = st.number_input("Frais d'agence (€)", value=0)
    montant_travaux = st.number_input("Travaux (€)", value=0)
    frais_garantie = st.number_input("Frais de garantie (€)", value=0)
    frais_tiers = st.number_input("Frais de tiers (€)", value=0)
    mobilier = st.number_input("Mobilier (€)", value=0)

    duree_annees = st.slider("Durée prêt (années)", 5, 30, 20)
    taux_interet = st.number_input("Taux d'intérêt (%)", value=3.0)
    taux_assurance = st.number_input("Taux assurance emprunteur (%)", value=0.3)
    differe_mois = st.slider("Différé (mois)", 0, 24, 0)

    charges_copro = st.number_input("Charges copropriété (€)", value=0)
    assurance_habitation = st.number_input("Assurance habitation (€)", value=0)
    assurance_gli = st.number_input("Assurance GLI (€)", value=0)
    taxe_fonciere = st.number_input("Taxe foncière (€)", value=0)
    frais_entretien = st.number_input("Entretien (€)", value=0)
    frais_compta = st.number_input("Comptabilité (€)", value=0)
    frais_bancaires = st.number_input("Frais bancaires (€)", value=0)
    gestion_locative = st.number_input("Gestion locative (€)", value=0)
    taxe_habitation = st.number_input("Taxe d'habitation (€)", value=0)

    loyer_mensuel_hc = st.number_input("Loyer mensuel HC (€)", value=0)
    vacance_locative_mois = st.slider("Vacance locative (mois)", 0, 12, 0)
    tmi = st.slider("TMI (%)", 0, 45, 30)

    if st.button("Lancer la simulation"):
        lmnp = LMNPReel(
            prix_bien, part_terrain, apport, frais_dossier, frais_agence,
            montant_travaux, frais_garantie, frais_tiers, mobilier,
            duree_annees, taux_interet, taux_assurance, differe_mois,
            charges_copro, assurance_habitation, assurance_gli, taxe_fonciere,
            frais_entretien, frais_compta, frais_bancaires, gestion_locative,
            taxe_habitation, loyer_mensuel_hc, vacance_locative_mois, tmi
        )
        st.subheader("📆 Résultats sur 10 ans")
        st.dataframe(lmnp.resultat_fiscal_annuel())
        st.subheader("📉 Tableau d’amortissement de l’emprunt")
        st.dataframe(lmnp.tableau_amortissement())
        st.subheader("📑 Amortissements comptables")
        st.dataframe(lmnp.amortissements())
# Tu veux aussi la partie SCI à l'IS complète ?
# --------------------------------------------------------------------------------
# CLASSE SCI À L'IS
# --------------------------------------------------------------------------------
elif regime == "SCI à l'IS":

    # --------------------------------------------------------------------------------
# CLASSE SCI À L'IS
# --------------------------------------------------------------------------------
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
        assurance_gli: float
        taxe_fonciere: float
        frais_entretien: float
        frais_compta: float
        frais_bancaires: float
        gestion_locative: float
        loyer_mensuel_hc: float
        vacance_locative_mois: int

        duree_amort_bati: int
        duree_amort_travaux: int
        duree_amort_mobilier: int
        duree_amort_frais: int

        frais_notaire_pct: float = 8.0
        montant_emprunt: float = field(init=False)
        frais_notaire: float = field(init=False)

        def __post_init__(self):
            self.frais_notaire = self.prix_bien * self.frais_notaire_pct / 100
            total_a_financer = (
                self.prix_bien + self.frais_notaire + self.frais_agence +
                self.frais_dossier + self.frais_garantie + self.frais_tiers + self.montant_travaux
            )
            self.montant_emprunt = max(0, total_a_financer - self.apport)

        def mensualite_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt

            for _ in range(self.differe_mois):
                capital += capital * tm

            n = self.duree_annees * 12 - self.differe_mois
            if n <= 0:
                raise ValueError("Durée ou différé incohérents")

            m_hors_assurance = capital * tm / (1 - (1 + tm) ** -n)
            m_assurance = self.montant_emprunt * ta
            return m_hors_assurance + m_assurance

        def tableau_amortissement_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            capital_rest = capital
            mensualite_hors_assurance = None
            rows = []

            for mois in range(1, self.duree_annees * 12 + 1):
                if mois <= self.differe_mois:
                    interets = capital_rest * tm
                    principal = 0
                    capital_rest += interets
                else:
                    if mensualite_hors_assurance is None:
                        mensualite_hors_assurance = self.mensualite_emprunt() - capital * ta
                    interets = capital_rest * tm
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
                    'Assurance': capital * ta,
                    'Capital restant dû': capital_rest
                })

            return pd.DataFrame(rows)

        def amortissements(self):
            valeur_bati = self.prix_bien * (1 - self.part_terrain / 100)
            rows = []
            for annee in range(1, 11):
                bati = valeur_bati / self.duree_amort_bati if annee <= self.duree_amort_bati else 0
                mobilier = self.mobilier / self.duree_amort_mobilier if annee <= self.duree_amort_mobilier else 0
                travaux = self.montant_travaux / self.duree_amort_travaux if annee <= self.duree_amort_travaux else 0
                frais = (self.frais_dossier + self.frais_agence + self.frais_garantie + self.frais_tiers) / self.duree_amort_frais if annee <= self.duree_amort_frais else 0
                total = bati + mobilier + travaux + frais
                rows.append({
                    'Année': annee,
                    'Amortissement Bâti': bati,
                    'Amortissement Mobilier': mobilier,
                    'Amortissement Travaux': travaux,
                    'Amortissement Frais': frais,
                    'Total Amortissement': total
                })
            return pd.DataFrame(rows)

        def resultat_fiscal_annuel(self):
            amort = self.amortissements().set_index('Année')['Total Amortissement'].to_dict()
            amort_table = self.tableau_amortissement_emprunt()
            interets = amort_table.groupby('Année')['Intérêts'].sum().to_dict()
            assurances = amort_table.groupby('Année')['Assurance'].sum().to_dict()

            mensualite = self.mensualite_emprunt()
            results = []
            deficit_reportable = 0.0

            for annee in range(1, 11):
                revenus = self.loyer_mensuel_hc * (12 - self.vacance_locative_mois)

                charges_reelles = (
                    self.charges_copro + self.assurance + self.assurance_gli +
                    self.taxe_fonciere + self.frais_entretien + self.frais_compta +
                    self.frais_bancaires + self.gestion_locative
                )
                charges_recup = self.charges_copro * 0.8
                charges_fiscales = charges_reelles - charges_recup

                interet = interets.get(annee, 0.0)
                assurance = assurances.get(annee, 0.0)
                dotation = amort.get(annee, 0.0)

                resultat_brut = revenus - charges_fiscales - interet - assurance - dotation
                resultat_net = resultat_brut + deficit_reportable

                if resultat_net < 0:
                    is_impot = 0.0
                    deficit_reportable = resultat_net
                else:
                    if resultat_net <= 42500:
                        is_impot = resultat_net * 0.15
                    else:
                        is_impot = 42500 * 0.15 + (resultat_net - 42500) * 0.25
                    deficit_reportable = 0.0

                cashflow_mensuel = (revenus - charges_reelles - is_impot - mensualite * 12 + charges_recup) / 12

                results.append({
                    'Année': annee,
                    'Revenus': revenus,
                    'Charges réelles': charges_reelles,
                    'Charges récupérables': charges_recup,
                    'Intérêts': interet,
                    'Assurance': assurance,
                    'Amortissements': dotation,
                    'Résultat fiscal brut': resultat_brut,
                    'Résultat fiscal net': resultat_net,
                    'Déficit reportable': deficit_reportable if deficit_reportable < 0 else 0.0,
                    'IS': is_impot,
                    'Cashflow mensuel (€)': round(cashflow_mensuel, 2)
                })

            return pd.DataFrame(results)

    # Interface utilisateur SCI à l'IS
    st.title("Simulateur SCI à l’IS")

    prix_bien = st.number_input("Prix du bien (€)", value=0)
    part_terrain = st.slider("Part du terrain (%)", 0, 100, 15)
    apport = st.number_input("Apport (€)", value=0)
    frais_dossier = st.number_input("Frais de dossier (€)", value=0)
    frais_agence = st.number_input("Frais d’agence (€)", value=0)
    montant_travaux = st.number_input("Montant des travaux (€)", value=0)
    frais_garantie = st.number_input("Frais de garantie (€)", value=0)
    frais_tiers = st.number_input("Frais de tiers (€)", value=0)
    mobilier = st.number_input("Montant mobilier (€)", value=0)

    duree_annees = st.slider("Durée prêt (années)", 5, 30, 20)
    taux_interet = st.number_input("Taux d’intérêt (%)", value=3.0)
    taux_assurance = st.number_input("Taux assurance emprunteur (%)", value=0.3)
    differe_mois = st.slider("Différé (mois)", 0, 24, 0)

    charges_copro = st.number_input("Charges de copropriété (€)", value=0)
    assurance = st.number_input("Assurance PNO (€)", value=0)
    assurance_gli = st.number_input("Assurance GLI (€)", value=0)
    taxe_fonciere = st.number_input("Taxe foncière (€)", value=0)
    frais_entretien = st.number_input("Frais d'entretien (€)", value=0)
    frais_compta = st.number_input("Frais comptabilité (€)", value=0)
    frais_bancaires = st.number_input("Frais bancaires (€)", value=0)
    gestion_locative = st.number_input("Gestion locative (€)", value=0)

    loyer_mensuel_hc = st.number_input("Loyer mensuel HC (€)", value=0)
    vacance_locative_mois = st.slider("Vacance locative (mois)", 0, 12, 0)

    duree_amort_bati = st.slider("Amortissement bâti", 20, 50, 30)
    duree_amort_travaux = st.slider("Amortissement travaux", 5, 20, 10)
    duree_amort_mobilier = st.slider("Amortissement mobilier", 5, 15, 7)
    duree_amort_frais = st.slider("Amortissement frais annexes", 3, 10, 5)

    if st.button("Lancer la simulation SCI à l'IS"):
        sci = SCIaIS(
            prix_bien, part_terrain, apport, frais_dossier, frais_agence, montant_travaux,
            frais_garantie, frais_tiers, mobilier,
            duree_annees, taux_interet, taux_assurance, differe_mois,
            charges_copro, assurance, assurance_gli, taxe_fonciere,
            frais_entretien, frais_compta, frais_bancaires, gestion_locative,
            loyer_mensuel_hc, vacance_locative_mois,
            duree_amort_bati, duree_amort_travaux, duree_amort_mobilier, duree_amort_frais
        )
        st.subheader("📊 Résultats sur 10 ans")
        st.dataframe(sci.resultat_fiscal_annuel())
        st.subheader("📉 Tableau d’amortissement de l’emprunt")
        st.dataframe(sci.tableau_amortissement_emprunt())
        st.subheader("📑 Amortissements comptables")
        st.dataframe(sci.amortissements())


# --------------------------------------------------------------------------------
# CLASSE MICRO BIC
# --------------------------------------------------------------------------------
elif regime == "LMNP Micro-Bic":

    @dataclass
    class MicroBIC:
        # Revenus
        loyer_mensuel_hc: float
        vacance_locative_mois: int

        # Charges réelles non déductibles
        charges_copro: float
        taxe_fonciere: float
        frais_gestion: float
        assurance_pno: float
        assurance_gli: float

        # Emprunt
        montant_emprunt: float
        duree_annees: int
        taux_interet: float
        taux_assurance: float
        differe_mois: int

        # Fiscalité
        tmi: float
        csg_crds: float = 17.2
        abattement: float = 0.5
        plafond_microbic: float = 77700

        def revenus_annuels(self):
            return self.loyer_mensuel_hc * (12 - self.vacance_locative_mois)

        def revenu_imposable(self):
            return self.revenus_annuels() * (1 - self.abattement)

        def impot_ir(self):
            return self.revenu_imposable() * (self.tmi / 100)

        def prelevements_sociaux(self):
            return self.revenu_imposable() * (self.csg_crds / 100)

        def mensualite_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt

            # différé : capital augmente des intérêts intercalaires
            for _ in range(self.differe_mois):
                capital += capital * tm

            n = self.duree_annees * 12 - self.differe_mois
            if n <= 0:
                return 0

            m_hors_assurance = capital * tm / (1 - (1 + tm) ** -n)
            m_assurance = self.montant_emprunt * ta
            return m_hors_assurance + m_assurance

        def charges_non_recup(self):
            return (
                self.taxe_fonciere +
                self.frais_gestion +
                self.assurance_pno +
                self.assurance_gli +
                self.charges_copro * 0.2
            )

        def cashflow_annuel(self):
            mensualite = self.mensualite_emprunt()
            return (
                self.revenus_annuels()
                - self.impot_ir()
                - self.prelevements_sociaux()
                - self.charges_non_recup()
                - mensualite * 12
            )

        def resultat_fiscal_annuel(self):
            revenu_brut = self.revenus_annuels()
            revenu_net = self.revenu_imposable()
            ir = self.impot_ir()
            ps = self.prelevements_sociaux()
            mensualite = self.mensualite_emprunt()
            charges_non_recup = self.charges_non_recup()
            cashflow = self.cashflow_annuel()

            rows = []
            for annee in range(1, 11):
                rows.append({
                    "Année": annee,
                    "Revenus bruts": round(revenu_brut, 2),
                    "Abattement 50%": round(revenu_brut * self.abattement, 2),
                    "Revenu imposable": round(revenu_net, 2),
                    "IR (TMI)": round(ir, 2),
                    "Prélèvements sociaux (17.2%)": round(ps, 2),
                    "Charges non récupérables": round(charges_non_recup, 2),
                    "Mensualité de prêt (avec assurance)": round(mensualite, 2),
                    "💡 Remarque": "Aucune charge déductible fiscalement",
                    "Cashflow mensuel (€)": round(cashflow / 12, 2)
                })
            return pd.DataFrame(rows)

    # Interface utilisateur Micro BIC
    st.title("Simulation LMNP Micro BIC")

    st.subheader("Revenus")
    loyer_mensuel_hc = st.number_input("Loyer mensuel HC (€)", value=0)
    vacance_locative_mois = st.slider("Vacance locative (mois)", 0, 12, 0)

    st.subheader("Charges")
    charges_copro = st.number_input("Charges de copropriété (€)", value=0)
    taxe_fonciere = st.number_input("Taxe foncière (€)", value=0)
    frais_gestion = st.number_input("Frais de gestion locative (€)", value=0)
    assurance_pno = st.number_input("Assurance PNO (€)", value=0)
    assurance_gli = st.number_input("Assurance GLI (€)", value=0)

    st.subheader("Emprunt")
    montant_emprunt = st.number_input("Montant emprunté (€)", value=0)
    duree_annees = st.slider("Durée de l’emprunt (ans)", 5, 30, 20)
    taux_interet = st.number_input("Taux d’intérêt (%)", value=3.0)
    taux_assurance = st.number_input("Taux assurance (%)", value=0.3)
    differe_mois = st.slider("Différé (mois)", 0, 24, 0)

    st.subheader("Fiscalité")
    tmi = st.slider("TMI (%)", 11, 45, 30)

    if st.button("Lancer la simulation LMNP Micro BIC"):
        microbic = MicroBIC(
            loyer_mensuel_hc, vacance_locative_mois,
            charges_copro, taxe_fonciere, frais_gestion,
            assurance_pno, assurance_gli,
            montant_emprunt, duree_annees, taux_interet, taux_assurance, differe_mois,
            tmi
        )

        if microbic.revenus_annuels() > microbic.plafond_microbic:
            st.warning(f"⚠️ Revenus bruts annuels ({microbic.revenus_annuels():,.0f} €) dépassent le plafond micro-BIC ({microbic.plafond_microbic:,.0f} €). Basculer vers le régime réel.")

        st.subheader("📊 Résultats sur 10 ans")
        st.dataframe(microbic.resultat_fiscal_annuel()) 

elif regime == "SCI à l'IR":

    @dataclass
    class SCIaIR:
        prix_bien: float
        part_terrain: float
        apport: float
        frais_dossier: float
        frais_agence: float
        montant_travaux: float
        frais_garantie: float
        frais_tiers: float

        duree_annees: int
        taux_interet: float
        taux_assurance: float
        differe_mois: int

        charges_copro: float
        assurance: float
        assurance_gli: float
        taxe_fonciere: float
        frais_entretien: float
        frais_compta: float
        frais_bancaires: float
        gestion_locative: float

        loyer_mensuel_hc: float
        vacance_locative_mois: int
        tmi: float

        frais_notaire_pct: float = 8.0
        montant_emprunt: float = field(init=False)
        frais_notaire: float = field(init=False)

        def __post_init__(self):
            self.frais_notaire = self.prix_bien * self.frais_notaire_pct / 100
            total_a_financer = (
                self.prix_bien + self.frais_notaire + self.frais_agence +
                self.frais_dossier + self.frais_garantie + self.frais_tiers + self.montant_travaux
            )
            self.montant_emprunt = max(0, total_a_financer - self.apport)

        def mensualite_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            for _ in range(self.differe_mois):
                capital += capital * tm
            n = self.duree_annees * 12 - self.differe_mois
            if n <= 0:
                raise ValueError("Durée ou différé incohérents")
            m_hors_assurance = capital * tm / (1 - (1 + tm) ** -n)
            m_assurance = self.montant_emprunt * ta
            return m_hors_assurance + m_assurance

        def tableau_amortissement_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            capital_rest = capital
            mensualite_hors_assurance = None
            rows = []
            for mois in range(1, self.duree_annees * 12 + 1):
                if mois <= self.differe_mois:
                    interets = capital_rest * tm
                    principal = 0
                    capital_rest += interets
                else:
                    if mensualite_hors_assurance is None:
                        mensualite_hors_assurance = self.mensualite_emprunt() - capital * ta
                    interets = capital_rest * tm
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
                    'Assurance': capital * ta,
                    'Capital restant dû': capital_rest
                })
            return pd.DataFrame(rows)

        def resultat_fiscal_annuel(self):
            interets = self.tableau_amortissement_emprunt().groupby('Année')['Intérêts'].sum().to_dict()
            assurances = self.tableau_amortissement_emprunt().groupby('Année')['Assurance'].sum().to_dict()
            mensualite = self.mensualite_emprunt()
            results = []
            deficit_reportable = 0.0

            for annee in range(1, 11):
                revenus = self.loyer_mensuel_hc * (12 - self.vacance_locative_mois)
                charges_reelles = (
                    self.charges_copro + self.assurance + self.assurance_gli +
                    self.taxe_fonciere + self.frais_entretien + self.frais_compta +
                    self.frais_bancaires + self.gestion_locative
                )
                charges_recup = self.charges_copro * 0.8
                interet = interets.get(annee, 0.0)
                assurance = assurances.get(annee, 0.0)

                resultat_foncier = revenus - charges_reelles - interet - assurance
                resultat_fiscal = resultat_foncier + deficit_reportable

                if resultat_fiscal < 0:
                    ir = 0.0
                    deficit_reportable = resultat_fiscal
                else:
                    ir = resultat_fiscal * (self.tmi / 100)
                    deficit_reportable = 0.0

                cashflow_mensuel = (revenus - charges_reelles - ir - mensualite * 12 + charges_recup) / 12

                results.append({
                    'Année': annee,
                    'Revenus': revenus,
                    'Charges réelles': charges_reelles,
                    'Charges récupérables': charges_recup,
                    'Intérêts': interet,
                    'Assurance': assurance,
                    'Résultat foncier': resultat_foncier,
                    'Résultat fiscal après report': resultat_fiscal,
                    'Déficit reportable': deficit_reportable if deficit_reportable < 0 else 0.0,
                    'Impôt sur le revenu (IR)': ir,
                    'Cashflow mensuel (€)': round(cashflow_mensuel, 2)
                })

            return pd.DataFrame(results)

    # Interface utilisateur SCI à l’IR
    st.title("Simulateur SCI à l’IR")

    prix_bien = st.number_input("Prix du bien (€)", value=0)
    part_terrain = st.slider("Part du terrain (%)", 0, 100, 15)
    apport = st.number_input("Apport (€)", value=0)
    frais_dossier = st.number_input("Frais de dossier (€)", value=0)
    frais_agence = st.number_input("Frais d’agence (€)", value=0)
    montant_travaux = st.number_input("Montant des travaux (€)", value=0)
    frais_garantie = st.number_input("Frais de garantie (€)", value=0)
    frais_tiers = st.number_input("Frais de tiers (€)", value=0)

    duree_annees = st.slider("Durée du prêt (années)", 5, 30, 20)
    taux_interet = st.number_input("Taux d’intérêt (%)", value=3.0)
    taux_assurance = st.number_input("Taux d’assurance emprunteur (%)", value=0.3)
    differe_mois = st.slider("Différé (mois)", 0, 24, 0)

    charges_copro = st.number_input("Charges de copropriété (€)", value=0)
    assurance = st.number_input("Assurance PNO (€)", value=0)
    assurance_gli = st.number_input("Assurance GLI (€)", value=0)
    taxe_fonciere = st.number_input("Taxe foncière (€)", value=0)
    frais_entretien = st.number_input("Frais d’entretien (€)", value=0)
    frais_compta = st.number_input("Frais de comptabilité (€)", value=0)
    frais_bancaires = st.number_input("Frais bancaires (€)", value=0)
    gestion_locative = st.number_input("Gestion locative (€)", value=0)

    loyer_mensuel_hc = st.number_input("Loyer mensuel HC (€)", value=0)
    vacance_locative_mois = st.slider("Vacance locative (mois)", 0, 12, 0)
    tmi = st.slider("TMI (Tranche Marginale d’Imposition en %)", 11, 45, 30)

    if st.button("Lancer la simulation SCI à l’IR"):
        sci_ir = SCIaIR(
            prix_bien, part_terrain, apport, frais_dossier, frais_agence, montant_travaux,
            frais_garantie, frais_tiers,
            duree_annees, taux_interet, taux_assurance, differe_mois,
            charges_copro, assurance, assurance_gli, taxe_fonciere,
            frais_entretien, frais_compta, frais_bancaires, gestion_locative,
            loyer_mensuel_hc, vacance_locative_mois, tmi
        )

        st.subheader("📆 Résultats SCI à l’IR sur 10 ans")
        st.dataframe(sci_ir.resultat_fiscal_annuel())
        
elif regime == "Location nue":

    @dataclass
    class LocationNue:
        prix_bien: float
        apport: float
        frais_dossier: float
        frais_agence: float
        montant_travaux: float
        frais_garantie: float
        frais_tiers: float

        duree_annees: int
        taux_interet: float
        taux_assurance: float
        differe_mois: int

        charges_copro: float
        taxe_fonciere: float
        frais_entretien: float
        frais_bancaires: float
        gestion_locative: float

        loyer_mensuel_hc: float
        vacance_locative_mois: int
        tmi: float  # Tranche marginale d'imposition

        frais_notaire_pct: float = 8.0
        montant_emprunt: float = field(init=False)
        frais_notaire: float = field(init=False)

        def __post_init__(self):
            self.frais_notaire = self.prix_bien * self.frais_notaire_pct / 100
            total_a_financer = (
                self.prix_bien + self.frais_notaire + self.frais_agence +
                self.frais_dossier + self.frais_garantie + self.frais_tiers + self.montant_travaux
            )
            self.montant_emprunt = max(0, total_a_financer - self.apport)

        def mensualite_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            for _ in range(self.differe_mois):
                capital += capital * tm
            n = self.duree_annees * 12 - self.differe_mois
            if n <= 0:
                raise ValueError("Durée ou différé incohérents")
            m_hors_assurance = capital * tm / (1 - (1 + tm) ** -n)
            m_assurance = self.montant_emprunt * ta
            return m_hors_assurance + m_assurance

        def tableau_amortissement_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            capital_rest = capital
            mensualite_hors_assurance = None
            rows = []
            for mois in range(1, self.duree_annees * 12 + 1):
                if mois <= self.differe_mois:
                    interets = capital_rest * tm
                    principal = 0
                    capital_rest += interets
                else:
                    if mensualite_hors_assurance is None:
                        mensualite_hors_assurance = self.mensualite_emprunt() - capital * ta
                    interets = capital_rest * tm
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
                    'Assurance': capital * ta,
                    'Capital restant dû': capital_rest
                })
            return pd.DataFrame(rows)

        def resultat_fiscal_annuel(self):
            amort_table = self.tableau_amortissement_emprunt()
            interets = amort_table.groupby('Année')['Intérêts'].sum().to_dict()
            assurances = amort_table.groupby('Année')['Assurance'].sum().to_dict()
            mensualite = self.mensualite_emprunt()
            results = []
            deficit_reportable = 0.0

            for annee in range(1, 11):
                revenus = self.loyer_mensuel_hc * (12 - self.vacance_locative_mois)

                charges_non_recup = (
                    self.taxe_fonciere + self.frais_entretien +
                    self.frais_bancaires + self.gestion_locative +
                    self.charges_copro * 0.2  # 20% non récupérables
                )

                charges_recup = self.charges_copro * 0.8  # 80% récupérables

                interet = interets.get(annee, 0.0)
                assurance = assurances.get(annee, 0.0)

                resultat_foncier = revenus - charges_non_recup - interet - assurance
                resultat_fiscal = resultat_foncier + deficit_reportable

                if resultat_fiscal < 0:
                    ir = 0.0
                    deficit_reportable = resultat_fiscal
                else:
                    ir = resultat_fiscal * (self.tmi / 100)
                    deficit_reportable = 0.0

                cashflow_mensuel = (revenus - charges_non_recup - ir - mensualite * 12 + charges_recup) / 12

                results.append({
                    'Année': annee,
                    'Revenus': revenus,
                    'Charges non récupérables': round(charges_non_recup, 2),
                    'Charges récupérables': round(charges_recup, 2),
                    'Intérêts': round(interet, 2),
                    'Assurance': round(assurance, 2),
                    'Résultat foncier': round(resultat_foncier, 2),
                    'Résultat fiscal après report': round(resultat_fiscal, 2),
                    'Déficit reportable': round(deficit_reportable, 2) if deficit_reportable < 0 else 0.0,
                    'IR': round(ir, 2),
                    'Cashflow mensuel (€)': round(cashflow_mensuel, 2)
                })

            return pd.DataFrame(results)

    # Interface utilisateur Location Nue
    st.title("Simulateur Location Nue")

    prix_bien = st.number_input("Prix du bien (€)", value=0)
    apport = st.number_input("Apport (€)", value=0)
    frais_dossier = st.number_input("Frais de dossier (€)", value=0)
    frais_agence = st.number_input("Frais d’agence (€)", value=0)
    montant_travaux = st.number_input("Montant des travaux (€)", value=0)
    frais_garantie = st.number_input("Frais de garantie (€)", value=0)
    frais_tiers = st.number_input("Frais de tiers (€)", value=0)

    duree_annees = st.slider("Durée du prêt (années)", 5, 30, 20)
    taux_interet = st.number_input("Taux d’intérêt (%)", value=3.0)
    taux_assurance = st.number_input("Taux d’assurance emprunteur (%)", value=0.3)
    differe_mois = st.slider("Différé (mois)", 0, 24, 0)

    charges_copro = st.number_input("Charges de copropriété (€)", value=0)
    taxe_fonciere = st.number_input("Taxe foncière (€)", value=0)
    frais_entretien = st.number_input("Frais d’entretien (€)", value=0)
    frais_bancaires = st.number_input("Frais bancaires (€)", value=0)
    gestion_locative = st.number_input("Gestion locative (€)", value=0)

    loyer_mensuel_hc = st.number_input("Loyer mensuel HC (€)", value=0)
    vacance_locative_mois = st.slider("Vacance locative (mois)", 0, 12, 0)
    tmi = st.slider("TMI (Tranche Marginale d’Imposition en %)", 11, 45, 30)

    if st.button("Lancer la simulation Location nue"):
        location = LocationNue(
            prix_bien, apport, frais_dossier, frais_agence, montant_travaux,
            frais_garantie, frais_tiers,
            duree_annees, taux_interet, taux_assurance, differe_mois,
            charges_copro, taxe_fonciere, frais_entretien,
            frais_bancaires, gestion_locative,
            loyer_mensuel_hc, vacance_locative_mois, tmi
        )

        st.subheader("📆 Résultats Location nue sur 10 ans")
        st.dataframe(location.resultat_fiscal_annuel())

        st.subheader("📉 Tableau d’amortissement de l’emprunt")
        st.dataframe(location.tableau_amortissement_emprunt()) 

elif regime == "Micro foncier":

    @dataclass
    class MicroFoncier:
        loyer_mensuel_hc: float
        vacance_locative_mois: int
        tmi: float

        prix_bien: float
        apport: float
        frais_dossier: float
        frais_agence: float
        montant_travaux: float
        frais_garantie: float
        frais_tiers: float

        duree_annees: int
        taux_interet: float
        taux_assurance: float
        differe_mois: int

        charges_copro: float
        taxe_fonciere: float
        frais_entretien: float
        frais_bancaires: float
        gestion_locative: float

        frais_notaire_pct: float = 8.0
        csg_crds: float = 17.2
        abattement: float = 0.3
        montant_emprunt: float = field(init=False)
        frais_notaire: float = field(init=False)

        def __post_init__(self):
            self.frais_notaire = self.prix_bien * self.frais_notaire_pct / 100
            total_a_financer = (
                self.prix_bien + self.frais_notaire + self.frais_agence +
                self.frais_dossier + self.frais_garantie + self.frais_tiers + self.montant_travaux
            )
            self.montant_emprunt = max(0, total_a_financer - self.apport)

        def mensualite_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            for _ in range(self.differe_mois):
                capital += capital * tm
            n = self.duree_annees * 12 - self.differe_mois
            if n <= 0:
                raise ValueError("Durée ou différé incohérents")
            m_hors_assurance = capital * tm / (1 - (1 + tm) ** -n)
            m_assurance = self.montant_emprunt * ta
            return m_hors_assurance + m_assurance

        def tableau_amortissement_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            capital_rest = capital
            mensualite_hors_assurance = None
            rows = []
            for mois in range(1, self.duree_annees * 12 + 1):
                if mois <= self.differe_mois:
                    interets = capital_rest * tm
                    principal = 0
                    capital_rest += interets
                else:
                    if mensualite_hors_assurance is None:
                        mensualite_hors_assurance = self.mensualite_emprunt() - capital * ta
                    interets = capital_rest * tm
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
                    'Assurance': capital * ta,
                    'Capital restant dû': capital_rest
                })
            return pd.DataFrame(rows)

        def resultat_fiscal_annuel(self):
            interets = self.tableau_amortissement_emprunt().groupby('Année')['Intérêts'].sum().to_dict()
            assurances = self.tableau_amortissement_emprunt().groupby('Année')['Assurance'].sum().to_dict()
            mensualite = self.mensualite_emprunt()

            rows = []
            for annee in range(1, 11):
                revenus = self.loyer_mensuel_hc * (12 - self.vacance_locative_mois)
                revenu_imposable = revenus * (1 - self.abattement)
                ir = revenu_imposable * (self.tmi / 100)
                ps = revenu_imposable * (self.csg_crds / 100)

                charges_reelles = (
                    self.charges_copro + self.taxe_fonciere + self.frais_entretien +
                    self.frais_bancaires + self.gestion_locative
                )
                charges_recup = self.charges_copro * 0.8
                interet = interets.get(annee, 0.0)
                assurance = assurances.get(annee, 0.0)

                cashflow = (revenus - charges_reelles - interet - assurance - ir - ps + charges_recup - mensualite * 12) / 12

                rows.append({
                    "Année": annee,
                    "Revenus bruts": round(revenus, 2),
                    "Revenu imposable (abattement 30%)": round(revenu_imposable, 2),
                    "IR (TMI)": round(ir, 2),
                    "Prélèvements sociaux (17.2%)": round(ps, 2),
                    "Charges réelles": round(charges_reelles, 2),
                    "Intérêts": round(interet, 2),
                    "Assurance emprunt": round(assurance, 2),
                    "Charges récupérables": round(charges_recup, 2),
                    "Mensualité emprunt (annuelle)": round(mensualite * 12, 2),
                    "Cashflow mensuel": round(cashflow, 2) / 12
                })

            return pd.DataFrame(rows)

    # Interface utilisateur Micro-Foncier
    st.title("Simulateur Micro-Foncier")

    prix_bien = st.number_input("Prix du bien (€)", value=0)
    apport = st.number_input("Apport (€)", value=0)
    frais_dossier = st.number_input("Frais de dossier (€)", value=0)
    frais_agence = st.number_input("Frais d’agence (€)", value=0)
    montant_travaux = st.number_input("Montant des travaux (€)", value=0)
    frais_garantie = st.number_input("Frais de garantie (€)", value=0)
    frais_tiers = st.number_input("Frais de tiers (€)", value=0)

    duree_annees = st.slider("Durée prêt (années)", 5, 30, 20)
    taux_interet = st.number_input("Taux d’intérêt (%)", value=3.0)
    taux_assurance = st.number_input("Taux assurance emprunteur (%)", value=0.3)
    differe_mois = st.slider("Différé (mois)", 0, 24, 0)

    charges_copro = st.number_input("Charges de copropriété (€)", value=0)
    taxe_fonciere = st.number_input("Taxe foncière (€)", value=0)
    frais_entretien = st.number_input("Frais d’entretien (€)", value=0)
    frais_bancaires = st.number_input("Frais bancaires (€)", value=0)
    gestion_locative = st.number_input("Frais de gestion locative (€)", value=0)

    loyer_mensuel_hc = st.number_input("Loyer mensuel HC (€)", value=0)
    vacance_locative_mois = st.slider("Vacance locative (mois)", 0, 12, 1)
    tmi = st.slider("TMI (Tranche Marginale d’Imposition en %)", 0, 45, 30)

    if st.button("Lancer la simulation Micro-Foncier"):
        micro = MicroFoncier(
            loyer_mensuel_hc, vacance_locative_mois, tmi,
            prix_bien, apport, frais_dossier, frais_agence, montant_travaux,
            frais_garantie, frais_tiers,
            duree_annees, taux_interet, taux_assurance, differe_mois,
            charges_copro, taxe_fonciere, frais_entretien, frais_bancaires, gestion_locative
        )

        st.subheader("📊 Résultats Micro-Foncier sur 10 ans")
        st.dataframe(micro.resultat_fiscal_annuel())
        st.subheader("📉 Tableau d’amortissement de l’emprunt")
        st.dataframe(micro.tableau_amortissement_emprunt())

elif regime == "LMP réel":

    @dataclass
    class LMPReel:
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
        assurance_gli: float
        taxe_fonciere: float
        frais_entretien: float
        frais_compta: float
        frais_bancaires: float
        gestion_locative: float
        loyer_mensuel_hc: float
        vacance_locative_mois: int
        tmi: float

        duree_amort_bati: int
        duree_amort_travaux: int
        duree_amort_mobilier: int
        duree_amort_frais: int

        frais_notaire_pct: float = 8.0
        montant_emprunt: float = field(init=False)
        frais_notaire: float = field(init=False)

        def __post_init__(self):
            self.frais_notaire = self.prix_bien * self.frais_notaire_pct / 100
            total_a_financer = (
                self.prix_bien + self.frais_notaire + self.frais_agence +
                self.frais_dossier + self.frais_garantie + self.frais_tiers + self.montant_travaux
            )
            self.montant_emprunt = max(0, total_a_financer - self.apport)

        def mensualite_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            for _ in range(self.differe_mois):
                capital += capital * tm
            n = self.duree_annees * 12 - self.differe_mois
            if n <= 0:
                raise ValueError("Durée ou différé incohérents")
            m_hors_assurance = capital * tm / (1 - (1 + tm) ** -n)
            m_assurance = self.montant_emprunt * ta
            return m_hors_assurance + m_assurance

        def tableau_amortissement_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            capital_rest = capital
            mensualite_hors_assurance = None
            rows = []
            for mois in range(1, self.duree_annees * 12 + 1):
                if mois <= self.differe_mois:
                    interets = capital_rest * tm
                    principal = 0
                    capital_rest += interets
                else:
                    if mensualite_hors_assurance is None:
                        mensualite_hors_assurance = self.mensualite_emprunt() - capital * ta
                    interets = capital_rest * tm
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
                    'Assurance': capital * ta,
                    'Capital restant dû': capital_rest
                })
            return pd.DataFrame(rows)

        def amortissements(self):
            valeur_bati = self.prix_bien * (1 - self.part_terrain / 100)
            rows = []
            for annee in range(1, 11):
                bati = valeur_bati / self.duree_amort_bati if annee <= self.duree_amort_bati else 0
                mobilier = self.mobilier / self.duree_amort_mobilier if annee <= self.duree_amort_mobilier else 0
                travaux = self.montant_travaux / self.duree_amort_travaux if annee <= self.duree_amort_travaux else 0
                frais = (self.frais_dossier + self.frais_agence + self.frais_garantie + self.frais_tiers) / self.duree_amort_frais if annee <= self.duree_amort_frais else 0
                total = bati + mobilier + travaux + frais
                rows.append({
                    'Année': annee,
                    'Amortissement Bâti': bati,
                    'Amortissement Mobilier': mobilier,
                    'Amortissement Travaux': travaux,
                    'Amortissement Frais': frais,
                    'Total Amortissement': total
                })
            return pd.DataFrame(rows)

        def resultat_fiscal_annuel(self):
            amort = self.amortissements().set_index('Année')['Total Amortissement'].to_dict()
            amort_table = self.tableau_amortissement_emprunt()
            interets = amort_table.groupby('Année')['Intérêts'].sum().to_dict()
            assurances = amort_table.groupby('Année')['Assurance'].sum().to_dict()

            mensualite = self.mensualite_emprunt()
            results = []
            deficit_reportable = 0.0

            for annee in range(1, 11):
                revenus = self.loyer_mensuel_hc * (12 - self.vacance_locative_mois)
                charges_reelles = (
                    self.charges_copro + self.assurance + self.assurance_gli +
                    self.taxe_fonciere + self.frais_entretien + self.frais_compta +
                    self.frais_bancaires + self.gestion_locative
                )
                charges_recup = self.charges_copro * 0.8
                interet = interets.get(annee, 0.0)
                assurance = assurances.get(annee, 0.0)
                dotation = amort.get(annee, 0.0)

                resultat_brut = revenus - charges_reelles - interet - assurance - dotation
                resultat_net = resultat_brut + deficit_reportable

                if resultat_net < 0:
                    ir = 0.0
                    ssi = 0.0
                    deficit_reportable = resultat_net
                else:
                    ir = resultat_net * (self.tmi / 100)
                    ssi = resultat_net * 0.40
                    deficit_reportable = 0.0

                cashflow_mensuel = (revenus - charges_reelles - ir - ssi - mensualite * 12 + charges_recup) / 12

                results.append({
                    'Année': annee,
                    'Revenus': revenus,
                    'Charges réelles': charges_reelles,
                    'Charges récupérables': charges_recup,
                    'Intérêts': interet,
                    'Assurance': assurance,
                    'Amortissements': dotation,
                    'Résultat fiscal brut': resultat_brut,
                    'Résultat fiscal net': resultat_net,
                    'Déficit reportable': deficit_reportable if deficit_reportable < 0 else 0.0,
                    'IR (TMI)': round(ir, 2),
                    'Cotisations sociales (SSI)': round(ssi, 2),
                    'Cashflow mensuel (€)': round(cashflow_mensuel, 2)
                })

            return pd.DataFrame(results)

    # Interface utilisateur LMP réel
    st.title("Simulateur LMP réel")

    prix_bien = st.number_input("Prix du bien (€)", value=0)
    part_terrain = st.slider("Part du terrain (%)", 0, 50, 10)
    apport = st.number_input("Apport (€)", value=0)
    frais_dossier = st.number_input("Frais de dossier (€)", value=0)
    frais_agence = st.number_input("Frais d’agence (€)", value=0)
    montant_travaux = st.number_input("Montant des travaux (€)", value=0)
    frais_garantie = st.number_input("Frais de garantie (€)", value=0)
    frais_tiers = st.number_input("Frais de tiers (€)", value=0)
    mobilier = st.number_input("Mobilier (€)", value=0)

    duree_annees = st.slider("Durée du prêt (années)", 5, 30, 20)
    taux_interet = st.number_input("Taux d’intérêt (%)", value=3.0)
    taux_assurance = st.number_input("Taux assurance emprunteur (%)", value=0.3)
    differe_mois = st.slider("Différé (mois)", 0, 24, 0)

    charges_copro = st.number_input("Charges de copropriété (€)", value=0)
    assurance = st.number_input("Assurance propriétaire (€)", value=0)
    assurance_gli = st.number_input("Assurance GLI (€)", value=0)
    taxe_fonciere = st.number_input("Taxe foncière (€)", value=0)
    frais_entretien = st.number_input("Frais d’entretien (€)", value=0)
    frais_compta = st.number_input("Frais de comptabilité (€)", value=0)
    frais_bancaires = st.number_input("Frais bancaires (€)", value=0)
    gestion_locative = st.number_input("Frais de gestion locative (€)", value=0)

    loyer_mensuel_hc = st.number_input("Loyer mensuel HC (€)", value=1000)
    vacance_locative_mois = st.slider("Vacance locative (mois)", 0, 12, 0)
    tmi = st.slider("TMI (Tranche Marginale d’Imposition en %)", 0, 45, 30)

    duree_amort_bati = st.slider("Durée amortissement bâti (années)", 20, 50, 30)
    duree_amort_travaux = st.slider("Durée amortissement travaux (années)", 5, 20, 10)
    duree_amort_mobilier = st.slider("Durée amortissement mobilier (années)", 5, 15, 7)
    duree_amort_frais = st.slider("Durée amortissement frais (années)", 5, 15, 10)

    if st.button("Lancer la simulation LMP réel"):
        lmp = LMPReel(
            prix_bien, part_terrain, apport, frais_dossier, frais_agence, montant_travaux,
            frais_garantie, frais_tiers, mobilier,
            duree_annees, taux_interet, taux_assurance, differe_mois,
            charges_copro, assurance, assurance_gli, taxe_fonciere, frais_entretien,
            frais_compta, frais_bancaires, gestion_locative,
            loyer_mensuel_hc, vacance_locative_mois, tmi,
            duree_amort_bati, duree_amort_travaux, duree_amort_mobilier, duree_amort_frais
        )

        st.subheader("📊 Résultats LMP réel sur 10 ans")
        st.dataframe(lmp.resultat_fiscal_annuel())

        st.subheader("📉 Tableau d’amortissement de l’emprunt")
        st.dataframe(lmp.tableau_amortissement_emprunt())

        st.subheader("📑 Tableau des amortissements comptables")
        st.dataframe(lmp.amortissements()) 

elif regime == "SARL de famille":

    @dataclass
    class SARLDeFamille:
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
        assurance_gli: float
        taxe_fonciere: float
        frais_entretien: float
        frais_compta: float
        frais_bancaires: float
        gestion_locative: float
        loyer_mensuel_hc: float
        vacance_locative_mois: int
        tmi: float

        duree_amort_bati: int
        duree_amort_travaux: int
        duree_amort_mobilier: int
        duree_amort_frais: int

        frais_notaire_pct: float = 8.0
        montant_emprunt: float = field(init=False)
        frais_notaire: float = field(init=False)

        def __post_init__(self):
            self.frais_notaire = self.prix_bien * self.frais_notaire_pct / 100
            total_a_financer = (
                self.prix_bien + self.frais_notaire + self.frais_agence +
                self.frais_dossier + self.frais_garantie + self.frais_tiers + self.montant_travaux
            )
            self.montant_emprunt = max(0, total_a_financer - self.apport)

        def mensualite_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            for _ in range(self.differe_mois):
                capital += capital * tm
            n = self.duree_annees * 12 - self.differe_mois
            if n <= 0:
                raise ValueError("Durée ou différé incohérents")
            m_hors_assurance = capital * tm / (1 - (1 + tm) ** -n)
            m_assurance = self.montant_emprunt * ta
            return m_hors_assurance + m_assurance

        def tableau_amortissement_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            capital_rest = capital
            mensualite_hors_assurance = None
            rows = []
            for mois in range(1, self.duree_annees * 12 + 1):
                if mois <= self.differe_mois:
                    interets = capital_rest * tm
                    principal = 0
                    capital_rest += interets
                else:
                    if mensualite_hors_assurance is None:
                        mensualite_hors_assurance = self.mensualite_emprunt() - capital * ta
                    interets = capital_rest * tm
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
                    'Assurance': capital * ta,
                    'Capital restant dû': capital_rest
                })
            return pd.DataFrame(rows)

        def amortissements(self):
            valeur_bati = self.prix_bien * (1 - self.part_terrain / 100)
            rows = []
            for annee in range(1, 11):
                bati = valeur_bati / self.duree_amort_bati if annee <= self.duree_amort_bati else 0
                mobilier = self.mobilier / self.duree_amort_mobilier if annee <= self.duree_amort_mobilier else 0
                travaux = self.montant_travaux / self.duree_amort_travaux if annee <= self.duree_amort_travaux else 0
                frais = (self.frais_dossier + self.frais_agence + self.frais_garantie + self.frais_tiers) / self.duree_amort_frais if annee <= self.duree_amort_frais else 0
                total = bati + mobilier + travaux + frais
                rows.append({
                    'Année': annee,
                    'Amortissement Bâti': bati,
                    'Amortissement Mobilier': mobilier,
                    'Amortissement Travaux': travaux,
                    'Amortissement Frais': frais,
                    'Total Amortissement': total
                })
            return pd.DataFrame(rows)

        def resultat_fiscal_annuel(self):
            amort = self.amortissements().set_index('Année')['Total Amortissement'].to_dict()
            amort_table = self.tableau_amortissement_emprunt()
            interets = amort_table.groupby('Année')['Intérêts'].sum().to_dict()
            assurances = amort_table.groupby('Année')['Assurance'].sum().to_dict()

            mensualite = self.mensualite_emprunt()
            results = []
            deficit_reportable = 0.0

            for annee in range(1, 11):
                revenus = self.loyer_mensuel_hc * (12 - self.vacance_locative_mois)
                charges_reelles = (
                    self.charges_copro + self.assurance + self.assurance_gli +
                    self.taxe_fonciere + self.frais_entretien + self.frais_compta +
                    self.frais_bancaires + self.gestion_locative
                )
                charges_recup = self.charges_copro * 0.8
                interet = interets.get(annee, 0.0)
                assurance = assurances.get(annee, 0.0)
                dotation = amort.get(annee, 0.0)

                resultat_brut = revenus - charges_reelles - interet - assurance - dotation
                resultat_net = resultat_brut + deficit_reportable

                if resultat_net < 0:
                    ir = 0.0
                    deficit_reportable = resultat_net
                else:
                    ir = resultat_net * (self.tmi / 100)
                    deficit_reportable = 0.0

                cashflow_mensuel = (revenus - charges_reelles - ir - mensualite * 12 + charges_recup) / 12

                results.append({
                    'Année': annee,
                    'Revenus': revenus,
                    'Charges réelles': charges_reelles,
                    'Charges récupérables': charges_recup,
                    'Intérêts': interet,
                    'Assurance': assurance,
                    'Amortissements': dotation,
                    'Résultat fiscal brut': resultat_brut,
                    'Résultat fiscal net': resultat_net,
                    'Déficit reportable': deficit_reportable if deficit_reportable < 0 else 0.0,
                    'IR (TMI)': round(ir, 2),
                    'Cashflow mensuel (€)': round(cashflow_mensuel, 2)
                })

            return pd.DataFrame(results) 
                
    # Interface utilisateur SARL de famille
    st.title("Simulation SARL de Famille (IR)")

    prix_bien = st.number_input("Prix du bien (€)", value=0)
    part_terrain = st.number_input("Part du terrain (%)", value=10)
    apport = st.number_input("Apport (€)", value=0)
    frais_dossier = st.number_input("Frais de dossier (€)", value=0)
    frais_agence = st.number_input("Frais d’agence (€)", value=0)
    montant_travaux = st.number_input("Montant des travaux (€)", value=0)
    frais_garantie = st.number_input("Frais de garantie (€)", value=0)
    frais_tiers = st.number_input("Frais de tiers (€)", value=0)
    mobilier = st.number_input("Valeur du mobilier (€)", value=0)

    duree_annees = st.slider("Durée de l’emprunt (années)", 5, 30, 20)
    taux_interet = st.number_input("Taux d’intérêt (%)", value=3.0)
    taux_assurance = st.number_input("Taux assurance emprunteur (%)", value=0.3)
    differe_mois = st.slider("Différé de remboursement (mois)", 0, 24, 0)

    charges_copro = st.number_input("Charges de copropriété (€)", value=0)
    assurance = st.number_input("Assurance propriétaire (€)", value=0)
    assurance_gli = st.number_input("Assurance GLI (€)", value=0)
    taxe_fonciere = st.number_input("Taxe foncière (€)", value=0)
    frais_entretien = st.number_input("Frais d’entretien (€)", value=0)
    frais_compta = st.number_input("Frais de comptabilité (€)", value=0)
    frais_bancaires = st.number_input("Frais bancaires (€)", value=0)
    gestion_locative = st.number_input("Frais de gestion locative (€)", value=0)
    loyer_mensuel_hc = st.number_input("Loyer mensuel HC (€)", value=0)
    vacance_locative_mois = st.slider("Vacance locative (mois)", 0, 12, 0)
    tmi = st.slider("TMI (%)", 0, 45, 30)

    duree_amort_bati = st.slider("Durée amort. bâti (ans)", 20, 50, 30)
    duree_amort_travaux = st.slider("Durée amort. travaux (ans)", 5, 20, 10)
    duree_amort_mobilier = st.slider("Durée amort. mobilier (ans)", 5, 10, 7)
    duree_amort_frais = st.slider("Durée amort. frais (ans)", 5, 10, 5)

    if st.button("Lancer la simulation SARL de Famille"):
        sarl = SARLDeFamille(
            prix_bien, part_terrain, apport, frais_dossier, frais_agence,
            montant_travaux, frais_garantie, frais_tiers, mobilier,
            duree_annees, taux_interet, taux_assurance, differe_mois,
            charges_copro, assurance, assurance_gli, taxe_fonciere, frais_entretien,
            frais_compta, frais_bancaires, gestion_locative,
            loyer_mensuel_hc, vacance_locative_mois, tmi,
            duree_amort_bati, duree_amort_travaux, duree_amort_mobilier, duree_amort_frais
        )

        st.subheader("📈 Résultats fiscaux SARL de Famille sur 10 ans")
        st.dataframe(sarl.resultat_fiscal_annuel())

        st.subheader("📊 Tableau d’amortissement de l’emprunt")
        st.dataframe(sarl.tableau_amortissement_emprunt())

elif regime == "Réel foncier":

    @dataclass
    class ReelFoncier:
        prix_bien: float
        apport: float
        frais_dossier: float
        frais_agence: float
        montant_travaux: float
        frais_garantie: float
        frais_tiers: float

        duree_annees: int
        taux_interet: float
        taux_assurance: float
        differe_mois: int

        charges_copro: float
        taxe_fonciere: float
        frais_entretien: float
        frais_compta: float
        frais_bancaires: float
        gestion_locative: float
        loyer_mensuel_hc: float
        vacance_locative_mois: int
        tmi: float

        frais_notaire_pct: float = 8.0
        montant_emprunt: float = field(init=False)
        frais_notaire: float = field(init=False)

        def __post_init__(self):
            self.frais_notaire = self.prix_bien * self.frais_notaire_pct / 100
            total = self.prix_bien + self.frais_notaire + self.frais_agence + self.frais_dossier + self.frais_garantie + self.frais_tiers + self.montant_travaux
            self.montant_emprunt = max(0, total - self.apport)

        def mensualite_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            for _ in range(self.differe_mois):
                capital += capital * tm
            n = self.duree_annees * 12 - self.differe_mois
            m_hors_assurance = capital * tm / (1 - (1 + tm) ** -n)
            m_assurance = self.montant_emprunt * ta
            return m_hors_assurance + m_assurance

        def tableau_amortissement_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            capital_rest = capital
            mensualite_hors_assurance = None
            rows = []
            for mois in range(1, self.duree_annees * 12 + 1):
                if mois <= self.differe_mois:
                    interets = capital_rest * tm
                    principal = 0
                    capital_rest += interets
                else:
                    if mensualite_hors_assurance is None:
                        mensualite_hors_assurance = self.mensualite_emprunt() - capital * ta
                    interets = capital_rest * tm
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
                    'Assurance': capital * ta,
                    'Capital restant dû': capital_rest
                })
            return pd.DataFrame(rows)

        def resultat_fiscal_annuel(self):
            amort_emprunt = self.tableau_amortissement_emprunt()
            interets = amort_emprunt.groupby('Année')['Intérêts'].sum().to_dict()
            assurances = amort_emprunt.groupby('Année')['Assurance'].sum().to_dict()
            mensualite = self.mensualite_emprunt()

            results = []
            deficit_reportable_foncier = 0.0

            for annee in range(1, 11):
                revenus = self.loyer_mensuel_hc * (12 - self.vacance_locative_mois)
                charges = (
                    self.charges_copro + self.taxe_fonciere + self.frais_entretien +
                    self.frais_compta + self.frais_bancaires + self.gestion_locative
                )
                interet = interets.get(annee, 0.0)
                assurance = assurances.get(annee, 0.0)
                charges_recup = self.charges_copro * 0.8

                resultat_foncier = revenus - charges - interet - assurance
                resultat_net = resultat_foncier + deficit_reportable_foncier

                if resultat_net < 0:
                    imputable_rg = max(resultat_net, -10700)
                    reportable = resultat_net - imputable_rg
                    ir = 0.0
                    deficit_reportable_foncier = reportable
                else:
                    ir = resultat_net * (self.tmi / 100)
                    imputable_rg = 0.0
                    deficit_reportable_foncier = 0.0

                cashflow = (revenus - charges - interet - assurance - ir - mensualite * 12 + charges_recup) / 12

                results.append({
                    'Année': annee,
                    'Revenus': revenus,
                    'Charges réelles': charges,
                    'Charges récupérables': charges_recup,
                    'Intérêts': interet,
                    'Assurance': assurance,
                    'Résultat foncier': resultat_foncier,
                    'Résultat fiscal net': resultat_net,
                    'Déficit imputé sur revenu global': -imputable_rg if imputable_rg < 0 else 0.0,
                    'Déficit reportable foncier': deficit_reportable_foncier if deficit_reportable_foncier < 0 else 0.0,
                    'Impôt (IR)': round(ir, 2),
                    'Cashflow mensuel (€)': round(cashflow, 2) / 12
                })

            return pd.DataFrame(results) 
    
    # Interface utilisateur – Régime Réel Foncier
    st.title("Simulateur Réel Foncier")

    prix_bien = st.number_input("Prix du bien (€)", value=0)
    apport = st.number_input("Apport (€)", value=0)
    frais_dossier = st.number_input("Frais de dossier (€)", value=0)
    frais_agence = st.number_input("Frais d’agence (€)", value=0)
    montant_travaux = st.number_input("Montant des travaux (€)", value=0)
    frais_garantie = st.number_input("Frais de garantie (€)", value=0)
    frais_tiers = st.number_input("Frais de tiers (€)", value=0)

    duree_annees = st.slider("Durée du prêt (années)", 5, 30, 20)
    taux_interet = st.number_input("Taux d’intérêt (%)", value=3.0)
    taux_assurance = st.number_input("Taux d’assurance emprunteur (%)", value=0.3)
    differe_mois = st.slider("Différé (mois)", 0, 24, 0)

    charges_copro = st.number_input("Charges de copropriété (€)", value=0)
    taxe_fonciere = st.number_input("Taxe foncière (€)", value=0)
    frais_entretien = st.number_input("Frais d’entretien (€)", value=0)
    frais_compta = st.number_input("Frais de comptabilité (€)", value=0)
    frais_bancaires = st.number_input("Frais bancaires (€)", value=0)
    gestion_locative = st.number_input("Frais de gestion locative (€)", value=0)

    loyer_mensuel_hc = st.number_input("Loyer mensuel HC (€)", value=850)
    vacance_locative_mois = st.slider("Vacance locative (mois)", 0, 12, 0)
    tmi = st.slider("TMI (Tranche Marginale d’Imposition en %)", 0, 45, 30)

    if st.button("Lancer la simulation Réel Foncier"):
        reel = ReelFoncier(
            prix_bien, apport, frais_dossier, frais_agence, montant_travaux,
            frais_garantie, frais_tiers,
            duree_annees, taux_interet, taux_assurance, differe_mois,
            charges_copro, taxe_fonciere, frais_entretien, frais_compta,
            frais_bancaires, gestion_locative,
            loyer_mensuel_hc, vacance_locative_mois, tmi
        )

        st.subheader("📆 Résultats régime réel foncier sur 10 ans")
        st.dataframe(reel.resultat_fiscal_annuel())
        st.subheader("📉 Tableau d’amortissement de l’emprunt")
        st.dataframe(reel.tableau_amortissement_emprunt())
        
elif regime == "Holding à l'IS":

    # --------------------------------------------------------------------------------
    # CLASSE HOLDING À L'IS
    # --------------------------------------------------------------------------------
    @dataclass
    class HoldingIS:
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
        assurance_gli: float
        taxe_fonciere: float
        frais_entretien: float
        frais_compta: float
        frais_bancaires: float
        gestion_locative: float
        loyer_mensuel_hc: float
        vacance_locative_mois: int

        duree_amort_bati: int
        duree_amort_travaux: int
        duree_amort_mobilier: int
        duree_amort_frais: int

        frais_notaire_pct: float = 8.0
        montant_emprunt: float = field(init=False)
        frais_notaire: float = field(init=False)

        def __post_init__(self):
            self.frais_notaire = self.prix_bien * self.frais_notaire_pct / 100
            total_a_financer = (
                self.prix_bien + self.frais_notaire + self.frais_agence +
                self.frais_dossier + self.frais_garantie + self.frais_tiers + self.montant_travaux
            )
            self.montant_emprunt = max(0, total_a_financer - self.apport)

        def mensualite_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            for _ in range(self.differe_mois):
                capital += capital * tm
            n = self.duree_annees * 12 - self.differe_mois
            m_hors_assurance = capital * tm / (1 - (1 + tm) ** -n)
            m_assurance = self.montant_emprunt * ta
            return m_hors_assurance + m_assurance

        def tableau_amortissement_emprunt(self):
            tm = self.taux_interet / 100 / 12
            ta = self.taux_assurance / 100 / 12
            capital = self.montant_emprunt
            capital_rest = capital
            mensualite_hors_assurance = None
            rows = []
            for mois in range(1, self.duree_annees * 12 + 1):
                if mois <= self.differe_mois:
                    interets = capital_rest * tm
                    principal = 0
                    capital_rest += interets
                else:
                    if mensualite_hors_assurance is None:
                        mensualite_hors_assurance = self.mensualite_emprunt() - capital * ta
                    interets = capital_rest * tm
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
                    'Assurance': capital * ta,
                    'Capital restant dû': capital_rest
                })
            return pd.DataFrame(rows)

        def amortissements(self):
            valeur_bati = self.prix_bien * (1 - self.part_terrain / 100)
            rows = []
            for annee in range(1, 11):
                bati = valeur_bati / self.duree_amort_bati if annee <= self.duree_amort_bati else 0
                mobilier = self.mobilier / self.duree_amort_mobilier if annee <= self.duree_amort_mobilier else 0
                travaux = self.montant_travaux / self.duree_amort_travaux if annee <= self.duree_amort_travaux else 0
                frais = (self.frais_dossier + self.frais_agence + self.frais_garantie + self.frais_tiers) / self.duree_amort_frais if annee <= self.duree_amort_frais else 0
                total = bati + mobilier + travaux + frais
                rows.append({
                    'Année': annee,
                    'Amortissement Bâti': bati,
                    'Amortissement Mobilier': mobilier,
                    'Amortissement Travaux': travaux,
                    'Amortissement Frais': frais,
                    'Total Amortissement': total
                })
            return pd.DataFrame(rows)

        def resultat_fiscal_annuel(self):
            amort = self.amortissements().set_index('Année')['Total Amortissement'].to_dict()
            amort_table = self.tableau_amortissement_emprunt()
            interets = amort_table.groupby('Année')['Intérêts'].sum().to_dict()
            assurances = amort_table.groupby('Année')['Assurance'].sum().to_dict()
            mensualite = self.mensualite_emprunt()
            results = []
            deficit_reportable = 0.0
            for annee in range(1, 11):
                revenus = self.loyer_mensuel_hc * (12 - self.vacance_locative_mois)
                charges_reelles = (
                    self.charges_copro + self.assurance + self.assurance_gli +
                    self.taxe_fonciere + self.frais_entretien + self.frais_compta +
                    self.frais_bancaires + self.gestion_locative
                )
                charges_recup = self.charges_copro * 0.8
                charges_fiscales = charges_reelles - charges_recup
                interet = interets.get(annee, 0.0)
                assurance = assurances.get(annee, 0.0)
                dotation = amort.get(annee, 0.0)
                resultat_brut = revenus - charges_fiscales - interet - assurance - dotation
                resultat_net = resultat_brut + deficit_reportable
                if resultat_net < 0:
                    is_impot = 0.0
                    deficit_reportable = resultat_net
                else:
                    if resultat_net <= 42500:
                        is_impot = resultat_net * 0.15
                    else:
                        is_impot = 42500 * 0.15 + (resultat_net - 42500) * 0.25
                    deficit_reportable = 0.0
                cashflow_mensuel = (revenus - charges_reelles - is_impot - mensualite * 12 + charges_recup) / 12
                results.append({
                    'Année': annee,
                    'Revenus': revenus,
                    'Charges réelles': charges_reelles,
                    'Charges récupérables': charges_recup,
                    'Intérêts': interet,
                    'Assurance': assurance,
                    'Amortissements': dotation,
                    'Résultat fiscal brut': resultat_brut,
                    'Résultat fiscal net': resultat_net,
                    'Déficit reportable': deficit_reportable if deficit_reportable < 0 else 0.0,
                    'IS': is_impot,
                    'Cashflow mensuel (€)': round(cashflow_mensuel, 2)
                })
            return pd.DataFrame(results)

    # Interface utilisateur Holding à l’IS
    st.title("Simulateur Holding à l’IS")

    prix_bien = st.number_input("Prix du bien (€)", value=0)
    part_terrain = st.slider("Part du terrain (%)", 0, 100, 15)
    apport = st.number_input("Apport (€)", value=0)
    frais_dossier = st.number_input("Frais de dossier (€)", value=0)
    frais_agence = st.number_input("Frais d’agence (€)", value=0)
    montant_travaux = st.number_input("Montant des travaux (€)", value=0)
    frais_garantie = st.number_input("Frais de garantie (€)", value=0)
    frais_tiers = st.number_input("Frais de tiers (€)", value=0)
    mobilier = st.number_input("Montant mobilier (€)", value=0)

    duree_annees = st.slider("Durée prêt (années)", 5, 30, 20)
    taux_interet = st.number_input("Taux d’intérêt (%)", value=3.0)
    taux_assurance = st.number_input("Taux assurance emprunteur (%)", value=0.3)
    differe_mois = st.slider("Différé (mois)", 0, 24, 0)

    charges_copro = st.number_input("Charges de copropriété (€)", value=0)
    assurance = st.number_input("Assurance PNO (€)", value=0)
    assurance_gli = st.number_input("Assurance GLI (€)", value=0)
    taxe_fonciere = st.number_input("Taxe foncière (€)", value=0)
    frais_entretien = st.number_input("Frais d'entretien (€)", value=0)
    frais_compta = st.number_input("Frais comptabilité (€)", value=0)
    frais_bancaires = st.number_input("Frais bancaires (€)", value=0)
    gestion_locative = st.number_input("Gestion locative (€)", value=0)

    loyer_mensuel_hc = st.number_input("Loyer mensuel HC (€)", value=0)
    vacance_locative_mois = st.slider("Vacance locative (mois)", 0, 12, 0)

    duree_amort_bati = st.slider("Amortissement bâti", 20, 50, 30)
    duree_amort_travaux = st.slider("Amortissement travaux", 5, 20, 10)
    duree_amort_mobilier = st.slider("Amortissement mobilier", 5, 15, 7)
    duree_amort_frais = st.slider("Amortissement frais annexes", 3, 10, 5)

    if st.button("Lancer la simulation Holding à l’IS"):
        hold = HoldingIS(
            prix_bien, part_terrain, apport, frais_dossier, frais_agence, montant_travaux,
            frais_garantie, frais_tiers, mobilier,
            duree_annees, taux_interet, taux_assurance, differe_mois,
            charges_copro, assurance, assurance_gli, taxe_fonciere,
            frais_entretien, frais_compta, frais_bancaires, gestion_locative,
            loyer_mensuel_hc, vacance_locative_mois,
            duree_amort_bati, duree_amort_travaux, duree_amort_mobilier, duree_amort_frais
        )
        st.subheader("📊 Résultats sur 10 ans")
        st.dataframe(hold.resultat_fiscal_annuel())
        st.subheader("📉 Tableau d’amortissement de l’emprunt")
        st.dataframe(hold.tableau_amortissement_emprunt())
        st.subheader("📑 Amortissements comptables")
        st.dataframe(hold.amortissements())






