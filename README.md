# Générateur de basic strategy Blackjack

Application complète (backend FastAPI + frontend React) pour générer des tableaux de basic strategy de blackjack en fonction de règles configurables, les afficher dans une interface web et les télécharger en PDF.

## 1. Aperçu

Fonctionnalités principales :

- Configuration des règles de blackjack :
  - `num_decks`
  - `csm`
  - `dealer_hits_soft_17` (H17 / S17)
  - `european_no_hole_card` (ENHC / jeu US avec hole card + peek)
  - `allow_split_aces`, `allow_resplit_aces`
  - `allow_double_after_split` (DAS)
  - `allow_surrender`, `surrender_allowed_vs_ace`
  - `one_card_only_after_split_aces`
- Calcul de la basic strategy via un moteur Python (programmation dynamique, mémoïsation).
- Trois tableaux :
  - Hard totals
  - Soft totals
  - Paires
- Codes d’action :  
  `H` = Hit, `S` = Stand, `D` = Double, `P` = Split, `R` = Surrender
- Téléchargement d’un PDF généré côté backend à partir d’un template HTML.

---

## 2. Prérequis

- **Python** ≥ 3.10 (recommandé)
- **Node.js** ≥ 18
- **npm** ou **pnpm** / **yarn**
- **WeasyPrint** nécessite des dépendances système (à installer via le gestionnaire de paquets de votre OS), par exemple :
  - `libcairo`, `pango`, `gdk-pixbuf`, etc.
  - Voir la documentation officielle de WeasyPrint pour le détail selon votre plateforme.

---

## 3. Installation et lancement du backend

Depuis le dossier `backend` :

```bash
cd backend

# (Optionnel mais recommandé) créer un venv
python -m venv .venv
source .venv/bin/activate  # sous Windows: .venv\Scripts\activate

# Installer les dépendances Python
pip install -r requirements.txt
```

Lancer le serveur FastAPI (dev) :

uvicorn app.main:app --reload --port 8000


Endpoints principaux :

POST http://localhost:8000/strategy
Corps JSON : configuration des règles (voir ci-dessous).
Réponse JSON : stratégie avec rules, hard, soft, pairs.

POST http://localhost:8000/strategy/pdf
Corps JSON : même configuration.
Réponse : application/pdf + fichier binaire (avec header Content-Disposition pour le téléchargement).

Endpoint de healthcheck :

GET http://localhost:8000/health

Swagger / docs FastAPI :

http://localhost:8000/docs