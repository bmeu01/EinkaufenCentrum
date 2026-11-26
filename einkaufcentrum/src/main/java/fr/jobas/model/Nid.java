package fr.jobas.model;

import java.util.UUID;

public class Nid {

  private final String nomEquipe;
  private final Noeud noeud;

  public Nid(String nomEquipe, Noeud noeud) {
    this.nomEquipe = nomEquipe;
    this.noeud = noeud;
  }

  public String getNomEquipe() {
    return nomEquipe;
  }

  public Noeud getNoeud() {
    return noeud;
  }
}
