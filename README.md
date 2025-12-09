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

```bash
uvicorn app.main:app --reload --port 8000
```

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

---

## 4. Aperçu visuel (UI)

### Points clés UI
- Interface React moderne (Vite) avec tables colorées et légende.
- Formulaire de règles flexible (S17/H17, DAS, RSA, ENHC, decks, etc.).
- Aperçu instantané des décisions: Hit/Stand/Double/Split/Surrender.
- Export PDF haute qualité depuis le backend (template HTML).

### Badges

<p>
  <img alt="React" src="https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?logo=react&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" />
  <img alt="Tests" src="https://img.shields.io/badge/Tests-Pytest-6DB33F?logo=pytest&logoColor=white" />
  <img alt="License" src="https://img.shields.io/badge/Status-Project%20Lab-blue" />
  
</p>

---

## 5. Lancer le frontend

Depuis le dossier `frontend` :

```bash
cd frontend
npm install
npm run dev
```

Par défaut: http://localhost:5173 (Vite).

---

## 6. Essai rapide

- Démarrez le backend (`uvicorn app.main:app --reload --port 8000`).
- Démarrez le frontend (`npm run dev`).
- Configurez les règles dans l’UI et observez les tables.
- Exportez le PDF via le bouton dédié.

---

## 7. À propos

Ce projet démontre une architecture claire (moteur Python testé + UI moderne) et une valeur pratique: visualiser et exporter une basic strategy adaptée aux règles de casino.