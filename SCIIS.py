from dataclasses import dataclass, field
import pandas as pd

@dataclass
class SCIaIS:
    # Données d'acquisition
    prix_bien: float
    part_terrain: float  # en %
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
    assurance: float
    taxe_fonciere: float
    frais_entretien: float
    frais_compta: float
    frais_bancaires: float
    gestion_locative: float = 0.0

    # Revenus
    loyer_mensuel_hc: float
    vacance_locative_mois: int

    # Amortissements
    duree_amort_bati: int = 30
    duree_amort_travaux: int = 10
    duree_amort_mobilier: int = 7
    duree_amort_frais: int = 5

    taux_is: float = 0.25  # taux d’IS

    montant_emprunt: float = field(init=False)

    def __post_init__(self):
        frais_notaire = self.prix_bien * self.frais_notaire_pct / 100
        total_a_financer = (
            self.prix_bien + frais_notaire +
            self.frais_agence + self.frais_dossier +
            self.frais_garantie + self.frais_tiers +
            self.montant_travaux
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

        for annee in range(1, 11):
            revenus = self.loyer_mensuel_hc * (12 - self.vacance_locative_mois)
            charges = (
                self.charges_copro + self.assurance + self.taxe_fonciere +
                self.frais_entretien + self.frais_compta + self.frais_bancaires +
                self.gestion_locative
            )
            interet = interets.get(annee, 0)
            dotation = amort.get(annee, 0)
            resultat_fiscal = revenus - charges - interet - dotation
            impot = max(0, resultat_fiscal * self.taux_is)
            cashflow = revenus - charges - mensualite * 12

            invest_initial = self.apport + max(0, self.montant_emprunt)
            rent_brute = revenus * 12 / invest_initial * 100
            rent_nette = (revenus - charges - impot) / invest_initial * 100

            resultats.append({
                'Année': annee,
                'Revenus nets': revenus,
                'Charges': charges,
                'Intérêts': interet,
                'Amortissements': dotation,
                'Résultat fiscal': resultat_fiscal,
                'IS': impot,
                'Cashflow annuel': cashflow,
                'Rentabilité brute (%)': rent_brute,
                'Rentabilité nette (%)': rent_nette
            })

        return pd.DataFrame(resultats)
