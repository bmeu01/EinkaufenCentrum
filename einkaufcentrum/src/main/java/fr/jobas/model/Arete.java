package fr.jobas.model;

import java.util.UUID;

/** arete */
public class Arete {
  private UUID arete;
  private float tauxAcide;
  private char accessibilite;
  private int capaciteMax;
  private float tauxOccupation;
  private Statut statut;
  private float largeur;
  private float longueur;
  private int nbPheromones;

  public Arete(
      UUID arete,
      float tauxAcide,
      char accessibilite,
      int capaciteMax,
      float tauxOccupation,
      Statut statut,
      float largeur,
      float longueur) {
    this.arete = arete;
    this.tauxAcide = tauxAcide;
    this.accessibilite = accessibilite;
    this.capaciteMax = capaciteMax;
    this.tauxOccupation = tauxOccupation;
    this.statut = statut;
    this.largeur = largeur;
    this.longueur = longueur;
  }

  public UUID getArete() {
    return arete;
  }

  public void setArete(UUID arete) {
    this.arete = arete;
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

  public float getLargeur() {
    return largeur;
  }

  public void setLargeur(float largeur) {
    this.largeur = largeur;
  }

  public float getLongueur() {
    return longueur;
  }

  public void setLongueur(float longueur) {
    this.longueur = longueur;
  }
}
