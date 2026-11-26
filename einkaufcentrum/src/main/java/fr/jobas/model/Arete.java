package fr.jobas.model;

import java.util.UUID;

public class Arete extends Racine {
  private float largeur;
  private float longueur;
  private int nbPheromones;
  private Noeud depart;
  private Noeud arrive;

  public Arete(Noeud depart, Noeud arrive) {
    this(UUID.randomUUID(), 0.0f, 'O', 20, 0.0f, Statut.LIBRE, 1.0f, 10.0f, 0, depart, arrive);
  }

  public Arete(
      UUID idArete,
      float tauxAcide,
      char accessibilite,
      int capaciteMax,
      float tauxOccupation,
      Statut statut,
      float largeur,
      float longueur,
      int nbPheromones,
      Noeud depart,
      Noeud arrive) {
    super(idArete, tauxAcide, accessibilite, capaciteMax, tauxOccupation, statut);
    
    if (depart == null && arrive == null) {
      throw new IllegalArgumentException("Les noeuds de départ et d'arrivée ne peuvent pas être null.");
    }
    
    this.largeur = largeur;
    this.longueur = longueur;
    this.nbPheromones = Math.max(0, nbPheromones);
    this.depart = depart;
    this.arrive = arrive;
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

  public int getNbPheromones() {
    return nbPheromones;
  }

  public void setNbPheromones(int nbPheromones) {
    this.nbPheromones = Math.max(0, nbPheromones);
  }

  public void ajouterPheromones(int quantite) {
    this.nbPheromones = Math.max(0, this.nbPheromones + quantite);
  }

  public Noeud getDepart() {
    return depart;
  }

  public void setDepart(Noeud depart) {
    this.depart = depart;
  }

  public Noeud getArrive() {
    return arrive;
  }

  public void setArrive(Noeud arrive) {
    this.arrive = arrive;
  }

  public Noeud getAutreNoeud(Noeud noeud) {
    if (noeud.equals(depart)) {
      return arrive;
    }
    if (noeud.equals(arrive)) {
      return depart;
    }
    throw new IllegalArgumentException("Ce noeud n'appartient pas à cette arête.");
  }
}