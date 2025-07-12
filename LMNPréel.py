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
    frais_notaire_pct: float = 8.0  # frais de notaire en % du prix du bien
    
    # Emprunt
    duree_annees: int
    taux_interet: float  # annuel en %
    taux_assurance: float  # annuel en %
    differé_mois: int  # 0 à 24 mois
    
    # Charges annuelles
    charges_copro: float
    assurance_habitation: float
    assurance_gli: float
    taxe_fonciere: float
    frais_entretien: float
    frais_compta: float
    frais_bancaires: float
    gestion_locative: float = 0.0  # optionnel
    taxe_habitation: float = 0.0  # optionnel
    
    # Revenus
    loyer_mensuel_hc: float
    vacance_locative_mois: int  # nombre de mois
    
    # Fiscalité
    tmi: float  # en %, 11,30,41,45
    
    # Variables internes (calcul automatique)
    montant_emprunt: float = field(init=False)
    
    # Déficits reportables
    deficits_reportables: list = field(default_factory=lambda: [0]*10)
    
    def __post_init__(self):
        # Calcul frais notaire
        frais_notaire = self.prix_bien * self.frais_notaire_pct / 100
        
        # Montant emprunt = prix + frais - apport
        self.montant_emprunt = (self.prix_bien + frais_notaire + self.frais_agence +
                                self.frais_dossier + self.montant_travaux + 
                                self.frais_garantie + self.frais_tiers) - self.apport
        if self.montant_emprunt < 0:
            self.montant_emprunt = 0
        
    def mensualite_emprunt(self):
        """Calcul de la mensualité assurance comprise, gestion différé avec capitalisation des intérêts intercalaires"""
        # Taux mensuel
        taux_mensuel = self.taux_interet / 100 / 12
        taux_assurance_mens = self.taux_assurance / 100 / 12
        
        # Capital initial
        capital = self.montant_emprunt
        
        # Différé : capitalisation des intérêts intercalaires
        capital_differe = capital
        for _ in range(self.differé_mois):
            interets_intercalaires = capital_differe * taux_mensuel
            capital_differe += interets_intercalaires
        capital_apres_differe = capital_differe
        
        # Nombre de mensualités après différé
        nb_mensualites = self.duree_annees * 12 - self.differé_mois
        if nb_mensualites <= 0:
            raise ValueError("Durée trop courte ou différé trop long")
        
        # Calcul mensualité capital + intérêts après différé
        mensualite = (capital_apres_differe * taux_mensuel) / (1 - (1 + taux_mensuel) ** (-nb_mensualites))
        
        # Assurance mensuelle sur capital initial (souvent calculée sur capital initial, pas amorti)
        assurance_mens = self.montant_emprunt * taux_assurance_mens
        
        mensualite_totale = mensualite + assurance_mens
        return mensualite_totale
    
    def tableau_amortissement(self):
        """Calcule le tableau d'amortissement avec différé et capitalisation intérêts"""
        taux_mensuel = self.taux_interet / 100 / 12
        capital = self.montant_emprunt
        
        # Capitalisation intérêts pendant différé
        capital_differe = capital
        rows = []
        for mois in range(1, self.duree_annees * 12 + 1):
            if mois <= self.differé_mois:
                interets = capital_differe * taux_mensuel
                principal = 0
                capital_differe += interets
                capital_rest = capital_differe
            else:
                if mois == self.differé_mois + 1:
                    capital_rest = capital_differe
                    mensualite = self.mensualite_emprunt() - (self.montant_emprunt * self.taux_assurance / 100 / 12)
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
                'Principal remboursé': principal,
            })
        return pd.DataFrame(rows)
    
    def amortissements(self):
        """Calcul amortissement sur 10 ans"""
        # Valeur amortissable = prix bien hors terrain + mobilier
        valeur_bati = self.prix_bien * (1 - self.part_terrain / 100)
        amort_bati_annuel = valeur_bati / 30  # amorti sur 30 ans linéaire
        amort_mobilier_annuel = self.mobilier / 7  # amorti sur 7 ans linéaire
        
        amortissements = []
        for annee in range(1, 11):
            amortissements.append({
                'Année': annee,
                'Amortissement Bâti': amort_bati_annuel if annee <= 30 else 0,
                'Amortissement Mobilier': amort_mobilier_annuel if annee <= 7 else 0,
                'Total Amortissement': (amort_bati_annuel if annee <= 30 else 0) + (amort_mobilier_annuel if annee <= 7 else 0)
            })
        return pd.DataFrame(amortissements)
    
    def resultat_fiscal_annuel(self):
        """Calcul du résultat fiscal annuel en intégrant amortissements, charges, intérêts"""
        
        # Amortissements annuels
        amort = self.amortissements()
        
        # Tableau d'amortissement pour intérêts annuels (12 mois)
        amort_table = self.tableau_amortissement()
        amort_table['Année'] = ((amort_table['Mois'] - 1) // 12) + 1
        interets_annuels = amort_table.groupby('Année')['Intérêts'].sum()
        
        resultats = []
        deficits_reportables = self.deficits_reportables.copy()
        
        for annee in range(1, 11):
            # Revenus locatifs nets vacance
            revenus_annuels = self.loyer_mensuel_hc * (12 - self.vacance_locative_mois)
            
            # Charges annuelles totales
            charges_totales = (self.charges_copro + self.assurance_habitation + self.assurance_gli + 
                              self.taxe_fonciere + self.frais_entretien + self.frais_compta + self.frais_bancaires +
                              self.gestion_locative + self.taxe_habitation)
            
            # Intérêts d'emprunt sur l'année
            interets = interets_annuels.get(annee, 0)
            
            # Amortissements sur l'année
            amort_bati = amort.loc[annette - 1, 'Amortissement Bâti'] if annee <= 10 else 0
            amort_mob = amort.loc[annette - 1, 'Amortissement Mobilier'] if annee <= 10 else 0
            amort_total = amort_bati + amort_mob
            
            # Résultat avant report déficit
            resultat = revenus_annuels - charges_totales - interets - amort_total
            
            # Application des déficits reportables
            deficit_anterieur = deficits_reportables[annee-1]
            if resultat < 0:
                deficits_reportables[annee-1] = -resultat
                resultat = 0
            else:
                # On essaie de réduire le résultat avec le déficit reportable des années précédentes
                for i in range(annee - 1):
                    if deficits_reportables[i] > 0:
                        if resultat >= deficits_reportables[i]:
                            resultat -= deficits_reportables[i]
                            deficits_reportables[i] = 0
                        else:
                            deficits_reportables[i] -= resultat
                            resultat = 0
                            break
            
            # Calcul impôt
            impot = resultat * self.tmi / 100
            
            # Cashflow annuel (revenus - charges - mensualités *12)
            mensualite_tot = self.mensualite_emprunt()
            cashflow = revenus_annuels - charges_totales - mensualite_tot * 12
            
            # Rentabilité brute et nette (en %)
            investissement_initial = self.apport + (self.montant_emprunt if self.montant_emprunt > 0 else 0)
            rentabilite_brute = (self.loyer_mensuel_hc * 12) / investissement_initial * 100
            rentabilite_nette = (revenus_annuels - charges_totales - impot) / investissement_initial * 100
            
            resultats.append({
                'Année': annee,
                'Revenus nets vacance': revenus_annuels,
                'Charges': charges_totales,
                'Intérêts Emprunt': interets,
                'Amortissement': amort_total,
                'Résultat fiscal imposable': resultat,
                'Impôt': impot,
                'Cashflow annuel': cashflow,
                'Rentabilité brute (%)': rentabilite_brute,
                'Rentabilité nette (%)': rentabilite_nette,
                'Déficits reportables': sum(deficits_reportables),
            })
        
        return pd.DataFrame(resultats)

# Exemple d'utilisation
lmnp = LMNPReel(
    prix_bien=200000,
    part_terrain=15,
    apport=50000,
    frais_dossier=1000,
    frais_agence=3000,
    montant_travaux=15000,
    frais_garantie=800,
    frais_tiers=500,
    mobilier=10000,
    duree_annees=20,
    taux_interet=1.5,
    taux_assurance=0.3,
    differé_mois=12,
    charges_copro=1200,
    assurance_habitation=250,
    assurance_gli=400,
    taxe_fonciere=900,
    frais_entretien=500,
    frais_compta=600,
    frais_bancaires=150,
    gestion_locative=600,
    taxe_habitation=300,
    loyer_mensuel_hc=1000,
    vacance_locative_mois=1,
    tmi=30
)

print(lmnp.mensualite_emprunt())
print(lmnp.tableau_amortissement().head())
print(lmnp.amortissements())
print(lmnp.resultat_fiscal_annuel())
