from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI()


class SimulationInputs(BaseModel):
    regime: str
    prix_bien: float
    montant_apport: float
    frais_notaire: float
    frais_agence: float
    travaux: float
    mobilier: float
    frais_dossier: float
    caution: float
    frais_tiers: float
    charges_copro: float
    assurance_pno: float
    assurance_gli: float
    taxe_fonciere: float
    frais_entretien: float
    frais_gestion: float
    frais_bancaire: float
    comptabilite: float
    loyer_mensuel_hc: float
    loyer_mensuel_cc: float
    amortissement_bien_duree: Optional[int]
    amortissement_notaire_duree: Optional[int]
    amortissement_mobilier_duree: Optional[int]
    amortissement_travaux_duree: Optional[int]
    taux_interet: float
    taux_assurance: float
    revenu_annuel_global: float
    nombre_parts: float


def calcul_tmi(revenu_imposable, parts):
    tranches = [
        (0, 11294, 0.0),
        (11295, 28797, 0.11),
        (28798, 82341, 0.30),
        (82342, 177106, 0.41),
        (177107, float('inf'), 0.45),
    ]
    quotient = revenu_imposable / parts
    for bas, haut, taux in tranches:
        if bas <= quotient <= haut:
            return taux
    return 0.30


def calcul_impot_ir(revenu_foncier_net, inputs: SimulationInputs):
    revenu_total = inputs.revenu_annuel_global + revenu_foncier_net
    tmi = calcul_tmi(revenu_total, inputs.nombre_parts)
    prelevements_sociaux = 0.172
    if revenu_foncier_net < 0:
        return 0
    return revenu_foncier_net * (tmi + prelevements_sociaux)


def calcul_impot_is(benefice):
    if benefice <= 42500:
        return benefice * 0.15
    return 42500 * 0.15 + (benefice - 42500) * 0.25


def calcul_amortissement(prix, duree):
    return prix / duree if duree and duree > 0 else 0


def simulate(inputs: SimulationInputs):
    loyer_annuel = inputs.loyer_mensuel_hc * 12

    charges = sum([
        inputs.charges_copro,
        inputs.assurance_pno,
        inputs.assurance_gli,
        inputs.taxe_fonciere,
        inputs.frais_entretien,
        inputs.frais_gestion,
        inputs.frais_bancaire,
        inputs.comptabilite
    ])

    charges_annuelles = charges
    interets_emprunt = (inputs.prix_bien - inputs.montant_apport) * inputs.taux_interet
    assurance_credit = (inputs.prix_bien - inputs.montant_apport) * inputs.taux_assurance

    total_amortissements = 0
    if inputs.regime in ["LMNP réel", "LMP réel", "SCI à l'IS", "SARL de famille", "Holding à l'IS"]:
        amort_bien = calcul_amortissement(inputs.prix_bien * 0.8, inputs.amortissement_bien_duree)
        amort_notaire = calcul_amortissement(inputs.frais_notaire, inputs.amortissement_notaire_duree)
        amort_mobilier = calcul_amortissement(inputs.mobilier, inputs.amortissement_mobilier_duree)
        amort_travaux = calcul_amortissement(inputs.travaux, inputs.amortissement_travaux_duree)
        total_amortissements = amort_bien + amort_notaire + amort_mobilier + amort_travaux

    revenu_net = loyer_annuel - charges_annuelles - interets_emprunt - assurance_credit

    if inputs.regime == "Micro BIC":
        revenu_imposable = loyer_annuel * 0.5
        impot = calcul_impot_ir(revenu_imposable, inputs)
        return {"impot": impot, "cashflow": revenu_net - impot}

    elif inputs.regime == "Micro foncier":
        revenu_imposable = loyer_annuel * 0.7
        impot = calcul_impot_ir(revenu_imposable, inputs)
        return {"impot": impot, "cashflow": revenu_net - impot}

    elif inputs.regime in ["LMNP réel", "LMP réel", "SARL de famille"]:
        revenu_net_bic = revenu_net - total_amortissements
        impot = 0 if revenu_net_bic < 0 else calcul_impot_ir(revenu_net_bic, inputs)
        return {"impot": impot, "cashflow": revenu_net - impot}

    elif inputs.regime in ["Location nue réel", "SCI à l'IR"]:
        revenu_foncier = revenu_net
        if revenu_foncier < -10700:
            revenu_foncier = -10700
        impot = calcul_impot_ir(revenu_foncier, inputs)
        return {"impot": impot, "cashflow": revenu_net - impot}

    elif inputs.regime in ["SCI à l'IS", "Holding à l'IS"]:
        benefice = revenu_net - total_amortissements
        impot = 0 if benefice < 0 else calcul_impot_is(benefice)
        return {"impot": impot, "cashflow": revenu_net - impot}

    else:
        raise ValueError("Régime inconnu")


@app.post("/simulate")
def simulate_endpoint(inputs: SimulationInputs):
    result = simulate(inputs)
    return result
