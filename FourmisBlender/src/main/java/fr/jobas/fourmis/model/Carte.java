package fr.jobas.fourmis.model;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * La carte de l'étage 1 : une HashMap Position -> TypeBloc. Au départ, toutes les cases sont du
 * chemin ; effacer un bloc remet du chemin (il n'y a jamais de case vide). Il ne peut y avoir
 * qu'un seul spawn : le premier posé est gardé.
 */
public class Carte {

  private static final int[][] DIRECTIONS = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};

  private final int taille;
  private final Map<Position, TypeBloc> blocs = new HashMap<>();
  private Position spawn;

  public Carte(int taille) {
    this.taille = taille;
    remplirDeChemin();
  }

  private void remplirDeChemin() {
    for (int y = 0; y < taille; y++) {
      for (int x = 0; x < taille; x++) {
        blocs.put(new Position(x, y), TypeBloc.CHEMIN);
      }
    }
  }

  /** Copie indépendante (la simulation travaille sur une copie figée). */
  public Carte(Carte autre) {
    this.taille = autre.taille;
    this.blocs.putAll(autre.blocs);
    this.spawn = autre.spawn;
  }

  public int getTaille() {
    return taille;
  }

  public boolean dansLaGrille(Position p) {
    return p.getX() >= 0 && p.getY() >= 0 && p.getX() < taille && p.getY() < taille;
  }

  /**
   * Pose un bloc (remplace celui qui était là).
   *
   * @return null si c'est fait, sinon un message expliquant le refus.
   */
  public String placer(Position p, TypeBloc type) {
    if (!dansLaGrille(p)) {
      return "Case hors de la grille";
    }
    if (type == TypeBloc.SPAWN) {
      if (spawn != null && !spawn.equals(p)) {
        return "Il y a déjà un spawn en " + spawn + " : supprimez-le pour en placer un autre";
      }
      spawn = p;
    } else if (p.equals(spawn)) {
      spawn = null;
    }
    blocs.put(p, type);
    return null;
  }

  /** Efface le bloc : la case redevient du chemin. */
  public void supprimer(Position p) {
    if (!dansLaGrille(p)) {
      return;
    }
    blocs.put(p, TypeBloc.CHEMIN);
    if (p.equals(spawn)) {
      spawn = null;
    }
  }

  /** Remet toute la carte en chemin (et retire le spawn). */
  public void vider() {
    blocs.clear();
    spawn = null;
    remplirDeChemin();
  }

  /** Le bloc de la case (null seulement hors de la grille). */
  public TypeBloc getBloc(Position p) {
    return blocs.get(p);
  }

  public boolean estPraticable(Position p) {
    TypeBloc t = blocs.get(p);
    return t != null && t.estPraticable();
  }

  /** Les cases voisines (haut, bas, gauche, droite) où une fourmi peut aller. */
  public List<Position> voisinsPraticables(Position p) {
    List<Position> res = new ArrayList<>(4);
    for (int[] d : DIRECTIONS) {
      Position v = p.decaler(d[0], d[1]);
      if (estPraticable(v)) {
        res.add(v);
      }
    }
    return res;
  }

  /** Nombre de cases praticables atteignables depuis le spawn (0 s'il n'y a pas de spawn). */
  public int casesAccessiblesDepuisSpawn() {
    if (spawn == null) {
      return 0;
    }
    Set<Position> vues = new HashSet<>();
    Deque<Position> file = new ArrayDeque<>();
    vues.add(spawn);
    file.add(spawn);
    while (!file.isEmpty()) {
      for (Position v : voisinsPraticables(file.poll())) {
        if (vues.add(v)) {
          file.add(v);
        }
      }
    }
    return vues.size();
  }

  public Map<Position, TypeBloc> getBlocs() {
    return Collections.unmodifiableMap(blocs);
  }

  public Position getSpawn() {
    return spawn;
  }
}
