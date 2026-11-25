package fr.jobas.model;

import java.util.UUID;

public class Nid {

  private final UUID uuid;
  private final String nomEquipe;
  private final Noeud noeud;

  public Nid(String nomEquipe, Noeud noeud) {
    this.uuid = UUID.randomUUID();
    this.nomEquipe = nomEquipe;
    this.noeud = noeud;
  }

  public UUID getUuid() {
    return uuid;
  }

  public String getNomEquipe() {
    return nomEquipe;
  }

  public Noeud getNoeud() {
    return noeud;
  }
}
