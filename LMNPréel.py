from dataclasses import dataclass, field
import numpy as np
import pandas as pd

@dataclass
class LMNPReel:
    # Données achat
    prix_bien: float
    part_terrain: float  # en %, ex: 15 pour 15%
    apport: float
    frais_dossier: float
    frais_agence: float
    montant_travaux: float
    frais_garantie: float
    frais_tiers: float
    mobilier: float
    frais_notaire_pct: float = 8.0  # en % du prix du bien

    # Emprunt
    duree_annees: int
    taux_interet: float  # annuel en %
    taux_assurance: float  # annuel en %
    differe_mois: int  # 0 à 24

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
    tmi: float  # tranche marginale d’imposition
    duree_amort_bati: int = 30
    duree_amort_mobilier: int = 7

    # Internes
    montant_emprunt: float = field(init=False)
    deficits_reportables: list = field(default_factory=lambda: [0] * 10)

    def __post_init__(self):
        frais_notaire = self.prix_bien * self.frais_notaire_pct / 100
        total_frais = (self.prix_bien + frais_notaire + self.frais_agence +
                       self.frais_dossier + self.montant_travaux +
                       self.frais_garantie + self.frais_tiers)
        self.montant_emprunt = max(0, total_frais - self.apport)

    def mensualite_emprunt(self):
        taux_mensuel = self.taux_interet / 100 / 12
        taux_assurance_mens = self.taux_assurance / 100 / 12
        capital = self.montant_emprunt

        capital_differe = capital
        for _ in range(self.differe_mois):
            interets_intercalaires = capital_differe * taux_mensuel
            capital_differe += interets_intercalaires

        nb_mensualites = self.duree_annees * 12 - self.differe_mois
        if nb_mensualites <= 0:
            raise ValueError("Durée trop courte ou différé trop long")

        mensualite = (capital_differe * taux_mensuel) / (1 - (1 + taux_mensuel) ** -nb_mensualites)
        assurance_mens = capital * taux_assurance_mens
        return mensualite + assurance_mens

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
                    mensualite = self.mensualite_emprunt() - (capital * self.taux_assurance / 100 / 12)
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

            charges = (self.charges_copro + self.assurance_habitation + self.assurance_gli +
                       self.taxe_fonciere + self.frais_entretien + self.frais_compta +
                       self.frais_bancaires + self.gestion_locative + self.taxe_habitation)

            interets = interets_annuels.get(annee, 0)
            amort = amortissement_dict.get(annee, 0)

            resultat = revenus - charges - interets - amort

            # Application des déficits
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
            cashflow = revenus - charges - mensualite * 12
            investissement_initial = self.apport + max(0, self.montant_emprunt)

            rent_brute = (self.loyer_mensuel_hc * 12) / investissement_initial * 100
            rent_nette = (revenus - charges - impot) / investissement_initial * 100

            resultats.append({
                'Année': annee,
                'Revenus nets vacance': revenus,
                'Charges': charges,
                'Intérêts Emprunt': interets,
                'Amortissement': amort,
                'Résultat fiscal imposable': resultat_fiscal,
                'Impôt': impot,
                'Cashflow annuel': cashflow,
                'Rentabilité brute (%)': rent_brute,
                'Rentabilité nette (%)': rent_nette,
                'Déficits reportables': sum(deficits_reportables)
            })

        return pd.DataFrame(resultats)
