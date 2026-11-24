package fr.jobas.model;

import java.util.ArrayList;
import java.util.List;

/** Graph */
public class Graph {

  // listes de nœuds et d'arêtes
  List<Noeud> noeuds;
  List<Arete> aretes;

  public Graph(List<Noeud> noeuds, List<Arete> aretes) {
    this.noeuds = noeuds;
    this.aretes = aretes;
  }

  public Graph() {
    this(new ArrayList<Noeud>(), new ArrayList<Arete>());
  }
}
