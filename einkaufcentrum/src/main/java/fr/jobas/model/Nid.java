package fr.jobas.model;

import java.util.ArrayList;
import java.util.UUID;

public class Nid extends Noeud {

  private String nomEquipe;

  public Nid(String nomEquipe) {
    super(
        UUID.randomUUID(),
        0.0f,
        false,
        TypeSalle.NID,
        'O',
        50,
        0.0f,
        Statut.LIBRE,
        new ArrayList<>());
    this.nomEquipe = nomEquipe;
  }

  public String getNomEquipe() {
    return nomEquipe;
  }

  public void setNomEquipe(String nomEquipe) {
    this.nomEquipe = nomEquipe;
  }
}