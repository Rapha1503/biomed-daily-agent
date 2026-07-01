# Déploiement gratuit

Objectif : avoir BioMed Daily Agent accessible depuis ton iPhone partout, sans payer.

## Ce qui sera gratuit

- L'app installable : Hugging Face Spaces gratuit.
- Les notifications : ntfy gratuit.
- La veille quotidienne automatique : GitHub Actions gratuit, avec limites raisonnables.

## Étape 1 : mettre l'app en ligne sur Hugging Face Spaces

1. Crée un compte gratuit sur Hugging Face.
2. Crée un nouveau Space.
3. Choisis :
   - SDK : Docker
   - Visibility : Public ou Private selon ton choix
4. Envoie le contenu du projet dans le Space.
5. Hugging Face construit l'app avec le `Dockerfile`.
6. Tu obtiens une adresse en `https://...hf.space`.

Sur iPhone :

1. Ouvre l'adresse `https://...hf.space` dans Safari.
2. Appuie sur Partager.
3. Choisis `Ajouter à l'écran d'accueil`.
4. Valide le nom `BioMed Daily`.

## Étape 2 : notifications ntfy gratuites

1. Installe ntfy sur iPhone.
2. Abonne-toi à un sujet secret, par exemple `biomed-elinor-veille-2026`.
3. Dans l'app, mets exactement ce même sujet.
4. Clique sur `Tester ntfy`.

## Étape 3 : veille quotidienne automatique gratuite

Le fichier `.github/workflows/daily-watch.yml` est prêt.

Dans GitHub, ajoute au minimum ce secret :

```text
NTFY_TOPIC=ton-sujet-ntfy-secret
```

Optionnel :

```text
NTFY_SERVER=https://ntfy.sh
ENTREZ_EMAIL=ton.email@example.com
ENTREZ_API_KEY=cle_ncbi_optionnelle
```

Le workflow tourne tous les jours à 7h UTC. Cela correspond à 8h ou 9h en France selon l'heure d'hiver/été.

Tu peux aussi le lancer à la main dans GitHub Actions avec `Run workflow`.

## Limites du gratuit

- Hugging Face Spaces gratuit peut être lent au réveil.
- GitHub Actions gratuit suffit pour un petit usage personnel, mais dépend des limites GitHub.
- La base SQLite du Space n'est pas un stockage fiable à long terme sur hébergement gratuit.
- Les notifications passent par ntfy, pas par une notification native iOS de l'app.

Malgré ces limites, cette architecture permet une app installable sur iPhone et une veille quotidienne sans abonnement payant.
