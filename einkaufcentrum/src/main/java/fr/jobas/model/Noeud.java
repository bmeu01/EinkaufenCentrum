package fr.jobas.model;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class Noeud {

  private UUID idNoeud;
  private float tauxAcide;
  private boolean capteurAcide;
  private TypeSalle typeSalle;
  private char accessibilite;
  private int capaciteMax;
  private float tauxOccupation;
  private Statut statut;
  private List<Arete> aretes;

  // Constructeur simple pour créer un noeud au clic de la souris
  public Noeud() {
    this(
        UUID.randomUUID(),
        0.0f,
        false,
        TypeSalle.VIDE,
        'O',
        50,
        0.0f,
        Statut.LIBRE,
        new ArrayList<>());
  }

  public Noeud(
      UUID idNoeud,
      float tauxAcide,
      boolean capteurAcide,
      TypeSalle typeSalle,
      char accessibilite,
      int capaciteMax,
      float tauxOccupation,
      Statut statut,
      List<Arete> aretes) {
    this.idNoeud = idNoeud;
    this.tauxAcide = tauxAcide;
    this.capteurAcide = capteurAcide;
    this.typeSalle = typeSalle;
    this.accessibilite = accessibilite;
    this.capaciteMax = capaciteMax;
    this.tauxOccupation = tauxOccupation;
    this.statut = statut;
    this.aretes = (aretes != null) ? aretes : new ArrayList<>();
  }

  public TypeSalle getTypeSalle() {
    return typeSalle;
  }

  public void setTypeSalle(TypeSalle typeSalle) {
    this.typeSalle = typeSalle;
  }

  public UUID getIdNoeud() {
    return idNoeud;
  }

  public void setIdNoeud(UUID idNoeud) {
    this.idNoeud = idNoeud;
  }

  public float getTauxAcide() {
    return tauxAcide;
  }

  public void setTauxAcide(float tauxAcide) {
    this.tauxAcide = tauxAcide;
  }

  public boolean isCapteurAcide() {
    return capteurAcide;
  }

  public void setCapteurAcide(boolean capteurAcide) {
    this.capteurAcide = capteurAcide;
  }

  public TypeSalle getType() {
    return type;
  }

  public void setType(TypeSalle type) {
    this.type = type;
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

  public List<Arete> getaretes() {
    return aretes;
  }

  public void setaretes(List<Arete> aretes) {
    this.aretes = aretes;
  }
}
