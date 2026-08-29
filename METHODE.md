# MÉTHODE — détruire ses propres revendications en sept étapes

Appliquée entre le 19 et le 24 août 2026 à un projet auquel son auteur tenait.
Coût : six jours. Résultat : le projet n'avait pas de question propre.

Rien ici n'est original en soi. Ce qui l'est peut-être, c'est de l'appliquer à
soi-même, dans cet ordre, **avant** l'expérimentation plutôt qu'après.

---

## 1. Écrire le système, jusqu'à ce qu'il tourne

Pas de maquette. Du code exécutable, des tests verts, une commande qui produit
un chiffre. Tant qu'un système ne tourne pas, on ne peut pas savoir ce qu'il
revendique réellement — les intentions sont toujours plus nobles que
l'implémentation.

## 2. L'attaquer soi-même, avant que quiconque d'autre le fasse

Écrire une suite adverse dont le but explicite est de casser son propre système.
Ici : dix attaques, six failles réelles trouvées dans le kernel — dont une qui
permettait de faire passer une croyance pour une preuve, et une qui laissait
contourner le seuil d'approbation humaine en rendant le coût non mesurable
(`NaN > seuil` vaut `False` en Python).

**Règle : les failles qu'on décide de ne pas corriger sont verrouillées par un
test**, pour qu'elles restent visibles au lieu de s'effacer.

## 3. Vérifier que le banc de test est seulement testable

Avant de mesurer quoi que ce soit, mesurer l'instrument. Deux contrôles suffisent
à disqualifier la plupart des bancs maison :

- **Ablation mot à mot.** Retirer chaque mot de l'énoncé, un par un. Si la
  décision bascule sur un seul mot, le test mesure la présence de ce mot.
  Ici : 13 cas sur 18.
- **Contrôle négatif par famille.** Au moins un cas où le comportement
  « naïf » est le bon. Sans ça, le banc récompense un système qui refuse tout.

## 4. Séparer ce qu'on donne au système de ce qu'il doit trouver

Le test le plus révélateur de l'étude : le moteur ne lisait jamais l'énoncé, il
lisait des drapeaux posés à la main par l'auteur du banc. En le forçant à
dériver ces drapeaux du texte, le score est passé de **1.00 à 0.50**. Sur
énoncés réécrits, il répondait avec assurance dans un tiers des cas où il aurait
dû s'abstenir.

**Si votre système obtient un score parfait, cherchez ce que vous lui avez donné
sans le compter.**

## 5. Geler les seuils, et rendre leur modification détectable

Écrire dans un fichier versionné : hypothèse, seuils, règle de décision
go / simplifier / no-go. Calculer son empreinte cryptographique et l'inscrire
dans chaque rapport de campagne.

Modifier un seuil après avoir vu un résultat change l'empreinte et rend toutes
les campagnes antérieures non conformes. **La triche devient visible dans un
diff au lieu d'être invisible dans une intention.**

## 6. Chercher l'antériorité de chaque primitive, puis de chaque combinaison

Décomposer le système en primitives et chercher chacune séparément. Puis —
l'étape que presque personne ne fait — **chercher les combinaisons** : un
système peut être nouveau composant par composant et déjà décrit dans une
architecture voisine.

Construire une matrice : revendication · antériorité · similarité · preuve ·
différence réelle · statut. **Aucune case verte sans une recherche spécifique
qui a été menée et qui est citée.** Une case sans recherche est `UNKNOWN`, pas
« probablement nouveau ».

Cartographier ensuite l'espace de conception par axes, et regarder les
intersections vides plutôt que les points denses. Attention : une intersection
vide peut signifier « personne n'a essayé » — ou « personne n'en veut ». La
seconde est plus fréquente.

## 7. Nommer d'avance ce qui tuerait la dernière hypothèse, puis le chercher

Pour chaque revendication survivante, écrire les trois faits qui l'invalideraient,
classés par probabilité. Puis lancer la recherche qui correspond au premier.

Ici, elle a tué la dernière case en une requête.

---

## Le coût honnête de cette méthode

Elle détruit. Elle ne construit rien. Sur six jours, elle a produit zéro
fonctionnalité et un dépôt qui dit « ceci ne marche pas comme annoncé ».

Elle vaut son prix dans un seul cas : quand l'alternative est six mois de
construction sur une question déjà résolue par quelqu'un d'autre.

## Ce qu'elle ne remplace pas

- Une expérience réelle. Aucune étape ci-dessus ne dit si le système *marche*,
  seulement s'il *revendique* quelque chose de défendable.
- Un acheteur. Aucune étape ne dit si quelqu'un paierait.
- Un tiers. Toutes ces étapes ont été menées par l'auteur du système sur son
  propre travail. C'est mieux que rien, et c'est moins bon qu'une relecture
  extérieure.
