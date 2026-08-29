# Contribuer

## Règles anti-triche (non négociables)

1. Les métriques ne sont **jamais** modifiées après avoir vu un résultat.
2. L'ordre des règles du Behavior Engine est figé pendant une campagne.
3. Un résultat négatif se publie tel quel. Le supprimer est une faute.
4. Aucune revendication de nouveauté sans recherche d'antériorité écrite.
5. Un chiffre sans le JSON de campagne correspondant n'existe pas.

## Ajouter un cas au banc

Un cas doit être **observable** : aucun champ de `Situation` ne doit encoder la
réponse attendue. Chaque famille garde au moins un contrôle négatif (un cas où
`ANSWER` est la bonne réponse), sinon le banc récompense la sur-prudence.

## Ajouter un provider

Implémenter `ModelProvider` (`nom`, `complete`). Ne rien mettre d'autre dans le
kernel : le kernel doit rester exécutable hors ligne.
