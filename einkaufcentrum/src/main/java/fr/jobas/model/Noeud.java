package fr.jobas.model;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class Noeud extends Racine {

  private boolean capteurAcide;
  private TypeSalle typeSalle;
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
    super(idNoeud, tauxAcide, accessibilite, capaciteMax, tauxOccupation, statut);
    this.capteurAcide = capteurAcide;
    this.typeSalle = typeSalle;
    this.aretes = (aretes != null) ? aretes : new ArrayList<>();
  }

  public TypeSalle getTypeSalle() {
    return typeSalle;
  }

  public void setTypeSalle(TypeSalle typeSalle) {
    this.typeSalle = typeSalle;
  }

  public boolean isCapteurAcide() {
    return capteurAcide;
  }

  public void setCapteurAcide(boolean capteurAcide) {
    this.capteurAcide = capteurAcide;
  }

  public TypeSalle getType() {
    return typeSalle;
  }

  public void setType(TypeSalle type) {
    this.typeSalle = type;
  }

  public List<Arete> getAretes() {
    return aretes;
  }

  public void setAretes(List<Arete> aretes) {
    this.aretes = aretes;
  }
}
