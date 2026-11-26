package fr.jobas.model;

import java.util.ArrayList;
import java.util.UUID;

import fr.jobas.model.TypeSalle;

public class Nourriture extends Noeud {

  private int quantite;

  public Nourriture(int quantite) {
    super(
        UUID.randomUUID(),
        0.0f,
        false,
        TypeSalle.NOURRITURE,
        'O',
        50,
        0.0f,
        Statut.LIBRE,
        new ArrayList<>());
    this.quantite = quantite;
  }

  public int getQuantite() {
    return quantite;
  }

  public void setQuantite(int quantite) {
    this.quantite = quantite;
  }
}
