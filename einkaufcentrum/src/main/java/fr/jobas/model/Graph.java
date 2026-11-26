package fr.jobas.model;

import java.util.ArrayList;
import java.util.List;

public class Graph {

  List<Noeud> noeuds;
  List<Arete> aretes;
  List<Nid> nids;

  public Graph() {
    this.noeuds = new ArrayList<>();
    this.aretes = new ArrayList<>();
    this.nids = new ArrayList<>();
  }

  // Ajoute un noeud dans la liste du graphe
  public void ajouterNoeud(Noeud noeud) {
    if (noeud != null && !this.noeuds.contains(noeud)) {
      this.noeuds.add(noeud);
    }
  }

  // Ajoute une arête dans la liste du graphe
  public void ajouterArete(Arete arete) {
    if (arete != null && !this.aretes.contains(arete)) {
      this.aretes.add(arete); 
    }
  }

  public List<Noeud> getNoeuds() {
    return this.noeuds;
  }

  public List<Arete> getAretes() {
    return this.aretes;
  }
}
