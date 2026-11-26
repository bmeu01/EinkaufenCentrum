package fr.jobas.model;

import java.util.UUID;

/** Caractéristiques communes aux noeuds et aux arêtes */
public abstract class Racine {
  private final UUID id;
  private float tauxAcide;
  private char accessibilite;
  private int capaciteMax;
  private float tauxOccupation;
  private Statut statut;

  protected Racine(
      UUID id,
      float tauxAcide,
      char accessibilite,
      int capaciteMax,
      float tauxOccupation,
      Statut statut) {
    this.id = id;
    this.tauxAcide = tauxAcide;
    this.accessibilite = accessibilite;
    this.capaciteMax = capaciteMax;
    this.tauxOccupation = tauxOccupation;
    this.statut = statut;
  }

  public UUID getId() {
    return id;
  }

  public float getTauxAcide() {
    return tauxAcide;
  }

  public void setTauxAcide(float tauxAcide) {
    this.tauxAcide = tauxAcide;
  }

  public char getAccessibilite() {
    return accessibilite;
  }

  public void setAccessibilite(char accessibilite) {
    this.accessibilite = accessibilite;
  }

  public int getCapaciteMax() {
    return capaciteMax;
  }

  public void setCapaciteMax(int capaciteMax) {
    this.capaciteMax = capaciteMax;
  }

  public float getTauxOccupation() {
    return tauxOccupation;
  }

  public void setTauxOccupation(float tauxOccupation) {
    this.tauxOccupation = tauxOccupation;
  }

  public Statut getStatut() {
    return statut;
  }

  public void setStatut(Statut statut) {
    this.statut = statut;
  }
}
