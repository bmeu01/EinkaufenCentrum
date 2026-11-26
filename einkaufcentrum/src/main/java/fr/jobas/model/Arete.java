package fr.jobas.model;

import java.util.UUID;

/** arete */
public class Arete extends Racine {
  private float largeur;
  private float longueur;
  private int nbPheromones;
  private Noeud depart;
  private Noeud arrive;

  public Arete(Noeud depart, Noeud arrive) {
    this(UUID.randomUUID(), 0.0f, 'O', 20, 0.0f, Statut.LIBRE, 1.0f, 10.0f);
    this.depart = depart;
    this.arrive = arrive;
  }

  public Arete(
      UUID arete,
      float tauxAcide,
      char accessibilite,
      int capaciteMax,
      float tauxOccupation,
      Statut statut,
      float largeur,
      float longueur) {
    super(arete, tauxAcide, accessibilite, capaciteMax, tauxOccupation, statut);
    this.largeur = largeur;
    this.longueur = longueur;
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

  public Noeud getDepart() {
    return depart;
  }

  public Noeud getArrive() {
    return arrive;
  }


  
}
