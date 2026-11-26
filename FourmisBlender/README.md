# Fourmis — éditeur 2D en Java, affichage 3D dans Blender

Toute la simulation (carte, règles, déplacements des fourmis) est en **Java**.
Blender ne fait qu'**afficher** ce que Java lui envoie, en 3D style dessin animé.

```
JavaFX (éditeur 2D + simulation)  --TCP 127.0.0.1:9877, JSON-->  Blender (fourmis_blender.py)
```

## Lancer

1. **Blender** (4.2 ou plus) : onglet *Scripting* > *Open* > `blender/fourmis_blender.py` > *Run Script* (`Alt+P`).
   Le script crée sa propre scène `Fourmis_Simulation`, vos autres scènes ne sont pas touchées.
2. **Java** : dans ce dossier, `mvn clean javafx:run`.
3. Dessinez la carte (ou *Carte d'exemple*), placez un **Spawn**, puis **Lancer la simulation**.
   Le terrain 3D apparaît dans Blender et les fourmis sortent du nid.

Sans Blender, la simulation tourne quand même et s'affiche sur la grille 2D.

## Blocs

| Bloc | Praticable |
|---|---|
| Chemin | oui |
| Spawn (nid) | oui — un seul, le premier posé est gardé |
| Caillou, Herbe, Fleur, Flaque d'eau, Souche | non |
| Case vide (trou) | non |

## Organisation

| Fichier | Rôle |
|---|---|
| `model/Carte.java` | la carte : `HashMap<Position, TypeBloc>`, règle du spawn unique, voisins praticables |
| `model/TypeBloc.java` | les 7 types de blocs |
| `simulation/Simulation.java` | un pas = chaque fourmi va sur une case voisine praticable au hasard (évite le demi-tour, un peu d'inertie) |
| `blender/Protocole.java` | messages JSON (`carte`, `fourmis`, `stop`) |
| `blender/BlenderClient.java` | connexion TCP, envois sur un thread à part |
| `ui/EditeurView.java` | grille 20x20, palette, boucle de simulation (`Timeline`) |
| `blender/fourmis_blender.py` | serveur dans Blender : construit le terrain, anime les fourmis entre deux pas |
