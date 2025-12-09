# backend/app/main.py

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from .rules import Rules
from .strategy_engine import generate_strategy
from .pdf_generator import generate_strategy_pdf


class StrategyRequest(BaseModel):
    """
    Modèle d'entrée pour la génération de stratégie.
    Tous les champs ont des valeurs par défaut cohérentes avec DEFAULT_RULES.
    """
    num_decks: int = 6
    csm: bool = False

    dealer_hits_soft_17: bool = False
    european_no_hole_card: bool = False

    allow_split_aces: bool = True
    allow_resplit_aces: bool = False
    allow_double_after_split: bool = True

    allow_surrender: bool = False
    surrender_allowed_vs_ace: bool = False

    one_card_only_after_split_aces: bool = True


def request_to_rules(req: StrategyRequest) -> Rules:
    """
    Conversion Pydantic -> dataclass Rules.
    """
    if req.num_decks <= 0:
        raise HTTPException(status_code=400, detail="num_decks doit être > 0")

    return Rules(
        num_decks=req.num_decks,
        csm=req.csm,
        dealer_hits_soft_17=req.dealer_hits_soft_17,
        european_no_hole_card=req.european_no_hole_card,
        allow_split_aces=req.allow_split_aces,
        allow_resplit_aces=req.allow_resplit_aces,
        allow_double_after_split=req.allow_double_after_split,
        allow_surrender=req.allow_surrender,
        surrender_allowed_vs_ace=req.surrender_allowed_vs_ace,
        one_card_only_after_split_aces=req.one_card_only_after_split_aces,
    )


app = FastAPI(
    title="Blackjack Strategy API",
    version="0.1.0",
)

# CORS pour le frontend Vite (localhost:5173)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """
    Endpoint simple de healthcheck.
    """
    return {"status": "ok"}


@app.post("/strategy")
def post_strategy(req: StrategyRequest):
    """
    Génère une stratégie JSON à partir des règles.
    """
    rules = request_to_rules(req)
    strategy = generate_strategy(rules)
    return strategy


@app.post("/strategy/pdf")
def post_strategy_pdf(req: StrategyRequest):
    """
    Génère un PDF contenant les tableaux de stratégie.

    Réponse :
    - Content-Type: application/pdf
    - Content-Disposition: attachment; filename="blackjack_strategy.pdf"
    """
    rules = request_to_rules(req)
    strategy = generate_strategy(rules)

    pdf_bytes = generate_strategy_pdf(strategy)

    headers = {
        "Content-Disposition": 'attachment; filename="blackjack_strategy.pdf"'
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
