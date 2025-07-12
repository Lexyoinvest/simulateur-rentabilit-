from dataclasses import dataclass
import numpy as np

@dataclass
class BienImmobilier:
    prix: float
    travaux: float
    frais_notaire: float
    frais_agence: float
    frais_dossier: float
    autres_frais: float
    quote_part_terrain: float = 0.1  # 10 % par défaut non amortissable

    def valeur_amortissable(self) -> float:
        total_hors_terrain = self.prix * (1 - self.quote_part_terrain)
        return total_hors_terrain + self.travaux

    def cout_total(self) -> float:
        return self.prix + self.travaux + self.frais_notaire + self.frais_agence + self.frais_dossier + self.autres_frais


@dataclass
class Emprunt:
    montant: float
    duree: int  # en années
    taux: float  # annuel en %
    assurance: float  # annuel en %
    mensualite: float = None  # peut être fixée à l'avance si connue
    differe: int = 0  # différé total ou partiel en années

    def calcul_mensualite(self):
        if self.mensualite:
            return self.mensualite
        taux_mensuel = self.taux / 100 / 12
        n = self.duree * 12
        return self.montant * taux_mensuel / (1 - (1 + taux_mensuel) ** -n)

    def interets_annuels(self, annee):
        if annee < self.differe:
            return self.montant * self.taux / 100  # différé total
        capital_restant = self.montant
        taux_mensuel = self.taux / 100 / 12
        mensualite = self.calcul_mensualite()
        for mois in range(12 * annee):
            interet = capital_restant * taux_mensuel
            capital_restant -= (mensualite - interet)
        return capital_restant * taux_mensuel * 12

    def assurance_annuelle(self):
        return self.montant * self.assurance / 100


@dataclass
class LoyersEtCharges:
    loyers_annuels: float
    charges_annuelles: float
    croissance_loyers: float = 0.0  # %
    croissance_charges: float = 0.0  # %

    def loyers(self, annee):
        return self.loyers_annuels * (1 + self.croissance_loyers / 100) ** annee

    def charges(self, annee):
        return self.charges_annuelles * (1 + self.croissance_charges / 100) ** annee


@dataclass
class Amortissements:
    bien: BienImmobilier
    duree_batiment: int = 40
    duree_travaux: int = 10

    def annuite_bien(self):
        return (self.bien.prix * (1 - self.bien.quote_part_terrain)) / self.duree_batiment

    def annuite_travaux(self):
        return self.bien.travaux / self.duree_travaux

    def total_annuite(self):
        return self.annuite_bien() + self.annuite_travaux()


class SCIIS:
    def __init__(self, bien: BienImmobilier, emprunt: Emprunt, flux: LoyersEtCharges):
        self.bien = bien
        self.emprunt = emprunt
        self.flux = flux
        self.amortissements = Amortissements(bien)

    def resultat_fiscal(self, annee):
        loyers = self.flux.loyers(annee)
        charges = self.flux.charges(annee)
        interets = self.emprunt.interets_annuels(annee)
        assurance = self.emprunt.assurance_annuelle()
        amort = self.amortissements.total_annuite()
        return loyers - charges - interets - assurance - amort

    def impot_is(self, resultat):
        if resultat <= 0:
            return 0
        if resultat <= 42500:
            return resultat * 0.15
        else:
            return 42500 * 0.15 + (resultat - 42500) * 0.25

    def projection_sur_10_ans(self):
        projection = []
        for annee in range(10):
            loyers = self.flux.loyers(annee)
            charges = self.flux.charges(annee)
            interets = self.emprunt.interets_annuels(annee)
            assurance = self.emprunt.assurance_annuelle()
            amort = self.amortissements.total_annuite()
            resultat = loyers - charges - interets - assurance - amort
            impot = self.impot_is(resultat)
            cashflow = loyers - charges - self.emprunt.calcul_mensualite() * 12 - assurance - impot
            projection.append({
                'annee': annee + 1,
                'loyers': loyers,
                'charges': charges,
                'interets': interets,
                'assurance': assurance,
                'amortissements': amort,
                'resultat_fiscal': resultat,
                'impot_is': impot,
                'cashflow_net_apres_is': cashflow
            })
        return projection
