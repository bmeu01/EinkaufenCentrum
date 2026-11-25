package fr.jobas.model;

import java.util.UUID;

public class Nourriture {

  private final UUID uuid;
  private final Noeud noeud;
  private int quantite;

  public Nourriture(Noeud noeud, int quantite) {
    this.uuid = UUID.randomUUID();
    this.noeud = noeud;
    this.quantite = quantite;
  }

  public UUID getUuid() {
    return uuid;
  }

  public Noeud getNoeud() {
    return noeud;
  }

  public int getQuantite() {
    return quantite;
  }

  public void setQuantite(int quantite) {
    this.quantite = quantite;
  }
}
