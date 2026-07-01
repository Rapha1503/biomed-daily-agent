---
title: BioMed Daily Agent
colorFrom: green
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# BioMed Daily Agent

BioMed Daily Agent est une app Streamlit pour une étudiante ou un étudiant en sciences biomédicales. Elle récupère des articles PubMed récents, extrait les métadonnées importantes, produit des résumés pédagogiques, puis génère un journal d'apprentissage quotidien en Markdown.

> Cet outil sert uniquement à l'apprentissage biomédical et à la veille bibliographique. Il ne fournit ni avis médical, ni diagnostic.

## Fonctionnalités

- Choisir des thèmes : immunologie, oncologie, neurosciences, pharmacologie, microbiologie, génétique et santé publique.
- Récupérer les articles récents via l'API PubMed/Entrez.
- Extraire titre, auteurs, revue, date de publication, résumé, lien PubMed et mots-clés quand ils sont disponibles.
- Résumer chaque article avec :
  - résumé simple
  - résultat principal
  - pourquoi c'est important
  - notions biomédicales à connaître
  - limites
  - niveau de preuve
  - glossaire
- Enregistrer articles et résumés dans SQLite.
- Générer un journal biomédical quotidien en Markdown.
- Traduire les titres et résumés PubMed en français.
- Envoyer automatiquement une notification téléphone via ntfy après génération.
- Poser une question sur la veille du jour et ajouter une image de contexte.
- Préparer une automatisation quotidienne avec `daily_watch.py`.

## Project Structure

```text
.
├── biomed_daily_agent/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── journal.py
│   ├── models.py
│   ├── pubmed.py
│   └── summarizer.py
├── data/
│   └── .gitkeep
├── exports/
│   └── .gitkeep
├── streamlit_app.py
├── requirements.txt
└── README.md
```

## Installation

1. Créer et activer un environnement virtuel.

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Installer les dépendances.

```bash
pip install -r requirements.txt
```

3. Optionnel : créer un fichier `.env`.

```bash
ENTREZ_EMAIL=your.email@example.com
ENTREZ_API_KEY=optional_ncbi_api_key
LLM_API_KEY=optional_llm_key
NTFY_TOPIC=un-sujet-prive-et-difficile-a-deviner
NTFY_SERVER=https://ntfy.sh
NTFY_TOKEN=optional_private_server_token
```

NCBI recommande de fournir une adresse email pour Entrez. L'app fonctionne sans, mais `ENTREZ_EMAIL` est conseillé.

4. Lancer l'app.

```bash
streamlit run streamlit_app.py
```

## Notifications téléphone

Cette version utilise ntfy, une solution simple de notifications push.

1. Installer l'app ntfy sur le téléphone.
2. Choisir un sujet privé, par exemple `biomed-veille-prenom-2026`.
3. Dans l'app ntfy, s'abonner à ce sujet.
4. Dans BioMed Daily Agent, saisir le même sujet dans la barre latérale.
5. Après génération du journal, cliquer sur `Envoyer la notification maintenant`.

Pour une vraie notification automatique chaque jour, l'ordinateur ou le serveur qui héberge le projet doit être allumé et planifié. Le script suivant lance la veille, exporte le Markdown et envoie la notification :

```bash
.venv/bin/python daily_watch.py --articles-per-topic 3 --days-back 1 --notify
```

Exemple de planification avec cron, tous les jours à 8h :

```bash
0 8 * * * cd "/Users/elinor/Documents/agent veille biomed" && .venv/bin/python daily_watch.py --articles-per-topic 3 --days-back 1 --notify
```

## Version installable sur téléphone

Le projet contient aussi une version PWA, pensée pour mobile et installable comme icône.

Lancer la PWA en local :

```bash
.venv/bin/uvicorn pwa_app:app --host 0.0.0.0 --port 8787
```

Adresse locale :

```text
http://localhost:8787
```

Pour l'ajouter à l'écran d'accueil d'un iPhone, il faut que l'app soit accessible depuis l'iPhone avec une adresse réseau ou une adresse déployée en HTTPS. Ensuite :

1. Ouvrir l'adresse dans Safari sur iPhone.
2. Appuyer sur le bouton de partage.
3. Choisir `Ajouter à l'écran d'accueil`.
4. Valider le nom `BioMed Daily`.

En local, `localhost` désigne seulement l'appareil qui ouvre le lien. Pour tester depuis l'iPhone, il faudra utiliser l'adresse réseau du Mac ou déployer l'app en ligne.

## Notes sur les résumés

L'app minimale utilise des résumés déterministes pour fonctionner sans clé payante. Le module de résumé est structuré pour ajouter plus tard un fournisseur LLM tout en gardant le même schéma de sortie.

## Disclaimer

Cet outil sert uniquement à l'apprentissage biomédical et à la veille bibliographique. Il ne fournit ni avis médical, ni diagnostic.
